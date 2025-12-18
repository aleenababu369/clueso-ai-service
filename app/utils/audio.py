"""
Audio utility functions for handling audio data.
"""

import base64
import os
from pathlib import Path
from typing import Optional

from .logger import logger


def audio_to_base64(audio_bytes: bytes) -> str:
    """
    Convert audio bytes to base64 string.
    
    Args:
        audio_bytes: Raw audio data
    
    Returns:
        Base64-encoded string
    """
    if not audio_bytes:
        logger.warning("Empty audio bytes provided for base64 encoding")
        return ""
    
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    logger.debug(f"Encoded {len(audio_bytes)} bytes to base64 ({len(encoded)} chars)")
    return encoded


def base64_to_audio(base64_string: str) -> bytes:
    """
    Convert base64 string back to audio bytes.
    
    Args:
        base64_string: Base64-encoded audio data
    
    Returns:
        Raw audio bytes
    """
    if not base64_string:
        logger.warning("Empty base64 string provided for decoding")
        return b""
    
    audio_bytes = base64.b64decode(base64_string)
    logger.debug(f"Decoded base64 to {len(audio_bytes)} bytes")
    return audio_bytes


def save_audio_file(
    audio_bytes: bytes,
    file_path: str,
    create_dirs: bool = True
) -> bool:
    """
    Save audio bytes to a file (for debugging/testing).
    
    Args:
        audio_bytes: Raw audio data
        file_path: Path to save the file
        create_dirs: Whether to create parent directories
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if create_dirs:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
        
        logger.info(f"Saved audio file: {file_path} ({len(audio_bytes)} bytes)")
        return True
    except Exception as e:
        logger.error(f"Failed to save audio file: {e}")
        return False


def load_audio_file(file_path: str) -> Optional[bytes]:
    """
    Load audio bytes from a file.
    
    Args:
        file_path: Path to the audio file
    
    Returns:
        Audio bytes or None if failed
    """
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        logger.debug(f"Loaded audio file: {file_path} ({len(audio_bytes)} bytes)")
        return audio_bytes
    except Exception as e:
        logger.error(f"Failed to load audio file: {e}")
        return None


def get_audio_duration_estimate(audio_bytes: bytes, sample_rate: int = 44100) -> float:
    """
    Estimate audio duration from raw bytes.
    Note: This is a rough estimate assuming 16-bit mono PCM.
    
    Args:
        audio_bytes: Raw audio data
        sample_rate: Sample rate in Hz
    
    Returns:
        Estimated duration in seconds
    """
    # Assuming 16-bit (2 bytes) mono audio
    samples = len(audio_bytes) / 2
    duration = samples / sample_rate
    return duration


def validate_audio_bytes(audio_bytes: bytes) -> bool:
    """
    Validate that audio bytes appear to be valid audio data.
    
    Args:
        audio_bytes: Raw audio data to validate
    
    Returns:
        True if appears valid, False otherwise
    """
    if not audio_bytes:
        return False
    
    # Check for common audio file signatures
    # WAV: RIFF....WAVE
    if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
        return True
    
    # MP3: ID3 or 0xFF 0xFB
    if audio_bytes[:3] == b"ID3" or audio_bytes[:2] == b"\xff\xfb":
        return True
    
    # If no signature found, check minimum size (1KB)
    return len(audio_bytes) > 1024
