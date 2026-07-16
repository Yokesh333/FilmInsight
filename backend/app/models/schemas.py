from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from app.models.favorite_movie_schemas import FavoriteMovieCreate, FavoriteMovieResponse
from app.models.recently_viewed_schemas import RecentlyViewedCreate, RecentlyViewedResponse

# ── Chat ──────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question:  str = Field(..., min_length=1, max_length=4000)
    sessionId: str = Field(..., description="Session UUID")
    movie_name: Optional[str] = None


class SourceDocument(BaseModel):
    pageLabel: Optional[str]   = None
    content:   Optional[str]   = None
    page:      Optional[int]   = None
    score:     Optional[float] = None


class ChatResponse(BaseModel):
    answer:     str
    sources:    List[SourceDocument] = []
    sessionId:  str
    confidence: Optional[float] = None
    movieTitle: Optional[str]   = None
    timestamp:  datetime        = Field(default_factory=datetime.utcnow)


# ── Movie ─────────────────────────────────────────────────────────
class MovieResponse(BaseModel):
    title:    str
    year:     Optional[int]         = None
    genre:    Optional[List[str]]   = None
    director: Optional[str]         = None
    cast:     Optional[List[str]]   = None
    plot:     Optional[str]         = None
    rating:   Optional[float]       = None
    runtime:  Optional[str]         = None
    awards:   Optional[str]         = None
    poster:   Optional[str]         = None


# ── Upload ────────────────────────────────────────────────────────
class UploadResponse(BaseModel):
    filename: str
    status:   str
    message:  str
    chunks:   Optional[int] = None


# ── Health ────────────────────────────────────────────────────────
class ServiceStatus(str, Enum):
    ok          = "ok"
    degraded    = "degraded"
    unreachable = "unreachable"


class HealthResponse(BaseModel):
    status:   ServiceStatus = ServiceStatus.ok
    flowise:  str           = "unknown"
    database: str           = "unknown"
    version:  str           = "1.0.0"
    uptime:   Optional[str] = None


# ── Error ─────────────────────────────────────────────────────────
class ErrorResponse(BaseModel):
    error:   str
    detail:  Optional[str] = None
    code:    int           = 500
