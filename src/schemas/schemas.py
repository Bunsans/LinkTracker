from urllib.parse import urlparse

import validators
from pydantic import BaseModel, field_validator

from src.settings import MIN_LEN_PATH_PARTS, MIN_LEN_PATH_PARTS_STACKOVERFLOW


def _validate_link(http_url: str) -> str:
    if not validators.url(http_url):
        raise ValueError("The URL is not valid")
    parsed_url = urlparse(http_url)
    netloc = parsed_url.netloc
    path_parts = parsed_url.path.strip("/").split("/")
    if "github.com" in netloc:
        if (
            len(path_parts) < MIN_LEN_PATH_PARTS - 1
            or not path_parts[0]
            or not path_parts[1]
            or len(path_parts) > MIN_LEN_PATH_PARTS
        ):
            raise ValueError("GitHub URL must contain both owner and repo")
        if len(path_parts) == MIN_LEN_PATH_PARTS and path_parts[2] not in ["issues", "pull"]:
            raise ValueError("GitHub URL must contain either issues or pull")

    elif "stackoverflow.com" in netloc:
        if len(path_parts) != MIN_LEN_PATH_PARTS_STACKOVERFLOW:
            raise ValueError("StackOverflow URL must contain a question number")
        if "questions" not in path_parts or not path_parts[-1].isdigit():
            raise ValueError("StackOverflow URL must contain a question number")
    else:
        raise ValueError("The URL must point to either GitHub or StackOverflow")
    return http_url


class LinkResponse(BaseModel):
    id: int
    link: str
    tags: list[str]
    filters: list[str]

    @field_validator("link", mode="before")
    @classmethod
    def validate_link(cls, http_url: str) -> str:
        return _validate_link(http_url)


class ApiErrorResponse(BaseModel):
    description: str
    code: str
    exception_name: str
    exception_message: str
    stacktrace: list[str]


class AddLinkRequest(BaseModel):
    link: str
    tags: list[str]
    filters: list[str]

    @field_validator("link", mode="before")
    @classmethod
    def validate_link(cls, http_url: str) -> str:
        return _validate_link(http_url)


class ListLinksResponse(BaseModel):
    links: list[LinkResponse]
    size: int


class RemoveLinkRequest(BaseModel):
    link: str

    @field_validator("link", mode="before")
    @classmethod
    def validate_link(cls, http_url: str) -> str:
        return _validate_link(http_url)


class LinkUpdate(BaseModel):
    id: int
    link: str
    description: str
    tg_chat_ids: list[int]

    @field_validator("link", mode="before")
    @classmethod
    def validate_link(cls, http_url: str) -> str:
        return _validate_link(http_url)
