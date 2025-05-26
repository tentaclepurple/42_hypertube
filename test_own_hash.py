#!/usr/bin/env python3
# simple_test.py

from kafka import KafkaProducer
import json
import time

def test_hash(hash_value, title="Mi Película"):
    """Prueba un hash específico"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=['192.168.0.12:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        movie_id = f"test-{int(time.time())}"
        
        message = {
            'movie_id': movie_id,
            'torrent_hash': hash_value,
            'movie_title': title,
            'user_id': 'test-user',
            'timestamp': time.time()
        }
        
        print(f"📤 Enviando: {title}")
        print(f"   Hash: {hash_value}")
        print(f"   Movie ID: {movie_id}")
        
        producer.send('movie-download-requests', message)
        producer.flush()
        producer.close()
        
        print(f"✅ Enviado! Ver logs: docker logs -f torrent_service")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # CAMBIA ESTOS VALORES:
    hash_to_test = "FA60DB6A27519692B0F030148DF0AA28FF8656FE"  # <-- Pon tu hash aquí
    movie_title = "Tu Película"    # <-- Pon el título aquí
    
    if hash_to_test == "TU_HASH_AQUI":
        print("❌ Edita el script y pon tu hash en 'hash_to_test'")
    else:
        test_hash(hash_to_test, movie_title)