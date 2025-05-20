# Backend

[![Build](https://github.com/TSMC-NTU-G4/backend/actions/workflows/build.yml/badge.svg?event=push)](https://github.com/TSMC-NTU-G4/backend/actions/workflows/build.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=bugs)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=coverage)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=ncloc)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=reliability_rating)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=TSMC-NTU-G4_backend&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=TSMC-NTU-G4_backend)

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

## Run tests
```bash
uv run pytest -v
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
      "data": null
    }
    ```

- GET `/api/earthquake/alerts`
    - Response
        ```json
        {
            "message": "Found 4 alerts data",
            "data": [
                {
                    "id": "0792fa95-08c9-438b-88a3-b71d2c0c2be5-Hsinchu",
                    "source": "Simulation",
                    "originTime": "2025-05-20T22:51:45",
                    "location": "Hsinchu",
                    "severityLevel": 2,
                    "status": "OPEN",
                    "hasDamage": -1,
                    "needsCommandCenter": -1,
                    "processedTime": null,
                    "processingDuration": 0
                },
                {
                    "id": "0792fa95-08c9-438b-88a3-b71d2c0c2be5-Taichung",
                    "source": "Simulation",
                    "originTime": "2025-05-20T22:51:45",
                    "location": "Taichung",
                    "severityLevel": 2,
                    "status": "OPEN",
                    "hasDamage": -1,
                    "needsCommandCenter": -1,
                    "processedTime": null,
                    "processingDuration": 0
                },
                {
                    "id": "0792fa95-08c9-438b-88a3-b71d2c0c2be5-Tainan",
                    "source": "Simulation",
                    "originTime": "2025-05-20T22:51:45",
                    "location": "Tainan",
                    "severityLevel": 2,
                    "status": "OPEN",
                    "hasDamage": -1,
                    "needsCommandCenter": -1,
                    "processedTime": null,
                    "processingDuration": 0
                },
                {
                    "id": "0792fa95-08c9-438b-88a3-b71d2c0c2be5-Taipei",
                    "source": "Simulation",
                    "originTime": "2025-05-20T22:51:45",
                    "location": "Taipei",
                    "severityLevel": 2,
                    "status": "OPEN",
                    "hasDamage": -1,
                    "needsCommandCenter": -1,
                    "processedTime": null,
                    "processingDuration": 0
                }
            ]
        }
        ```