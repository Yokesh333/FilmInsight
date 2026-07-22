"""
upload.py — FilmInsight screenplay upload endpoint.

Flow:
  1. Validate PDF (type + size)
  2. Upload bytes to Supabase Storage (bucket: movie_scripts)
  3. Create MovieScript row in PostgreSQL with status='uploaded'
  4. Mark any linked MovieRequest as 'fulfilled'
  5. Kick off background ingestion task:
       a. Set status='ingesting'
       b. Run local ingestion pipeline:
            Download PDF → PyMuPDF → RecursiveCharacterTextSplitter
            → HuggingFace Embeddings → Persistent Chroma
       c. On success: status='ingested', chunks_stored=N, ingested_at=now
       d. On failure: status='failed', ingestion_error=<message>
  6. Return immediately with 200 — ingestion runs async
"""

import logging
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import get_db
from app.models.movie_request import MovieRequest
from app.models.movie_script import MovieScript
from app.models.schemas import UploadResponse
from app.services.ingestion_service import IngestionError, IngestionService
from app.services.supabase_storage import upload_file_to_supabase

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/upload", tags=["Upload"])

MAX_SIZE_MB     = 50
SUPABASE_BUCKET = "movie_scripts"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_title(filename: str) -> str:
    """Convert a PDF filename into a human-readable movie title."""
    stem = Path(filename).stem
    stem = re.sub(r"[\(\[]\s*\d{4}\s*[\)\]]", "", stem)   # remove (2010)
    stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)           # remove bare years
    stem = re.sub(r"[_.\\-]+", " ", stem)                  # _ . - → space
    stem = re.sub(r"\s{2,}", " ", stem).strip()
    return stem.title()


def _sanitise_supabase_name(filename: str) -> str:
    """
    Produce a safe filename for the Supabase bucket that preserves the
    original name as closely as possible (for human readability).
    Strips only characters that cause issues in storage paths.
    """
    safe = re.sub(r"[^\w\s.\-&]", "", filename)
    safe = safe.strip()
    return safe if safe else filename


# ── Background ingestion task ─────────────────────────────────────────────────

def _run_ingestion_background(
    script_id:         int,
    supabase_filename: str,
    db_url:            str,
) -> None:
    """
    Background task: runs the local ingestion pipeline and updates
    PostgreSQL status.

    Runs in a thread-pool (FastAPI BackgroundTasks) — creates its own
    DB session since the request session is closed by this point.

    Pipeline:
        Supabase Storage → PyMuPDF → RecursiveCharacterTextSplitter
        → HuggingFace Embeddings → Persistent Chroma → PostgreSQL update
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine  = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    with Session() as db:
        script = db.query(MovieScript).filter(MovieScript.id == script_id).first()
        if not script:
            logger.error(f"[Ingestion BG] MovieScript id={script_id} not found in DB.")
            return

        # ── Mark as ingesting ──────────────────────────────────────────────
        script.status = "ingesting"
        db.commit()
        logger.info(
            f"[Ingestion BG] Starting ingestion for '{script.title}' "
            f"(id={script_id}, file='{supabase_filename}')"
        )

        try:
            svc    = IngestionService()
            chunks = svc.ingest_from_supabase(
                supabase_filename=supabase_filename,
                movie_id=script_id,
            )

            # ── Success ───────────────────────────────────────────────────
            script.status          = "ingested"
            script.chunks_stored   = chunks
            script.ingested_at     = datetime.utcnow()
            script.ingestion_error = None
            db.commit()
            logger.info(
                f"[Ingestion BG] '{script.title}' ingested successfully "
                f"({chunks} chunks stored in Chroma)."
            )

        except (IngestionError, Exception) as exc:
            # ── Failure ───────────────────────────────────────────────────
            error_msg              = str(exc)[:1000]
            script.status          = "failed"
            script.ingestion_error = error_msg
            db.commit()
            logger.error(
                f"[Ingestion BG] Ingestion failed for '{script.title}': {error_msg}"
            )


# ── Upload endpoint ───────────────────────────────────────────────────────────

@router.post("", response_model=UploadResponse)
async def upload_screenplay(
    background_tasks: BackgroundTasks,
    file:       UploadFile = File(...),
    request_id: int        = Form(None),
    db:         Session    = Depends(get_db),
) -> UploadResponse:
    """
    Upload a movie screenplay PDF.

    - Stores the file in Supabase Storage (`movie_scripts` bucket).
    - Records the upload in PostgreSQL (`movie_scripts` table).
    - Automatically triggers **local** ingestion in the background:
        PDF → PyMuPDF → chunks → HuggingFace embeddings → Chroma vector DB.
    - Optionally marks a `MovieRequest` as fulfilled via `request_id`.

    Status lifecycle in PostgreSQL:
        `uploaded` → `ingesting` → `ingested` | `failed`
    """

    # ── Validation ────────────────────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    size_mb  = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size_mb:.1f} MB. Maximum: {MAX_SIZE_MB} MB.",
        )

    title             = _parse_title(file.filename)
    supabase_filename = _sanitise_supabase_name(file.filename)

    # ── Upload to Supabase Storage ────────────────────────────────────────────
    try:
        upload_file_to_supabase(SUPABASE_BUCKET, supabase_filename, contents)
        logger.info(
            f"Uploaded '{file.filename}' → "
            f"Supabase bucket '{SUPABASE_BUCKET}/{supabase_filename}'"
        )
    except Exception as exc:
        logger.error(f"Supabase upload error: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file to storage: {exc}")

    # ── Save to PostgreSQL ────────────────────────────────────────────────────
    try:
        script_record = MovieScript(
            title         = title,
            file_path     = file.filename,       # original upload name
            supabase_path = supabase_filename,   # path in Supabase bucket
            status        = "uploaded",
        )
        db.add(script_record)

        # Mark linked request as fulfilled
        if request_id:
            req = db.query(MovieRequest).filter(MovieRequest.id == request_id).first()
            if req:
                req.status = "fulfilled"

        db.commit()
        db.refresh(script_record)
        script_id = script_record.id

    except Exception as exc:
        logger.error(f"Database save error: {exc}")
        raise HTTPException(status_code=500, detail="Failed to save record to database.")

    # ── Schedule background ingestion ─────────────────────────────────────────
    settings = get_settings()
    background_tasks.add_task(
        _run_ingestion_background,
        script_id=script_id,
        supabase_filename=supabase_filename,
        db_url=settings.DATABASE_URL,
    )

    logger.info(
        f"Upload complete: '{title}' (id={script_id}). "
        f"Background ingestion scheduled."
    )

    return UploadResponse(
        filename = file.filename,
        status   = "uploaded",
        message  = (
            f'"{title}" uploaded to Supabase and saved to database. '
            f"Ingestion into the local Chroma vector database has started in the background. "
            f"The movie will be searchable once ingestion completes."
        ),
    )
