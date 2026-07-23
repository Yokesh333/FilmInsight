"""
kb_startup.py — Knowledge-base startup logic for FilmInsight.

Called during the FastAPI lifespan to:
  1. Reset stale PROCESSING records (crash recovery).
  2. Check Chroma DB state.
  3. If Chroma is empty but movies in DB have PDFs, trigger ingestion directly
     via IngestionService (no subprocess, no hardcoded paths).
  4. Log clear warnings if no knowledge base is available.

The application NEVER crashes due to a missing knowledge base.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("filminsight.kb_startup")

# ── Resolve project root ───────────────────────────────────────────────────────
_PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "")).resolve()

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


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def initialise_knowledge_base() -> "KBState":
    """
    Inspect the environment and take the appropriate action.

    Steps:
      1. Recover stale PROCESSING records in PostgreSQL.
      2. If Chroma is already populated → use it.
      3. If Chroma empty but DB has UPLOADED/FAILED movies → re-ingest via IngestionService.
      4. If Chroma empty and no DB movies → warn and continue.

    Returns a :class:`KBState` describing what happened.
    """
    logger.info("  Checking knowledge-base state...")
    logger.info(f"  CHROMA_DB_DIR    : {CHROMA_DB_DIR}")
    logger.info(f"  MOVIE_SCRIPTS_DIR: {MOVIE_SCRIPTS_DIR}")

    # ── Step 1: Crash recovery — reset stale PROCESSING records ─────────────
    _reset_stale_processing()

    # ── Step 2: Chroma already populated ────────────────────────────────────
    if _chroma_is_populated():
        doc_count = _chroma_doc_count()
        msg = (
            f"Existing Chroma database found "
            f"({doc_count:,} document(s)). Skipping ingestion."
        )
        logger.info(f"  ✅  {msg}")
        return KBState(status="ready", message=msg, doc_count=doc_count)

    # ── Step 3: Chroma empty — look for pending movies in PostgreSQL ─────────
    pending_scripts = _get_pending_scripts()
    if pending_scripts:
        logger.info(
            f"  ⚙️   No Chroma DB found. "
            f"Found {len(pending_scripts)} pending movie(s) in PostgreSQL."
        )
        logger.info("  ⚙️   Running ingestion pipeline via IngestionService...")
        success_count, failure_count = _run_ingestion_for_scripts(pending_scripts)
        doc_count = _chroma_doc_count()
        msg = (
            f"Startup ingestion completed. "
            f"{success_count} succeeded, {failure_count} failed. "
            f"{doc_count:,} chunks in Chroma."
        )
        if success_count > 0:
            logger.info(f"  ✅  {msg}")
            return KBState(status="ready", message=msg, doc_count=doc_count)
        else:
            logger.error(f"  ❌  {msg}")
            return KBState(status="error", message=msg, doc_count=0)

    # ── Step 4: No Chroma, no DB movies — check local PDFs as last resort ────
    pdf_files = _list_pdfs()
    if pdf_files:
        logger.info(
            f"  ⚙️   No Chroma DB or DB movies found. "
            f"Found {len(pdf_files)} PDF(s) in {MOVIE_SCRIPTS_DIR}. "
            "Add them via the Admin Dashboard to ingest."
        )

    msg = (
        "No knowledge base found. The system is ready to accept uploads "
        "via the Admin Dashboard. Movies will be indexed automatically after upload."
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
        self.status    = status
        self.message   = message
        self.doc_count = doc_count

    def to_dict(self) -> dict:
        return {
            "status":    self.status,
            "message":   self.message,
            "doc_count": self.doc_count,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _reset_stale_processing() -> None:
    """
    Find movies stuck in PROCESSING status from a previous server crash
    and reset them to UPLOADED so they can be re-ingested.
    """
    try:
        from app.db.database import SessionLocal
        from app.models.movie_script import MovieScript

        with SessionLocal() as db:
            stale = db.query(MovieScript).filter(
                MovieScript.status == "PROCESSING"
            ).all()
            if not stale:
                return
            for s in stale:
                logger.warning(
                    f"  ⚠️   Resetting stale PROCESSING → UPLOADED: '{s.title}'"
                )
                s.status = "UPLOADED"
            db.commit()
            logger.info(f"  Crash recovery: reset {len(stale)} stale PROCESSING record(s).")
    except Exception as exc:
        logger.warning(f"  Crash recovery failed (non-fatal): {exc}")


def _get_pending_scripts() -> list:
    """Return all MovieScript records with UPLOADED or FAILED status."""
    try:
        from app.db.database import SessionLocal
        from app.models.movie_script import MovieScript

        with SessionLocal() as db:
            return db.query(MovieScript).filter(
                MovieScript.status.in_(["UPLOADED", "FAILED"])
            ).all()
    except Exception as exc:
        logger.warning(f"  Could not query pending scripts: {exc}")
        return []


def _run_ingestion_for_scripts(scripts: list) -> tuple[int, int]:
    """
    Directly call IngestionService for each pending script.
    Returns (success_count, failure_count).
    """
    from app.services.ingestion_service import IngestionService, IngestionError
    from app.db.database import SessionLocal
    from app.models.movie_script import MovieScript

    svc = IngestionService()
    success_count = 0
    failure_count = 0

    for script in scripts:
        title     = script.title
        script_id = script.id
        supabase_filename = script.supabase_path
        local_path_candidate = MOVIE_SCRIPTS_DIR / (script.file_path or f"{title}.pdf")
        local_path = local_path_candidate if local_path_candidate.exists() else None

        logger.info(f"  ⚙️   Ingesting '{title}' (id={script_id})...")

        # Mark PROCESSING
        try:
            with SessionLocal() as db:
                s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
                if s:
                    s.status = "PROCESSING"
                    db.commit()
        except Exception as exc:
            logger.warning(f"  Could not mark PROCESSING for '{title}': {exc}")

        try:
            if supabase_filename:
                chunks = svc.ingest_movie(
                    movie_name=title,
                    movie_id=script_id,
                    supabase_filename=supabase_filename,
                )
            elif local_path:
                chunks = svc.ingest_movie(
                    movie_name=title,
                    movie_id=script_id,
                    local_pdf_path=local_path,
                )
            else:
                raise IngestionError(
                    f"No PDF source: supabase_path='{supabase_filename}', "
                    f"local='{local_path_candidate}' not found."
                )

            with SessionLocal() as db:
                s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
                if s:
                    s.status          = "READY"
                    s.chunks_stored   = chunks
                    s.ingested_at     = datetime.utcnow()
                    s.ingestion_error = None
                    db.commit()

            logger.info(f"  ✅  '{title}' ingested ({chunks} chunks).")
            success_count += 1

        except Exception as exc:
            error_msg = str(exc)[:1000]
            try:
                with SessionLocal() as db:
                    s = db.query(MovieScript).filter(MovieScript.id == script_id).first()
                    if s:
                        s.status          = "FAILED"
                        s.ingestion_error = error_msg
                        db.commit()
            except Exception:
                pass
            logger.error(f"  ❌  Ingestion failed for '{title}': {error_msg}")
            failure_count += 1

    return success_count, failure_count


def _chroma_is_populated() -> bool:
    """Return True if the Chroma DB directory exists and contains data."""
    if not CHROMA_DB_DIR.exists():
        return False
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

        col_name = os.environ.get("CHROMA_COLLECTION_NAME", "filminsight_scripts")
        client   = chromadb.PersistentClient(
            path=str(CHROMA_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        col = client.get_or_create_collection(col_name)
        return col.count()
    except Exception as exc:
        logger.debug(f"Could not count Chroma docs: {exc}")
        return 0


def _list_pdfs() -> list[Path]:
    """Return all PDF files in MOVIE_SCRIPTS_DIR (non-recursive)."""
    if not MOVIE_SCRIPTS_DIR.exists():
        return []
    return sorted(MOVIE_SCRIPTS_DIR.glob("*.pdf"))
