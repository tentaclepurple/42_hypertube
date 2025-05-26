import asyncio
import logging
import json
import libtorrent as lt
from kafka import KafkaConsumer, KafkaProducer
from pathlib import Path
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TorrentDownloader:
    def __init__(self):
        self.session = lt.session()
        self.download_path = Path("/data/movies")
        self.download_path.mkdir(exist_ok=True)
        self.active_torrents = {}
        
        # Kafka
        self.producer = KafkaProducer(
            bootstrap_servers=['192.168.0.12:9092'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
    async def start_download(self, movie_id: str, magnet_link: str):
        """Iniciar descarga de torrent"""
        logger.info(f"🔥 Iniciando descarga: {movie_id}")
        
        try:
            # Configurar descarga
            params = {
                'save_path': str(self.download_path),
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }
            
            # Añadir torrent
            handle = self.session.add_torrent({
                'url': magnet_link,
                **params
            })
            
            # Configurar para streaming (descarga secuencial)
            handle.set_sequential_download(True)
            
            self.active_torrents[movie_id] = handle
            
            # Reportar que empezó
            self.producer.send('download-progress', {
                'movie_id': movie_id,
                'status': 'started',
                'progress': 0
            })
            
            logger.info(f"✅ Torrent añadido: {movie_id}")
            
        except Exception as e:
            logger.error(f"❌ Error añadiendo torrent: {e}")
    
    async def monitor_downloads(self):
        """Monitorear progreso de descargas"""
        while True:
            for movie_id, handle in self.active_torrents.items():
                status = handle.status()
                
                progress = int(status.progress * 100)
                
                # Reportar progreso
                self.producer.send('download-progress', {
                    'movie_id': movie_id,
                    'progress': progress,
                    'download_rate': status.download_rate,
                    'can_stream': progress > 5,  # Streameable con 5%
                    'completed': status.is_seeding
                })
                
                if progress % 10 == 0:  # Log cada 10%
                    logger.info(f"📊 {movie_id}: {progress}%")
            
            await asyncio.sleep(5)  # Check cada 5 segundos

async def listen_for_requests():
    """Escuchar peticiones de descarga vía Kafka"""
    consumer = KafkaConsumer(
        'movie-download-requests',
        bootstrap_servers=['192.168.0.12:9092'],
        group_id='torrent-service',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    downloader = TorrentDownloader()
    
    # Iniciar monitoreo en background
    asyncio.create_task(downloader.monitor_downloads())
    
    logger.info("🎧 Escuchando peticiones de descarga...")
    
    for message in consumer:
        try:
            data = message.value
            movie_id = data.get('movie_id')
            magnet_link = data.get('magnet_link')
            
            logger.info(f"📨 Petición recibida: {movie_id}")
            
            await downloader.start_download(movie_id, magnet_link)
            
        except Exception as e:
            logger.error(f"❌ Error procesando petición: {e}")

async def main():
    logger.info("🔥 Torrent Service iniciado")
    
    try:
        await listen_for_requests()
    except KeyboardInterrupt:
        logger.info("🛑 Torrent Service detenido")

if __name__ == "__main__":
    asyncio.run(main())