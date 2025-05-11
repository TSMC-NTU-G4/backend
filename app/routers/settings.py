from fastapi import APIRouter

from app.core.redis import get_alert_suppress_time, redis_client
from app.models.response import Response
from app.models.settings import Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.put("/alert-suppress-time")
async def set_suppress_time(data: Settings) -> Response[str]:
    await redis_client.set("ALERT_SUPPRESS_TIME", str(data.alert_suppress_time))
    return {
        "message": f"Updated to {data.alert_suppress_time} seconds successfully",
        "data": f"{data.alert_suppress_time}",
    }


@router.get("/alert-suppress-time")
async def get_suppress_time() -> Response[str]:
    time = await get_alert_suppress_time()
    return {
        "message": f"The current suppress time is {time} seconds",
        "data": f"{time}",
    }
