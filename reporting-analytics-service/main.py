from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uvicorn
import os
import json
import asyncio

# Импорты из того же каталога
import crud
import models
from database import get_db, init_db

# Локальные заглушки вместо общего shared модуля
class AuthUtils:
    @staticmethod
    def verify_token(token: str):
        # Заглушка для тестирования
        if token and token.startswith("Bearer "):
            return {"user_id": 1, "email": "manager@test.com", "role": "manager"}
        return None

class UserRole:
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"

app = FastAPI(
    title="Reporting & Analytics Service",
    description="Analytics and reporting service for auto dealership",
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

# Dependency to get current user from token
async def get_current_user(token: Optional[str] = Query(None, alias="token")):
    """Get current user from token parameter or Authorization header"""
    # Если токен не передан в query, пробуем получить из заголовка
    if not token:
        # Заглушка для тестирования - разрешаем доступ без токена
        print("Warning: No token provided, using test user")
        return {"user_id": 1, "email": "test@example.com", "role": "manager"}
    
    # Проверяем токен через AuthUtils
    user_data = AuthUtils.verify_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user_data

async def require_manager(user: dict = Depends(get_current_user)):
    if user.get("role") not in [UserRole.MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return user

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reporting-analytics"}

@app.get("/")
async def root():
    return {
        "service": "Reporting & Analytics Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "reports": "/reports",
            "dashboards": "/dashboards",
            "analytics": "/analytics",
            "stats": "/stats"
        }
    }

# ==================== REPORT ENDPOINTS ====================
@app.post("/reports", response_model=Dict[str, Any])
async def create_report(
    report_type: models.ReportType,
    name: str,
    period_start: date,
    period_end: date,
    parameters: Optional[Dict[str, Any]] = None,
    filters: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_manager)
):
    """Create new report request"""
    report_data = {
        "report_type": report_type,
        "name": name,
        "period_start": period_start,
        "period_end": period_end,
        "parameters": parameters or {},
        "filters": filters or {},
        "generated_by": current_user.get("user_id"),
        "status": models.ReportStatus.PENDING
    }
    
    report = crud.ReportCRUD.create_report(db, report_data, current_user.get("user_id"))
    
    # Generate report in background
    async def generate_report_task():
        try:
            start_time = datetime.utcnow()
            
            # Generate report based on type
            if report_type == models.ReportType.DAILY_SALES:
                report_data = crud.ReportGenerator.generate_daily_sales_report(period_start, period_end, filters)
            elif report_type == models.ReportType.POPULAR_MODELS:
                report_data = crud.ReportGenerator.generate_popular_models_report(period_start, period_end)
            elif report_type == models.ReportType.SERVICE_EFFECTIVENESS:
                report_data = crud.ReportGenerator.generate_service_effectiveness_report(period_start, period_end)
            else:
                report_data = {"message": "Report type not implemented yet"}
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Update report status
            crud.ReportCRUD.update_report_status(
                db, report.id, models.ReportStatus.COMPLETED,
                file_path=f"/reports/{report.id}.json",
                execution_time=execution_time
            )
            
            # Cache the result
            cache_key = f"report_{report.id}"
            crud.CacheCRUD.set_cached_data(db, cache_key, report_data, ttl_minutes=60)
            
        except Exception as e:
            crud.ReportCRUD.update_report_status(
                db, report.id, models.ReportStatus.FAILED,
                error_message=str(e)
            )
    
    if background_tasks:
        background_tasks.add_task(generate_report_task)
    else:
        asyncio.create_task(generate_report_task())
    
    return {
        "message": "Report generation started",
        "report_id": report.id,
        "report_type": report_type.value,
        "status": report.status.value
    }

@app.get("/reports", response_model=List[Dict[str, Any]])
async def get_reports(
    report_type: Optional[models.ReportType] = None,
    status: Optional[models.ReportStatus] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get reports for current user"""
    reports = crud.ReportCRUD.get_user_reports(db, current_user.get("user_id"), report_type)
    
    if status:
        reports = [r for r in reports if r.status == status]
    
    reports = reports[:limit]
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "report_type": r.report_type.value,
            "period_start": r.period_start.isoformat() if r.period_start else None,
            "period_end": r.period_end.isoformat() if r.period_end else None,
            "status": r.status.value,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "execution_time_ms": r.execution_time_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in reports
    ]

@app.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get report by ID with data"""
    report = crud.ReportCRUD.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check access
    if report.generated_by != current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Try to get cached data
    cache_key = f"report_{report_id}"
    cached = crud.CacheCRUD.get_cached_data(db, cache_key)
    
    report_data = {
        "id": report.id,
        "name": report.name,
        "description": report.description,
        "report_type": report.report_type.value,
        "period_start": report.period_start.isoformat() if report.period_start else None,
        "period_end": report.period_end.isoformat() if report.period_end else None,
        "status": report.status.value,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "execution_time_ms": report.execution_time_ms,
        "parameters": report.parameters,
        "filters": report.filters,
        "created_at": report.created_at.isoformat() if report.created_at else None
    }
    
    if cached:
        report_data["data"] = cached.data
        report_data["cached"] = True
        report_data["cache_expires"] = cached.expires_at.isoformat()
    elif report.status == models.ReportStatus.COMPLETED:
        # Regenerate if not cached
        report_data["data"] = {"message": "Report data not cached, regenerate please"}
        report_data["cached"] = False
    
    return report_data

# ==================== DASHBOARD ENDPOINTS ====================
@app.post("/dashboards", response_model=Dict[str, Any])
async def create_dashboard(
    name: str,
    description: Optional[str] = None,
    is_public: bool = False,
    layout_config: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_manager)
):
    """Create new dashboard"""
    dashboard_data = {
        "name": name,
        "description": description,
        "is_public": is_public,
        "layout_config": layout_config or {}
    }
    
    dashboard = crud.DashboardCRUD.create_dashboard(db, dashboard_data, current_user.get("user_id"))
    
    return {
        "message": "Dashboard created successfully",
        "dashboard_id": dashboard.id,
        "name": dashboard.name
    }

@app.get("/dashboards", response_model=List[Dict[str, Any]])
async def get_dashboards(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboards accessible to current user"""
    # Get public dashboards and user's own dashboards
    dashboards = db.query(models.Dashboard).filter(
        (models.Dashboard.is_public == True) | 
        (models.Dashboard.created_by == current_user.get("user_id"))
    ).all()
    
    return [
        {
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "is_public": d.is_public,
            "created_by": d.created_by,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "widget_count": db.query(models.DashboardWidget).filter(
                models.DashboardWidget.dashboard_id == d.id
            ).count()
        }
        for d in dashboards
    ]

# ==================== ANALYTICS ENDPOINTS ====================
@app.post("/analytics/event")
async def track_event(
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    properties: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Track analytics event"""
    event_data = {
        "event_type": event_type,
        "user_id": current_user.get("user_id"),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "properties": properties or {},
        "context": {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "reporting-analytics"
        }
    }
    
    event = crud.AnalyticsCRUD.track_event(db, event_data)
    
    return {
        "message": "Event tracked successfully",
        "event_id": event.id,
        "event_type": event.event_type
    }

@app.get("/analytics/events/{event_type}")
async def get_events(
    event_type: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_manager)
):
    """Get analytics events by type (managers only)"""
    events = crud.AnalyticsCRUD.get_events_by_type(db, event_type, limit)
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "user_id": e.user_id,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "properties": e.properties,
            "created_at": e.created_at.isoformat() if e.created_at else None
        }
        for e in events
    ]

# ==================== STATISTICS ENDPOINTS ====================
@app.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_manager)
):
    """Get service statistics (managers only)"""
    from sqlalchemy import func
    
    # Report statistics
    total_reports = db.query(models.Report).count()
    completed_reports = db.query(models.Report).filter(
        models.Report.status == models.ReportStatus.COMPLETED
    ).count()
    failed_reports = db.query(models.Report).filter(
        models.Report.status == models.ReportStatus.FAILED
    ).count()
    
    # Dashboard statistics
    total_dashboards = db.query(models.Dashboard).count()
    public_dashboards = db.query(models.Dashboard).filter(
        models.Dashboard.is_public == True
    ).count()
    
    # Cache statistics
    cache_hits = db.query(func.sum(models.CachedData.hits)).scalar() or 0
    active_cache = db.query(models.CachedData).filter(
        models.CachedData.expires_at > datetime.utcnow()
    ).count()
    
    # Analytics statistics
    total_events = db.query(models.AnalyticsEvent).count()
    
    return {
        "reports": {
            "total": total_reports,
            "completed": completed_reports,
            "failed": failed_reports,
            "pending": total_reports - completed_reports - failed_reports
        },
        "dashboards": {
            "total": total_dashboards,
            "public": public_dashboards,
            "private": total_dashboards - public_dashboards
        },
        "cache": {
            "hits": cache_hits,
            "active_entries": active_cache
        },
        "analytics": {
            "total_events": total_events,
            "events_today": db.query(models.AnalyticsEvent).filter(
                func.date(models.AnalyticsEvent.created_at) == datetime.utcnow().date()
            ).count()
        }
    }

# ==================== QUICK REPORTS ====================
@app.get("/reports/quick/daily-sales")
async def quick_daily_sales(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Quick daily sales report (last N days)"""
    period_end = date.today()
    period_start = period_end - timedelta(days=days)
    
    # Check cache first
    cache_key = f"quick_daily_sales_{days}_{period_start}_{period_end}"
    cached = crud.CacheCRUD.get_cached_data(db, cache_key)
    
    if cached:
        return {
            "cached": True,
            "data": cached.data
        }
    
    # Generate fresh data
    report_data = crud.ReportGenerator.generate_daily_sales_report(period_start, period_end)
    
    # Cache for 5 minutes
    crud.CacheCRUD.set_cached_data(db, cache_key, report_data, ttl_minutes=5)
    
    return {
        "cached": False,
        "data": report_data
    }

@app.get("/reports/quick/popular-models")
async def quick_popular_models(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Quick popular models report (last N days)"""
    period_end = date.today()
    period_start = period_end - timedelta(days=days)
    
    cache_key = f"quick_popular_models_{days}_{period_start}_{period_end}"
    cached = crud.CacheCRUD.get_cached_data(db, cache_key)
    
    if cached:
        return {"cached": True, "data": cached.data}
    
    report_data = crud.ReportGenerator.generate_popular_models_report(period_start, period_end)
    crud.CacheCRUD.set_cached_data(db, cache_key, report_data, ttl_minutes=10)
    
    return {"cached": False, "data": report_data}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Reporting & Analytics Service starting up...")
    
    # Инициализируем БД
    init_db()
    print("Database initialized")
    
    # Subscribe to events for analytics
    from crud import message_broker
    
    def handle_event(event):
        print(f"Analytics event received: {event['event_type']}")
        db = next(get_db())
        try:
            # Track event in analytics
            event_data = {
                "event_type": event["event_type"],
                "properties": event.get("payload", {}),
                "context": {
                    "source": "rabbitmq",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            crud.AnalyticsCRUD.track_event(db, event_data)
        except Exception as e:
            print(f"Error tracking event: {e}")
        finally:
            db.close()
    
    message_broker.subscribe_to_events(
        exchange="*",
        routing_keys=["*.*"],
        callback=handle_event
    )
    
    print("Service ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)