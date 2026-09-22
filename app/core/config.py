from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Tool Adapter Mode
    TOOL_MODE: Literal["mock", "live", "hybrid"] = "mock"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fintech_user:fintech_secret@localhost:5432/fintech_support"
    SYNC_DATABASE_URL: str = "postgresql://fintech_user:fintech_secret@localhost:5432/fintech_support"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Financial / HITL Business Rules
    # Amounts stored in paise (1 INR = 100 paise)
    REFUND_HITL_THRESHOLD_PAISE: int = 10_000_00  # ₹10,000 in paise

    # LLM Settings (FEAT-001)
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash"

    # External Provider Credentials (Live Mode)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    CORE_BANKING_API_URL: str = ""
    CORE_BANKING_API_KEY: str = ""
    FRESHDESK_DOMAIN: str = ""
    FRESHDESK_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""


settings = Settings()
