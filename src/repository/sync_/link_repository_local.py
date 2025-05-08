from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.exceptions import LinkNotFoundError, NotRegistratedChatError
from src.exceptions.exceptions import EntityAlreadyExistsError
from src.repository.link_repository_interfaces import LinkRepositoryInterface


class LinkRepositoryLocal(LinkRepositoryInterface):
    def __init__(self) -> None:
        self.chat_id_links_mapper: dict[int, list[LinkResponse]] = {}
        self.links_chat_id_mapper: dict[str, set[int]] = {}

    def _is_chat_registrated(self, tg_chat_id: int, session: AsyncSession | None = None) -> bool:
        if session:
            session = None
        return tg_chat_id in self.chat_id_links_mapper

    def is_chat_registrated(self, tg_chat_id: int, session: AsyncSession | None = None) -> bool:
        if session:
            session = None
        if self._is_chat_registrated(tg_chat_id):
            return True
        else:
            raise NotRegistratedChatError("Not registrated chat.")

    def get_links(
        self,
        tg_chat_id: int,
        session: AsyncSession | None = None,
    ) -> list[LinkResponse]:
        if session:
            session = None
        if not self.is_chat_registrated(tg_chat_id):
            raise NotRegistratedChatError("Not registrated chat.")
        return self.chat_id_links_mapper[tg_chat_id]

    def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: AsyncSession | None = None,
    ) -> LinkResponse:

        if session:
            session = None
        if not self.is_chat_registrated(tg_chat_id):
            raise NotRegistratedChatError("Not registrated chat.")

        logger.debug(f"Before: chat_id_links_mapper: {self.chat_id_links_mapper}")
        list_links = self.chat_id_links_mapper[tg_chat_id]
        link_response = LinkResponse(
            id=tg_chat_id,
            link=link_request.link,
            tags=link_request.tags,
            filters=link_request.filters,
        )
        for link_ in list_links:
            if link_response.link == link_.link:
                list_links.remove(link_)
        list_links.append(link_response)

        self.chat_id_links_mapper[tg_chat_id] = list_links
        if link_response.link not in self.links_chat_id_mapper:
            self.links_chat_id_mapper[link_response.link] = {tg_chat_id}
        else:
            self.links_chat_id_mapper[link_response.link].add(tg_chat_id)

        logger.debug(f"After: chat_id_links_mapper: {self.chat_id_links_mapper}")
        return link_response

    def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: AsyncSession | None = None,
    ) -> LinkResponse:
        if session:
            session = None
        if not self.is_chat_registrated(tg_chat_id):
            raise NotRegistratedChatError("Not registrated chat.")

        logger.debug(f"Before: chat_id_links_mapper: {self.chat_id_links_mapper}")
        if link_request.link in self.links_chat_id_mapper:
            self.links_chat_id_mapper[link_request.link].remove(tg_chat_id)
            if not self.links_chat_id_mapper[link_request.link]:
                del self.links_chat_id_mapper[link_request.link]

        list_links = self.chat_id_links_mapper[tg_chat_id]
        for link_ in list_links:
            if link_.link == link_request.link:
                list_links.remove(link_)
                logger.debug(f"After: chat_id_links_mapper: {self.chat_id_links_mapper}")
                return LinkResponse(
                    id=tg_chat_id,
                    link=link_request.link,
                    tags=link_.tags,
                    filters=link_.filters,
                )
        logger.debug(f"After: chat_id_links_mapper: {self.chat_id_links_mapper}")
        raise LinkNotFoundError("Link not found.")

    def register_chat(self, tg_chat_id: int, session: AsyncSession | None = None) -> None:
        if session:
            session = None
        if self._is_chat_registrated(tg_chat_id):
            raise EntityAlreadyExistsError(
                message="Chat already registered. While registering chat",
            )
        logger.debug(f"Before: chat_id_links_mapper: {self.chat_id_links_mapper}")
        self.chat_id_links_mapper[tg_chat_id] = []
        logger.debug(f"After: chat_id_links_mapper: {self.chat_id_links_mapper}")

    def delete_chat(self, tg_chat_id: int, session: AsyncSession | None = None) -> None:
        if session:
            session = None
        if not self.is_chat_registrated(tg_chat_id):
            raise NotRegistratedChatError(message="Not registrated chat. While deleting chat")
        logger.debug(f"Before: chat_id_links_mapper: {self.chat_id_links_mapper}")
        del self.chat_id_links_mapper[tg_chat_id]
        logger.debug(f"After: chat_id_links_mapper: {self.chat_id_links_mapper}")

    def get_chat_id_group_by_link(
        self,
        session: AsyncSession | None = None,
    ) -> dict[str, set[int]]:
        if session:
            session = None
        return self.links_chat_id_mapper
