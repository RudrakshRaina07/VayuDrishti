import requests
import random
import os

AQI_API_KEY = os.getenv("AQI_API_KEY")

def get_aqi(city="Delhi"):
    """
    External AQI provider.
    Can be replaced by IoT sensors later.
    """
    if not AQI_API_KEY:
        # fallback (demo safety)
        return random.randint(80, 180)

    try:
        url = f"https://api.waqi.info/feed/{city}/?token={AQI_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("status") == "ok":
            return int(data["data"]["aqi"])
    except Exception as e:
        print("AQI API error:", e)

    return random.randint(80, 180)
