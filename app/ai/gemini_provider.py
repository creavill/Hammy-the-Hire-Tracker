"""
Gemini Provider - Google Gemini implementation

This module provides the Google Gemini-specific AI implementation.
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

DEFAULT_MODEL = "gemini-1.5-pro"


class GeminiProvider(AIProvider):
    """Google Gemini provider using the Google Generative AI API."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Gemini provider.

        Args:
            config: Configuration dict with optional 'ai.model' setting
        """
        config = config or {}
        ai_config = config.get('ai', {})
        self._model = ai_config.get('model') or DEFAULT_MODEL

        # Check for API key
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. "
                "Set it in .env or environment variables."
            )

        # Import google.generativeai here to avoid requiring it if not used
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
            self._model_instance = genai.GenerativeModel(self._model)
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install it with: pip install google-generativeai"
            )

    @property
    def provider_name(self) -> str:
        return 'gemini'

    @property
    def model_name(self) -> str:
        return self._model

    def _generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using Gemini."""
        try:
            # Use specified model or default model instance
            if model and model != self._model:
                model_instance = self._genai.GenerativeModel(model)
            else:
                model_instance = self._model_instance

            # Configure generation parameters
            generation_config = self._genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
            )

            response = model_instance.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
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

        Note: Gemini has grounding capabilities that could be used here.
        This would require enabling grounding in the API call.
        """
        # TODO: Could implement with Gemini's grounding feature
        return {
            "found": False,
            "description": "",
            "requirements": [],
            "salary_range": None,
            "source_url": None,
            "enrichment_status": "not_supported",
            "error": "Web search enrichment not yet implemented for Gemini provider."
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
def get_gemini_provider(model: Optional[str] = None) -> GeminiProvider:
    """Get Gemini provider instance."""
    config = {'ai': {'model': model}} if model else {}
    return GeminiProvider(config)
