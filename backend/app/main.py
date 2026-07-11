import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers import chat, movie, upload
from app.models.schemas import HealthResponse, ServiceStatus
from app.services.flowise import get_flowise_service
from app.services.kb_startup import initialise_knowledge_base

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
    logger.info(f'  Flowise URL:  {settings.FLOWISE_URL}')
    logger.info(f'  Chatflow ID:  {settings.FLOWISE_CHATFLOW_ID or "(not set)"}')

    # ── Knowledge-base initialisation ────────────────────────────
    # Three-state decision tree (never crashes the application):
    #   1. chroma_db exists → use it
    #   2. movie_scripts has PDFs → auto-ingest, then use it
    #   3. Neither → warn and continue with empty KB
    try:
        kb_state = initialise_knowledge_base()
        app.state.kb_state = kb_state
    except Exception as exc:  # noqa: BLE001
        # Safety net — initialisation must never crash the server
        logger.error(f'Knowledge-base initialisation raised an unexpected error: {exc}')
        from app.services.kb_startup import KBState
        app.state.kb_state = KBState(
            status='error',
            message=f'KB initialisation error: {exc}',
            doc_count=0,
        )

    yield
    logger.info('FilmInsight API — Shutting down')


# ── App ──────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title       = settings.APP_NAME,
    version     = settings.APP_VERSION,
    description = (
        'FilmInsight REST API — AI-powered movie assistant backed by Flowise RAG. '
        'Forwards questions to the Flowise Prediction API and returns structured responses.'
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

# ── Global Exception Handler ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f'Unhandled exception: {exc}', exc_info=True)
    return JSONResponse(
        status_code = 500,
        content     = {'error': 'Internal server error', 'detail': str(exc)},
    )

# ── Routers ──────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(movie.router)
app.include_router(upload.router)

# ── Endpoints ────────────────────────────────────────────────────
@app.get('/health', response_model=HealthResponse, tags=['Health'])
async def health():
    """Health check — pings Flowise and returns service status."""
    flowise_status = await get_flowise_service().health()
    uptime_s       = int(time.time() - _start_time)
    uptime_str     = f'{uptime_s // 3600}h {(uptime_s % 3600) // 60}m {uptime_s % 60}s'

    return HealthResponse(
        status  = ServiceStatus.ok if flowise_status == 'ok' else ServiceStatus.degraded,
        flowise = flowise_status,
        version = settings.APP_VERSION,
        uptime  = uptime_str,
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
