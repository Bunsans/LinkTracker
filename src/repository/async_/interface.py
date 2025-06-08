from collections.abc import AsyncGenerator
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.chat import Chat
from src.schemas.schemas import AddLinkRequest, LinkResponse, RemoveLinkRequest


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

    async def get_chat_id_group_by_link(  # type: ignore
        self,
        session: AsyncSession,
        batch_size: int = 100,
    ) -> AsyncGenerator[dict[str, list[int]], None]:  # type: ignore
        pass
