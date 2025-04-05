from typing import Dict

from src.api.links.schemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest
from src.repository.link_repository import LinkRepositoryInterface


class LinkService:
    """For work with LinkRepositoryInterface."""

    def __init__(self, link_repository: LinkRepositoryInterface) -> None:
        self._link_repository = link_repository

    def get_links(self, tg_chat_id: int) -> ListLinksResponse:
        links = self._link_repository.get_links(tg_chat_id)
        return ListLinksResponse(links=links, size=len(links))

    def add_link(self, tg_chat_id: int, link_request: AddLinkRequest) -> LinkResponse:
        return self._link_repository.add_link(tg_chat_id, link_request)

    def remove_link(self, tg_chat_id: int, link_request: RemoveLinkRequest) -> LinkResponse:
        return self._link_repository.remove_link(tg_chat_id, link_request)

    def register_chat(self, tg_chat_id: int) -> None:
        self._link_repository.register_chat(tg_chat_id)

    def delete_chat(self, tg_chat_id: int) -> None:
        self._link_repository.delete_chat(tg_chat_id)

    def get_chat_id_group_by_link(self) -> Dict[str, set[int]]:
        return self._link_repository.get_chat_id_group_by_link()

    def is_chat_registrated(self, tg_chat_id: int) -> bool:
        return self._link_repository.is_chat_registrated(tg_chat_id)
