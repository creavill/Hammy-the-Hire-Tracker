# Job Tracker

Personal AWS-hosted job application tracker with AI-powered job matching and cover letter generation.

## Features

- 📧 **Auto-scan Gmail** for LinkedIn/Indeed job alerts
- 🤖 **AI job scoring** against your resume variants
- 📝 **Tailored cover letters** generated on demand
- 📊 **Dashboard** with filtering, status tracking
- 💰 **~$10/month** serverless architecture

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Gmail API       │───▶│ Email Scanner   │───▶│ DynamoDB        │
│ (alerts)        │    │ Lambda (6hr)    │    │ (jobs table)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                       │
                              ▼                       │
                       ┌─────────────────┐            │
                       │ Job Analyzer    │◀───────────┘
                       │ Lambda (Claude) │
                       └─────────────────┘
                              │
┌─────────────────┐    ┌──────┴──────────┐    ┌─────────────────┐
│ React Dashboard │◀───│ API Gateway     │───▶│ Cover Letter    │
│ (S3/CloudFront) │    │                 │    │ Lambda (Claude) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- AWS CLI configured
- Python 3.12
- Node.js 18+
- Gmail API credentials (see below)
- Anthropic API key

### 1. Deploy Infrastructure

```bash
cd infrastructure
sam build
sam deploy --guided
```

Note the outputs:
- `ResumesBucketName` - for resume uploads
- `GmailSecretArn` - for Gmail OAuth
- `AnthropicSecretArn` - for Claude API key
- `CloudFrontUrl` - your dashboard URL

### 2. Setup Gmail OAuth

```bash
# 1. Go to https://console.cloud.google.com
# 2. Create project → Enable Gmail API
# 3. Create OAuth credentials (Desktop app)
# 4. Download as credentials.json

cd scripts
pip install google-auth-oauthlib boto3

python setup.py gmail \
  --credentials ../credentials.json \
  --secret-arn <GmailSecretArn from deploy>
```

### 3. Add Anthropic API Key

```bash
python setup.py anthropic \
  --api-key sk-ant-... \
  --secret-arn <AnthropicSecretArn from deploy>
```

### 4. Upload Resumes

Place your resumes (`.txt` or `.md`) in a folder:
```
resumes/
├── backend.txt
├── cloud.txt
└── fullstack.txt
```

Upload:
```bash
python setup.py resumes \
  --dir ../resumes \
  --bucket <ResumesBucketName>
```

### 5. Build & Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Upload to S3
aws s3 sync dist/ s3://<StaticSiteBucketName>/
```

### 6. Access Dashboard

Open `CloudFrontUrl` from deploy output.

## Usage

**Automatic scanning:** Email scanner runs every 6 hours via EventBridge.

**Manual scan:** Click "Scan Emails" button in dashboard.

**Workflow:**
1. New jobs appear with AI scores
2. Review matches, update status (Interested → Applied)
3. Generate tailored cover letters for promising jobs
4. Track application progress

## Configuration

### Environment Variables

In `template.yaml`, modify:
- `Schedule: rate(6 hours)` - scan frequency
- `DEFAULT_USER_ID` - your user identifier

### Adding Job Sources

Edit `src/functions/email_scanner/handler.py`:
```python
queries = [
    f'from:jobs-noreply@linkedin.com after:{after_date}',
    f'from:noreply@indeed.com after:{after_date}',
    # Add more:
    f'from:alerts@glassdoor.com after:{after_date}',
]
```

## Future: Multi-Tenant Expansion

The architecture is designed for expansion:

1. **Enable Cognito** (uncommented in template.yaml)
2. **Add API Gateway authorizer**
3. **User ID from JWT claims** instead of DEFAULT_USER_ID
4. **Per-user S3 prefixes** already in place

## Costs

| Service | Estimated Monthly |
|---------|------------------|
| DynamoDB (on-demand) | $2-5 |
| Lambda | $1-3 |
| S3 | $0.50 |
| CloudFront | $1-2 |
| Secrets Manager | $0.80 |
| Anthropic API | ~$5-10 |
| **Total** | **~$10-20** |

## Troubleshooting

**No jobs appearing:**
- Check Gmail OAuth is working: `aws secretsmanager get-secret-value --secret-id <arn>`
- Verify you have LinkedIn/Indeed alerts enabled
- Check CloudWatch logs for email_scanner Lambda

**Analysis failing:**
- Verify Anthropic key in Secrets Manager
- Check resumes are uploaded to S3
- Review job_analyzer Lambda logs

**Cover letters not generating:**
- Check cover_letter Lambda logs
- Ensure job exists and has been analyzed

## Project Structure

```
job-tracker/
├── infrastructure/
│   └── template.yaml       # SAM/CloudFormation
├── src/
│   ├── functions/
│   │   ├── api/           # REST API handler
│   │   ├── cover_letter/  # Cover letter generator
│   │   ├── email_scanner/ # Gmail scanner
│   │   └── job_analyzer/  # Claude analysis
│   └── layers/
│       └── shared/        # Common utilities
├── frontend/
│   └── src/App.jsx        # React dashboard
├── scripts/
│   └── setup.py           # Setup helper
└── resumes/               # Your resume files
```
