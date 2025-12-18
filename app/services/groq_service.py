"""
Groq fallback service for transcript cleaning.
Used when both Gemini and OpenAI are rate limited.
Groq has a generous free tier with Llama models.
"""

import time
from typing import List, Optional

from ..config import settings
from ..utils.logger import logger, log_processing_time, log_success, log_error
from .gemini_service import SYSTEM_PROMPT
from ..models.dom_event import format_events_for_prompt


class GroqService:
    """Service for interacting with Groq API as a fallback."""
    
    def __init__(self):
        """Initialize the Groq service."""
        self.api_key = settings.groq_api_key
        self.client = None
        self._initialized = False
        self.model_name = settings.groq_model_name
    
    def initialize(self) -> bool:
        """
        Initialize the Groq client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        if not self.api_key:
            logger.warning("Groq API key not configured - fallback disabled")
            return False
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self._initialized = True
            log_success("Groq service initialized", f"Model: {self.model_name}")
            return True
        except ImportError:
            logger.warning("Groq package not installed - run: pip install groq")
            return False
        except Exception as e:
            log_error("Groq initialization", e)
            return False
    
    def is_available(self) -> bool:
        """Check if Groq is available as a fallback."""
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
        Clean and rewrite a raw transcript using Groq.
        
        Args:
            raw_text: Raw transcript text from speech-to-text
            dom_events: Optional list of DOM events for context
        
        Returns:
            Cleaned instructional script
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Groq service not initialized")
        
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
            
            # Call Groq API (OpenAI-compatible)
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
            
            # Remove common LLM preambles that models sometimes add
            preambles_to_remove = [
                "Here's the polished, professional voiceover text:",
                "Here's the polished professional voiceover text:",
                "Here's the cleaned and polished voiceover text:",
                "Here's the professional voiceover script:",
                "Here is the polished voiceover text:",
                "Here is the cleaned transcript:",
                "Here's the cleaned version:",
                "Here's the rewritten text:",
            ]
            for preamble in preambles_to_remove:
                if cleaned_text.startswith(preamble):
                    cleaned_text = cleaned_text[len(preamble):].strip()
                    break
            
            # Also remove any leading/trailing quotes if present
            if cleaned_text.startswith('"') and cleaned_text.endswith('"'):
                cleaned_text = cleaned_text[1:-1].strip()
            
            duration_ms = (time.time() - start_time) * 1000
            log_processing_time("Groq transcript cleaning", duration_ms)
            log_success(
                "Transcript cleaned (Groq fallback)",
                f"Input: {len(raw_text)} chars → Output: {len(cleaned_text)} chars"
            )
            
            return cleaned_text
            
        except Exception as e:
            log_error("Groq transcript cleaning", e)
            raise RuntimeError(f"Groq fallback failed: {str(e)}")


# Global service instance
groq_service = GroqService()


def clean_transcript_groq(raw_text: str, dom_events: Optional[List] = None) -> str:
    """
    Convenience function to clean a transcript using Groq.
    
    Args:
        raw_text: Raw transcript text
        dom_events: Optional DOM events for context
    
    Returns:
        Cleaned instructional script
    """
    return groq_service.clean_transcript(raw_text, dom_events)
