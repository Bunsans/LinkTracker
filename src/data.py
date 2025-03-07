from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class State:
    state: str
    link: str | None = None
    tags: List[str] | None = None
    filters: List[str] | None = None


STATE_TRACK = "track"
STATE_TAGS = "tags"
STATE_FILTERS = "filters"

user_states: Dict[int, State] = {}


chat_id_links_mapper: Dict[int, List[Any]] = {}

links_chat_id_mapper: Dict[str, set[int]] = {}
