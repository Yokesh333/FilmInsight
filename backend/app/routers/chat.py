import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.flowise import FlowiseService, FlowiseError, get_flowise_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/chat', tags=['Chat'])


def _parse_sources(raw: list) -> List[SourceDocument]:
    """Parse Flowise sourceDocuments into SourceDocument models."""
    sources = []
    for doc in (raw or []):
        meta    = doc.get('metadata', {})
        loc     = meta.get('loc', {})
        content = doc.get('pageContent', '')
        sources.append(SourceDocument(
            pageLabel = (
                meta.get('source')
                or meta.get('pdf', {}).get('info', {}).get('Title')
                or (f"Page {loc.get('pageNumber')}" if loc.get('pageNumber') else None)
                or 'Screenplay'
            ),
            content = content[:600] if content else None,
            page    = loc.get('pageNumber'),
            score   = doc.get('score'),
        ))
    return sources


@router.post('', response_model=ChatResponse)
async def chat(
    body:    ChatRequest,
    flowise: FlowiseService = Depends(get_flowise_service),
):
    """
    Send a question to the FilmInsight RAG pipeline.

    - Forwards to Flowise Prediction API
    - Parses source documents from the response
    - Returns structured ChatResponse
    """
    logger.info(f'[/chat] question="{body.question[:80]}…" session={body.sessionId[:8]}')

    try:
        data = await flowise.predict(body.question, body.sessionId)
    except FlowiseError as exc:
        logger.error(f'[/chat] FlowiseError: {exc}')
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    except Exception as exc:
        logger.error(f'[/chat] Unexpected: {exc}', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal server error')

    # Extract answer — Flowise may use 'text' or 'answer'
    answer = (
        data.get('text')
        or data.get('answer')
        or data.get('output')
        or 'I could not generate a response. Please try again.'
    )

    sources = _parse_sources(data.get('sourceDocuments', []))

    return ChatResponse(
        answer    = answer,
        sources   = sources,
        sessionId = body.sessionId,
    )


@router.get('/history/{session_id}', tags=['Chat'])
async def get_history(session_id: str):
    """Get chat history for a session (placeholder — extend with DB)."""
    return {'sessionId': session_id, 'messages': []}


@router.delete('/history/{session_id}', tags=['Chat'])
async def clear_history(session_id: str):
    """Clear session history."""
    return {'status': 'cleared', 'sessionId': session_id}
