from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"

class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CLIENT

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None

# Event models for message broker
class EventBase(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict

class OrderEvent(EventBase):
    pass

class PaymentEvent(EventBase):
    pass

class FinancingEvent(EventBase):
    pass

class InsuranceEvent(EventBase):
    pass

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ReportType(str, Enum):
    DAILY_SALES = "daily_sales"
    MONTHLY_REVENUE = "monthly_revenue"
    POPULAR_MODELS = "popular_models"
    SERVICE_EFFECTIVENESS = "service_effectiveness"
    CUSTOMER_ANALYTICS = "customer_analytics"

class ConfigType(str, Enum):
    BRANCH = "branch"
    EMPLOYEE = "employee"
    TARIFF = "tariff"
    ROLE = "role"
    SYSTEM = "system"

# Базовые модели для новых сущностей
class CustomerBase(BaseModel):
    user_id: Optional[int] = None
    first_name: str
    last_name: str
    phone: str
    email: str
    address: Optional[str] = None

class VehicleBase(BaseModel):
    make: str
    model: str
    year: int
    vin: str
    license_plate: Optional[str] = None
    color: Optional[str] = None
    mileage: Optional[int] = None

# Модели событий для RabbitMQ
class BookingEvent(EventBase):
    pass

class NotificationEvent(EventBase):
    pass

class ReportEvent(EventBase):
    pass

class LogEvent(EventBase):
    pass

class ConfigEvent(EventBase):
    pass