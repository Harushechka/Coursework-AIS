import httpx
import os
from typing import Dict, Any

INVENTORY_SERVICE_URL = os.getenv("INVENTORY_SERVICE_URL", "http://localhost:8007")

async def reserve_vehicle(vehicle_id: int, order_id: int, quantity: int = 1) -> Dict[str, Any]:
    """
    Резервирует автомобиль через inventory-service
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "vehicle_id": vehicle_id,
                "order_id": order_id,
                "quantity": quantity
            }
            response = await client.post(
                f"{INVENTORY_SERVICE_URL}/inventory/reserve",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error reserving vehicle: {e}")
        raise Exception(f"Failed to reserve vehicle {vehicle_id}: {e}")

async def release_vehicle(vehicle_id: int, quantity: int = 1) -> Dict[str, Any]:
    """
    Освобождает резервирование автомобиля
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "vehicle_id": vehicle_id,
                "quantity": quantity
            }
            response = await client.post(
                f"{INVENTORY_SERVICE_URL}/inventory/release",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error releasing vehicle: {e}")
        return {"status": "error", "message": str(e)}

async def mark_as_sold(vehicle_id: int, order_id: int, quantity: int = 1) -> Dict[str, Any]:
    """
    Отмечает автомобиль как проданный
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "vehicle_id": vehicle_id,
                "order_id": order_id,
                "quantity": quantity
            }
            response = await client.post(
                f"{INVENTORY_SERVICE_URL}/inventory/sold",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error marking vehicle as sold: {e}")
        raise Exception(f"Failed to mark vehicle {vehicle_id} as sold: {e}")

async def check_availability(vehicle_id: int) -> Dict[str, Any]:
    """
    Проверяет наличие автомобиля
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{INVENTORY_SERVICE_URL}/inventory/{vehicle_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        print(f"Error checking availability: {e}")
        return {"available": False, "message": "Inventory service unavailable"}