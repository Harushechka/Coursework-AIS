from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_
from typing import List, Optional
from datetime import datetime, timedelta
import json

from models import (
    Technician, ServiceSlot, Appointment, Service, AppointmentService,
    AppointmentType, AppointmentStatus, ServiceSlotStatus
)

# Заглушки вместо общего shared модуля
class BookingEvent:
    pass

class MessageBroker:
    def publish_event(self, exchange, routing_key, event_data):
        print(f"[STUB] Event: {exchange}.{routing_key} - {event_data}")
    
    def subscribe_to_events(self, exchange, routing_keys, callback):
        print(f"[STUB] Subscribed to {exchange}: {routing_keys}")

message_broker = MessageBroker()

# ==================== TECHNICIAN OPERATIONS ====================
class TechnicianCRUD:
    @staticmethod
    def create_technician(db: Session, technician_data: dict, user_id: int):
        """Create new technician"""
        technician = Technician(**technician_data)
        db.add(technician)
        db.commit()
        db.refresh(technician)
        
        message_broker.publish_event(
            exchange="booking",
            routing_key="technician.created",
            event_data={
                "technician_id": technician.id,
                "employee_id": technician.employee_id,
                "created_by": user_id
            }
        )
        
        return technician
    
    @staticmethod
    def get_available_technicians(db: Session, branch_id: int, date: datetime):
        """Get technicians available at specific branch on date"""
        return db.query(Technician).filter(
            Technician.is_active == True
        ).all()

# ==================== SERVICE SLOT OPERATIONS ====================
class ServiceSlotCRUD:
    @staticmethod
    def create_slots(db: Session, branch_id: int, start_date: datetime, 
                    end_date: datetime, duration: int = 60, user_id: int = None):
        """Create time slots for a date range"""
        slots = []
        current = start_date
        
        while current < end_date:
            slot = ServiceSlot(
                branch_id=branch_id,
                slot_date=current,
                duration_minutes=duration,
                status=ServiceSlotStatus.AVAILABLE
            )
            slots.append(slot)
            current += timedelta(minutes=duration)
        
        db.add_all(slots)
        db.commit()
        
        if user_id:
            message_broker.publish_event(
                exchange="booking",
                routing_key="slots.created",
                event_data={
                    "branch_id": branch_id,
                    "count": len(slots),
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "created_by": user_id
                }
            )
        
        return slots
    
    @staticmethod
    def get_available_slots(db: Session, branch_id: int, date: datetime):
        """Get available slots for branch on date"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        return db.query(ServiceSlot).filter(
            ServiceSlot.branch_id == branch_id,
            ServiceSlot.slot_date >= start_of_day,
            ServiceSlot.slot_date < end_of_day,
            ServiceSlot.status == ServiceSlotStatus.AVAILABLE
        ).order_by(ServiceSlot.slot_date).all()

# ==================== APPOINTMENT OPERATIONS ====================
class AppointmentCRUD:
    @staticmethod
    def create_appointment(db: Session, appointment_data: dict, user_id: int):
        """Create new appointment"""
        appointment = Appointment(**appointment_data)
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        
        # Update slot status
        slot = db.query(ServiceSlot).filter(ServiceSlot.id == appointment.slot_id).first()
        if slot:
            slot.status = ServiceSlotStatus.BOOKED
            db.commit()
        
        # Publish event
        message_broker.publish_event(
            exchange="booking",
            routing_key="appointment.created",
            event_data={
                "appointment_id": appointment.id,
                "customer_id": appointment.customer_id,
                "vehicle_id": appointment.vehicle_id,
                "branch_id": appointment.branch_id,
                "scheduled_start": appointment.scheduled_start.isoformat(),
                "type": appointment.appointment_type.value,
                "created_by": user_id
            }
        )
        
        return appointment
    
    @staticmethod
    def get_appointment(db: Session, appointment_id: int):
        """Get appointment by ID with relationships"""
        return db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    @staticmethod
    def get_customer_appointments(db: Session, customer_id: int, 
                                 status: Optional[str] = None):
        """Get appointments for customer"""
        query = db.query(Appointment).filter(Appointment.customer_id == customer_id)
        
        if status:
            query = query.filter(Appointment.status == status)
        
        return query.order_by(Appointment.scheduled_start.desc()).all()
    
    @staticmethod
    def update_status(db: Session, appointment_id: int, status: AppointmentStatus, 
                     user_id: int, notes: str = None):
        """Update appointment status"""
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return None
        
        old_status = appointment.status
        appointment.status = status
        appointment.updated_at = datetime.utcnow()
        
        if notes:
            appointment.notes = notes
        
        # If cancelled, free up the slot
        if status == AppointmentStatus.CANCELLED:
            slot = db.query(ServiceSlot).filter(ServiceSlot.id == appointment.slot_id).first()
            if slot:
                slot.status = ServiceSlotStatus.AVAILABLE
        
        db.commit()
        
        # Publish event
        message_broker.publish_event(
            exchange="booking",
            routing_key="appointment.updated",
            event_data={
                "appointment_id": appointment.id,
                "old_status": old_status.value,
                "new_status": status.value,
                "updated_by": user_id
            }
        )
        
        return appointment

# ==================== SERVICE OPERATIONS ====================
class ServiceCRUD:
    @staticmethod
    def create_service(db: Session, service_data: dict, user_id: int):
        """Create new service"""
        service = Service(**service_data)
        db.add(service)
        db.commit()
        db.refresh(service)
        
        message_broker.publish_event(
            exchange="booking",
            routing_key="service.created",
            event_data={
                "service_id": service.id,
                "name": service.name,
                "price": service.base_price,
                "created_by": user_id
            }
        )
        
        return service
    
    @staticmethod
    def get_services(db: Session, category: Optional[str] = None, active_only: bool = True):
        """Get all services"""
        query = db.query(Service)
        
        if active_only:
            query = query.filter(Service.is_active == True)
        
        if category:
            query = query.filter(Service.category == category)
        
        return query.all()