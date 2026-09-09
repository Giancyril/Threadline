from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Assistant With Memory Backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
