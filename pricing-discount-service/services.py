from sqlalchemy.orm import Session
from datetime import datetime
import crud
from typing import List, Dict, Any, Tuple
import json

# Глобальная переменная для хранения примененных скидок в текущем запросе
_applied_discounts = []

def calculate_final_price(base_price: float, customer_id: Optional[int] = None,
                         payment_method: str = "cash", trade_in: Optional[float] = None,
                         discount_code: Optional[str] = None, db: Session = None) -> float:
    """
    Рассчитывает финальную цену с учетом всех факторов
    """
    global _applied_discounts
    _applied_discounts = []
    
    final_price = base_price
    
    # Применяем скидку по коду, если указан
    if discount_code and db:
        discount = crud.get_discount_by_code(db, discount_code)
        if discount and is_discount_valid(discount, customer_id, None, base_price):
            final_price = apply_discount(final_price, discount)
            _applied_discounts.append({
                "type": "discount_code",
                "code": discount.code,
                "value": discount.value,
                "discount_type": discount.discount_type
            })
            crud.increment_discount_usage(db, discount_code)
    
    # Скидка за способ оплаты
    payment_discount = get_payment_method_discount(payment_method)
    if payment_discount:
        final_price = final_price * (1 - payment_discount)
        _applied_discounts.append({
            "type": "payment_method",
            "method": payment_method,
            "percentage": payment_discount * 100
        })
    
    # Скидка для постоянных клиентов
    if customer_id and is_loyal_customer(customer_id):
        loyalty_discount = 0.05  # 5% для постоянных клиентов
        final_price = final_price * (1 - loyalty_discount)
        _applied_discounts.append({
            "type": "loyalty",
            "customer_id": customer_id,
            "percentage": loyalty_discount * 100
        })
    
    # Trade-in значение (вычитаем из цены)
    if trade_in and trade_in > 0:
        final_price = max(0, final_price - trade_in)
        _applied_discounts.append({
            "type": "trade_in",
            "value": trade_in
        })
    
    # Округляем до 2 знаков
    final_price = round(final_price, 2)
    
    # Сохраняем историю цен
    if db:
        crud.save_price_history(
            db=db,
            vehicle_id=0,  # В реальной системе нужно передавать vehicle_id
            base_price=base_price,
            final_price=final_price,
            customer_id=customer_id,
            discount_code=discount_code,
            applied_discounts=json.dumps(_applied_discounts)
        )
    
    return final_price

def apply_discount(price: float, discount) -> float:
    """Применяет скидку к цене"""
    if discount.discount_type == "percentage":
        discounted = price * (1 - discount.value / 100)
        if discount.max_discount_amount:
            max_discount = discount.max_discount_amount
            actual_discount = price - discounted
            if actual_discount > max_discount:
                discounted = price - max_discount
    elif discount.discount_type == "fixed_amount":
        discounted = max(0, price - discount.value)
    else:
        discounted = price
    
    return round(discounted, 2)

def get_payment_method_discount(payment_method: str) -> float:
    """Возвращает скидку в зависимости от способа оплаты"""
    discounts = {
        "cash": 0.03,      # 3% за наличные
        "credit_card": 0.0, # 0% за кредитную карту
        "financing": 0.01,  # 1% за финансирование
        "lease": 0.02      # 2% за лизинг
    }
    return discounts.get(payment_method, 0.0)

def is_loyal_customer(customer_id: int) -> bool:
    """Проверяет, является ли клиент постоянным"""
    # В реальной системе здесь был бы запрос к customer-service
    # Для примера считаем постоянными клиентов с четным ID
    return customer_id % 2 == 0

def is_discount_valid(discount, customer_id: Optional[int], vehicle_id: Optional[int], purchase_amount: float) -> bool:
    """Проверяет, действительна ли скидка"""
    now = datetime.utcnow()
    
    # Проверка срока действия
    if not (discount.valid_from <= now <= discount.valid_to):
        return False
    
    # Проверка активности
    if not discount.is_active:
        return False
    
    # Проверка лимита использования
    if discount.usage_limit and discount.used_count >= discount.usage_limit:
        return False
    
    # Проверка минимальной суммы покупки
    if purchase_amount < discount.min_purchase_amount:
        return False
    
    # Проверка применения к конкретным автомобилям
    if not discount.applies_to_all_vehicles and vehicle_id:
        try:
            vehicle_ids = json.loads(discount.vehicle_ids or "[]")
            if vehicle_id not in vehicle_ids:
                return False
        except:
            return False
    
    # Проверка группы клиентов
    if discount.customer_group != "all" and customer_id:
        # В реальной системе здесь была бы проверка группы клиента
        pass
    
    return True

def validate_discount(discount_code: str, customer_id: Optional[int], 
                     vehicle_id: Optional[int], db: Session) -> Tuple[bool, str]:
    """Валидирует скидочный код"""
    discount = crud.get_discount_by_code(db, discount_code)
    
    if not discount:
        return False, "Discount code not found"
    
    if not is_discount_valid(discount, customer_id, vehicle_id, 0):
        return False, "Discount is not valid or expired"
    
    return True, "Discount is valid"

def get_applied_discounts() -> List[Dict[str, Any]]:
    """Возвращает список примененных скидок"""
    return _applied_discounts