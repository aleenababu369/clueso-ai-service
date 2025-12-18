"""
FastAPI AI Service - Main Application
Provides AI-powered transcript cleaning and voiceover generation.
"""

import time
import traceback
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .schemas import (
    AIProcessRequest,
    AIProcessResponse,
    HealthResponse,
    TestVoiceRequest,
    TestVoiceResponse,
    ErrorResponse,
)
from .services import (
    instructions_service,
    process_instruction_pipeline,
    elevenlabs_service,
    generate_voiceover,
)
from .utils import (
    logger,
    log_request,
    log_error,
    audio_to_base64,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - runs on startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Service...")
    logger.info(f"📍 Port: {settings.port}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info("=" * 60)
    
    # Initialize services
    missing_keys = settings.validate_required_keys()
    if missing_keys:
        logger.warning(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
        logger.warning("Some features may not work until keys are configured.")
    else:
        success, errors = instructions_service.initialize()
        if not success:
            for error in errors:
                logger.error(f"❌ {error}")
        else:
            logger.info("✅ All services initialized successfully")
    
    logger.info("=" * 60)
    logger.info("🎉 AI Service is ready!")
    logger.info(f"📖 API Docs: http://localhost:{settings.port}/docs")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down AI Service...")


# Create FastAPI application
app = FastAPI(
    title="Clueso AI Service",
    description="AI-powered transcript cleaning and voiceover generation service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    log_error(f"Unhandled exception on {request.url.path}", exc)
    
    error_detail = None
    if settings.debug:
        error_detail = traceback.format_exc()
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error=str(exc),
            detail=error_detail,
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns service status and connected services health.
    """
    services_health = instructions_service.health_check()
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        services=services_health,
    )


@app.post(
    "/process",
    response_model=AIProcessResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["AI Processing"],
)
async def process_transcript(request: AIProcessRequest):
    """
    Process a transcript through the AI pipeline.
    
    - Cleans the transcript using Google Gemini
    - Generates voiceover audio using ElevenLabs
    - Returns cleaned script and base64-encoded audio
    """
    start_time = time.time()
    
    # Log incoming request
    log_request("/process", len(request.transcript))
    
    # Validate transcript is not empty
    if not request.transcript or not request.transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Transcript cannot be empty",
        )
    
    try:
        # Convert DOM events to list of dicts for processing
        dom_events = [event.model_dump() for event in request.dom_events]
        
        # Run the processing pipeline
        cleaned_script, audio_bytes = process_instruction_pipeline(
            transcript=request.transcript,
            dom_events=dom_events,
            target_language=request.target_language,
        )
        
        # Convert audio to base64
        voiceover_base64 = audio_to_base64(audio_bytes)
        
        duration_ms = (time.time() - start_time) * 1000
        logger.info(f"✅ /process completed in {duration_ms:.2f}ms")
        
        return AIProcessResponse(
            cleanedScript=cleaned_script,
            voiceoverBase64=voiceover_base64,
            success=True,
        )
        
    except Exception as e:
        log_error("/process endpoint", e)
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}",
        )


@app.post(
    "/test-voice",
    response_model=TestVoiceResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    tags=["Testing"],
)
async def test_voice(request: TestVoiceRequest):
    """
    Test endpoint for voiceover generation.
    Generates audio for the provided text.
    """
    log_request("/test-voice", len(request.text))
    
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text cannot be empty",
        )
    
    try:
        audio_bytes = generate_voiceover(request.text)
        audio_base64 = audio_to_base64(audio_bytes)
        
        return TestVoiceResponse(
            audioBase64=audio_base64,
            success=True,
        )
        
    except Exception as e:
        log_error("/test-voice endpoint", e)
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}",
        )


@app.get("/voices", tags=["Testing"])
async def list_voices():
    """
    List available ElevenLabs voices.
    Useful for selecting a voice ID.
    """
    try:
        voices = elevenlabs_service.get_available_voices()
        return {"voices": voices, "count": len(voices)}
    except Exception as e:
        log_error("/voices endpoint", e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch voices: {str(e)}",
        )


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - redirects to docs."""
    return {
        "service": "Clueso AI Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# For running with `python -m app.main`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )
