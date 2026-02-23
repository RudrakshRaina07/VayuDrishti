"""
VayuDrishti — Real-Time AI Traffic & AQI Stream
CITY + JUNCTION AWARE (STABLE)
"""

import pathway as pw
import random
import time

# ---------------- CONFIG ----------------
CITIES = {
    "Delhi": ["A", "B", "C"],
    "Mumbai": ["D", "E", "F"]
}

# ---------------- SCHEMA ----------------
class Traffic(pw.Schema):
    city: str
    junction: str
    density: int
    aqi: int
    timestamp: int

# ---------------- DATA SOURCE ----------------
rows = []

now = int(time.time())

for city, junctions in CITIES.items():
    for j in junctions:
        rows.append(
            (
                city,
                j,
                random.randint(30, 90),
                random.randint(80, 160),
                now
            )
        )

traffic = pw.debug.table_from_rows(
    schema=Traffic,
    rows=rows
)

# ---------------- AI LOGIC ----------------
optimized = traffic.select(
    city=traffic.city,
    junction=traffic.junction,
    density=traffic.density,
    aqi=traffic.aqi,
    timestamp=traffic.timestamp,

    green_time=pw.apply(
        lambda d: max(20, 120 - d),
        traffic.density
    ),

    pollution_cost=pw.apply(
        lambda d, a: round(d * 0.7 + a * 0.3, 2),
        traffic.density,
        traffic.aqi
    ),
)

# ---------------- OUTPUT ----------------
pw.io.jsonlines.write(
    optimized,
    "live_output.jsonl"
)

if __name__ == "__main__":
    print("🚀 Pathway stream running (city + junction aware)")
    pw.run(monitoring_level=pw.MonitoringLevel.NONE)
