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
import threading
from queue import Queue

from app.subtitles_service import SubtitlesService

HOST = 'kafka'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TorrentDownloader:
    def __init__(self):
        self.session = lt.session()
        self.download_path = Path("/data/movies")
        self.download_path.mkdir(exist_ok=True)
        self.active_torrents = {}
        
        # Cola para mensajes de Kafka
        self.download_queue = Queue()
        
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            logger.warning("DATABASE_URL is not set. Download records will not be saved.")
        
        # Popular trackers
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
        
        # Configure libtorrent session
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
            logger.info("Kafka Producer started")
        except Exception as e:
            logger.error(f"Error initializing Kafka Producer: {e}")
            self.producer = None

    async def _get_movie_info_from_db(self, movie_id: str) -> dict:
        """Get movie information from database"""
        if not self.db_url:
            return {}
            
        try:
            conn = await asyncpg.connect(self.db_url, statement_cache_size=0)
            
            # Query movie information
            result = await conn.fetchrow(
                """
                SELECT imdb_id, title, year 
                FROM movies 
                WHERE id = $1::uuid
                """,
                movie_id
            )
            
            await conn.close()
            
            if result:
                return {
                    'imdb_id': result['imdb_id'],
                    'title': result['title'],
                    'year': result['year']
                }
            else:
                logger.warning(f"Movie not found in database: {movie_id}")
                return {}
                
        except Exception as e:
            logger.error(f"Error querying movie info: {e}")
            return {}

    def _get_torrent_download_directory(self, handle) -> Path:
        """Get the actual download directory created by the torrent"""
        if not handle.has_metadata():
            return None
            
        try:
            torrent_file = handle.get_torrent_info()
            torrent_name = torrent_file.name()
            
            # The torrent creates a subdirectory with its name
            torrent_directory = self.download_path / torrent_name
            return torrent_directory
            
        except Exception as e:
            logger.error(f"Error getting torrent directory: {e}")
            return None

    async def _download_movie_subtitles(self, movie_id: str, movie_title: str, torrent_directory: Path):
        """Download subtitles for the movie in the torrent's actual directory"""
        try:
            logger.info(f"SUBTITLES: Starting download for movie {movie_id}")
            logger.info(f"SUBTITLES: Target directory: {torrent_directory}")
            
            # Verify directory exists
            if not torrent_directory.exists():
                logger.error(f"SUBTITLES: Directory does not exist: {torrent_directory}")
                return {'spanish': False, 'english': False}
            
            # Get movie info from database
            movie_info = await self._get_movie_info_from_db(movie_id)
            
            imdb_id = movie_info.get('imdb_id')
            db_title = movie_info.get('title')
            logger.info(f"SUBTITLES: IMDB ID: {imdb_id}, DB TITLE: {db_title}")
            
            # Use database title if available, fallback to provided title
            title_to_use = db_title or movie_title
            
            logger.info(f"SUBTITLES: Downloading subtitles for: {title_to_use}")
            if imdb_id:
                logger.info(f"SUBTITLES: Using IMDB ID: {imdb_id}")
            else:
                logger.info("SUBTITLES: No IMDB ID found, using title search")
            
            # Initialize subtitles service
            subtitles_service = SubtitlesService()
            
            # Download subtitles to the torrent's actual directory
            results = await subtitles_service.download_subtitles_for_movie(
                movie_directory=torrent_directory,
                imdb_id=imdb_id,
                movie_title=title_to_use
            )
            
            # Log results
            if results.get('spanish'):
                logger.info("SUBTITLES: Spanish subtitles downloaded successfully")
            else:
                logger.warning("SUBTITLES: Failed to download Spanish subtitles")
                
            if results.get('english'):
                logger.info("SUBTITLES: English subtitles downloaded successfully")
            else:
                logger.warning("SUBTITLES: Failed to download English subtitles")
            
            return results
            
        except Exception as e:
            logger.error(f"SUBTITLES: Error downloading subtitles: {e}")
            return {'spanish': False, 'english': False}

    async def _check_download_status(self, torrent_hash: str) -> bool:
        """Check if download already exists (completed or in progress)"""
        if not self.db_url:
            return False
            
        # Check if already in active downloads
        if torrent_hash in self.active_torrents:
            logger.info(f"Download in progress: {torrent_hash[:8]}...")
            return True
            
        try:
            conn = await asyncpg.connect(self.db_url, statement_cache_size=0)
            
            result = await conn.fetchrow(
                """
                SELECT downloaded_lg FROM movie_downloads_42 
                WHERE hash_id = $1 AND downloaded_lg = true
                ORDER BY update_dt DESC
                LIMIT 1
                """,
                torrent_hash.lower()
            )
            
            await conn.close()
            
            if result:
                logger.info(f"Download already completed: {torrent_hash[:8]}...")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"ERROR checking download status: {e}")
            return False

    async def _mark_download_started(self, movie_id: str, torrent_hash: str):
        """Mark download as started immediately when request is accepted"""
        await self._update_download_record(movie_id, torrent_hash, 'downloading', 0)
        logger.info(f"Download marked as started: {torrent_hash[:8]}...")
    
    async def _update_download_record(self, movie_id: str, torrent_hash: str, status: str, progress: int = 0, file_path: str = None):
        """Update download record in movie_downloads_42"""
        if not self.db_url:
            return
            
        try:
            conn = await asyncpg.connect(self.db_url, statement_cache_size=0)
            
            # Check if download is considered complete
            is_downloaded = (status == 'completed' and progress >= 100)
            
            # Insert or update record
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

            logger.info(f"Download record updated: {torrent_hash[:8]}... - {status} {progress}%")

            await conn.close()
            
        except Exception as e:
            logger.error(f"Error updating download record: {e}")

    def _hash_to_magnet(self, torrent_hash: str, movie_title: str = None) -> str:
        """Convert a torrent hash to a magnet link"""
        clean_hash = torrent_hash.strip().lower()
        
        if not re.match(r'^[a-f0-9]{40}$', clean_hash):
            raise ValueError(f"Invalid hash: {torrent_hash}")

        magnet = f"magnet:?xt=urn:btih:{clean_hash}"
        
        if movie_title:
            clean_title = re.sub(r'[^\w\s-]', '', movie_title).strip()
            clean_title = re.sub(r'[-\s]+', '+', clean_title)
            magnet += f"&dn={clean_title}"
        
        for tracker in self.default_trackers:
            magnet += f"&tr={tracker}"
        
        return magnet
    
    def _detect_input_type(self, input_string: str) -> tuple[str, str]:
        """Detect if the input is a hash or a magnet link"""
        input_string = input_string.strip()
        
        if input_string.startswith('magnet:?'):
            return ('magnet', input_string)
        elif re.match(r'^[a-fA-F0-9]{40}$', input_string):
            return ('hash', input_string.lower())
        else:
            raise ValueError(f"Input not recognized as hash or magnet: {input_string[:50]}...")

    def _send_progress_update(self, movie_id: str, torrent_hash: str, data: dict):
        """Send progress update to Kafka and update DB"""
        # Send to Kafka
        if self.producer:
            try:
                message = {'movie_id': movie_id, 'torrent_hash': torrent_hash, **data}
                self.producer.send('download-progress', message)
                logger.debug(f"Progress sent to Kafka: {torrent_hash[:8]}... - {data.get('status', 'progress')}")
            except Exception as e:
                logger.error(f"Error sending progress to Kafka: {e}")

        # Update database asynchronously
        asyncio.create_task(self._update_download_record(
            movie_id, 
            torrent_hash,
            data.get('status', 'downloading'), 
            data.get('progress', 0),
            data.get('file_path')
        ))
    
    def _validate_magnet_link(self, magnet_link: str) -> bool:
        """Validate that the magnet link has the correct format"""
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
        """Extract the hash from a magnet link"""
        hash_match = re.search(r'xt=urn:btih:([a-fA-F0-9]{40})', magnet_link)
        if hash_match:
            return hash_match.group(1).lower()
        return None

    def _get_torrent_main_video_file(self, handle) -> str:
        """Get the main video file path from torrent metadata"""
        if not handle.has_metadata():
            return None
            
        try:
            torrent_file = handle.get_torrent_info()
            video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
            
            largest_file = None
            largest_size = 0
            
            for i in range(torrent_file.num_files()):
                file_info = torrent_file.file_at(i)
                
                if (Path(file_info.path).suffix.lower() in video_extensions and 
                    file_info.size > largest_size and 
                    file_info.size > 10 * 1024 * 1024):  # > 10MB
                    
                    largest_file = str(Path(self.download_path) / file_info.path)
                    largest_size = file_info.size
            
            return largest_file
            
        except Exception as e:
            logger.error(f"ERROR getting main video file: {e}")
            return None
    
    async def start_download(self, movie_id: str, torrent_input: str, movie_title: str = None):
        """Start torrent download from hash or magnet link"""
        logger.info(f"Starting download: {movie_id}")
        logger.info(f"Input: {torrent_input[:100]}{'...' if len(torrent_input) > 100 else ''}")
        
        try:
            # Detect input type
            input_type, processed_input = self._detect_input_type(torrent_input)

            # Get torrent hash
            if input_type == 'hash':
                torrent_hash = processed_input
                magnet_link = self._hash_to_magnet(processed_input, movie_title)
            else:
                magnet_link = processed_input
                torrent_hash = self._extract_hash_from_magnet(magnet_link)
                if not torrent_hash:
                    raise ValueError("Could not extract hash from magnet link")

            # Check if torrent is already downloaded or in progress
            if await self._check_download_status(torrent_hash):
                logger.info(f"Torrent {torrent_hash[:8]}... already exists or in progress")
                return

            # Mark download as started immediately
            await self._mark_download_started(movie_id, torrent_hash)

            # Validate magnet link
            if not self._validate_magnet_link(magnet_link):
                error_msg = "Invalid magnet link after processing"
                logger.error(f"{error_msg}")
                self._send_progress_update(movie_id, torrent_hash, {
                    'status': 'error',
                    'error': error_msg,
                    'progress': 0,
                    'title': movie_title
                })
                return

            # Configure download parameters - use base download path
            # LibTorrent will create subdirectory based on torrent name
            add_torrent_params = {
                'save_path': str(self.download_path),
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
                'url': magnet_link,
                'flags': lt.torrent_flags.sequential_download | lt.torrent_flags.auto_managed,
            }

            # Add torrent to session
            try:
                handle = self.session.add_torrent(add_torrent_params)
                logger.info(f"Torrent added with direct magnet link")
            except Exception as e:
                logger.error(f"Error adding torrent: {e}")
                self._send_progress_update(movie_id, torrent_hash, {
                    'status': 'error',
                    'error': f"Error adding torrent: {str(e)}",
                    'progress': 0,
                    'title': movie_title
                })
                return

            # Configure streaming priorities
            handle.set_sequential_download(True)

            # Save handle (use hash as key)
            self.active_torrents[torrent_hash] = {
                'handle': handle,
                'movie_id': movie_id,
                'start_time': time.time(),
                'last_progress': 0,
                'title': movie_title or movie_id,
                'last_update': 0,
                'file_detected': False,
                'file_path': None,
                'subtitles_downloaded': False,  # Track subtitle download status
                'torrent_directory': None,  # Will be set when metadata is available
            }

            # Report successful start
            self._send_progress_update(movie_id, torrent_hash, {
                'status': 'downloading',
                'progress': 0,
                'message': 'Download started successfully',
                'input_type': input_type,
                'title': movie_title
            })

            logger.info(f"Torrent added successfully: {torrent_hash[:8]}...")
            
        except ValueError as e:
            logger.error(f"Validation error for {movie_id}: {e}")
            # If no hash, use movie_id as fallback
            self._send_progress_update(movie_id, movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0,
                'title': movie_title
            })
        except Exception as e:
            logger.error(f"Error adding torrent {movie_id}: {e}")
            self._send_progress_update(movie_id, movie_id, {
                'status': 'error',
                'error': str(e),
                'progress': 0,
                'title': movie_title
            })
    
    async def process_download_queue(self):
        """Process downloads from queue in the main event loop"""
        logger.info("Starting download queue processor...")
        
        while True:
            try:
                if not self.download_queue.empty():
                    # Get message from queue
                    message_data = self.download_queue.get()
                    
                    movie_id = message_data.get('movie_id')
                    torrent_input = message_data.get('torrent_input')
                    movie_title = message_data.get('movie_title')
                    user_id = message_data.get('user_id', 'unknown')
                    
                    logger.info(f"Processing queued download: {movie_id} (user: {user_id})")
                    if movie_title:
                        logger.info(f"Title: {movie_title}")
                    
                    # Process download in main event loop
                    await self.start_download(movie_id, torrent_input, movie_title)
                    
                    self.download_queue.task_done()
                    
            except Exception as e:
                logger.error(f"Error processing download queue: {e}")
            
            # Small delay to prevent tight loop
            await asyncio.sleep(1)

    async def monitor_downloads(self):
        """Monitor download progress"""
        logger.info("Starting download monitor...")

        while True:
            try:
                current_time = time.time()
                
                for torrent_hash in list(self.active_torrents.keys()):
                    torrent_info = self.active_torrents[torrent_hash]
                    handle = torrent_info['handle']
                    movie_id = torrent_info['movie_id']
                    
                    if not handle.is_valid():
                        logger.warning(f"Invalid handle for {torrent_hash[:8]}..., removing...")
                        self.active_torrents.pop(torrent_hash, None)
                        continue
                    
                    status = handle.status()
                    progress = int(status.progress * 100)

                    # Detect torrent directory when metadata becomes available
                    if not torrent_info['torrent_directory'] and handle.has_metadata():
                        torrent_directory = self._get_torrent_download_directory(handle)
                        if torrent_directory:
                            torrent_info['torrent_directory'] = torrent_directory
                            logger.info(f"Torrent directory detected: {torrent_directory}")

                    # Download subtitles once directory is available and we haven't downloaded them yet
                    if (torrent_info['torrent_directory'] and 
                        not torrent_info['subtitles_downloaded'] and 
                        progress > 0):  # Some progress to ensure directory creation
                        
                        logger.info(f"SUBTITLES: Initiating subtitle download for {torrent_hash[:8]}...")
                        try:
                            await self._download_movie_subtitles(
                                movie_id, 
                                torrent_info['title'], 
                                torrent_info['torrent_directory']
                            )
                            torrent_info['subtitles_downloaded'] = True
                            logger.info(f"SUBTITLES: Subtitle download completed for {torrent_hash[:8]}...")
                        except Exception as e:
                            logger.error(f"SUBTITLES: Subtitle download failed for {torrent_hash[:8]}...: {e}")
                            torrent_info['subtitles_downloaded'] = True  # Mark as attempted to avoid retries

                    # Detect main video file from torrent metadata
                    if not torrent_info['file_detected'] and progress > 0:
                        main_file_path = self._get_torrent_main_video_file(handle)
                        
                        if main_file_path:
                            torrent_info['file_detected'] = True
                            torrent_info['file_path'] = main_file_path
                            
                            # Update DB with the specific file path from torrent metadata
                            await self._update_download_record(
                                movie_id, 
                                torrent_hash, 
                                'downloading', 
                                progress, 
                                main_file_path
                            )
                            
                            logger.info(f"File detected from torrent metadata {torrent_hash[:8]}...: {Path(main_file_path).name}")

                    # Only report significant changes
                    last_progress = torrent_info['last_progress']
                    time_since_last = current_time - torrent_info.get('last_update', 0)
                    
                    should_update = (
                        progress != last_progress and progress % 5 == 0 or
                        time_since_last > 30 or
                        status.is_seeding or
                        status.error or
                        not torrent_info['file_detected']
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
                            'file_path': torrent_info.get('file_path')
                        }
                        
                        if status.error:
                            progress_data['status'] = 'error'
                            progress_data['error'] = status.error
                            logger.error(f"Error downloading {torrent_hash[:8]}...: {status.error}")
                        elif status.is_seeding:
                            progress_data['status'] = 'completed'
                            logger.info(f"Download completed: {torrent_hash[:8]}...")

                            # Register completion in database using existing file path
                            await self._register_completed_download(torrent_hash, torrent_info)
                            
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
                logger.error(f"Error in monitor loop: {e}")
            
            await asyncio.sleep(5)
    
    async def _register_completed_download(self, torrent_hash: str, torrent_info: dict):
        """Register completed download in database using torrent metadata"""
        try:
            movie_id = torrent_info.get('movie_id')
            file_path = torrent_info.get('file_path')
            
            # If we have a detected file path, use it
            if file_path:
                await self._update_download_record(
                    movie_id, 
                    torrent_hash, 
                    'completed', 
                    100, 
                    file_path
                )
                
                logger.info(f"Download completed and registered: {torrent_hash[:8]}...")
                logger.info(f"   File: {Path(file_path).name}")
                
            else:
                # Fallback: try to get file from torrent metadata one more time
                handle = torrent_info.get('handle')
                main_file = self._get_torrent_main_video_file(handle)
                
                if main_file:
                    await self._update_download_record(
                        movie_id, 
                        torrent_hash, 
                        'completed', 
                        100, 
                        main_file
                    )
                    logger.info(f"Download completed with fallback detection: {torrent_hash[:8]}...")
                else:
                    # Mark as completed without file path
                    await self._update_download_record(
                        movie_id, 
                        torrent_hash, 
                        'completed', 
                        100
                    )
                    logger.info(f"Download completed (no video file detected): {torrent_hash[:8]}...")

        except Exception as e:
            logger.error(f"ERROR registering completed download for {torrent_hash[:8]}...: {e}")


def start_kafka_consumer(downloader):
    """Start the Kafka consumer in a separate thread"""
    logger.info("Starting Kafka consumer...")

    try:
        consumer = KafkaConsumer(
            'movie-download-requests',
            bootstrap_servers=[f'{HOST}:9092'],
            group_id='torrent-service',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )

        logger.info("Kafka consumer connected and waiting for messages...")

        for message in consumer:
            try:
                data = message.value
                movie_id = data.get('movie_id')

                # Support both 'magnet_link' and 'torrent_hash'
                torrent_input = data.get('magnet_link') or data.get('torrent_hash')
                
                movie_title = data.get('movie_title') or data.get('title')
                user_id = data.get('user_id', 'unknown')
                
                if not movie_id or not torrent_input:
                    logger.error("Invalid message: missing movie_id or torrent_input")
                    continue

                # Add to queue instead of processing directly
                message_data = {
                    'movie_id': movie_id,
                    'torrent_input': torrent_input,
                    'movie_title': movie_title,
                    'user_id': user_id
                }
                
                downloader.download_queue.put(message_data)
                logger.info(f"Message queued: {movie_id} (user: {user_id})")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")


async def main():
    logger.info("Torrent Service started (with movie_downloads)")
    logger.info(f"Download directory: /data/movies")

    try:
        downloader = TorrentDownloader()
        
        # Start Kafka consumer in separate thread
        kafka_thread = threading.Thread(target=start_kafka_consumer, args=(downloader,), daemon=True)
        kafka_thread.start()
        logger.info("Kafka consumer started in separate thread")
        
        # Start both the download queue processor and monitor concurrently
        await asyncio.gather(
            downloader.process_download_queue(),
            downloader.monitor_downloads()
        )
        
    except KeyboardInterrupt:
        logger.info("Torrent Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())