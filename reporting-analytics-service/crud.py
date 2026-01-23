from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json
import random

from models import (
    Report, Metric, Dashboard, DashboardWidget, CachedData, AnalyticsEvent,
    ReportType, ReportStatus, MetricType
)

# Заглушки вместо общего shared модуля
class MessageBroker:
    def publish_event(self, exchange, routing_key, event_data):
        print(f"[STUB] Event: {exchange}.{routing_key} - {event_data}")
    
    def subscribe_to_events(self, exchange, routing_keys, callback):
        print(f"[STUB] Subscribed to {exchange}: {routing_keys}")

message_broker = MessageBroker()

# ==================== REPORT OPERATIONS ====================
class ReportCRUD:
    @staticmethod
    def create_report(db: Session, report_data: dict, user_id: int):
        """Create new report request"""
        report = Report(**report_data)
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_report(db: Session, report_id: int):
        """Get report by ID"""
        return db.query(Report).filter(Report.id == report_id).first()
    
    @staticmethod
    def get_user_reports(db: Session, user_id: int, report_type: Optional[str] = None):
        """Get reports for user"""
        query = db.query(Report).filter(Report.generated_by == user_id)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        return query.order_by(Report.created_at.desc()).all()
    
    @staticmethod
    def update_report_status(db: Session, report_id: int, status: ReportStatus, 
                           file_path: str = None, execution_time: int = None, 
                           error_message: str = None):
        """Update report status"""
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return None
        
        report.status = status
        report.updated_at = datetime.utcnow()
        
        if status == ReportStatus.COMPLETED:
            report.generated_at = datetime.utcnow()
            if file_path:
                report.file_path = file_path
            if execution_time:
                report.execution_time_ms = execution_time
        elif status == ReportStatus.FAILED and error_message:
            report.error_message = error_message
        
        db.commit()
        return report

# ==================== REPORT GENERATORS ====================
class ReportGenerator:
    @staticmethod
    def generate_daily_sales_report(period_start: date, period_end: date, 
                                  filters: dict = None) -> Dict[str, Any]:
        """Generate daily sales report"""
        days = (period_end - period_start).days + 1
        report_data = {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "total_sales": random.randint(10000, 50000),
            "total_vehicles": random.randint(5, 20),
            "average_price": random.randint(2000, 5000),
            "daily_data": []
        }
        
        current_date = period_start
        for i in range(days):
            report_data["daily_data"].append({
                "date": current_date.isoformat(),
                "sales": random.randint(1000, 5000),
                "vehicles": random.randint(0, 3),
                "customers": random.randint(2, 8)
            })
            current_date += timedelta(days=1)
        
        return report_data
    
    @staticmethod
    def generate_popular_models_report(period_start: date, 
                                     period_end: date) -> Dict[str, Any]:
        """Generate popular models report"""
        models = [
            {"model": "Toyota Camry", "sales": 15, "revenue": 45000},
            {"model": "Honda Civic", "sales": 12, "revenue": 36000},
            {"model": "BMW X5", "sales": 8, "revenue": 64000},
            {"model": "Mercedes C-Class", "sales": 7, "revenue": 49000},
            {"model": "Ford Focus", "sales": 5, "revenue": 12500},
        ]
        
        return {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "total_models": len(models),
            "total_sales": sum(m["sales"] for m in models),
            "total_revenue": sum(m["revenue"] for m in models),
            "models": models
        }
    
    @staticmethod
    def generate_service_effectiveness_report(period_start: date, 
                                            period_end: date) -> Dict[str, Any]:
        """Generate service effectiveness report"""
        services = [
            {"service": "ТО", "appointments": 45, "avg_time": 120, "satisfaction": 4.5},
            {"service": "Ремонт ДВС", "appointments": 12, "avg_time": 240, "satisfaction": 4.2},
            {"service": "Шиномонтаж", "appointments": 28, "avg_time": 60, "satisfaction": 4.8},
            {"service": "Диагностика", "appointments": 33, "avg_time": 90, "satisfaction": 4.3},
        ]
        
        return {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "total_appointments": sum(s["appointments"] for s in services),
            "services": services,
            "metrics": {
                "avg_service_time": sum(s["avg_time"] * s["appointments"] for s in services) / sum(s["appointments"] for s in services),
                "avg_satisfaction": sum(s["satisfaction"] * s["appointments"] for s in services) / sum(s["appointments"] for s in services)
            }
        }

# ==================== DASHBOARD OPERATIONS ====================
class DashboardCRUD:
    @staticmethod
    def create_dashboard(db: Session, dashboard_data: dict, user_id: int):
        """Create new dashboard"""
        dashboard_data["created_by"] = user_id
        dashboard = Dashboard(**dashboard_data)
        db.add(dashboard)
        db.commit()
        db.refresh(dashboard)
        return dashboard
    
    @staticmethod
    def get_dashboard(db: Session, dashboard_id: int, user_id: int = None):
        """Get dashboard by ID with access check"""
        query = db.query(Dashboard).filter(Dashboard.id == dashboard_id)
        
        if user_id:
            query = query.filter(
                (Dashboard.created_by == user_id) | (Dashboard.is_public == True)
            )
        
        return query.first()

# ==================== CACHE OPERATIONS ====================
class CacheCRUD:
    @staticmethod
    def get_cached_data(db: Session, cache_key: str):
        """Get cached data if not expired"""
        cached = db.query(CachedData).filter(
            CachedData.cache_key == cache_key,
            CachedData.expires_at > datetime.utcnow()
        ).first()
        
        if cached:
            cached.hits += 1
            cached.last_accessed = datetime.utcnow()
            db.commit()
        
        return cached
    
    @staticmethod
    def set_cached_data(db: Session, cache_key: str, data: dict, ttl_minutes: int = 60):
        """Set cached data"""
        # Delete old cache
        db.query(CachedData).filter(CachedData.cache_key == cache_key).delete()
        
        cached = CachedData(
            cache_key=cache_key,
            data=data,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
        )
        db.add(cached)
        db.commit()

# ==================== ANALYTICS EVENTS ====================
class AnalyticsCRUD:
    @staticmethod
    def track_event(db: Session, event_data: dict):
        """Track analytics event"""
        event = AnalyticsEvent(**event_data)
        db.add(event)
        db.commit()
        return event
    
    @staticmethod
    def get_events_by_type(db: Session, event_type: str, limit: int = 100):
        """Get events by type"""
        return db.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == event_type
        ).order_by(AnalyticsEvent.created_at.desc()).limit(limit).all()