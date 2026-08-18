from pydantic import BaseModel


class ZoneTelemetry(BaseModel):
    ldr_value: int
    motion: bool
    bulb_on: bool


class EnvironmentTelemetry(BaseModel):
    temperature: float
    humidity: float


class FanTelemetry(BaseModel):
    fan_on: bool
    current: float | None = None


class Telemetry(BaseModel):
    device_id: str
    zone1: ZoneTelemetry
    zone2: ZoneTelemetry
    environment: EnvironmentTelemetry
    fan: FanTelemetry