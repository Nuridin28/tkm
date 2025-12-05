"""
Configuration for Telegram Bot
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    
    # Backend API
    API_URL: str = "http://localhost:8000"
    TELEGRAM_BOT_API_KEY: Optional[str] = None  # API key for backend authentication
    
    # OpenAI (optional, если нужен прямой доступ)
    OPENAI_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

