#!/usr/bin/env python3
"""
Job Alert Analyzer
Scans Gmail for LinkedIn/Indeed job alerts and uses Claude to analyze job fit.
"""

import os
import json
import re
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

# Google API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Anthropic API
import anthropic

# Email parsing
from bs4 import BeautifulSoup
from email import message_from_bytes

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
RESUME_DIR = Path(__file__).parent / 'resumes'
OUTPUT_DIR = Path(__file__).parent / 'output'


@dataclass
class JobListing:
    """Represents a parsed job listing from email."""
    title: str
    company: str
    location: str
    description: str
    url: str
    source: str  # 'linkedin' or 'indeed'
    email_date: datetime
    raw_text: str = ""


@dataclass
class JobAnalysis:
    """Claude's analysis of job fit."""
    job: JobListing
    qualification_score: int  # 1-100
    should_apply: bool
    strengths: list[str]
    gaps: list[str]
    recommendation: str
    tailoring_tips: list[str]


class GmailJobExtractor:
    """Extracts job listings from Gmail job alert emails."""
    
    def __init__(self):
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail API using OAuth."""
        creds = None
        token_path = Path(__file__).parent / 'token.json'
        credentials_path = Path(__file__).parent / 'credentials.json'
        
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not credentials_path.exists():
                    raise FileNotFoundError(
                        f"Missing {credentials_path}. Download OAuth credentials from "
                        "Google Cloud Console: https://console.cloud.google.com/apis/credentials"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        return build('gmail', 'v1', credentials=creds)
    
    def get_job_emails(self, days_back: int = 7) -> list[dict]:
        """Fetch job alert emails from the last N days."""
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        
        # Search for LinkedIn and Indeed job alert emails
        queries = [
            f'from:jobs-noreply@linkedin.com after:{after_date}',
            f'from:jobalerts-noreply@linkedin.com after:{after_date}',
            f'from:noreply@indeed.com subject:job after:{after_date}',
            f'from:alert@indeed.com after:{after_date}',
        ]
        
        all_messages = []
        for query in queries:
            try:
                results = self.service.users().messages().list(
                    userId='me', q=query, maxResults=50
                ).execute()
                messages = results.get('messages', [])
                all_messages.extend(messages)
            except Exception as e:
                print(f"Warning: Query failed - {query}: {e}")
        
        return all_messages
    
    def parse_email(self, msg_id: str) -> Optional[str]:
        """Get the full content of an email."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=msg_id, format='full'
            ).execute()
            
            payload = message.get('payload', {})
            
            # Get email body
            body = self._get_body(payload)
            return body
        except Exception as e:
            print(f"Error parsing email {msg_id}: {e}")
            return None
    
    def _get_body(self, payload: dict) -> str:
        """Extract text/HTML body from email payload."""
        body = ""
        
        if 'body' in payload and payload['body'].get('data'):
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/html':
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/plain':
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'parts' in part:
                    body = self._get_body(part)
                    if body:
                        break
        
        return body


class JobParser:
    """Parse job listings from email HTML content."""
    
    @staticmethod
    def parse_linkedin_email(html_content: str) -> list[JobListing]:
        """Extract job listings from LinkedIn alert emails."""
        jobs = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # LinkedIn job cards are typically in table cells or divs
        # Look for job titles and company names
        job_links = soup.find_all('a', href=re.compile(r'linkedin\.com/comm/jobs/view'))
        
        seen_urls = set()
        for link in job_links:
            url = link.get('href', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Try to find job title
            title_elem = link.find(['h2', 'h3', 'strong', 'span'])
            title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
            
            if not title or len(title) < 3:
                continue
            
            # Look for company and location in nearby elements
            parent = link.find_parent(['td', 'div', 'tr'])
            company = ""
            location = ""
            
            if parent:
                text_content = parent.get_text(' ', strip=True)
                # Try to extract company (usually follows the title)
                parts = text_content.split('·')
                if len(parts) >= 2:
                    company = parts[1].strip() if len(parts) > 1 else ""
                    location = parts[2].strip() if len(parts) > 2 else ""
            
            jobs.append(JobListing(
                title=title[:200],
                company=company[:100],
                location=location[:100],
                description="",  # LinkedIn emails don't include full descriptions
                url=url,
                source='linkedin',
                email_date=datetime.now(),
                raw_text=text_content if parent else title
            ))
        
        return jobs
    
    @staticmethod
    def parse_indeed_email(html_content: str) -> list[JobListing]:
        """Extract job listings from Indeed alert emails."""
        jobs = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Indeed job links
        job_links = soup.find_all('a', href=re.compile(r'indeed\.com.*jk=|indeed\.com.*vjk='))
        
        seen_urls = set()
        for link in job_links:
            url = link.get('href', '')
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue
            
            # Find parent container for more info
            parent = link.find_parent(['td', 'div', 'tr'])
            company = ""
            location = ""
            
            if parent:
                text = parent.get_text(' ', strip=True)
                # Indeed format often has company and location on separate lines
                lines = [l.strip() for l in parent.get_text('\n').split('\n') if l.strip()]
                if len(lines) >= 2:
                    company = lines[1] if len(lines) > 1 else ""
                if len(lines) >= 3:
                    location = lines[2] if len(lines) > 2 else ""
            
            jobs.append(JobListing(
                title=title[:200],
                company=company[:100],
                location=location[:100],
                description="",
                url=url,
                source='indeed',
                email_date=datetime.now(),
                raw_text=text if parent else title
            ))
        
        return jobs


class JobAnalyzer:
    """Uses Claude to analyze job fit against resumes."""
    
    def __init__(self, resume_texts: list[str]):
        self.client = anthropic.Anthropic()
        self.resume_texts = resume_texts
        self.combined_resume = "\n\n---\n\n".join(resume_texts)
    
    def analyze_job(self, job: JobListing) -> JobAnalysis:
        """Analyze a single job listing against the resume."""
        
        prompt = f"""Analyze how well this candidate matches the job listing.

## CANDIDATE'S RESUME(S):
{self.combined_resume}

## JOB LISTING:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Source: {job.source}
Available Details: {job.raw_text}

## INSTRUCTIONS:
Based on the resume and job listing, provide:
1. A qualification score (1-100) where:
   - 80-100: Highly qualified, strong match
   - 60-79: Good match, meets most requirements
   - 40-59: Partial match, some gaps
   - 1-39: Weak match, significant gaps

2. A clear YES/NO on whether to apply

3. Key strengths that match the role

4. Gaps or areas where the candidate may be weaker

5. A brief recommendation

6. Tips for tailoring the application

Respond in this exact JSON format:
{{
    "qualification_score": <int>,
    "should_apply": <bool>,
    "strengths": ["strength1", "strength2", ...],
    "gaps": ["gap1", "gap2", ...],
    "recommendation": "brief recommendation text",
    "tailoring_tips": ["tip1", "tip2", ...]
}}
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            response_text = response.content[0].text
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return JobAnalysis(
                job=job,
                qualification_score=analysis_data.get('qualification_score', 0),
                should_apply=analysis_data.get('should_apply', False),
                strengths=analysis_data.get('strengths', []),
                gaps=analysis_data.get('gaps', []),
                recommendation=analysis_data.get('recommendation', ''),
                tailoring_tips=analysis_data.get('tailoring_tips', [])
            )
            
        except Exception as e:
            print(f"Error analyzing job '{job.title}': {e}")
            return JobAnalysis(
                job=job,
                qualification_score=0,
                should_apply=False,
                strengths=[],
                gaps=[f"Analysis failed: {str(e)}"],
                recommendation="Unable to analyze",
                tailoring_tips=[]
            )
    
    def analyze_batch(self, jobs: list[JobListing]) -> list[JobAnalysis]:
        """Analyze multiple jobs and return sorted by qualification score."""
        analyses = []
        for i, job in enumerate(jobs):
            print(f"Analyzing job {i+1}/{len(jobs)}: {job.title} at {job.company}")
            analysis = self.analyze_job(job)
            analyses.append(analysis)
        
        # Sort by qualification score (highest first)
        analyses.sort(key=lambda x: x.qualification_score, reverse=True)
        return analyses


def load_resumes(resume_dir: Path) -> list[str]:
    """Load resume text files from directory."""
    resumes = []
    
    if not resume_dir.exists():
        resume_dir.mkdir(parents=True)
        print(f"Created resume directory: {resume_dir}")
        print("Please add your resume files (.txt or .md) to this directory")
        return resumes
    
    for file in resume_dir.glob('*'):
        if file.suffix.lower() in ['.txt', '.md']:
            resumes.append(file.read_text())
        elif file.suffix.lower() == '.pdf':
            # Note: PDF parsing would require additional libraries
            print(f"Note: PDF parsing not implemented. Convert {file.name} to .txt")
    
    return resumes


def generate_report(analyses: list[JobAnalysis], output_path: Path) -> str:
    """Generate a markdown report of job analyses."""
    
    report = f"""# Job Alert Analysis Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- Total jobs analyzed: {len(analyses)}
- Recommended to apply: {sum(1 for a in analyses if a.should_apply)}
- Average qualification score: {sum(a.qualification_score for a in analyses) / len(analyses):.1f}

---

## Top Recommendations (Score ≥ 60)

"""
    
    top_jobs = [a for a in analyses if a.qualification_score >= 60]
    
    if top_jobs:
        for analysis in top_jobs:
            report += f"""### {analysis.job.title}
**Company:** {analysis.job.company or 'Unknown'}  
**Location:** {analysis.job.location or 'Unknown'}  
**Source:** {analysis.job.source.capitalize()}  
**Score:** {analysis.qualification_score}/100 {'✅ APPLY' if analysis.should_apply else '⚠️ CONSIDER'}

**Strengths:**
{chr(10).join(f'- {s}' for s in analysis.strengths[:3])}

**Gaps:**
{chr(10).join(f'- {g}' for g in analysis.gaps[:3])}

**Recommendation:** {analysis.recommendation}

**Tailoring Tips:**
{chr(10).join(f'- {t}' for t in analysis.tailoring_tips[:3])}

[Apply Here]({analysis.job.url})

---

"""
    else:
        report += "*No highly qualified matches found.*\n\n---\n\n"
    
    # Add lower-scored jobs
    other_jobs = [a for a in analyses if a.qualification_score < 60]
    if other_jobs:
        report += "## Other Jobs Reviewed\n\n"
        for analysis in other_jobs[:10]:  # Limit to 10
            report += f"- **{analysis.job.title}** at {analysis.job.company or 'Unknown'} - Score: {analysis.qualification_score}/100\n"
    
    return report


def main():
    """Main entry point."""
    print("=" * 60)
    print("JOB ALERT ANALYZER")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("\n❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    # Load resumes
    print("\n📄 Loading resumes...")
    resumes = load_resumes(RESUME_DIR)
    if not resumes:
        print("❌ No resumes found. Add .txt or .md files to:", RESUME_DIR)
        return
    print(f"✓ Loaded {len(resumes)} resume(s)")
    
    # Extract jobs from Gmail
    print("\n📧 Connecting to Gmail...")
    try:
        extractor = GmailJobExtractor()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nSetup instructions:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 credentials for a Desktop app")
        print("3. Download and save as 'credentials.json' in this directory")
        return
    
    print("✓ Authenticated with Gmail")
    
    print("\n🔍 Searching for job alert emails (last 7 days)...")
    messages = extractor.get_job_emails(days_back=7)
    print(f"✓ Found {len(messages)} job alert emails")
    
    if not messages:
        print("No job alert emails found. Check your LinkedIn/Indeed alert settings.")
        return
    
    # Parse job listings from emails
    print("\n📋 Parsing job listings...")
    all_jobs = []
    parser = JobParser()
    
    for msg in messages:
        html_content = extractor.parse_email(msg['id'])
        if not html_content:
            continue
        
        # Try LinkedIn parser
        jobs = parser.parse_linkedin_email(html_content)
        if not jobs:
            # Try Indeed parser
            jobs = parser.parse_indeed_email(html_content)
        
        all_jobs.extend(jobs)
    
    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        if job.url not in seen_urls:
            seen_urls.add(job.url)
            unique_jobs.append(job)
    
    print(f"✓ Found {len(unique_jobs)} unique job listings")
    
    if not unique_jobs:
        print("No job listings could be parsed from emails.")
        return
    
    # Analyze jobs
    print("\n🤖 Analyzing job fit with Claude...")
    analyzer = JobAnalyzer(resumes)
    analyses = analyzer.analyze_batch(unique_jobs)
    
    # Generate report
    print("\n📊 Generating report...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / f"job_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    report = generate_report(analyses, report_path)
    report_path.write_text(report)
    print(f"✓ Report saved to: {report_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    top_matches = [a for a in analyses if a.qualification_score >= 60]
    print(f"\n🎯 Top matches ({len(top_matches)} jobs):")
    for analysis in top_matches[:5]:
        emoji = "✅" if analysis.should_apply else "⚠️"
        print(f"  {emoji} {analysis.qualification_score}/100 - {analysis.job.title} at {analysis.job.company or 'Unknown'}")
    
    if not top_matches:
        print("  No strong matches found in recent alerts.")
    
    print(f"\n📁 Full report: {report_path}")


if __name__ == "__main__":
    main()
