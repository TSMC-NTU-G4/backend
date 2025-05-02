import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def main() -> str:
    return "Hello from backend!"


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
