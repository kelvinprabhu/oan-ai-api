"""
Core cache instance configuration using Redis and aiocache.
Provides a resilient cache that falls back to memory if Redis is unavailable.
"""
import asyncio
import socket
from aiocache import Cache
from aiocache.serializers import JsonSerializer
from app.config import settings
from helpers.utils import get_logger

logger = get_logger(__name__)

def is_placeholder_host(host: str) -> bool:
    """Check if the hostname is a common placeholder or unconfigured value."""
    placeholders = [
        "localhost", 
        "127.0.0.1", 
        "azure_redis", 
        "redis", 
        "your-redis-name.redis.cache.windows.net"
    ]
    return not host or host.lower() in placeholders

class ResilientCache:
    """
    A wrapper for aiocache that handles connection failures by falling back to memory.
    """
    def __init__(self):
        self._redis = None
        self._memory = Cache(
            Cache.MEMORY,
            serializer=JsonSerializer(),
            ttl=settings.default_cache_ttl,
            key_builder=lambda key, namespace: f"{settings.redis_key_prefix}{namespace}:{key}" if namespace else f"{settings.redis_key_prefix}{key}",
        )
        self._use_fallback = False
        
        cache_type = getattr(settings, "cache_type", "redis").lower()
        
        # Immediate fallback if host is obviously a placeholder in production
        if settings.environment == "production" and cache_type == "redis" and is_placeholder_host(settings.redis_host):
            logger.warning(f"REDIS_HOST '{settings.redis_host}' appears to be a placeholder. Using Memory cache fallback.")
            self._use_fallback = True
        
        if cache_type == "redis" and not self._use_fallback:
            try:
                self._redis = Cache(
                    Cache.REDIS,
                    endpoint=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    serializer=JsonSerializer(),
                    ttl=settings.default_cache_ttl,
                    timeout=settings.redis_socket_timeout,
                    pool_max_size=settings.redis_max_connections,
                    key_builder=lambda key, namespace: f"{settings.redis_key_prefix}{namespace}:{key}" if namespace else f"{settings.redis_key_prefix}{key}",
                )
                logger.info(f"Redis cache initialized with host: {settings.redis_host}")
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache: {e}. Falling back to memory.")
                self._use_fallback = True
        else:
            self._use_fallback = True
            logger.info("Initializing with Memory cache.")

    @property
    def _active_cache(self):
        return self._memory if self._use_fallback else self._redis

    async def get(self, *args, **kwargs):
        if self._use_fallback:
            return await self._memory.get(*args, **kwargs)
        try:
            return await self._redis.get(*args, **kwargs)
        except (Exception, socket.gaierror) as e:
            logger.warning(f"Redis connection failed during GET: {e}. Switching to Memory cache fallback.")
            self._use_fallback = True
            return await self._memory.get(*args, **kwargs)

    async def set(self, *args, **kwargs):
        if self._use_fallback:
            return await self._memory.set(*args, **kwargs)
        try:
            return await self._redis.set(*args, **kwargs)
        except (Exception, socket.gaierror) as e:
            logger.warning(f"Redis connection failed during SET: {e}. Switching to Memory cache fallback.")
            self._use_fallback = True
            return await self._memory.set(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        if self._use_fallback:
            return await self._memory.delete(*args, **kwargs)
        try:
            return await self._redis.delete(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis connection failed during DELETE: {e}. Switching to Memory cache fallback.")
            self._use_fallback = True
            return await self._memory.delete(*args, **kwargs)

    async def exists(self, *args, **kwargs):
        if self._use_fallback:
            return await self._memory.exists(*args, **kwargs)
        try:
            return await self._redis.exists(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis connection failed during EXISTS: {e}. Switching to Memory cache fallback.")
            self._use_fallback = True
            return await self._memory.exists(*args, **kwargs)

    async def clear(self, *args, **kwargs):
        if self._use_fallback:
            return await self._memory.clear(*args, **kwargs)
        try:
            return await self._redis.clear(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Redis connection failed during CLEAR: {e}. Switching to Memory cache fallback.")
            self._use_fallback = True
            return await self._memory.clear(*args, **kwargs)

# Export the singleton instance
cache = ResilientCache()