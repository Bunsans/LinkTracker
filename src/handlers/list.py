import httpx
from fastapi import status
from loguru import logger
from telethon.events import NewMessage

from src.dependencies import redis_service, redis_settings
from src.handlers.handlers_settings import api_settings, user_states
from src.schemas.schemas import ListLinksResponse
from src.utils.bot_utils import send_message_from_bot

__all__ = ("list_cmd_handler",)


async def list_cmd_handler(
    event: NewMessage.Event,
) -> None:

    if event.chat_id in user_states:
        del user_states[event.chat_id]

    # try get from cache
    cached_result = await redis_service.get_cached_list(event.chat_id)
    if cached_result:
        logger.info("Returning cached list")
        await send_message_from_bot(event, cached_result)
        return

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=api_settings.url_server + "/links",
            headers={"tg-chat-id": str(event.chat_id)},
        )
        if response.status_code == status.HTTP_200_OK:
            list_link_response = ListLinksResponse.model_validate_json(response.text)
            if not list_link_response.links:
                message = "Список ссылок пуст"
            else:
                message = "\n".join(
                    [
                        f"""Url: {link.link}
Tags: {', '.join(link.tags)}
Filters: {', '.join(link.filters)}\n"""
                        for link in list_link_response.links
                    ],
                )
                logger.debug(f"#####{message}#####")
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            message = "Чат не зарегистрирован, для регистрации введите /start"
        elif response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            message = f"Ошибка сервера:\n{response.text}"
        else:
            message = "Неизвестная ошибка"
    await redis_service.cache_list(chat_id=event.chat_id, items=message, ttl=redis_settings.ttl)
    await send_message_from_bot(event, message)
