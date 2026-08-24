from sqlalchemy.orm import Session

from .db.models import TelemetryRecord


def get_latest_insights(db: Session):
    record = (
        db.query(TelemetryRecord)
        .filter(
            TelemetryRecord.device_id == "esp32-01"
        )
        .order_by(
            TelemetryRecord.timestamp.desc()
        )
        .first()
    )

    if record is None:
        return {
            "status": "no_data",
            "insights": []
        }

    insights = []

    # Occupancy / motion insight
    if record.pir1_motion or record.pir2_motion:
        insights.append(
            "Motion detected in the campus zones."
        )
    else:
        insights.append(
            "No motion detected in the monitored zones."
        )

    # Temperature / cooling insight
    if record.temperature_c >= 35:
        if record.fan_state:
            insights.append(
                "High temperature detected and fan is running."
            )
        else:
            insights.append(
                "High temperature detected while fan is OFF."
            )
    else:
        insights.append(
            "Temperature is within the current normal range."
        )

    # Lighting insight
    if (
        record.pir1_motion
        and not record.bulb1_state
    ):
        insights.append(
            "Motion detected in Zone 1 while the bulb is OFF."
        )

    if (
        record.pir2_motion
        and not record.bulb2_state
    ):
        insights.append(
            "Motion detected in Zone 2 while the bulb is OFF."
        )

    # Energy insight
    if (
        record.current_indication is not None
        and record.current_indication > 0.5
    ):
        insights.append(
            "Current consumption is relatively high."
        )

    return {
        "status": "ok",
        "device_id": record.device_id,
        "timestamp": record.timestamp,
        "insights": insights
    }