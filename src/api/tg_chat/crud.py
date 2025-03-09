from typing import Optional

from loguru import logger

from src.data import chat_id_links_mapper
from src.exceptions import NotRegistratedChat
from src.exceptions.exceptions import EntityAlreadyExistsError


def is_registered_chat(tg_chat_id: int) -> None:
    """Зарегистрировать чат."""
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id in chat_id_links_mapper:
        return
    raise NotRegistratedChat(message="Not registrated chat. While checking registration")


def register_chat(tg_chat_id: int) -> Optional[str]:
    """Зарегистрировать чат."""
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id in chat_id_links_mapper:
        raise EntityAlreadyExistsError(message="Chat already registered. While registering chat")
    chat_id_links_mapper[tg_chat_id] = []
    return "Чат зарегистрирован"


def delete_chat(tg_chat_id: int) -> str:
    """Удалить чат."""
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id not in chat_id_links_mapper:
        raise NotRegistratedChat(message="Not registrated chat. While deleting chat")
    del chat_id_links_mapper[tg_chat_id]
    return "Чат успешно удалён"
