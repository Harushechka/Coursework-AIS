from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    FINANCING = "financing"
    LEASE = "lease"

class OrderBase(BaseModel):
    customer_id: int
    vehicle_id: int
    payment_method: PaymentMethod = PaymentMethod.CASH
    discount_code: Optional[str] = None
    notes: Optional[str] = None
    customer_notes: Optional[str] = None
    delivery_address: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    payment_method: Optional[PaymentMethod] = None
    discount_code: Optional[str] = None
    notes: Optional[str] = None
    customer_notes: Optional[str] = None
    delivery_address: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None

class OrderStatusUpdate(BaseModel):
    status: OrderStatus

class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus

class Order(OrderBase):
    id: int
    vin: str
    base_price: float
    final_price: float
    currency: str
    status: OrderStatus
    payment_status: PaymentStatus
    applied_discounts: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderHistoryBase(BaseModel):
    order_id: int
    status: OrderStatus
    payment_status: Optional[PaymentStatus] = None
    changed_by: Optional[str] = None
    notes: Optional[str] = None

class OrderHistory(OrderHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True