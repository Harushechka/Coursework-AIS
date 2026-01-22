from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogSource(str, enum.Enum):
    AUTH = "auth"
    PAYMENT = "payment"
    SALES = "sales"
    INVENTORY = "inventory"
    CUSTOMER = "customer"
    VEHICLE = "vehicle"
    FINANCING = "financing"
    INSURANCE = "insurance"
    API_GATEWAY = "api_gateway"
    REPORTING = "reporting"
    SYSTEM = "system"

class ApplicationLog(Base):
    __tablename__ = "application_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    level = Column(Enum(LogLevel), nullable=False, index=True)
    source = Column(Enum(LogSource), nullable=False, index=True)
    service = Column(String(100), nullable=False)
    
    message = Column(Text, nullable=False)
    correlation_id = Column(String(100), index=True)
    request_id = Column(String(100))
    user_id = Column(Integer, index=True)
    
    endpoint = Column(String(200))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    additional_data = Column(JSON, default=dict)
    stack_trace = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    
    service = Column(String(100), nullable=False, index=True)
    instance_id = Column(String(100))
    
    tags = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditTrail(Base):
    __tablename__ = "audit_trails"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    user_id = Column(Integer, index=True)
    user_email = Column(String(200))
    user_role = Column(String(50))
    
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    changes = Column(JSON)
    meta_info = Column(JSON, default=dict)  # <-- ИЗМЕНИТЬ НА meta_info или audit_metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ErrorReport(Base):
    __tablename__ = "error_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    error_code = Column(String(100), index=True)
    error_type = Column(String(100))
    
    service = Column(String(100), nullable=False, index=True)
    endpoint = Column(String(200))
    
    message = Column(Text, nullable=False)
    stack_trace = Column(Text)
    
    request_data = Column(JSON)
    request_headers = Column(JSON)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(Integer)
    resolution_notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())