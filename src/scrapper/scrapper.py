"""Module for scraping and checking updates from GitHub and StackOverflow links."""

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_classes import LinkUpdate
from src.db import db_helper
from src.dependencies import link_service
from src.exceptions.exceptions import ExtractResponseError
from src.scrapper.clients import GitHubClient, StackOverflowClient
from src.scrapper.update_notifier import AbstractUpdateNotifier, NotifierFactory
from src.settings import (
    BATCH_SIZE,
    PERIOD_OF_CHECK_SECONDS,
    TIMEZONE,
    APIServerSettings,
    MessageBrokerSettings,
)

if TYPE_CHECKING:
    from src.link_service.link_service import AsyncLinkService, LinkService

api_settings = APIServerSettings()
message_broker_settings = MessageBrokerSettings()


class Scrapper:
    """Main scraper class for checking updates from GitHub and StackOverflow links."""

    def __init__(self) -> None:
        """Initialize Scrapper with clients and services."""
        self.curr_id = 0
        self.github_client = GitHubClient()
        self.stackoverflow_client = StackOverflowClient()
        self.link_service: LinkService | AsyncLinkService = link_service
        self.update_notifier: AbstractUpdateNotifier = NotifierFactory().get_notifier(
            type_=message_broker_settings.transport_type,
        )
        logger.debug(f"update_notifier: {self.update_notifier}")

    async def start(self) -> None:
        if hasattr(self.update_notifier, "start"):
            await self.update_notifier.start()
            logger.debug("update_notifier: started")

    async def stop(self) -> None:
        if hasattr(self.update_notifier, "stop"):
            await self.update_notifier.stop()
            logger.debug("update_notifier: stopped")

    def _get_type_link(self, link: str) -> Literal["github", "stackoverflow"] | None:
        """Determine the type of link (GitHub or StackOverflow).

        Args:
            link: The URL to check.

        Returns:
            The link type as either "github" or "stackoverflow".

        Raises:
            ValueError: If the link type cannot be determined.

        """
        if link.startswith("https://github.com/"):
            return "github"
        elif link.startswith("https://stackoverflow.com/"):
            return "stackoverflow"
        else:
            raise ValueError("Can't get type of link")

    async def get_description(
        self,
        link: str,
        last_seen_dt: datetime,
        http_client: httpx.AsyncClient,
    ) -> str | None:
        """Get description updates for a given link since last seen datetime.

        Args:
            link: The URL to check for updates.
            last_seen_dt: The datetime to check for updates since.
            http_client: The HTTP client to use for requests.

        Returns:
            The updated description if found, None otherwise.

        """
        type_link = self._get_type_link(link)

        try:
            match type_link:
                case "github":
                    return await self.github_client.get_description(
                        link,
                        http_client,
                        last_seen_dt,
                    )

                case "stackoverflow":
                    return await self.stackoverflow_client.get_description(
                        link,
                        http_client,
                        last_seen_dt,
                    )
        except ExtractResponseError as e:
            logger.exception(e)
        except ConnectionError as e:
            logger.exception(e)
        except ValueError as e:
            logger.exception(e)
        return None

    async def check_updates(self, session: AsyncSession) -> None:
        """Check for updates on all tracked links and send notifications.

        Args:
            session: The database session to use for queries.

        """
        current_time = datetime.now(TIMEZONE)
        week_ago = current_time - timedelta(seconds=PERIOD_OF_CHECK_SECONDS)
        async for chat_id_group_by_link in self.link_service.get_chat_id_group_by_link(  # type: ignore
            session=session,
            batch_size=BATCH_SIZE,
        ):
            link_updates = []
            logger.debug(f"chat_id_group_by_link: {chat_id_group_by_link}")
            async with httpx.AsyncClient() as http_client:
                for link, chat_ids in chat_id_group_by_link.items():
                    description = await self.get_description(link, week_ago, http_client)
                    if description:
                        link_update = LinkUpdate(
                            id=self.curr_id,
                            link=link,
                            description=description,
                            tg_chat_ids=chat_ids,
                        )
                        self.curr_id += 1
                        link_updates.append(link_update)
            await self.update_notifier.send_notifications(link_updates)


async def scrapper() -> None:
    """Main scraper function that runs indefinitely to check for updates."""
    scraper = Scrapper()
    await scraper.start()
    async with db_helper.get_session() as session:
        while True:
            try:
                await scraper.check_updates(session)
                await asyncio.sleep(PERIOD_OF_CHECK_SECONDS)
            except Exception as e:  # noqa: PERF203
                logger.error(f"error while check updates\n\n{e}")
                await scraper.stop()
                raise


if __name__ == "__main__":
    asyncio.run(scrapper())
