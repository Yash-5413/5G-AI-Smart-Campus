from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .db.dependencies import get_db
from .db.models import Device, Event, TelemetryRecord
from .db.init_db import init_db
from .models import Telemetry
from .analytics import get_latest_insights, get_historical_insights, get_anomaly_summary


app = FastAPI()

init_db()


@app.get("/dashboard")
def dashboard():
    return FileResponse(
        "backend/app/static/dashboard.html"
    )


OFFLINE_TIMEOUT_SECONDS = 60

def create_event(
    db: Session,
    device_id: str,
    timestamp: datetime,
    event_type: str,
    source: str,
    message: str
):
    event = Event(
        device_id=device_id,
        timestamp=timestamp,
        event_type=event_type,
        source=source,
        message=message
    )
    db.add(event)

    print(
        f"EVENT CREATED: {event_type} | "
        f"{source} | {message}"
    )


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
    received_at = datetime.now(timezone.utc)

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
    
    db.flush()

    previous = (
        db.query(TelemetryRecord)
        .filter(
            TelemetryRecord.device_id == data.device_id,
            TelemetryRecord.id != record.id
        )
        .order_by(
            TelemetryRecord.timestamp.desc()
        )
        .first()
    )


    if previous is not None:

        if (
            not previous.pir1_motion
            and data.zone1.pir1_motion
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "MOTION_DETECTED",
                "ZONE_1",
                "Motion detected in Zone 1"
            )

        if (
            previous.pir1_motion
            and not data.zone1.pir1_motion
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "MOTION_CLEARED",
                "ZONE_1",
                "Motion cleared in Zone 1"
            )

        if (
            not previous.bulb1_state
            and data.zone1.bulb1_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "BULB_TURNED_ON",
                "ZONE_1",
                "Zone 1 bulb turned ON"
            )

        if (
            previous.bulb1_state
            and not data.zone1.bulb1_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "BULB_TURNED_OFF",
                "ZONE_1",
                "Zone 1 bulb turned OFF"
            )

        if (
            not previous.pir2_motion
            and data.zone2.pir2_motion
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "MOTION_DETECTED",
                "ZONE_2",
                "Motion detected in Zone 2"
            )

        if (
            previous.pir2_motion
            and not data.zone2.pir2_motion
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "MOTION_CLEARED",
                "ZONE_2",
                "Motion cleared in Zone 2"
            )

        if (
            not previous.bulb2_state
            and data.zone2.bulb2_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "BULB_TURNED_ON",
                "ZONE_2",
                "Zone 2 bulb turned ON"
            )

        if (
            previous.bulb2_state
            and not data.zone2.bulb2_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "BULB_TURNED_OFF",
                "ZONE_2",
                "Zone 2 bulb turned OFF"
            )

        if (
            not previous.fan_state
            and data.fan.fan_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "FAN_TURNED_ON",
                "FAN",
                "Fan turned ON"
            )

        if (
            previous.fan_state
            and not data.fan.fan_state
        ):
            create_event(
                db,
                data.device_id,
                data.timestamp,
                "FAN_TURNED_OFF",
                "FAN",
                "Fan turned OFF"
            )

    device = (
        db.query(Device)
        .filter(Device.device_id == data.device_id)
        .first()
    )
    if device is None:
        device = Device(
            device_id=data.device_id,
            last_seen=received_at,
            is_online=True
        )
        db.add(device)
    else:
        device.last_seen = received_at
        device.is_online = True

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
def get_telemetry(db: Session = Depends(get_db)):
    return (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .all()
    )


@app.get("/api/v1/telemetry/latest")
def get_latest_telemetry(db: Session = Depends(get_db)):
    record = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )

    if record is None:
        return {
            "status": "no_data",
            "message": "No telemetry records found"
        }

    return record

@app.get("/api/v1/events")
def get_events(db: Session = Depends(get_db)):
    return (
        db.query(Event)
        .order_by(Event.timestamp.desc())
        .limit(10)
        .all()
    )

def update_device_status(device):
    if device.last_seen is None:
        device.is_online = False
        return

    last_seen = device.last_seen

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    elapsed_seconds = (
        datetime.now(timezone.utc) - last_seen
    ).total_seconds()

    device.is_online = elapsed_seconds <= OFFLINE_TIMEOUT_SECONDS


@app.get("/api/v1/devices")
def get_devices(db: Session = Depends(get_db)):
    devices = (
        db.query(Device)
        .order_by(Device.device_id)
        .all()
    )

    response = []

    for device in devices:
        update_device_status(device)

        response.append({
            "id": device.id,
            "device_id": device.device_id,
            "last_seen": device.last_seen,
            "is_online": device.is_online
        })

    db.commit()

    return response


@app.get("/api/v1/devices/{device_id}")
def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    device = (
        db.query(Device)
        .filter(Device.device_id == device_id)
        .first()
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found"
        )

    update_device_status(device)

    response = {
        "id": device.id,
        "device_id": device.device_id,
        "last_seen": device.last_seen,
        "is_online": device.is_online
    }

    db.commit()

    return response

@app.get("/api/v1/analytics/latest")
def get_latest_analytics(
    db: Session = Depends(get_db)
):
    return get_latest_insights(db)


@app.get("/api/v1/analytics/historical")
def get_historical_analytics(
    db: Session = Depends(get_db)
):
    return get_historical_insights(db)


@app.get("/api/v1/analytics/anomalies")
def get_anomaly_analytics(
    db: Session = Depends(get_db)
):
    return get_anomaly_summary(db)


@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    latest = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.timestamp.desc())
        .first()
    )

    if latest is None:
        return {
            "status": "no_data",
            "message": "No telemetry data available"
        }

    device = (
        db.query(Device)
        .filter(Device.device_id == latest.device_id)
        .first()
    )

    if device is not None:
        update_device_status(device)
        db.commit()

    return {
        "device": {
            "device_id": latest.device_id,
            "is_online": (
                device.is_online
                if device is not None
                else False
            ),
            "last_seen": (
                device.last_seen
                if device is not None
                else None
            )
        },

        "zone1": {
            "ldr1_value": latest.ldr1_value,
            "pir1_motion": latest.pir1_motion,
            "bulb1_state": latest.bulb1_state
        },

        "zone2": {
            "ldr2_value": latest.ldr2_value,
            "pir2_motion": latest.pir2_motion,
            "bulb2_state": latest.bulb2_state
        },

        "environment": {
            "temperature_c": latest.temperature_c,
            "humidity_percent": latest.humidity_percent
        },

        "fan": {
            "fan_state": latest.fan_state
        },

        "energy": {
            "acs712_sensor_voltage": latest.acs712_sensor_voltage,
            "current_indication": latest.current_indication,
            "measurement_status": "experimental"
        },

        "telemetry_timestamp": latest.timestamp
    }

