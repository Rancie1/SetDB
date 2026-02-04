"""
Configuration settings for the SetDB application.

Uses Pydantic Settings to manage environment variables with type validation.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import Optional
from urllib.parse import urlparse


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Environment detection
    ENVIRONMENT: str = "development"  # Can be "development" or "production"
    
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
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # OAuth Redirect URLs
    SOUNDCLOUD_REDIRECT_URI: Optional[str] = None  # e.g., "http://localhost:5173/auth/soundcloud/callback"
    GOOGLE_REDIRECT_URI: Optional[str] = None  # e.g., "http://localhost:5173/auth/google/callback"
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )
    
    @field_validator('GOOGLE_REDIRECT_URI')
    @classmethod
    def validate_google_redirect_uri(cls, v, info):
        """Validate Google OAuth redirect URI based on environment."""
        if v is None:
            return v
            
        try:
            parsed = urlparse(v)
            environment = info.data.get('ENVIRONMENT', 'development')
            
            # In production, enforce HTTPS
            if environment == 'production':
                if parsed.scheme != 'https':
                    raise ValueError(
                        f"Google OAuth redirect URI must use HTTPS in production environment. "
                        f"Got: {parsed.scheme}://{parsed.netloc}{parsed.path}"
                    )
            
            # In development, allow localhost with HTTP
            elif environment == 'development':
                if parsed.scheme not in ['http', 'https']:
                    raise ValueError(
                        f"Google OAuth redirect URI must use HTTP or HTTPS. "
                        f"Got: {parsed.scheme}://{parsed.netloc}{parsed.path}"
                    )
                
                # Allow localhost and 127.0.0.1 in development
                if parsed.scheme == 'http' and parsed.hostname not in ['localhost', '127.0.0.1']:
                    raise ValueError(
                        f"HTTP redirect URIs are only allowed for localhost in development. "
                        f"Got: {parsed.hostname}. Use HTTPS for other domains."
                    )
            
            return v
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Invalid Google OAuth redirect URI format: {v}")
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is either development or production."""
        if v not in ['development', 'production']:
            raise ValueError(f"ENVIRONMENT must be 'development' or 'production', got: {v}")
        return v
    
    def is_google_oauth_configured(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(
            self.GOOGLE_CLIENT_ID and 
            self.GOOGLE_CLIENT_SECRET and 
            self.GOOGLE_REDIRECT_URI
        )
    
    def validate_google_oauth_config(self) -> tuple[bool, list[str]]:
        """
        Validate Google OAuth configuration and return status with error messages.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID environment variable is required")
        
        if not self.GOOGLE_CLIENT_SECRET:
            errors.append("GOOGLE_CLIENT_SECRET environment variable is required")
        
        if not self.GOOGLE_REDIRECT_URI:
            errors.append("GOOGLE_REDIRECT_URI environment variable is required")
        else:
            # Validate redirect URI format and security
            try:
                parsed = urlparse(self.GOOGLE_REDIRECT_URI)
                
                if self.ENVIRONMENT == 'production':
                    if parsed.scheme != 'https':
                        errors.append(
                            f"Google OAuth redirect URI must use HTTPS in production. "
                            f"Current URI: {self.GOOGLE_REDIRECT_URI}"
                        )
                elif self.ENVIRONMENT == 'development':
                    if parsed.scheme not in ['http', 'https']:
                        errors.append(
                            f"Google OAuth redirect URI must use HTTP or HTTPS. "
                            f"Current URI: {self.GOOGLE_REDIRECT_URI}"
                        )
                    
                    if parsed.scheme == 'http' and parsed.hostname not in ['localhost', '127.0.0.1']:
                        errors.append(
                            f"HTTP redirect URIs are only allowed for localhost in development. "
                            f"Current hostname: {parsed.hostname}. Use HTTPS for other domains."
                        )
                        
            except Exception as e:
                errors.append(f"Invalid Google OAuth redirect URI format: {self.GOOGLE_REDIRECT_URI}")
        
        return len(errors) == 0, errors


# Create a single settings instance
settings = Settings()


