"""
Configuration settings for Vocala application.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = Field(default="Vocala", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    version: str = Field(default="0.1.0", description="Application version")
    
    # Database settings
    database_url: str = Field(
        description="Database connection URL",
        examples=["postgresql+asyncpg://user:password@localhost:5432/vocala_db"]
    )
    database_echo: bool = Field(default=False, description="SQLAlchemy echo mode")
    
    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Celery settings
    celery_broker_url: str = Field(
        alias="redis_url",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        alias="redis_url", 
        description="Celery result backend URL"
    )
    
    # Telegram Bot settings
    telegram_bot_token: str = Field(
        description="Telegram bot token from BotFather"
    )
    telegram_webhook_url: Optional[str] = Field(
        default=None,
        description="Telegram webhook URL (optional, uses polling if not set)"
    )
    telegram_webhook_secret: Optional[str] = Field(
        default=None,
        description="Telegram webhook secret token"
    )
    
    # LLM API settings
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-3.5-turbo",
        description="OpenAI model to use"
    )
    
    google_ai_api_key: Optional[str] = Field(
        default=None,
        description="Google AI (Gemini) API key"
    )
    google_ai_model: str = Field(
        default="gemini-pro",
        description="Google AI model to use"
    )
    
    # LLM Service settings
    llm_provider: str = Field(
        default="openai",
        description="LLM provider (openai, google, mock)"
    )
    llm_request_timeout: int = Field(
        default=30,
        description="LLM request timeout in seconds"
    )
    llm_max_retries: int = Field(
        default=3,
        description="Maximum LLM request retries"
    )
    
    # Notion integration settings
    notion_api_key: Optional[str] = Field(
        default=None,
        description="Notion integration API key"
    )
    
    # Learning system settings
    daily_word_count: int = Field(
        default=5,
        description="Default number of daily words per user"
    )
    oxford_3000_difficulty: str = Field(
        default="B1_B2",
        description="Oxford 3000 difficulty level"
    )
    srs_intervals: list[int] = Field(
        default=[1, 3, 7, 14, 30, 90],
        description="SRS review intervals in days"
    )
    
    # Security settings
    secret_key: str = Field(
        description="Secret key for JWT tokens and other security purposes"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes"
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Logging format"
    )


# Global settings instance
settings = Settings() 