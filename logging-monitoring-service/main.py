from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uvicorn
import os
import json
from logging_handler import log_handler
from metrics_collector import metrics_collector
import config
from database import get_db, init_db
import models
import crud

app = FastAPI(
    title="Logging & Monitoring Service",
    description="Centralized logging and monitoring for microservices",
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

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "logging-monitoring"}

@app.get("/")
async def root():
    return {
        "service": "Logging & Monitoring Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "logs": "/logs",
            "metrics": "/metrics",
            "audit": "/audit",
            "errors": "/errors",
            "stats": "/stats"
        }
    }

# ==================== LOG ENDPOINTS ====================
@app.post("/logs")
async def create_log(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create log entry (for services to send logs)"""
    try:
        log_data = await request.json()
        
        # Add timestamp if not provided
        if 'timestamp' not in log_data:
            log_data['timestamp'] = datetime.utcnow()
        
        log = crud.LogCRUD.create_log(db, log_data)
        
        return {
            "message": "Log created successfully",
            "log_id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid log data: {str(e)}"
        )

@app.get("/logs")
async def get_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    level: Optional[models.LogLevel] = None,
    service: Optional[str] = None,
    source: Optional[models.LogSource] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get logs with filters"""
    # Parse dates
    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')) if start_date else None
    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else None
    
    logs = crud.LogCRUD.get_logs(
        db, start_dt, end_dt, level, service, source, user_id, limit
    )
    
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "level": log.level.value,
            "source": log.source.value,
            "service": log.service,
            "message": log.message,
            "correlation_id": log.correlation_id,
            "user_id": log.user_id,
            "endpoint": log.endpoint,
            "status_code": log.status_code,
            "response_time_ms": log.response_time_ms,
            "ip_address": log.ip_address,
            "additional_data": log.additional_data
        }
        for log in logs
    ]

# ==================== METRICS ENDPOINTS ====================
@app.post("/metrics")
async def add_metric(
    request: Request,
    db: Session = Depends(get_db)
):
    """Add system metric"""
    try:
        metric_data = await request.json()
        
        # Add timestamp if not provided
        if 'timestamp' not in metric_data:
            metric_data['timestamp'] = datetime.utcnow()
        
        metric = crud.MetricsCRUD.add_metric(db, metric_data)
        
        return {
            "message": "Metric added successfully",
            "metric_id": metric.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metric data: {str(e)}"
        )

@app.get("/metrics/{service}/{metric_name}")
async def get_metrics(
    service: str,
    metric_name: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get metrics for service"""
    metrics = crud.MetricsCRUD.get_service_metrics(db, service, metric_name, hours)
    
    return [
        {
            "id": m.id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "metric_name": m.metric_name,
            "metric_value": m.metric_value,
            "service": m.service,
            "instance_id": m.instance_id,
            "tags": m.tags
        }
        for m in metrics
    ]

# ==================== AUDIT ENDPOINTS ====================
@app.post("/audit")
async def create_audit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Create audit trail record"""
    try:
        audit_data = await request.json()
        
        # Add timestamp if not provided
        if 'timestamp' not in audit_data:
            audit_data['timestamp'] = datetime.utcnow()
        
        audit = crud.AuditCRUD.create_audit(db, audit_data)
        
        return {
            "message": "Audit record created",
            "audit_id": audit.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audit data: {str(e)}"
        )

# ==================== STATISTICS ====================
@app.get("/stats")
async def get_stats(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get service statistics"""
    from sqlalchemy import func
    
    # Log statistics
    total_logs = db.query(models.ApplicationLog).count()
    error_logs = db.query(models.ApplicationLog).filter(
        models.ApplicationLog.level.in_(['ERROR', 'CRITICAL'])
    ).count()
    
    # Metrics statistics
    total_metrics = db.query(models.SystemMetric).count()
    
    # Recent errors by service
    recent_errors = crud.LogCRUD.get_error_summary(db, days)
    
    # Logs by level (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(hours=24)
    logs_by_level = db.query(
        models.ApplicationLog.level,
        func.count(models.ApplicationLog.id).label('count')
    ).filter(
        models.ApplicationLog.timestamp >= day_ago
    ).group_by(
        models.ApplicationLog.level
    ).all()
    
    return {
        "logs": {
            "total": total_logs,
            "errors": error_logs,
            "by_level": {level: count for level, count in logs_by_level}
        },
        "metrics": {
            "total": total_metrics
        },
        "recent_errors": [
            {
                "service": service,
                "level": level,
                "count": count
            }
            for service, level, count in recent_errors
        ]
    }

# ==================== ERROR REPORTS ====================
@app.get("/errors")
async def get_errors(
    resolved: Optional[bool] = None,
    days: int = 7,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get error reports"""
    from sqlalchemy import desc
    
    query = db.query(models.ErrorReport)
    
    if resolved is not None:
        query = query.filter(models.ErrorReport.is_resolved == resolved)
    
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(models.ErrorReport.timestamp >= start_date)
    
    errors = query.order_by(desc(models.ErrorReport.timestamp)).limit(limit).all()
    
    return [
        {
            "id": e.id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "error_code": e.error_code,
            "error_type": e.error_type,
            "service": e.service,
            "endpoint": e.endpoint,
            "message": e.message,
            "is_resolved": e.is_resolved,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None
        }
        for e in errors
    ]

# ==================== QUICK REPORTS ====================
@app.get("/reports/services-health")
async def services_health(
    hours: int = 1,
    db: Session = Depends(get_db)
):
    """Get services health report"""
    from sqlalchemy import func
    
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    # Get last heartbeat from each service
    # Assuming services send regular heartbeat metrics
    heartbeats = db.query(
        models.SystemMetric.service,
        func.max(models.SystemMetric.timestamp).label('last_heartbeat')
    ).filter(
        models.SystemMetric.metric_name == 'heartbeat'
    ).group_by(
        models.SystemMetric.service
    ).all()
    
    services = []
    for service, last_heartbeat in heartbeats:
        if last_heartbeat:
            minutes_ago = (datetime.utcnow() - last_heartbeat).total_seconds() / 60
            status = "healthy" if minutes_ago < 5 else "unhealthy"
        else:
            status = "unknown"
            minutes_ago = None
        
        services.append({
            "service": service,
            "status": status,
            "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None,
            "minutes_since_heartbeat": minutes_ago
        })
    
    return {
        "report_time": datetime.utcnow().isoformat(),
        "services": services
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Logging & Monitoring Service starting up...")
    
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Start metrics collection in background
    import asyncio
    asyncio.create_task(metrics_collector.start_periodic_collection(
        interval_seconds=config.settings.METRICS_INTERVAL_SECONDS
    ))
    
    print("Service ready")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)