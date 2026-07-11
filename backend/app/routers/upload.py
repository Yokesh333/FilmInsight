import logging
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/upload', tags=['Upload'])

UPLOAD_DIR  = Path('/tmp/filminsight_uploads')
MAX_SIZE_MB = 50


@router.post('', response_model=UploadResponse)
async def upload_screenplay(file: UploadFile = File(...)):
    """
    Upload a movie screenplay PDF.
    Saves the file and returns upload status.
    (In production: trigger Flowise document store ingestion)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail='Only PDF files are supported.')

    # Check size
    contents = await file.read()
    size_mb   = len(contents) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f'File too large: {size_mb:.1f} MB. Maximum allowed: {MAX_SIZE_MB} MB.'
        )

    # Save file
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        dest = UPLOAD_DIR / file.filename
        async with aiofiles.open(dest, 'wb') as f:
            await f.write(contents)
    except Exception as exc:
        logger.error(f'Upload save error: {exc}')
        raise HTTPException(status_code=500, detail='Failed to save uploaded file.')

    logger.info(f'Uploaded: {file.filename} ({size_mb:.1f} MB)')

    return UploadResponse(
        filename = file.filename,
        status   = 'uploaded',
        message  = f'"{file.filename}" uploaded successfully ({size_mb:.1f} MB). Processing will begin shortly.',
    )
