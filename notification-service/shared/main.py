from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uvicorn
import os
import asyncio
import json

# Импорты из того же каталога
import crud
import models
from database import get_db, init_db
from datetime import datetime

# Локальные заглушки вместо общего shared модуля
class AuthUtils:
    @staticmethod
    def verify_token(token: str):
        # Заглушка для тестирования
        if token and token.startswith("Bearer "):
            return {"user_id": 1, "email": "user@test.com", "role": "client"}
        return None

class UserRole:
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"

app = FastAPI(
    title="Notification Service",
    description="Email and notification service for auto dealership",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация компонентов
email_sender = crud.EmailSender()
template_renderer = crud.TemplateRenderer()
event_processor = crud.EventProcessor()

# Dependency to get current user from token
async def get_current_user(token: str = Depends(AuthUtils.verify_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token

async def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "notification"}

@app.get("/")
async def root():
    return {
        "service": "Notification Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "notifications": "/notifications",
            "templates": "/templates",
            "send": "/send",
            "events": "/events"
        }
    }

# ==================== NOTIFICATION ENDPOINTS ====================
@app.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    notifications = crud.NotificationCRUD.get_user_notifications(
        db, current_user.get("user_id"), limit, unread_only
    )
    
    return [
        {
            "id": n.id,
            "type": n.type.value,
            "channel": n.channel.value,
            "subject": n.subject,
            "message": n.message,
            "status": n.status.value,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "metadata": n.metadata
        }
        for n in notifications
    ]

@app.get("/notifications/{notification_id}")
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific notification"""
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.get("user_id")
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Mark as read when fetched
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        notification.status = models.NotificationStatus.READ
        db.commit()
    
    return {
        "id": notification.id,
        "type": notification.type.value,
        "channel": notification.channel.value,
        "subject": notification.subject,
        "message": notification.message,
        "status": notification.status.value,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
        "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "metadata": notification.metadata,
        "context": notification.context
    }

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark notification as read"""
    notification = crud.NotificationCRUD.mark_as_read(db, notification_id, current_user.get("user_id"))
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read", "notification_id": notification.id}

# ==================== TEMPLATE ENDPOINTS ====================
@app.post("/templates", response_model=Dict[str, Any])
async def create_template(
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create notification template (admin only)"""
    template = crud.TemplateCRUD.create_template(db, template_data, current_user.get("user_id"))
    
    return {
        "message": "Template created successfully",
        "template_id": template.id,
        "name": template.name
    }

@app.get("/templates", response_model=List[Dict[str, Any]])
async def get_templates(
    channel: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get notification templates"""
    query = db.query(models.NotificationTemplate)
    
    if active_only:
        query = query.filter(models.NotificationTemplate.is_active == True)
    
    if channel:
        query = query.filter(models.NotificationTemplate.channel == channel)
    
    templates = query.all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "channel": t.channel.value,
            "type": t.type.value,
            "subject_template": t.subject_template,
            "variables": t.variables,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in templates
    ]

@app.get("/templates/{template_id}")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get template by ID"""
    template = crud.TemplateCRUD.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "channel": template.channel.value,
        "type": template.type.value,
        "subject_template": template.subject_template,
        "body_template": template.body_template,
        "variables": template.variables,
        "language": template.language,
        "is_active": template.is_active,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None
    }

# ==================== SEND ENDPOINTS ====================
@app.post("/send/email", response_model=Dict[str, Any])
async def send_email(
    recipient_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    user_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
    # Убрали current_user: dict = Depends(get_current_user)
):
    """Send email immediately (без аутентификации для тестов)"""
    # Создаём фиктивного пользователя для тестов
    fake_user_id = 1
    
    # Create notification record
    notification_data = {
        "user_id": user_id or fake_user_id,  # Используем fake_user_id если не передан
        "type": models.NotificationType.EMAIL,
        "channel": models.NotificationChannel.SYSTEM_ALERT,
        "recipient_email": recipient_email,
        "subject": subject,
        "message": body,
        "status": models.NotificationStatus.PENDING
    }
    
    notification = crud.NotificationCRUD.create_notification(db, notification_data)
    
    # Send email in background
    async def send_email_task():
        success = await email_sender.send_email(recipient_email, subject, body, html_body)
        
        if success:
            crud.NotificationCRUD.update_status(
                db, notification.id, models.NotificationStatus.SENT
            )
        else:
            crud.NotificationCRUD.update_status(
                db, notification.id, models.NotificationStatus.FAILED,
                error_message="Failed to send email"
            )
    
    if background_tasks:
        background_tasks.add_task(send_email_task)
    else:
        asyncio.create_task(send_email_task())
    
    return {
        "message": "Email queued for sending",
        "notification_id": notification.id,
        "recipient": recipient_email
    }

@app.post("/send/template", response_model=Dict[str, Any])
async def send_template(
    template_name: str,
    recipient_email: str,
    context: Dict[str, Any],
    user_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send email using template"""
    # Get template
    template = crud.TemplateCRUD.get_template_by_name(db, template_name)
    if not template or not template.is_active:
        raise HTTPException(status_code=404, detail="Template not found or inactive")
    
    # Render template
    subject = template_renderer.render_template(template.subject_template or "", context)
    body = template_renderer.render_template(template.body_template, context)
    
    # Create notification
    notification_data = {
        "template_id": template.id,
        "user_id": user_id or current_user.get("user_id"),
        "type": template.type,
        "channel": template.channel,
        "recipient_email": recipient_email,
        "subject": subject,
        "message": body,
        "context": context,
        "status": models.NotificationStatus.PENDING
    }
    
    notification = crud.NotificationCRUD.create_notification(db, notification_data)
    
    # Send in background
    async def send_template_task():
        success = await email_sender.send_email(recipient_email, subject, body)
        
        if success:
            crud.NotificationCRUD.update_status(
                db, notification.id, models.NotificationStatus.SENT
            )
        else:
            crud.NotificationCRUD.update_status(
                db, notification.id, models.NotificationStatus.FAILED,
                error_message="Failed to send template email"
            )
    
    if background_tasks:
        background_tasks.add_task(send_template_task)
    else:
        asyncio.create_task(send_template_task())
    
    return {
        "message": "Template email queued for sending",
        "notification_id": notification.id,
        "template": template.name,
        "recipient": recipient_email
    }

# ==================== EVENT ENDPOINTS ====================
@app.post("/events/process", response_model=Dict[str, Any])
async def process_event(
    event_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Process event manually (admin only)"""
    notification = event_processor.process_event(db, event_data)
    
    if notification:
        return {
            "message": "Event processed successfully",
            "event_id": event_data.get("event_id"),
            "notification_id": notification.id
        }
    else:
        return {
            "message": "Event already processed or invalid",
            "event_id": event_data.get("event_id")
        }

@app.get("/events", response_model=List[Dict[str, Any]])
async def get_events(
    processed: Optional[bool] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get event history (admin only)"""
    query = db.query(models.EventHistory)
    
    if processed is not None:
        query = query.filter(models.EventHistory.processed == processed)
    
    events = query.order_by(models.EventHistory.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "event_type": e.event_type,
            "source_service": e.source_service,
            "processed": e.processed,
            "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]

# ==================== STATISTICS ====================
@app.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get notification statistics (admin only)"""
    from sqlalchemy import func
    
    # Total notifications by type
    by_type = db.query(
        models.Notification.type,
        func.count(models.Notification.id).label('count')
    ).group_by(models.Notification.type).all()
    
    # Total notifications by status
    by_status = db.query(
        models.Notification.status,
        func.count(models.Notification.id).label('count')
    ).group_by(models.Notification.status).all()
    
    # Today's notifications
    today = datetime.utcnow().date()
    today_count = db.query(models.Notification).filter(
        func.date(models.Notification.created_at) == today
    ).count()
    
    # Failed notifications
    failed_count = db.query(models.Notification).filter(
        models.Notification.status == models.NotificationStatus.FAILED
    ).count()
    
    return {
        "total_by_type": {t[0].value: t[1] for t in by_type},
        "total_by_status": {s[0].value: s[1] for s in by_status},
        "today_count": today_count,
        "failed_count": failed_count,
        "total_templates": db.query(models.NotificationTemplate).count(),
        "total_events": db.query(models.EventHistory).count()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Notification Service starting up...")
    
    # Инициализируем БД
    init_db()
    print("Database initialized")
    
    # Create default templates if they don't exist
    from datetime import datetime
    db = next(get_db())
    try:
        # Welcome email template
        if not crud.TemplateCRUD.get_template_by_name(db, "welcome_email"):
            welcome_template = models.NotificationTemplate(
                name="welcome_email",
                description="Welcome email for new users",
                channel=models.NotificationChannel.USER_REGISTRATION,
                type=models.NotificationType.EMAIL,
                subject_template="Добро пожаловать в AutoSalon, {{ user_name }}!",
                body_template="""Уважаемый(ая) {{ user_name }},

Добро пожаловать в AutoSalon! Ваш аккаунт был успешно создан {{ registration_date }}.

С уважением,
Команда AutoSalon""",
                variables=["user_name", "email", "registration_date"],
                language="ru"
            )
            db.add(welcome_template)
        
        # Appointment confirmation template
        if not crud.TemplateCRUD.get_template_by_name(db, "appointment_confirmation"):
            appointment_template = models.NotificationTemplate(
                name="appointment_confirmation",
                description="Appointment confirmation email",
                channel=models.NotificationChannel.APPOINTMENT_BOOKING,
                type=models.NotificationType.EMAIL,
                subject_template="Подтверждение записи #{{ appointment_id }}",
                body_template="""Ваша запись на сервис подтверждена.

Детали записи:
- ID записи: {{ appointment_id }}
- Дата и время: {{ appointment_date }}
- Филиал: {{ branch_name }}
- Тип услуги: {{ service_type }}

Пожалуйста, приходите за 10 минут до назначенного времени.

С уважением,
AutoSalon""",
                variables=["appointment_id", "appointment_date", "branch_name", "service_type"],
                language="ru"
            )
            db.add(appointment_template)
        
        db.commit()
        print("Default templates created")
        
    except Exception as e:
        print(f"Error creating default templates: {e}")
        db.rollback()
    finally:
        db.close()
    
    # Subscribe to all events
    from crud import message_broker
    
    def handle_event(event):
        print(f"Processing event: {event['event_type']}")
        db = next(get_db())
        try:
            crud.EventProcessor.process_event(db, event)
        except Exception as e:
            print(f"Error processing event: {e}")
        finally:
            db.close()
    
    message_broker.subscribe_to_events(
        exchange="*",  # Listen to all exchanges
        routing_keys=["*.*"],  # All events
        callback=handle_event
    )
    
    print("Service ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)