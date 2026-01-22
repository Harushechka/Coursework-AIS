import httpx
import os
from typing import Dict, Any, Optional

PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "http://localhost:8008")

async def calculate_price(vehicle_id: int, customer_id: Optional[int] = None, 
                         payment_method: str = "cash", discount_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Вызывает pricing-service для расчета цены
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "vehicle_id": vehicle_id,
                "customer_id": customer_id,
                "payment_method": payment_method,
                "discount_code": discount_code
            }
            response = await client.post(
                f"{PRICING_SERVICE_URL}/pricing/calculate",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error calling pricing service: {e}")
        # Возвращаем дефолтную цену в случае ошибки
        return {
            "base_price": 25000.0,
            "final_price": 25000.0,
            "applied_discounts": [],
            "currency": "USD"
        }

async def validate_discount(discount_code: str, customer_id: Optional[int] = None, 
                           vehicle_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Валидирует скидочный код через pricing-service
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "discount_code": discount_code,
                "customer_id": customer_id,
                "vehicle_id": vehicle_id
            }
            response = await client.post(
                f"{PRICING_SERVICE_URL}/discounts/validate",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error validating discount: {e}")
        return {"is_valid": False, "message": "Discount validation service unavailable"}