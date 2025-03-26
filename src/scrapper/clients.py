from abc import ABC, abstractmethod
from datetime import datetime

import httpx
from loguru import logger

from src.settings import LEN_OF_PARTS_GITHUB_URL, TIMEZONE


class UpdateClientAbstract(ABC):
    API_NAME: str
    BASE_URL: str

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    @abstractmethod
    def parse_url(self, url: str) -> str:
        pass

    @abstractmethod
    def extract_last_update(self, response: httpx.Response) -> datetime:
        pass

    async def get_last_update(self, url: str) -> datetime:
        url = self.parse_url(url)
        response = await self.client.get(url)
        match response.status_code:
            case 404:
                raise ConnectionError(f"{self.API_NAME} question not found")
            case 500:
                raise ConnectionError(f"{self.API_NAME} API error")
            case 200:
                return self.extract_last_update(response)
            case _:
                raise ConnectionError(f"{self.API_NAME} API error unknown error")


class StackOverflowClient(UpdateClientAbstract):
    BASE_URL = "https://api.stackexchange.com/2.3"
    API_NAME = "StackOverflow"

    def parse_url(self, url: str) -> str:
        prefix = "https://stackoverflow.com/"

        url_splitted = url.split("/")
        questions = url_splitted[-2]  # must be a "questions"
        question_id = url_splitted[-1]

        if not url.startswith(prefix):
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        if questions != "questions":
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        if not question_id.isdigit():
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        return (
            f"{self.BASE_URL}/questions/{question_id}?order=desc&sort=activity&site=stackoverflow"
        )

    def extract_last_update(self, response: httpx.Response) -> datetime:
        data = response.json()
        items = data.get("items", [])
        if not items:
            raise ValueError("No items in response")

        last_updated_timestamp: int = items[0].get("last_activity_date", 0)
        logger.debug(
            f"""last_updated_str_unix_timestamp: {last_updated_timestamp},
type: {type(last_updated_timestamp)}""",
        )
        if not last_updated_timestamp:
            raise ValueError("No last_activity_date in response")

        return datetime.fromtimestamp(last_updated_timestamp, tz=TIMEZONE)


class GitHubClient(UpdateClientAbstract):
    BASE_URL = "https://api.github.com"
    API_NAME = "GitHub"

    def parse_url(self, url: str) -> str:
        prefix = "https://github.com/"
        if not url.startswith(prefix):
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        path = url[len(prefix) :]
        parts = path.split("/")
        if len(parts) < LEN_OF_PARTS_GITHUB_URL:
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        owner = parts[0]
        repo = parts[1]
        return f"{self.BASE_URL}/repos/{owner}/{repo}"

    def extract_last_update(self, response: httpx.Response) -> datetime:
        data = response.json()
        last_updated_str = data.get("updated_at", "")
        if not last_updated_str:
            raise ValueError("No updated_at in response")
        logger.debug(f"Last updated git: {last_updated_str}, type: {type(last_updated_str)}")

        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=TIMEZONE,
        )

        logger.debug(f"Last updated git: {last_updated}, type: {type(last_updated)}")
        return last_updated
