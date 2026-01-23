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
            return {"user_id": 1, "email": "customer@test.com", "role": "client"}
        return None

class UserRole:
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"

app = FastAPI(
    title="Service Booking Service",
    description="Appointment booking service for auto dealership",
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

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "service-booking"}

@app.get("/")
async def root():
    return {
        "service": "Service Booking Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "slots": "/slots",
            "appointments": "/appointments",
            "technicians": "/technicians",
            "services": "/services"
        }
    }

# ==================== TECHNICIAN ENDPOINTS ====================
@app.post("/technicians", response_model=dict)
async def create_technician(
    technician_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new technician (admin/managers only)"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    technician = crud.TechnicianCRUD.create_technician(db, technician_data, current_user.get("user_id"))
    
    return {
        "message": "Technician created successfully",
        "technician_id": technician.id,
        "name": f"{technician.first_name} {technician.last_name}"
    }

@app.get("/technicians", response_model=List[dict])
async def get_technicians(
    branch_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get technicians"""
    technicians = db.query(models.Technician)
    
    if active_only:
        technicians = technicians.filter(models.Technician.is_active == True)
    
    if branch_id:
        # Здесь нужна логика фильтрации по филиалу
        pass
    
    result = technicians.all()
    
    return [
        {
            "id": t.id,
            "employee_id": t.employee_id,
            "first_name": t.first_name,
            "last_name": t.last_name,
            "specialization": t.specialization,
            "phone": t.phone,
            "email": t.email,
            "is_active": t.is_active
        }
        for t in result
    ]

# ==================== SERVICE SLOT ENDPOINTS ====================
@app.post("/slots", response_model=dict)
async def create_slots(
    branch_id: int,
    start_date: str,  # ISO format
    end_date: str,    # ISO format
    duration: int = 60,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create time slots (admin/managers only)"""
    if current_user.get("role") not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from datetime import datetime
    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    
    slots = crud.ServiceSlotCRUD.create_slots(
        db, branch_id, start, end, duration, current_user.get("user_id")
    )
    
    return {
        "message": f"{len(slots)} slots created successfully",
        "branch_id": branch_id,
        "date_range": {"start": start_date, "end": end_date}
    }

@app.get("/slots/available", response_model=List[dict])
async def get_available_slots(
    branch_id: int,
    date: str,  # ISO format date only (YYYY-MM-DD)
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get available slots for branch on date"""
    from datetime import datetime
    target_date = datetime.fromisoformat(date)
    
    slots = crud.ServiceSlotCRUD.get_available_slots(db, branch_id, target_date)
    
    return [
        {
            "id": s.id,
            "slot_date": s.slot_date.isoformat(),
            "duration_minutes": s.duration_minutes,
            "status": s.status.value,
            "technician_id": s.technician_id
        }
        for s in slots
    ]

# ==================== APPOINTMENT ENDPOINTS ====================
@app.post("/appointments", response_model=dict)
async def create_appointment(
    appointment_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new appointment"""
    # Добавляем user_id в данные
    appointment_data["created_by"] = current_user.get("user_id")
    
    appointment = crud.AppointmentCRUD.create_appointment(
        db, appointment_data, current_user.get("user_id")
    )
    
    return {
        "message": "Appointment created successfully",
        "appointment_id": appointment.id,
        "scheduled_start": appointment.scheduled_start.isoformat(),
        "status": appointment.status.value
    }

@app.get("/appointments/{appointment_id}", response_model=dict)
async def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get appointment by ID"""
    appointment = crud.AppointmentCRUD.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {
        "id": appointment.id,
        "customer_id": appointment.customer_id,
        "vehicle_id": appointment.vehicle_id,
        "branch_id": appointment.branch_id,
        "appointment_type": appointment.appointment_type.value,
        "status": appointment.status.value,
        "scheduled_start": appointment.scheduled_start.isoformat(),
        "scheduled_end": appointment.scheduled_end.isoformat(),
        "estimated_cost": appointment.estimated_cost,
        "description": appointment.description,
        "notes": appointment.notes
    }

@app.get("/appointments", response_model=List[dict])
async def get_my_appointments(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's appointments"""
    # Предполагаем, что current_user["user_id"] соответствует customer_id
    appointments = crud.AppointmentCRUD.get_customer_appointments(
        db, current_user.get("user_id"), status
    )
    
    return [
        {
            "id": a.id,
            "vehicle_id": a.vehicle_id,
            "branch_id": a.branch_id,
            "appointment_type": a.appointment_type.value,
            "status": a.status.value,
            "scheduled_start": a.scheduled_start.isoformat(),
            "scheduled_end": a.scheduled_end.isoformat(),
            "estimated_cost": a.estimated_cost
        }
        for a in appointments
    ]

@app.put("/appointments/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update appointment status"""
    from models import AppointmentStatus
    
    try:
        status_enum = AppointmentStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {[s.value for s in AppointmentStatus]}")
    
    appointment = crud.AppointmentCRUD.update_status(
        db, appointment_id, status_enum, current_user.get("user_id"), notes
    )
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return {
        "message": "Appointment status updated",
        "appointment_id": appointment.id,
        "new_status": appointment.status.value
    }

# ==================== SERVICE ENDPOINTS ====================
@app.get("/services", response_model=List[dict])
async def get_services(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get available services"""
    services = crud.ServiceCRUD.get_services(db, category, active_only)
    
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "duration_minutes": s.duration_minutes,
            "base_price": s.base_price,
            "is_active": s.is_active
        }
        for s in services
    ]

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    print("Service Booking Service starting up...")
    
    # Инициализируем БД
    init_db()
    print("Database initialized")
    
    # Subscribe to events
    from crud import message_broker
    message_broker.subscribe_to_events(
        exchange="booking",
        routing_keys=["booking.*"],
        callback=lambda event: print(f"Booking event received: {event['event_type']}")
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)