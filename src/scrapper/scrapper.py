import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import httpx
from fastapi import status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_classes import LinkUpdate
from src.db import db_helper
from src.dependencies import link_service
from src.exceptions.exceptions import ExtractResponseError
from src.scrapper.clients import GitHubClient, StackOverflowClient
from src.settings import BATCH_SIZE, PERIOD_OF_CHECK_SECONDS, TIMEZONE, APIServerSettings

if TYPE_CHECKING:
    from src.link_service.link_service import AsyncLinkService, LinkService

api_settings = APIServerSettings()


class AbstractUpdateNotifier(ABC):
    @abstractmethod
    async def send_notification(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        pass


class UpdateNotifier(AbstractUpdateNotifier):
    async def send_notification(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        async with httpx.AsyncClient() as http_client:
            for link_update in link_updates:
                response = await http_client.post(
                    url=api_settings.url_server + "/updates",
                    json=link_update.model_dump(),
                )
                if response.status_code == status.HTTP_200_OK:
                    logger.success("All send good")
                else:
                    logger.warning(f"Something wrong\n{response.text}")


class Scrapper:
    def __init__(self) -> None:
        self.github_client = GitHubClient()
        self.stackoverflow_client = StackOverflowClient()
        self.link_service: LinkService | AsyncLinkService = link_service
        self.update_notifier = UpdateNotifier()

    def _get_type_link(self, link: str) -> Literal["github", "stackoverflow"] | None:
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
                    logger.debug(
                        f"""Last update for {link}:
{description[:100] if isinstance(description, str) else None}""",
                    )
                    if description:
                        link_update = LinkUpdate(
                            id=1,
                            link=link,
                            description=description,
                            tg_chat_ids=chat_ids,
                        )
                        link_updates.append(link_update)
            await self.update_notifier.send_notification(link_updates)


async def scrapper() -> None:
    scraper = Scrapper()
    session = await anext(db_helper.session_getter())

    while True:
        await scraper.check_updates(session)
        await asyncio.sleep(PERIOD_OF_CHECK_SECONDS)


if __name__ == "__main__":
    asyncio.run(scrapper())
