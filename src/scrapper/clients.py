from datetime import datetime
from typing import Protocol, Tuple

import httpx
from loguru import logger

from src.settings import LEN_OF_PARTS_GITHUB_URL, TIMEZONE


class UpdateClientInterface(Protocol):
    def parse_url(self, url: str) -> str | Tuple[str, str]:
        pass

    async def get_last_update(self, url: str) -> datetime:
        pass


class StackOverflowClient(UpdateClientInterface):
    BASE_URL = "https://api.stackexchange.com/2.3"

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    def parse_url(self, url: str) -> str:
        question_id = url.split("/")[-1]
        if not question_id.isdigit():
            raise ValueError("Invalid Stackoverflow URL format")
        return question_id

    async def get_last_update(self, url: str) -> datetime:
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


class GitHubClient(UpdateClientInterface):
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

    async def get_last_update(self, url: str) -> datetime:
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
