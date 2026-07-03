"""Health check router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return HTTP 200 when the service is operational."""
    return {"status": "ok"}
