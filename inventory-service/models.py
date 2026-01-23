from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class InventoryStatus(str, enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    MAINTENANCE = "maintenance"

class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, unique=True, index=True, nullable=False)
    vin = Column(String(17), unique=True, index=True, nullable=False)
    stock_quantity = Column(Integer, default=1)
    available_quantity = Column(Integer, default=1)
    reserved_quantity = Column(Integer, default=0)
    sold_quantity = Column(Integer, default=0)
    status = Column(Enum(InventoryStatus), default=InventoryStatus.AVAILABLE)
    location = Column(String(100))  # Место хранения
    purchase_price = Column(Float)  # Цена закупки
    selling_price = Column(Float)   # Рекомендованная цена продажи
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(String(500))