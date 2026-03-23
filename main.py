import asyncio
import json
import os
import random
import time
from collections import deque
from typing import Dict, Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="IoT-Based Smart Monitoring Dashboard")

# ✅ Serve static folder safely
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# Oil Simulator State
# ================================
DEVICE_ID = "oil-sensor-001"

DEVICE_INFO = {
    "device_id": DEVICE_ID,
    "model": "KitchenOilMonitor v1",
    "firmware": "1.0.0"
}

state = {
    "running": True,
    "oil_level_ml": 1000.0,
    "capacity_ml": 1000.0,
    "last_update": time.time(),
}

settings = {
    "drain_rate_min_ml": 1.0,
    "drain_rate_max_ml": 5.0,
    "update_interval_seconds": 2.0,
    "stop_on_empty": False
}

historical_data = deque(maxlen=1000)


def clamp(v, a, b):
    return max(a, min(b, v))


# ================================
# SSE Generator
# ================================
async def event_generator():
    while True:
        if state["running"]:
            drain = random.uniform(
                settings["drain_rate_min_ml"],
                settings["drain_rate_max_ml"]
            )

            new_level = max(0.0, state["oil_level_ml"] - drain)
            state["oil_level_ml"] = round(new_level, 2)
            state["last_update"] = time.time()

            if state["oil_level_ml"] <= 0 and settings["stop_on_empty"]:
                state["running"] = False

        oil_percent = 0.0
        if state["capacity_ml"] > 0:
            oil_percent = round(
                (state["oil_level_ml"] / state["capacity_ml"]) * 100.0, 2
            )

        payload = {
            "timestamp": int(time.time()),
            "device_id": DEVICE_ID,
            "oil_level_ml": state["oil_level_ml"],
            "oil_percent": oil_percent,
            "capacity_ml": state["capacity_ml"],
            "running": state["running"]
        }

        historical_data.append(payload.copy())

        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(settings["update_interval_seconds"])


# ================================
# HOME PAGE
# ================================
@app.get("/", response_class=HTMLResponse)
async def homepage():
    return HTMLResponse(content=HTML_PAGE)


# ================================
# API ROUTES
# ================================
@app.get("/api/stream")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/state")
async def get_state():
    return JSONResponse({"state": state, "settings": settings})


@app.post("/api/settings")
async def update_settings(payload: Dict):
    for k, v in payload.items():
        if k in settings:
            try:
                if k == "stop_on_empty":
                    settings[k] = bool(v)
                else:
                    settings[k] = float(v)
            except:
                pass

    return {"ok": True}


@app.post("/api/control")
async def control(payload: Dict):
    cmd = (payload.get("cmd") or "").lower()

    if cmd == "start":
        state["running"] = True
    elif cmd == "stop":
        state["running"] = False
    elif cmd == "refill":
        state["oil_level_ml"] = state["capacity_ml"]

    return {"ok": True}


@app.get("/api/device-info")
async def device_info():
    return DEVICE_INFO


@app.get("/api/history")
async def history(n: Optional[int] = 10):
    data = list(historical_data)
    return data[-n:]


# ================================
# HTML PAGE (FINAL UI)
# ================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IoT-Based Smart Monitoring Dashboard</title>

  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      font-family: "Segoe UI", Arial, sans-serif;
      color: white;
      padding: 20px;
      box-sizing: border-box;

      background-color: #0f172a;

      background-image:
        linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)),
        url("/static/iot-bg.png");

      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
    }

    .container {
      width: 90%;
      max-width: 750px;
      text-align: center;
      background: rgba(255,255,255,0.08);
      padding: 40px;
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.4);
      backdrop-filter: blur(8px);
    }

    h1 {
      font-size: 32px;
      margin-bottom: 10px;
    }

    .subtitle {
      color: #cbd5e1;
      margin-bottom: 20px;
    }

    .description {
      font-size: 15px;
      line-height: 1.6;
      color: #e2e8f0;
      margin-bottom: 30px;
    }

    .btn {
      display: inline-block;
      margin: 10px;
      padding: 14px 26px;
      font-size: 16px;
      font-weight: bold;
      border-radius: 10px;
      text-decoration: none;
      transition: 0.3s;
      color: white;
    }

    .btn-oil {
      background: linear-gradient(135deg, #f59e0b, #d97706);
    }

    .btn-watch {
      background: linear-gradient(135deg, #10b981, #059669);
    }

    .btn:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    }

    .footer {
      margin-top: 20px;
      font-size: 13px;
      color: #94a3b8;
    }

    @media (max-width: 600px) {
      .container {
        padding: 25px;
      }

      h1 {
        font-size: 24px;
      }

      .btn {
        display: block;
        margin: 12px auto;
      }
    }
  </style>
</head>

<body>
  <div class="container">

    <h1>IoT-Based Smart Monitoring Dashboard</h1>

    <div class="subtitle">
      Choose a system to monitor real-time IoT data
    </div>

    <div class="description">
      This platform demonstrates IoT-based smart monitoring applications,
      integrating real-time cooking oil level tracking and wearable health monitoring.
      It simulates how connected devices collect, process, and visualize data
      to enhance efficiency, safety, and intelligent decision-making in modern environments.
    </div>

    <a href="https://cooking-oil-iot-simulator.onrender.com/" class="btn btn-oil" target="_blank">
      🛢️ Cooking Oil IoT Simulator
    </a>

    <a href="https://smartwatch-simulator.onrender.com/" class="btn btn-watch" target="_blank">
      ⌚ Smartwatch Simulator
    </a>

    <div class="footer">
      Powered by FastAPI • IoT Simulation Platform
    </div>

  </div>
</body>
</html>
"""