from typing import List
from urllib.parse import urlparse

import validators
from pydantic import BaseModel, field_validator


def _validate_link(http_url: str):
    if not validators.url(http_url):
        raise ValueError("The URL is not valid")
    parsed_url = urlparse(http_url)
    netloc = parsed_url.netloc
    path_parts = parsed_url.path.strip("/").split("/")
    if "github.com" in netloc:
        if len(path_parts) < 2 or not path_parts[0] or not path_parts[1]:
            raise ValueError("GitHub URL must contain both owner and repo")
    elif "stackoverflow.com" in netloc:
        if "questions" not in path_parts or not path_parts[-1].isdigit():
            raise ValueError("StackOverflow URL must contain a question number")
    else:
        raise ValueError("The URL must point to either GitHub or StackOverflow")
    return http_url


class LinkResponse(BaseModel):
    id: int
    link: str
    tags: List[str]
    filters: List[str]

    @field_validator("link")
    def validate_link(cls, http_url: str):
        return _validate_link(http_url)


class ApiErrorResponse(BaseModel):
    description: str
    code: str
    exceptionName: str
    exceptionMessage: str
    stacktrace: List[str]


class AddLinkRequest(BaseModel):
    link: str
    tags: List[str]
    filters: List[str]

    @field_validator("link")
    def validate_link(cls, http_url: str):
        return _validate_link(http_url)


class ListLinksResponse(BaseModel):
    links: List[LinkResponse]
    size: int


class RemoveLinkRequest(BaseModel):
    link: str

    @field_validator("link")
    def validate_link(cls, http_url: str):
        return _validate_link(http_url)


class LinkUpdate(BaseModel):
    id: int
    link: str
    description: str
    tg_chat_ids: List[int]

    @field_validator("link")
    def validate_link(cls, http_url: str):
        return _validate_link(http_url)
