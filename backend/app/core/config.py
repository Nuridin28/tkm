"""
Application configuration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union, Optional
import json


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    DATABASE_URL: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # App
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173"
    
    # SLA
    DEFAULT_SLA_ACCEPT_MINUTES: int = 15
    DEFAULT_SLA_REMOTE_MINUTES: int = 60
    
    # Telegram Bot
    TELEGRAM_BOT_API_KEY: Union[str, None] = None  # API key for Telegram bot authentication
    
    # WhatsApp Bot
    WHATSAPP_BOT_API_KEY: Union[str, None] = None  # API key for WhatsApp bot authentication
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

