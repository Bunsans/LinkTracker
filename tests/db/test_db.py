import asyncio
import contextlib
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from testcontainers.postgres import PostgresContainer

from src.db.base import Base
from src.db.db_helper import DatabaseHelper
from src.exceptions.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    NotRegistratedChatError,
)
from src.repository.async_.link_repository_orm import LinkRepositoryORM
from src.schemas.schemas import AddLinkRequest, RemoveLinkRequest

LEN_BATCH = 2


@pytest_asyncio.fixture(scope="session")
def postgres_container() -> PostgresContainer:
    """Fixture providing PostgreSQL test container instance.

    Yields:
        Running PostgresContainer instance for testing

    """
    container = PostgresContainer("postgres:latest", dbname="link", driver="asyncpg")
    container.start()
    yield container
    with contextlib.suppress(Exception):
        container.stop()


@pytest_asyncio.fixture(scope="session")  # type: ignore
def db_url(postgres_container: PostgresContainer) -> str:  # type: ignore
    """Get database connection URL from test container.

    Returns:
        Connection string for test database

    """
    db_url_ = postgres_container.get_connection_url()
    logger.debug(f"DB URL: {db_url_}")
    return db_url_  # type: ignore


@pytest_asyncio.fixture(scope="session")  # type: ignore
def event_loop() -> asyncio.AbstractEventLoop:  # type: ignore
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")  # type: ignore
async def db_helper(  # type: ignore
    db_url: str,
    event_loop: asyncio.AbstractEventLoop,
) -> DatabaseHelper:  # type: ignore
    """Fixture providing initialized DatabaseHelper instance.

    Yields:
        Configured DatabaseHelper for testing

    """
    logger.info(event_loop)

    db_helper = DatabaseHelper(url=db_url)
    yield db_helper
    await db_helper.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_db(
    db_helper: DatabaseHelper,
    event_loop: asyncio.AbstractEventLoop,
) -> AsyncGenerator[Any, Any]:
    """Fixture for database schema initialization.

    Drops and recreates all database tables before tests
    """
    logger.info(event_loop)
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture(scope="function")  # type: ignore
async def session(db_helper: DatabaseHelper) -> AsyncSession:  # type: ignore
    """Fixture providing database session for individual tests.

    Yields:
        New AsyncSession for each test function

    """
    session = await anext(db_helper.session_getter())
    yield session


###################


@pytest.fixture
def repo() -> LinkRepositoryORM:
    """Fixture providing LinkRepositoryORM instance for testing."""
    return LinkRepositoryORM()


@pytest.mark.asyncio
async def test_register_chat(repo: LinkRepositoryORM, session: AsyncSession) -> None:
    """Test chat registration functionality.

    Verifies:
    - Successful chat registration
    - Duplicate registration prevention
    """
    curr_chat_id = 123
    await repo.register_chat(curr_chat_id, session)
    chat = await repo.is_chat_registrated(curr_chat_id, session)

    assert chat is not None
    assert chat.tg_chat_id == curr_chat_id

    with pytest.raises(EntityAlreadyExistsError):
        await repo.register_chat(curr_chat_id, session)


@pytest.mark.asyncio
async def test_add_and_get_links(repo: LinkRepositoryORM, session: AsyncSession) -> None:
    """Test link management workflow.

    Verifies:
    - Link addition functionality
    - Link update capability
    - Link retrieval correctness
    """
    curr_chat_id = 456
    await repo.register_chat(curr_chat_id, session)

    link_request = AddLinkRequest(
        link="https://stackoverflow.com/questions/123456",
        tags=["tag1", "tag2"],
        filters=["filter1"],
    )
    await repo.add_link(curr_chat_id, link_request, session)

    links = await repo.get_links(curr_chat_id, session)
    assert len(links) == 1
    assert links[0].link == "https://stackoverflow.com/questions/123456"
    assert links[0].tags == ["tag1", "tag2"]

    updated_request = AddLinkRequest(
        link="https://stackoverflow.com/questions/123456",
        tags=["new_tag"],
        filters=["new_filter"],
    )
    updated_link = await repo.add_link(curr_chat_id, updated_request, session)
    assert updated_link.tags == ["new_tag"]


@pytest.mark.asyncio
async def test_remove_link(repo: LinkRepositoryORM, session: AsyncSession) -> None:
    """Test link removal functionality.

    Verifies:
    - Successful link removal
    - Error handling for non-existent links
    """
    await repo.register_chat(789, session)
    link_request = AddLinkRequest(
        link="https://stackoverflow.com/questions/123456",
        tags=[],
        filters=[],
    )
    await repo.add_link(789, link_request, session)

    removed = await repo.remove_link(
        789,
        RemoveLinkRequest(link="https://stackoverflow.com/questions/123456"),
        session,
    )
    assert removed.link == "https://stackoverflow.com/questions/123456"

    with pytest.raises(LinkNotFoundError):
        await repo.remove_link(
            789,
            RemoveLinkRequest(link="https://stackoverflow.com/questions/123456"),
            session,
        )


@pytest.mark.asyncio
async def test_delete_chat(repo: LinkRepositoryORM, session: AsyncSession) -> None:
    """Test chat deletion functionality.

    Verifies:
    - Complete chat removal
    - Data consistency after deletion
    """
    await repo.register_chat(999, session)
    await repo.add_link(
        999,
        AddLinkRequest(link="https://stackoverflow.com/questions/123456", tags=[], filters=[]),
        session,
    )

    await repo.delete_chat(999, session)

    with pytest.raises(NotRegistratedChatError):
        await repo.get_links(999, session)


@pytest.mark.asyncio
async def test_batch_processing(repo: LinkRepositoryORM, session: AsyncSession) -> None:
    """Test batch processing of chat-link associations.

    Verifies:
    - Correct batch size handling
    - Proper data grouping by links
    """
    for i in range(1, 6):
        await repo.register_chat(i, session)
        await repo.add_link(
            i,
            AddLinkRequest(
                link=f"https://stackoverflow.com/questions/123456{i}",
                tags=[],
                filters=[],
            ),
            session,
        )

    batch_gen = repo.get_chat_id_group_by_link(session, batch_size=2)
    batches = [batch async for batch in batch_gen]

    assert len(batches) >= LEN_BATCH
    for batch in batches:
        assert len(batch) <= LEN_BATCH
