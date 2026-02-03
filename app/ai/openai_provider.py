"""
OpenAI Provider - OpenAI GPT implementation

This module provides the OpenAI-specific AI implementation.
"""

import logging
import os
from typing import Any, Dict, Optional

from .base import AIProvider
from .prompts import (
    build_filter_and_score_prompt,
    build_analyze_job_prompt,
    build_cover_letter_prompt,
    build_interview_answer_prompt,
    build_search_job_prompt,
    build_classify_email_prompt,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider using the OpenAI API."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize OpenAI provider.

        Args:
            config: Configuration dict with optional 'ai.model' setting
        """
        config = config or {}
        ai_config = config.get('ai', {})
        self._model = ai_config.get('model') or DEFAULT_MODEL

        # Check for API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Set it in .env or environment variables."
            )

        # Import openai here to avoid requiring it if not used
        try:
            import openai
            self._client = openai.OpenAI()
        except ImportError:
            raise ImportError(
                "openai package not installed. "
                "Install it with: pip install openai"
            )

    @property
    def provider_name(self) -> str:
        return 'openai'

    @property
    def model_name(self) -> str:
        return self._model

    def _generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using OpenAI."""
        try:
            response = self._client.chat.completions.create(
                model=model or self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise

    def filter_and_score(
        self,
        job_data: Dict[str, Any],
        resume_text: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI-based job filtering and baseline scoring."""
        prompt = build_filter_and_score_prompt(job_data, resume_text, preferences)

        try:
            response = self._generate(prompt, max_tokens=500)
            result = self._parse_json_response(response)
            return result
        except Exception as e:
            logger.error(f"AI filter error: {e}")
            return {
                "keep": True,
                "baseline_score": 30,
                "filter_reason": "filter error - kept by default",
                "location_match": "unknown",
                "skill_level_match": "unknown"
            }

    def analyze_job(
        self,
        job_data: Dict[str, Any],
        resume_text: str
    ) -> Dict[str, Any]:
        """Perform detailed job qualification analysis."""
        prompt = build_analyze_job_prompt(job_data, resume_text)

        try:
            response = self._generate(prompt, max_tokens=1000)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "qualification_score": 0,
                "should_apply": False,
                "strengths": [],
                "gaps": [],
                "recommendation": str(e),
                "resume_to_use": "fullstack"
            }

    def generate_cover_letter(
        self,
        job: Dict[str, Any],
        resume_text: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a tailored cover letter."""
        import json

        # Parse analysis from job if not provided separately
        if analysis is None and job.get('analysis'):
            try:
                analysis = json.loads(job['analysis'])
            except (json.JSONDecodeError, TypeError):
                analysis = {}

        prompt = build_cover_letter_prompt(job, resume_text, analysis)

        try:
            return self._generate(prompt, max_tokens=1000)
        except Exception as e:
            return f"Error generating cover letter: {e}"

    def generate_interview_answer(
        self,
        question: str,
        job: Dict[str, Any],
        resume_text: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an interview answer."""
        prompt = build_interview_answer_prompt(question, job, resume_text, analysis)

        try:
            return self._generate(prompt, max_tokens=800)
        except Exception as e:
            return f"Error generating answer: {e}"

    def search_job_description(
        self,
        company: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Search for and enrich job description data.

        Note: OpenAI does not have built-in web search.
        This would require integration with a search API.
        """
        return {
            "found": False,
            "description": "",
            "requirements": [],
            "salary_range": None,
            "source_url": None,
            "enrichment_status": "not_supported",
            "error": "Web search enrichment not supported for OpenAI provider."
        }

    def classify_email(
        self,
        subject: str,
        sender: str,
        body: str
    ) -> Dict[str, Any]:
        """Classify an email for job-search relevance."""
        prompt = build_classify_email_prompt(subject, sender, body)

        try:
            response = self._generate(prompt, max_tokens=500)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Email classification error: {e}")
            return {
                "is_job_related": False,
                "classification": "other",
                "confidence": 0.0,
                "company": None,
                "summary": f"Classification failed: {e}"
            }


# Legacy support function
def get_openai_provider(model: Optional[str] = None) -> OpenAIProvider:
    """Get OpenAI provider instance."""
    config = {'ai': {'model': model}} if model else {}
    return OpenAIProvider(config)
