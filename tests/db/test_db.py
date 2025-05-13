import pytest
import pytest_asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
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


@pytest_asyncio.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15", driver="asyncpg") as container:
        container.start()
        yield container
        container.stop()


@pytest_asyncio.fixture(scope="session")
def db_url(postgres_container):
    db_url_ = postgres_container.get_connection_url()
    logger.debug(f"DB URL: {db_url_}")
    return db_url_


@pytest_asyncio.fixture(scope="session")
async def db_helper(db_url):
    db_helper = DatabaseHelper(url=db_url)
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield db_helper
    await db_helper.dispose()

    # engine = create_async_engine(db_url)
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)
    # yield engine
    # await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(db_helper):
    async with db_helper.session_factory() as session:
        async with session.begin():  # Явная транзакция
            yield session
        await session.close()  # Закрываем сессию

    # session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    # async with session_factory() as session:
    #     async with session.begin():
    #         yield session
    #         session.rollback()


###################


@pytest.fixture
def repo():
    return LinkRepositoryORM()


class TestLinkRepositoryORM:
    @pytest.mark.asyncio
    async def test_register_chat(self, repo, session):
        logger.debug(f"repo:{repo}, session:{session}")
        await repo.register_chat(123, session)
        chat = await repo.is_chat_registrated(123, session)

        assert chat is not None
        assert chat.tg_chat_id == 123

        with pytest.raises(EntityAlreadyExistsError):
            await repo.register_chat(123, session)

    @pytest.mark.asyncio
    async def test_add_and_get_links(self, repo, session):
        await repo.register_chat(456, session)

        link_request = AddLinkRequest(
            link="https://stackoverflow.com/questions/123456",
            tags=["tag1", "tag2"],
            filters=["filter1"],
        )
        added_link = await repo.add_link(456, link_request, session)

        links = await repo.get_links(456, session)
        assert len(links) == 1
        assert links[0].link == "https://stackoverflow.com/questions/123456"
        assert links[0].tags == ["tag1", "tag2"]

        updated_request = AddLinkRequest(
            link="https://stackoverflow.com/questions/123456",
            tags=["new_tag"],
            filters=["new_filter"],
        )
        updated_link = await repo.add_link(456, updated_request, session)
        assert updated_link.tags == ["new_tag"]

    @pytest.mark.asyncio
    async def test_remove_link(self, repo, session):
        await repo.register_chat(789, session)
        link_request = AddLinkRequest(
            link="https://stackoverflow.com/questions/123456", tags=[], filters=[]
        )
        added = await repo.add_link(789, link_request, session)

        removed = await repo.remove_link(
            789, RemoveLinkRequest(link="https://stackoverflow.com/questions/123456"), session
        )
        assert removed.link == "https://stackoverflow.com/questions/123456"

        with pytest.raises(LinkNotFoundError):
            await repo.remove_link(
                789, RemoveLinkRequest(link="https://stackoverflow.com/questions/123456"), session
            )

    @pytest.mark.asyncio
    async def test_delete_chat(self, repo, session):
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
    async def test_batch_processing(self, repo, session):
        for i in range(1, 6):
            await repo.register_chat(i, session)
            await repo.add_link(
                i,
                AddLinkRequest(
                    link=f"https://stackoverflow.com/questions/123456{i}.com", tags=[], filters=[]
                ),
                session,
            )

        batch_gen = repo.get_chat_id_group_by_link(session, batch_size=2)
        batches = [batch async for batch in batch_gen]

        assert len(batches) >= 2
        for batch in batches:
            assert len(batch) <= 2
