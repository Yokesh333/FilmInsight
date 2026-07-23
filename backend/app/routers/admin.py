"""
admin.py — FilmInsight Admin Dashboard API.

All data is sourced from PostgreSQL (movie_scripts table).
Chroma vectors are kept in sync with the database:
  • DELETE → removes DB record AND Chroma vectors
  • REINGEST → clears old vectors, marks UPLOADED, triggers IngestionService

No dependency on processed_movies.json.
No subprocess execution.
No hardcoded filesystem paths.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.models.movie_request import MovieRequest
from app.models.movie_script import MovieScript
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])
logger = logging.getLogger(__name__)


# ── RBAC ─────────────────────────────────────────────────────────────────────

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_chroma_collection():
    """Open the shared Chroma collection (same config as IngestionService)."""
    import chromadb
    from chromadb.config import Settings
    from app.core.config import get_settings

    s = get_settings()
    chroma_dir = Path(
        os.environ.get("CHROMA_DB_DIR", "")
        or getattr(s, "CHROMA_DB_DIR", "")
        or _resolve_chroma_dir()
    )
    col_name = (
        os.environ.get("CHROMA_COLLECTION_NAME", "")
        or getattr(s, "CHROMA_COLLECTION_NAME", "filminsight_scripts")
    )
    chroma_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(anonymized_telemetry=False),
    )
    return client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},
    )


def _resolve_chroma_dir() -> str:
    here = Path(__file__).resolve().parent
    for candidate in [here.parent.parent, here.parent.parent.parent]:
        chroma = candidate / "chroma_db"
        if chroma.exists():
            return str(chroma)
    return str(here.parent.parent / "chroma_db")


def _delete_chroma_vectors(movie_name: str) -> int:
    """
    Delete all Chroma vectors for *movie_name*.
    Returns the count that was present before deletion (best-effort).
    Returns -1 if collection not reachable.
    """
    try:
        col = _get_chroma_collection()
        result = col.get(where={"movie_name": movie_name}, limit=1)
        had_vectors = len(result.get("ids", [])) > 0
        col.delete(where={"movie_name": movie_name})
        logger.info(f"[Admin] Deleted Chroma vectors for '{movie_name}' (had_vectors={had_vectors})")
        return 1 if had_vectors else 0
    except Exception as exc:
        logger.warning(f"[Admin] Could not delete Chroma vectors for '{movie_name}': {exc}")
        return -1


def _run_ingestion_background(script_id: int, db_url: str) -> None:
    """
    Background task: marks the script PROCESSING, then runs the canonical
    IngestionService pipeline, updating status to READY or FAILED.
    Uses its own DB session (the request session is long-closed by this point).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.services.ingestion_service import IngestionService, IngestionError

    engine = create_engine(db_url)
    LocalSession = sessionmaker(bind=engine)

    with LocalSession() as db:
        script = db.query(MovieScript).filter(MovieScript.id == script_id).first()
        if not script:
            logger.error(f"[Admin BG] MovieScript id={script_id} not found.")
            return

        title = script.title
        supabase_filename = script.supabase_path
        file_path = script.file_path

        # Mark PROCESSING
        script.status = "PROCESSING"
        db.commit()

    logger.info(f"[Admin BG] Starting re-ingestion for '{title}' (id={script_id})")

    # Resolve local PDF fallback
    local_path: Path | None = None
    if file_path:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        candidate = project_root / "movie_scripts" / file_path
        if candidate.exists():
            local_path = candidate

    try:
        svc = IngestionService()

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
                f"No source PDF found: supabase_path='{supabase_filename}', "
                f"local_path='{local_path}'"
            )

        with LocalSession() as db:
            script = db.query(MovieScript).filter(MovieScript.id == script_id).first()
            if script:
                script.status = "READY"
                script.chunks_stored = chunks
                script.ingested_at = datetime.utcnow()
                script.ingestion_error = None
                db.commit()

        logger.info(f"[Admin BG] '{title}' re-ingested successfully ({chunks} chunks).")

    except Exception as exc:
        error_msg = str(exc)[:1000]
        with LocalSession() as db:
            script = db.query(MovieScript).filter(MovieScript.id == script_id).first()
            if script:
                script.status = "FAILED"
                script.ingestion_error = error_msg
                db.commit()
        logger.error(f"[Admin BG] Re-ingestion failed for '{title}': {error_msg}")


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Dashboard statistics — sourced entirely from PostgreSQL.
    No processed_movies.json dependency.
    """
    total_users    = db.query(User).count()
    total_requests = db.query(MovieRequest).filter(MovieRequest.status == "pending").count()
    total_movies   = db.query(MovieScript).filter(MovieScript.status == "READY").count()

    # Chroma total doc count (best-effort)
    chroma_docs = 0
    try:
        col = _get_chroma_collection()
        chroma_docs = col.count()
    except Exception as exc:
        logger.warning(f"[Admin] Chroma count failed: {exc}")

    return {
        "users":            total_users,
        "movies":           total_movies,
        "pending_requests": total_requests,
        "chat_calls":       0,          # placeholder — extend with analytics table if needed
        "chroma_docs":      chroma_docs,
    }


# ── Movie list ────────────────────────────────────────────────────────────────

@router.get("/movies")
def get_movies(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Full movie list from PostgreSQL, including ingestion status.
    No processed_movies.json dependency.
    """
    scripts = db.query(MovieScript).order_by(MovieScript.uploaded_at.desc()).all()
    return [
        {
            "id":              s.id,
            "title":           s.title,
            "status":          s.status,
            "chunks_stored":   s.chunks_stored,
            "processed_at":    s.ingested_at.isoformat() if s.ingested_at else None,
            "uploaded_at":     s.uploaded_at.isoformat() if s.uploaded_at else None,
            "ingestion_error": s.ingestion_error,
            "supabase_path":   s.supabase_path,
            "file_path":       s.file_path,
            "tmdb_id":         s.tmdb_id,
            "poster_url":      s.poster_url,
        }
        for s in scripts
    ]


# ── Delete movie ──────────────────────────────────────────────────────────────

@router.delete("/movies/{title}")
def delete_movie(
    title: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Delete a movie from both PostgreSQL AND Chroma.
    Never leaves orphan vectors.
    """
    script = db.query(MovieScript).filter(MovieScript.title == title).first()
    if not script:
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found in database.")

    # 1. Delete Chroma vectors first (before DB record is gone)
    _delete_chroma_vectors(title)

    # 2. Delete from Supabase Storage (best-effort — don't fail if missing)
    try:
        from app.services.supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        if script.supabase_path:
            supabase.storage.from_("movie_scripts").remove([script.supabase_path])
            logger.info(f"[Admin] Deleted '{script.supabase_path}' from Supabase storage.")
    except Exception as exc:
        logger.warning(f"[Admin] Supabase storage delete failed (non-fatal): {exc}")

    # 3. Delete from PostgreSQL
    db.delete(script)
    db.commit()

    logger.info(f"[Admin] Movie '{title}' fully deleted (DB + Chroma).")
    return {"status": "success", "message": f"Deleted '{title}' from database and vector store."}


# ── Reingest movie ────────────────────────────────────────────────────────────

@router.post("/movies/{title}/reingest")
def reingest_movie(
    title: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Re-ingest a movie:
      1. Delete existing Chroma vectors (clean slate).
      2. Reset status to UPLOADED.
      3. Trigger IngestionService in the background.

    Safe to call on READY, FAILED, or PROCESSING movies.
    """
    script = db.query(MovieScript).filter(MovieScript.title == title).first()
    if not script:
        raise HTTPException(status_code=404, detail=f"Movie '{title}' not found.")

    # 1. Clear old Chroma vectors
    _delete_chroma_vectors(title)

    # 2. Reset status in PostgreSQL
    script.status          = "UPLOADED"
    script.ingestion_error = None
    script.chunks_stored   = None
    script.ingested_at     = None
    db.commit()
    script_id = script.id

    # 3. Trigger background ingestion
    from app.core.config import get_settings
    settings = get_settings()
    background_tasks.add_task(
        _run_ingestion_background,
        script_id=script_id,
        db_url=settings.DATABASE_URL,
    )

    logger.info(f"[Admin] Re-ingestion triggered for '{title}' (id={script_id}).")
    return {
        "status":  "success",
        "message": f"Re-ingestion started for '{title}'. Status will transition: UPLOADED → PROCESSING → READY.",
    }


# ── Trigger ingestion pipeline ────────────────────────────────────────────────

@router.post("/ingest")
def trigger_ingestion(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    """
    Scan for all movies in UPLOADED or FAILED status and re-ingest them.
    No subprocess execution. No hardcoded paths. Calls IngestionService directly.
    """
    pending = db.query(MovieScript).filter(
        MovieScript.status.in_(["UPLOADED", "FAILED"])
    ).all()

    if not pending:
        return {
            "status":  "ok",
            "message": "No pending movies found (all are PROCESSING or READY).",
            "queued":  0,
        }

    from app.core.config import get_settings
    settings = get_settings()
    queued_titles = []

    for script in pending:
        # Clear old vectors before re-queueing
        _delete_chroma_vectors(script.title)

        # Reset status
        script.status          = "UPLOADED"
        script.ingestion_error = None
        db.commit()

        background_tasks.add_task(
            _run_ingestion_background,
            script_id=script.id,
            db_url=settings.DATABASE_URL,
        )
        queued_titles.append(script.title)

    logger.info(f"[Admin] Bulk ingestion triggered for {len(queued_titles)} movie(s): {queued_titles}")
    return {
        "status":  "success",
        "message": f"Ingestion pipeline triggered for {len(queued_titles)} movie(s).",
        "queued":  len(queued_titles),
        "titles":  queued_titles,
    }


# ── Requests ──────────────────────────────────────────────────────────────────

@router.get("/requests")
def get_requests(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    requests = db.query(MovieRequest).order_by(MovieRequest.requested_at.desc()).all()
    result = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id":         req.id,
            "title":      req.movie_name,
            "status":     req.status,
            "username":   user.username if user else "Unknown",
            "created_at": req.requested_at,
        })
    return result


@router.post("/requests/{req_id}/approve")
def approve_request(
    req_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    req = db.query(MovieRequest).filter(MovieRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "approved"
    db.commit()
    return {"status": "success"}


@router.post("/requests/{req_id}/reject")
def reject_request(
    req_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    req = db.query(MovieRequest).filter(MovieRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "rejected"
    db.commit()
    return {"status": "success"}


# ── TMDB Preview ──────────────────────────────────────────────────────────────

@router.get("/tmdb-preview")
async def get_tmdb_preview(
    url: str,
    admin: User = Depends(get_admin_user),
):
    import re
    from app.services.tmdb import fetch_movie_metadata_by_id

    match = re.search(r"themoviedb\.org/movie/(\d+)", url, re.IGNORECASE)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid TMDB Movie URL.")

    tmdb_id  = int(match.group(1))
    metadata = await fetch_movie_metadata_by_id(tmdb_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Movie not found on TMDB.")

    return metadata
