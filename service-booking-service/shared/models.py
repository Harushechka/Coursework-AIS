from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

# Enums
class AppointmentType(str, enum.Enum):
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    TIRE_SERVICE = "tire_service"
    INSPECTION = "inspection"
    OTHER = "other"

class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class ServiceSlotStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"

# Таблица мастеров/техников
class Technician(Base):
    __tablename__ = "technicians"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, nullable=False)  # ID из employees (admin-config-service)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    specialization = Column(String(100))  # ДВС, электрика, шиномонтаж
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица слотов времени
class ServiceSlot(Base):
    __tablename__ = "service_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, nullable=False)  # Филиал
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    slot_date = Column(DateTime, nullable=False)  # Дата и время слота
    duration_minutes = Column(Integer, default=60)  # Длительность в минутах
    status = Column(SQLEnum(ServiceSlotStatus), default=ServiceSlotStatus.AVAILABLE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связь
    technician = relationship("Technician")

# Таблица записей на сервис
class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, nullable=False)  # ID клиента из customer-service
    vehicle_id = Column(Integer, nullable=False)  # ID автомобиля из vehicle-catalog-service
    branch_id = Column(Integer, nullable=False)  # Филиал
    slot_id = Column(Integer, ForeignKey("service_slots.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("technicians.id"), nullable=True)
    
    appointment_type = Column(SQLEnum(AppointmentType), nullable=False)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING)
    
    description = Column(Text)  # Описание проблемы/работы
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    notes = Column(Text)  # Заметки мастера
    customer_notes = Column(Text)  # Пожелания клиента
    
    created_by = Column(Integer)  # user_id создавшего запись
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    slot = relationship("ServiceSlot")
    technician = relationship("Technician")

# Таблица услуг
class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # ТО, ремонт, шины и т.д.
    duration_minutes = Column(Integer, default=60)
    base_price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица связи записей и услуг
class AppointmentService(Base):
    __tablename__ = "appointment_services"
    
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    appointment = relationship("Appointment")
    service = relationship("Service")