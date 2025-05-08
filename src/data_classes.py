from urllib.parse import urlparse

import validators
from pydantic import BaseModel, Field

from src.settings import MIN_LEN_PATH_PARTS


def _validate_link(http_url: str) -> str:
    if not validators.url(http_url):
        raise ValueError("The URL is not valid")
    parsed_url = urlparse(http_url)
    netloc = parsed_url.netloc
    path_parts = parsed_url.path.strip("/").split("/")
    if "github.com" in netloc:
        if len(path_parts) < MIN_LEN_PATH_PARTS or not path_parts[0] or not path_parts[1]:
            raise ValueError("GitHub URL must contain both owner and repo")
    elif "stackoverflow.com" in netloc:
        if "questions" not in path_parts or not path_parts[-1].isdigit():
            raise ValueError("StackOverflow URL must contain a question number")
    else:
        raise ValueError("The URL must point to either GitHub or StackOverflow")
    return http_url


class LinkUpdate(BaseModel):
    id: int
    link: str
    description: str = Field(
        description="Message to users of update in link or error while scrapping",
    )
    tg_chat_ids: list[int]
