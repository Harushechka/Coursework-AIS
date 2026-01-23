from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text, JSON, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime, date

Base = declarative_base()

# Enums
class ReportType(str, enum.Enum):
    DAILY_SALES = "daily_sales"
    MONTHLY_REVENUE = "monthly_revenue"
    POPULAR_MODELS = "popular_models"
    SERVICE_EFFECTIVENESS = "service_effectiveness"
    CUSTOMER_ANALYTICS = "customer_analytics"
    INVENTORY_ANALYSIS = "inventory_analysis"
    EMPLOYEE_PERFORMANCE = "employee_performance"

class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class MetricType(str, enum.Enum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    PERCENTAGE = "percentage"
    RATIO = "ratio"

# Таблица отчётов
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    
    parameters = Column(JSON, default=dict)
    filters = Column(JSON, default=dict)
    
    generated_by = Column(Integer)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    file_path = Column(String(500))
    file_format = Column(String(10))
    
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Таблица метрик
class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)
    
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(SQLEnum(MetricType), nullable=False)
    metric_value = Column(Float, nullable=False)
    
    dimension_1 = Column(String(100))
    dimension_2 = Column(String(100))
    dimension_3 = Column(String(100))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица дашбордов
class Dashboard(Base):
    __tablename__ = "dashboards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    layout_config = Column(JSON, default=dict)
    is_public = Column(Boolean, default=False)
    
    created_by = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Таблица виджетов дашборда
class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"
    
    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False)
    
    widget_type = Column(String(50), nullable=False)
    title = Column(String(100), nullable=False)
    
    report_type = Column(SQLEnum(ReportType), nullable=True)
    parameters = Column(JSON, default=dict)
    
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)
    height = Column(Integer, default=3)
    
    refresh_interval_minutes = Column(Integer, default=60)
    last_refreshed = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица кэшированных данных
class CachedData(Base):
    __tablename__ = "cached_data"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(500), unique=True, nullable=False)
    
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    hits = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица событий для аналитики
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=True)
    session_id = Column(String(100))
    
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    
    properties = Column(JSON, default=dict)
    context = Column(JSON, default=dict)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
