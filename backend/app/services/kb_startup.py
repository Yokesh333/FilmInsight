"""
kb_startup.py — Knowledge-base startup logic for FilmInsight.

Called during the FastAPI lifespan to detect whether a Chroma database
already exists, trigger automatic ingestion if movie_scripts are available,
or emit a warning if neither is present.

Decision tree
─────────────
  chroma_db/ exists and is populated
      → Use existing database. Log summary.

  chroma_db/ missing or empty, but movie_scripts/ has PDFs
      → Run ingestion/ingest_movies.py as a subprocess.
      → Block startup until ingestion completes.
      → Continue.

  Neither present
      → Start normally.
      → Log a clear WARNING: "No movie scripts found. The knowledge base is empty."

The application NEVER crashes due to a missing knowledge base.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("filminsight.kb_startup")

# ── Resolve paths relative to project root ────────────────────────────────────
# Supports both local dev (project root two levels above this file's location)
# and Docker (PROJECT_ROOT env var explicitly set in Compose / Dockerfile).

_PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "")).resolve()

# Fallback: walk up from this file's location until we find ingestion/
if not _PROJECT_ROOT or not (_PROJECT_ROOT / "ingestion").exists():
    _here = Path(__file__).resolve().parent  # backend/app/services/
    for candidate in [_here.parent.parent, _here.parent.parent.parent]:
        if (candidate / "ingestion").exists():
            _PROJECT_ROOT = candidate
            break

CHROMA_DB_DIR: Path = Path(
    os.environ.get("CHROMA_DB_DIR", str(_PROJECT_ROOT / "chroma_db"))
)
MOVIE_SCRIPTS_DIR: Path = Path(
    os.environ.get("MOVIE_SCRIPTS_DIR", str(_PROJECT_ROOT / "movie_scripts"))
)
INGEST_SCRIPT: Path = _PROJECT_ROOT / "ingestion" / "ingest_movies.py"


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def initialise_knowledge_base() -> KBState:
    """
    Inspect the environment and take the appropriate action.

    Returns a :class:`KBState` describing what happened, which is stored
    on the FastAPI app state for use by the ``/health`` endpoint.
    """
    logger.info("  Checking knowledge-base state...")
    logger.info(f"  CHROMA_DB_DIR    : {CHROMA_DB_DIR}")
    logger.info(f"  MOVIE_SCRIPTS_DIR: {MOVIE_SCRIPTS_DIR}")

    # ── Case 1: Chroma DB already exists and is non-empty ────────────────────
    if _chroma_is_populated():
        doc_count = _chroma_doc_count()
        msg = (
            f"Existing Chroma database found "
            f"({doc_count:,} document(s)). Skipping ingestion."
        )
        logger.info(f"  ✅  {msg}")
        return KBState(status="ready", message=msg, doc_count=doc_count)

    # ── Case 2: No DB yet, but PDFs are available → run ingestion ────────────
    pdf_files = _list_pdfs()
    if pdf_files:
        logger.info(
            f"  ⚙️   No Chroma DB found. "
            f"Found {len(pdf_files)} PDF(s) in {MOVIE_SCRIPTS_DIR}."
        )
        logger.info("  ⚙️   Running ingestion pipeline. This may take several minutes...")
        success, error_msg = _run_ingestion()
        if success:
            doc_count = _chroma_doc_count()
            msg = (
                f"Ingestion completed successfully. "
                f"{len(pdf_files)} movie(s) processed, "
                f"{doc_count:,} chunks stored."
            )
            logger.info(f"  ✅  {msg}")
            return KBState(status="ready", message=msg, doc_count=doc_count)
        else:
            msg = f"Ingestion failed: {error_msg}. Starting with empty knowledge base."
            logger.error(f"  ❌  {msg}")
            return KBState(status="error", message=msg, doc_count=0)

    # ── Case 3: Nothing available → warn and continue ─────────────────────────
    msg = (
        "No movie scripts found. The knowledge base is empty. "
        "Add screenplay PDFs to the movie_scripts/ folder and "
        "run: python -m ingestion.ingest_movies"
    )
    logger.warning("  " + "=" * 58)
    logger.warning(f"  ⚠️   WARNING: {msg}")
    logger.warning("  " + "=" * 58)
    return KBState(status="empty", message=msg, doc_count=0)


# ─────────────────────────────────────────────────────────────────────────────
# State dataclass
# ─────────────────────────────────────────────────────────────────────────────

class KBState:
    """Immutable record of the knowledge-base initialisation outcome."""

    __slots__ = ("status", "message", "doc_count")

    def __init__(self, status: str, message: str, doc_count: int) -> None:
        # status: "ready" | "empty" | "error"
        self.status = status
        self.message = message
        self.doc_count = doc_count

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "doc_count": self.doc_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _chroma_is_populated() -> bool:
    """Return True if the Chroma DB directory exists and contains data."""
    if not CHROMA_DB_DIR.exists():
        return False
    # A populated Chroma store has at least a chroma.sqlite3 file
    sqlite_files = list(CHROMA_DB_DIR.glob("*.sqlite3"))
    segment_dirs = [
        p for p in CHROMA_DB_DIR.rglob("*") if p.is_dir() and p != CHROMA_DB_DIR
    ]
    return bool(sqlite_files or segment_dirs)


def _chroma_doc_count() -> int:
    """Attempt to count documents in the Chroma collection; return 0 on error."""
    try:
        import chromadb
        from chromadb.config import Settings

        chroma_collection = os.environ.get(
            "CHROMA_COLLECTION_NAME", "filminsight_scripts"
        )
        client = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        col = client.get_or_create_collection(chroma_collection)
        return col.count()
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Could not count Chroma docs: {exc}")
        return 0


def _list_pdfs() -> list[Path]:
    """Return all PDF files in MOVIE_SCRIPTS_DIR (non-recursive)."""
    if not MOVIE_SCRIPTS_DIR.exists():
        return []
    return sorted(MOVIE_SCRIPTS_DIR.glob("*.pdf"))


def _run_ingestion() -> tuple[bool, str]:
    """
    Execute the ingestion script as a subprocess.

    Returns ``(True, "")`` on success or ``(False, error_message)`` on failure.
    """
    if not INGEST_SCRIPT.exists():
        return False, f"Ingestion script not found at {INGEST_SCRIPT}"

    env = os.environ.copy()
    env["PROJECT_ROOT"] = str(_PROJECT_ROOT)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ingestion.ingest_movies"],
            cwd=str(_PROJECT_ROOT),
            env=env,
            check=False,        # we handle non-zero exit ourselves
            capture_output=False,  # let output flow to the container logs
            timeout=3600,       # 1-hour hard limit
        )
        if result.returncode == 0:
            return True, ""
        return False, f"Ingestion exited with code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "Ingestion timed out after 1 hour"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
