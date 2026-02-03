"""
AI Package - AI-powered analysis for Hammy the Hire Tracker

This module provides AI-powered job analysis, cover letter generation,
and interview answer generation.

Usage:
    from app.ai import ai_filter_and_score, analyze_job, generate_cover_letter

    # Filter and score a job
    keep, score, reason = ai_filter_and_score(job, resume_text)

    # Full analysis
    analysis = analyze_job(job, resume_text)

    # Generate cover letter
    letter = generate_cover_letter(job, resume_text)
"""

from .base import BaseAIProvider
from .claude import ClaudeProvider, get_claude_provider
from .analyzer import (
    ai_filter_and_score,
    analyze_job,
    generate_cover_letter,
    generate_interview_answer,
    calculate_weighted_score,
)

__all__ = [
    # Base
    'BaseAIProvider',
    # Providers
    'ClaudeProvider',
    'get_claude_provider',
    # Analyzer functions
    'ai_filter_and_score',
    'analyze_job',
    'generate_cover_letter',
    'generate_interview_answer',
    'calculate_weighted_score',
]
