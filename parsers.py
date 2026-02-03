"""
Parsers - Email parsing functions (Backwards Compatibility Wrapper)

This module provides backwards compatibility for code importing from parsers.py.
The actual implementation has moved to app/parsers/.

For new code, import directly from app.parsers:
    from app.parsers import parse_email, get_parser, PARSER_REGISTRY
"""

# Re-export everything from app.parsers for backwards compatibility
from app.parsers import (
    # Registry and utilities
    PARSER_REGISTRY,
    get_parser,
    detect_source,
    parse_email,
    # Parsers
    BaseParser,
    LinkedInParser,
    IndeedParser,
    GreenhouseParser,
    WellfoundParser,
    WeWorkRemotelyParser,
    # Utility functions
    clean_job_url,
    generate_job_id,
    clean_text_field,
    fetch_wwr_jobs,
)

# Legacy function names for backwards compatibility
def parse_linkedin_jobs(html, email_date):
    """Parse LinkedIn job alert emails."""
    parser = get_parser('linkedin')
    return parser.parse(html, email_date)


def parse_indeed_jobs(html, email_date):
    """Parse Indeed job alert emails."""
    parser = get_parser('indeed')
    return parser.parse(html, email_date)


def parse_greenhouse_jobs(html, email_date):
    """Parse Greenhouse ATS job alert emails."""
    parser = get_parser('greenhouse')
    return parser.parse(html, email_date)


def parse_wellfound_jobs(html, email_date):
    """Parse Wellfound (AngelList) job alert emails."""
    parser = get_parser('wellfound')
    return parser.parse(html, email_date)


# Helper function also used in old code
def improved_title_company_split(combined_text):
    """Split combined title/company text."""
    from app.parsers.linkedin import improved_title_company_split as _split
    return _split(combined_text)


__all__ = [
    # Registry
    'PARSER_REGISTRY',
    'get_parser',
    'detect_source',
    'parse_email',
    # Parsers
    'BaseParser',
    'LinkedInParser',
    'IndeedParser',
    'GreenhouseParser',
    'WellfoundParser',
    'WeWorkRemotelyParser',
    # Utility functions
    'clean_job_url',
    'generate_job_id',
    'clean_text_field',
    'fetch_wwr_jobs',
    # Legacy function names
    'parse_linkedin_jobs',
    'parse_indeed_jobs',
    'parse_greenhouse_jobs',
    'parse_wellfound_jobs',
    'improved_title_company_split',
]
