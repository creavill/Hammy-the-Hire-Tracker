"""
API Handler Lambda - REST API for dashboard frontend.
"""

import os
import json
import boto3

from shared import json_response, JobModel, JobStatus


JOBS_TABLE = os.environ['JOBS_TABLE']
RESUMES_BUCKET = os.environ['RESUMES_BUCKET']
DEFAULT_USER_ID = os.environ.get('DEFAULT_USER_ID', 'default')


def get_user_id(event: dict) -> str:
    """Extract user ID. Future: from Cognito claims."""
    # Future multi-tenant:
    # claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
    # return claims.get('sub', DEFAULT_USER_ID)
    return DEFAULT_USER_ID


def handle_get_jobs(event: dict, model: JobModel) -> dict:
    """GET /api/jobs - List jobs with optional filters."""
    user_id = get_user_id(event)
    params = event.get('queryStringParameters') or {}
    
    status = params.get('status')
    min_score = params.get('min_score')
    sort_by = params.get('sort', 'score')  # score, date, status
    limit = int(params.get('limit', 50))
    
    if status and status in JobStatus.ALL:
        jobs = model.query_by_status(user_id, status, limit)
    elif min_score:
        jobs = model.query_by_score(user_id, int(min_score), limit)
    elif sort_by == 'date':
        jobs = model.query_recent(user_id, limit)
    elif sort_by == 'score':
        jobs = model.query_by_score(user_id, 0, limit)
    else:
        jobs = model.query_all(user_id, limit)
    
    # Summary stats
    all_jobs = model.query_all(user_id, 500)
    stats = {
        'total': len(all_jobs),
        'new': len([j for j in all_jobs if j.get('status') == JobStatus.NEW]),
        'interested': len([j for j in all_jobs if j.get('status') == JobStatus.INTERESTED]),
        'applied': len([j for j in all_jobs if j.get('status') == JobStatus.APPLIED]),
        'avg_score': sum(j.get('score', 0) for j in all_jobs) / len(all_jobs) if all_jobs else 0
    }
    
    return json_response(200, {
        'jobs': jobs,
        'stats': stats,
        'count': len(jobs)
    })


def handle_get_job(event: dict, model: JobModel) -> dict:
    """GET /api/jobs/{job_id} - Get single job."""
    user_id = get_user_id(event)
    job_id = event.get('pathParameters', {}).get('job_id')
    
    if not job_id:
        return json_response(400, {'error': 'job_id required'})
    
    job = model.get_job(user_id, job_id)
    
    if not job:
        return json_response(404, {'error': 'Job not found'})
    
    return json_response(200, job)


def handle_update_job(event: dict, model: JobModel) -> dict:
    """PATCH /api/jobs/{job_id} - Update job status/notes."""
    user_id = get_user_id(event)
    job_id = event.get('pathParameters', {}).get('job_id')
    
    if not job_id:
        return json_response(400, {'error': 'job_id required'})
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return json_response(400, {'error': 'Invalid JSON'})
    
    # Allowed updates
    allowed_fields = ['status', 'notes', 'applied_date', 'interview_date']
    updates = {k: v for k, v in body.items() if k in allowed_fields}
    
    if 'status' in updates and updates['status'] not in JobStatus.ALL:
        return json_response(400, {'error': f'Invalid status. Use: {JobStatus.ALL}'})
    
    if not updates:
        return json_response(400, {'error': 'No valid fields to update'})
    
    job = model.update_job(user_id, job_id, updates)
    return json_response(200, job)


def handle_generate_cover_letter(event: dict, model: JobModel) -> dict:
    """POST /api/jobs/{job_id}/cover-letter - Trigger cover letter generation."""
    user_id = get_user_id(event)
    job_id = event.get('pathParameters', {}).get('job_id')
    
    if not job_id:
        return json_response(400, {'error': 'job_id required'})
    
    # Invoke cover letter Lambda async
    lambda_client = boto3.client('lambda')
    
    try:
        lambda_client.invoke(
            FunctionName=f"job-tracker-cover-letter-{os.environ.get('ENVIRONMENT', 'dev')}",
            InvocationType='Event',  # Async
            Payload=json.dumps({
                'user_id': user_id,
                'job_id': job_id
            })
        )
        return json_response(202, {'message': 'Cover letter generation started', 'job_id': job_id})
    except Exception as e:
        return json_response(500, {'error': f'Failed to start generation: {str(e)}'})


def handle_trigger_scan(event: dict) -> dict:
    """POST /api/scan - Manually trigger email scan."""
    user_id = get_user_id(event)
    
    lambda_client = boto3.client('lambda')
    
    try:
        # Trigger email scanner
        lambda_client.invoke(
            FunctionName=f"job-tracker-email-scanner-{os.environ.get('ENVIRONMENT', 'dev')}",
            InvocationType='Event',
            Payload=json.dumps({'user_id': user_id})
        )
        
        # Trigger analyzer after scanner
        lambda_client.invoke(
            FunctionName=f"job-tracker-analyzer-{os.environ.get('ENVIRONMENT', 'dev')}",
            InvocationType='Event',
            Payload=json.dumps({'user_id': user_id, 'analyze_all': True})
        )
        
        return json_response(202, {'message': 'Scan and analysis started'})
    except Exception as e:
        return json_response(500, {'error': f'Failed to start scan: {str(e)}'})


def lambda_handler(event, context):
    """Route API requests."""
    http_method = event.get('httpMethod', '')
    path = event.get('path', '')
    
    model = JobModel(JOBS_TABLE)
    
    # Routing
    if path == '/api/jobs' and http_method == 'GET':
        return handle_get_jobs(event, model)
    
    elif path.startswith('/api/jobs/') and '/cover-letter' in path and http_method == 'POST':
        return handle_generate_cover_letter(event, model)
    
    elif path.startswith('/api/jobs/') and http_method == 'GET':
        return handle_get_job(event, model)
    
    elif path.startswith('/api/jobs/') and http_method == 'PATCH':
        return handle_update_job(event, model)
    
    elif path == '/api/scan' and http_method == 'POST':
        return handle_trigger_scan(event)
    
    else:
        return json_response(404, {'error': 'Not found'})
