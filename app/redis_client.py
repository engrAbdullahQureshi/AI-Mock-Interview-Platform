import redis.asyncio as redis
from typing import Optional
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages Redis connection for caching and rate limiting.
    
    WHY REDIS?
    1. Caching: Store frequently accessed data in memory (super fast)
    2. Rate Limiting: Track API usage per user
    3. Session Management: Store temporary data
    
    IMPORTANT: This is OPTIONAL
    - App works fine without Redis
    - If Redis unavailable, features gracefully degrade
    """
    
    client: Optional[redis.Redis] = None
    
    @classmethod
    async def connect_redis(cls):
        """
        Connect to Redis server.
        If connection fails, app continues without Redis.
        """
        try:
            cls.client = await redis.from_url(
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                encoding="utf-8",
                decode_responses=True  # Automatically decode bytes to strings
            )
            
            # Test connection
            await cls.client.ping()
            logger.info(f"Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            logger.warning("App will continue without caching and rate limiting")
            cls.client = None  # Set to None, so we know Redis is unavailable
    
    @classmethod
    async def close_redis(cls):
        """Close Redis connection"""
        if cls.client:
            await cls.client.close()
            logger.info("Redis connection closed")
    
    @classmethod
    async def get_client(cls) -> Optional[redis.Redis]:
        """Get Redis client instance (may be None if not connected)"""
        return cls.client
    
    # ========== CACHE OPERATIONS ==========
    
    @classmethod
    async def cache_set(cls, key: str, value: dict, expire: int = 3600):
        """
        Store data in cache with automatic expiration.
        
        EXAMPLE USE CASE:
        User uploads resume → Parse it (slow, 2 seconds)
        Next time user views resume → Get from cache (fast, 0.01 seconds)
        
        Args:
            key: Cache key (e.g., "resume:user123")
            value: Data to store (dictionary)
            expire: Seconds until auto-delete (default 1 hour)
        
        Returns:
            True if successful, False if Redis unavailable
        """
        if cls.client is None:
            return False  # Redis not available, skip caching
        
        try:
            # Convert dict to JSON string for storage
            await cls.client.setex(
                key,
                expire,
                json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    @classmethod
    async def cache_get(cls, key: str) -> Optional[dict]:
        """
        Retrieve data from cache.
        
        Returns:
            Cached data if found, None if not found or Redis unavailable
        """
        if cls.client is None:
            return None
        
        try:
            data = await cls.client.get(key)
            if data:
                return json.loads(data)  # Convert JSON string back to dict
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    @classmethod
    async def cache_delete(cls, key: str):
        """Delete specific cached data"""
        if cls.client is None:
            return False
        
        try:
            await cls.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    # ========== RATE LIMITING ==========
    
    @classmethod
    async def check_rate_limit(cls, identifier: str, limit: int, period: int) -> bool:
        """
        Check if request is within rate limit.
        
        HOW IT WORKS:
        1. First request from user → Set counter to 1, expires in 1 hour
        2. Second request → Increment counter to 2
        3. 101st request → Counter exceeds limit → Reject!
        4. After 1 hour → Counter expires → Resets to 0
        
        Args:
            identifier: User ID or IP address
            limit: Max requests allowed (e.g., 100)
            period: Time window in seconds (e.g., 3600 = 1 hour)
        
        Returns:
            True = Allow request
            False = Rate limit exceeded
        """
        if cls.client is None:
            return True  # If Redis unavailable, allow all requests
        
        try:
            key = f"rate_limit:{identifier}"
            current = await cls.client.get(key)
            
            if current is None:
                # First request - start counter
                await cls.client.setex(key, period, 1)
                return True  # Allow
            
            current_count = int(current)
            
            if current_count >= limit:
                return False  # Exceeded limit - block
            
            # Increment counter
            await cls.client.incr(key)
            return True  # Still within limit - allow
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # On error, allow request (fail-open approach)


# ========== FastAPI Dependency ==========
async def get_redis() -> Optional[redis.Redis]:
    """
    FastAPI dependency for Redis access.
    
    Usage in routes:
    @router.get("/data")
    async def get_data(redis: Redis = Depends(get_redis)):
        if redis:
            cached = await redis.get("key")
    """
    return await RedisManager.get_client()