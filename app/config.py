"""
Configuration module for the AI Service.
Loads environment variables and provides a settings object.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API Configuration
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key"
    )
    model_name: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model name to use"
    )
    
    # ElevenLabs API Configuration
    elevenlabs_api_key: str = Field(
        default="",
        description="ElevenLabs API key"
    )
    voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="ElevenLabs voice ID (default: Rachel)"
    )
    
    # OpenAI API Configuration (Fallback)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for fallback when Gemini rate limits"
    )
    openai_model_name: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.)"
    )
    
    # Groq API Configuration (Second Fallback - FREE)
    groq_api_key: str = Field(
        default="",
        description="Groq API key for fallback (free tier available at console.groq.com)"
    )
    groq_model_name: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model to use (llama-3.1-8b-instant, mixtral-8x7b-32768, etc.)"
    )
    
    # Server Configuration
    port: int = Field(
        default=8000,
        description="Server port"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def validate_required_keys(self) -> list[str]:
        """Validate required API keys are set. Returns list of missing keys."""
        missing = []
        if not self.gemini_api_key or self.gemini_api_key == "your_gemini_api_key_here":
            missing.append("GEMINI_API_KEY")
        if not self.elevenlabs_api_key or self.elevenlabs_api_key == "your_elevenlabs_api_key_here":
            missing.append("ELEVENLABS_API_KEY")
        return missing


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
