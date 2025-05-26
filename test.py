import requests
import random
from datetime import datetime, timedelta
import uuid
import time
def generate_random_earthquake():
    # Generate random data
    magnitude = 3
    intensity = random.randint(3, 7)
    
    # Generate random time within the last 24 hours
    current_time = datetime.utcnow()

    
    # Generate random location
    locations = ["Taipei", "Hsinchu", "Taichung", "Tainan"]
    location = random.choice(locations)
    
    return {
        "id": str(uuid.uuid4()),
        "source": "asdasd",
        "originTime": current_time.isoformat() + "Z",
        "epicenterLocation": "aaaaaaa",
        "magnitudeValue": 3,
        "focalDepth": random.randint(1, 100),
        "shakingArea": [
            {
                "countyName": "Taipei",
                "areaIntensity": intensity
            }
        ]
    }

def main():
    url = "http://localhost:8000/api/earthquake/"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    print("Sending 2 random earthquake data points...")
    
    for i in range(1):
        data = generate_random_earthquake()
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\nEarthquake {i+1}:")
        print(f"Location: {data['epicenterLocation']}")
        print(f"Magnitude: {data['magnitudeValue']}")
        print(f"Intensity: {data['shakingArea'][0]['areaIntensity']}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error: {response.text}")
            
        time.sleep(1)

if __name__ == "__main__":
    main()
