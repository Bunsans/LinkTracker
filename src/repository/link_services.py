from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.shemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest
from src.repository.link_repository_interfaces import (
    AcyncLinkRepositoryInterface,
    LinkRepositoryInterface,
)


class LinkService:
    """For work with LinkRepositoryInterface."""

    def __init__(self, link_repository: LinkRepositoryInterface) -> None:
        self._link_repository = link_repository

    def get_links(
        self,
        tg_chat_id: int,
        session: Optional[AsyncSession] = None,
    ) -> ListLinksResponse:
        links = self._link_repository.get_links(tg_chat_id, session)
        return ListLinksResponse(links=links, size=len(links))

    def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        return self._link_repository.add_link(tg_chat_id, link_request, session)

    def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        return self._link_repository.remove_link(tg_chat_id, link_request, session)

    def register_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        self._link_repository.register_chat(tg_chat_id, session)

    def delete_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        self._link_repository.delete_chat(tg_chat_id, session)

    def get_chat_id_group_by_link(
        self,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, set[int]]:
        return self._link_repository.get_chat_id_group_by_link(session)

    def is_chat_registrated(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> bool:
        return self._link_repository.is_chat_registrated(tg_chat_id, session)


class AsyncLinkService:
    """For work with AsyncLinkRepositoryInterface."""

    def __init__(self, link_repository: AcyncLinkRepositoryInterface) -> None:
        self._link_repository = link_repository

    async def get_links(
        self,
        tg_chat_id: int,
        session: Optional[AsyncSession] = None,
    ) -> ListLinksResponse:
        links = await self._link_repository.get_links(tg_chat_id, session)
        return ListLinksResponse(links=links, size=len(links))

    async def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        return await self._link_repository.add_link(tg_chat_id, link_request, session)

    async def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        return await self._link_repository.remove_link(tg_chat_id, link_request, session)

    async def register_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        await self._link_repository.register_chat(tg_chat_id, session)

    async def delete_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        await self._link_repository.delete_chat(tg_chat_id, session)

    async def get_chat_id_group_by_link(
        self,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, set[int]]:
        return await self._link_repository.get_chat_id_group_by_link(session)

    async def is_chat_registrated(
        self, tg_chat_id: int, session: Optional[AsyncSession] = None
    ) -> bool:
        return await self._link_repository._is_chat_registrated(tg_chat_id, session)
