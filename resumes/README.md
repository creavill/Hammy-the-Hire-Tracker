# Resume Setup Guide

## Quick Start

1. **Copy template files to this directory:**
   ```bash
   cp templates/fullstack_developer_resume_template.txt fullstack_developer_resume.txt
   cp templates/backend_developer_resume_template.txt backend_developer_resume.txt
   cp templates/cloud_engineer_resume_template.txt cloud_engineer_resume.txt
   ```

2. **Edit each file** and replace ALL placeholder text (anything in `[BRACKETS]`) with your actual information.

3. **Update `config.yaml`** to reference your resume files:
   ```yaml
   resumes:
     files:
       - "resumes/backend_developer_resume.txt"
       - "resumes/cloud_engineer_resume.txt"
       - "resumes/fullstack_developer_resume.txt"
   ```

## Important Notes

- ⚠️ **Your resume files are gitignored** - they will NOT be committed to version control
- Keep your resume files in `.txt` format for AI analysis
- Use clear, consistent formatting within each file
- Include metrics and specific achievements where possible

## Templates Provided

- **fullstack_developer_resume_template.txt** - For full-stack development roles
- **backend_developer_resume_template.txt** - For backend/systems engineering roles
- **cloud_engineer_resume_template.txt** - For cloud infrastructure/DevOps roles

## Creating Custom Resume Variants

You can create additional resume variants by:

1. Copying one of the templates
2. Tailoring it to a specific role type
3. Adding it to your `config.yaml` under `resumes.files`
4. Optionally defining it in `resumes.variants` for AI recommendation

The AI will analyze all your resume files and recommend the best match for each job.
