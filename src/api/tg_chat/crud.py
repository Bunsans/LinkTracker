from typing import Optional

from src.data import link_service


def is_chat_registrated(tg_chat_id: int) -> bool:
    return link_service.is_chat_registrated(tg_chat_id)


def register_chat(tg_chat_id: int) -> Optional[str]:
    """Зарегистрировать чат."""
    link_service.register_chat(tg_chat_id)
    return "Чат зарегистрирован"


def delete_chat(tg_chat_id: int) -> str:
    """Удалить чат."""
    link_service.delete_chat(tg_chat_id)
    return "Чат успешно удалён"
