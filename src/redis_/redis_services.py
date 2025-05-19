from typing import Optional

import redis
from loguru import logger


class RedisService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.asyncio.Redis.from_url(
            url=redis_url,
            decode_responses=True,
        )
        self.default_ttl = 300  # 5 minutes

    async def get_cached_list(self, chat_id: int) -> Optional[str]:
        try:
            cached = await self.redis.get(f"list:{chat_id}")
            if cached:
                logger.info("Cache founded")
                return cached
            logger.info("Cache not found")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached list\n{e}")
            return None

    async def cache_list(self, chat_id: int, items: str, ttl: int = None) -> bool:
        try:
            await self.redis.set(f"list:{chat_id}", items, ex=ttl or self.default_ttl)
            logger.info(f"List cached successfully: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache list\n{e}")
            return False

    async def invalidate_cache(self, chat_id: int) -> bool:
        try:
            await self.redis.delete(f"list:{chat_id}")
            logger.info(f"Cache invalidated {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate cache\n{e}")
            return False
