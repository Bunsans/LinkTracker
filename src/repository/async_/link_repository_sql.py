import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import Result, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db_helper
from src.exceptions.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    NotRegistratedChatError,
)
from src.repository.async_.interface import AcyncLinkRepositoryInterface
from src.schemas.schemas import AddLinkRequest, LinkResponse, RemoveLinkRequest


class LinkRepositoryRawSQL(AcyncLinkRepositoryInterface):

    async def is_chat_registrated(  # type: ignore
        self,
        tg_chat_id: int,
        session: AsyncSession,
    ) -> dict | None:  # type: ignore
        """Check if a chat is registered in the system.

        Args:
            tg_chat_id: Telegram chat ID to check
            session: Async database session

        Returns:
            Dictionary with chat data if found, None otherwise

        """
        query = text(
            """
            SELECT id, tg_chat_id
            FROM chats
            WHERE tg_chat_id = :tg_chat_id
        """,
        )
        result: Result[Any] = await session.execute(query, {"tg_chat_id": tg_chat_id})
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def _find_link(self, link: str, session: AsyncSession) -> dict[Any, Any] | None:
        """Internal method to find a link by its URL.

        Args:
            link: URL string to search for
            session: Async database session

        Returns:
            Dictionary with link data if found, None otherwise

        """
        query = text("SELECT * FROM links WHERE link = :link")
        result: Result[Any] = await session.execute(query, {"link": link})
        row = result.mappings().one_or_none()
        return dict(row) if row else None

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
        chat = await self.is_chat_registrated(tg_chat_id, session)
        if not chat:
            raise NotRegistratedChatError("Not registrated chat.")

        query = text(
            """
            SELECT cla.tags, cla.filters, l.link, l.id
            FROM chat_link_associations cla
            JOIN links l ON cla.link_id = l.id
            WHERE cla.chat_id = :chat_id
        """,
        )
        result: Result[Any] = await session.execute(query, {"chat_id": chat["id"]})
        return [
            LinkResponse(id=row["id"], link=row["link"], tags=row["tags"], filters=row["filters"])
            for row in result.mappings().all()
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

        """
        chat = await self.is_chat_registrated(tg_chat_id, session)
        if not chat:
            raise NotRegistratedChatError("Not registrated chat.")

        link = await self._find_link(link_request.link, session)

        if not link:
            insert_link = text(
                "INSERT INTO links (link, count_chats) VALUES (:link, 1) RETURNING id",
            )
            result = await session.execute(insert_link, {"link": link_request.link})
            link_id = result.scalar()
        else:
            link_id = link["id"]
            check_assoc = text(
                """
                SELECT * FROM chat_link_associations
                WHERE chat_id = :chat_id AND link_id = :link_id
            """,
            )
            assoc_result = await session.execute(
                check_assoc,
                {"chat_id": chat["id"], "link_id": link_id},
            )

            if assoc_result.scalar_one_or_none():
                update_assoc = text(
                    """
                    UPDATE chat_link_associations
                    SET tags = :tags, filters = :filters
                    WHERE chat_id = :chat_id AND link_id = :link_id
                    RETURNING *
                """,
                )
                result = await session.execute(
                    update_assoc,
                    {
                        "tags": json.dumps(link_request.tags),
                        "filters": json.dumps(link_request.filters),
                        "chat_id": chat["id"],
                        "link_id": link_id,
                    },
                )
                updated = result.mappings().one()
                await session.commit()
                return LinkResponse(
                    id=link_id,
                    link=link_request.link,
                    tags=updated["tags"],
                    filters=updated["filters"],
                )
            else:
                update_count = text(
                    """
                    UPDATE links
                    count_chats = count_chats + 1
                    WHERE id = :link_id
                """,
                )
                await session.execute(update_count, {"link_id": link_id})
        insert_assoc = text(
            """
            INSERT INTO chat_link_associations
            (chat_id, link_id, tags, filters)
            VALUES (:chat_id, :link_id, CAST(:tags AS JSONB), CAST(:filters AS JSONB))
            RETURNING *
        """,
        )
        result = await session.execute(
            insert_assoc,
            {
                "chat_id": chat["id"],
                "link_id": link_id,
                "tags": json.dumps(link_request.tags),
                "filters": json.dumps(link_request.filters),
            },
        )
        new_assoc = result.mappings().one()
        await session.commit()

        return LinkResponse(
            id=new_assoc["id"],
            link=link_request.link,
            tags=new_assoc["tags"],
            filters=new_assoc["filters"],
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
        chat = await self.is_chat_registrated(tg_chat_id, session)
        if not chat:
            raise NotRegistratedChatError("Not registrated chat.")

        link = await self._find_link(link_request.link, session)
        if link is None:
            raise LinkNotFoundError("Link not found.")

        delete_assoc = text(
            """
            DELETE FROM chat_link_associations
            WHERE chat_id = :chat_id AND link_id = :link_id
            RETURNING *
        """,
        )
        result = await session.execute(
            delete_assoc,
            {"chat_id": chat["id"], "link_id": link["id"]},
        )
        row = result.mappings().one_or_none()
        deleted = dict(row) if row else None
        update_count = text(
            """
            UPDATE links
            SET count_chats = count_chats - 1
            WHERE id = :link_id
        """,
        )
        await session.execute(update_count, {"link_id": link["id"]})
        await session.commit()
        check_count = text("SELECT count_chats FROM links WHERE id = :link_id")
        count_result = await session.execute(check_count, {"link_id": link["id"]})
        if count_result.scalar() == 0:
            delete_link = text("DELETE FROM links WHERE id = :link_id")
            await session.execute(delete_link, {"link_id": link["id"]})

        await session.commit()
        if deleted is None:
            tags = []
            filters = []
        else:
            tags = deleted.get("tags", [])
            filters = deleted.get("filters", [])
        return LinkResponse(
            id=link["id"],
            link=link["link"],
            tags=tags,
            filters=filters,
        )

    async def register_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        """Register a new chat in the system.

        Args:
            tg_chat_id: Telegram chat ID to register
            session: Async database session

        Raises:
            EntityAlreadyExistsError: If chat is already registered

        """
        if await self.is_chat_registrated(tg_chat_id, session):
            raise EntityAlreadyExistsError("Chat already registered")

        insert_chat = text("INSERT INTO chats (tg_chat_id) VALUES (:tg_chat_id)")
        await session.execute(insert_chat, {"tg_chat_id": tg_chat_id})
        await session.commit()

    async def delete_chat(self, tg_chat_id: int, session: AsyncSession) -> None:
        """Delete a chat and all its associations.

        Args:
            tg_chat_id: Telegram chat ID to delete
            session: Async database session

        Raises:
            NotRegistratedChatError: If chat is not registered

        """
        chat = await self.is_chat_registrated(tg_chat_id, session)
        if not chat:
            raise NotRegistratedChatError("Not registrated chat")

        delete_assoc = text(
            """
            DELETE FROM chat_link_associations
            WHERE chat_id = :chat_id
            RETURNING link_id
        """,
        )
        result = await session.execute(delete_assoc, {"chat_id": chat["id"]})
        link_ids = [row["link_id"] for row in result.mappings().all()]

        update_links = text(
            """
            UPDATE links
            SET count_chats = count_chats - 1
            WHERE id = ANY(:link_ids)
        """,
        )
        await session.execute(update_links, {"link_ids": link_ids})

        delete_links = text(
            """
            DELETE FROM links
            WHERE count_chats <= 0
        """,
        )
        await session.execute(delete_links)

        delete_chat = text("DELETE FROM chats WHERE id = :chat_id")
        await session.execute(delete_chat, {"chat_id": chat["id"]})
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
        offset = 0
        while True:
            query = text(
                """
                SELECT l.link, array_agg(c.tg_chat_id) AS chat_ids
                FROM links l
                JOIN chat_link_associations cla ON l.id = cla.link_id
                JOIN chats c ON cla.chat_id = c.id
                GROUP BY l.link
                LIMIT :batch_size OFFSET :offset
            """,
            )
            result: Result[Any] = await session.execute(
                query,
                {"batch_size": batch_size, "offset": offset},
            )
            batch = result.mappings().all()

            if not batch:
                break

            yield {row["link"]: row["chat_ids"] for row in batch}
            offset += batch_size


async def manual_test(session: AsyncSession) -> None:
    """tg_chat_id = 1
    link_repository_sql = LinkRepositoryRawSQL().
    """
    """
    # res = await link_repository_orm.is_chat_registrated(tg_chat_id, session=session)
    # print(res)

    # await link_repository_sql.register_chat(tg_chat_id, session=session)
    # # await link_repository_orm.delete_chat(tg_chat_id, session=session)

    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612688", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612667", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612665", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/79612613", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/42393259", tags=[], filters=[]),
    #     session,
    # )
    # await link_repository_sql.add_link(
    #     tg_chat_id,
    #     AddLinkRequest(link=f"https://stackoverflow.com/questions/56219834", tags=[], filters=[]),
    #     session,
    # )

    # res = await link_repository_sql.get_links(tg_chat_id, session)
    # logger.debug("before remove")
    # logger.debug(res)

    # res = await link_repository_sql.remove_link(
    #     tg_chat_id,
    #     link_request=RemoveLinkRequest(link="https://stackoverflow.com/questions/79612613"),
    #     session=session,
    # )
    # logger.debug(" remove")
    # logger.debug(res)

    # res = await link_repository_sql.get_links(tg_chat_id, session)
    # logger.debug("after remove")
    # logger.debug(res)

    # await link_repository_sql.delete_chat(
    #     tg_chat_id,
    #     session,
    # )

    # async for batch in link_repository_sql.get_chat_id_group_by_link(session, batch_size=3):
    #     for link, chat_ids in batch.items():
    #         logger.debug(f"Link: {link}")
    #         logger.debug(f"Chat IDs: {chat_ids}")

"""


async def main() -> None:
    async with db_helper.session_factory() as session:
        await manual_test(session)


if __name__ == "__main__":
    asyncio.run(main())
