from .database import Base, engine
from .models import TelemetryRecord, Device, Event

def init_db():
    Base.metadata.create_all(bind=engine)