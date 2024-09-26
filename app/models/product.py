from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.database import Base
from datetime import datetime
import pytz

kiev_tz = pytz.timezone('Europe/Kiev')

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    price = Column(Float)
    quantity = Column(Integer)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(kiev_tz))
