from typing import Dict, List, Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest


class LinkRepositoryInterface(Protocol):
    def get_links(
        self,
        tg_chat_id: int,
        session: Optional[AsyncSession] = None,
    ) -> List[LinkResponse]:
        pass

    def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        pass

    def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        pass

    def is_chat_registrated(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> bool:
        pass

    def register_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        pass

    def delete_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        pass

    def get_chat_id_group_by_link(
        self,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, set[int]]:
        pass


class AcyncLinkRepositoryInterface(Protocol):
    async def get_links(
        self,
        tg_chat_id: int,
        session: Optional[AsyncSession] = None,
    ) -> List[LinkResponse]:
        pass

    async def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        pass

    async def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: Optional[AsyncSession] = None,
    ) -> LinkResponse:
        pass

    async def _is_chat_registrated(
        self, tg_chat_id: int, session: Optional[AsyncSession] = None
    ) -> bool:
        pass

    async def register_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        pass

    async def delete_chat(self, tg_chat_id: int, session: Optional[AsyncSession] = None) -> None:
        pass

    async def get_chat_id_group_by_link(
        self,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, set[int]]:
        pass
