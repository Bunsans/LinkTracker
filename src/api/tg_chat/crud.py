from typing import Optional

from fastapi import HTTPException
from loguru import logger

from src.data import chat_id_links_mapper


def register_chat(tg_chat_id: int) -> Optional[str]:
    """Зарегистрировать чат."""
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id in chat_id_links_mapper:
        return "Чат уже зарегистрирован"
    else:
        chat_id_links_mapper[tg_chat_id] = []
        return "Чат зарегистрирован"


def delete_chat(tg_chat_id: int) -> str:
    """Удалить чат."""
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")

    if tg_chat_id not in chat_id_links_mapper:
        raise HTTPException(status_code=401, detail="Чат не зарегистрирован")

    del chat_id_links_mapper[tg_chat_id]
    return "Чат успешно удалён"
