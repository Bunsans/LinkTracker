from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx

from src.exceptions.exceptions import GitHubExtractResponseError, StackOverflowExtractResponseError
from src.scrapper.schemas import GitHubApiResponse, StackOverflowApiResponse
from src.settings import LEN_OF_PARTS_GITHUB_URL, ScrapperSettings

scrapper_settings = ScrapperSettings()


class UpdateClientAbstract(ABC):
    API_NAME: str
    BASE_URL: str

    @abstractmethod
    def get_api_url(self, url: str) -> str:
        pass

    @abstractmethod
    def extract_info(self, response: httpx.Response, last_seen_dt: datetime) -> str | None:
        pass

    @abstractmethod
    async def get_request(self, url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        pass

    async def get_description(
        self,
        url: str,
        http_client: httpx.AsyncClient,
        last_seen_dt: datetime,
    ) -> str | None:
        api_url = self.get_api_url(url)
        # debug logger.debug(f"Getting {self.API_NAME} description for {api_url}")
        response: httpx.Response = await self.get_request(api_url, http_client)
        match response.status_code:
            case 404:
                raise ConnectionError(f"{self.API_NAME} question not found")
            case 500:
                raise ConnectionError(f"{self.API_NAME} API error")
            case 200:
                return self.extract_info(response, last_seen_dt)
            case _:
                raise ConnectionError(f"{self.API_NAME} API error unknown error, {response.text}")


class StackOverflowClient(UpdateClientAbstract):
    BASE_URL = "https://api.stackexchange.com/2.3"
    API_NAME = "StackOverflow"
    stack_query = scrapper_settings.stack_query

    async def get_request(self, api_url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        return await http_client.get(api_url)

    def get_api_url(self, url: str) -> str:
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
        return f"{self.BASE_URL}/questions/{question_id}/{self.stack_query}"

    def extract_info(self, response: httpx.Response, last_seen_dt: datetime) -> str | None:
        data: dict[Any, Any] = response.json()
        items: list[Any] = data.get("items", [])
        if items is None:
            raise StackOverflowExtractResponseError("No items in response")
        result_str = ""

        for item in items:
            extracted_info = StackOverflowApiResponse(**item)
            if extracted_info.last_activity_date is None:
                raise StackOverflowExtractResponseError("No last_activity_date in response")
            if extracted_info.last_activity_date > last_seen_dt:  # type: ignore
                result_str += extracted_info.get_description() + "\n"

        return result_str.rstrip()


class GitHubClient(UpdateClientAbstract):
    BASE_URL = "https://api.github.com"
    API_NAME = "GitHub"
    GITHUB_TOKEN = scrapper_settings.github_token

    async def get_request(self, api_url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        return await http_client.get(
            api_url,
            headers={"Authorization": f"Bearer {self.GITHUB_TOKEN}"},
        )

    def get_api_url(self, url: str) -> str:
        prefix = "https://github.com/"
        if not url.startswith(prefix):
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        path = url[len(prefix) :]
        parts = path.split("/")
        if len(parts) < LEN_OF_PARTS_GITHUB_URL:
            raise ValueError(f"Invalid {self.API_NAME} URL format")
        owner = parts[0]
        repo = parts[1]

        if len(parts) > LEN_OF_PARTS_GITHUB_URL and parts[2] == "issues":
            return f"{self.BASE_URL}/repos/{owner}/{repo}/issues"
        if len(parts) > LEN_OF_PARTS_GITHUB_URL and parts[2] == "pull":
            ### FOR API NEED `pulls`
            return f"{self.BASE_URL}/repos/{owner}/{repo}/pulls"
        ## subscribe to new issues by default
        return f"{self.BASE_URL}/repos/{owner}/{repo}/issues"

    def extract_info(self, response: httpx.Response, last_seen_dt: datetime) -> str:
        items: list[Any] = response.json()
        if items is None:
            raise GitHubExtractResponseError("No items in response")
        example: str = items[0].get("html_url", "")
        if example:
            result_str = f"Обновления по: {"".join(example.split("/")[:-1])}\n"
        result_str = ""

        for item in items:
            extracted_info = GitHubApiResponse(**item)
            if extracted_info.updated_at is None:
                raise StackOverflowExtractResponseError("No last_activity_date in response")
            if extracted_info.updated_at > last_seen_dt:  # type: ignore
                result_str += extracted_info.get_description() + "\n"

        return result_str.rstrip()
