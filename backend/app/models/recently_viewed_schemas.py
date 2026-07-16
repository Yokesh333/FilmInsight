from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RecentlyViewedCreate(BaseModel):
    movie_title: str
    movie_year: Optional[str] = None
    poster_url: Optional[str] = None

class RecentlyViewedResponse(RecentlyViewedCreate):
    id: int
    viewed_at: datetime
    
    class Config:
        from_attributes = True
