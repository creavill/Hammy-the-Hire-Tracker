#!/usr/bin/env python3
"""
Setup script for Job Tracker.
Handles Gmail OAuth and stores credentials in AWS Secrets Manager.
"""

import json
import sys
import boto3
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def setup_gmail_oauth(credentials_file: str, secret_arn: str, region: str = 'us-west-2'):
    """
    Run OAuth flow and store credentials in Secrets Manager.
    """
    credentials_path = Path(credentials_file)
    
    if not credentials_path.exists():
        print(f"Error: {credentials_file} not found.")
        print("\nTo get credentials:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 credentials (Desktop app)")
        print("3. Download JSON and save as credentials.json")
        return False
    
    # Load client secrets
    with open(credentials_path) as f:
        client_config = json.load(f)
    
    # Run OAuth flow
    print("Opening browser for Gmail authorization...")
    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Prepare secret payload
    secret_data = {
        'credentials': {
            'client_id': client_config.get('installed', client_config.get('web', {})).get('client_id'),
            'client_secret': client_config.get('installed', client_config.get('web', {})).get('client_secret'),
        },
        'token': {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'expiry': creds.expiry.isoformat() if creds.expiry else None,
        }
    }
    
    # Store in Secrets Manager
    print(f"\nStoring credentials in Secrets Manager: {secret_arn}")
    sm = boto3.client('secretsmanager', region_name=region)
    
    try:
        sm.put_secret_value(
            SecretId=secret_arn,
            SecretString=json.dumps(secret_data)
        )
        print("✓ Gmail credentials stored successfully!")
        return True
    except Exception as e:
        print(f"Error storing secret: {e}")
        return False


def setup_anthropic_key(api_key: str, secret_arn: str, region: str = 'us-west-2'):
    """Store Anthropic API key in Secrets Manager."""
    sm = boto3.client('secretsmanager', region_name=region)
    
    try:
        sm.put_secret_value(
            SecretId=secret_arn,
            SecretString=json.dumps({'api_key': api_key})
        )
        print("✓ Anthropic API key stored successfully!")
        return True
    except Exception as e:
        print(f"Error storing secret: {e}")
        return False


def upload_resumes(resume_dir: str, bucket: str, user_id: str = 'default', region: str = 'us-west-2'):
    """Upload resume files to S3."""
    s3 = boto3.client('s3', region_name=region)
    resume_path = Path(resume_dir)
    
    if not resume_path.exists():
        print(f"Resume directory not found: {resume_dir}")
        return False
    
    uploaded = 0
    for file in resume_path.glob('*'):
        if file.suffix.lower() in ['.txt', '.md']:
            key = f"users/{user_id}/resumes/{file.name}"
            print(f"Uploading {file.name}...")
            s3.upload_file(str(file), bucket, key)
            uploaded += 1
    
    print(f"✓ Uploaded {uploaded} resume files")
    return uploaded > 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Job Tracker Setup')
    parser.add_argument('--region', default='us-west-2', help='AWS region')
    parser.add_argument('--env', default='dev', help='Environment (dev/prod)')
    
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Gmail setup
    gmail_parser = subparsers.add_parser('gmail', help='Setup Gmail OAuth')
    gmail_parser.add_argument('--credentials', default='credentials.json', help='Path to OAuth credentials')
    gmail_parser.add_argument('--secret-arn', help='Secrets Manager ARN for Gmail')
    
    # Anthropic setup
    anthropic_parser = subparsers.add_parser('anthropic', help='Setup Anthropic API key')
    anthropic_parser.add_argument('--api-key', required=True, help='Anthropic API key')
    anthropic_parser.add_argument('--secret-arn', help='Secrets Manager ARN for Anthropic')
    
    # Resume upload
    resume_parser = subparsers.add_parser('resumes', help='Upload resumes to S3')
    resume_parser.add_argument('--dir', default='./resumes', help='Directory with resume files')
    resume_parser.add_argument('--bucket', required=True, help='S3 bucket name')
    resume_parser.add_argument('--user-id', default='default', help='User ID')
    
    args = parser.parse_args()
    
    if args.command == 'gmail':
        secret_arn = args.secret_arn or f"job-tracker/gmail-credentials-{args.env}"
        setup_gmail_oauth(args.credentials, secret_arn, args.region)
    
    elif args.command == 'anthropic':
        secret_arn = args.secret_arn or f"job-tracker/anthropic-api-key-{args.env}"
        setup_anthropic_key(args.api_key, secret_arn, args.region)
    
    elif args.command == 'resumes':
        upload_resumes(args.dir, args.bucket, args.user_id, args.region)


if __name__ == '__main__':
    main()
