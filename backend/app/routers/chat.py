import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.security import get_optional_user, get_current_user
from app.models.chat_history import ChatHistory

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
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user)
):
    """
    Send a question to the FilmInsight RAG pipeline.

    - Forwards to Flowise Prediction API
    - Parses source documents from the response
    - Returns structured ChatResponse
    """
    logger.info(f'[/chat] question="{body.question[:80]}…" session={body.sessionId[:8]}')

    # Inject RAG pipeline rules into the question
    system_rules = f"""
[SYSTEM INSTRUCTIONS]
You are a knowledgeable movie enthusiast explaining the story.
Rules:
1. Always retrieve relevant screenplay chunks before generating a response.
2. Generate a natural, conversational answer instead of copying screenplay text.
3. If screenplay context exists, never ignore it.
4. Clearly separate screenplay-derived information from supplementary information.
5. If additional information such as trivia, cast, release year, IMDb rating or interesting facts is available from TMDb, OMDb or trusted web sources, present it under separate headings.
6. Never hallucinate screenplay events.
7. If the screenplay does not contain enough information, clearly state that and then provide additional web information.

User Question: {body.question}
"""

    try:
        data = await flowise.predict(system_rules.strip(), body.sessionId)
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

    # Save to Chat History
    try:
        history_record = ChatHistory(
            user_id=user.id if user else None,
            movie_name=body.movie_name,
            question=body.question,
            ai_response=answer
        )
        db.add(history_record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")

    return ChatResponse(
        answer    = answer,
        sources   = sources,
        sessionId = body.sessionId,
    )


@router.get('/history', tags=['Chat'])
async def get_history(query: str = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get chat history for the authenticated user, with optional text search."""
    history_query = db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
    if query:
        history_query = history_query.filter(
            ChatHistory.question.ilike(f"%{query}%") | 
            ChatHistory.ai_response.ilike(f"%{query}%") | 
            ChatHistory.movie_name.ilike(f"%{query}%")
        )
    return history_query.order_by(ChatHistory.timestamp.desc()).all()


@router.delete('/history/{chat_id}', tags=['Chat'])
async def delete_history(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Delete a specific chat record."""
    record = db.query(ChatHistory).filter(ChatHistory.id == chat_id, ChatHistory.user_id == user.id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Chat record not found")
    db.delete(record)
    db.commit()
    return {'status': 'deleted'}
