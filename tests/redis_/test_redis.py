import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from loguru import logger
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

from src.redis_.redis_services import RedisService


@pytest.fixture(scope="session")
def redis_container() -> DockerContainer:
    """Fixture for creating and managing a Redis test container."""
    container = DockerContainer("redis:7.0")
    container.with_exposed_ports(6379)

    try:
        container.start()
        wait_for_logs(container, "Ready to accept connections", timeout=10.0)

        logger.info(
            "Redis container started successfully",
            event="redis_container_started",
            host=container.get_container_host_ip(),
            port=container.get_exposed_port(6379),
        )

        yield container

    except Exception as e:
        logger.error(f"Failed to start Redis container: {e}")
        raise
    finally:
        try:
            container.stop()
            logger.info("Redis container stopped", event="redis_container_stopped")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error stopping Redis container: {e}")


@pytest_asyncio.fixture(scope="function")  # type: ignore
async def redis_service(redis_container: DockerContainer) -> AsyncGenerator[RedisService, None]:
    """Fixture providing a RedisService instance connected to test container."""
    redis_url = (
        f"redis://{redis_container.get_container_host_ip()}:"
        f"{redis_container.get_exposed_port(6379)}"
    )
    service = RedisService(redis_url=redis_url)

    # Clean Redis before each test
    await service.invalidate_cache(0)  # Clear all keys starting with 'list:'

    yield service

    # Cleanup connection
    await service.redis.aclose()


class TestRedisService:
    """Test suite for RedisService functionality."""

    @pytest.mark.asyncio
    async def test_get_cached_list_hit(self, redis_service: RedisService) -> None:
        """Test successful retrieval of cached data."""
        chat_id = 123
        test_data = "Список ссылок: https://example.com"

        await redis_service.cache_list(chat_id, test_data)
        result = await redis_service.get_cached_list(chat_id)

        assert result == test_data

    @pytest.mark.asyncio
    async def test_get_cached_list_miss(self, redis_service: RedisService) -> None:
        """Test cache miss returns None."""
        result = await redis_service.get_cached_list(456)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_list_success(self, redis_service: RedisService) -> None:
        """Test data is successfully cached and retrievable."""
        chat_id = 789
        test_data = "Список ссылок: https://example.com"

        cache_result = await redis_service.cache_list(chat_id, test_data)
        retrieval_result = await redis_service.get_cached_list(chat_id)

        assert cache_result is True
        assert retrieval_result == test_data

    @pytest.mark.asyncio
    async def test_cache_list_with_ttl(self, redis_service: RedisService) -> None:
        """Test cached data expires after TTL."""
        chat_id = 101112
        test_data = "Список ссылок: https://example.com"
        ttl = 1  # 1 second TTL

        await redis_service.cache_list(chat_id, test_data, ttl=ttl)

        # Verify data exists before TTL
        assert await redis_service.get_cached_list(chat_id) == test_data

        # Wait for TTL to expire
        await asyncio.sleep(ttl + 0.1)

        # Verify data is gone after TTL
        assert await redis_service.get_cached_list(chat_id) is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_success(self, redis_service: RedisService) -> None:
        """Test cache invalidation removes data."""
        chat_id = 131415
        test_data = "Список ссылок: https://example.com"

        await redis_service.cache_list(chat_id, test_data)
        invalidate_result = await redis_service.invalidate_cache(chat_id)

        assert invalidate_result is True
        assert await redis_service.get_cached_list(chat_id) is None

    @pytest.mark.asyncio
    async def test_invalidate_cache_non_existent(self, redis_service: RedisService) -> None:
        """Test invalidating non-existent key returns True."""
        assert await redis_service.invalidate_cache(161718) is True

    @pytest.mark.asyncio
    async def test_connection_errors(self) -> None:
        """Test service handles connection errors gracefully."""
        with patch("redis.asyncio.Redis") as mock_redis:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = ConnectionError
            mock_instance.set.side_effect = ConnectionError
            mock_instance.delete.side_effect = ConnectionError
            mock_redis.return_value = mock_instance

            service = RedisService(redis_url="redis://invalid:6379")
            test_data = "Список ссылок: https://example.com"

            # Verify all operations handle connection errors
            assert await service.get_cached_list(192021) is None
            assert await service.cache_list(192021, test_data) is False
            assert await service.invalidate_cache(192021) is False
