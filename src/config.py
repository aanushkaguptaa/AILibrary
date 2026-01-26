from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    groq_api_key: str
    
    host: str = "0.0.0.0"
    port: int = 8000
    
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    mongodb_uri: str = ""
    mongodb_db_name: str = "ai_library"
    
    app_name: str = "AI Library"
    debug: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()