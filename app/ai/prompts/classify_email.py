"""
Classify Email Prompt Template

This prompt is used for classifying job-related emails.
"""


def build_classify_email_prompt(subject: str, sender: str, body: str) -> str:
    """
    Build the prompt for email classification.

    Determines if an email is job-search related and categorizes it
    as interview, offer, rejection, update, or other.

    Args:
        subject: Email subject line
        sender: Sender email address
        body: Email body text (may be truncated)

    Returns:
        str: Formatted prompt string
    """
    # Truncate body if too long
    truncated_body = body[:2000] if len(body) > 2000 else body

    return f"""Classify this email for job search relevance.

EMAIL:
Subject: {subject}
From: {sender}
Body:
{truncated_body}

CLASSIFICATION CATEGORIES:
- "interview": Email scheduling or confirming an interview
- "offer": Job offer or compensation discussion
- "rejection": Application rejected or position filled
- "update": Application status update, "we're still reviewing", etc.
- "other": Not job-search related

CONFIDENCE SCORING:
- 0.9-1.0: Very confident in classification
- 0.7-0.9: Fairly confident
- 0.5-0.7: Somewhat uncertain
- Below 0.5: Guessing

Return JSON only:
{{
    "is_job_related": <bool>,
    "classification": "interview|offer|rejection|update|other",
    "confidence": <0.0-1.0>,
    "company": "Extracted company name" or null,
    "summary": "Brief 1-sentence summary of the email"
}}
"""
