from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os

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
            return {"user_id": 1, "email": "admin@test.com", "role": "admin"}
        return None

class UserRole:
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"

class ConfigType:
    BRANCH = "branch"
    EMPLOYEE = "employee"
    TARIFF = "tariff"
    ROLE = "role"
    SYSTEM = "system"

app = FastAPI(
    title="Admin Config Service",
    description="Configuration management service for auto dealership",
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
async def get_current_user(token: str = Depends(AuthUtils.verify_token)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return token

# Dependency to check admin role
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
    return {"status": "healthy", "service": "admin-config"}

@app.get("/")
async def root():
    return {
        "service": "Admin Config Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "branches": "/branches",
            "employees": "/branches/{branch_id}/employees",
            "tariffs": "/tariffs",
            "permissions": "/permissions",
            "settings": "/settings"
        }
    }

# ==================== BRANCH ENDPOINTS ====================
@app.post("/branches", response_model=dict)
async def create_branch(
    branch_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create new branch"""
    try:
        branch = crud.BranchCRUD.create_branch(db, branch_data, current_user.get("user_id"))
        return {
            "message": "Branch created successfully",
            "branch_id": branch.id,
            "branch_name": branch.name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/branches", response_model=List[dict])
async def get_branches(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all branches"""
    branches = crud.BranchCRUD.get_branches(db, skip, limit, status)
    return [
        {
            "id": b.id,
            "name": b.name,
            "address": b.address,
            "city": b.city,
            "status": b.status.value,
            "manager_id": b.manager_id,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        for b in branches
    ]

@app.get("/branches/{branch_id}", response_model=dict)
async def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get branch by ID"""
    branch = crud.BranchCRUD.get_branch(db, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return {
        "id": branch.id,
        "name": branch.name,
        "address": branch.address,
        "city": branch.city,
        "phone": branch.phone,
        "email": branch.email,
        "status": branch.status.value,
        "manager_id": branch.manager_id,
        "created_at": branch.created_at.isoformat() if branch.created_at else None,
        "updated_at": branch.updated_at.isoformat() if branch.updated_at else None
    }

@app.put("/branches/{branch_id}")
async def update_branch(
    branch_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update branch"""
    branch = crud.BranchCRUD.update_branch(db, branch_id, update_data, current_user.get("user_id"))
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    return {
        "message": "Branch updated successfully",
        "branch_id": branch.id
    }

# ==================== EMPLOYEE ENDPOINTS ====================
@app.post("/branches/{branch_id}/employees", response_model=dict)
async def create_employee(
    branch_id: int,
    employee_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create employee for branch"""
    employee_data["branch_id"] = branch_id
    employee = crud.EmployeeCRUD.create_employee(db, employee_data, current_user.get("user_id"))
    
    return {
        "message": "Employee created successfully",
        "employee_id": employee.id,
        "user_id": employee.user_id
    }

@app.get("/branches/{branch_id}/employees", response_model=List[dict])
async def get_branch_employees(
    branch_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get employees for branch"""
    employees = crud.EmployeeCRUD.get_employees_by_branch(db, branch_id, active_only)
    
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "position": e.position,
            "role": e.role.value,
            "phone": e.phone,
            "email": e.email,
            "hire_date": e.hire_date.isoformat() if e.hire_date else None,
            "is_active": e.is_active
        }
        for e in employees
    ]

@app.get("/employees/user/{user_id}", response_model=dict)
async def get_employee_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get employee by user ID"""
    employee = crud.EmployeeCRUD.get_employee_by_user_id(db, user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "user_id": employee.user_id,
        "branch_id": employee.branch_id,
        "first_name": employee.first_name,
        "last_name": employee.last_name,
        "position": employee.position,
        "role": employee.role.value,
        "is_active": employee.is_active
    }

# ==================== TARIFF ENDPOINTS ====================
@app.post("/tariffs", response_model=dict)
async def create_tariff(
    tariff_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create new tariff"""
    tariff = crud.TariffCRUD.create_tariff(db, tariff_data, current_user.get("user_id"))
    
    return {
        "message": "Tariff created successfully",
        "tariff_id": tariff.id,
        "name": tariff.name
    }

@app.get("/tariffs", response_model=List[dict])
async def get_tariffs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all active tariffs"""
    tariffs = crud.TariffCRUD.get_active_tariffs(db)
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "price": t.price,
            "currency": t.currency,
            "valid_from": t.valid_from.isoformat() if t.valid_from else None,
            "valid_to": t.valid_to.isoformat() if t.valid_to else None,
            "is_active": t.is_active
        }
        for t in tariffs
    ]

# ==================== PERMISSION ENDPOINTS ====================
@app.post("/permissions", response_model=dict)
async def set_permission(
    permission_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Set or update permission"""
    required_fields = ["role_name", "service_name", "endpoint", "method", "is_allowed"]
    for field in required_fields:
        if field not in permission_data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")
    
    permission = crud.RolePermissionCRUD.set_permission(db, permission_data, current_user.get("user_id"))
    
    return {
        "message": "Permission set successfully",
        "permission_id": permission.id
    }

@app.get("/permissions/check")
async def check_permission(
    role: str,
    service: str,
    endpoint: str,
    method: str = "GET",
    db: Session = Depends(get_db)
):
    """Check permission (public endpoint)"""
    is_allowed = crud.RolePermissionCRUD.check_permission(db, role, service, endpoint, method)
    
    return {
        "role": role,
        "service": service,
        "endpoint": endpoint,
        "method": method,
        "is_allowed": is_allowed
    }

# ==================== SYSTEM SETTINGS ENDPOINTS ====================
@app.post("/settings", response_model=dict)
async def set_setting(
    key: str,
    value: str,
    description: str = "",
    category: str = "general",
    is_public: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Set system setting"""
    setting = crud.SystemSettingCRUD.set_setting(
        db, key, value, description, category, is_public, current_user.get("user_id")
    )
    
    return {
        "message": "Setting updated successfully",
        "key": setting.key,
        "value": setting.value
    }

@app.get("/settings/{key}")
async def get_setting(
    key: str,
    db: Session = Depends(get_db)
):
    """Get system setting (public if marked as public)"""
    setting = crud.SystemSettingCRUD.get_setting(db, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if not setting.is_public:
        # Require authentication for non-public settings
        current_user = await get_current_user()
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "key": setting.key,
        "value": setting.value,
        "description": setting.description,
        "category": setting.category,
        "is_public": setting.is_public,
        "created_at": setting.created_at.isoformat() if setting.created_at else None
    }

@app.get("/settings")
async def get_settings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all settings (requires authentication)"""
    settings = db.query(models.SystemSetting).all()
    
    return [
        {
            "key": s.key,
            "value": s.value,
            "description": s.description,
            "category": s.category,
            "is_public": s.is_public,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in settings
    ]

# ==================== CHANGE LOG ENDPOINTS ====================
@app.get("/changes")
async def get_changes(
    config_type: Optional[str] = None,
    config_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get configuration change log"""
    changes = crud.ConfigChangeLogCRUD.get_changes(db, config_type, config_id, limit)
    
    return [
        {
            "id": c.id,
            "config_type": c.config_type.value,
            "config_id": c.config_id,
            "changed_by": c.changed_by,
            "change_type": c.change_type,
            "change_timestamp": c.change_timestamp.isoformat() if c.change_timestamp else None
        }
        for c in changes
    ]

# Startup event
# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Admin Config Service starting up...")
    
    # Инициализируем БД (создаём таблицы если их нет)
    init_db()
    print("Database initialized")
    
    # Subscribe to config events from other services
    from crud import message_broker  # Добавляем импорт здесь
    message_broker.subscribe_to_events(
        exchange="config",
        routing_keys=["config.*"],
        callback=lambda event: print(f"Config event received: {event['event_type']}")
    )
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)