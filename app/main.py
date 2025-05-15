import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.redis import check_redis_connection
from app.core.redis_listener import listen_to_alerts
from app.models.response import Response
from app.routers import earthquake, redis, settings
from app.websockets import alerts_ws

app = FastAPI()
Instrumentator().instrument(app).expose(app)

# enable CORS related config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(earthquake.router)
app.include_router(settings.router)
app.include_router(redis.router)
app.include_router(alerts_ws.router)

alert_listener_task = None


@app.on_event("startup")
async def startup_event() -> None:
    global alert_listener_task
    alert_listener_task = asyncio.create_task(listen_to_alerts())


@app.get("/")
def root() -> Response:
    return {"message": "Welcome to the Earthquake API!"}


@app.get("/health")
async def health_check() -> Response:
    redis_ok = await check_redis_connection()

    # TODO: check for prometheus and grafana status

    overall_status = all([redis_ok])
    return {
        "message": "All services are healthy"
        if overall_status
        else "Some services are unhealthy",
        "data": {
            "redis": "healthy" if redis_ok else "unhealthy",
        },
    }
