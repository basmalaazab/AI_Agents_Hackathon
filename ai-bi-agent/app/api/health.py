"""Health check endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import check_db_connection, get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Application health check")
def health_check(db: Session = Depends(get_db)):
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }
