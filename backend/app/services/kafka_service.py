# hypertube/backend/app/services/kafka_service.py

import json
import logging
from kafka import KafkaProducer
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.producer = None
        # No intentar conectar inmediatamente
        logger.info("🔄 Kafka Service inicializado (conexión lazy)")
    
    def _get_producer(self):
        """Conectar a Kafka solo cuando se necesite"""
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=['192.168.0.12:9092'],
                    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                    request_timeout_ms=5000,
                    retries=3
                )
                logger.info("✅ Kafka Producer conectado")
            except Exception as e:
                logger.error(f"❌ Error conectando Kafka: {e}")
                return None
        return self.producer
    
    def send_download_request(self, movie_id: str, magnet_link: str, user_id: str = None):
        """Enviar petición de descarga al torrent service"""
        producer = self._get_producer()
        if not producer:
            logger.error("❌ Kafka Producer no disponible")
            return False
        
        try:
            message = {
                'movie_id': movie_id,
                'magnet_link': magnet_link,
                'user_id': user_id,
                'timestamp': time.time()
            }
            
            producer.send('movie-download-requests', message)
            producer.flush()  # Asegurar envío
            
            logger.info(f"📤 Petición enviada: {movie_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando petición: {e}")
            # Reset producer para reintento
            self.producer = None
            return False

# Singleton
kafka_service = KafkaService()