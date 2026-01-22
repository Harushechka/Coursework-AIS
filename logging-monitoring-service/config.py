import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@logging-db:5432/logging_db")
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Service
    SERVICE_NAME: str = "logging-monitoring-service"
    SERVICE_VERSION: str = "1.0.0"
    
    # Retention policies (in days)
    LOG_RETENTION_DAYS: int = 30
    METRICS_RETENTION_DAYS: int = 7
    AUDIT_RETENTION_DAYS: int = 90
    
    # API
    API_PREFIX: str = ""
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Monitoring
    METRICS_INTERVAL_SECONDS: int = 60
    HEALTH_CHECK_INTERVAL: int = 30
    
    # Elasticsearch (optional)
    ELASTICSEARCH_URL: Optional[str] = os.getenv("ELASTICSEARCH_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()