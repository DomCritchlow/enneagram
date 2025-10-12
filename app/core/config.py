"""
Configuration management for the Enneagram application.
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    
    # Google Sheets Integration
    google_service_account_json: str = Field(default="", description="Google service account JSON (file path or JSON string)")
    google_sheets_id: str = Field(default="", description="Google Sheets spreadsheet ID")
    google_sheets_range: str = Field(default="Sheet1!A:Z", description="Google Sheets range for data")
    google_sheets_scopes: list = Field(default=["https://www.googleapis.com/auth/spreadsheets"], description="Google Sheets API scopes")
    
    # Application
    debug: bool = Field(default=False, description="Debug mode")
    app_title: str = Field(default="Enneagram (Team Use)", description="Application title")
    
    # Production settings
    force_https: bool = Field(default=True, description="Force HTTPS redirects in production")
    
    # File paths
    app_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent, description="Application directory")
    questions_file: str = Field(default="questions.json", description="Questions JSON file name (use 'questions_short.json' for debugging)")
    blurbs_file: str = Field(default="type_blurbs.json", description="Type blurbs JSON file name")
    
    # Security settings
    name_max_length: int = Field(default=100, description="Maximum name length")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    
    @property
    def questions_path(self) -> Path:
        """Get full path to questions file."""
        return self.app_dir / self.questions_file
    
    @property
    def blurbs_path(self) -> Path:
        """Get full path to blurbs file."""
        return self.app_dir / self.blurbs_file
    


# Global settings instance
settings = Settings()
