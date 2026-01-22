class MessageBroker:
    def publish_event(self, exchange, routing_key, event_data):
        print(f"[STUB] Event: {exchange}.{routing_key} - {event_data}")
    
    def subscribe_to_events(self, exchange, routing_keys, callback):
        print(f"[STUB] Subscribed to {exchange}: {routing_keys}")

message_broker = MessageBroker()