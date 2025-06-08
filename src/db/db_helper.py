"""Database helper module for managing async SQLAlchemy connections and sessions."""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.settings import db_settings


class DatabaseHelper:
    """Helper class for managing database connections and sessions asynchronously."""

    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """Initialize the DatabaseHelper with connection parameters.

        Args:
            url: Database connection URL.
            echo: Whether to echo SQL statements (for debugging).
            echo_pool: Whether to echo connection pool operations.
            pool_size: Number of connections to keep in the pool.
            max_overflow: Maximum number of connections beyond pool_size to allow.

        """
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """Close all connections in the connection pool."""
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        """Async generator that yields database sessions.

        Yields:
            AsyncSession: A new database session.

        """
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """Recommended context manager for session handling
        Provides proper cleanup and error handling.

        Yields:
            AsyncSession: A new database session.

        Raises:
            SQLAlchemyError: If any database error occurs during the session.

        """
        session: AsyncSession | None = None
        try:
            session = self.session_factory()
            yield session
            await session.commit()
        except SQLAlchemyError:
            if session:
                await session.rollback()
            raise
        finally:
            if session:
                await session.close()


# Global instance of DatabaseHelper configured with settings
db_helper = DatabaseHelper(
    url=str(db_settings.url),
    echo=db_settings.echo,
    echo_pool=db_settings.echo_pool,
    pool_size=db_settings.pool_size,
    max_overflow=db_settings.max_overflow,
)
