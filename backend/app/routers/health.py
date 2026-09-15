from fastapi import APIRouter
from app.services.cache import ais_cache_stats

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "ais": ais_cache_stats()}