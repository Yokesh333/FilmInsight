from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FavoriteMovieBase(BaseModel):
    movie_title: str
    movie_year: Optional[str] = None
    poster_url: Optional[str] = None

class FavoriteMovieCreate(FavoriteMovieBase):
    pass

class FavoriteMovieResponse(FavoriteMovieBase):
    id: int
    added_at: datetime
    
    class Config:
        from_attributes = True
