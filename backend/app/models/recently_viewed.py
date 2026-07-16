import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class RecentlyViewedMovie(Base):
    __tablename__ = "recently_viewed_movies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    movie_title = Column(String, nullable=False)
    movie_year = Column(String, nullable=True)
    poster_url = Column(String, nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
