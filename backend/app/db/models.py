from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id: Mapped[str] = mapped_column(
        String,
        index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        index=True
    )

    ldr1_value: Mapped[int] = mapped_column(Integer)
    pir1_motion: Mapped[bool] = mapped_column(Boolean)
    bulb1_state: Mapped[bool] = mapped_column(Boolean)

    ldr2_value: Mapped[int] = mapped_column(Integer)
    pir2_motion: Mapped[bool] = mapped_column(Boolean)
    bulb2_state: Mapped[bool] = mapped_column(Boolean)

    temperature_c: Mapped[float] = mapped_column(Float)
    humidity_percent: Mapped[float] = mapped_column(Float)

    fan_state: Mapped[bool] = mapped_column(Boolean)

    acs712_sensor_voltage: Mapped[float] = mapped_column(Float)

    current_indication: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True
    )

    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id: Mapped[str] = mapped_column(
        String,
        index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        index=True
    )

    event_type: Mapped[str] = mapped_column(
        String,
        index=True
    )

    source: Mapped[str] = mapped_column(
        String
    )

    message: Mapped[str] = mapped_column(
        String
    )