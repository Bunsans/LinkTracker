from pydantic import BaseModel, Field


class LinkUpdate(BaseModel):
    id: int
    link: str
    description: str = Field(
        description="Message to users of update in link or error while scrapping",
    )
    tg_chat_ids: list[int]
