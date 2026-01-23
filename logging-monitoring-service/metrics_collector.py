import psutil
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import httpx

from models import SystemMetric
from database import SessionLocal
from config import settings
import crud

class MetricsCollector:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
        self.service_name = settings.SERVICE_NAME
        self.instance_id = f"{self.service_name}-{psutil.Process().pid}"
    
    async def collect_system_metrics(self) -> List[Dict[str, Any]]:
        """Collect system metrics"""
        metrics = []
        current_time = datetime.utcnow()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append({
                "timestamp": current_time,
                "metric_name": "cpu_usage_percent",
                "metric_value": cpu_percent,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "system"}
            })
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.append({
                "timestamp": current_time,
                "metric_name": "memory_usage_percent",
                "metric_value": memory.percent,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "system"}
            })
            
            metrics.append({
                "timestamp": current_time,
                "metric_name": "memory_available_mb",
                "metric_value": memory.available / (1024 * 1024),
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "system"}
            })
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            metrics.append({
                "timestamp": current_time,
                "metric_name": "disk_usage_percent",
                "metric_value": disk.percent,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "system"}
            })
            
            # Network metrics
            net_io = psutil.net_io_counters()
            metrics.append({
                "timestamp": current_time,
                "metric_name": "network_bytes_sent",
                "metric_value": net_io.bytes_sent,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "network", "direction": "sent"}
            })
            
            metrics.append({
                "timestamp": current_time,
                "metric_name": "network_bytes_received",
                "metric_value": net_io.bytes_recv,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "network", "direction": "received"}
            })
            
            # Process metrics
            process = psutil.Process()
            metrics.append({
                "timestamp": current_time,
                "metric_name": "process_cpu_percent",
                "metric_value": process.cpu_percent(),
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "process"}
            })
            
            metrics.append({
                "timestamp": current_time,
                "metric_name": "process_memory_mb",
                "metric_value": process.memory_info().rss / (1024 * 1024),
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "process"}
            })
            
            metrics.append({
                "timestamp": current_time,
                "metric_name": "process_threads",
                "metric_value": process.num_threads(),
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "process"}
            })
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
        
        return metrics
    
    async def collect_service_metrics(self) -> List[Dict[str, Any]]:
        """Collect service-specific metrics"""
        metrics = []
        current_time = datetime.utcnow()
        
        try:
            db = SessionLocal()
            
            # Database metrics
            from sqlalchemy import func, text
            
            # Log counts by level
            log_counts = db.execute(text("""
                SELECT level, COUNT(*) as count 
                FROM application_logs 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY level
            """)).fetchall()
            
            for level, count in log_counts:
                metrics.append({
                    "timestamp": current_time,
                    "metric_name": f"logs_{level.lower()}_per_hour",
                    "metric_value": count,
                    "service": self.service_name,
                    "instance_id": self.instance_id,
                    "tags": {"metric_type": "service", "log_level": level}
                })
            
            # Total logs count
            total_logs = db.execute(text("SELECT COUNT(*) FROM application_logs")).scalar()
            metrics.append({
                "timestamp": current_time,
                "metric_name": "total_logs",
                "metric_value": total_logs,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "service"}
            })
            
            # Database connection pool metrics (simplified)
            metrics.append({
                "timestamp": current_time,
                "metric_name": "heartbeat",
                "metric_value": 1,
                "service": self.service_name,
                "instance_id": self.instance_id,
                "tags": {"metric_type": "health"}
            })
            
            db.close()
            
        except Exception as e:
            print(f"Error collecting service metrics: {e}")
        
        return metrics
    
    async def save_metrics(self, metrics: List[Dict[str, Any]]):
        """Save metrics to database"""
        if not metrics:
            return
        
        db = SessionLocal()
        try:
            for metric_data in metrics:
                metric = SystemMetric(**metric_data)
                db.add(metric)
            
            db.commit()
        except Exception as e:
            print(f"Error saving metrics: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def collect_and_save_all_metrics(self):
        """Collect and save all metrics"""
        system_metrics = await self.collect_system_metrics()
        service_metrics = await self.collect_service_metrics()
        
        all_metrics = system_metrics + service_metrics
        
        if all_metrics:
            await self.save_metrics(all_metrics)
            print(f"Collected and saved {len(all_metrics)} metrics")
    
    async def start_periodic_collection(self, interval_seconds: int = 60):
        """Start periodic metrics collection"""
        while True:
            try:
                await self.collect_and_save_all_metrics()
            except Exception as e:
                print(f"Error in metrics collection: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    async def check_service_health(self, service_url: str, service_name: str) -> Dict[str, Any]:
        """Check health of external service"""
        try:
            start_time = time.time()
            response = await self.client.get(f"{service_url}/health", timeout=5.0)
            response_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "service": service_name,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response_time,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            return {
                "service": service_name,
                "status": "unavailable",
                "error": str(e),
                "response_time_ms": 0,
                "timestamp": datetime.utcnow()
            }

# Global instance
metrics_collector = MetricsCollector()