"""
Authentication & User API Router.
Handles:
- POST /api/v1/auth/signup
- POST /api/v1/auth/login
- GET  /api/v1/auth/me
- GET  /api/v1/auth/chat-history
- POST /api/v1/auth/chat-history
- DELETE /api/v1/auth/chat-history
"""
import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import AppUser, UserChatMessage

router = APIRouter(prefix="/auth", tags=["User Authentication & Chat Persistence"])

SECRET_SALT = "hackathon-secret-salt-bi-agent-2026"


def _hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET_SALT).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    token: str


class ChatMessageSaveRequest(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    executed_sql: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Auth Helper Dependency
# ---------------------------------------------------------------------------

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AppUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token. Please log in.",
        )
    token = authorization.replace("Bearer ", "").strip()
    try:
        user_uuid = uuid.UUID(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token format.",
        )

    user = db.query(AppUser).filter(AppUser.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or session expired.",
        )
    return user


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    existing = db.query(AppUser).filter(AppUser.email == clean_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists. Please log in.",
        )

    user = AppUser(
        id=uuid.uuid4(),
        email=clean_email,
        full_name=req.full_name.strip() if req.full_name else clean_email.split("@")[0].title(),
        hashed_password=_hash_password(req.password),
        role="business_owner",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        token=str(user.id),  # Simple deterministic session token for hackathon
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    clean_email = req.email.strip().lower()
    user = db.query(AppUser).filter(AppUser.email == clean_email).first()
    if not user or user.hashed_password != _hash_password(req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    return AuthResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        token=str(user.id),
    )


@router.get("/me", response_model=AuthResponse)
def get_me(user: AppUser = Depends(get_current_user)):
    return AuthResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        token=str(user.id),
    )


@router.get("/chat-history")
def get_chat_history(
    limit: int = 50,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves saved chat messages specifically for the logged-in user."""
    msgs = (
        db.query(UserChatMessage)
        .filter(UserChatMessage.user_id == user.id)
        .order_by(UserChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "executed_sql": m.executed_sql,
            "timestamp": m.created_at.strftime("%I:%M %p"),
            "metadata_json": m.metadata_json,
        }
        for m in msgs
    ]


@router.post("/chat-history", status_code=status.HTTP_201_CREATED)
def save_chat_message(
    msg: ChatMessageSaveRequest,
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a message (user or assistant) to this user's persistent chat log."""
    new_msg = UserChatMessage(
        id=uuid.uuid4(),
        user_id=user.id,
        role=msg.role,
        content=msg.content,
        intent=msg.intent,
        executed_sql=msg.executed_sql,
        metadata_json=msg.metadata_json,
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return {"id": str(new_msg.id), "status": "saved"}


@router.delete("/chat-history")
def clear_chat_history(
    user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clears chat history for the logged-in user."""
    db.query(UserChatMessage).filter(UserChatMessage.user_id == user.id).delete()
    db.commit()
    return {"status": "cleared"}
