from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME:    str = "FilmInsight API"
    APP_VERSION: str = "1.0.0"
    DEBUG:       bool = False

    # Flowise
    FLOWISE_URL:         str = "http://localhost:9000"
    FLOWISE_CHATFLOW_ID: str = ""
    FLOWISE_API_KEY:     str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
