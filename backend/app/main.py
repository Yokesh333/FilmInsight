import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, movie, upload, auth, admin, requests, favorites, recently_viewed
from app.models.schemas import HealthResponse, ServiceStatus
from app.db.database import engine, Base, get_db
from app.core.config import get_settings
from app.services.kb_startup import initialise_knowledge_base
from app.models import movie_script  # Import to register with Base
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends

# ── Logging ─────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

_start_time = time.time()


# ── Lifespan ─────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('═' * 50)
    logger.info('  FilmInsight API  — Starting up')
    logger.info('═' * 50)

    settings = get_settings()
    logger.info(f'  Embedding model : {settings.EMBEDDING_MODEL_NAME}')
    logger.info(f'  Chroma dir      : {settings.CHROMA_DB_DIR or "(auto-detected)"}')
    logger.info(f'  Collection      : {settings.CHROMA_COLLECTION_NAME}')
    logger.info(f'  Groq model      : {settings.GROQ_MODEL}')
    logger.info(f'  Groq key set    : {"yes" if settings.GROQ_API_KEY else "NO — set GROQ_API_KEY in .env"}')

    # ── Knowledge-base initialisation ────────────────────────────
    # Three-state decision tree (never crashes the application):
    #   1. chroma_db exists → use it
    #   2. movie_scripts has PDFs → auto-ingest, then use it
    #   3. Neither → warn and continue with empty KB
    try:
        kb_state = initialise_knowledge_base()
        app.state.kb_state = kb_state
    except Exception as exc:  # noqa: BLE001
        logger.error(f'Knowledge-base initialisation raised an unexpected error: {exc}')
        from app.services.kb_startup import KBState
        app.state.kb_state = KBState(
            status='error',
            message=f'KB initialisation error: {exc}',
            doc_count=0,
        )

    # Initialize Database Tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Database tables initialized successfully.')
    except Exception as exc:
        logger.error(f'Database initialization failed: {exc}')

    yield
    logger.info('FilmInsight API — Shutting down')


# ── App ──────────────────────────────────────────────────────────
settings = get_settings()

tags_metadata = [
    {"name": "Health",         "description": "Operations to check service health."},
    {"name": "Authentication", "description": "JWT-based authentication and user management."},
    {"name": "Chat",           "description": "Interact with the FilmInsight RAG chatbot."},
    {"name": "Movies",         "description": "Query and manage movie screenplays."},
    {"name": "Favorites",      "description": "Manage user favorite movies."},
    {"name": "Recent",         "description": "Track recently viewed movies."},
    {"name": "Requests",       "description": "Submit and manage movie script requests."},
    {"name": "Admin",          "description": "Administrative actions and statistics."},
]

app = FastAPI(
    title        = settings.APP_NAME,
    version      = settings.APP_VERSION,
    openapi_tags = tags_metadata,
    description  = (
        'FilmInsight REST API — AI-powered movie assistant backed by a local RAG pipeline.\n\n'
        'Documents are stored in Supabase, embedded with HuggingFace sentence-transformers, '
        'indexed in a persistent Chroma vector database, and answered via Groq LLM.'
    ),
    lifespan  = lifespan,
    docs_url  = '/docs',
    redoc_url = '/redoc',
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ['*'],
    allow_headers     = ['*'],
)

# ── Request Logging Middleware ────────────────────────────────────
@app.middleware('http')
async def log_requests(request: Request, call_next):
    t0       = time.monotonic()
    response = await call_next(request)
    ms       = round((time.monotonic() - t0) * 1000)
    logger.info(f'{request.method} {request.url.path} → {response.status_code} ({ms}ms)')
    return response

# ── Global Exception Handlers ────────────────────────────────────
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f'Database error occurred: {exc}', exc_info=True)
    return JSONResponse(
        status_code = 500,
        content     = {'error': 'Database error', 'detail': 'An internal database error occurred. Please try again later.'},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f'Unhandled exception: {exc}', exc_info=True)
    return JSONResponse(
        status_code = 500,
        content     = {'error': 'Internal server error', 'detail': str(exc)},
    )

# ── Routers ──────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(requests.router)
app.include_router(chat.router)
app.include_router(movie.router)
app.include_router(upload.router)
app.include_router(favorites.router)
app.include_router(recently_viewed.router)

# ── Endpoints ────────────────────────────────────────────────────
@app.get('/health', response_model=HealthResponse, tags=['Health'])
async def health(db: Session = Depends(get_db)):
    """
    Health check — pings the Chroma vector database and PostgreSQL,
    returns service status.
    """
    # Check Chroma status
    try:
        from app.services.rag_service import get_rag_service
        rag          = get_rag_service()
        chroma_count = rag.chroma_doc_count()
        chroma_status = f"ok ({chroma_count:,} docs)"
    except Exception as exc:
        logger.warning(f"Chroma health check failed: {exc}")
        chroma_status = "error"

    # Check Database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error(f"DB health check failed: {exc}")
        db_status = "error"

    uptime_s   = int(time.time() - _start_time)
    uptime_str = f'{uptime_s // 3600}h {(uptime_s % 3600) // 60}m {uptime_s % 60}s'

    is_healthy = db_status == "ok"

    return HealthResponse(
        status   = ServiceStatus.ok if is_healthy else ServiceStatus.degraded,
        chroma   = chroma_status,
        database = db_status,
        version  = settings.APP_VERSION,
        uptime   = uptime_str,
    )


@app.get('/kb-status', tags=['Knowledge Base'])
async def kb_status(request: Request):
    """
    Returns the current state of the Chroma knowledge base.

    Possible statuses:
    - **ready**  — Chroma DB is populated and ready for queries.
    - **empty**  — No movie scripts or Chroma DB found. Queries will return no context.
    - **error**  — Ingestion was attempted but failed (see message).
    """
    kb = getattr(request.app.state, 'kb_state', None)
    if kb is None:
        return {'status': 'unknown', 'message': 'KB state not yet initialised', 'doc_count': 0}
    return kb.to_dict()


@app.get('/', tags=['Root'])
async def root():
    return {
        'name':    'FilmInsight API',
        'version': settings.APP_VERSION,
        'docs':    '/docs',
        'health':  '/health',
        'kb':      '/kb-status',
    }
