# Backend

## Project setup
```bash
# install dependencies
uv sync --frozen --no-cache
```

## Start the development server
```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Lint and fix files
```bash
uv run ruff format . 
uv run ruff check . --fix  
```

## Run backend with Docker
```bash
docker build -t backend .         # build image
docker run -p 8000:8000 backend   # run container
```

## API document
- POST `/api/earthquake`
  - Request body
    ```json
    {
        "epicenterLocation": "20.8 km NNE of Hualien County Hall",
        "magnitudeValue": "4.5",
        "focalDepth": "27.4",
        "shakingArea": [
            {
                "countyName": "Taipei",
                "areaIntensity": "1"
            },
            {
                "countyName": "Hsinchu",
                "areaIntensity": "2"
            }
        ],
        "originTime": "2025-05-06 11:20:01",
        "source": "Simulation"
    }
    ```
  - Response
    - Status: `204 No Content`