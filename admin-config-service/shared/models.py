from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, JSON, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

# Enums
class ConfigType(str, enum.Enum):
    BRANCH = "branch"
    EMPLOYEE = "employee"
    TARIFF = "tariff"
    ROLE = "role"
    SYSTEM = "system"
    NOTIFICATION = "notification"
    BUSINESS = "business"

class BranchStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"

class EmployeeRole(str, enum.Enum):
    MANAGER = "manager"
    SALES = "sales"
    MECHANIC = "mechanic"
    SUPPORT = "support"
    ADMIN = "admin"

# Таблица филиалов
class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    manager_id = Column(Integer, nullable=True)  # ID менеджера из auth-service
    status = Column(SQLEnum(BranchStatus), default=BranchStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Таблица сотрудников (привязаны к филиалам)
class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # ID из auth-service
    branch_id = Column(Integer, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    position = Column(String(100))
    role = Column(SQLEnum(EmployeeRole), default=EmployeeRole.SALES)
    phone = Column(String(20))
    email = Column(String(100))
    hire_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица тарифов и цен
class Tariff(Base):
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    config_type = Column(SQLEnum(ConfigType), default=ConfigType.TARIFF)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    tariff_metadata = Column('metadata', JSON, default=dict)  # Дополнительные параметры
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица ролей и прав
class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), nullable=False)  # client, manager, admin и т.д.
    service_name = Column(String(50), nullable=False)  # auth, payment, booking и т.д.
    endpoint = Column(String(100), nullable=False)  # /users, /payments/create
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    is_allowed = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица системных настроек
class SystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general")
    is_public = Column(Boolean, default=False)  # Доступно без аутентификации
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Таблица конфигурационных событий
class ConfigChangeLog(Base):
    __tablename__ = "config_change_log"
    
    id = Column(Integer, primary_key=True, index=True)
    config_type = Column(SQLEnum(ConfigType), nullable=False)
    config_id = Column(Integer, nullable=False)  # ID изменяемой конфигурации
    changed_by = Column(Integer, nullable=False)  # user_id
    change_type = Column(String(20))  # create, update, delete
    old_value = Column(Text)
    new_value = Column(Text)
    change_timestamp = Column(DateTime(timezone=True), server_default=func.now())