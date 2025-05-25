import requests
import json
import random
from datetime import datetime, timedelta
import time

def generate_earthquake_data():
    """Continuously generate simulated earthquake data and send to API every 30 minutes"""
    
    # List of available areas
    available_areas = ["Taipei", "Taichung", "Tainan", "Hsinchu"]
    
    # Epicenter location options
    epicenter_locations = [
        "台北市北投區", "新竹縣竹北市", "台中市西屯區", 
        "台南市安南區", "花蓮縣秀林鄉", "宜蘭縣頭城鎮",
        "南投縣仁愛鄉", "雲林縣斗六市"
    ]
    
    count = 1
    
    while True:
        # Use current time
        current_time = datetime.now()
        
        # Convert to ISO format
        origin_time_iso = current_time.isoformat() + "Z"
        
        # Generate ID using unix timestamp
        unix_timestamp = int(current_time.timestamp())
        earthquake_id = f"{unix_timestamp:x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(100000000000, 999999999999):012x}"
        
        # Randomly select 1-4 areas
        num_areas = random.randint(1, 4)
        selected_areas = random.sample(available_areas, num_areas)
        
        # Generate intensity data for each selected area
        shaking_area = []
        for area in selected_areas:
            shaking_area.append({
                "countyName": area,
                "areaIntensity": random.randint(1, 9)
            })
        
        # Construct request data
        earthquake_data = {
            "id": earthquake_id,
            "source": f"Auto-generated-{count}",
            "originTime": origin_time_iso,
            "epicenterLocation": random.choice(epicenter_locations),
            "magnitudeValue": round(random.uniform(0, 9), 1),
            "focalDepth": random.randint(0, 500),
            "shakingArea": shaking_area
        }
        
        # Send POST request
        try:
            response = requests.post(
                'http://localhost:8000/api/earthquake/',
                headers={
                    'accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                json=earthquake_data
            )
            
            if response.status_code == 200 or response.status_code == 201:
                print(f"✅ Data {count} sent successfully")
                print(f"   Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Magnitude: {earthquake_data['magnitudeValue']}")
                print(f"   Depth: {earthquake_data['focalDepth']} km")
                print(f"   Affected Areas: {[area['countyName'] for area in shaking_area]}")
            else:
                print(f"❌ Failed to send data {count}: {response.status_code}")
                print(f"   Error Message: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error while sending data {count}: {e}")
        
        # Output JSON data for review
        print(f"📝 Data Content: {json.dumps(earthquake_data, indent=2, ensure_ascii=False)}")
        print("-" * 50)
        
        count += 1
        
        # Wait for 30 minutes (1800 seconds)
        print(f"⏰ Waiting 30 minutes before generating next data...")
        time.sleep(1800)

if __name__ == "__main__":
    print("🌍 Starting continuous earthquake data generation and sending...")
    print("⚠️  Program will generate data every 30 minutes. Press Ctrl+C to stop.")
    try:
        generate_earthquake_data()
    except KeyboardInterrupt:
        print("\n🛑 Program stopped.")