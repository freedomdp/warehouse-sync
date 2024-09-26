from sqlalchemy import Column, DateTime
from app.db.base import Base

class StartupTime(Base):
    __tablename__ = "startup_time"
    id = Column(DateTime, primary_key=True, index=True)
