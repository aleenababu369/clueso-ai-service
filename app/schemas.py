"""
Pydantic schemas for API request/response validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box coordinates for DOM elements."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    width: float = Field(default=0, description="Element width")
    height: float = Field(default=0, description="Element height")


class DOMEvent(BaseModel):
    """Schema for DOM interaction events."""
    type: str = Field(
        description="Event type: click, input, scroll, etc."
    )
    timestamp: float = Field(
        description="Event timestamp in milliseconds"
    )
    selector: Optional[str] = Field(
        default=None,
        description="CSS selector of the target element"
    )
    bounding_box: Optional[BoundingBox] = Field(
        default=None,
        alias="boundingBox",
        description="Bounding box of the target element"
    )
    target: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Target element information"
    )
    coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Click coordinates"
    )
    viewport: Optional[Dict[str, float]] = Field(
        default=None,
        description="Viewport dimensions"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional event data"
    )

    class Config:
        populate_by_name = True


class AIProcessRequest(BaseModel):
    """Request schema for the /process endpoint."""
    transcript: str = Field(
        description="Raw transcript text from Deepgram"
    )
    dom_events: List[DOMEvent] = Field(
        default=[],
        alias="domEvents",
        description="List of DOM interaction events"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata for future use"
    )
    target_language: str = Field(
        default="en",
        alias="targetLanguage",
        description="Target language for translation (default: en)"
    )

    class Config:
        populate_by_name = True


class AIProcessResponse(BaseModel):
    """Response schema for the /process endpoint."""
    cleaned_script: str = Field(
        alias="cleanedScript",
        description="Cleaned instructional script"
    )
    voiceover_base64: str = Field(
        alias="voiceoverBase64",
        description="Base64-encoded WAV audio"
    )
    success: bool = Field(
        default=True,
        description="Whether the processing was successful"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    """Response schema for health check."""
    status: str = Field(default="ok")
    version: str = Field(default="1.0.0")
    services: Dict[str, bool] = Field(
        default={},
        description="Status of connected services"
    )


class TestVoiceRequest(BaseModel):
    """Request schema for test voice endpoint."""
    text: str = Field(
        description="Text to convert to speech"
    )


class TestVoiceResponse(BaseModel):
    """Response schema for test voice endpoint."""
    audio_base64: str = Field(
        alias="audioBase64",
        description="Base64-encoded audio"
    )
    success: bool = Field(default=True)

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = Field(default=False)
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information (debug mode only)"
    )
