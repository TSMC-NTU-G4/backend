import datetime
import math
import random
import time
from typing import Any

import httpx

# Configuration parameters (translated from JS CONFIG)
CONFIG: dict[str, Any] = {
    # Subscription interval (milliseconds)
    "interval": 1000,
    # Request timeout (milliseconds)
    "timeout": {
        "RTS": 2000,
        "EEW": 2000,
        "INTENSITY": 2000,
        "LPGM": 2000,
        "STATION": 3500,
    },
    # API servers
    "servers": {
        "api": ["api-1.exptech.dev", "api-2.exptech.dev"],
        "lb": [
            "lb-1.exptech.dev",
            "lb-2.exptech.dev",
            "lb-3.exptech.dev",
            "lb-4.exptech.dev",
        ],
    },
    # Target monitoring areas
    "targetAreas": [
        {"code": 106, "name": "臺北市大安區"},
        {"code": 402, "name": "臺中市南區"},
        {"code": 710, "name": "臺南市永康區"},
        {"code": 301, "name": "新竹市東區"},
    ],
    # Display intensity threshold (0 means always display)
    "displayThreshold": 0,
}

# Intensity scale text representation (from JS INTENSITY_LIST)
INTENSITY_LIST: list[str] = ["0", "1", "2", "3", "4", "5⁻", "5⁺", "6⁻", "6⁺", "7"]

# Global state variables
last_fetch_time: float = 0.0
request_counter: int = 0
is_offline: bool = False
area_status: dict[int, dict[str, Any]] = {}
station_info: dict[str, Any] | None = None
last_station_info_fetch: float = 0.0
STATION_INFO_INTERVAL: int = 5 * 60 * 1000  # 5 minutes in milliseconds
unified_magnitude: float = 0.0

# Initialize status for each target area
for area in CONFIG["targetAreas"]:
    area_status[area["code"]] = {
        "name": area["name"],
        "pga": 0.0,
        "intensity": 0,  # Integer intensity (0-9)
        "intensity_text": "0",  # Textual representation (e.g., "0", "5-") or float value from API
        "magnitude": "0.0",
        "lastUpdate": None,
    }


class IntensityCalculator:
    """Utility functions for intensity calculation."""

    @staticmethod
    def pga_to_float(pga: float) -> float:
        """Converts PGA (gal) to float intensity."""
        if pga <= 0:
            return -3.0  # Avoid math domain error for log(0) or log(<0)
        return 2 * (math.log(pga) / math.log(10)) + 0.7

    @staticmethod
    def pga_to_intensity(pga: float) -> int:
        """Converts PGA (gal) to integer intensity (0-9)."""
        return IntensityCalculator.intensity_float_to_int(
            IntensityCalculator.pga_to_float(pga),
        )

    @staticmethod
    def intensity_float_to_int(float_value: float) -> int:
        """Converts float intensity to integer intensity (0-9)."""
        if float_value < 0:
            return 0
        if float_value < 4.5:
            return round(float_value)
        if float_value < 5:
            return 5  # 5-
        if float_value < 5.5:
            return 6  # 5+
        if float_value < 6:
            return 7  # 6-
        if float_value < 6.5:
            return 8  # 6+
        return 9  # 7

    @staticmethod
    def intensity_to_text(level: float) -> str:
        """Converts integer intensity (0-9) to text representation."""
        level = round(level)  # round() returns int if an integer is passed
        if 0 <= level < len(INTENSITY_LIST):
            return INTENSITY_LIST[level]
        return "不明"

    @staticmethod
    def estimate_magnitude(intensity: float, distance: float) -> float:
        """Estimates earthquake magnitude based on intensity and distance (Kawasumi formula)."""
        if distance <= 0:
            distance = 1  # Avoid log(0) or division by zero
        # M = 0.58I + 1.5log10(D) - 0.007D + 0.5
        return 0.58 * intensity + 1.5 * math.log10(distance) - 0.007 * distance + 0.5

    @staticmethod
    def estimate_reasonable_magnitude(intensity_float: float) -> float:
        """Estimates a reasonable earthquake magnitude based on float intensity."""
        estimated_distance = 30
        if intensity_float <= 0:
            estimated_distance = 30
        elif intensity_float <= 2:
            estimated_distance = 40
        elif intensity_float <= 4:
            estimated_distance = 50
        elif intensity_float <= 6:
            estimated_distance = 60
        else:
            estimated_distance = 70

        magnitude = IntensityCalculator.estimate_magnitude(
            intensity_float,
            estimated_distance,
        )

        if intensity_float < 0 and magnitude > 3:
            magnitude = 2 + (intensity_float + 3) * 0.3

        if magnitude < 0:
            magnitude = 0.0
        if magnitude > 9:
            magnitude = 9.0
        return magnitude


async def fetch_data(url: str, timeout_ms: int = 1000) -> httpx.Response | None:
    """Custom fetch function with timeout and error handling using httpx."""
    global is_offline
    timeout_seconds = timeout_ms / 1000.0
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                timeout=timeout_seconds,
                headers={"Cache-Control": "no-cache"},
            )
            response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

            if is_offline:
                # Consider using logging instead of print for library/module code
                # print(f"[realtime_data_handler.py] -> Network connection restored")
                is_offline = False
            return response
        except httpx.TimeoutException:
            if not is_offline:
                # print(f"[realtime_data_handler.py] -> Request timed out | {url}")
                is_offline = True
            return None
        except httpx.RequestError:
            if not is_offline:
                # print(f"[realtime_data_handler.py] -> Request failed: {url} | {error}")
                is_offline = True
            return None


def get_random_server(server_type: str) -> str:
    """Gets a random server from the CONFIG."""
    servers = CONFIG["servers"].get(server_type, CONFIG["servers"]["lb"])
    return random.choice(servers)


async def get_station_info() -> dict[str, Any] | None:
    """Fetches station information."""
    global station_info, last_station_info_fetch
    now = time.time() * 1000

    if station_info and (now - last_station_info_fetch < STATION_INFO_INTERVAL):
        return station_info

    server = get_random_server("api")
    url = f"https://{server}/api/v1/trem/station"
    response = await fetch_data(url, CONFIG["timeout"]["STATION"])

    if response:
        try:
            station_info = response.json()
            last_station_info_fetch = now
            # print(f"[realtime_data_handler.py] -> Station information updated successfully")
            return station_info
        except ValueError:  # Includes JSONDecodeError
            # print(f"[realtime_data_handler.py] -> Failed to decode JSON from station info: {url}")
            return None

    # print(f"[realtime_data_handler.py] -> Failed to fetch station information")
    return None


async def process_target_area_data(data: dict[str, Any]) -> dict[str, Any] | None:
    """Processes RTS data to find data for target areas."""
    global area_status, unified_magnitude
    if not data or "station" not in data:
        return None

    current_station_info = await get_station_info()
    if not current_station_info:
        # print(f"[realtime_data_handler.py] -> Cannot process RTS data: Missing station information")
        return None

    result: dict[str, Any] = {
        "time": data.get("time", time.time() * 1000),
        "updatedAreas": [],
    }

    total_intensity_float_sum: float = 0.0
    counted_stations: int = 0

    for station_id, station_data in data["station"].items():
        station_details = current_station_info.get(station_id)
        if (
            not station_details
            or not station_details.get("info")
            or not station_details["info"]
        ):
            continue

        latest_info = station_details["info"][-1]
        area_code = latest_info.get("code")

        target_area_config = next(
            (area for area in CONFIG["targetAreas"] if area["code"] == area_code),
            None,
        )
        if not target_area_config:
            continue

        pga = float(station_data.get("pga", 0.0))
        # Assuming station_data['i'] is a float or string convertible to float for detailed intensity
        # And station_data['I'] is an integer for intensity level
        intensity_float_val = float(station_data.get("i", 0.0))
        intensity_int_val = int(station_data.get("I", 0))

        # For display, if station_data.get('i') is textual like "5-", it would be used.
        # If it's a float, it's used as is. The current JS seems to treat it as float.
        # For clarity, we can use intensity_to_text for display from integer intensity.
        # However, to match JS, we use station_data.get('i') as intensity_text for area_status.
        # The problem description for JS: `intensityText = stationData.i;`
        # This implies stationData.i itself is the text to be displayed or a numerical value.
        # If `stationData.i` is "5-", then `float("5-")` would fail.
        # Assuming `stationData.i` is numerically convertible if used in calculations.
        # For `area_status['intensity_text']`, using `IntensityCalculator.intensity_to_text(intensity_int_val)`
        # would be more robust for textual display, but JS used `stationData.i`.
        # Let's assume station_data.get('i') is the value to be stored as "text" (could be float string).
        intensity_text_val = str(station_data.get("i", "0"))

        magnitude = IntensityCalculator.estimate_reasonable_magnitude(
            intensity_float_val,
        )

        total_intensity_float_sum += intensity_float_val
        counted_stations += 1

        current_area_stat = area_status[area_code]
        changed = (
            current_area_stat["pga"] != pga
            or current_area_stat["intensity"] != intensity_int_val
        )

        if changed or current_area_stat["lastUpdate"] is None:
            current_area_stat["pga"] = pga
            current_area_stat["intensity"] = intensity_int_val
            # Store the text from station_data.i as per JS logic
            current_area_stat["intensity_text"] = intensity_text_val
            current_area_stat["magnitude"] = f"{magnitude:.1f}"
            current_area_stat["lastUpdate"] = datetime.datetime.now()

            result["updatedAreas"].append(
                {
                    "code": area_code,
                    "name": target_area_config["name"],
                    "pga": pga,
                    "intensityFloat": f"{intensity_float_val:.2f}",
                    "intensity": intensity_int_val,
                    # Use calculated text for this specific report, but status uses direct 'i'
                    "intensityText": IntensityCalculator.intensity_to_text(
                        intensity_int_val,
                    ),
                    "magnitude": f"{magnitude:.1f}",
                    "stationId": station_id,
                    "location": {
                        "lat": latest_info.get("lat"),
                        "lon": latest_info.get("lon"),
                    },
                },
            )

    if counted_stations > 0:
        average_intensity = total_intensity_float_sum / counted_stations
        unified_magnitude = IntensityCalculator.estimate_reasonable_magnitude(
            average_intensity,
        )

    return result


async def fetch_realtime_data() -> list[dict[str, Any]]:
    """Fetches real-time data and returns a list of area statuses."""
    global last_fetch_time, request_counter, area_status

    now = time.time() * 1000  # Current time in milliseconds

    # This condition was part of the original script but might not be desired for an API endpoint
    # if now - last_fetch_time < CONFIG['interval']:
    #     return [area_status[area_cfg['code']] for area_cfg in CONFIG['targetAreas']] # Return current status if too soon

    last_fetch_time = now
    request_counter += 1

    server = get_random_server("lb")
    url = f"https://{server}/api/v2/trem/rts"

    try:
        rts_response = await fetch_data(url, CONFIG["timeout"]["RTS"])
        if rts_response:
            try:
                rts_data = rts_response.json()
            except ValueError:  # Includes JSONDecodeError
                # print(f"[realtime_data_handler.py] -> Failed to decode JSON from RTS: {url}")
                rts_data = None

            if rts_data:
                await process_target_area_data(
                    rts_data,
                )  # This updates global area_status

        # Always return the current state of area_status after attempting to fetch/process
        return [area_status[area_cfg["code"]] for area_cfg in CONFIG["targetAreas"]]

    except Exception:  # Catch any other unexpected error during fetch/process
        # In case of error, return the last known status or an empty list if never populated.
        # This ensures the API endpoint still returns data in the expected format.
        # Consider logging the exception here.
        # print(f"Error fetching/processing real-time data: {error}")
        if area_status:
            return [area_status[area_cfg["code"]] for area_cfg in CONFIG["targetAreas"]]
        return []
