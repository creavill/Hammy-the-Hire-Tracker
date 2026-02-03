"""
Base AI Provider - Abstract base class for AI providers

This module defines the interface for AI providers (Claude, OpenAI, etc.).
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """
    Abstract base class for AI providers.

    Implementations should provide job analysis, cover letter generation,
    and interview answer generation capabilities.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this AI provider."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return the default model to use."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """
        Generate a response from the AI model.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens in response
            model: Model to use (defaults to provider's default)

        Returns:
            Generated text response
        """
        pass

    def filter_and_score(
        self,
        job: Dict,
        resume_text: str,
        location_filter: str,
        experience_level: Dict,
        exclude_keywords: List[str]
    ) -> Tuple[bool, int, str]:
        """
        AI-based job filtering and baseline scoring.

        Args:
            job: Job dictionary
            resume_text: Combined resume text
            location_filter: Location filter prompt
            experience_level: Experience level preferences
            exclude_keywords: Keywords to auto-reject

        Returns:
            Tuple of (should_keep, baseline_score, reason)
        """
        pass

    def analyze_job(self, job: Dict, resume_text: str) -> Dict:
        """
        Perform detailed job qualification analysis.

        Args:
            job: Job dictionary
            resume_text: Combined resume text

        Returns:
            Analysis dictionary with score, strengths, gaps, recommendation
        """
        pass

    def generate_cover_letter(self, job: Dict, resume_text: str) -> str:
        """
        Generate a tailored cover letter.

        Args:
            job: Job dictionary
            resume_text: Combined resume text

        Returns:
            Cover letter text
        """
        pass

    def generate_interview_answer(
        self,
        question: str,
        job: Dict,
        resume_text: str,
        analysis: Dict
    ) -> str:
        """
        Generate an interview answer.

        Args:
            question: Interview question
            job: Job context
            resume_text: Resume content
            analysis: Previous AI analysis

        Returns:
            Interview answer text
        """
        pass
