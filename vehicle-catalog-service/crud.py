from sqlalchemy.orm import Session
from sqlalchemy import and_
import models
import schemas
from typing import List, Optional, Dict

def get_vehicle(db: Session, vehicle_id: int):
    return db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()

def get_vehicle_by_vin(db: Session, vin: str):
    return db.query(models.Vehicle).filter(models.Vehicle.vin == vin).first()

def get_vehicles(db: Session, skip: int = 0, limit: int = 100, filters: Optional[Dict] = None):
    query = db.query(models.Vehicle)
    
    if filters:
        if filters.get("brand"):
            query = query.filter(models.Vehicle.brand.ilike(f"%{filters['brand']}%"))
        if filters.get("model"):
            query = query.filter(models.Vehicle.model.ilike(f"%{filters['model']}%"))
        if filters.get("min_year"):
            query = query.filter(models.Vehicle.year >= filters["min_year"])
        if filters.get("max_year"):
            query = query.filter(models.Vehicle.year <= filters["max_year"])
        if filters.get("min_price"):
            query = query.filter(models.Vehicle.price >= filters["min_price"])
        if filters.get("max_price"):
            query = query.filter(models.Vehicle.price <= filters["max_price"])
    
    return query.offset(skip).limit(limit).all()

def create_vehicle(db: Session, vehicle: schemas.VehicleCreate):
    # Проверяем уникальность VIN
    existing = get_vehicle_by_vin(db, vehicle.vin)
    if existing:
        raise ValueError(f"Vehicle with VIN {vehicle.vin} already exists")
    
    db_vehicle = models.Vehicle(**vehicle.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def update_vehicle(db: Session, vehicle_id: int, vehicle: schemas.VehicleUpdate):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        return None
    
    update_data = vehicle.model_dump(exclude_unset=True)
    
    # Если обновляется VIN, проверяем уникальность
    if "vin" in update_data and update_data["vin"] != db_vehicle.vin:
        existing = get_vehicle_by_vin(db, update_data["vin"])
        if existing:
            raise ValueError(f"Vehicle with VIN {update_data['vin']} already exists")
    
    for field, value in update_data.items():
        setattr(db_vehicle, field, value)
    
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle

def delete_vehicle(db: Session, vehicle_id: int):
    db_vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not db_vehicle:
        return False
    
    db.delete(db_vehicle)
    db.commit()
    return True

def get_brands(db: Session) -> List[str]:
    return [brand[0] for brand in db.query(models.Vehicle.brand).distinct().all()]

def get_models(db: Session, brand: Optional[str] = None) -> List[str]:
    query = db.query(models.Vehicle.model).distinct()
    if brand:
        query = query.filter(models.Vehicle.brand == brand)
    return [model[0] for model in query.all()]