import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import earthquake

# load env variables
load_dotenv()
app = FastAPI()

# enable CORS related config
origins = [
    os.environ.get("FRONTEND_BASE_URL"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(earthquake.router, prefix="/api", tags=["earthquake"])
