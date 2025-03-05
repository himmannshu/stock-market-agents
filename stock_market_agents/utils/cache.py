import os
import json
import time
import hashlib
from typing import Any, Optional, Dict
import logging
from ..config.database import CACHE_SETTINGS

logger = logging.getLogger(__name__)

class Cache:
    """Simple file-based cache implementation"""
    
    def __init__(self, namespace: str):
        """Initialize the cache
        
        Args:
            namespace: Namespace for this cache instance
        """
        self.cache_dir = os.path.join(CACHE_SETTINGS["directory"], namespace)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key
        
        Args:
            key: Cache key
            
        Returns:
            Path to cache file
        """
        # Create a hash of the key to use as filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache has expired
            if cache_data["expiry"] < time.time():
                logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None
            
            return cache_data["value"]
            
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.error(f"Error reading cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, expiry: Optional[int] = None) -> None:
        """Set a value in the cache
        
        Args:
            key: Cache key
            value: Value to cache
            expiry: Optional custom expiry time in seconds
        """
        cache_path = self._get_cache_path(key)
        
        # Use default expiry if none provided
        if expiry is None:
            expiry = CACHE_SETTINGS["default_expiry"]
        
        try:
            # Try to serialize the value first to catch any JSON errors
            cache_data = {
                "value": value,
                "expiry": time.time() + expiry
            }
            json.dumps(cache_data)  # Test serialization
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
                
        except (TypeError, ValueError) as e:
            logger.error(f"Error caching value: {str(e)}")
            # Don't try to store string representation, just fail silently
            return None
    
    def delete(self, key: str) -> None:
        """Delete a value from the cache
        
        Args:
            key: Cache key to delete
        """
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
            except IOError as e:
                logger.error(f"Error deleting cache file: {str(e)}")
                pass
