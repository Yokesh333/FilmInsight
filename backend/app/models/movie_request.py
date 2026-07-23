import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base

class MovieRequest(Base):
    __tablename__ = "movie_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    movie_name = Column(String, nullable=False)
    status = Column(String, default="pending", nullable=False) # pending, approved, rejected
    requested_at = Column(DateTime, default=datetime.utcnow)
