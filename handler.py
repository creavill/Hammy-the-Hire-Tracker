"""
Job Analyzer Lambda - Uses Claude to analyze job fit and generate scores.
"""

import os
import json
import re
from typing import Optional

import anthropic

from shared import get_secret, get_s3, JobModel, JobStatus


JOBS_TABLE = os.environ['JOBS_TABLE']
RESUMES_BUCKET = os.environ['RESUMES_BUCKET']
ANTHROPIC_SECRET_ARN = os.environ['ANTHROPIC_SECRET_ARN']

# Cache
_client = None


def get_anthropic_client():
    """Get Anthropic client with API key from Secrets Manager."""
    global _client
    if _client is None:
        secret = get_secret(ANTHROPIC_SECRET_ARN)
        api_key = secret.get('api_key')
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def load_resumes(user_id: str) -> str:
    """Load all resumes for a user from S3."""
    s3 = get_s3()
    prefix = f"users/{user_id}/resumes/"
    
    try:
        response = s3.list_objects_v2(Bucket=RESUMES_BUCKET, Prefix=prefix)
        
        resumes = []
        for obj in response.get('Contents', []):
            if obj['Key'].endswith(('.txt', '.md')):
                file_response = s3.get_object(Bucket=RESUMES_BUCKET, Key=obj['Key'])
                content = file_response['Body'].read().decode('utf-8')
                resumes.append(content)
        
        return "\n\n---\n\n".join(resumes) if resumes else ""
        
    except Exception as e:
        print(f"Error loading resumes: {e}")
        return ""


def analyze_job(job: dict, resume_text: str) -> dict:
    """Use Claude to analyze job fit."""
    client = get_anthropic_client()
    
    prompt = f"""Analyze how well this candidate matches the job listing.

## CANDIDATE'S RESUME:
{resume_text}

## JOB LISTING:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Source: {job.get('source', 'Unknown')}
Details: {job.get('raw_text', job.get('description', 'No details available'))}

## INSTRUCTIONS:
Provide a JSON analysis with:
1. qualification_score (1-100):
   - 80-100: Highly qualified, strong match
   - 60-79: Good match, meets most requirements
   - 40-59: Partial match, some gaps
   - 1-39: Weak match, significant gaps

2. should_apply (boolean): Clear recommendation

3. strengths (array): Key matching qualifications (max 5)

4. gaps (array): Missing skills or experience (max 5)

5. recommendation (string): 2-3 sentence summary

6. resume_to_use (string): Which resume variant to use - "backend", "cloud", or "fullstack"

Respond ONLY with valid JSON:
{{
    "qualification_score": <int>,
    "should_apply": <bool>,
    "strengths": ["...", "..."],
    "gaps": ["...", "..."],
    "recommendation": "...",
    "resume_to_use": "..."
}}
"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        
        raise ValueError("No JSON in response")
        
    except Exception as e:
        print(f"Analysis error for job {job.get('job_id')}: {e}")
        return {
            "qualification_score": 0,
            "should_apply": False,
            "strengths": [],
            "gaps": [f"Analysis failed: {str(e)}"],
            "recommendation": "Unable to analyze",
            "resume_to_use": "fullstack"
        }


def lambda_handler(event, context):
    """
    Analyze jobs. Can analyze:
    - Single job: {"user_id": "...", "job_id": "..."}
    - All unanalyzed: {"user_id": "...", "analyze_all": true}
    """
    user_id = event.get('user_id', 'default')
    job_id = event.get('job_id')
    analyze_all = event.get('analyze_all', False)
    
    model = JobModel(JOBS_TABLE)
    
    # Load resumes
    resume_text = load_resumes(user_id)
    if not resume_text:
        return {
            'statusCode': 400,
            'body': {'error': 'No resumes found. Upload resumes to S3 first.'}
        }
    
    jobs_to_analyze = []
    
    if job_id:
        # Single job
        job = model.get_job(user_id, job_id)
        if job:
            jobs_to_analyze = [job]
    elif analyze_all:
        # All jobs with score=0 (unanalyzed)
        all_jobs = model.query_all(user_id, limit=100)
        jobs_to_analyze = [j for j in all_jobs if j.get('score', 0) == 0]
    
    if not jobs_to_analyze:
        return {
            'statusCode': 200,
            'body': {'message': 'No jobs to analyze', 'analyzed': 0}
        }
    
    analyzed_count = 0
    
    for job in jobs_to_analyze:
        print(f"Analyzing: {job.get('title')} at {job.get('company')}")
        
        analysis = analyze_job(job, resume_text)
        
        # Update job with analysis
        model.update_job(user_id, job['job_id'], {
            'score': analysis.get('qualification_score', 0),
            'analysis': analysis,
            'status': JobStatus.INTERESTED if analysis.get('should_apply') else JobStatus.NEW
        })
        
        analyzed_count += 1
    
    return {
        'statusCode': 200,
        'body': {
            'analyzed': analyzed_count,
            'user_id': user_id
        }
    }
