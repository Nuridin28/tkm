"""
Configuration for Email Bot
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Email Configuration
    EMAIL_IMAP_SERVER: str = "imap.gmail.com"
    EMAIL_IMAP_PORT: int = 993
    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str  # Email address to send from
    EMAIL_FROM_NAME: str = "Казахтелеком Help Desk"
    
    # Email Processing
    CHECK_INTERVAL: int = 60  # Check for new emails every N seconds
    PROCESSED_EMAILS_DB: str = "processed_emails.db"  # SQLite DB for tracking processed emails
    
    # Backend API
    API_URL: str = "http://localhost:8000"
    EMAIL_BOT_API_KEY: Optional[str] = None  # API key for backend authentication
    
    # OpenAI (optional, если нужен прямой доступ)
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

