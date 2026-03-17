"""Configuration management for Glaze backend."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google OAuth
    google_client_id: str = Field(..., env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/auth/callback",
        env="GOOGLE_REDIRECT_URI"
    )
    
    # Google Gemini API
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    
    # Backend Configuration
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def __repr__(self) -> str:
        """Safe representation without sensitive data."""
        return (
            f"Settings(google_client_id='***', "
            f"qdrant_host='{self.qdrant_host}', "
            f"qdrant_port={self.qdrant_port}, "
            f"environment='{self.environment}')"
        )


def load_settings() -> Settings:
    """Load and validate settings from environment variables."""
    try:
        settings = Settings()
        return settings
    except Exception as e:
        raise ValueError(
            f"Failed to load configuration. Please ensure all required "
            f"environment variables are set. Error: {str(e)}"
        )


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global settings
    if settings is None:
        settings = load_settings()
    return settings
