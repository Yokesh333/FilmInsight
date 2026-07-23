import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.recently_viewed import RecentlyViewedMovie
from app.models.recently_viewed_schemas import RecentlyViewedCreate, RecentlyViewedResponse
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/recent', tags=['Recent'])

@router.get('', response_model=List[RecentlyViewedResponse])
def get_recent(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all recently viewed movies for the current user."""
    recent = db.query(RecentlyViewedMovie).filter(RecentlyViewedMovie.user_id == current_user.id).order_by(RecentlyViewedMovie.viewed_at.desc()).limit(20).all()
    return recent

@router.post('', response_model=RecentlyViewedResponse)
def add_recent(
    recent: RecentlyViewedCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Record a recently viewed movie. Updates timestamp if exists."""
    existing = db.query(RecentlyViewedMovie).filter(
        RecentlyViewedMovie.user_id == current_user.id,
        RecentlyViewedMovie.movie_title == recent.movie_title
    ).first()
    
    if existing:
        existing.viewed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
        
    db_recent = RecentlyViewedMovie(
        user_id=current_user.id,
        movie_title=recent.movie_title,
        movie_year=recent.movie_year,
        poster_url=recent.poster_url
    )
    db.add(db_recent)
    db.commit()
    db.refresh(db_recent)
    return db_recent
