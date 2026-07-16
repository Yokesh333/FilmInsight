import logging
import uuid
import subprocess
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from sqlalchemy.orm import Session
from app.models.schemas import UploadResponse
from app.models.movie_script import MovieScript
from app.models.movie_request import MovieRequest
from app.db.database import get_db
from app.services.supabase_storage import upload_file_to_supabase
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/upload', tags=['Upload'])

MAX_SIZE_MB = 50

def parse_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[\(\[]\s*\d{4}\s*[\)\]]", "", stem)
    stem = re.sub(r"\b(19|20)\d{2}\b", "", stem)
    stem = re.sub(r"[_.\-]+", " ", stem)
    stem = re.sub(r"\s{2,}", " ", stem).strip()
    return stem.title()

def run_ingestion():
    try:
        logger.info("Automatically triggering ingestion pipeline in the background...")
        subprocess.run(["python", "-m", "ingestion.ingest_movies"], cwd="C:\\Users\\Yokesh\\Downloads\\FilmInsight_AI")
        logger.info("Automated ingestion pipeline finished.")
    except Exception as e:
        logger.error(f"Automated ingestion process failed: {e}")

@router.post('', response_model=UploadResponse)
async def upload_screenplay(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    request_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a movie screenplay PDF to Supabase Storage.
    Saves the file to 'movie-scripts' bucket and creates a DB record.
    Automatically triggers the ingestion pipeline.
    If request_id is provided, marks the request as fulfilled.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files are supported.')

    contents = await file.read()
    size_mb   = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f'File too large: {size_mb:.1f} MB. Maximum allowed: {MAX_SIZE_MB} MB.'
        )

    title = parse_title(file.filename)
    unique_filename = f"{uuid.uuid4().hex}.pdf"

    try:
        upload_file_to_supabase("movie-scripts", unique_filename, contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail='Failed to upload file to storage.')

    # Save to database
    try:
        script_record = MovieScript(
            title=title,
            file_path=unique_filename,
            status="uploaded"
        )
        db.add(script_record)
        
        # Mark request as fulfilled if provided
        if request_id:
            req = db.query(MovieRequest).filter(MovieRequest.id == request_id).first()
            if req:
                req.status = "fulfilled"

        db.commit()
    except Exception as exc:
        logger.error(f'Database save error: {exc}')
        raise HTTPException(status_code=500, detail='Failed to save record to database.')

    logger.info(f'Uploaded: {file.filename} as {unique_filename} ({size_mb:.1f} MB)')

    # Automatically trigger ingestion
    background_tasks.add_task(run_ingestion)

    return UploadResponse(
        filename = file.filename,
        status   = 'uploaded',
        message  = f'"{title}" uploaded successfully. Automated ingestion has been triggered and will process in the background.',
    )
