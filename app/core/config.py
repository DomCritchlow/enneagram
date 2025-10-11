"""
Configuration management for the Enneagram application.
"""
import secrets
from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Security
    admin_user: str = Field(default="admin", description="Admin username")
    admin_pass: str = Field(default="change-me-please", description="Admin password")
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32), description="Secret key for sessions")
    
    # Database
    database_url: str = Field(default="sqlite:///app/results.sqlite", description="Database connection URL")
    
    # Application
    debug: bool = Field(default=False, description="Debug mode")
    app_title: str = Field(default="Enneagram (Team Use)", description="Application title")
    
    # Production settings
    force_https: bool = Field(default=True, description="Force HTTPS redirects in production")
    session_timeout: int = Field(default=86400, description="Session timeout in seconds (24 hours)")
    
    # File paths
    app_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent, description="Application directory")
    questions_file: str = Field(default="questions.json", description="Questions JSON file name (use 'questions_short.json' for debugging)")
    blurbs_file: str = Field(default="type_blurbs.json", description="Type blurbs JSON file name")
    
    # Security settings
    password_min_length: int = Field(default=8, description="Minimum password length")
    name_max_length: int = Field(default=100, description="Maximum name length")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @validator('admin_pass')
    def validate_admin_pass(cls, v):
        # Only enforce in production (when debug is False)
        import os
        if os.getenv('DEBUG', 'True').lower() != 'true':
            if v == "change-me-please":
                raise ValueError("Please change the default admin password")
        if len(v) < 8:
            raise ValueError("Admin password must be at least 8 characters")
        return v
    
    @property
    def questions_path(self) -> Path:
        """Get full path to questions file."""
        return self.app_dir / self.questions_file
    
    @property
    def blurbs_path(self) -> Path:
        """Get full path to blurbs file."""
        return self.app_dir / self.blurbs_file
    
    @property
    def database_path(self) -> Path:
        """Get database file path (for SQLite)."""
        if self.database_url.startswith("sqlite:///"):
            db_file = self.database_url.replace("sqlite:///", "")
            return Path(db_file) if db_file.startswith("/") else self.app_dir / db_file
        return None


# Global settings instance
settings = Settings()
