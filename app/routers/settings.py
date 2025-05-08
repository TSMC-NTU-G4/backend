from fastapi import APIRouter

from app.core.redis import get_alert_suppress_time, redis_client
from app.models.settings import Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.put("/alert-suppress-time")
def set_suppress_time(data: Settings) -> dict[str, str]:
    redis_client.set("ALERT_SUPPRESS_TIME", str(data.alert_suppress_time))
    return {
        "message": f"Updated to {data.alert_suppress_time} seconds",
    }


@router.get("/alert-suppress-time")
def get_suppress_time() -> int:
    return get_alert_suppress_time()
