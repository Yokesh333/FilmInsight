import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.models.favorite_movie import FavoriteMovie
from app.models.favorite_movie_schemas import FavoriteMovieCreate, FavoriteMovieResponse
from app.core.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/favorites', tags=['Favorites'])

@router.get('', response_model=List[FavoriteMovieResponse])
def get_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all favorite movies for the current user."""
    favorites = db.query(FavoriteMovie).filter(FavoriteMovie.user_id == current_user.id).order_by(FavoriteMovie.added_at.desc()).all()
    return favorites

@router.post('', response_model=FavoriteMovieResponse)
def add_favorite(
    favorite: FavoriteMovieCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Add a movie to favorites."""
    # Check if already favorited
    existing = db.query(FavoriteMovie).filter(
        FavoriteMovie.user_id == current_user.id,
        FavoriteMovie.movie_title == favorite.movie_title
    ).first()
    
    if existing:
        return existing
        
    db_favorite = FavoriteMovie(
        user_id=current_user.id,
        movie_title=favorite.movie_title,
        movie_year=favorite.movie_year,
        poster_url=favorite.poster_url
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

@router.delete('/{movie_title}')
def remove_favorite(
    movie_title: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Remove a movie from favorites by title."""
    db_favorite = db.query(FavoriteMovie).filter(
        FavoriteMovie.user_id == current_user.id,
        FavoriteMovie.movie_title == movie_title
    ).first()
    
    if not db_favorite:
        raise HTTPException(status_code=404, detail="Favorite movie not found")
        
    db.delete(db_favorite)
    db.commit()
    return {"status": "removed"}
