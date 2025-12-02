"""
Cover Letter Generator Lambda - Creates tailored cover letters using Claude.
"""

import os
import json
import re
from datetime import datetime

import anthropic

from shared import get_secret, get_s3, JobModel


JOBS_TABLE = os.environ['JOBS_TABLE']
RESUMES_BUCKET = os.environ['RESUMES_BUCKET']
ANTHROPIC_SECRET_ARN = os.environ['ANTHROPIC_SECRET_ARN']

_client = None


def get_anthropic_client():
    global _client
    if _client is None:
        secret = get_secret(ANTHROPIC_SECRET_ARN)
        _client = anthropic.Anthropic(api_key=secret.get('api_key'))
    return _client


def load_resume(user_id: str, resume_type: str = "fullstack") -> str:
    """Load specific resume variant."""
    s3 = get_s3()
    
    # Try specific type first, fall back to any
    keys_to_try = [
        f"users/{user_id}/resumes/{resume_type}.txt",
        f"users/{user_id}/resumes/{resume_type}_resume.txt",
        f"users/{user_id}/resumes/resume.txt",
    ]
    
    for key in keys_to_try:
        try:
            response = s3.get_object(Bucket=RESUMES_BUCKET, Key=key)
            return response['Body'].read().decode('utf-8')
        except s3.exceptions.NoSuchKey:
            continue
    
    # Fall back to listing all resumes
    try:
        response = s3.list_objects_v2(
            Bucket=RESUMES_BUCKET, 
            Prefix=f"users/{user_id}/resumes/"
        )
        for obj in response.get('Contents', []):
            if obj['Key'].endswith(('.txt', '.md')):
                file_response = s3.get_object(Bucket=RESUMES_BUCKET, Key=obj['Key'])
                return file_response['Body'].read().decode('utf-8')
    except Exception as e:
        print(f"Error loading resume: {e}")
    
    return ""


def load_template(user_id: str) -> str:
    """Load cover letter template from S3."""
    s3 = get_s3()
    key = f"users/{user_id}/templates/cover_letter.txt"
    
    try:
        response = s3.get_object(Bucket=RESUMES_BUCKET, Key=key)
        return response['Body'].read().decode('utf-8')
    except:
        # Default template
        return """Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. {opening_hook}

{body_paragraphs}

{closing}

Sincerely,
{name}
"""


def generate_cover_letter(job: dict, resume: str, template: str) -> str:
    """Generate tailored cover letter using Claude."""
    client = get_anthropic_client()
    
    analysis = job.get('analysis', {})
    
    prompt = f"""Generate a tailored cover letter for this job application.

## JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Details: {job.get('raw_text', job.get('description', ''))}

## CANDIDATE'S RESUME:
{resume}

## PREVIOUS ANALYSIS:
Strengths: {', '.join(analysis.get('strengths', []))}
Recommendation: {analysis.get('recommendation', '')}
Tailoring tips: {', '.join(analysis.get('tailoring_tips', []))}

## TEMPLATE STRUCTURE (follow this format):
{template}

## INSTRUCTIONS:
1. Write a compelling, personalized cover letter
2. Highlight the candidate's most relevant experience
3. Show enthusiasm for the specific company and role
4. Keep it concise (3-4 paragraphs, under 400 words)
5. Use a professional but personable tone
6. Reference specific projects/achievements from the resume
7. Address any gaps diplomatically if relevant

Write the complete cover letter below (no JSON, just the letter text):
"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Cover letter generation error: {e}")
        return f"Error generating cover letter: {str(e)}"


def save_cover_letter(user_id: str, job_id: str, cover_letter: str) -> str:
    """Save cover letter to S3 and return the key."""
    s3 = get_s3()
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    key = f"users/{user_id}/cover_letters/{job_id}_{timestamp}.txt"
    
    s3.put_object(
        Bucket=RESUMES_BUCKET,
        Key=key,
        Body=cover_letter.encode('utf-8'),
        ContentType='text/plain'
    )
    
    return key


def lambda_handler(event, context):
    """
    Generate cover letter for a job.
    Input: {"user_id": "...", "job_id": "..."}
    """
    user_id = event.get('user_id', 'default')
    job_id = event.get('job_id')
    
    if not job_id:
        return {
            'statusCode': 400,
            'body': {'error': 'job_id required'}
        }
    
    model = JobModel(JOBS_TABLE)
    job = model.get_job(user_id, job_id)
    
    if not job:
        return {
            'statusCode': 404,
            'body': {'error': 'Job not found'}
        }
    
    # Determine which resume to use
    analysis = job.get('analysis', {})
    resume_type = analysis.get('resume_to_use', 'fullstack')
    
    resume = load_resume(user_id, resume_type)
    if not resume:
        return {
            'statusCode': 400,
            'body': {'error': 'No resume found'}
        }
    
    template = load_template(user_id)
    
    # Generate
    print(f"Generating cover letter for {job.get('title')} at {job.get('company')}")
    cover_letter = generate_cover_letter(job, resume, template)
    
    # Save to S3
    s3_key = save_cover_letter(user_id, job_id, cover_letter)
    
    # Update job record
    model.update_job(user_id, job_id, {
        'cover_letter': cover_letter,
        'cover_letter_s3_key': s3_key
    })
    
    return {
        'statusCode': 200,
        'body': {
            'cover_letter': cover_letter,
            's3_key': s3_key,
            'job_id': job_id
        }
    }
