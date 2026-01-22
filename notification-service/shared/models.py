from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime

Base = declarative_base()

# Enums
class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SYSTEM = "system"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"
    DELIVERED = "delivered"

class NotificationChannel(str, enum.Enum):
    USER_REGISTRATION = "user.registration"
    APPOINTMENT_BOOKING = "appointment.booking"
    PAYMENT_CONFIRMATION = "payment.confirmation"
    ORDER_STATUS = "order.status"
    SYSTEM_ALERT = "system.alert"
    PROMOTIONAL = "promotional"

# Таблица шаблонов уведомлений
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.EMAIL)
    
    subject_template = Column(Text)  # Шаблон темы (для email)
    body_template = Column(Text, nullable=False)  # Шаблон тела
    language = Column(String(10), default="ru")  # ru, en и т.д.
    
    variables = Column(JSON, default=list)  # Список переменных для шаблона
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Таблица уведомлений
class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    user_id = Column(Integer, nullable=False)  # Получатель (user_id из auth-service)
    
    type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    
    subject = Column(String(255))  # Тема (для email)
    message = Column(Text, nullable=False)  # Текст сообщения
    
    notification_metadata = Column('metadata', JSON, default=dict)  # Дополнительные данные
    context = Column(JSON, default=dict)  # Контекст для шаблона
    
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    
    error_message = Column(Text)  # Сообщение об ошибке если отправка не удалась
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи
    template = relationship("NotificationTemplate")

# Таблица истории событий (какие события обработаны)
class EventHistory(Base):
    __tablename__ = "event_history"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, nullable=False)  # ID события из RabbitMQ
    event_type = Column(String(100), nullable=False)  # Тип события (user.registered и т.д.)
    source_service = Column(String(50), nullable=False)  # Сервис-источник
    
    payload = Column(JSON, nullable=False)  # Данные события
    processed = Column(Boolean, default=False)  # Обработано ли
    
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица настроек уведомлений пользователей
class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    
    # Каналы
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    
    # Типы уведомлений
    receive_promotional = Column(Boolean, default=True)
    receive_system = Column(Boolean, default=True)
    receive_order_updates = Column(Boolean, default=True)
    
    email_frequency = Column(String(20), default="immediate")  # immediate, daily, weekly
    last_email_sent = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())