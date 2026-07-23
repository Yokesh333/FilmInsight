"""
config.py — Central configuration for the FilmInsight ingestion pipeline.

All tuneable parameters, paths, and API credentials live here.
Import this module in every other ingestion module instead of
hard-coding values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Resolve project root (two levels up from this file) ──────────────────────
_INGESTION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _INGESTION_DIR.parent

# Load .env from project root and backend folder
load_dotenv(PROJECT_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / "backend" / ".env", override=False)

# ─────────────────────────────────────────────────────────────────────────────
# Directory paths
# ─────────────────────────────────────────────────────────────────────────────
MOVIE_SCRIPTS_DIR: Path = PROJECT_ROOT / "movie_scripts"
CHROMA_DB_DIR: Path = Path(
    os.getenv("CHROMA_DB_DIR", str(PROJECT_ROOT / "chroma_db"))
)
PROCESSED_MOVIES_FILE: Path = _INGESTION_DIR / "processed_movies.json"
LOGS_DIR: Path = _INGESTION_DIR / "logs"

# Ensure directories exist at import time
MOVIE_SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# API Keys
# ─────────────────────────────────────────────────────────────────────────────
TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "239967a7888fc811609db5aa3b554431")
OMDB_API_KEY: str = os.getenv("OMDB_API_KEY", "72bf0fb9")

# ─────────────────────────────────────────────────────────────────────────────
# Database & Supabase settings
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/filminsight")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ─────────────────────────────────────────────────────────────────────────────
# TMDb settings
# ─────────────────────────────────────────────────────────────────────────────
TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL: str = "https://image.tmdb.org/t/p/w500"

# ─────────────────────────────────────────────────────────────────────────────
# OMDb settings
# ─────────────────────────────────────────────────────────────────────────────
OMDB_BASE_URL: str = "http://www.omdbapi.com/"

# ─────────────────────────────────────────────────────────────────────────────
# Embedding model
# ─────────────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL_NAME: str = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)
# Device for HuggingFace embeddings: "cpu" | "cuda" | "mps"
EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")

# ─────────────────────────────────────────────────────────────────────────────
# Text chunking
# ─────────────────────────────────────────────────────────────────────────────
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))

# ─────────────────────────────────────────────────────────────────────────────
# Chroma settings
# ─────────────────────────────────────────────────────────────────────────────
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "filminsight_scripts")

# ─────────────────────────────────────────────────────────────────────────────
# Ingestion behaviour
# ─────────────────────────────────────────────────────────────────────────────
# Maximum number of PDF pages to read (None = all pages)
MAX_PAGES: int | None = None

# Batch size for upserting documents into Chroma
CHROMA_BATCH_SIZE: int = int(os.getenv("CHROMA_BATCH_SIZE", "100"))

# HTTP request timeout (seconds)
HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "15"))

# Whether to raise an exception when metadata fetch fails
STRICT_METADATA: bool = os.getenv("STRICT_METADATA", "false").lower() == "true"
