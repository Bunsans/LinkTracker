from dataclasses import dataclass

from src.settings import APIServerSettings

api_settings = APIServerSettings()


@dataclass
class State:
    state: str
    link: str | None = None
    tags: list[str] | None = None
    filters: list[str] | None = None


user_states: dict[int, State] = {}
STATE_TRACK = "track"
STATE_TAGS = "tags"
STATE_FILTERS = "filters"
