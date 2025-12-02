# Job Alert Analyzer

Automatically scan your Gmail for LinkedIn/Indeed job alerts and use Claude AI to analyze which jobs best match your qualifications.

## Features

- 📧 Scans Gmail for LinkedIn and Indeed job alert emails
- 🤖 Uses Claude to analyze job fit against your resume(s)
- 📊 Generates qualification scores (1-100)
- ✅ Clear YES/NO recommendations
- 💡 Tailoring tips for applications
- 📋 Markdown report output

## Setup

### 1. Install Dependencies

```bash
cd job_analyzer
pip install -r requirements.txt
```

### 2. Set Up Gmail API Access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**:
   - Go to APIs & Services → Library
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
5. Save the downloaded file as `credentials.json` in this directory

### 3. Set Anthropic API Key

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or add to your `.bashrc`/`.zshrc` for persistence.

### 4. Add Your Resume(s)

Create the `resumes/` folder and add your resume as `.txt` or `.md` files:

```bash
mkdir -p resumes
# Copy your resume text into resumes/resume.txt
```

You can add multiple resume versions (e.g., backend-focused, cloud-focused).

## Usage

```bash
python job_analyzer.py
```

On first run, it will open a browser for Gmail authentication. After that, it will:

1. Search for job alert emails from the last 7 days
2. Parse job listings from LinkedIn/Indeed emails
3. Analyze each job against your resume
4. Generate a report in `output/`

## Output

The tool generates a Markdown report including:

- Overall summary statistics
- Top recommended jobs (score ≥ 60)
  - Qualification score
  - Strengths matching the role
  - Potential gaps
  - Tailoring tips
  - Direct apply link
- List of other reviewed jobs

## Customization

Edit `job_analyzer.py` to:

- Change `days_back` in `get_job_emails()` to scan more history
- Adjust score thresholds for recommendations
- Add more email sources (other job boards)
- Modify the Claude prompt for different analysis styles

## File Structure

```
job_analyzer/
├── job_analyzer.py      # Main application
├── requirements.txt     # Python dependencies
├── credentials.json     # Gmail OAuth credentials (you add this)
├── token.json          # Auto-generated after first auth
├── resumes/            # Your resume files
│   └── resume.txt
└── output/             # Generated reports
    └── job_analysis_YYYYMMDD_HHMM.md
```

## Troubleshooting

**"Missing credentials.json"**  
Download OAuth credentials from Google Cloud Console.

**"ANTHROPIC_API_KEY not set"**  
Set your API key: `export ANTHROPIC_API_KEY='sk-...'`

**No jobs found**  
- Check that you have LinkedIn/Indeed job alerts set up
- Verify emails are in your inbox (not filtered to spam)
- Try increasing `days_back` parameter

**Authentication errors**  
Delete `token.json` and re-run to re-authenticate.
"# HireTrack" 
