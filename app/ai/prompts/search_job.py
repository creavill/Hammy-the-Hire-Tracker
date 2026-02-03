"""
Search Job Description Prompt Template

This prompt is used for web search enrichment to find additional job details.
Note: This is a stub for Phase 4 implementation.
"""


def build_search_job_prompt(company: str, title: str) -> str:
    """
    Build the prompt for job description search/enrichment.

    This is used with providers that support web search to find
    additional details about a job posting.

    Args:
        company: Company name
        title: Job title

    Returns:
        str: Formatted prompt string

    Note:
        This prompt will be used with Claude's web search or similar
        capabilities in Phase 4. For now, it's a stub.
    """
    return f"""Search for the job posting: "{title}" at "{company}"

Find and return:
1. The full job description
2. Listed requirements and qualifications
3. Salary range if available
4. Application deadline if mentioned
5. Benefits and perks mentioned

Return JSON:
{{
    "found": <bool>,
    "description": "Full job description text",
    "requirements": ["requirement 1", "requirement 2"],
    "salary_range": "$X - $Y" or null,
    "deadline": "YYYY-MM-DD" or null,
    "benefits": ["benefit 1", "benefit 2"],
    "source_url": "URL where found" or null,
    "enrichment_status": "success|not_found"
}}

If no job posting is found, return:
{{
    "found": false,
    "enrichment_status": "not_found",
    "error": "Could not find job posting for {title} at {company}"
}}
"""
