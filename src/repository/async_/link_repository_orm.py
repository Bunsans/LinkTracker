from typing import Dict, List

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db.chat import Chat
from src.db.link import Link
from src.exceptions.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    NotRegistratedChatError,
)
from src.repository.link_repository_interfaces import AcyncLinkRepositoryInterface


class LinkRepositoryORM(AcyncLinkRepositoryInterface):
    async def _is_chat_registrated(self, tg_chat_id: int, session: AsyncSession) -> bool:
        result = await session.execute(select(Chat).where(Chat.chat_id == tg_chat_id))
        result = result.scalar()
        return result is not None

    async def get_links(self, tg_chat_id: int, session: AsyncSession) -> List[LinkResponse]:
        if not await self._is_chat_registrated(tg_chat_id, session=session):
            raise NotRegistratedChatError("Not registrated chat.")

        result = await session.execute(select(Link).where(Link.chat_id == tg_chat_id))
        links = result.scalars().all()
        return [
            LinkResponse(id=link_.id, link=link_.link, tags=link_.tags, filters=link_.filters)
            for link_ in links
        ]

    async def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        if not await self._is_chat_registrated(tg_chat_id, session=session):
            raise NotRegistratedChatError("Not registrated chat.")

        logger.debug(f"tg_chat_id: {tg_chat_id}, link_request: {link_request}")
        new_link = Link(chat_id=tg_chat_id, **link_request.model_dump())
        session.add(new_link)
        await session.commit()  # To get the link_id
        await session.refresh(new_link)  # To get the link_id
        return LinkResponse(
            id=new_link.id,
            link=new_link.link,
            tags=new_link.tags,
            filters=new_link.filters,
        )

    async def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        if not await self._is_chat_registrated(tg_chat_id, session=session):
            raise NotRegistratedChatError("Not registrated chat.")

        result = await session.execute(
            delete(Link)
            .where(Link.link == link_request.link, Link.chat_id == tg_chat_id)
            .returning(Link.id, Link.link, Link.tags, Link.filters)
        )

        logger.debug(f"result delete:{result}")
        deleted_link = result.first()
        await session.commit()

        logger.debug(f"deleted_link :{deleted_link}")
        if deleted_link:
            return LinkResponse(
                id=deleted_link.id,
                link=deleted_link.link,
                tags=deleted_link.tags,
                filters=deleted_link.filters,
            )
        raise LinkNotFoundError("Link not found.")

    async def register_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        if await self._is_chat_registrated(tg_chat_id, session=session):
            raise EntityAlreadyExistsError(
                message="Chat already registered. While registering chat",
            )
        new_chat = Chat(chat_id=tg_chat_id)
        session.add(new_chat)
        logger.debug(f"Chat {tg_chat_id} registered")
        await session.commit()  # To get the link_id

    async def delete_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        logger.debug(f"Try delete: {tg_chat_id}")
        if not await self._is_chat_registrated(tg_chat_id, session=session):
            raise NotRegistratedChatError(message="Not registrated chat. While deleting chat")
        await session.execute(delete(Chat).where(Chat.chat_id == tg_chat_id))
        await session.execute(delete(Link).where(Link.chat_id == tg_chat_id))
        await session.commit()

    async def get_chat_id_group_by_link(self, session: AsyncSession) -> Dict[str, set[int]]:
        result_db = await session.execute(
            select(Link.link, func.array_agg(Link.chat_id).label("chat_list")).group_by(Link.link)
        )
        result = dict()
        for row in result_db:
            result[row[0]] = set(row[1])
        return result
