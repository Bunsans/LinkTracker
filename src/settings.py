import typing
from pathlib import Path

import pytz
from pydantic import Field, PostgresDsn
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

    host_server: str = Field(default="0.0.0.0")
    port_server: int = Field(default=7777)
    prefix_server: str = Field(default=PREFIX_API)

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


class DBSettings(BaseSettings):
    url: PostgresDsn = Field(default=...)
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    # something for alembic
    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=True,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent / ".env",
        env_prefix="DB_",
    )


db_settings = DBSettings()  # type: ignore[attr-defined]
