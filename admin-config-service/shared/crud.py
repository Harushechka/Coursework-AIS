from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime
import json

from models import (
    Base, Branch, Employee, Tariff, RolePermission, SystemSetting, ConfigChangeLog, 
    ConfigType, BranchStatus, EmployeeRole
)

# Заглушки вместо общего shared модуля
class ConfigEvent:
    pass

class MessageBroker:
    def publish_event(self, exchange, routing_key, event_data):
        print(f"[STUB] Event: {exchange}.{routing_key} - {event_data}")
    
    def subscribe_to_events(self, exchange, routing_keys, callback):
        print(f"[STUB] Subscribed to {exchange}: {routing_keys}")

message_broker = MessageBroker()

# ==================== BRANCH OPERATIONS ====================
class BranchCRUD:
    @staticmethod
    def create_branch(db: Session, branch_data: dict, user_id: int):
        """Create new branch"""
        branch = Branch(**branch_data)
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
        # Publish event
        message_broker.publish_event(
            exchange="config",
            routing_key="branch.created",
            event_data={
                "branch_id": branch.id,
                "name": branch.name,
                "created_by": user_id
            }
        )
        
        # Log change
        ConfigChangeLogCRUD.log_change(
            db=db,
            config_type=ConfigType.BRANCH,
            config_id=branch.id,
            changed_by=user_id,
            change_type="create",
            new_value=json.dumps(branch_data)
        )
        
        return branch
    
    @staticmethod
    def get_branch(db: Session, branch_id: int):
        """Get branch by ID"""
        return db.query(Branch).filter(Branch.id == branch_id).first()
    
    @staticmethod
    def get_branches(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None):
        """Get all branches with optional filtering"""
        query = db.query(Branch)
        if status:
            query = query.filter(Branch.status == status)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def update_branch(db: Session, branch_id: int, update_data: dict, user_id: int):
        """Update branch"""
        branch = db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            return None
        
        old_values = {col.name: getattr(branch, col.name) for col in Branch.__table__.columns}
        
        for key, value in update_data.items():
            if hasattr(branch, key):
                setattr(branch, key, value)
        
        branch.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(branch)
        
        # Publish event
        message_broker.publish_event(
            exchange="config",
            routing_key="branch.updated",
            event_data={
                "branch_id": branch.id,
                "updated_by": user_id,
                "changes": update_data
            }
        )
        
        # Log change
        ConfigChangeLogCRUD.log_change(
            db=db,
            config_type=ConfigType.BRANCH,
            config_id=branch.id,
            changed_by=user_id,
            change_type="update",
            old_value=json.dumps(old_values),
            new_value=json.dumps(update_data)
        )
        
        return branch

# ==================== EMPLOYEE OPERATIONS ====================
class EmployeeCRUD:
    @staticmethod
    def create_employee(db: Session, employee_data: dict, user_id: int):
        """Create new employee"""
        employee = Employee(**employee_data)
        db.add(employee)
        db.commit()
        db.refresh(employee)
        
        message_broker.publish_event(
            exchange="config",
            routing_key="employee.created",
            event_data={
                "employee_id": employee.id,
                "user_id": employee.user_id,
                "branch_id": employee.branch_id,
                "created_by": user_id
            }
        )
        
        return employee
    
    @staticmethod
    def get_employees_by_branch(db: Session, branch_id: int, active_only: bool = True):
        """Get employees by branch"""
        query = db.query(Employee).filter(Employee.branch_id == branch_id)
        if active_only:
            query = query.filter(Employee.is_active == True)
        return query.all()
    
    @staticmethod
    def get_employee_by_user_id(db: Session, user_id: int):
        """Get employee by user ID"""
        return db.query(Employee).filter(Employee.user_id == user_id).first()

# ==================== TARIFF OPERATIONS ====================
class TariffCRUD:
    @staticmethod
    def create_tariff(db: Session, tariff_data: dict, user_id: int):
        """Create new tariff"""
        tariff = Tariff(**tariff_data)
        db.add(tariff)
        db.commit()
        db.refresh(tariff)
        
        message_broker.publish_event(
            exchange="config",
            routing_key="tariff.created",
            event_data={
                "tariff_id": tariff.id,
                "name": tariff.name,
                "price": tariff.price,
                "created_by": user_id
            }
        )
        
        return tariff
    
    @staticmethod
    def get_active_tariffs(db: Session):
        """Get all active tariffs"""
        now = datetime.utcnow()
        return db.query(Tariff).filter(
            Tariff.is_active == True,
            or_(
                Tariff.valid_to == None,
                Tariff.valid_to > now
            )
        ).all()

# ==================== ROLE PERMISSION OPERATIONS ====================
class RolePermissionCRUD:
    @staticmethod
    def set_permission(db: Session, permission_data: dict, user_id: int):
        """Set or update permission"""
        # Check if exists
        existing = db.query(RolePermission).filter(
            RolePermission.role_name == permission_data["role_name"],
            RolePermission.service_name == permission_data["service_name"],
            RolePermission.endpoint == permission_data["endpoint"],
            RolePermission.method == permission_data["method"]
        ).first()
        
        if existing:
            # Update
            existing.is_allowed = permission_data["is_allowed"]
        else:
            # Create new
            existing = RolePermission(**permission_data)
            db.add(existing)
        
        db.commit()
        db.refresh(existing)
        
        message_broker.publish_event(
            exchange="config",
            routing_key="permission.updated",
            event_data={
                "role": permission_data["role_name"],
                "service": permission_data["service_name"],
                "endpoint": permission_data["endpoint"],
                "allowed": permission_data["is_allowed"],
                "updated_by": user_id
            }
        )
        
        return existing
    
    @staticmethod
    def check_permission(db: Session, role: str, service: str, endpoint: str, method: str) -> bool:
        """Check if role has permission"""
        permission = db.query(RolePermission).filter(
            RolePermission.role_name == role,
            RolePermission.service_name == service,
            RolePermission.endpoint == endpoint,
            RolePermission.method == method
        ).first()
        
        return permission.is_allowed if permission else True  # Default to allowed if no rule

# ==================== SYSTEM SETTINGS OPERATIONS ====================
class SystemSettingCRUD:
    @staticmethod
    def set_setting(db: Session, key: str, value: str, description: str = "", 
                   category: str = "general", is_public: bool = False, user_id: int = None):
        """Set system setting"""
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        
        old_value = setting.value if setting else None
        
        if setting:
            setting.value = value
            setting.description = description
            setting.category = category
            setting.is_public = is_public
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSetting(
                key=key, value=value, description=description,
                category=category, is_public=is_public
            )
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        
        if user_id:
            message_broker.publish_event(
                exchange="config",
                routing_key="setting.updated",
                event_data={
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "updated_by": user_id
                }
            )
        
        return setting
    
    @staticmethod
    def get_setting(db: Session, key: str):
        """Get system setting by key"""
        return db.query(SystemSetting).filter(SystemSetting.key == key).first()
    
    @staticmethod
    def get_public_settings(db: Session):
        """Get all public settings"""
        return db.query(SystemSetting).filter(SystemSetting.is_public == True).all()

# ==================== CONFIG CHANGE LOG ====================
class ConfigChangeLogCRUD:
    @staticmethod
    def log_change(db: Session, config_type: ConfigType, config_id: int, 
                  changed_by: int, change_type: str, old_value: str = None, 
                  new_value: str = None):
        """Log configuration change"""
        log_entry = ConfigChangeLog(
            config_type=config_type,
            config_id=config_id,
            changed_by=changed_by,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value
        )
        db.add(log_entry)
        db.commit()
        return log_entry
    
    @staticmethod
    def get_changes(db: Session, config_type: Optional[str] = None, 
                   config_id: Optional[int] = None, limit: int = 100):
        """Get configuration changes"""
        query = db.query(ConfigChangeLog)
        
        if config_type:
            query = query.filter(ConfigChangeLog.config_type == config_type)
        if config_id:
            query = query.filter(ConfigChangeLog.config_id == config_id)
        
        return query.order_by(ConfigChangeLog.change_timestamp.desc()).limit(limit).all()