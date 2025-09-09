# microservices/torrent_service/main.py


import asyncio
import logging
import json
import libtorrent as lt
from kafka import KafkaConsumer, KafkaProducer
from pathlib import Path
import os
import re
import time


HOST = 'kafka'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TorrentDownloader:
    def __init__(self):
        self.session = lt.session()
        self.download_path = Path("/data/movies")
        self.download_path.mkdir(exist_ok=True)
        self.active_torrents = {}
        
        # Lista de trackers populares para construir magnet links
        self.default_trackers = [
            'udp://tracker.openbittorrent.com:80/announce',
            'udp://tracker.opentrackr.org:1337/announce',
            'udp://9.rarbg.to:2710/announce',
            'udp://9.rarbg.me:2710/announce',
            'udp://exodus.desync.com:6969/announce',
            'udp://tracker.cyberia.is:6969/announce',
            'udp://open.stealth.si:80/announce',
            'udp://tracker.tiny-vps.com:6969/announce',
            'udp://bt1.archive.org:6969/announce',
            'udp://bt2.archive.org:6969/announce'
        ]
        
        # Configurar sesión de libtorrent
        settings = {
            'user_agent': 'Hypertube/1.0',
            'listen_interfaces': '0.0.0.0:6881',
            'enable_dht': True,
            'enable_lsd': True,
            'enable_upnp': True,
            'enable_natpmp': True,
        }
        self.session.apply_settings(settings)
        
        # Kafka producer
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[f'{HOST}:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                retries=3,
                acks=1
            )
            logger.info("✅ Kafka Producer inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Kafka Producer: {e}")
            self.producer = None
    
    def _hash_to_magnet(self, torrent_hash: str, movie_title: str = None) -> str:
        """Convierte un hash de torrent a magnet link"""
        clean_hash = torrent_hash.strip().lower()
        
        if not re.match(r'^[a-f0-9]{40}$', clean_hash):
            raise ValueError(f"Hash inválido: {torrent_hash}")
        
        magnet = f"magnet:?xt=urn:btih:{clean_hash}"
        
        if movie_title:
            clean_title = re.sub(r'[^\w\s-]', '', movie_title).strip()
            clean_title = re.sub(r'[-\s]+', '+', clean_title)
            magnet += f"&dn={clean_title}"
        
        for tracker in self.default_trackers:
            magnet += f"&tr={tracker}"
        
        return magnet
    
    def _detect_input_type(self, input_string: str) -> tuple[str, str]:
        """Detecta si el input es un hash o un magnet link"""
        input_string = input_string.strip()
        
        if input_string.startswith('magnet:?'):
            return ('magnet', input_string)
        elif re.match(r'^[a-fA-F0-9]{40}$', input_string):
            return ('hash', input_string.lower())
        else:
            raise ValueError(f"Input no reconocido como hash o magnet: {input_string[:50]}...")
    
    def _send_progress_update(self, movie_id: str, data: dict):
        """Envía actualización de progreso a Kafka"""
        if not self.producer:
            logger.warning("⚠️ No hay producer de Kafka disponible")
            return
            
        try:
            message = {'movie_id': movie_id, **data}
            self.producer.send('download-progress', message)
            logger.debug(f"📤 Progreso enviado: {movie_id} - {data.get('status', 'progress')}")
        except Exception as e:
            logger.error(f"❌ Error enviando progreso: {e}")
    
    def _validate_magnet_link(self, magnet_link: str) -> bool:
        """Valida que el magnet link tenga el formato correcto"""
        if not magnet_link.startswith('magnet:?'):
            return False
            
        if 'xt=urn:btih:' not in magnet_link:
            return False
            
        try:
            hash_match = re.search(r'xt=urn:btih:([a-fA-F0-9]{40}|[a-zA-Z2-7]{32})', magnet_link)
            if not hash_match:
                return False
            
            hash_value = hash_match.group(1)
            if len(hash_value) not in [32, 40]:
                return False
                
            return True
        except Exception:
            return False
    
    async def start_download(self, movie_id: str, torrent_input: str, movie_title: str = None):
        """Iniciar descarga de torrent desde hash o magnet link"""
        logger.info(f"🔥 Iniciando descarga: {movie_id}")
        logger.info(f"📥 Input: {torrent_input[:100]}{'...' if len(torrent_input) > 100 else ''}")
        
        try:
            # Detectar tipo de input
            input_type, processed_input = self._detect_input_type(torrent_input)
            logger.info(f"🔍 Tipo detectado: {input_type}")
            
            # Convertir a magnet si es necesario
            if input_type == 'hash':
                magnet_link = self._hash_to_magnet(processed_input, movie_title)
                logger.info(f"🧲 Hash convertido a magnet: {magnet_link[:100]}...")
            else:
                magnet_link = processed_input
            
            # Validar magnet link
            if not self._validate_magnet_link(magnet_link):
                error_msg = "Magnet link inválido después de procesar"
                logger.error(f"❌ {error_msg}")
                self._send_progress_update(movie_id, {
                    'status': 'error',
                    'error': error_msg,
                    'progress': 0
                })
                return
            
            # Verificar si ya está siendo descargado
            if movie_id in self.active_torrents:
                logger.warning(f"⚠️ La película {movie_id} ya se está descargando")
                return
            
            # Configurar parámetros de descarga (método simplificado)
            add_torrent_params = {
                'save_path': str(self.download_path),
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                'url': magnet_link,  # Usar directamente la URL del magnet
                'flags': lt.torrent_flags.sequential_download | lt.torrent_flags.auto_managed,
            }
            
            # Añadir torrent a la sesión (método directo)
            try:
                handle = self.session.add_torrent(add_torrent_params)
                logger.info(f"✅ Torrent añadido con magnet link directo")
            except Exception as e:
                logger.error(f"❌ Error añadiendo torrent: {e}")
                self._send_progress_update(movie_id, {
                    'status': 'error',
                    'error': f"Error añadiendo torrent: {str(e)}",
                    'progress': 0
                })
                return
            
            # Configurar prioridades para streaming
            handle.set_sequential_download(True)
            
            # Guardar handle
            self.active_torrents[movie_id] = {
                'handle': handle,
                'start_time': time.time(),
                'last_progress': 0,
                'title': movie_title or movie_id,
                'last_update': 0
            }
            
            # Reportar inicio exitoso
            self._send_progress_update(movie_id, {
                'status': 'downloading',
                'progress': 0,
                'message': 'Descarga iniciada exitosamente',
                'input_type': input_type,
                'title': movie_title
            })
            
            logger.info(f"✅ Torrent añadido exitosamente: {movie_id}")
            
        except ValueError as e:
            logger.error(f"❌ Error de validación para {movie_id}: {e}")
            self._send_progress_update(movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0
            })
        except Exception as e:
            logger.error(f"❌ Error añadiendo torrent {movie_id}: {e}")
            self._send_progress_update(movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0
            })
    
    async def monitor_downloads(self):
        """Monitorear progreso de descargas"""
        logger.info("📊 Iniciando monitor de descargas...")
        
        while True:
            try:
                current_time = time.time()
                
                for movie_id in list(self.active_torrents.keys()):
                    torrent_info = self.active_torrents[movie_id]
                    handle = torrent_info['handle']
                    
                    if not handle.is_valid():
                        logger.warning(f"⚠️ Handle inválido para {movie_id}, removiendo...")
                        self.active_torrents.pop(movie_id, None)
                        continue
                    
                    status = handle.status()
                    progress = int(status.progress * 100)
                    
                    # Solo reportar cambios significativos
                    last_progress = torrent_info['last_progress']
                    time_since_last = current_time - torrent_info.get('last_update', 0)
                    
                    should_update = (
                        progress != last_progress and progress % 5 == 0 or
                        time_since_last > 30 or
                        status.is_seeding or
                        status.error
                    )
                    
                    if should_update:
                        progress_data = {
                            'progress': progress,
                            'download_rate': status.download_rate,
                            'upload_rate': status.upload_rate,
                            'num_peers': status.num_peers,
                            'num_seeds': status.num_seeds,
                            'can_stream': progress > 5,
                            'completed': status.is_seeding,
                            'total_size': status.total_wanted,
                            'downloaded': status.total_wanted_done,
                            'title': torrent_info.get('title', movie_id)
                        }
                        
                        if status.error:
                            progress_data['status'] = 'error'
                            progress_data['error'] = status.error
                            logger.error(f"❌ Error en descarga {movie_id}: {status.error}")
                        elif status.is_seeding:
                            progress_data['status'] = 'completed'
                            logger.info(f"✅ Descarga completada: {movie_id}")
                            self.active_torrents.pop(movie_id, None)
                        else:
                            progress_data['status'] = 'downloading'
                        
                        self._send_progress_update(movie_id, progress_data)
                        
                        torrent_info['last_progress'] = progress
                        torrent_info['last_update'] = current_time
                        
                        if progress != last_progress:
                            logger.info(f"📊 {movie_id}: {progress}% "
                                      f"({status.download_rate/1024:.1f} KB/s, "
                                      f"{status.num_peers} peers)")
                
            except Exception as e:
                logger.error(f"❌ Error en monitor de descargas: {e}")
            
            await asyncio.sleep(5)

# Función separada para manejar Kafka de forma síncrona
def process_kafka_message(downloader, message):
    """Procesa un mensaje de Kafka de forma síncrona"""
    try:
        data = message.value
        movie_id = data.get('movie_id')
        
        # Soportar tanto 'magnet_link' como 'torrent_hash'
        torrent_input = data.get('magnet_link') or data.get('torrent_hash')
        
        movie_title = data.get('movie_title') or data.get('title')
        user_id = data.get('user_id', 'unknown')
        
        if not movie_id or not torrent_input:
            logger.error("❌ Mensaje inválido: falta movie_id o torrent_input")
            return False
        
        logger.info(f"📨 Petición recibida: {movie_id} (usuario: {user_id})")
        if movie_title:
            logger.info(f"🎬 Título: {movie_title}")
        
        # Ejecutar la descarga de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(downloader.start_download(movie_id, torrent_input, movie_title))
        loop.close()
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error decodificando JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error procesando petición: {e}")
        return False

async def start_kafka_consumer(downloader):
    """Inicia el consumer de Kafka en un hilo separado"""
    import threading
    
    def kafka_consumer_thread():
        logger.info("🎧 Iniciando consumer de Kafka...")
        
        try:
            consumer = KafkaConsumer(
                'movie-download-requests',
                bootstrap_servers=['kafka:9092'],
                group_id='torrent-service',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            logger.info("✅ Consumer de Kafka conectado y esperando mensajes...")
            
            for message in consumer:
                process_kafka_message(downloader, message)
                
        except Exception as e:
            logger.error(f"❌ Error en consumer de Kafka: {e}")
    
    # Iniciar en hilo separado
    kafka_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    kafka_thread.start()
    
    logger.info("✅ Consumer de Kafka iniciado en hilo separado")

async def main():
    logger.info("🔥 Torrent Service iniciado (con soporte para hashes)")
    logger.info(f"📂 Directorio de descarga: /data/movies")
    
    try:
        downloader = TorrentDownloader()
        
        # Iniciar consumer de Kafka en hilo separado
        await start_kafka_consumer(downloader)
        
        # Iniciar monitor de descargas
        await downloader.monitor_downloads()
        
    except KeyboardInterrupt:
        logger.info("🛑 Torrent Service detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())