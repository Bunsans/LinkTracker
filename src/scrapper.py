import asyncio
from datetime import datetime, timedelta
from typing import Literal, Tuple

import httpx
from loguru import logger

from src.data import links_chat_id_mapper
from src.data_classes import LinkUpdate


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, client):
        self.client = client

    def parse_url(url: str) -> Tuple[str, str]:
        pass

    async def get_repo_last_updated(self, url: str):
        owner, repo = self.parse_url(url)
        url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        response = await self.client.get(url)
        data = response.json()
        return data.get("updated_at")


class StackOverflowClient:
    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, client):
        self.client = client

    async def get_question_last_updated(self, question_id):
        url = f"{self.BASE_URL}/questions/{question_id}?order=desc&sort=activity&site=stackoverflow"
        response = await self.client.get(url)
        data = response.json()
        items = data.get("items", [])
        if items:
            return items[0].get("last_activity_date")


def check_type(url: str) -> Literal["github", "stackoverflow"]:
    pass


# Функция для проверки обновлений
async def check_updates():
    async with httpx.AsyncClient() as client:
        current_time = datetime.now()
        week_ago = current_time - timedelta(days=7)

        github_client = GitHubClient(client)
        stackoverflow_client = StackOverflowClient(client)

        # github_repos = [("donnemartin", "system-design-primer")]
        # stackoverflow_questions = [79473781]

        for link, chat_ids in links_chat_id_mapper.items():
            type_link = check_type(url=link)
            # match type_link:
            #     case "github":
            #         last_updated = await github_client.get_repo_last_updated(link)
            #     case "stackoverflow":
            #         last_updated = await stackoverflow_client.get_question_last_updated(link)
            last_updated = current_time
            if last_updated > week_ago:
                body = LinkUpdate(
                    id=1,
                    link=link,
                    description=f"Появилось обновление. Последнее в {last_updated}",
                    tg_chat_ids=chat_ids,
                )
                logger.debug(body.model_dump())
                response = await client.post(
                    url="http://0.0.0.0:7777/updates",
                    json=body.model_dump(),
                )
                if response.status_code == 200:
                    logger.info("good send")
                else:
                    logger.info(f"Something wrong\n{response.text}")

        # # Проверка обновлений на GitHub
        # for owner, repo in github_repos:

        #     print(f"Repo {owner}/{repo} last updated at {last_updated}")

        # # Проверка обновлений на StackOverflow
        # for question_id in stackoverflow_questions:
        #     print(f"Question {question_id} last updated at {datetime.fromtimestamp(last_updated)}")


# Планировщик задач
async def scrapper():
    while True:
        await check_updates()
        await asyncio.sleep(60)  # Проверять каждую минуту


if __name__ == "__main__":
    asyncio.run(scrapper())
