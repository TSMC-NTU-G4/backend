from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import earthquake, settings

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


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Welcome to the Earthquake API!"}
