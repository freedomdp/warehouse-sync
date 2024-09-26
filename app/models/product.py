from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    code = Column(String(255))
    article = Column(String(255))
    price = Column(Float)
    sale_price = Column(Float)
    min_price = Column(Float)
    archived = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Product(id={self.id}, external_id='{self.external_id}', name='{self.name}', code='{self.code}', article='{self.article}', price={self.price})>"
