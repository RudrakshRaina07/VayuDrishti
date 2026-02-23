from fastapi import FastAPI
from pydantic import BaseModel
import json
import time

app = FastAPI()

DATA_FILE = "traffic_input.jsonl"

class TrafficIn(BaseModel):
    junction: str
    density: int

@app.post("/ingest/traffic")
def ingest_traffic(data: TrafficIn):
    record = {
        "junction": data.junction,
        "density": data.density,
        "timestamp": int(time.time()),
    }

    with open(DATA_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return {"status": "ok"}
