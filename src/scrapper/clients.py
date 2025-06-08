"""Module containing abstract and concrete implementations of
clients for checking updates from GitHub and StackOverflow.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import httpx

from src.exceptions.exceptions import GitHubExtractResponseError, StackOverflowExtractResponseError
from src.scrapper.schemas import GitHubApiResponse, StackOverflowApiResponse
from src.settings import LEN_OF_PARTS_GITHUB_URL, ScrapperSettings

scrapper_settings = ScrapperSettings()


class UpdateClientAbstract(ABC):
    """Abstract base class for update clients."""

    API_NAME: str
    BASE_URL: str

    @abstractmethod
    def get_api_url(self, url: str) -> str:
        """Convert a web URL to an API endpoint URL.

        Args:
            url: The web URL to convert.

        Returns:
            The corresponding API endpoint URL.

        """

    @abstractmethod
    def extract_info(self, response: httpx.Response, last_seen_dt: datetime) -> str | None:
        """Extract relevant information from the API response.

        Args:
            response: The HTTP response from the API.
            last_seen_dt: The datetime to compare against for new updates.

        Returns:
            Extracted information as a string, or None if no updates.

        """

    @abstractmethod
    async def get_request(self, url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        """Make an API request.

        Args:
            url: The API URL to request.
            http_client: The HTTP client to use for the request.

        Returns:
            The HTTP response from the API.

        """

    async def get_description(
        self,
        url: str,
        http_client: httpx.AsyncClient,
        last_seen_dt: datetime,
    ) -> str | None:
        """Get description updates for a given URL since last seen datetime.

        Args:
            url: The URL to check for updates.
            http_client: The HTTP client to use for requests.
            last_seen_dt: The datetime to check for updates since.

        Returns:
            The updated description if found, None otherwise.

        Raises:
            ConnectionError: If there are issues connecting to the API or the resource is not found.

        """
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
    """Client for interacting with the StackOverflow API."""

    BASE_URL = "https://api.stackexchange.com/2.3"
    API_NAME = "StackOverflow"
    stack_query = scrapper_settings.stack_query

    async def get_request(self, api_url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        """Make a GET request to the StackOverflow API.

        Args:
            api_url: The API URL to request.
            http_client: The HTTP client to use for the request.

        Returns:
            The HTTP response from the API.

        """
        return await http_client.get(api_url)

    def get_api_url(self, url: str) -> str:
        """Convert a StackOverflow web URL to an API endpoint URL.

        Args:
            url: The StackOverflow web URL to convert.

        Returns:
            The corresponding StackOverflow API endpoint URL.

        Raises:
            ValueError: If the URL format is invalid.

        """
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
        """Extract information from StackOverflow API response.

        Args:
            response: The HTTP response from the StackOverflow API.
            last_seen_dt: The datetime to compare against for new updates.

        Returns:
            Formatted string of updates, or None if no updates.

        Raises:
            StackOverflowExtractResponseError: If the response format is invalid.

        """
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
    """Client for interacting with the GitHub API."""

    BASE_URL = "https://api.github.com"
    API_NAME = "GitHub"
    GITHUB_TOKEN = scrapper_settings.github_token

    async def get_request(self, api_url: str, http_client: httpx.AsyncClient) -> httpx.Response:
        """Make an authenticated GET request to the GitHub API.

        Args:
            api_url: The API URL to request.
            http_client: The HTTP client to use for the request.

        Returns:
            The HTTP response from the API.

        """
        return await http_client.get(
            api_url,
            headers={"Authorization": f"Bearer {self.GITHUB_TOKEN}"},
        )

    def get_api_url(self, url: str) -> str:
        """Convert a GitHub web URL to an API endpoint URL.

        Args:
            url: The GitHub web URL to convert.

        Returns:
            The corresponding GitHub API endpoint URL.

        Raises:
            ValueError: If the URL format is invalid.

        """
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
        """Extract information from GitHub API response.

        Args:
            response: The HTTP response from the GitHub API.
            last_seen_dt: The datetime to compare against for new updates.

        Returns:
            Formatted string of updates.

        Raises:
            GitHubExtractResponseError: If the response format is invalid.
            StackOverflowExtractResponseError: If the response format is invalid
                                                (inherited from parent).

        """
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
