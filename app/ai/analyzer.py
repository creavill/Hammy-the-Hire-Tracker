"""
AI Analyzer - High-level AI analysis functions

This module provides convenient functions for job analysis using the configured
AI provider. Currently supports Claude.
"""

import logging
from typing import Dict, Tuple

from .claude import get_claude_provider

logger = logging.getLogger(__name__)


def ai_filter_and_score(job: Dict, resume_text: str) -> Tuple[bool, int, str]:
    """
    AI-based job filtering and baseline scoring.

    Args:
        job: Job dictionary with title, company, location, and raw_text
        resume_text: Combined text from all user's resumes

    Returns:
        Tuple of (should_keep, baseline_score, reason)
    """
    from app.config import get_config
    config = get_config()

    location_filter = config.get_location_filter_prompt()
    experience_level = config.experience_level
    exclude_keywords = config.exclude_keywords

    provider = get_claude_provider()
    return provider.filter_and_score(
        job, resume_text, location_filter, experience_level, exclude_keywords
    )


def analyze_job(job: Dict, resume_text: str) -> Dict:
    """
    Perform detailed job qualification analysis.

    Args:
        job: Job dictionary with title, company, location, and details
        resume_text: Combined text from all user's resumes

    Returns:
        Analysis dictionary with score, strengths, gaps, recommendation
    """
    provider = get_claude_provider()
    return provider.analyze_job(job, resume_text)


def generate_cover_letter(job: Dict, resume_text: str) -> str:
    """
    Generate a tailored cover letter.

    Args:
        job: Job dictionary with title, company, location, and analysis
        resume_text: Combined text from all user's resumes

    Returns:
        Cover letter text
    """
    provider = get_claude_provider()
    return provider.generate_cover_letter(job, resume_text)


def generate_interview_answer(
    question: str,
    job: Dict,
    resume_text: str,
    analysis: Dict
) -> str:
    """
    Generate an interview answer.

    Args:
        question: Interview question to answer
        job: Job dictionary with context
        resume_text: Candidate's resume content
        analysis: Previous AI analysis with strengths/gaps

    Returns:
        Generated interview answer
    """
    provider = get_claude_provider()
    return provider.generate_interview_answer(question, job, resume_text, analysis)


# Re-export calculate_weighted_score from scoring module for backwards compatibility
from app.scoring import calculate_weighted_score
