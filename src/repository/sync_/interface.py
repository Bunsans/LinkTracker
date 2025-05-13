from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.schemas import AddLinkRequest, LinkResponse, RemoveLinkRequest


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
