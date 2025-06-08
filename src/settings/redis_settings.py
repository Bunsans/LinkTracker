import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379", description="URL подключения к Redis")
    ttl: int = Field(default=300, description="Время жизни кэша в секундах")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=False,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_prefix="APP_",
    )
