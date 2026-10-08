"""Company accounts, bearer sessions, and per-workspace data access."""
import hashlib
import hmac
import logging
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth import AppUser, AuthSession, UserChatMessage, Workspace, WorkspaceInvitation
from app.models.data_source import DataSource

router = APIRouter(prefix="/auth", tags=["User Authentication & Chat Persistence"])
logger = logging.getLogger(__name__)
SESSION_DAYS = 14
INVITATION_DAYS = 7


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${derived.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("scrypt$"):
        _, salt, expected = stored.split("$", 2)
        return hmac.compare_digest(_hash_password(password, bytes.fromhex(salt)).split("$", 2)[2], expected)
    # Upgrade passwords created by the former demo-only SHA-256 implementation on successful login.
    legacy = hashlib.sha256((password + "hackathon-secret-salt-bi-agent-2026").encode()).hexdigest()
    return hmac.compare_digest(legacy, stored)


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    business_name: str = Field(..., min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: Literal["manager", "viewer"] = "viewer"


class InvitationAcceptRequest(BaseModel):
    token: str = Field(..., min_length=24)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class RoleUpdateRequest(BaseModel):
    role: Literal["manager", "viewer"]


class AuthResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    token: Optional[str] = None
    workspace_id: str
    business_name: str


class ChatMessageSaveRequest(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None
    executed_sql: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


def _new_session(db: Session, user: AppUser) -> str:
    raw_token = secrets.token_urlsafe(40)
    db.add(AuthSession(user_id=user.id, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
                       expires_at=datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)))
    return raw_token


def _response(user: AppUser, workspace: Workspace, token: str | None = None) -> AuthResponse:
    return AuthResponse(user_id=str(user.id), email=user.email, full_name=user.full_name,
                        role=user.role, token=token, workspace_id=str(workspace.id),
                        business_name=workspace.name)


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> AppUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Please log in to access company data.")
    token = authorization[7:].strip()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = db.query(AuthSession).filter(AuthSession.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if not session or session.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=401, detail="Your session expired. Please log in again.")
    user = db.query(AppUser).filter(AppUser.id == session.user_id).first()
    if not user or not user.workspace_id:
        raise HTTPException(status_code=401, detail="Account is not connected to a company workspace.")
    sources = db.query(DataSource).filter(DataSource.workspace_id == user.workspace_id).all()
    db.info["workspace_id"] = user.workspace_id
    db.info["workspace_source_names"] = tuple(s.name for s in sources)
    db.info["workspace_source_labels"] = {s.name: (s.display_name or s.name) for s in sources}
    db.info["workspace_source_ids"] = tuple(s.id for s in sources)
    db.info["app_user_id"] = user.id
    return user


def require_manager(user: AppUser = Depends(get_current_user)) -> AppUser:
    if user.role not in {"business_owner", "manager"}:
        raise HTTPException(status_code=403, detail="A company manager must approve this action.")
    return user


def _send_invitation_email(to_email: str, workspace_name: str, role: str, invite_url: str) -> bool:
    """Send through optional SMTP settings; invitations remain usable without mail credentials."""
    from app.config import get_settings
    settings = get_settings()
    if not (settings.smtp_host and settings.smtp_from_email):
        return False
    message = EmailMessage()
    message["Subject"] = f"Join {workspace_name} on Clearview BI"
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message.set_content(
        f"You have been invited to join {workspace_name} as a {role}.\n\n"
        f"Accept the invitation within {INVITATION_DAYS} days: {invite_url}\n"
    )
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password or "")
            smtp.send_message(message)
    return True


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if db.query(AppUser).filter(AppUser.email == email).first():
        raise HTTPException(status_code=409, detail="This email already has an account. Please log in.")
    # Preserve existing demo data for the first account; each later company starts isolated.
    workspace = db.query(Workspace).first() if not db.query(AppUser).first() else None
    if workspace is None:
        workspace = Workspace(name=req.business_name.strip())
        db.add(workspace)
        db.flush()
    else:
        workspace.name = req.business_name.strip()
    user = AppUser(email=email, full_name=(req.full_name or email.split("@")[0]).strip(),
                   hashed_password=_hash_password(req.password), role="business_owner", workspace_id=workspace.id)
    db.add(user)
    db.flush()
    token = _new_session(db, user)
    db.commit()
    db.refresh(user)
    return _response(user, workspace, token)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(AppUser).filter(AppUser.email == email).first()
    if not user or not _verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.hashed_password.startswith("scrypt$"):
        user.hashed_password = _hash_password(req.password)
    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=401, detail="Company workspace is unavailable.")
    token = _new_session(db, user)
    db.commit()
    return _response(user, workspace, token)


@router.post("/logout", status_code=204)
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        digest = hashlib.sha256(authorization[7:].strip().encode()).hexdigest()
        db.query(AuthSession).filter(AuthSession.token_hash == digest).delete()
        db.commit()


@router.get("/me", response_model=AuthResponse)
def get_me(user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    return _response(user, workspace)


@router.get("/chat-history")
def get_chat_history(limit: int = 50, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.query(UserChatMessage).filter(UserChatMessage.user_id == user.id).order_by(UserChatMessage.created_at.asc()).limit(limit).all()
    return [{"id": str(m.id), "role": m.role, "content": m.content, "intent": m.intent,
             "executed_sql": m.executed_sql, "timestamp": m.created_at.strftime("%I:%M %p"),
             "metadata_json": m.metadata_json} for m in msgs]


@router.post("/chat-history", status_code=201)
def save_chat_message(msg: ChatMessageSaveRequest, user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    new_msg = UserChatMessage(user_id=user.id, role=msg.role, content=msg.content, intent=msg.intent,
                              executed_sql=msg.executed_sql, metadata_json=msg.metadata_json)
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    return {"id": str(new_msg.id), "status": "saved"}


@router.delete("/chat-history")
def clear_chat_history(user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(UserChatMessage).filter(UserChatMessage.user_id == user.id).delete()
    db.commit()
    return {"status": "cleared"}


@router.get("/team")
def get_team(user: AppUser = Depends(get_current_user), db: Session = Depends(get_db)):
    members = db.query(AppUser).filter(AppUser.workspace_id == user.workspace_id).order_by(AppUser.created_at.asc()).all()
    now = datetime.now(timezone.utc)
    invitations = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.workspace_id == user.workspace_id,
        WorkspaceInvitation.accepted_at.is_(None),
    ).order_by(WorkspaceInvitation.created_at.desc()).all()
    return {
        "members": [{"id": str(member.id), "email": member.email, "full_name": member.full_name,
                     "role": member.role, "joined_at": member.created_at.isoformat(),
                     "is_current_user": member.id == user.id} for member in members],
        "invitations": [{"id": str(invite.id), "email": invite.invited_email, "role": invite.role,
                         "expires_at": invite.expires_at.isoformat(),
                         "expired": invite.expires_at.replace(tzinfo=timezone.utc) <= now}
                        for invite in invitations],
    }


@router.post("/invitations", status_code=201)
def create_invitation(req: InvitationCreateRequest, user: AppUser = Depends(require_manager), db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    existing = db.query(AppUser).filter(AppUser.email == email).first()
    if existing:
        if existing.workspace_id == user.workspace_id:
            raise HTTPException(status_code=409, detail="This person is already a member of your company.")
        raise HTTPException(status_code=409, detail="This email already belongs to another Clearview company account.")
    now = datetime.now(timezone.utc)
    pending = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.workspace_id == user.workspace_id,
        WorkspaceInvitation.invited_email == email,
        WorkspaceInvitation.accepted_at.is_(None),
    ).all()
    for old in pending:
        db.delete(old)
    raw_token = secrets.token_urlsafe(32)
    invitation = WorkspaceInvitation(
        workspace_id=user.workspace_id, invited_email=email, role=req.role,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), created_by=user.id,
        expires_at=now + timedelta(days=INVITATION_DAYS),
    )
    db.add(invitation)
    db.flush()
    workspace = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    from app.config import get_settings
    base_url = get_settings().frontend_base_url.rstrip("/")
    invite_url = f"{base_url}/?invite={raw_token}"
    try:
        email_sent = _send_invitation_email(email, workspace.name, req.role, invite_url)
    except Exception:
        logger.exception("Could not send company invitation email")
        email_sent = False
    db.commit()
    return {"id": str(invitation.id), "email": email, "role": req.role,
            "expires_at": invitation.expires_at.isoformat(), "invitation_url": invite_url,
            "email_sent": email_sent}


@router.get("/invitations/preview")
def preview_invitation(token: str, db: Session = Depends(get_db)):
    digest = hashlib.sha256(token.encode()).hexdigest()
    invite = db.query(WorkspaceInvitation).filter(WorkspaceInvitation.token_hash == digest).first()
    now = datetime.now(timezone.utc)
    if not invite or invite.accepted_at or invite.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=404, detail="This invitation is invalid or has expired.")
    workspace = db.query(Workspace).filter(Workspace.id == invite.workspace_id).first()
    return {"email": invite.invited_email, "role": invite.role,
            "business_name": workspace.name if workspace else "Company workspace",
            "expires_at": invite.expires_at.isoformat()}


@router.post("/invitations/accept", response_model=AuthResponse, status_code=201)
def accept_invitation(req: InvitationAcceptRequest, db: Session = Depends(get_db)):
    digest = hashlib.sha256(req.token.encode()).hexdigest()
    invite = db.query(WorkspaceInvitation).filter(WorkspaceInvitation.token_hash == digest).first()
    now = datetime.now(timezone.utc)
    if not invite or invite.accepted_at or invite.expires_at.replace(tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=400, detail="This invitation is invalid or has expired.")
    if db.query(AppUser).filter(AppUser.email == invite.invited_email).first():
        raise HTTPException(status_code=409, detail="This email already has a Clearview account.")
    workspace = db.query(Workspace).filter(Workspace.id == invite.workspace_id).first()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Company workspace not found.")
    user = AppUser(email=invite.invited_email, full_name=(req.full_name or invite.invited_email.split("@")[0]).strip(),
                   hashed_password=_hash_password(req.password), role=invite.role, workspace_id=workspace.id)
    invite.accepted_at = now
    db.add(user)
    db.flush()
    token = _new_session(db, user)
    db.commit()
    db.refresh(user)
    return _response(user, workspace, token)


@router.patch("/team/{member_id}/role")
def update_member_role(member_id: uuid.UUID, req: RoleUpdateRequest,
                       actor: AppUser = Depends(require_manager), db: Session = Depends(get_db)):
    member = db.query(AppUser).filter(AppUser.id == member_id, AppUser.workspace_id == actor.workspace_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Company member not found.")
    if member.role == "business_owner":
        raise HTTPException(status_code=400, detail="The company owner role cannot be changed here.")
    member.role = req.role
    db.commit()
    return {"id": str(member.id), "role": member.role}


@router.delete("/team/{member_id}", status_code=204)
def remove_member(member_id: uuid.UUID, actor: AppUser = Depends(require_manager), db: Session = Depends(get_db)):
    member = db.query(AppUser).filter(AppUser.id == member_id, AppUser.workspace_id == actor.workspace_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Company member not found.")
    if member.id == actor.id or member.role == "business_owner":
        raise HTTPException(status_code=400, detail="The company owner cannot remove this account.")
    db.delete(member)
    db.commit()


@router.delete("/invitations/{invitation_id}", status_code=204)
def revoke_invitation(invitation_id: uuid.UUID, actor: AppUser = Depends(require_manager), db: Session = Depends(get_db)):
    invite = db.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.id == invitation_id,
        WorkspaceInvitation.workspace_id == actor.workspace_id,
        WorkspaceInvitation.accepted_at.is_(None),
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Pending invitation not found.")
    db.delete(invite)
    db.commit()
