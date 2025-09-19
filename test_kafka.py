#!/usr/bin/env python3
# test_simple_hash.py

from kafka import KafkaProducer
import json
import time

def test_single_hash():
    """Prueba con un solo hash bien conocido"""
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Hash conocido de Big Buck Bunny
        test_hash = 'dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c'
        movie_id = f'debug-hash-test-{int(time.time())}'
        
        message = {
            'movie_id': movie_id,
            'torrent_hash': test_hash,
            'movie_title': 'Big Buck Bunny',
            'user_id': 'debug-user',
            'timestamp': time.time()
        }
        

        
        producer.send('movie-download-requests', message)
        producer.flush()
        producer.close()
        

        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_hash()