from fastapi import APIRouter

from app.core.redis import redis_client
from app.models.response import Response

router = APIRouter(prefix="/api/redis", tags=["redis"])


@router.delete("/")
async def clear_cache() -> Response:
    await redis_client.flushdb()
    return {"message": "Clear redis cache successfully"}
