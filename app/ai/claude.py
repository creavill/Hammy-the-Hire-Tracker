"""
Claude AI Provider - Anthropic Claude implementation

This module provides the Claude-specific AI implementation.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple

import anthropic

from .base import BaseAIProvider

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeProvider(BaseAIProvider):
    """Claude AI provider using the Anthropic API."""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize Claude provider.

        Args:
            model: Model to use (defaults to claude-sonnet-4-20250514)
        """
        self._model = model or DEFAULT_MODEL
        self._client = anthropic.Anthropic()

    @property
    def provider_name(self) -> str:
        return 'claude'

    @property
    def default_model(self) -> str:
        return self._model

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using Claude."""
        try:
            response = self._client.messages.create(
                model=model or self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    def filter_and_score(
        self,
        job: Dict,
        resume_text: str,
        location_filter: str,
        experience_level: Dict,
        exclude_keywords: List[str]
    ) -> Tuple[bool, int, str]:
        """AI-based job filtering and baseline scoring."""
        exclude_str = ", ".join(exclude_keywords) if exclude_keywords else "None"

        prompt = f"""Analyze this job for filtering and baseline scoring.

CANDIDATE'S RESUME:
{resume_text}

JOB:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Brief Description: {(job.get('raw_text') or 'No description available')[:500]}

INSTRUCTIONS:
1. LOCATION FILTER:
{location_filter}

2. TITLE FILTER: Auto-reject if title contains: {exclude_str}

3. SKILL LEVEL: Keep ALL levels but score appropriately:
   - Entry-level/Junior roles: Give lower score (30-50) but KEEP if candidate has {experience_level.get('min_years', 1)}+ years
   - Mid-level matching candidate's {experience_level.get('current_level', 'mid')} level: High score (60-85)
   - Senior roles slightly above resume: Keep with moderate score (50-70)
   - ONLY filter if extremely mismatched: VP/Director/C-level roles, or requires {experience_level.get('max_years', 10)}+ more years than candidate has

4. BASELINE SCORE (1-100):
   - Location: Use score bonuses from location preferences (Remote=100, primary city=95, etc.)
   - Seniority: Perfect match=+20, Entry-level=-15, Slightly senior=+0, Too senior=-30
   - Company: Top tier (FAANG/unicorn)=+10, Well-known=+5, Startup=+3, Unknown=+0
   - Tech stack overlap: High=+15, Medium=+5, Low=-10

Return JSON only:
{{
    "keep": <bool>,
    "baseline_score": <1-100>,
    "filter_reason": "kept: good location match" OR "filtered: outside target location",
    "location_match": "remote|primary_location|secondary_location|excluded",
    "skill_level_match": "entry_level|good_fit|slightly_senior|too_senior"
}}
"""

        try:
            response = self.generate(prompt, max_tokens=500)
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                result = json.loads(match.group())
                return (
                    result.get('keep', False),
                    result.get('baseline_score', 0),
                    result.get('filter_reason', 'unknown')
                )
        except Exception as e:
            logger.error(f"AI filter error: {e}")

        return (True, 30, "filter error - kept by default")

    def analyze_job(self, job: Dict, resume_text: str) -> Dict:
        """Perform detailed job qualification analysis."""
        prompt = f"""Analyze job fit with strict accuracy. Respond ONLY with valid JSON.

CANDIDATE'S RESUME:
{resume_text}

JOB LISTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Details: {job['raw_text']}

CRITICAL INSTRUCTIONS:
1. ONLY mention job titles/roles the candidate has ACTUALLY held (check resume carefully)
2. ONLY cite technologies/skills explicitly listed in resume
3. should_apply = true ONLY if qualification_score >= 65 AND no major dealbreakers
4. Dealbreakers: wrong tech stack, requires 5+ years when candidate has 2, senior leadership role

SCORING RUBRIC:
- 80-100: Strong match, most requirements met, similar past roles
- 60-79: Good match, can do the job with minor gaps
- 40-59: Partial match, significant skill gaps but learnable
- 1-39: Weak match, wrong seniority/stack/domain

Return JSON:
{{
    "qualification_score": <1-100>,
    "should_apply": <bool>,
    "strengths": ["actual skills from resume that match", "relevant past experience"],
    "gaps": ["missing requirements", "areas to improve"],
    "recommendation": "2-3 sentence honest assessment",
    "resume_to_use": "backend|cloud|fullstack"
}}
"""

        try:
            response = self.generate(prompt, max_tokens=1000)
            match = re.search(r'\{[\s\S]*\}', response)
            return json.loads(match.group()) if match else {}
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {"qualification_score": 0, "should_apply": False, "recommendation": str(e)}

    def generate_cover_letter(self, job: Dict, resume_text: str) -> str:
        """Generate a tailored cover letter."""
        analysis = json.loads(job['analysis']) if job.get('analysis') else {}

        prompt = f"""Write a tailored cover letter (3-4 paragraphs, under 350 words).

JOB: {job['title']} at {job['company']}
Details: {job.get('raw_text', '')}

CANDIDATE RESUME:
{resume_text}

STRENGTHS: {', '.join(analysis.get('strengths', []))}

Write the cover letter now:"""

        try:
            return self.generate(prompt, max_tokens=1000)
        except Exception as e:
            return f"Error: {e}"

    def generate_interview_answer(
        self,
        question: str,
        job: Dict,
        resume_text: str,
        analysis: Dict
    ) -> str:
        """Generate an interview answer."""
        prompt = f"""Generate a strong interview answer using ONLY actual resume content.

QUESTION: {question}

JOB CONTEXT:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:500]}

CANDIDATE'S RESUME:
{resume_text}

VERIFIED ANALYSIS:
Strengths: {', '.join(analysis.get('strengths', []))}
Gaps: {', '.join(analysis.get('gaps', []))}

CRITICAL RULES:
1. ONLY cite projects, roles, metrics from the actual resume
2. Do NOT invent experience or extrapolate skills
3. Use specific examples with concrete details
4. Be honest about gaps but frame positively
5. Natural, conversational tone (not rehearsed)

Generate 2-3 paragraph answer (150-200 words):"""

        try:
            return self.generate(prompt, max_tokens=800)
        except Exception as e:
            return f"Error: {e}"


# Singleton provider instance
_provider: Optional[ClaudeProvider] = None


def get_claude_provider(model: Optional[str] = None) -> ClaudeProvider:
    """Get singleton Claude provider instance."""
    global _provider
    if _provider is None:
        _provider = ClaudeProvider(model)
    return _provider
