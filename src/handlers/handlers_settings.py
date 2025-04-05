from dataclasses import dataclass
from typing import Dict, List

from src.settings import APIServerSettings

api_settings = APIServerSettings()


@dataclass
class State:
    state: str
    link: str | None = None
    tags: List[str] | None = None
    filters: List[str] | None = None


user_states: Dict[int, State] = {}
STATE_TRACK = "track"
STATE_TAGS = "tags"
STATE_FILTERS = "filters"
