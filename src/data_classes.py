from urllib.parse import urlparse

import validators
from pydantic import BaseModel, Field

from src.settings import MIN_LEN_PATH_PARTS


class LinkUpdate(BaseModel):
    id: int
    link: str
    description: str = Field(
        description="Message to users of update in link or error while scrapping",
    )
    tg_chat_ids: list[int]
