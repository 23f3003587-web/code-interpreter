from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics
from typing import List, Dict, Any

app = FastAPI()

# Enable CORS for any origin (as required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data once at startup (adjust key names if your JSON structure differs)
with open("telemetry.json", "r") as f:
    TELEMETRY_DATA: List[Dict[str, Any]] = json.load(f)

def calculate_p95(data: List[float]) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = int(0.95 * (len(sorted_data) - 1))
    return float(sorted_data[index])

@app.post("/metrics")
async def get_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        # Filter records for this region (adjust field names based on your telemetry.json)
        region_data = [r for r in TELEMETRY_DATA if r.get("region") == region]
        
        latencies = [float(r.get("latency_ms", 0)) for r in region_data if "latency_ms" in r]
        uptimes = [float(r.get("uptime", 0)) for r in region_data if "uptime" in r]  # adjust key if needed

        avg_latency = statistics.mean(latencies) if latencies else 0.0
        p95_latency = calculate_p95(latencies)
        avg_uptime = statistics.mean(uptimes) if uptimes else 0.0
        breaches = sum(1 for lat in latencies if lat > threshold_ms)

        result[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches
        }

    return result