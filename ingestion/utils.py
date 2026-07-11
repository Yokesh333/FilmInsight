"""
utils.py — Shared utilities for the FilmInsight ingestion pipeline.

Provides:
  • Rich-styled console logger
  • Processed-movies registry (read / update / persist)
  • Filesystem helpers
  • Title normalisation for API queries
"""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

# ── Optional Rich pretty-printer ─────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.theme import Theme

    _theme = Theme(
        {
            "info": "bold cyan",
            "success": "bold green",
            "warning": "bold yellow",
            "error": "bold red",
        }
    )
    _console = Console(theme=_theme)

    def _build_rich_logger(name: str) -> logging.Logger:
        handler = RichHandler(
            console=_console,
            show_time=True,
            show_level=True,
            show_path=False,
            markup=True,
        )
        logger = logging.getLogger(name)
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger

    RICH_AVAILABLE = True

except ImportError:  # fall back to stdlib logging
    RICH_AVAILABLE = False
    _console = None  # type: ignore[assignment]

    def _build_rich_logger(name: str) -> logging.Logger:  # type: ignore[misc]
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return logging.getLogger(name)


def get_logger(name: str = "filminsight.ingestion") -> logging.Logger:
    """Return a configured logger instance."""
    return _build_rich_logger(name)


# ─────────────────────────────────────────────────────────────────────────────
# Processed-movies registry
# ─────────────────────────────────────────────────────────────────────────────

def load_processed_movies(filepath: Path) -> dict[str, Any]:
    """
    Load the processed-movies registry from *filepath*.

    Returns a dict of the form::

        {
          "Interstellar": {
            "processed_at": "2025-01-15T10:30:00",
            "chunks_stored": 182,
            "pdf_path": "movie_scripts/Interstellar.pdf"
          },
          ...
        }

    Returns an empty dict if the file does not exist or is malformed.
    """
    if not filepath.exists():
        return {}
    try:
        with filepath.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            return {}
        return data
    except (json.JSONDecodeError, OSError):
        return {}


def save_processed_movies(registry: dict[str, Any], filepath: Path) -> None:
    """Persist the processed-movies registry to *filepath* (atomic write)."""
    tmp = filepath.with_suffix(".tmp")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(registry, fh, indent=2, ensure_ascii=False)
    tmp.replace(filepath)


def mark_movie_processed(
    registry: dict[str, Any],
    movie_name: str,
    filepath: Path,
    chunks_stored: int,
    pdf_path: str,
) -> None:
    """Add / update a movie entry in the registry and save immediately."""
    from datetime import datetime, timezone

    registry[movie_name] = {
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "chunks_stored": chunks_stored,
        "pdf_path": str(pdf_path),
    }
    save_processed_movies(registry, filepath)


# ─────────────────────────────────────────────────────────────────────────────
# Title normalisation
# ─────────────────────────────────────────────────────────────────────────────

def normalise_title(raw_filename: str) -> str:
    """
    Convert a PDF filename to a human-readable movie title suitable for
    API queries.

    Examples
    --------
    >>> normalise_title("500_days_of_summer.pdf")
    '500 Days Of Summer'
    >>> normalise_title("The.Dark.Knight.2008.pdf")
    'The Dark Knight'
    >>> normalise_title("Interstellar (2014).pdf")
    'Interstellar'
    """
    # Strip extension
    stem = Path(raw_filename).stem

    # Remove common parenthetical year patterns like (2008) or [2008]
    stem = re.sub(r"[\(\[]\s*\d{4}\s*[\)\]]", "", stem)

    # Remove trailing standalone 4-digit years
    stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)

    # Replace underscores, dots, and hyphens with spaces
    stem = re.sub(r"[_.\-]+", " ", stem)

    # Collapse multiple spaces
    stem = re.sub(r"\s{2,}", " ", stem).strip()

    # Title-case the result
    return stem.title()


def slugify(text: str) -> str:
    """Return a filesystem-safe slug from *text*."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s-]+", "_", text)


# ─────────────────────────────────────────────────────────────────────────────
# Filesystem helpers
# ─────────────────────────────────────────────────────────────────────────────

def scan_pdf_files(directory: Path) -> list[Path]:
    """
    Return a sorted list of all PDF files in *directory* (non-recursive).
    """
    return sorted(directory.glob("*.pdf"))


def discover_new_pdfs(
    directory: Path, registry: dict[str, Any]
) -> list[tuple[Path, str]]:
    """
    Compare PDFs in *directory* against *registry* and return a list of
    ``(pdf_path, movie_title)`` tuples for movies not yet processed.
    """
    pdfs = scan_pdf_files(directory)
    new: list[tuple[Path, str]] = []
    for pdf in pdfs:
        title = normalise_title(pdf.name)
        if title not in registry:
            new.append((pdf, title))
    return new


def safe_str(value: Any, fallback: str = "N/A") -> str:
    """Return *value* as a stripped string, or *fallback* if falsy."""
    if value is None:
        return fallback
    s = str(value).strip()
    return s if s else fallback
