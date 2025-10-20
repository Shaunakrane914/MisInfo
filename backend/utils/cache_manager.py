"""
Project Aegis - Cache Manager
Implements caching to reduce redundant AI API calls
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages caching of claim analysis results to avoid redundant API calls.
    Falls back to in-memory dict if Redis is not available.
    """
    
    def __init__(self, use_redis=False, redis_host='localhost', redis_port=6379):
        self.use_redis = use_redis
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        
        if use_redis:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("[CacheManager] Redis connection established")
            except ImportError:
                logger.warning("[CacheManager] Redis library not installed, using in-memory cache")
                self.use_redis = False
            except Exception as e:
                logger.warning(f"[CacheManager] Redis connection failed: {e}, using in-memory cache")
                self.use_redis = False
        else:
            logger.info("[CacheManager] Using in-memory cache")
    
    def generate_cache_key(self, claim_text: str, prefix: str = "claim") -> str:
        """Generate a unique cache key from claim text"""
        # Normalize text
        normalized = claim_text.lower().strip()
        # Generate hash
        claim_hash = hashlib.md5(normalized.encode()).hexdigest()
        return f"{prefix}:{claim_hash}"
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result"""
        try:
            if self.use_redis and self.redis_client:
                cached_data = self.redis_client.get(key)
                if cached_data:
                    logger.info(f"[CacheManager] Cache HIT for key: {key[:20]}...")
                    return json.loads(cached_data)
            else:
                if key in self.memory_cache:
                    logger.info(f"[CacheManager] Memory cache HIT for key: {key[:20]}...")
                    return self.memory_cache[key]
            
            logger.debug(f"[CacheManager] Cache MISS for key: {key[:20]}...")
            return None
        except Exception as e:
            logger.error(f"[CacheManager] Error retrieving from cache: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl_days: int = 30) -> bool:
        """Store result in cache"""
        try:
            if self.use_redis and self.redis_client:
                ttl_seconds = ttl_days * 24 * 60 * 60
                self.redis_client.setex(
                    key,
                    ttl_seconds,
                    json.dumps(value)
                )
                logger.info(f"[CacheManager] Cached result for key: {key[:20]}... (TTL: {ttl_days} days)")
            else:
                self.memory_cache[key] = value
                logger.info(f"[CacheManager] Stored in memory cache: {key[:20]}...")
            
            return True
        except Exception as e:
            logger.error(f"[CacheManager] Error storing in cache: {e}")
            return False
    
    def check_similar_claim(self, claim_text: str) -> Optional[Dict[str, Any]]:
        """
        Check if a similar claim has been analyzed before.
        Returns cached result if found.
        """
        cache_key = self.generate_cache_key(claim_text)
        return self.get(cache_key)
    
    def cache_claim_result(self, claim_text: str, result: Dict[str, Any], ttl_days: int = 30) -> bool:
        """Cache the analysis result for a claim"""
        cache_key = self.generate_cache_key(claim_text)
        return self.set(cache_key, result, ttl_days)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.use_redis and self.redis_client:
            try:
                info = self.redis_client.info('stats')
                return {
                    "type": "redis",
                    "total_keys": self.redis_client.dbsize(),
                    "hits": info.get('keyspace_hits', 0),
                    "misses": info.get('keyspace_misses', 0)
                }
            except Exception as e:
                logger.error(f"[CacheManager] Error getting Redis stats: {e}")
                return {"type": "redis", "error": str(e)}
        else:
            return {
                "type": "memory",
                "total_keys": len(self.memory_cache)
            }
    
    def clear_cache(self) -> bool:
        """Clear all cached data"""
        try:
            if self.use_redis and self.redis_client:
                self.redis_client.flushdb()
                logger.info("[CacheManager] Redis cache cleared")
            else:
                self.memory_cache.clear()
                logger.info("[CacheManager] Memory cache cleared")
            return True
        except Exception as e:
            logger.error(f"[CacheManager] Error clearing cache: {e}")
            return False


# Global cache instance
cache_manager = CacheManager(use_redis=False)  # Set to True if Redis is available


# Example usage
if __name__ == "__main__":
    # Test cache manager
    cache = CacheManager(use_redis=False)
    
    # Test caching
    test_claim = "Breaking: Major earthquake hits city center!"
    test_result = {
        "verdict": "False",
        "confidence": 0.95,
        "reasoning": "No seismic activity reported"
    }
    
    # Cache the result
    cache.cache_claim_result(test_claim, test_result)
    
    # Retrieve from cache
    cached = cache.check_similar_claim(test_claim)
    print(f"Cached result: {cached}")
    
    # Get stats
    stats = cache.get_cache_stats()
    print(f"Cache stats: {stats}")
