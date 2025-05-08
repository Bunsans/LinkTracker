import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

import httpx
from fastapi import status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_classes import LinkUpdate
from src.db import db_helper
from src.dependencies import link_service
from src.scrapper.clients import GitHubClient, StackOverflowClient
from src.settings import TIMEZONE, APIServerSettings

if TYPE_CHECKING:
    from src.repository.link_services import AsyncLinkService, LinkService

api_settings = APIServerSettings()


class Scrapper:
    def __init__(self) -> None:
        self.github_client = GitHubClient()
        self.stackoverflow_client = StackOverflowClient()
        self.link_service: LinkService | AsyncLinkService = link_service

    def _get_type_link(self, link: str) -> Literal["github", "stackoverflow"] | None:
        if link.startswith("https://github.com/"):
            return "github"
        elif link.startswith("https://stackoverflow.com/"):
            return "stackoverflow"
        else:
            raise ValueError("Can't get type of link")

    async def _get_last_update(
        self,
        link: str,
        http_client: httpx.AsyncClient,
    ) -> datetime | None:
        type_link = self._get_type_link(link=link)
        match type_link:
            case "github":
                return await self.github_client.get_last_update(link, http_client)
            case "stackoverflow":
                return await self.stackoverflow_client.get_last_update(link, http_client)
            case _:
                return None

    def _get_description_good(self, link: str, last_updated: datetime) -> str:
        return f"""Появилось обновление по ссылке {link}.
Последнее в {last_updated.strftime('%Y-%m-%d %H:%M:%S')}"""

    # if need notifie about
    # not updated link: def _get_description_none_last_update(self, link: str) -> str:
    # if need notifie about
    # not updated link: return f"Нет обновлений по ссылке: {link}"

    def _get_description_error(self, link: str, e: Exception | str) -> str:
        return f"Проблема при скраппинге обновления по ссылке: {link}\nОшибка:{e}"

    async def get_description(
        self,
        link: str,
        week_ago: datetime,
        http_client: httpx.AsyncClient,
    ) -> str | None:
        try:
            last_updated = await self._get_last_update(link, http_client)
        except ConnectionError as error:
            return self._get_description_error(link, error)
        except ValueError as error:
            return self._get_description_error(link, error)
        else:
            if last_updated is None:
                return self._get_description_error(link, "last update is None ")
            if last_updated > week_ago:
                return self._get_description_good(link, last_updated)

        return None
        # if need notifie about not
        # updated link: return self._get_description_none_last_update(link)

    async def send_notification(
        self,
        link_update: LinkUpdate,
        http_client: httpx.AsyncClient,
    ) -> None:
        response = await http_client.post(
            url=api_settings.url_server + "/updates",
            json=link_update.model_dump(),
        )
        if response.status_code == status.HTTP_200_OK:
            logger.info("All send good")
        else:
            logger.warning(f"Something wrong\n{response.text}")

    async def check_updates(self, session: AsyncSession) -> None:
        current_time = datetime.now(TIMEZONE)
        week_ago = current_time - timedelta(days=7)
        chat_id_group_by_link = {"session": {1}}
        await session.commit()
        # TODO change to generator chat_id_group_by_link =
        # TODO  await self.link_service.get_chat_id_group_by_link(session=session)
        logger.warning(f"Scrapper: {chat_id_group_by_link}")
        async with httpx.AsyncClient() as http_client:
            for link, chat_ids in chat_id_group_by_link.items():
                description = await self.get_description(link, week_ago, http_client)
                logger.debug(f"Last update for {link} is {description}")
                if description:
                    link_update = LinkUpdate(
                        id=1,
                        link=link,
                        description=description,
                        tg_chat_ids=list(chat_ids),
                    )
                    logger.debug(link_update)
                    await self.send_notification(link_update, http_client)


async def scrapper() -> None:
    scraper = Scrapper()
    session = await anext(db_helper.session_getter())

    while True:
        await asyncio.sleep(10)
        await scraper.check_updates(session)


if __name__ == "__main__":
    asyncio.run(scrapper())
