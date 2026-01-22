import logging
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
import asyncio
from sqlalchemy.orm import Session

from models import ApplicationLog, LogLevel, LogSource
from database import SessionLocal
import config

# Настройка structlog для структурированного логирования
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

class LogHandler:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
        self.batch_size = 100
        self.log_buffer = []
    
    async def log_to_database(self, log_data: Dict[str, Any]):
        """Save log to database"""
        try:
            db = SessionLocal()
            try:
                # Convert string level to enum
                if isinstance(log_data.get('level'), str):
                    log_data['level'] = LogLevel(log_data['level'].upper())
                
                # Convert string source to enum
                if isinstance(log_data.get('source'), str):
                    log_data['source'] = LogSource(log_data['source'].lower())
                
                log = ApplicationLog(**log_data)
                db.add(log)
                db.commit()
                
                # Also log locally
                self._log_locally(log_data)
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error saving log to database: {e}")
            self._log_locally(log_data)
    
    def _log_locally(self, log_data: Dict[str, Any]):
        """Local fallback logging"""
        level = log_data.get('level', 'INFO').lower()
        message = log_data.get('message', '')
        
        if level == 'error':
            logger.error(message, **log_data)
        elif level == 'warning':
            logger.warning(message, **log_data)
        elif level == 'info':
            logger.info(message, **log_data)
        elif level == 'debug':
            logger.debug(message, **log_data)
        else:
            logger.info(message, **log_data)
    
    async def process_log_batch(self, logs: list):
        """Process batch of logs"""
        for log_data in logs:
            await self.log_to_database(log_data)
    
    async def log_external(self, service_name: str, level: str, message: str, **kwargs):
        """Log from external service (simplified - could be via HTTP/RabbitMQ)"""
        log_data = {
            "timestamp": datetime.utcnow(),
            "level": level,
            "source": LogSource.SYSTEM,
            "service": service_name,
            "message": message,
            "additional_data": kwargs
        }
        
        await self.log_to_database(log_data)
    
    def create_request_log(self, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured log for HTTP request"""
        return {
            "timestamp": datetime.utcnow(),
            "level": "INFO",
            "source": LogSource.API_GATEWAY,
            "service": request_info.get('service', 'unknown'),
            "message": f"HTTP {request_info.get('method')} {request_info.get('endpoint')}",
            "endpoint": request_info.get('endpoint'),
            "method": request_info.get('method'),
            "status_code": request_info.get('status_code'),
            "response_time_ms": request_info.get('response_time_ms'),
            "user_id": request_info.get('user_id'),
            "ip_address": request_info.get('ip_address'),
            "user_agent": request_info.get('user_agent'),
            "correlation_id": request_info.get('correlation_id'),
            "additional_data": {
                "query_params": request_info.get('query_params'),
                "body_size": request_info.get('body_size')
            }
        }
    
    async def cleanup_old_logs(self, days: int = 30):
        """Cleanup logs older than specified days"""
        try:
            db = SessionLocal()
            try:
                from sqlalchemy import func, text
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Archive old logs (simplified)
                # In production, you might want to move to cold storage
                result = db.query(ApplicationLog).filter(
                    ApplicationLog.timestamp < cutoff_date
                ).delete()
                
                db.commit()
                logger.info(f"Cleaned up {result} logs older than {days} days")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

# Global instance
log_handler = LogHandler()

# Utility functions for easy logging
async def log_error(service: str, message: str, error: Exception = None, **kwargs):
    """Log error with stack trace"""
    log_data = {
        "timestamp": datetime.utcnow(),
        "level": LogLevel.ERROR,
        "source": LogSource.SYSTEM,
        "service": service,
        "message": message,
        "additional_data": kwargs
    }
    
    if error:
        import traceback
        log_data["stack_trace"] = traceback.format_exc()
        log_data["additional_data"]["error_type"] = type(error).__name__
        log_data["additional_data"]["error_message"] = str(error)
    
    await log_handler.log_to_database(log_data)

async def log_audit(user_id: int, action: str, entity_type: str = None, 
                   entity_id: int = None, old_values: dict = None, 
                   new_values: dict = None, **kwargs):
    """Log audit trail"""
    from crud import AuditCRUD
    
    db = SessionLocal()
    try:
        audit_data = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_values": old_values,
            "new_values": new_values,
            "changes": _calculate_changes(old_values, new_values),
            "meta_info": kwargs
        }
        
        AuditCRUD.create_audit(db, audit_data)
        
    finally:
        db.close()

def _calculate_changes(old_values: dict, new_values: dict) -> dict:
    """Calculate differences between old and new values"""
    if not old_values or not new_values:
        return {}
    
    changes = {}
    all_keys = set(old_values.keys()) | set(new_values.keys())
    
    for key in all_keys:
        old_val = old_values.get(key)
        new_val = new_values.get(key)
        
        if old_val != new_val:
            changes[key] = {
                "old": old_val,
                "new": new_val
            }
    
    return changes