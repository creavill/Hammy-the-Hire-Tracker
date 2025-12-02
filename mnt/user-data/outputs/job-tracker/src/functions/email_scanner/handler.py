"""
Email Scanner Lambda - Scans Gmail for job alerts and queues for analysis.
"""

import os
import json
import re
import base64
from datetime import datetime, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from shared import get_secret, JobModel, generate_job_id, JobStatus


# Config from environment
JOBS_TABLE = os.environ['JOBS_TABLE']
GMAIL_SECRET_ARN = os.environ['GMAIL_SECRET_ARN']
DEFAULT_USER_ID = os.environ.get('DEFAULT_USER_ID', 'default')

# Gmail scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Initialize Gmail API service from stored credentials."""
    secret = get_secret(GMAIL_SECRET_ARN)
    
    creds_data = secret.get('credentials', {})
    token_data = secret.get('token', {})
    
    if not token_data:
        raise ValueError("No Gmail token found. Run setup script to authenticate.")
    
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=creds_data.get('client_id'),
        client_secret=creds_data.get('client_secret'),
        scopes=SCOPES
    )
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # TODO: Update secret with new token
    
    return build('gmail', 'v1', credentials=creds)


def get_email_body(payload: dict) -> str:
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
            elif part['mimeType'] == 'text/plain' and not body:
                if 'data' in part.get('body', {}):
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif 'parts' in part:
                body = get_email_body(part)
                if body:
                    break
    
    return body


def parse_linkedin_jobs(html: str, email_date: str) -> list[dict]:
    """Extract job listings from LinkedIn alert emails."""
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')
    
    job_links = soup.find_all('a', href=re.compile(r'linkedin\.com/comm/jobs/view'))
    
    seen_urls = set()
    for link in job_links:
        url = link.get('href', '')
        if url in seen_urls:
            continue
        seen_urls.add(url)
        
        # Extract title
        title_elem = link.find(['h2', 'h3', 'strong', 'span'])
        title = title_elem.get_text(strip=True) if title_elem else link.get_text(strip=True)
        
        if not title or len(title) < 3:
            continue
        
        # Find context
        parent = link.find_parent(['td', 'div', 'tr'])
        company = ""
        location = ""
        raw_text = title
        
        if parent:
            raw_text = parent.get_text(' ', strip=True)
            parts = raw_text.split('·')
            if len(parts) >= 2:
                company = parts[1].strip()[:100]
            if len(parts) >= 3:
                location = parts[2].strip()[:100]
        
        job_id = generate_job_id(url, title, company)
        
        jobs.append({
            'job_id': job_id,
            'title': title[:200],
            'company': company,
            'location': location,
            'url': url,
            'source': 'linkedin',
            'email_date': email_date,
            'raw_text': raw_text[:1000],
            'status': JobStatus.NEW,
            'score': 0,
        })
    
    return jobs


def parse_indeed_jobs(html: str, email_date: str) -> list[dict]:
    """Extract job listings from Indeed alert emails."""
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')
    
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
        
        parent = link.find_parent(['td', 'div', 'tr'])
        company = ""
        location = ""
        raw_text = title
        
        if parent:
            raw_text = parent.get_text(' ', strip=True)
            lines = [l.strip() for l in parent.get_text('\n').split('\n') if l.strip()]
            if len(lines) >= 2:
                company = lines[1][:100]
            if len(lines) >= 3:
                location = lines[2][:100]
        
        job_id = generate_job_id(url, title, company)
        
        jobs.append({
            'job_id': job_id,
            'title': title[:200],
            'company': company,
            'location': location,
            'url': url,
            'source': 'indeed',
            'email_date': email_date,
            'raw_text': raw_text[:1000],
            'status': JobStatus.NEW,
            'score': 0,
        })
    
    return jobs


def scan_emails(service, days_back: int = 7) -> list[dict]:
    """Scan Gmail for job alert emails and extract jobs."""
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
    
    queries = [
        f'from:jobs-noreply@linkedin.com after:{after_date}',
        f'from:jobalerts-noreply@linkedin.com after:{after_date}',
        f'from:noreply@indeed.com subject:job after:{after_date}',
        f'from:alert@indeed.com after:{after_date}',
    ]
    
    all_jobs = []
    
    for query in queries:
        try:
            results = service.users().messages().list(
                userId='me', q=query, maxResults=50
            ).execute()
            
            for msg_info in results.get('messages', []):
                try:
                    message = service.users().messages().get(
                        userId='me', id=msg_info['id'], format='full'
                    ).execute()
                    
                    # Get email date
                    internal_date = int(message.get('internalDate', 0)) / 1000
                    email_date = datetime.fromtimestamp(internal_date).isoformat()
                    
                    payload = message.get('payload', {})
                    html = get_email_body(payload)
                    
                    if not html:
                        continue
                    
                    # Try LinkedIn parser first
                    if 'linkedin' in query:
                        jobs = parse_linkedin_jobs(html, email_date)
                    else:
                        jobs = parse_indeed_jobs(html, email_date)
                    
                    all_jobs.extend(jobs)
                    
                except Exception as e:
                    print(f"Error parsing email {msg_info['id']}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Query failed - {query}: {e}")
            continue
    
    return all_jobs


def lambda_handler(event, context):
    """Main Lambda handler - scan emails and store new jobs."""
    print("Starting email scan...")
    
    # Get user ID (single user for now, expandable later)
    user_id = event.get('user_id', DEFAULT_USER_ID)
    days_back = event.get('days_back', 7)
    
    try:
        # Initialize Gmail
        service = get_gmail_service()
        print("Gmail service initialized")
        
        # Scan emails
        jobs = scan_emails(service, days_back)
        print(f"Found {len(jobs)} jobs from emails")
        
        # Store new jobs in DynamoDB
        model = JobModel(JOBS_TABLE)
        new_count = 0
        
        for job in jobs:
            if not model.job_exists(user_id, job['job_id']):
                model.put_job(user_id, job)
                new_count += 1
        
        print(f"Stored {new_count} new jobs")
        
        return {
            'statusCode': 200,
            'body': {
                'jobs_found': len(jobs),
                'new_jobs_stored': new_count,
                'user_id': user_id
            }
        }
        
    except Exception as e:
        print(f"Error in email scan: {e}")
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
