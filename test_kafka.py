from kafka import KafkaProducer, KafkaConsumer
import json
import time
import uuid

def test_kafka():
    try:
        # Producer
        producer = KafkaProducer(
            bootstrap_servers=['192.168.0.12:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Mensaje único cada vez
        unique_message = {
            'message': f'Hello from Hypertube! {uuid.uuid4()}',
            'timestamp': time.time()
        }
        
        producer.send('test-topic', unique_message)
        print(f"✅ Mensaje enviado: {unique_message['message']}")
        
        # Consumer con grupo único
        consumer = KafkaConsumer(
            'test-topic',
            bootstrap_servers=['192.168.0.12:9092'],
            group_id=f'test-group-{uuid.uuid4()}',  # Grupo único
            auto_offset_reset='latest',  # Solo mensajes nuevos
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=5000
        )
        
        print("📡 Esperando mensajes...")
        for message in consumer:
            print(f"✅ Mensaje recibido: {message.value['message']}")
            break
            
    except Exception as e:
        print(f"❌ Error con Kafka: {e}")

if __name__ == "__main__":
    test_kafka()