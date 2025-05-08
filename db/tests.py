import pytest

from src.db import db_helper
from src.repository.async_.link_repository_orm import LinkRepositoryORM
from src.repository.link_services import AsyncLinkService

from .db_test import TestBases

# from src.dependencies import test_link_service_with_db


@pytest.fixture(scope="session", autouse=True)
def test_db():
    # Этот блок будет выполнен перед запуском тестов
    test_base = TestBases(db_image_name="postgres:11.8")
    yield
    # Этот блок будет выполнен после окончания работы тестов
    test_base.db.stop()


@pytest.fixture(scope="session", autouse=True)
def test_link_service_with_db():
    link_repository = LinkRepositoryORM()
    return AsyncLinkService(link_repository)


@pytest.fixture(autouse=True)
async def session():
    return await anext(db_helper.session_getter())


@pytest.mark.asyncio
async def test_get_links(expected, test_db, session, test_link_service_with_db) -> None:
    result = await test_link_service_with_db.get_links(tg_chat_id=..., session=session)
    assert result == expected


@pytest.mark.asyncio
async def test_add_link(expected, test_db, session, test_link_service_with_db) -> None:
    result = await test_link_service_with_db.get_links(tg_chat_id=..., session=session)
    assert result == expected


@pytest.mark.asyncio
async def test_remove_link(expected, test_db, session, test_link_service_with_db) -> None:
    result = await test_link_service_with_db.remove_link(tg_chat_id=..., session=session)
    assert result == expected


@pytest.mark.asyncio
async def test_register_chat(expected, test_db, session, test_link_service_with_db) -> None:
    result = await test_link_service_with_db.register_chat(tg_chat_id=..., session=session)
    assert result == expected


@pytest.mark.asyncio
async def test_delete_chat(expected, test_db, session, test_link_service_with_db) -> None:
    result = await test_link_service_with_db.delete_chat(tg_chat_id=..., session=session)
    assert result == expected


@pytest.mark.asyncio
async def test_get_chat_id_group_by_link(
    expected, test_db, session, test_link_service_with_db
) -> None:
    result = await test_link_service_with_db.get_chat_id_group_by_link(
        tg_chat_id=...,
        session=session,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_is_chat_registrated(expected, test_db, session) -> None:
    result = await test_link_service_with_db.is_chat_registrated(tg_chat_id=..., session=session)
    assert result == expected
