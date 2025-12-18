"""
Gemini AI service for transcript cleaning and instruction generation.
Uses Google's Generative AI (Gemini) to rewrite transcripts into clean instructions.
"""

import time
from typing import List, Optional
import google.generativeai as genai

import re

from ..config import settings
from ..utils.logger import logger, log_processing_time, log_error, log_success
from ..models.dom_event import format_events_for_prompt


# Patterns to strip preamble/postamble from AI responses
PREAMBLE_PATTERNS = [
    r"^(?:Here(?:'s| is) (?:the |a )?(?:polished|rewritten|cleaned|revised|updated|final|translated|improved)?\s*(?:version of the |version of |the )?(?:script|text|voiceover|transcript|content)[:\s]*\n*)",
    r"^(?:(?:The )?(?:polished|rewritten|cleaned|revised|updated|final|translated|improved)\s+(?:script|text|voiceover|transcript)(?:\s+is)?[:\s]*\n*)",
    r"^(?:Sure[!,.]?\s*(?:Here(?:'s| is)[^:]*:)?\s*\n*)",
    r"^(?:Certainly[!,.]?\s*(?:Here(?:'s| is)[^:]*:)?\s*\n*)",
    r"^(?:Of course[!,.]?\s*(?:Here(?:'s| is)[^:]*:)?\s*\n*)",
    r'^["\']',  # Leading quote
    r'["\']$',  # Trailing quote
]


def strip_preamble(text: str) -> str:
    """
    Remove common AI preamble phrases from the output.
    
    Args:
        text: Raw AI output text
        
    Returns:
        Cleaned text without preamble
    """
    cleaned = text.strip()
    
    # Apply each pattern
    for pattern in PREAMBLE_PATTERNS:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up any remaining leading/trailing whitespace or newlines
    cleaned = cleaned.strip()
    
    # Remove surrounding quotes if present
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    
    return cleaned

 # System prompt for transcript cleaning into voiceover
SYSTEM_PROMPT = """You are an expert voiceover script writer. Your task is to transform 
raw spoken transcripts into polished, professional voiceover scripts.

YOUR GOAL: Clean up what the user SAID into natural, professional voiceover text.

CRITICAL OUTPUT RULES:
- Output ONLY the cleaned script text, nothing else
- Do NOT start with "Here's", "Sure", "Certainly", or any introduction
- Do NOT add any preamble like "Here is the polished script:"
- Do NOT add any closing remarks like "Let me know if you need changes"
- Just output the script directly, as if you ARE the voiceover narrator

CONTENT RULES:
1. Remove filler words (uh, um, so, like, you know, basically, actually, etc.)
2. Fix grammatical errors and awkward phrasing
3. Keep the SAME meaning and message as the original transcript
4. Make it sound natural when read aloud by AI text-to-speech
5. Maintain a friendly, professional tone
6. Keep it concise - don't over-expand or add new information
7. Do NOT add technical instructions or step-by-step guides
8. Do NOT mention DOM elements, CSS selectors, or HTML tags
9. Do NOT generate "click here" or "navigate to" instructions
10. Simply polish what the user said into professional voiceover text

IMPORTANT: The user's spoken words are your ONLY source of content. 
Any DOM event data is for internal timing only - IGNORE it for content.

OUTPUT FORMAT:
- Natural, flowing voiceover text
- No markdown, bullet points, or numbered steps
- Should sound like a professional narrator speaking
- START DIRECTLY with the script content
"""

class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = settings.gemini_api_key
        self.model_name = settings.model_name
        self.model = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the Gemini client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.error("Gemini API key not configured")
            return False
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self._initialized = True
            log_success("Gemini service initialized", f"Model: {self.model_name}")
            return True
        except Exception as e:
            log_error("Gemini initialization", e)
            return False
    
    def clean_transcript(
        self,
        raw_text: str,
        dom_events: Optional[List] = None,
        target_language: str = "en",
        max_retries: int = 1  # Reduced: fast fallback to OpenAI if rate limited
    ) -> str:
        """
        Clean and rewrite a raw transcript into polished instructions.
        
        Args:
            raw_text: Raw transcript text from speech-to-text
            dom_events: Optional list of DOM events for context
            max_retries: Maximum number of retries for rate limiting
        
        Returns:
            Cleaned instructional script
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("Gemini service not initialized")
        
        if not raw_text or not raw_text.strip():
            logger.warning("Empty transcript provided")
            return ""
        
        start_time = time.time()
        
        # Build the prompt - only include the transcript to clean
        # DOM events are NOT included as they were causing the AI to generate
        # tutorial-style instructions instead of just cleaning the voiceover
        # Build the prompt
        if target_language.lower() == "en":
            user_prompt = f"Please clean and rewrite the following spoken transcript into professional voiceover text:\n\n{raw_text}"
        else:
            user_prompt = f"Please clean the following spoken transcript AND translate it to {target_language}. Output ONLY the translated, professional voiceover text:\n\n{raw_text}"
        
        try:
            # Generate response using Gemini (no retries - fail fast to fallback)
            response = self.model.generate_content(
                [
                    {"role": "user", "parts": [SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Understood. I will output only the cleaned voiceover script with no preamble, introduction, or commentary."]},
                    {"role": "user", "parts": [user_prompt]},
                ],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=4096,
                )
            )
            
            # Strip any preamble that the model might add despite instructions
            cleaned_text = strip_preamble(response.text)
            
            duration_ms = (time.time() - start_time) * 1000
            log_processing_time("Gemini transcript cleaning", duration_ms)
            log_success(
                "Transcript cleaned",
                f"Input: {len(raw_text)} chars → Output: {len(cleaned_text)} chars"
            )
            
            return cleaned_text
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                logger.warning(f"Gemini rate limited, will try fallback...")
                raise RuntimeError(f"Rate limit exceeded: {error_str[:200]}")
            else:
                # Non-rate-limit error
                log_error("Gemini transcript cleaning", e)
                raise RuntimeError(f"Failed to clean transcript: {error_str}")
    
    async def clean_transcript_async(
        self,
        raw_text: str,
        dom_events: Optional[List] = None,
        target_language: str = "en"
    ) -> str:
        """
        Async version of clean_transcript.
        Note: google-generativeai doesn't have native async, so this wraps sync.
        
        Args:
            raw_text: Raw transcript text
            dom_events: Optional list of DOM events
        
        Returns:
            Cleaned instructional script
        """
        # For now, call sync version (could use asyncio.to_thread in production)
        return self.clean_transcript(raw_text, dom_events, target_language)
    
    def health_check(self) -> bool:
        """Check if Gemini service is healthy."""
        try:
            if not self._initialized:
                return self.initialize()
            
            # Quick test generation
            response = self.model.generate_content(
                "Say 'OK' if you're working.",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                )
            )
            return bool(response.text)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False


# Global service instance
gemini_service = GeminiService()


def clean_transcript(
    raw_text: str, 
    dom_events: Optional[List] = None,
    target_language: str = "en"
) -> str:
    """
    Convenience function to clean a transcript with automatic fallback.
    
    Fallback chain: Gemini → OpenAI → Groq
    
    Args:
        raw_text: Raw transcript text
        dom_events: Optional DOM events for context
    
    Returns:
        Cleaned instructional script
    """
    # Try Gemini first
    try:
        return gemini_service.clean_transcript(raw_text, dom_events, target_language)
    except RuntimeError as e:
        error_str = str(e).lower()
        if "rate limit" not in error_str and "quota" not in error_str and "429" not in error_str:
            raise  # Non-rate-limit error, don't try fallbacks
        logger.warning("Gemini rate limited, trying fallbacks...")
    
    # Try OpenAI second
    try:
        from .openai_service import openai_service
        if openai_service.is_available():
            return openai_service.clean_transcript(raw_text, dom_events, target_language)
        logger.warning("OpenAI not available (no API key)")
    except Exception as e:
        logger.warning(f"OpenAI failed: {str(e)[:100]}")
    
    # Try Groq third (FREE)
    try:
        from .groq_service import groq_service
        if groq_service.is_available():
            return groq_service.clean_transcript(raw_text, dom_events, target_language)
        logger.warning("Groq not available (no API key)")
    except Exception as e:
        logger.warning(f"Groq failed: {str(e)[:100]}")
    
    # All fallbacks failed
    raise RuntimeError(
        "All AI services unavailable (Gemini, OpenAI, Groq). "
        "Please configure at least one API key in .env:\n"
        "- GROQ_API_KEY (free at console.groq.com)\n"
        "- OPENAI_API_KEY\n"
        "- Or wait for Gemini rate limits to reset."
    )

