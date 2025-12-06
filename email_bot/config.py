from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):

    EMAIL_IMAP_SERVER: str = "imap.gmail.com"
    EMAIL_IMAP_PORT: int = 993
    EMAIL_SMTP_SERVER: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_FROM_NAME: str = "Казахтелеком Help Desk"

    CHECK_INTERVAL: int = 60
    PROCESSED_EMAILS_DB: str = "processed_emails.db"

    API_URL: str = "http://localhost:8000"
    EMAIL_BOT_API_KEY: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

