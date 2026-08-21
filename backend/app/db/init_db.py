from .database import Base, engine
from .models import TelemetryRecord, Device


def init_db():
    Base.metadata.create_all(bind=engine)