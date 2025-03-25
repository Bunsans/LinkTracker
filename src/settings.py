import typing
from pathlib import Path

import pytz
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ("TGBotSettings", "APIServerSettings")

MIN_LEN_PATH_PARTS = 2
LEN_OF_PARTS_GITHUB_URL = 2
TIMEZONE = pytz.timezone("Europe/Moscow")
PREFIX_API = "/api/v1"


class TGBotSettings(BaseSettings):
    debug: bool = Field(default=False)

    api_id: int = Field(...)
    api_hash: str = Field(...)
    token: str = Field(...)

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="BOT_",
    )


class APIServerSettings(BaseSettings):
    debug: bool = Field(default=False)

    host_server: str = Field(default=...)
    port_server: int = Field(default=...)

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="API_",
    )

    @property
    def url_server(self) -> str:
        return f"http://{self.host_server}:{self.port_server}{self.prefix_server}"
