"""
Instructions service - orchestrates the full AI processing pipeline.
Combines Gemini transcript cleaning with ElevenLabs voiceover generation.
"""

import time
from typing import List, Optional, Tuple

from ..utils.logger import logger, log_processing_time, log_error, log_success
from .gemini_service import gemini_service, clean_transcript
from .elevenlabs_service import elevenlabs_service, generate_voiceover


class InstructionsService:
    """
    Orchestrates the instruction processing pipeline.
    Combines transcript cleaning with voiceover generation.
    """
    
    def __init__(self):
        """Initialize the instructions service."""
        self.gemini = gemini_service
        self.elevenlabs = elevenlabs_service
    
    def initialize(self) -> Tuple[bool, List[str]]:
        """
        Initialize all required services.
        
        Returns:
            Tuple of (success, list of error messages)
        """
        errors = []
        
        if not self.gemini.initialize():
            errors.append("Gemini service failed to initialize")
        
        if not self.elevenlabs.initialize():
            errors.append("ElevenLabs service failed to initialize")
        
        return len(errors) == 0, errors
    
    def process_instruction_pipeline(
        self,
        transcript: str,
        dom_events: Optional[List] = None,
        target_language: str = "en",
        skip_voiceover: bool = False
    ) -> Tuple[str, bytes]:
        """
        Process the full instruction pipeline.
        
        Steps:
        1. Clean the transcript using Gemini
        2. Generate voiceover using ElevenLabs
        
        Args:
            transcript: Raw transcript from Deepgram
            dom_events: Optional list of DOM events for context
            skip_voiceover: If True, skip voiceover generation (for testing)
        
        Returns:
            Tuple of (cleaned_script, audio_bytes)
        """
        start_time = time.time()
        
        logger.info("=" * 50)
        logger.info("Starting instruction processing pipeline")
        logger.info(f"Input transcript length: {len(transcript)} chars")
        logger.info(f"DOM events count: {len(dom_events) if dom_events else 0}")
        logger.info("=" * 50)
        
        # Step 1: Clean the transcript (and translate if needed)
        logger.info(f"Step 1/2: Cleaning transcript with Gemini (Language: {target_language})...")
        try:
            cleaned_script = clean_transcript(transcript, dom_events, target_language)
            logger.info(f"Cleaned script length: {len(cleaned_script)} chars")
        except Exception as e:
            log_error("Transcript cleaning", e)
            raise
        
        # Step 2: Generate voiceover
        if skip_voiceover:
            logger.info("Step 2/2: Skipping voiceover generation (skip_voiceover=True)")
            audio_bytes = b""
        else:
            logger.info("Step 2/2: Generating voiceover with ElevenLabs...")
            try:
                audio_bytes = generate_voiceover(cleaned_script)
                logger.info(f"Generated audio size: {len(audio_bytes)} bytes")
            except Exception as e:
                log_error("Voiceover generation", e)
                raise
        
        total_duration_ms = (time.time() - start_time) * 1000
        log_processing_time("Full instruction pipeline", total_duration_ms)
        
        logger.info("=" * 50)
        log_success(
            "Pipeline completed",
            f"Script: {len(cleaned_script)} chars, Audio: {len(audio_bytes)} bytes"
        )
        logger.info("=" * 50)
        
        return cleaned_script, audio_bytes
    
    async def process_instruction_pipeline_async(
        self,
        transcript: str,
        dom_events: Optional[List] = None,
        target_language: str = "en",
        skip_voiceover: bool = False
    ) -> Tuple[str, bytes]:
        """
        Async version of process_instruction_pipeline.
        
        Args:
            transcript: Raw transcript from Deepgram
            dom_events: Optional list of DOM events
            skip_voiceover: If True, skip voiceover generation
        
        Returns:
            Tuple of (cleaned_script, audio_bytes)
        """
        # For now, call sync version
        # In production, use asyncio.to_thread for true async
        return self.process_instruction_pipeline(transcript, dom_events, target_language, skip_voiceover)
    
    def health_check(self) -> dict:
        """
        Check health of all services.
        
        Returns:
            Dict with service health status
        """
        return {
            "gemini": self.gemini.health_check(),
            "elevenlabs": self.elevenlabs.health_check(),
        }


# Global service instance
instructions_service = InstructionsService()


def process_instruction_pipeline(
    transcript: str,
    dom_events: Optional[List] = None,
    target_language: str = "en"
) -> Tuple[str, bytes]:
    """
    Convenience function to process the instruction pipeline.
    
    Args:
        transcript: Raw transcript text
        dom_events: Optional DOM events for context
    
    Returns:
        Tuple of (cleaned_script, audio_bytes)
    """
    return instructions_service.process_instruction_pipeline(transcript, dom_events, target_language)
