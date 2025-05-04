import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware

from src import models, utils

app = FastAPI()

# enable CORS related config
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def main() -> str:
    return "Hello from backend!"


@app.post("/api/earthquake")
def create_earthquake(data: models.EarthquakeData) -> Response:
    utils.generate_events(data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
