from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME:    str = "FilmInsight API"
    APP_VERSION: str = "2.0.0"
    DEBUG:       bool = False

    # ── Groq LLM ─────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL:   str = "llama-3.3-70b-versatile"

    # ── HuggingFace Embeddings ────────────────────────────────────────────────
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE:     str = "cpu"   # "cpu" | "cuda" | "mps"

    # ── Chroma Vector Store ───────────────────────────────────────────────────
    CHROMA_DB_DIR:          str = ""                  # auto-detected if empty
    CHROMA_COLLECTION_NAME: str = "filminsight_scripts"
    CHROMA_BATCH_SIZE:      int = 100

    # ── Text Chunking ─────────────────────────────────────────────────────────
    CHUNK_SIZE:    int = 800
    CHUNK_OVERLAP: int = 150

    # ── TMDb ─────────────────────────────────────────────────────────────────
    TMDB_API_KEY:  str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMG_BASE: str = "https://image.tmdb.org/t/p/w500"

    # ── OMDb ─────────────────────────────────────────────────────────────────
    OMDB_API_KEY:  str = ""
    OMDB_BASE_URL: str = "http://www.omdbapi.com"

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5000"]

    # ── Knowledge-base paths ──────────────────────────────────────────────────
    # Override via environment variables (set in docker-compose or Jenkinsfile).
    # Defaults work for local development from the project root.
    PROJECT_ROOT:      str = ""   # auto-detected in kb_startup if empty
    MOVIE_SCRIPTS_DIR: str = ""   # e.g. /data/movie_scripts in Docker

    # ── Authentication & Database ─────────────────────────────────────────────
    DATABASE_URL:                str = "postgresql://postgres:postgres@localhost:5432/filminsight"
    SECRET_KEY:                  str = "my-super-secret-jwt-key-replace-in-production"
    ALGORITHM:                   str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL:              str = ""
    SUPABASE_ANON_KEY:         str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Legacy Flowise (kept for reference only — NOT used by any pipeline) ──
    # These fields are intentionally left here so existing .env files with
    # FLOWISE_* keys do not cause a validation error.
    FLOWISE_URL:         str = ""
    FLOWISE_CHATFLOW_ID: str = ""
    FLOWISE_API_KEY:     str = ""

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = True
        extra             = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
