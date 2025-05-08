from collections.abc import AsyncGenerator
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.chat import Chat


class LinkRepositoryInterface(Protocol):
    def get_links(
        self,
        tg_chat_id: int,
        session: AsyncSession | None = None,
    ) -> list[LinkResponse]:
        pass

    def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: AsyncSession | None = None,
    ) -> LinkResponse:
        pass

    def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: AsyncSession | None = None,
    ) -> LinkResponse:
        pass

    def is_chat_registrated(self, tg_chat_id: int, session: AsyncSession | None = None) -> bool:
        pass

    def register_chat(self, tg_chat_id: int, session: AsyncSession | None = None) -> None:
        pass

    def delete_chat(self, tg_chat_id: int, session: AsyncSession | None = None) -> None:
        pass

    def get_chat_id_group_by_link(
        self,
        session: AsyncSession | None = None,
    ) -> dict[str, set[int]]:
        pass


class AcyncLinkRepositoryInterface(Protocol):
    async def get_links(self, tg_chat_id: int, session: AsyncSession) -> list[LinkResponse]:
        pass

    async def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        pass

    async def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        pass

    async def is_chat_registrated(self, tg_chat_id: int, session: AsyncSession) -> Chat | None:
        pass

    async def register_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        pass

    async def delete_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        pass

    async def get_chat_id_group_by_link(
        self,
        session: AsyncSession,
        batch_size: int = 100,
    ) -> AsyncGenerator[dict[str, set[int]], None]:  # type: ignore
        pass
