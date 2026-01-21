"""
Configuration settings for the SetDB application.

Uses Pydantic Settings to manage environment variables with type validation.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # External APIs
    YOUTUBE_API_KEY: Optional[str] = None
    SOUNDCLOUD_CLIENT_ID: Optional[str] = None
    SOUNDCLOUD_CLIENT_SECRET: Optional[str] = None
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    
    # OAuth Redirect URLs
    SOUNDCLOUD_REDIRECT_URI: Optional[str] = None  # e.g., "http://localhost:5173/auth/soundcloud/callback"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create a single settings instance
settings = Settings()


