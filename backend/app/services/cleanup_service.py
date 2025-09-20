# backend/app/services/cleanup_service.py

import asyncio
import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.db.session import get_db_connection

logger = logging.getLogger(__name__)

class CleanupService:
    """Service to clean up old or excess movie files"""
    
    def __init__(self):
        self.max_movies = int(os.environ.get("CLEANUP_MAX_MOVIES", "51"))
        self.days_threshold = int(os.environ.get("CLEANUP_DAYS_THRESHOLD", "31"))
        self.download_path = Path("/data/movies")
        
    async def check_and_cleanup_if_needed(self) -> Dict[str, Any]:
        """
        Verify if cleanup is needed and perform it if so.
        Returns statistics about the cleanup operation.
        """
        try:
            
            print(f"Checking cleanup conditions... {self.download_path}, max: {self.max_movies}, days: {self.days_threshold}")
            current_count = await self._count_items_in_download_dir()
            
            needs_cleanup_by_count = current_count > self.max_movies
            
            old_movies = await self._get_movies_for_cleanup_by_days()
            needs_cleanup_by_days = len(old_movies) > 0
            
            stats = {
                "cleanup_executed": False,
                "current_count": current_count,
                "max_allowed": self.max_movies,
                "removed_by_count": 0,
                "removed_by_days": 0,
                "space_freed_mb": 0,
                "errors": []
            }
            
            if needs_cleanup_by_count or needs_cleanup_by_days:
                logger.info(f"Init cleaning - Items: {current_count}/{self.max_movies}, "
                           f"Old films: {len(old_movies)}")
                
                cleanup_result = await self._execute_cleanup(current_count, old_movies)
                stats.update(cleanup_result)
                stats["cleanup_executed"] = True
                
                logger.info(f"Cleaning completed: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in check_and_cleanup_if_needed: {e}")
            return {
                "cleanup_executed": False,
                "error": str(e),
                "current_count": 0,
                "max_allowed": self.max_movies
            }
    
    async def _count_items_in_download_dir(self) -> int:
        """Count non-hidden items in the download directory"""
        try:
            if not self.download_path.exists():
                return 0
            
            count = 0
            for item in self.download_path.iterdir():
                if not item.name.startswith('.'): 
                    count += 1
            
            return count
        except Exception as e:
            logger.error(f"Error counting items: {e}")
            return 0
    
    async def _get_movies_for_cleanup_by_days(self) -> List[Dict[str, Any]]:
        """Get movies not viewed in the last N days"""
        try:
            threshold_date = datetime.now() - timedelta(days=self.days_threshold)
            
            async with get_db_connection() as conn:

                query = """
                SELECT 
                    md.movie_id,
                    md.hash_id,
                    md.filepath_ds,
                    m.title,
                    MAX(umv.last_viewed_at) as last_viewed
                FROM movie_downloads md
                LEFT JOIN movies m ON md.movie_id = m.id
                LEFT JOIN user_movie_views umv ON md.movie_id = umv.movie_id
                WHERE md.downloaded_lg = true 
                  AND md.filepath_ds IS NOT NULL
                GROUP BY md.movie_id, md.hash_id, md.filepath_ds, m.title
                HAVING MAX(umv.last_viewed_at) IS NULL 
                    OR MAX(umv.last_viewed_at) < $1
                """
                
                results = await conn.fetch(query, threshold_date)
                
                movies_for_cleanup = []
                for row in results:
                    if row["filepath_ds"] and Path(row["filepath_ds"]).exists():
                        movies_for_cleanup.append({
                            "movie_id": str(row["movie_id"]),
                            "hash_id": row["hash_id"],
                            "filepath": row["filepath_ds"],
                            "title": row["title"] or "Unknown",
                            "last_viewed": row["last_viewed"]
                        })
                
                return movies_for_cleanup
                
        except Exception as e:
            logger.error(f"Error getting movies for cleanup: {e}")
            return []
    
    async def _execute_cleanup(self, current_count: int, old_movies: List[Dict]) -> Dict[str, Any]:
        """Execute cleanup based on count and days"""
        stats = {
            "removed_by_count": 0,
            "removed_by_days": 0,
            "space_freed_mb": 0,
            "errors": []
        }
        
        # 1. Cleanup by days
        for movie in old_movies:
            try:
                removed_size = await self._remove_movie_files(movie)
                if removed_size > 0:
                    await self._mark_as_not_downloaded(movie["movie_id"], movie["hash_id"])
                    stats["removed_by_days"] += 1
                    stats["space_freed_mb"] += removed_size
                    
                    days_ago = "never" if movie["last_viewed"] is None else (datetime.now() - movie["last_viewed"]).days
                    logger.info(f"Removed by days: {movie['title']} (last viewed: {days_ago} days) - {removed_size:.1f} MB")

            except Exception as e:
                error_msg = f"Error removing {movie['title']}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
        
        # 2. Cleanup by count if still needed
        updated_count = await self._count_items_in_download_dir()
        if updated_count > self.max_movies:
            items_to_remove = updated_count - self.max_movies
            removed_by_count = await self._cleanup_oldest_items(items_to_remove)
            stats["removed_by_count"] = len(removed_by_count)
            stats["space_freed_mb"] += sum(item.get("size_mb", 0) for item in removed_by_count)
        
        return stats
    
    async def _remove_movie_files(self, movie: Dict[str, Any]) -> float:
        """
        Delete movie files from disk
        """
        filepath = Path(movie["filepath"])
        
        if not filepath.exists():
            return 0
        
        try:
            if filepath.is_file():
                parent_dir = filepath.parent
                
                video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
                video_files = [f for f in parent_dir.iterdir() 
                             if f.is_file() and f.suffix.lower() in video_extensions]
                
                if len(video_files) <= 1 and parent_dir != self.download_path:
                    total_size = sum(f.stat().st_size for f in parent_dir.rglob('*') if f.is_file())
                    shutil.rmtree(parent_dir)
                    return total_size / (1024 * 1024)  # MB
                else:
                    file_size = filepath.stat().st_size
                    filepath.unlink()
                    return file_size / (1024 * 1024)  # MB
            
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
            return 0
    
    async def _cleanup_oldest_items(self, items_to_remove: int) -> List[Dict[str, Any]]:
        """Delete the oldest items by modification date"""
        try:
            # Get all items with their dates
            items = []
            for item_path in self.download_path.iterdir():
                if not item_path.name.startswith('.'):
                    items.append({
                        "path": item_path,
                        "name": item_path.name,
                        "modified_time": datetime.fromtimestamp(item_path.stat().st_mtime),
                        "size_mb": 0
                    })
            
            # Order by modification date
            items.sort(key=lambda x: x["modified_time"])

            # Delete the oldest items
            removed_items = []
            for item in items[:items_to_remove]:
                try:
                    size_mb = await self._calculate_item_size(item["path"])
                    
                    if item["path"].is_file():
                        item["path"].unlink()
                    elif item["path"].is_dir():
                        shutil.rmtree(item["path"])
                    
                    item["size_mb"] = size_mb
                    removed_items.append(item)
                    logger.info(f"Removed by count: {item['name']} - {size_mb:.1f} MB")
                    
                except Exception as e:
                    logger.error(f"Error deleting {item['name']}: {e}")
            
            return removed_items
            
        except Exception as e:
            logger.error(f"Error deleting oldest items: {e}")
            return []
    
    async def _calculate_item_size(self, path: Path) -> float:
        """Calculate file or directory size in MB"""
        try:
            if path.is_file():
                return path.stat().st_size / (1024 * 1024)
            elif path.is_dir():
                total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                return total_size / (1024 * 1024)
            return 0
        except Exception:
            return 0
    
    async def _mark_as_not_downloaded(self, movie_id: str, hash_id: str):
        """Mark movie as not downloaded in the DB"""
        try:
            async with get_db_connection() as conn:
                await conn.execute(
                    """
                    UPDATE movie_downloads 
                    SET downloaded_lg = false, filepath_ds = NULL, update_dt = NOW()
                    WHERE movie_id = $1::uuid AND hash_id = $2
                    """,
                    movie_id, hash_id
                )
                logger.debug(f"Marked as not downloaded: {hash_id[:8]}...")
        except Exception as e:
            logger.error(f"Error marking as not downloaded {hash_id}: {e}")

# Singleton instance of the service
cleanup_service = CleanupService()
