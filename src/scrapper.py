import asyncio
from datetime import datetime, timedelta
from typing import Literal, Tuple

import httpx
from loguru import logger

from src.constants import LEN_OF_PARTS_GITHUB_URL, SUCCESS_RESPONSE_CODE, TIMEZONE
from src.data import links_chat_id_mapper
from src.data_classes import LinkUpdate


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    def parse_url(self, url: str) -> Tuple[str, str]:
        prefix = "https://github.com/"
        if not url.startswith(prefix):
            raise ValueError("Invalid GitHub URL format")
        path = url[len(prefix) :]
        parts = path.split("/")
        if len(parts) < LEN_OF_PARTS_GITHUB_URL:
            raise ValueError("Invalid GitHub URL format")
        owner = parts[0]
        repo = parts[1]
        return owner, repo

    async def get_repo_last_updated(self, url: str) -> datetime:
        owner, repo = self.parse_url(url)
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = await self.client.get(url)
        data = response.json()
        last_updated_str = data.get("updated_at")
        logger.debug(f"Last updated git: {last_updated_str}, type: {type(last_updated_str)}")
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=TIMEZONE,
        )
        logger.debug(f"Last updated git: {last_updated}, type: {type(last_updated)}")

        return last_updated


class StackOverflowClient:
    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    def parse_url(self, url: str) -> str:
        question_id = url.split("/")[-1]
        if not question_id.isdigit():
            raise ValueError("Invalid Stackoverflow URL format")
        return question_id

    async def get_question_last_updated(self, url: str) -> datetime:
        question_id = self.parse_url(url)
        url = f"{self.BASE_URL}/questions/{question_id}?order=desc&sort=activity&site=stackoverflow"
        response = await self.client.get(url)
        data = response.json()
        items = data.get("items", [])
        if items:
            last_updated_timestamp: int = items[0].get("last_activity_date")
            logger.debug(
                f"""last_updated_str_unix_timestamp: {last_updated_timestamp},
type: {type(last_updated_timestamp)}""",
            )
            return datetime.fromtimestamp(last_updated_timestamp, tz=TIMEZONE)
        else:
            raise ValueError("No items in response")


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
        # for test  await github_client.get_repo_last_updated("https://github.com/catboost/catboost")
        # for test await stackoverflow_client.get_question_last_updated(79481727)
        for link, chat_ids in links_chat_id_mapper.items():
            type_link = check_type(url=link)
            match type_link:
                case "github":
                    last_updated = await github_client.get_repo_last_updated(link)
                case "stackoverflow":
                    last_updated = await stackoverflow_client.get_question_last_updated(link)
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
                if response.status_code == SUCCESS_RESPONSE_CODE:
                    logger.info("good send")
                else:
                    logger.info(f"Something wrong\n{response.text}")


async def scrapper() -> None:
    while True:
        await check_updates()
        await asyncio.sleep(360)


if __name__ == "__main__":
    asyncio.run(scrapper())
