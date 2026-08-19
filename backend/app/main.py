from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from .db.dependencies import get_db
from .db.models import TelemetryRecord
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
def receive_telemetry(
    data: Telemetry,
    db: Session = Depends(get_db)
):
    record = TelemetryRecord(
        device_id=data.device_id,
        timestamp=data.timestamp,

        ldr1_value=data.zone1.ldr1_value,
        pir1_motion=data.zone1.pir1_motion,
        bulb1_state=data.zone1.bulb1_state,

        ldr2_value=data.zone2.ldr2_value,
        pir2_motion=data.zone2.pir2_motion,
        bulb2_state=data.zone2.bulb2_state,

        temperature_c=data.environment.temperature_c,
        humidity_percent=data.environment.humidity_percent,

        fan_state=data.fan.fan_state,

        acs712_sensor_voltage=data.energy.acs712_sensor_voltage,
        current_indication=data.energy.current_indication,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "status": "received",
        "device_id": record.device_id,
        "timestamp": record.timestamp,
        "telemetry_id": record.id,
        "message": "Telemetry stored successfully"
    }


@app.get("/api/v1/telemetry")
def get_telemetry(
    db: Session = Depends(get_db)
):
    records = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .all()
    )

    return records