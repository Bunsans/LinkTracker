import asyncio
from datetime import datetime, timedelta
from typing import Literal

import httpx
from fastapi import status
from loguru import logger

from src.data import link_service
from src.data_classes import LinkUpdate
from src.scrapper.clients import GitHubClient, StackOverflowClient
from src.settings import TIMEZONE


def check_type(url: str) -> Literal["github", "stackoverflow"] | None:
    if "github" in url:
        return "github"
    if "stackoverflow" in url:
        return "stackoverflow"
    return None


# Функция для проверки обновлений
async def check_updates() -> None:
    async with httpx.AsyncClient() as client:
        current_time = datetime.now(TIMEZONE)
        week_ago = current_time - timedelta(days=7)

        github_client = GitHubClient(client)
        stackoverflow_client = StackOverflowClient(client)
        chat_id_group_by_link = link_service.get_chat_id_group_by_link()
        for link, chat_ids in chat_id_group_by_link.items():
            type_link = check_type(url=link)
            """ # try:
            # except ValueError:
            #     logger.warning(f"Invalid date format: {last_updated_str}")
            #     last_updated = datetime.fromisoformat("2000-01-01 00:00:00+00:00")"""
            match type_link:
                case "github":
                    last_updated = await github_client.get_last_update(link)
                case "stackoverflow":
                    last_updated = await stackoverflow_client.get_last_update(link)
                case None:
                    continue
            if last_updated > week_ago:
                body = LinkUpdate(
                    id=1,
                    link=link,
                    description=f"Появилось обновление. Последнее в {last_updated}",
                    tg_chat_ids=list(chat_ids),
                )
                logger.debug(body.model_dump())
                response = await client.post(
                    url="http://0.0.0.0:7777/updates",
                    json=body.model_dump(),
                )
                if response.status_code == status.HTTP_200_OK:
                    logger.info("good send")
                else:
                    logger.info(f"Something wrong\n{response.text}")


async def scrapper() -> None:
    while True:
        await check_updates()
        await asyncio.sleep(360)


if __name__ == "__main__":
    asyncio.run(scrapper())
