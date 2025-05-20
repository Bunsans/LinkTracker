import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.settings.constants import PREFIX_API


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
