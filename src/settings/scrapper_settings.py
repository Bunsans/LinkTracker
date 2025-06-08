import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.constants import BATCH_SIZE, BODY_MAX_LEN, TITLE_MAX_LEN


class ScrapperSettings(BaseSettings):
    stack_query: str = Field(default="?order=desc&sort=activity&site=stackoverflow&filter=withbody")
    github_token: str | None = Field(default=None)
    batch_size: int = Field(default=BATCH_SIZE)
    body_max_len: int = Field(default=BODY_MAX_LEN)
    title_max_len: int = Field(default=TITLE_MAX_LEN)

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="SCRAPPER_",
    )
