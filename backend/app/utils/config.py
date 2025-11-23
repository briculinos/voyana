"""
Configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    openai_api_key: str
    anthropic_api_key: str
    langsmith_api_key: str = ""

    # Amadeus
    amadeus_api_key: str
    amadeus_api_secret: str

    # SerpAPI (Google Flights scraper)
    serpapi_key: str = ""

    # Hotels API
    booking_com_api_key: str = ""
    hotelbeds_api_key: str = ""
    hotelbeds_api_secret: str = ""

    # Database
    database_url: str = "sqlite:///./voyana.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App Settings
    environment: str = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production-please"
    allowed_origins: Union[List[str], str] = "http://localhost:3000"

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_project: str = "travel-concierge"

    @field_validator('allowed_origins', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated string into list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
