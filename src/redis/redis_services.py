from typing import Optional
from redis.asyncio import Redis
from src.struct_logger import StructuredLogger

logger = StructuredLogger("redis_service")

class RedisService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Инициализация сервиса Redis.
        
        Args:
            redis_url: URL для подключения к Redis (включая пароль)
        """
        self.redis = Redis.from_url(
            url=redis_url,
            decode_responses=True,  # Автоматически декодировать ответы в строки
        )
        self.default_ttl = 300  # 5 минут по умолчанию

    async def get_cached_list(self, chat_id: int) -> Optional[str]:
        """Получение кэшированного списка для чата."""
        try:
            cached = await self.redis.get(f"list:{chat_id}")
            if cached:
                logger.info(
                    "Cache hit",
                    chat_id=chat_id
                )
                return cached
            logger.info(
                "Cache miss",
                chat_id=chat_id
            )
            return None
        except Exception as e:
            logger.error(
                "Failed to get cached list",
                error=str(e),
                chat_id=chat_id
            )
            return None

    async def cache_list(self, chat_id: int, items: str, ttl: int = None) -> bool:
        """
        Кэширование списка для чата.
        
        Args:
            chat_id: ID чата
            items: Строка для кэширования
            ttl: Опциональное время жизни кэша
        """
        try:
            await self.redis.set(
                f"list:{chat_id}",
                items,
                ex=ttl or self.default_ttl
            )
            logger.info(
                "List cached successfully",
                chat_id=chat_id
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to cache list",
                error=str(e),
                chat_id=chat_id
            )
            return False

    async def invalidate_cache(self, chat_id: int) -> bool:
        """
        Инвалидация кэша для чата.
        
        Args:
            chat_id: ID чата
        """
        try:
            await self.redis.delete(f"list:{chat_id}")
            logger.info(
                "Cache invalidated",
                chat_id=chat_id
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to invalidate cache",
                error=str(e),
                chat_id=chat_id
            )
            return False 