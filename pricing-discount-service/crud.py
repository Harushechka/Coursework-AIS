from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import models
import schemas
from typing import List, Optional
import json

def get_discount(db: Session, discount_id: int):
    return db.query(models.Discount).filter(models.Discount.id == discount_id).first()

def get_discount_by_code(db: Session, code: str):
    return db.query(models.Discount).filter(models.Discount.code == code).first()

def get_discounts(db: Session, active_only: bool = True, discount_type: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Discount)
    
    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            models.Discount.is_active == True,
            models.Discount.valid_from <= now,
            models.Discount.valid_to >= now
        )
    
    if discount_type:
        query = query.filter(models.Discount.discount_type == discount_type)
    
    return query.offset(skip).limit(limit).all()

def create_discount(db: Session, discount: schemas.DiscountCreate):
    # Проверяем уникальность кода
    existing = get_discount_by_code(db, discount.code)
    if existing:
        raise ValueError(f"Discount with code {discount.code} already exists")
    
    db_discount = models.Discount(**discount.model_dump())
    db.add(db_discount)
    db.commit()
    db.refresh(db_discount)
    return db_discount

def update_discount(db: Session, discount_id: int, discount: schemas.DiscountUpdate):
    db_discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not db_discount:
        return None
    
    update_data = discount.model_dump(exclude_unset=True)
    
    # Если обновляется код, проверяем уникальность
    if "code" in update_data and update_data["code"] != db_discount.code:
        existing = get_discount_by_code(db, update_data["code"])
        if existing:
            raise ValueError(f"Discount with code {update_data['code']} already exists")
    
    for field, value in update_data.items():
        setattr(db_discount, field, value)
    
    db.commit()
    db.refresh(db_discount)
    return db_discount

def delete_discount(db: Session, discount_id: int):
    db_discount = db.query(models.Discount).filter(models.Discount.id == discount_id).first()
    if not db_discount:
        return False
    
    db.delete(db_discount)
    db.commit()
    return True

def increment_discount_usage(db: Session, discount_code: str):
    discount = get_discount_by_code(db, discount_code)
    if discount:
        discount.used_count += 1
        db.commit()
        return True
    return False

def get_vehicle_price(db: Session, vehicle_id: int) -> Optional[float]:
    # В реальной системе здесь был бы запрос к vehicle-catalog-service
    # Для примера возвращаем фиктивную цену
    return 25000.0  # Базовая цена

def save_price_history(db: Session, vehicle_id: int, base_price: float, final_price: float, 
                       customer_id: Optional[int] = None, discount_code: Optional[str] = None,
                       applied_discounts: Optional[str] = None, order_id: Optional[int] = None):
    price_history = models.PriceHistory(
        vehicle_id=vehicle_id,
        base_price=base_price,
        final_price=final_price,
        customer_id=customer_id,
        discount_code=discount_code,
        applied_discounts=applied_discounts,
        order_id=order_id
    )
    db.add(price_history)
    db.commit()
    return price_history