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
    email: str
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    driver_license: Optional[str] = None
    created_at: Optional[datetime] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class VehicleBase(BaseModel):
    make: str
    model: str
    year: int
    vin: str
    mileage: Optional[int] = None
    price: float
    status: str = "available"
    description: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InventoryBase(BaseModel):
    vehicle_id: int
    location: str
    condition: str = "excellent"
    notes: Optional[str] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    customer_id: int
    vehicle_id: int
    total_price: float
    status: str = "pending"
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    order_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    status: str = "pending"

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class FinancingBase(BaseModel):
    customer_id: int
    vehicle_id: int
    loan_amount: float
    interest_rate: float
    term_months: int
    monthly_payment: float
    status: str = "pending"

class FinancingCreate(FinancingBase):
    pass

class FinancingResponse(FinancingBase):
    id: int
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InsuranceBase(BaseModel):
    customer_id: int
    vehicle_id: int
    policy_type: str
    coverage_amount: float
    premium: float
    start_date: datetime
    end_date: datetime
    status: str = "active"

class InsuranceCreate(InsuranceBase):
    pass

class InsuranceResponse(InsuranceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    customer_id: int
    technician_id: Optional[int] = None
    service_type: str
    scheduled_date: datetime
    duration_minutes: int
    status: AppointmentStatus = AppointmentStatus.PENDING
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    recipient_email: str
    recipient_phone: Optional[str] = None
    notification_type: NotificationType
    subject: str
    message: str
    status: NotificationStatus = NotificationStatus.PENDING

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: int
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LogBase(BaseModel):
    service_name: str
    level: LogLevel
    message: str
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class LogCreate(LogBase):
    pass

class LogResponse(LogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    report_type: ReportType
    parameters: dict
    generated_by: int
    status: str = "pending"

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    id: int
    file_path: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConfigBase(BaseModel):
    config_type: ConfigType
    key: str
    value: str
    description: Optional[str] = None
    is_active: bool = True

class ConfigCreate(ConfigBase):
    pass

class ConfigResponse(ConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    name: str
    description: str
    duration_minutes: int
    price: float
    is_active: bool = True

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TechnicianBase(BaseModel):
    user_id: int
    specialization: str
    experience_years: int
    rating: Optional[float] = None
    is_available: bool = True

class TechnicianCreate(TechnicianBase):
    pass

class TechnicianResponse(TechnicianBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ServiceSlotBase(BaseModel):
    technician_id: int
    service_date: datetime
    start_time: str
    end_time: str
    is_available: bool = True

class ServiceSlotCreate(ServiceSlotBase):
    pass

class ServiceSlotResponse(ServiceSlotBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Event models for message broker
class AppointmentEvent(EventBase):
    pass

class NotificationEvent(EventBase):
    pass

class ReportEvent(EventBase):
    pass

class LogEvent(EventBase):
    pass

class ConfigEvent(EventBase):
    pass