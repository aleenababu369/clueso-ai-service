"""
ElevenLabs service for text-to-speech voiceover generation.
Uses ElevenLabs API to generate high-quality AI voiceovers.
"""

import time
from typing import Optional
from elevenlabs import ElevenLabs, VoiceSettings

from ..config import settings
from ..utils.logger import logger, log_processing_time, log_error, log_success


class ElevenLabsService:
    """Service for interacting with ElevenLabs TTS API."""
    
    def __init__(self):
        """Initialize the ElevenLabs service."""
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.voice_id
        self.client = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the ElevenLabs client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._initialized:
            return True
        
        if not self.api_key or self.api_key == "your_elevenlabs_api_key_here":
            logger.error("ElevenLabs API key not configured")
            return False
        
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            self._initialized = True
            log_success("ElevenLabs service initialized", f"Voice ID: {self.voice_id}")
            return True
        except Exception as e:
            log_error("ElevenLabs initialization", e)
            return False
    
    def generate_voiceover(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2"  # Updated: better for translation
    ) -> bytes:
        """
        Generate voiceover audio from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID override
            model_id: ElevenLabs model to use
        
        Returns:
            Raw audio bytes (MP3 format)
        """
        if not self._initialized:
            if not self.initialize():
                raise RuntimeError("ElevenLabs service not initialized")
        
        if not text or not text.strip():
            logger.warning("Empty text provided for voiceover")
            return b""
        
        start_time = time.time()
        voice = voice_id or self.voice_id
        
        try:
            logger.info(f"Generating voiceover: {len(text)} chars with voice {voice}")
            
            # Generate audio using ElevenLabs
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice,
                text=text,
                model_id=model_id,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True,
                )
            )
            
            # Collect audio bytes from generator
            audio_chunks = []
            for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            audio_bytes = b"".join(audio_chunks)
            
            duration_ms = (time.time() - start_time) * 1000
            log_processing_time("ElevenLabs voiceover generation", duration_ms)
            log_success(
                "Voiceover generated",
                f"Text: {len(text)} chars → Audio: {len(audio_bytes)} bytes"
            )
            
            return audio_bytes
            
        except Exception as e:
            log_error("ElevenLabs voiceover generation", e)
            raise RuntimeError(f"Failed to generate voiceover: {str(e)}")
    
    async def generate_voiceover_async(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: str = "eleven_multilingual_v2"  # Updated: better for translation
    ) -> bytes:
        """
        Async version of generate_voiceover.
        Note: elevenlabs SDK doesn't have native async, so this wraps sync.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID override
            model_id: ElevenLabs model to use
        
        Returns:
            Raw audio bytes
        """
        # For now, call sync version (could use asyncio.to_thread in production)
        return self.generate_voiceover(text, voice_id, model_id)
    
    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            voices = self.client.voices.get_all()
            return [
                {"id": v.voice_id, "name": v.name}
                for v in voices.voices
            ]
        except Exception as e:
            log_error("Get available voices", e)
            return []
    
    def health_check(self) -> bool:
        """Check if ElevenLabs service is healthy."""
        try:
            if not self._initialized:
                return self.initialize()
            
            # Check if we can fetch voices (lightweight API call)
            voices = self.client.voices.get_all()
            return len(voices.voices) > 0
        except Exception as e:
            logger.warning(f"ElevenLabs health check failed: {e}")
            return False


# Global service instance
elevenlabs_service = ElevenLabsService()


def generate_voiceover(text: str) -> bytes:
    """
    Convenience function to generate voiceover audio.
    
    Args:
        text: Text to convert to speech
    
    Returns:
        Raw audio bytes
    """
    return elevenlabs_service.generate_voiceover(text)
