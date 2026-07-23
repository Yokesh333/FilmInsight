from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Float
from app.db.database import Base

class MovieScript(Base):
    __tablename__ = "movie_scripts"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title           = Column(String, index=True, nullable=False)
    file_path       = Column(String, nullable=False)           # original filename / UUID
    supabase_path   = Column(String, nullable=True)            # path inside Supabase bucket
    status          = Column(String, default="UPLOADED", nullable=False)
    # status values: 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED'
    chunks_stored   = Column(Integer, nullable=True)           # chunks in Flowise
    ingestion_error = Column(Text, nullable=True)              # error message if failed
    uploaded_at     = Column(DateTime, default=datetime.utcnow)
    ingested_at     = Column(DateTime, nullable=True)          # set when status='READY'
    
    # ── TMDB Metadata ─────────────────────────────────────────────────────────
    poster_url      = Column(String, nullable=True)
    backdrop_url    = Column(String, nullable=True)
    tmdb_id         = Column(Integer, nullable=True)
    overview        = Column(Text, nullable=True)
    release_date    = Column(String, nullable=True)
    genres          = Column(String, nullable=True)
    runtime         = Column(Integer, nullable=True)
    rating          = Column(Float, nullable=True)

