from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_db
from app.models.user import User
from app.models.movie_request import MovieRequest
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/requests",
    tags=["User Requests"]
)

class RequestCreate(BaseModel):
    title: str

@router.post("")
def create_request(req: RequestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_req = MovieRequest(
        user_id=user.id,
        movie_name=req.title,
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return {"status": "success", "message": "Request submitted successfully"}
    
@router.get("")
def get_user_requests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    requests = db.query(MovieRequest).filter(MovieRequest.user_id == user.id).all()
    # Map movie_name to title for the frontend
    return [
        {
            "id": r.id,
            "title": r.movie_name,
            "status": r.status,
            "requested_at": r.requested_at
        } for r in requests
    ]
