from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer
from app.db.database import Base

class MovieScript(Base):
    __tablename__ = "movie_scripts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="uploaded", nullable=False) # 'uploaded', 'ingested'
    uploaded_at = Column(DateTime, default=datetime.utcnow)
