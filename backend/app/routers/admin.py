from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User
from app.models.movie_request import MovieRequest
from app.models.movie_script import MovieScript
from app.core.security import get_current_user
import json
import os
import subprocess
import logging
from pathlib import Path

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"]
)

logger = logging.getLogger(__name__)

# Basic RBAC check
def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user

# Paths
PROCESSED_FILE = Path("C:\\Users\\Yokesh\\Downloads\\FilmInsight_AI\\ingestion\\processed_movies.json")
SCRIPTS_DIR = Path("C:\\Users\\Yokesh\\Downloads\\FilmInsight_AI\\movie_scripts")

def _read_processed_movies():
    if not PROCESSED_FILE.exists():
        return {}
    try:
        with open(PROCESSED_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_processed_movies(data):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    total_users = db.query(User).count()
    total_requests = db.query(MovieRequest).filter(MovieRequest.status == "pending").count()
    processed_movies = _read_processed_movies()
    total_movies = len(processed_movies)
    
    return {
        "users": total_users,
        "movies": total_movies,
        "pending_requests": total_requests,
        "chat_calls": 0 # Placeholder for Flowise chat analytics
    }

@router.get("/movies")
def get_movies(admin: User = Depends(get_admin_user)):
    movies = _read_processed_movies()
    # Format into list
    result = []
    for title, meta in movies.items():
        result.append({
            "title": title,
            "processed_at": meta.get("processed_at"),
            "chunks_stored": meta.get("chunks_stored"),
            "pdf_path": meta.get("pdf_path")
        })
    return result

@router.delete("/movies/{title}")
def delete_movie(title: str, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    movies = _read_processed_movies()
    
    # Try to find the movie in DB
    script = db.query(MovieScript).filter(MovieScript.title == title).first()
    
    if script:
        # Delete from Supabase
        try:
            from app.services.supabase_storage import get_supabase_client
            supabase = get_supabase_client()
            supabase.storage.from_("movie-scripts").remove([script.file_path])
        except Exception as e:
            logger.error(f"Failed to delete from Supabase: {e}")
            
        # Delete from DB
        db.delete(script)
        db.commit()

    if title in movies:
        del movies[title]
        _write_processed_movies(movies)
        
    return {"status": "success", "message": f"Deleted {title}"}

@router.post("/movies/{title}/reingest")
def reingest_movie(title: str, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    movies = _read_processed_movies()
    if title in movies:
        del movies[title]
        _write_processed_movies(movies)
        
    script = db.query(MovieScript).filter(MovieScript.title == title).first()
    if script:
        script.status = "uploaded"
        db.commit()
        
    return {"status": "success", "message": f"Marked {title} for re-ingestion"}

@router.post("/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks, admin: User = Depends(get_admin_user)):
    # Simple background trigger of the module
    # In production, use Celery or similar for better task management
    def run_ingestion():
        try:
            subprocess.run(["python", "-m", "ingestion.ingest_movies"], cwd="C:\\Users\\Yokesh\\Downloads\\FilmInsight_AI")
        except Exception as e:
            logger.error(f"Ingestion process failed: {e}")
            
    background_tasks.add_task(run_ingestion)
    return {"status": "success", "message": "Ingestion pipeline triggered in the background"}

@router.get("/requests")
def get_requests(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    requests = db.query(MovieRequest).all()
    # join with users to get username
    result = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        result.append({
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "username": user.username if user else "Unknown",
            "created_at": req.created_at
        })
    return result

@router.post("/requests/{req_id}/approve")
def approve_request(req_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    req = db.query(MovieRequest).filter(MovieRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "approved"
    db.commit()
    return {"status": "success"}

@router.post("/requests/{req_id}/reject")
def reject_request(req_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    req = db.query(MovieRequest).filter(MovieRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "rejected"
    db.commit()
    return {"status": "success"}
