from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

Base = declarative_base()

class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_SHIPPING = "free_shipping"
    BUY_ONE_GET_ONE = "bogo"

class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    discount_type = Column(Enum(DiscountType), nullable=False)
    value = Column(Float, nullable=False)  # Процент или фиксированная сумма
    min_purchase_amount = Column(Float, default=0)
    max_discount_amount = Column(Float, nullable=True)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    usage_limit = Column(Integer, nullable=True)  # Максимальное количество использований
    used_count = Column(Integer, default=0)
    applies_to_all_vehicles = Column(Boolean, default=True)
    vehicle_ids = Column(String)  # JSON массив ID автомобилей, к которым применяется
    customer_group = Column(String(50))  # "new_customer", "loyal_customer", "all"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, nullable=False)
    base_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    customer_id = Column(Integer, nullable=True)
    discount_code = Column(String(50), nullable=True)
    applied_discounts = Column(String)  # JSON массив примененных скидок
    calculation_date = Column(DateTime, default=datetime.utcnow)
    order_id = Column(Integer, nullable=True)