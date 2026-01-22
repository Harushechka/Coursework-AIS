from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jinja2
import asyncio
import os

from models import (
    Notification, NotificationTemplate, EventHistory, UserNotificationSettings,
    NotificationType, NotificationStatus, NotificationChannel
)

# Заглушки вместо общего shared модуля
class MessageBroker:
    def publish_event(self, exchange, routing_key, event_data):
        print(f"[STUB] Event: {exchange}.{routing_key} - {event_data}")
    
    def subscribe_to_events(self, exchange, routing_keys, callback):
        print(f"[STUB] Subscribed to {exchange}: {routing_keys}")

message_broker = MessageBroker()

# ==================== TEMPLATE OPERATIONS ====================
class TemplateCRUD:
    @staticmethod
    def create_template(db: Session, template_data: dict, user_id: int):
        """Create notification template"""
        template = NotificationTemplate(**template_data)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    
    @staticmethod
    def get_template(db: Session, template_id: int):
        """Get template by ID"""
        return db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    
    @staticmethod
    def get_template_by_name(db: Session, name: str):
        """Get template by name"""
        return db.query(NotificationTemplate).filter(NotificationTemplate.name == name).first()
    
    @staticmethod
    def get_templates_by_channel(db: Session, channel: str):
        """Get templates by channel"""
        return db.query(NotificationTemplate).filter(
            NotificationTemplate.channel == channel,
            NotificationTemplate.is_active == True
        ).all()

# ==================== NOTIFICATION OPERATIONS ====================
class NotificationCRUD:
    @staticmethod
    def create_notification(db: Session, notification_data: dict):
        """Create notification record"""
        notification = Notification(**notification_data)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, limit: int = 50, 
                              unread_only: bool = False):
        """Get notifications for user"""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read_at == None)
        
        return query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int):
        """Mark notification as read"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification and not notification.read_at:
            notification.read_at = datetime.utcnow()
            notification.status = NotificationStatus.READ
            db.commit()
        
        return notification
    
    @staticmethod
    def update_status(db: Session, notification_id: int, status: NotificationStatus,
                     error_message: str = None, delivery_attempts: int = None):
        """Update notification status"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return None
        
        notification.status = status
        
        if status == NotificationStatus.SENT:
            notification.sent_at = datetime.utcnow()
        elif status == NotificationStatus.FAILED and error_message:
            notification.error_message = error_message
        
        if delivery_attempts is not None:
            notification.delivery_attempts = delivery_attempts
        
        db.commit()
        return notification

# ==================== EVENT PROCESSING ====================
class EventProcessor:
    @staticmethod
    def process_event(db: Session, event_data: dict):
        """Process incoming event from RabbitMQ"""
        event_id = event_data.get("event_id")
        event_type = event_data.get("event_type")
        payload = event_data.get("payload", {})
        
        # Check if event already processed
        existing = db.query(EventHistory).filter(EventHistory.event_id == event_id).first()
        if existing:
            return None
        
        # Save event to history
        event_history = EventHistory(
            event_id=event_id,
            event_type=event_type,
            source_service=event_type.split(".")[0] if "." in event_type else "unknown",
            payload=payload
        )
        db.add(event_history)
        
        # Process based on event type
        notification = None
        
        if event_type == "user.registered":
            notification = EventProcessor._handle_user_registered(db, payload)
        elif event_type == "appointment.created":
            notification = EventProcessor._handle_appointment_created(db, payload)
        elif event_type == "payment.completed":
            notification = EventProcessor._handle_payment_completed(db, payload)
        elif event_type.startswith("booking."):
            notification = EventProcessor._handle_booking_event(db, event_type, payload)
        
        if notification:
            event_history.processed = True
            event_history.processed_at = datetime.utcnow()
        
        db.commit()
        return notification
    
    @staticmethod
    def _handle_user_registered(db: Session, payload: dict):
        """Handle user registration event"""
        user_id = payload.get("user_id")
        email = payload.get("email")
        name = payload.get("name", "Пользователь")
        
        if not user_id or not email:
            return None
        
        # Get welcome template
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.name == "welcome_email",
            NotificationTemplate.is_active == True
        ).first()
        
        if template:
            # Render template
            context = {
                "user_name": name,
                "email": email,
                "registration_date": datetime.utcnow().strftime("%d.%m.%Y")
            }
            
            # Create notification
            notification = Notification(
                template_id=template.id,
                user_id=user_id,
                type=NotificationType.EMAIL,
                channel=NotificationChannel.USER_REGISTRATION,
                recipient_email=email,
                subject="Добро пожаловать в AutoSalon!",
                message=f"Уважаемый(ая) {name}, добро пожаловать в AutoSalon!",
                context=context
            )
            db.add(notification)
            return notification
        
        return None
    
    @staticmethod
    def _handle_appointment_created(db: Session, payload: dict):
        """Handle appointment creation event"""
        customer_id = payload.get("customer_id")
        appointment_id = payload.get("appointment_id")
        scheduled_start = payload.get("scheduled_start")
        
        if not customer_id:
            return None
        
        # Create simple notification
        notification = Notification(
            user_id=customer_id,
            type=NotificationType.EMAIL,
            channel=NotificationChannel.APPOINTMENT_BOOKING,
            subject="Запись на сервис подтверждена",
            message=f"Ваша запись #{appointment_id} подтверждена на {scheduled_start}",
            notification_metadata={"appointment_id": appointment_id}
        )
        db.add(notification)
        return notification
    
    @staticmethod
    def _handle_payment_completed(db: Session, payload: dict):
        """Handle payment completion event"""
        user_id = payload.get("user_id")
        amount = payload.get("amount")
        payment_id = payload.get("payment_id")
        
        if not user_id:
            return None
        
        notification = Notification(
            user_id=user_id,
            type=NotificationType.EMAIL,
            channel=NotificationChannel.PAYMENT_CONFIRMATION,
            subject="Платеж подтвержден",
            message=f"Ваш платеж #{payment_id} на сумму {amount} успешно завершен",
            notification_metadata={"payment_id": payment_id, "amount": amount}
        )
        db.add(notification)
        return notification
    
    @staticmethod
    def _handle_booking_event(db: Session, event_type: str, payload: dict):
        """Handle booking events"""
        # Generic handler for booking events
        user_id = payload.get("customer_id") or payload.get("user_id")
        
        if not user_id:
            return None
        
        event_titles = {
            "booking.created": "Новая запись на сервис",
            "booking.updated": "Запись обновлена",
            "booking.cancelled": "Запись отменена"
        }
        
        title = event_titles.get(event_type, "Уведомление от сервиса")
        
        notification = Notification(
            user_id=user_id,
            type=NotificationType.EMAIL,
            channel=NotificationChannel.APPOINTMENT_BOOKING,
            subject=title,
            message=f"Событие: {event_type}. Детали: {json.dumps(payload, ensure_ascii=False)}",
            notification_metadata={"event_type": event_type, "payload": payload}
        )
        db.add(notification)
        return notification

# ==================== EMAIL SENDER ====================
class EmailSender:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "mailhog")
        self.smtp_port = int(os.getenv("SMTP_PORT", 1025))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "noreply@autosalon.com")
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        html_body: str = None) -> bool:
        """Send email asynchronously"""
        try:
            message = MIMEMultipart('alternative')
            message['From'] = self.email_from
            message['To'] = to_email
            message['Subject'] = subject
            
            # Add plain text version
            message.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Add HTML version if provided
            if html_body:
                message.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=False  # Mailhog doesn't use TLS
            ) as smtp:
                await smtp.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False

# ==================== TEMPLATE RENDERER ====================
class TemplateRenderer:
    def __init__(self):
        self.jinja_env = jinja2.Environment(
            loader=jinja2.DictLoader({}),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
    
    def render_template(self, template_text: str, context: dict) -> str:
        """Render template with context"""
        try:
            template = self.jinja_env.from_string(template_text)
            return template.render(**context)
        except Exception as e:
            print(f"Error rendering template: {e}")
            return template_text  # Return original if rendering fails