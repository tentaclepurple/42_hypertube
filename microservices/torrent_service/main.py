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
import asyncpg
import uuid

HOST = 'kafka'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TorrentDownloader:
    def __init__(self):
        self.session = lt.session()
        self.download_path = Path("/data/movies")
        self.download_path.mkdir(exist_ok=True)
        self.active_torrents = {}
        
        # Conexión a base de datos
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            logger.warning("DATABASE_URL no está configurada, no se actualizará la BD")
        
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
            logger.info("Kafka Producer inicializado")
        except Exception as e:
            logger.error(f"Error inicializando Kafka Producer: {e}")
            self.producer = None
    
    async def _update_download_record(self, movie_id: str, torrent_hash: str, status: str, progress: int = 0, file_path: str = None):
        """Actualizar registro de descarga en movie_downloads_42"""
        if not self.db_url:
            return
            
        try:
            conn = await asyncpg.connect(self.db_url, statement_cache_size=0)
            
            # Determinar si está descargado
            is_downloaded = (status == 'completed' and progress >= 100)
            
            # Insertar o actualizar registro de descarga
            await conn.execute(
                """
                INSERT INTO movie_downloads_42 (movie_id, hash_id, downloaded_lg, filepath_ds, update_dt)
                VALUES ($1::uuid, $2, $3, $4, NOW())
                ON CONFLICT (hash_id) DO UPDATE SET
                    downloaded_lg = $3,
                    filepath_ds = COALESCE($4, movie_downloads_42.filepath_ds),
                    update_dt = NOW()
                """,
                movie_id, torrent_hash, is_downloaded, file_path
            )
            
            logger.info(f"Descarga actualizada: {torrent_hash[:8]}... - {status} {progress}%")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error actualizando registro de descarga: {e}")
    
    async def _find_video_files(self, torrent_hash: str, movie_title: str = None) -> list:
        """Buscar archivos de video en el directorio de descarga"""
        video_files = []
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        
        try:
            # Buscar en todo el directorio de descarga
            for file_path in self.download_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                    # Filtrar archivos muy pequeños (muestras, trailers)
                    if file_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                        video_files.append(file_path)
                        
            # Estrategias de búsqueda en orden de prioridad
            if movie_title:
                # 1. Archivos que contienen palabras del título
                title_matches = []
                for file_path in video_files:
                    title_words = [word.lower() for word in movie_title.split() if len(word) > 3]
                    if any(word in file_path.name.lower() for word in title_words):
                        title_matches.append(file_path)
                
                if title_matches:
                    return title_matches
            
            # 2. Archivos en directorios que contienen el hash
            hash_matches = []
            for file_path in video_files:
                if torrent_hash[:8].lower() in str(file_path.parent).lower():
                    hash_matches.append(file_path)
            
            if hash_matches:
                return hash_matches
            
            # 3. Devolver todos los archivos encontrados
            return video_files
            
        except Exception as e:
            logger.error(f"Error buscando archivos de video: {e}")
            return []
    
    async def _update_file_path_in_db(self, movie_id: str, torrent_hash: str, file_path: str):
        """Actualizar el filepath en la base de datos"""
        try:
            await self._update_download_record(
                movie_id, 
                torrent_hash, 
                'downloading', 
                0,  # Progress será actualizado por el monitor
                str(file_path)
            )
            logger.info(f"Filepath actualizado en BD: {file_path}")
        except Exception as e:
            logger.error(f"Error actualizando filepath: {e}")
    
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
    
    def _send_progress_update(self, movie_id: str, torrent_hash: str, data: dict):
        """Envía actualización de progreso a Kafka Y actualiza BD"""
        # Enviar a Kafka
        if self.producer:
            try:
                message = {'movie_id': movie_id, 'torrent_hash': torrent_hash, **data}
                self.producer.send('download-progress', message)
                logger.debug(f"Progreso enviado a Kafka: {torrent_hash[:8]}... - {data.get('status', 'progress')}")
            except Exception as e:
                logger.error(f"Error enviando progreso a Kafka: {e}")
        
        # Actualizar base de datos de forma asíncrona
        asyncio.create_task(self._update_download_record(
            movie_id, 
            torrent_hash,
            data.get('status', 'downloading'), 
            data.get('progress', 0),
            data.get('file_path')
        ))
    
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
    
    def _extract_hash_from_magnet(self, magnet_link: str) -> str:
        """Extrae el hash de un magnet link"""
        hash_match = re.search(r'xt=urn:btih:([a-fA-F0-9]{40})', magnet_link)
        if hash_match:
            return hash_match.group(1).lower()
        return None
    
    async def start_download(self, movie_id: str, torrent_input: str, movie_title: str = None):
        """Iniciar descarga de torrent desde hash o magnet link"""
        logger.info(f"Iniciando descarga: {movie_id}")
        logger.info(f"Input: {torrent_input[:100]}{'...' if len(torrent_input) > 100 else ''}")
        
        try:
            # Detectar tipo de input
            input_type, processed_input = self._detect_input_type(torrent_input)
            
            # Obtener hash del torrent
            if input_type == 'hash':
                torrent_hash = processed_input
                magnet_link = self._hash_to_magnet(processed_input, movie_title)
            else:
                magnet_link = processed_input
                torrent_hash = self._extract_hash_from_magnet(magnet_link)
                if not torrent_hash:
                    raise ValueError("No se pudo extraer hash del magnet link")
            
            
            # Marcar como iniciando descarga en BD
            await self._update_download_record(movie_id, torrent_hash, 'downloading', 0)
            
            # Validar magnet link
            if not self._validate_magnet_link(magnet_link):
                error_msg = "Magnet link inválido después de procesar"
                logger.error(f"{error_msg}")
                self._send_progress_update(movie_id, torrent_hash, {
                    'status': 'error',
                    'error': error_msg,
                    'progress': 0,
                    'title': movie_title
                })
                return
            
            # Verificar si ya está siendo descargado (usar hash como clave)
            if torrent_hash in self.active_torrents:
                logger.warning(f"El torrent {torrent_hash[:8]}... ya se está descargando")
                return
            
            # Configurar parámetros de descarga
            add_torrent_params = {
                'save_path': str(self.download_path),
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                'url': magnet_link,
                'flags': lt.torrent_flags.sequential_download | lt.torrent_flags.auto_managed,
            }
            
            # Añadir torrent a la sesión
            try:
                handle = self.session.add_torrent(add_torrent_params)
                logger.info(f"Torrent añadido con magnet link directo")
            except Exception as e:
                logger.error(f"Error añadiendo torrent: {e}")
                self._send_progress_update(movie_id, torrent_hash, {
                    'status': 'error',
                    'error': f"Error añadiendo torrent: {str(e)}",
                    'progress': 0,
                    'title': movie_title
                })
                return
            
            # Configurar prioridades para streaming
            handle.set_sequential_download(True)
            
            # Guardar handle (usar hash como clave)
            self.active_torrents[torrent_hash] = {
                'handle': handle,
                'movie_id': movie_id,
                'start_time': time.time(),
                'last_progress': 0,
                'title': movie_title or movie_id,
                'last_update': 0,
                'file_detected': False,  # Nuevo campo para tracking
                'file_path': None
            }
            
            # Reportar inicio exitoso
            self._send_progress_update(movie_id, torrent_hash, {
                'status': 'downloading',
                'progress': 0,
                'message': 'Descarga iniciada exitosamente',
                'input_type': input_type,
                'title': movie_title
            })
            
            logger.info(f"Torrent añadido exitosamente: {torrent_hash[:8]}...")
            
        except ValueError as e:
            logger.error(f"Error de validación para {movie_id}: {e}")
            # Si no tenemos hash, usar movie_id como fallback
            self._send_progress_update(movie_id, movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0,
                'title': movie_title
            })
        except Exception as e:
            logger.error(f"Error añadiendo torrent {movie_id}: {e}")
            self._send_progress_update(movie_id, movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0,
                'title': movie_title
            })
    
    async def monitor_downloads(self):
        """Monitorear progreso de descargas"""
        logger.info("Iniciando monitor de descargas...")
        
        while True:
            try:
                current_time = time.time()
                
                for torrent_hash in list(self.active_torrents.keys()):
                    torrent_info = self.active_torrents[torrent_hash]
                    handle = torrent_info['handle']
                    movie_id = torrent_info['movie_id']
                    
                    if not handle.is_valid():
                        logger.warning(f"Handle inválido para {torrent_hash[:8]}..., removiendo...")
                        self.active_torrents.pop(torrent_hash, None)
                        continue
                    
                    status = handle.status()
                    progress = int(status.progress * 100)
                    
                    # Detectar archivo tan pronto como esté disponible
                    if not torrent_info['file_detected'] and progress > 0:
                        video_files = await self._find_video_files(torrent_hash, torrent_info['title'])
                        
                        if video_files:
                            # Seleccionar el archivo más grande (probablemente la película principal)
                            main_file = max(video_files, key=lambda f: f.stat().st_size)
                            torrent_info['file_detected'] = True
                            torrent_info['file_path'] = str(main_file)
                            
                            # Actualizar BD inmediatamente con el filepath
                            await self._update_file_path_in_db(movie_id, torrent_hash, str(main_file))
                            
                            logger.info(f"Archivo detectado para {torrent_hash[:8]}...: {main_file.name}")
                    
                    # Solo reportar cambios significativos
                    last_progress = torrent_info['last_progress']
                    time_since_last = current_time - torrent_info.get('last_update', 0)
                    
                    should_update = (
                        progress != last_progress and progress % 5 == 0 or
                        time_since_last > 30 or
                        status.is_seeding or
                        status.error or
                        not torrent_info['file_detected']  # Actualizar cuando detectemos archivo
                    )
                    
                    if should_update:
                        progress_data = {
                            'progress': progress,
                            'download_rate': status.download_rate,
                            'upload_rate': status.upload_rate,
                            'num_peers': status.num_peers,
                            'num_seeds': status.num_seeds,
                            'can_stream': progress > 5 and torrent_info['file_detected'],
                            'completed': status.is_seeding,
                            'total_size': status.total_wanted,
                            'downloaded': status.total_wanted_done,
                            'title': torrent_info.get('title', movie_id),
                            'file_path': torrent_info.get('file_path')  # Incluir filepath en progreso
                        }
                        
                        if status.error:
                            progress_data['status'] = 'error'
                            progress_data['error'] = status.error
                            logger.error(f"Error en descarga {torrent_hash[:8]}...: {status.error}")
                        elif status.is_seeding:
                            progress_data['status'] = 'completed'
                            logger.info(f"Descarga completada: {torrent_hash[:8]}...")
                            
                            # Escanear archivos descargados al completarse
                            await self._scan_downloaded_files(torrent_hash, torrent_info)
                            
                            self.active_torrents.pop(torrent_hash, None)
                        else:
                            progress_data['status'] = 'downloading'
                        
                        self._send_progress_update(movie_id, torrent_hash, progress_data)
                        
                        torrent_info['last_progress'] = progress
                        torrent_info['last_update'] = current_time
                        
                        if progress != last_progress:
                            logger.info(f"{torrent_hash[:8]}...: {progress}% "
                                      f"({status.download_rate/1024:.1f} KB/s, "
                                      f"{status.num_peers} peers)")
                
            except Exception as e:
                logger.error(f"Error en monitor de descargas: {e}")
            
            await asyncio.sleep(5)
    
    async def _scan_downloaded_files(self, torrent_hash: str, torrent_info: dict):
        """Escanear archivos descargados y actualizar BD con paths"""
        try:
            movie_id = torrent_info.get('movie_id')
            title = torrent_info.get('title', movie_id)
            
            # Buscar archivos de video y subtítulos
            video_files = []
            subtitle_files = []
            
            # Extensiones de video comunes
            video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
            subtitle_extensions = {'.srt', '.sub', '.vtt', '.ass', '.ssa'}
            
            # Escanear directorio de descarga
            for file_path in self.download_path.rglob("*"):
                if file_path.is_file():
                    file_ext = file_path.suffix.lower()
                    
                    if file_ext in video_extensions:
                        video_files.append(str(file_path))
                    elif file_ext in subtitle_extensions:
                        subtitle_files.append(str(file_path))
            
            if video_files:
                # Tomar el archivo de video más grande (probablemente la película principal)
                largest_video = max(video_files, key=lambda f: Path(f).stat().st_size)
                
                # Actualizar BD con información de archivos
                await self._update_download_record(
                    movie_id, 
                    torrent_hash, 
                    'completed', 
                    100, 
                    largest_video
                )
                
                logger.info(f"Archivos escaneados para {torrent_hash[:8]}...:")
                logger.info(f"   Video principal: {largest_video}")
                if subtitle_files:
                    logger.info(f"   Subtítulos encontrados: {len(subtitle_files)}")
                    
        except Exception as e:
            logger.error(f"Error escaneando archivos para {torrent_hash[:8]}...: {e}")


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
            logger.error("Mensaje inválido: falta movie_id o torrent_input")
            return False
        
        logger.info(f"Petición recibida: {movie_id} (usuario: {user_id})")
        if movie_title:
            logger.info(f"Título: {movie_title}")
        
        # Ejecutar la descarga de forma asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(downloader.start_download(movie_id, torrent_input, movie_title))
        loop.close()
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"Error procesando petición: {e}")
        return False

async def start_kafka_consumer(downloader):
    """Inicia el consumer de Kafka en un hilo separado"""
    import threading
    
    def kafka_consumer_thread():
        logger.info("Iniciando consumer de Kafka...")
        
        try:
            consumer = KafkaConsumer(
                'movie-download-requests',
                bootstrap_servers=[f'{HOST}:9092'],
                group_id='torrent-service',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            logger.info("Consumer de Kafka conectado y esperando mensajes...")
            
            for message in consumer:
                process_kafka_message(downloader, message)
                
        except Exception as e:
            logger.error(f"Error en consumer de Kafka: {e}")
    
    # Iniciar en hilo separado
    kafka_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
    kafka_thread.start()
    
    logger.info("Consumer de Kafka iniciado en hilo separado")

async def main():
    logger.info("Torrent Service iniciado (con movie_downloads_42)")
    logger.info(f"Directorio de descarga: /data/movies")
    
    try:
        downloader = TorrentDownloader()
        
        # Iniciar consumer de Kafka en hilo separado
        await start_kafka_consumer(downloader)
        
        # Iniciar monitor de descargas
        await downloader.monitor_downloads()
        
    except KeyboardInterrupt:
        logger.info("Torrent Service detenido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())