from sqlalchemy.orm import Session
from datetime import datetime
import models
import schemas
from typing import List, Optional

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_customer_orders(db: Session, customer_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Order).filter(
        models.Order.customer_id == customer_id
    ).offset(skip).limit(limit).all()

def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Создаем запись в истории
    add_order_history(
        db, 
        order_id=db_order.id,
        status=db_order.status,
        payment_status=db_order.payment_status,
        changed_by="system",
        notes="Order created"
    )
    
    return db_order

def update_order(db: Session, order_id: int, order: schemas.OrderUpdate):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        return None
    
    update_data = order.model_dump(exclude_unset=True)
    
    # Логируем изменения статуса
    if 'status' in update_data and update_data['status'] != db_order.status:
        add_order_history(
            db,
            order_id=order_id,
            status=update_data['status'],
            changed_by="system",
            notes=f"Status changed from {db_order.status} to {update_data['status']}"
        )
    
    # Логируем изменения статуса оплаты
    if 'payment_status' in update_data and update_data['payment_status'] != db_order.payment_status:
        add_order_history(
            db,
            order_id=order_id,
            status=db_order.status,
            payment_status=update_data['payment_status'],
            changed_by="system",
            notes=f"Payment status changed from {db_order.payment_status} to {update_data['payment_status']}"
        )
    
    # Обновляем временные метки при подтверждении/отмене
    if update_data.get('status') == models.OrderStatus.CONFIRMED:
        db_order.confirmed_at = datetime.utcnow()
    elif update_data.get('status') == models.OrderStatus.CANCELLED:
        db_order.cancelled_at = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: schemas.OrderStatus):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        return None
    
    # Логируем изменение статуса
    add_order_history(
        db,
        order_id=order_id,
        status=status,
        changed_by="system",
        notes=f"Status changed from {db_order.status} to {status}"
    )
    
    # Обновляем временные метки
    if status == models.OrderStatus.CONFIRMED:
        db_order.confirmed_at = datetime.utcnow()
    elif status == models.OrderStatus.CANCELLED:
        db_order.cancelled_at = datetime.utcnow()
    
    db_order.status = status
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order

def update_payment_status(db: Session, order_id: int, payment_status: schemas.PaymentStatus):
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        return None
    
    # Логируем изменение статуса оплаты
    add_order_history(
        db,
        order_id=order_id,
        status=db_order.status,
        payment_status=payment_status,
        changed_by="system",
        notes=f"Payment status changed from {db_order.payment_status} to {payment_status}"
    )
    
    db_order.payment_status = payment_status
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order

def add_order_history(db: Session, order_id: int, status: schemas.OrderStatus, 
                     changed_by: str = "system", notes: str = None,
                     payment_status: Optional[schemas.PaymentStatus] = None):
    history = models.OrderHistory(
        order_id=order_id,
        status=status,
        payment_status=payment_status,
        changed_by=changed_by,
        notes=notes
    )
    db.add(history)
    db.commit()
    return history

def get_order_history(db: Session, order_id: int):
    return db.query(models.OrderHistory).filter(
        models.OrderHistory.order_id == order_id
    ).order_by(models.OrderHistory.created_at.desc()).all()