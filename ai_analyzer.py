"""
AI Analyzer - AI analysis functions (Backwards Compatibility Wrapper)

This module provides backwards compatibility for code importing from ai_analyzer.py.
The actual implementation has moved to app/ai/.

For new code, import directly from app.ai:
    from app.ai import ai_filter_and_score, analyze_job, generate_cover_letter
"""

# Re-export everything from app.ai for backwards compatibility
from app.ai import (
    # Base
    BaseAIProvider,
    # Providers
    ClaudeProvider,
    get_claude_provider,
    # Analyzer functions
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
