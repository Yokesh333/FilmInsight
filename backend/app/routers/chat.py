import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.core.security import get_optional_user, get_current_user
from app.models.chat_history import ChatHistory

from app.models.schemas import ChatRequest, ChatResponse, SourceDocument
from app.services.rag_service import RAGService, get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/chat', tags=['Chat'])


def _parse_sources(raw: list) -> List[SourceDocument]:
    """
    Convert RAGService source dicts into SourceDocument response models.

    Accepts both the old Flowise-style keys and the new Chroma metadata keys
    so the contract with the React frontend is fully preserved.
    """
    sources = []
    for doc in (raw or []):
        sources.append(SourceDocument(
            pageLabel = (
                doc.get('pageLabel')
                or doc.get('movie_name')
                or f"Page {doc.get('page', '?')}"
            ),
            content   = doc.get('content'),
            page      = doc.get('page'),
            score     = doc.get('score'),
        ))
    return sources


@router.post('', response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    rag:  RAGService = Depends(get_rag_service),
    db:   Session    = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """
    Send a question to the FilmInsight local RAG pipeline.

    - Embeds the question using HuggingFace all-MiniLM-L6-v2
    - Retrieves the top-5 most relevant screenplay chunks from local Chroma
    - Removes duplicate chunks
    - Builds a structured prompt with preserved movie metadata
    - Sends to Groq LLM for a natural-language answer
    - Returns a structured ChatResponse (same schema as before)

    The endpoint URL, request model, and response model are unchanged
    so the React frontend requires no modifications.
    """
    logger.info(
        f'[/chat] question="{body.question[:80]}…" '
        f'session={body.session_id[:8] if hasattr(body, "session_id") else body.sessionId[:8]}'
    )

    # Resolve session ID (support both camelCase and snake_case from frontend)
    session_id = getattr(body, "sessionId", None) or getattr(body, "session_id", "unknown")

    try:
        result = await rag.query(
            question=body.question,
            session_id=session_id,
            movie_name=body.movie_name,
        )
    except RuntimeError as exc:
        logger.error(f'[/chat] RAG pipeline error: {exc}')
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        logger.error(f'[/chat] Unexpected error: {exc}', exc_info=True)
        raise HTTPException(status_code=500, detail='Internal server error')

    answer  = result.get("answer", "I could not generate a response. Please try again.")
    sources = _parse_sources(result.get("sources", []))

    # Persist to chat history
    try:
        history_record = ChatHistory(
            user_id    = user.id if user else None,
            movie_name = body.movie_name,
            question   = body.question,
            ai_response= answer,
        )
        db.add(history_record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to save chat history: {e}")

    return ChatResponse(
        answer     = answer,
        sources    = sources,
        sessionId  = session_id,
        movieTitle = result.get("movie_title"),
    )


@router.get('/history', tags=['Chat'])
async def get_history(
    query: str = None,
    db:    Session = Depends(get_db),
    user:  User    = Depends(get_current_user),
):
    """Get chat history for the authenticated user, with optional text search."""
    history_query = db.query(ChatHistory).filter(ChatHistory.user_id == user.id)
    if query:
        history_query = history_query.filter(
            ChatHistory.question.ilike(f"%{query}%")
            | ChatHistory.ai_response.ilike(f"%{query}%")
            | ChatHistory.movie_name.ilike(f"%{query}%")
        )
    return history_query.order_by(ChatHistory.timestamp.desc()).all()


@router.delete('/history/{chat_id}', tags=['Chat'])
async def delete_history(
    chat_id: int,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    """Delete a specific chat record."""
    record = db.query(ChatHistory).filter(
        ChatHistory.id == chat_id,
        ChatHistory.user_id == user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Chat record not found")
    db.delete(record)
    db.commit()
    return {'status': 'deleted'}
