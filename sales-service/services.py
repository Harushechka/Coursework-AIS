from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from datetime import datetime
import models
import crud
import schemas
import messaging
from clients import pricing_client, inventory_client
import json
from typing import Dict, Any

async def create_order(db: Session, order_data: schemas.OrderCreate, background_tasks: BackgroundTasks) -> models.Order:
    """
    Создает новый заказ с интеграцией с другими сервисами
    """
    # 1. Проверяем наличие автомобиля
    availability = await inventory_client.check_availability(order_data.vehicle_id)
    if not availability.get("available", False):
        raise Exception(f"Vehicle {order_data.vehicle_id} is not available")
    
    # 2. Рассчитываем цену через pricing-service
    price_calculation = await pricing_client.calculate_price(
        vehicle_id=order_data.vehicle_id,
        customer_id=order_data.customer_id,
        payment_method=order_data.payment_method,
        discount_code=order_data.discount_code
    )
    
    # 3. Резервируем автомобиль
    # (резервирование отложим до подтверждения заказа)
    
    # 4. Создаем заказ в БД
    db_order = crud.create_order(db, order_data)
    
    # 5. Обновляем заказ с расчетными данными
    update_data = schemas.OrderUpdate(
        base_price=price_calculation["base_price"],
        final_price=price_calculation["final_price"],
        applied_discounts=json.dumps(price_calculation.get("applied_discounts", [])),
        vin=availability.get("vin", "UNKNOWN")  # Получаем VIN из inventory
    )
    
    db_order = crud.update_order(db, db_order.id, update_data)
    
    # 6. Публикуем событие создания заказа
    background_tasks.add_task(
        messaging.publish_order_event,
        event_type="OrderCreated",
        order_id=db_order.id,
        customer_id=db_order.customer_id,
        vehicle_id=db_order.vehicle_id,
        amount=db_order.final_price
    )
    
    return db_order

async def confirm_order(db: Session, order_id: int, background_tasks: BackgroundTasks) -> models.Order:
    """
    Подтверждает заказ
    """
    # 1. Получаем заказ
    order = crud.get_order(db, order_id)
    if not order:
        return None
    
    # 2. Резервируем автомобиль
    try:
        await inventory_client.reserve_vehicle(
            vehicle_id=order.vehicle_id,
            order_id=order.id
        )
    except Exception as e:
        raise Exception(f"Failed to reserve vehicle: {e}")
    
    # 3. Обновляем статус заказа
    order = crud.update_order_status(db, order_id, schemas.OrderStatus.CONFIRMED)
    
    # 4. Публикуем событие подтверждения заказа
    background_tasks.add_task(
        messaging.publish_order_event,
        event_type="OrderConfirmed",
        order_id=order.id,
        customer_id=order.customer_id,
        vehicle_id=order.vehicle_id,
        amount=order.final_price
    )
    
    return order

async def cancel_order(db: Session, order_id: int, background_tasks: BackgroundTasks) -> models.Order:
    """
    Отменяет заказ
    """
    # 1. Получаем заказ
    order = crud.get_order(db, order_id)
    if not order:
        return None
    
    # 2. Освобождаем резервирование автомобиля
    try:
        await inventory_client.release_vehicle(
            vehicle_id=order.vehicle_id
        )
    except Exception as e:
        print(f"Warning: Failed to release vehicle reservation: {e}")
    
    # 3. Обновляем статус заказа
    order = crud.update_order_status(db, order_id, schemas.OrderStatus.CANCELLED)
    
    # 4. Публикуем событие отмены заказа
    background_tasks.add_task(
        messaging.publish_order_event,
        event_type="OrderCancelled",
        order_id=order.id,
        customer_id=order.customer_id,
        vehicle_id=order.vehicle_id,
        amount=order.final_price
    )
    
    return order

async def complete_order(db: Session, order_id: int, background_tasks: BackgroundTasks) -> models.Order:
    """
    Завершает заказ (автомобиль продан)
    """
    # 1. Получаем заказ
    order = crud.get_order(db, order_id)
    if not order:
        return None
    
    # 2. Отмечаем автомобиль как проданный
    try:
        await inventory_client.mark_as_sold(
            vehicle_id=order.vehicle_id,
            order_id=order.id
        )
    except Exception as e:
        raise Exception(f"Failed to mark vehicle as sold: {e}")
    
    # 3. Обновляем статус заказа
    order = crud.update_order_status(db, order_id, schemas.OrderStatus.DELIVERED)
    
    # 4. Публикуем событие завершения заказа
    background_tasks.add_task(
        messaging.publish_order_event,
        event_type="OrderCompleted",
        order_id=order.id,
        customer_id=order.customer_id,
        vehicle_id=order.vehicle_id,
        amount=order.final_price
    )
    
    return order