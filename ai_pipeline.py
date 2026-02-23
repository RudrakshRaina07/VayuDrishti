import os
import pathway as pw
import random
import requests

AQI_API_KEY = os.getenv("AQI_API_KEY")

# ---------- LIVE AQI ----------
def get_aqi():
    if not AQI_API_KEY:
        return random.randint(60, 120)

    try:
        url = f"https://api.waqi.info/feed/@3715/?token={AQI_API_KEY}"
        r = requests.get(url, timeout=5)
        data = r.json()

        if data.get("status") == "ok":
            return data["data"]["aqi"]

    except Exception:
        pass

    return random.randint(60, 120)

# ---------- TRAFFIC STREAM ----------
class Traffic(pw.Schema):
    junction: str
    density: int


def traffic_stream():
    rows = [
        {"junction": "A", "density": random.randint(20, 90)},
        {"junction": "B", "density": random.randint(20, 90)},
        {"junction": "C", "density": random.randint(20, 90)},
    ]
    return pw.debug.table_from_rows(rows, schema=Traffic)


table = traffic_stream()


# ---------- AI OPTIMIZATION ----------
optimized = table.select(
    table.junction,
    density=table.density,
    green_time=(120 - table.density),   # simple AI rule
    pollution_cost=(table.density * 0.8),
)

pw.run()
