import logging
from supabase import create_client, Client
from app.core.config import get_settings

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    settings = get_settings()
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    if not url or not key:
        raise ValueError("Supabase URL or Service Role Key is missing from configuration.")
    return create_client(url, key)

def upload_file_to_supabase(bucket_name: str, file_path: str, file_bytes: bytes) -> str:
    """
    Uploads bytes to a Supabase storage bucket.
    """
    supabase = get_supabase_client()
    try:
        # Uploading replacing if exists isn't strictly necessary since we use UUIDs,
        # but file_options ensures correct MIME type.
        supabase.storage.from_(bucket_name).upload(
            file=file_bytes,
            path=file_path,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        return file_path
    except Exception as e:
        logger.error(f"Failed to upload to Supabase: {e}")
        raise e
