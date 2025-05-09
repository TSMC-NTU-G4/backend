# Backend

## Project setup
```bash
uv sync --frozen --no-cache
```

## Configure environment
```bash
cp .env.example .env  
```

## Lint and fix files
```bash
uvx ruff format .  
uvx ruff check . --fix   
```

## Build and start services
```bash
docker-compose build
docker-compose up -d
```
> ✅ Changes in `app/` are auto-reloaded.

> ⚠️ For other updates, kindly restart with: 
> ```bash
> docker-compose down
> docker-compose build  
> docker-compose up -d
> ```


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
    ```json
    {
      "message": "Created earthquake 8afe3df4-10b8-4031-acdc-3477dac40e98 successfully",
      "data": [
          {
              "id": "8afe3df4-10b8-4031-acdc-3477dac40e98-Taipei",
              "source": "Simulation",
              "origin_time": "2025-05-09T10:13:34",
              "location": "Taipei",
              "severity_level": 2,
              "has_damage": -1,
              "needs_command_center": -1,
              "processing_duration": 0
          },
          {
              "id": "8afe3df4-10b8-4031-acdc-3477dac40e98-Hsinchu",
              "source": "Simulation",
              "origin_time": "2025-05-09T10:13:34",
              "location": "Hsinchu",
              "severity_level": 2,
              "has_damage": -1,
              "needs_command_center": -1,
              "processing_duration": 0
          },
          {
              "id": "8afe3df4-10b8-4031-acdc-3477dac40e98-Taichung",
              "source": "Simulation",
              "origin_time": "2025-05-09T10:13:34",
              "location": "Taichung",
              "severity_level": 2,
              "has_damage": -1,
              "needs_command_center": -1,
              "processing_duration": 0
          },
          {
              "id": "8afe3df4-10b8-4031-acdc-3477dac40e98-Tainan",
              "source": "Simulation",
              "origin_time": "2025-05-09T10:13:34",
              "location": "Tainan",
              "severity_level": 2,
              "has_damage": -1,
              "needs_command_center": -1,
              "processing_duration": 0
          }
      ]
    }
    ```