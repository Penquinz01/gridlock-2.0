import random
import time
from datetime import datetime
import requests

# Coordinates corresponding to police stations 0 to 53 resolved from the dataset
POLICE_STATIONS_COORDS = [
    {'police_station': 0, 'latitude': 12.9431035, 'longitude': 77.6220445},
    {'police_station': 1, 'latitude': 12.96672, 'longitude': 77.6093294},
    {'police_station': 2, 'latitude': 12.9238693, 'longitude': 77.5536044},
    {'police_station': 3, 'latitude': 13.0253205, 'longitude': 77.6400845},
    {'police_station': 4, 'latitude': 12.9392829, 'longitude': 77.5596125},
    {'police_station': 5, 'latitude': 12.9188682, 'longitude': 77.6687736},
    {'police_station': 6, 'latitude': 12.94457, 'longitude': 77.5274017},
    {'police_station': 7, 'latitude': 12.9688926, 'longitude': 77.569795},
    {'police_station': 8, 'latitude': 13.0467058, 'longitude': 77.5036495},
    {'police_station': 9, 'latitude': 13.1511992, 'longitude': 77.620242},
    {'police_station': 10, 'latitude': 12.95836, 'longitude': 77.5776317},
    {'police_station': 11, 'latitude': 12.973175, 'longitude': 77.6003961},
    {'police_station': 12, 'latitude': 13.2644465, 'longitude': 77.7187627},
    {'police_station': 13, 'latitude': 12.8636494, 'longitude': 77.6725849},
    {'police_station': 14, 'latitude': 12.9635109, 'longitude': 77.6642122},
    {'police_station': 15, 'latitude': 12.9218755, 'longitude': 77.6451585},
    {'police_station': 16, 'latitude': 12.975285, 'longitude': 77.6256902},
    {'police_station': 17, 'latitude': 12.9641056, 'longitude': 77.5825203},
    {'police_station': 18, 'latitude': 13.0664854, 'longitude': 77.5998755},
    {'police_station': 19, 'latitude': 13.0373543, 'longitude': 77.6540442},
    {'police_station': 20, 'latitude': 12.9936273, 'longitude': 77.5844677},
    {'police_station': 21, 'latitude': 12.8569988, 'longitude': 77.5889807},
    {'police_station': 22, 'latitude': 12.8955737, 'longitude': 77.5999},
    {'police_station': 23, 'latitude': 13.0414238, 'longitude': 77.545608},
    {'police_station': 24, 'latitude': 12.9233517, 'longitude': 77.5904883},
    {'police_station': 25, 'latitude': 12.9667047, 'longitude': 77.6615983},
    {'police_station': 26, 'latitude': 12.9513113, 'longitude': 77.4994888},
    {'police_station': 27, 'latitude': 13.0085677, 'longitude': 77.6131497},
    {'police_station': 28, 'latitude': 13.0008457, 'longitude': 77.6813712},
    {'police_station': 29, 'latitude': 12.9146696, 'longitude': 77.5640607},
    {'police_station': 30, 'latitude': 12.9838737, 'longitude': 77.5286068},
    {'police_station': 31, 'latitude': 12.9328703, 'longitude': 77.4879814},
    {'police_station': 32, 'latitude': 13.0633917, 'longitude': 77.5933483},
    {'police_station': 33, 'latitude': 12.9071221, 'longitude': 77.6286395},
    {'police_station': 34, 'latitude': 12.9789228, 'longitude': 77.5644032},
    {'police_station': 35, 'latitude': 12.9995223, 'longitude': 77.6827499},
    {'police_station': 36, 'latitude': 13.0127301, 'longitude': 77.5545135},
    {'police_station': 37, 'latitude': 12.9077383, 'longitude': 77.6005709},
    {'police_station': 38, 'latitude': 13.0753282, 'longitude': 77.4370383},
    {'police_station': 39, 'latitude': 13.0400041, 'longitude': 77.5180991},
    {'police_station': 40, 'latitude': 12.9873133, 'longitude': 77.6163481},
    {'police_station': 41, 'latitude': 13.0078566, 'longitude': 77.5920655},
    {'police_station': 42, 'latitude': 13.0192138, 'longitude': 77.5395595},
    {'police_station': 43, 'latitude': 13.0061469, 'longitude': 77.5794348},
    {'police_station': 44, 'latitude': 12.9847423, 'longitude': 77.574706},
    {'police_station': 45, 'latitude': 12.9856042, 'longitude': 77.5977438},
    {'police_station': 46, 'latitude': 12.8893347, 'longitude': 77.5379823},
    {'police_station': 47, 'latitude': 12.9763384, 'longitude': 77.575645},
    {'police_station': 48, 'latitude': 12.9511354, 'longitude': 77.5739687},
    {'police_station': 49, 'latitude': 12.976, 'longitude': 77.5452252},
    {'police_station': 50, 'latitude': 12.8966387, 'longitude': 77.7202071},
    {'police_station': 51, 'latitude': 12.955622, 'longitude': 77.5857083},
    {'police_station': 52, 'latitude': 13.114305, 'longitude': 77.60655},
    {'police_station': 53, 'latitude': 13.0309717, 'longitude': 77.5364661}
]

# Set to True to seed local server, or False to seed live hosted server
SEED_LOCAL = False

if SEED_LOCAL:
    API_URL = 'http://localhost:8000/report'
else:
    API_URL = 'https://gridlock-backend.janbaas.me/report'

def seed_database():
    print(f"Seeding database via API endpoint: {API_URL}")
    print("Populating exactly 1 active incident per police station (Stations 0-53)...")
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    success_count = 0
    
    for idx, entry in enumerate(POLICE_STATIONS_COORDS):
        ps_id = entry['police_station']
        lat = entry['latitude']
        lon = entry['longitude']
        
        # Randomize cause & vehicle type (vehicles restricted to 0-9 to comply with schema bounds)
        event_cause = random.randint(0, 17)
        veh_type = random.randint(0, 9)
        
        payload = {
            "latitude": lat,
            "longitude": lon,
            "event_cause": event_cause,
            "time": timestamp,
            "veh_type": veh_type,
            "description": "Seeded incident for dashboard verification." if event_cause == 17 else None
        }
        
        try:
            resp = requests.post(API_URL, json=payload, timeout=10)
            if resp.status_code == 200:
                success_count += 1
                print(f"[{idx+1}/54] Successfully seeded police station #{ps_id:02d}")
            else:
                print(f"[{idx+1}/54] Failed for station #{ps_id:02d} (Status: {resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[{idx+1}/54] Network error for station #{ps_id:02d}: {e}")
            
        time.sleep(0.1)  # Prevention against rate limiting
        
    print(f"\nFinished seeding! Successfully created {success_count} / 54 incidents.")

if __name__ == '__main__':
    seed_database()
