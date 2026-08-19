from datetime import datetime

from pydantic import BaseModel


class Zone1Telemetry(BaseModel):
    ldr1_value: int
    pir1_motion: bool
    bulb1_state: bool


class Zone2Telemetry(BaseModel):
    ldr2_value: int
    pir2_motion: bool
    bulb2_state: bool


class EnvironmentTelemetry(BaseModel):
    temperature_c: float
    humidity_percent: float


class FanTelemetry(BaseModel):
    fan_state: bool


class EnergyTelemetry(BaseModel):
    acs712_sensor_voltage: float
    current_indication: float | None = None


class Telemetry(BaseModel):
    device_id: str
    timestamp: datetime
    zone1: Zone1Telemetry
    zone2: Zone2Telemetry
    environment: EnvironmentTelemetry
    fan: FanTelemetry
    energy: EnergyTelemetry