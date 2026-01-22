import pika
import json
import os
from typing import Dict, Any

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

def publish_order_event(event_type: str, order_id: int, customer_id: int, 
                       vehicle_id: int, amount: float, **kwargs):
    """
    Публикует событие заказа в RabbitMQ
    """
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        
        # Объявляем exchange для событий заказов
        channel.exchange_declare(exchange='order_events', exchange_type='topic', durable=True)
        
        event_data = {
            "event_type": event_type,
            "order_id": order_id,
            "customer_id": customer_id,
            "vehicle_id": vehicle_id,
            "amount": amount,
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(__import__('time').time() * 1000))}}),
            **kwargs
        }
        
        channel.basic_publish(
            exchange='order_events',
            routing_key=f'order.{event_type.lower()}',
            body=json.dumps(event_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent message
                content_type='application/json'
            )
        )
        
        connection.close()
        print(f"Published {event_type} event for order {order_id}")
    except Exception as e:
        print(f"Failed to publish order event: {e}")