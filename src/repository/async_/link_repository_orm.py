import asyncio
from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db import db_helper
from src.db.chat import Chat
from src.db.chat_link_association import ChatLinkAssociation
from src.db.link import Link
from src.exceptions.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    NotRegistratedChatError,
)
from src.repository.async_.interface import AcyncLinkRepositoryInterface
from src.schemas.schemas import AddLinkRequest, LinkResponse, RemoveLinkRequest


class LinkRepositoryORM(AcyncLinkRepositoryInterface):
    async def is_chat_registrated(
        self,
        tg_chat_id: int,
        session: AsyncSession,
    ) -> Chat | None:
        """Check if a chat is registered in the system.

        Args:
            tg_chat_id: Telegram chat ID to check
            session: Async database session

        Returns:
            Chat object if found, None otherwise

        """
        stmt = select(Chat).where(Chat.tg_chat_id == tg_chat_id)
        result = await session.execute(stmt)
        chat: Chat | None = result.scalar_one_or_none()
        return chat

    async def _find_link(self, link: str, session: AsyncSession) -> Link | None:
        """Internal method to find a link by its URL.

        Args:
            link: URL string to search for
            session: Async database session

        Returns:
            Link object if found, None otherwise

        """
        stmt = select(Link).where(Link.link == link)
        result = await session.execute(stmt)
        link_: Link | None = result.scalar_one_or_none()
        return link_

    async def get_links(self, tg_chat_id: int, session: AsyncSession) -> list[LinkResponse]:
        """Get all links associated with a chat.

        Args:
            tg_chat_id: Telegram chat ID to get links for
            session: Async database session

        Returns:
            List of LinkResponse objects with link details

        Raises:
            NotRegistratedChatError: If chat is not registered

        """
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
        """Add a new link or update existing link association for a chat.

        Args:
            tg_chat_id: Telegram chat ID to add link to
            link_request: Link data including URL, tags and filters
            session: Async database session

        Returns:
            LinkResponse with created/updated link details

        Raises:
            NotRegistratedChatError: If chat is not registered
            EntityAlreadyExistsError: If link association already exists

        """
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
            result = await session.execute(
                select(ChatLinkAssociation).where(
                    and_(
                        ChatLinkAssociation.chat_id == chat.id,
                        ChatLinkAssociation.link_id == link.id,
                    ),
                ),
            )
            chat_link_association = result.scalar_one_or_none()
            if chat_link_association:
                # check for association, if exists - change tags and filters
                chat_link_association.tags = link_request.tags
                chat_link_association.filters = link_request.filters
                session.add(chat_link_association)
                await session.commit()
                return LinkResponse(
                    id=link.id,
                    link=link.link,
                    tags=chat_link_association.tags,
                    filters=chat_link_association.filters,
                )
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
        """Remove a link association from a chat.

        Args:
            tg_chat_id: Telegram chat ID to remove link from
            link_request: Link data to remove
            session: Async database session

        Returns:
            LinkResponse with removed link details

        Raises:
            NotRegistratedChatError: If chat is not registered
            LinkNotFoundError: If link or association not found

        """
        chat = await self.is_chat_registrated(tg_chat_id, session=session)
        if chat is None:
            raise NotRegistratedChatError(message="Not registrated chat.")

        link = await self._find_link(link_request.link, session=session)
        if link is None:
            raise LinkNotFoundError(message="Link not found.")
        # Find association
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
        """Register a new chat in the system.

        Args:
            tg_chat_id: Telegram chat ID to register
            session: Async database session

        Raises:
            EntityAlreadyExistsError: If chat is already registered

        """
        if await self.is_chat_registrated(tg_chat_id, session=session):
            raise EntityAlreadyExistsError(
                message="Chat already registered. While registering chat",
            )
        new_chat = Chat(tg_chat_id=tg_chat_id)
        session.add(new_chat)
        logger.debug(f"Chat {tg_chat_id} registered")
        await session.commit()  # To get the link_id

    async def delete_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        """Delete a chat and all its associations.

        Args:
            tg_chat_id: Telegram chat ID to delete
            session: Async database session

        Raises:
            NotRegistratedChatError: If chat is not registered

        """
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

    async def get_chat_id_group_by_link(  # type: ignore
        self,
        session: AsyncSession,
        batch_size: int = 2,
    ) -> AsyncGenerator[dict[str, list[int]], None]:  # type: ignore
        """Get chat IDs grouped by links in batches.

        Args:
            session: Async database session
            batch_size: Number of links to process per batch

        Yields:
            Dictionary mapping links to lists of associated chat IDs

        """
        last_id = 0
        while True:
            result = await session.execute(
                select(Link)
                .options(
                    selectinload(Link.chats_details).selectinload(
                        ChatLinkAssociation.chat,
                    ),  # Explicit loading path
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
                link.link: [
                    assoc.chat.tg_chat_id
                    for assoc in link.chats_details
                    if assoc.chat  # Protection against possible None
                ]
                for link in links
            }


async def manual_test(session: AsyncSession) -> None:
    tg_chat_id = 1
    link_repository_orm = LinkRepositoryORM()

    # was await link_repository_orm.register_chat(tg_chat_id, session=session)
    await link_repository_orm.delete_chat(tg_chat_id, session=session)

    """
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612688", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612667", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612665", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612613", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/42393259", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_orm.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/56219834", tags=[], filters=[]),
    #     session,
    # )"""


"""
    for i in range(10):
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
