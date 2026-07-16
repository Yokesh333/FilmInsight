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

    # TMDb
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMG_BASE: str = "https://image.tmdb.org/t/p/w500"

    # OMDb
    OMDB_API_KEY: str = ""
    OMDB_BASE_URL: str = "http://www.omdbapi.com"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5000"]

    # ── Knowledge-base paths ──────────────────────────────────────────────────
    # Override via environment variables (set in docker-compose or Jenkinsfile).
    # Defaults work for local development from the project root.
    PROJECT_ROOT:           str = ""           # auto-detected in kb_startup if empty
    MOVIE_SCRIPTS_DIR:      str = ""           # e.g. /data/movie_scripts in Docker
    CHROMA_DB_DIR:          str = ""           # e.g. /data/chroma_db in Docker
    CHROMA_COLLECTION_NAME: str = "filminsight_scripts"

    # ── Authentication & Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/filminsight"
    SECRET_KEY: str = "my-super-secret-jwt-key-replace-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
