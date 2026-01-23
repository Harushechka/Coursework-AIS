from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import models

class LogCRUD:
    @staticmethod
    def create_log(db: Session, log_data: dict):
        """Create new application log"""
        log = models.ApplicationLog(**log_data)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
    
    @staticmethod
    def get_logs(db: Session, 
                start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None,
                level: Optional[str] = None,
                service: Optional[str] = None,
                source: Optional[str] = None,
                user_id: Optional[int] = None,
                limit: int = 1000):
        """Get logs with filters"""
        query = db.query(models.ApplicationLog)
        
        if start_date:
            query = query.filter(models.ApplicationLog.timestamp >= start_date)
        if end_date:
            query = query.filter(models.ApplicationLog.timestamp <= end_date)
        if level:
            query = query.filter(models.ApplicationLog.level == level)
        if service:
            query = query.filter(models.ApplicationLog.service == service)
        if source:
            query = query.filter(models.ApplicationLog.source == source)
        if user_id:
            query = query.filter(models.ApplicationLog.user_id == user_id)
        
        return query.order_by(desc(models.ApplicationLog.timestamp)).limit(limit).all()
    
    @staticmethod
    def get_error_summary(db: Session, days: int = 7):
        """Get error summary for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = db.query(
            models.ApplicationLog.service,
            models.ApplicationLog.level,
            func.count(models.ApplicationLog.id).label('count')
        ).filter(
            models.ApplicationLog.timestamp >= start_date,
            models.ApplicationLog.level.in_(['ERROR', 'CRITICAL'])
        ).group_by(
            models.ApplicationLog.service,
            models.ApplicationLog.level
        ).order_by(
            desc('count')
        ).all()
        
        return result

class MetricsCRUD:
    @staticmethod
    def add_metric(db: Session, metric_data: dict):
        """Add system metric"""
        metric = models.SystemMetric(**metric_data)
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric
    
    @staticmethod
    def get_service_metrics(db: Session, service: str, metric_name: str, 
                           hours: int = 24, interval_minutes: int = 5):
        """Get metrics for service with aggregation"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Здесь будет сложный SQL запрос для агрегации
        # Для простоты вернем все метрики
        metrics = db.query(models.SystemMetric).filter(
            models.SystemMetric.service == service,
            models.SystemMetric.metric_name == metric_name,
            models.SystemMetric.timestamp >= start_time
        ).order_by(models.SystemMetric.timestamp).all()
        
        return metrics

class AuditCRUD:
    @staticmethod
    def create_audit(db: Session, audit_data: dict):
        """Create audit trail record"""
        audit = models.AuditTrail(**audit_data)
        db.add(audit)
        db.commit()
        db.refresh(audit)
        return audit
    
    @staticmethod
    def get_user_audit(db: Session, user_id: int, days: int = 30):
        """Get audit trail for user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(models.AuditTrail).filter(
            models.AuditTrail.user_id == user_id,
            models.AuditTrail.timestamp >= start_date
        ).order_by(desc(models.AuditTrail.timestamp)).all()