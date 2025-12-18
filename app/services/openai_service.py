"""
OpenAI fallback service for transcript cleaning.
Used when Gemini rate limits are exceeded.
"""

import time
from typing import List, Optional

from ..config import settings
from ..utils.logger import logger, log_processing_time, log_success, log_error
from .gemini_service import SYSTEM_PROMPT
from ..models.dom_event import format_events_for_prompt


class OpenAIService:
    """Service for interacting with OpenAI API as a fallback."""
    
    def __init__(self):
        """Initialize the OpenAI service."""
        self.api_key = settings.openai_api_key
        self.client = None
        self._initialized = False
        self.model_name = settings.openai_model_name
    
    def initialize(self) -> bool:
        """
        Initialize the OpenAI client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured - fallback disabled")
            return False
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self._initialized = True
            log_success("OpenAI service initialized", f"Model: {self.model_name}")
            return True
        except ImportError:
            logger.warning("OpenAI package not installed - run: pip install openai")
            return False
        except Exception as e:
            log_error("OpenAI initialization", e)
            return False
    
    def is_available(self) -> bool:
        """Check if OpenAI is available as a fallback."""
        if not self.api_key:
            return False
        if not self._initialized:
            return self.initialize()
        return self._initialized
    
    def clean_transcript(
        self,
        raw_text: str,
        dom_events: Optional[List] = None,
        target_language: str = "en"
    ) -> str:
        """
        Clean and rewrite a raw transcript using OpenAI.
        
        Args:
            raw_text: Raw transcript text from speech-to-text
            dom_events: Optional list of DOM events for context
        
        Returns:
            Cleaned instructional script
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("OpenAI service not initialized")
        
        if not raw_text or not raw_text.strip():
            logger.warning("Empty transcript provided")
            return ""
        
        start_time = time.time()
        
        try:
            # Build the prompt
            if target_language.lower() == "en":
                user_prompt = f"Please clean and rewrite the following spoken transcript into professional voiceover text:\n\n{raw_text}"
            else:
                user_prompt = f"Please clean the following spoken transcript AND translate it to {target_language}. Output ONLY the translated, professional voiceover text:\n\n{raw_text}"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            
            duration_ms = (time.time() - start_time) * 1000
            log_processing_time("OpenAI transcript cleaning", duration_ms)
            log_success(
                "Transcript cleaned (OpenAI fallback)",
                f"Input: {len(raw_text)} chars → Output: {len(cleaned_text)} chars"
            )
            
            return cleaned_text
            
        except Exception as e:
            log_error("OpenAI transcript cleaning", e)
            raise RuntimeError(f"OpenAI fallback failed: {str(e)}")


# Global service instance
openai_service = OpenAIService()


def clean_transcript_openai(raw_text: str, dom_events: Optional[List] = None) -> str:
    """
    Convenience function to clean a transcript using OpenAI.
    
    Args:
        raw_text: Raw transcript text
        dom_events: Optional DOM events for context
    
    Returns:
        Cleaned instructional script
    """
    return openai_service.clean_transcript(raw_text, dom_events)
