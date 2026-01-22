from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import models
import schemas
from typing import Optional

def get_inventory_item(db: Session, item_id: int):
    return db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()

def get_inventory_item_by_vehicle(db: Session, vehicle_id: int):
    return db.query(models.InventoryItem).filter(models.InventoryItem.vehicle_id == vehicle_id).first()

def get_inventory_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.InventoryItem).offset(skip).limit(limit).all()

def create_inventory_item(db: Session, item: schemas.InventoryCreate):
    db_item = models.InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_inventory_item(db: Session, item_id: int, item: schemas.InventoryUpdate):
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if not db_item:
        return None
    
    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

def reserve_vehicle(db: Session, vehicle_id: int, quantity: int = 1) -> Optional[models.InventoryItem]:
    item = get_inventory_item_by_vehicle(db, vehicle_id)
    if not item:
        return None
    
    if item.available_quantity < quantity:
        return None
    
    item.available_quantity -= quantity
    item.reserved_quantity += quantity
    item.status = models.InventoryStatus.RESERVED
    
    db.commit()
    db.refresh(item)
    return item

def release_vehicle(db: Session, vehicle_id: int, quantity: int = 1) -> Optional[models.InventoryItem]:
    item = get_inventory_item_by_vehicle(db, vehicle_id)
    if not item:
        return None
    
    if item.reserved_quantity < quantity:
        return None
    
    item.reserved_quantity -= quantity
    item.available_quantity += quantity
    
    # Если все резервы сняты и есть доступные авто, меняем статус
    if item.reserved_quantity == 0 and item.available_quantity > 0:
        item.status = models.InventoryStatus.AVAILABLE
    
    db.commit()
    db.refresh(item)
    return item

def sell_vehicle(db: Session, vehicle_id: int, quantity: int = 1) -> Optional[models.InventoryItem]:
    item = get_inventory_item_by_vehicle(db, vehicle_id)
    if not item:
        return None
    
    # Сначала пытаемся списать из резерва, потом из доступных
    if item.reserved_quantity >= quantity:
        item.reserved_quantity -= quantity
    elif item.available_quantity >= quantity:
        item.available_quantity -= quantity
    else:
        return None  # Недостаточно авто
    
    item.sold_quantity += quantity
    item.status = models.InventoryStatus.SOLD if item.available_quantity == 0 and item.reserved_quantity == 0 else item.status
    
    db.commit()
    db.refresh(item)
    return item