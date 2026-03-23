# Smart Kitchen Health & Oil Monitoring System

This project combines two IoT simulation modules into one FastAPI application:

1. Smartwatch health monitoring
2. Cooking oil level monitoring

## Features

- Real-time smartwatch simulation
- Real-time cooking oil simulation
- Combined live dashboard
- Separate APIs for both modules
- Combined API for unified data
- Historical records
- Configurable settings
- Start / Stop / Reset / Refill controls

## Project Structure

smart-kitchen-monitor/
├── main.py
├── requirements.txt
├── render.yaml
├── start.sh
├── README.md
└── static/
    ├── index.html
    └── styles.css

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000