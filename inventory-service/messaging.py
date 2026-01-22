import pika
import json
import os
from typing import Dict, Any

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

def publish_inventory_event(event_type: str, vehicle_id: int, order_id: int, quantity: int = 1):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Объявляем exchange для событий инвентаря
        channel.exchange_declare(exchange='inventory_events', exchange_type='topic', durable=True)
        
        event_data = {
            "event_type": event_type,
            "vehicle_id": vehicle_id,
            "order_id": order_id,
            "quantity": quantity,
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}})
        }
        
        channel.basic_publish(
            exchange='inventory_events',
            routing_key=f'inventory.{event_type.lower()}',
            body=json.dumps(event_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent message
            )
        )
        
        connection.close()
        print(f"Published {event_type} event for vehicle {vehicle_id}")
    except Exception as e:
        print(f"Failed to publish event: {e}")