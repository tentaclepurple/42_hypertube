# hypertube/backend/app/services/kafka_service.py

import json
import logging
from kafka import KafkaProducer
from typing import Dict, Any
import time


HOST = 'kafka'

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.producer = None
        logger.info("KafkaService initialized")
    
    def _get_producer(self):
        """Conect to Kafka producer if not already connected"""
        if self.producer is None:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=[f'{HOST}:9092'],
                    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                    request_timeout_ms=5000,
                    retries=3
                )
                logger.info("Kafka Producer connected")
            except Exception as e:
                logger.error(f"Error connecting to Kafka: {e}")
                return None
        return self.producer
    
    def send_download_request(self, movie_id: str, magnet_link: str, user_id: str = None):
        """Send download request to torrent service"""
        producer = self._get_producer()
        if not producer:
            logger.error("Kafka Producer not available")
            return False
        
        try:
            message = {
                'movie_id': movie_id,
                'magnet_link': magnet_link,
                'user_id': user_id,
                'timestamp': time.time()
            }
            
            producer.send('movie-download-requests', message)
            producer.flush()  # Ensure sending

            logger.info(f"📤 Request sent: {movie_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending request: {e}")
            # Reset producer for retry
            self.producer = None
            return False
    
    def send_download_request_enhanced(self, download_data: dict):
        """Send download request with complete data"""
        producer = self._get_producer()
        if not producer:
            logger.error("Kafka Producer not available")
            return False
        
        try:
            logger.info(f"Sending download request: {download_data.get('movie_title')} ({download_data.get('torrent_hash', 'no-hash')[:8]}...)")

            producer.send('movie-download-requests', download_data)
            producer.flush()  # Ensure sending

            logger.info(f"Request sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending request: {e}")
            # Reset producer for retry
            self.producer = None
            return False

# Singleton
kafka_service = KafkaService()