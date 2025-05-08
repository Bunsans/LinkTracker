import asyncio
from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.db import db_helper
from src.db.chat import Chat
from src.db.chat_link_association import ChatLinkAssociation
from src.db.link import Link
from src.exceptions.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    NotRegistratedChatError,
)
from src.repository.link_repository_interfaces import AcyncLinkRepositoryInterface


class LinkRepositoryORM(AcyncLinkRepositoryInterface):
    async def is_chat_registrated(
        self,
        tg_chat_id: int,
        session: AsyncSession,
    ) -> Chat | None:
        """SELECT chats.chat_id, chats.id
        FROM chats
        WHERE chats.chat_id = {}.
        """
        stmt = select(Chat).where(Chat.tg_chat_id == tg_chat_id)
        result = await session.execute(stmt)
        chat: Chat | None = result.scalar_one_or_none()
        return chat

    async def _find_link(self, link: str, session: AsyncSession) -> Link | None:
        stmt = select(Link).where(Link.link == link)
        result = await session.execute(stmt)
        link_: Link | None = result.scalar_one_or_none()
        return link_

    async def get_links(self, tg_chat_id: int, session: AsyncSession) -> list[LinkResponse]:
        chat = await self.is_chat_registrated(tg_chat_id, session=session)
        if chat is None:
            raise NotRegistratedChatError("Not registrated chat.")

        result = await session.execute(
            select(ChatLinkAssociation)
            .options(selectinload(ChatLinkAssociation.link))
            .where(ChatLinkAssociation.chat_id == chat.id),
        )
        association = result.scalars().all()
        return [
            LinkResponse(
                id=tg_chat_id,
                link=chat_link.link.link,
                tags=chat_link.tags,
                filters=chat_link.filters,
            )
            for chat_link in association
        ]

    async def add_link(
        self,
        tg_chat_id: int,
        link_request: AddLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        chat = await self.is_chat_registrated(tg_chat_id, session=session)
        if chat is None:
            raise NotRegistratedChatError("Not registrated chat.")

        link = await self._find_link(link_request.link, session=session)
        if link is None:
            link = Link(
                link=link_request.link,
            )
            session.add(link)
        else:
            link.count_chats += 1
        await session.commit()  # To get the link_id
        await session.refresh(link)  # To get the link_id

        logger.debug(f"tg_chat_id: {tg_chat_id}, link_request: {link_request}")
        new_link = ChatLinkAssociation(
            chat_id=chat.id,
            link_id=link.id,
            tags=link_request.tags,
            filters=link_request.filters,
        )
        session.add(new_link)
        await session.commit()  # To get the link_id
        await session.refresh(new_link)  # To get the link_id
        return LinkResponse(
            id=new_link.id,
            link=link.link,
            tags=new_link.tags,
            filters=new_link.filters,
        )

    async def remove_link(
        self,
        tg_chat_id: int,
        link_request: RemoveLinkRequest,
        session: AsyncSession,
    ) -> LinkResponse:
        chat = await self.is_chat_registrated(tg_chat_id, session=session)
        if chat is None:
            raise NotRegistratedChatError(message="Not registrated chat.")

        link = await self._find_link(link_request.link, session=session)
        if link is None:
            raise LinkNotFoundError(message="Link not found.")
        # Находим ассоциацию
        result = await session.execute(
            select(ChatLinkAssociation).where(
                and_(
                    ChatLinkAssociation.chat_id == chat.id,
                    ChatLinkAssociation.link_id == link.id,
                ),
            ),
        )
        chat_link_to_del = result.scalar_one_or_none()

        if not chat_link_to_del:
            raise LinkNotFoundError(message="Link not found.")

        await session.delete(chat_link_to_del)

        link.count_chats -= 1
        if link.count_chats == 0:
            await session.delete(link)

        await session.commit()

        return LinkResponse(
            id=link.id,
            link=link.link,
            tags=chat_link_to_del.tags,
            filters=chat_link_to_del.filters,
        )

    async def register_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        if await self.is_chat_registrated(tg_chat_id, session=session):
            raise EntityAlreadyExistsError(
                message="Chat already registered. While registering chat",
            )
        new_chat = Chat(tg_chat_id=tg_chat_id)
        session.add(new_chat)
        logger.debug(f"Chat {tg_chat_id} registered")
        await session.commit()  # To get the link_id

    async def delete_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        logger.debug(f"Try delete: {tg_chat_id}")
        chat = await self.is_chat_registrated(tg_chat_id, session=session)
        if chat is None:
            raise NotRegistratedChatError(message="Not registrated chat. While deleting chat")

        result = await session.execute(
            select(ChatLinkAssociation)
            .options(selectinload(ChatLinkAssociation.link))
            .where(ChatLinkAssociation.chat_id == chat.id),
        )
        chat_links = result.scalars().all()
        link_ids_to_del = []
        links_to_update = []
        chat_link_ids_to_del = []
        for chat_link in chat_links:
            chat_link_ids_to_del.append(chat_link.id)
            if chat_link.link.count_chats <= 1:
                link_ids_to_del.append(chat_link.link.id)
            else:
                chat_link.link.count_chats -= 1
                links_to_update.append(chat_link.link)
        await session.execute(
            delete(ChatLinkAssociation).where(ChatLinkAssociation.id.in_(chat_link_ids_to_del)),
        )

        if links_to_update:
            session.add_all(links_to_update)
        if link_ids_to_del:
            await session.execute(delete(Link).where(Link.id.in_(link_ids_to_del)))

        await session.execute(delete(Chat).where(Chat.id == chat.id))
        await session.commit()

    async def get_chat_id_group_by_link(
        self,
        session: AsyncSession,
        batch_size: int = 2,
    ) -> AsyncGenerator[dict[str, set[int]], None]:  # type: ignore
        last_id = 0
        while True:
            result = await session.execute(
                select(Link)
                .options(
                    selectinload(Link.chats_details).selectinload(
                        ChatLinkAssociation.chat,
                    ),  # Явное указание пути загрузки
                )
                .where(Link.id > last_id)
                .order_by(Link.id)
                .limit(batch_size),
            )

            links = result.scalars().all()
            if not links:
                break

            last_id = links[-1].id
            yield {
                link.link: {
                    assoc.chat.tg_chat_id
                    for assoc in link.chats_details
                    if assoc.chat  # Защита от возможных None
                }
                for link in links
            }


async def manual_test(session: AsyncSession) -> None:
    tg_chat_id = 1
    link_repository_orm = LinkRepositoryORM()

    await link_repository_orm.register_chat(tg_chat_id, session=session)


"""    for i in range(10):
        await link_repository_orm.add_link(
            tg_chat_id,
            AddLinkRequest(link=f"https://github.com/owner/repo", tags=[], filters=[]),
            session,
        )

    res = await link_repository_orm.remove_link(
        tg_chat_id,
        link_request=RemoveLinkRequest(link="https://github.com/owner/repo"),
        session=session,
    )
    logger.debug(res)
    res = await link_repository_orm.get_links(tg_chat_id, session)
    logger.debug(res)
    await link_repository_orm.delete_chat(
        tg_chat_id,
        session,
    )

    async for batch in link_repository_orm.get_chat_id_group_by_link(session, batch_size=2):
        for link, chat_ids in batch.items():
            logger.debug(f"Link: {link}")
            logger.debug(f"Chat IDs: {chat_ids}")

"""


async def main() -> None:
    async with db_helper.session_factory() as session:
        await manual_test(session)


if __name__ == "__main__":
    asyncio.run(main())
