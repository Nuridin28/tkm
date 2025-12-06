from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):

    TELEGRAM_BOT_TOKEN: str

    API_URL: str = "http://localhost:8000"
    TELEGRAM_BOT_API_KEY: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

