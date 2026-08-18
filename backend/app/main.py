from fastapi import FastAPI
from .models import Telemetry

app = FastAPI()


@app.get("/")
def home():
    return {"message": "5G AI Smart Campus backend is running!"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "5G AI Smart Campus backend"
    }


@app.post("/api/v1/telemetry")
def receive_telemetry(data: Telemetry):
    return {
        "status": "received",
        "device_id": data.device_id,
        "message": "Telemetry received successfully"
    }