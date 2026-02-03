# Hammy the Hire Tracker

**AI-Powered Job Search Assistant** that automatically scans your Gmail for job alerts, analyzes opportunities against your resume using Claude AI, and helps you track applications with intelligent insights.

---

## Features

### AI-Powered Analysis
- **Smart Filtering**: Automatically filters jobs by location preferences and experience level
- **Qualification Scoring**: Claude AI scores each job 1-100 based on your resume fit
- **Resume Matching**: Recommends which resume variant to use for each application
- **Cover Letter Generation**: Creates tailored cover letters citing actual resume experience
- **Interview Prep**: Generates practice answers to common interview questions

### Automated Job Discovery
- **Gmail Integration**: Scans LinkedIn, Indeed, Greenhouse, and Wellfound job alerts
- **WeWorkRemotely RSS**: Pulls remote job opportunities automatically
- **Smart Deduplication**: Removes tracking parameters to prevent duplicate entries
- **Follow-up Detection**: Identifies interview and offer emails

### Intelligent Tracking
- **Web Dashboard**: Clean UI for managing your job pipeline
- **Status Management**: Track applications through new → interested → applied → interviewing
- **Company Watchlist**: Monitor companies not currently hiring
- **Weighted Scoring**: Jobs sorted by 70% qualification + 30% recency

### Chrome Extension
- **Instant Analysis**: Analyze any job posting without leaving the page
- **Side Panel UI**: Clean interface that works on LinkedIn, Indeed, and more
- **One-Click Actions**: Generate cover letters and interview answers on the fly

---

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Gmail account with job alerts enabled
- [Anthropic API key](https://console.anthropic.com/) (Claude AI)
- Google Cloud project with Gmail API enabled

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/creavill/Hammy-the-Hire-Tracker.git
cd Hammy-the-Hire-Tracker
```

#### 2. Install Dependencies
```bash
# Python dependencies
pip install -r requirements.txt

# Frontend dependencies
npm install
npm run build
```

#### 3. Configure Your Profile
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with:
- Your name, email, phone, location
- LinkedIn, GitHub, portfolio URLs
- Location preferences (cities, remote preferences)
- Experience level and job preferences

#### 4. Add Your Resumes
```bash
cp resumes/templates/backend_developer_resume_template.txt resumes/backend_developer_resume.txt
```

Edit with your actual experience, then update `config.yaml` to reference your resume files.

#### 5. Set Up Gmail API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Gmail API**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials file as `credentials.json` in the project root

#### 6. Set Up Environment Variables
```bash
cp .env.example .env
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

#### 7. Run the Application
```bash
python run.py
# or
python local_app.py
```

Visit **http://localhost:5000** to see your dashboard!

---

## Usage Guide

### Dashboard Workflow

1. **Scan Gmail** - Click "Scan Gmail" to import job alerts
2. **Review Jobs** - Jobs sorted by weighted score (qualification + recency)
   - Green badges (80+): Strong matches
   - Blue badges (60-79): Good matches
   - Yellow badges (40-59): Partial matches
3. **Analyze All** - Get detailed AI analysis with strengths, gaps, recommendations
4. **Track Applications** - Update status and add notes
5. **Generate Cover Letters** - AI creates tailored letters based on your resume

### Chrome Extension Setup

1. In Chrome, go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension` folder
4. Navigate to any job posting and click the extension icon

---

## Project Structure

```
Hammy-the-Hire-Tracker/
├── run.py                    # New entry point (recommended)
├── local_app.py              # Legacy entry point
├── app/                      # Application package
│   ├── __init__.py           # Flask factory (create_app)
│   ├── config.py             # Configuration management
│   ├── database.py           # Database operations
│   ├── scoring.py            # Job scoring logic
│   ├── ai/                   # AI analysis module
│   │   ├── base.py           # Abstract AI provider
│   │   ├── claude.py         # Claude implementation
│   │   └── analyzer.py       # Analysis functions
│   ├── email/                # Email scanning module
│   │   ├── client.py         # Gmail client
│   │   └── scanner.py        # Email scanning
│   ├── parsers/              # Job board parsers
│   │   ├── base.py           # Base parser class
│   │   ├── linkedin.py       # LinkedIn parser
│   │   ├── indeed.py         # Indeed parser
│   │   └── ...               # Other parsers
│   └── routes/               # Flask blueprints
│       └── main.py           # Frontend routes
├── routes.py                 # API routes
├── config.yaml               # User configuration
├── config.example.yaml       # Configuration template
├── .env                      # API keys
├── requirements.txt          # Python dependencies
├── App.jsx                   # React dashboard
├── index.html                # Frontend entry
├── tailwind.config.js        # Tailwind configuration
├── extension/                # Chrome extension
└── resumes/                  # Resume files
```

---

## Configuration

### config.yaml

```yaml
user:
  name: "Your Name"
  email: "you@example.com"
  location: "Your City, State"

resumes:
  files:
    - "resumes/backend_developer_resume.txt"
  variants:
    backend:
      focus: "Backend development, APIs"
      file: "resumes/backend_developer_resume.txt"

preferences:
  locations:
    primary:
      - name: "Remote"
        type: "remote"
        score_bonus: 100
      - name: "San Francisco, CA"
        type: "city"
        score_bonus: 95

  experience_level:
    min_years: 2
    max_years: 7
    current_level: "mid"

  filters:
    exclude_keywords: ["Director", "VP", "Chief"]
    min_baseline_score: 30
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=your_claude_api_key
```

---

## Contributing

### Adding New Job Boards

1. Create parser in `app/parsers/`:
   ```python
   from .base import BaseParser

   class NewBoardParser(BaseParser):
       @property
       def source_name(self) -> str:
           return 'newboard'

       def parse(self, html, email_date):
           # Extract jobs
           return jobs_list
   ```

2. Register in `app/parsers/__init__.py`

### Customizing AI Prompts

Edit prompts in `app/ai/claude.py`:
- `filter_and_score()`: Location filtering and baseline scoring
- `analyze_job()`: Detailed qualification analysis
- `generate_cover_letter()`: Cover letter generation

---

## Troubleshooting

### "Missing credentials.json"
Download OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/). Enable Gmail API.

### "ANTHROPIC_API_KEY not set"
```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

### Gmail Authentication Errors
```bash
rm token.json
python run.py  # Re-authenticate
```

### UI Not Updating
Rebuild the frontend:
```bash
npm run build
```

---

## Tech Stack

- **Python 3.12** / Flask - Backend
- **SQLite** - Database
- **Claude Sonnet 4** - AI analysis (Anthropic API)
- **Gmail API** - Email scanning
- **React 18** / Vite / Tailwind CSS - Frontend

---

## License

MIT License - feel free to use this for your own job search!

---

**Built for job seekers by job seekers**
