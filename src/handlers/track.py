import httpx
from fastapi import status
from loguru import logger
from telethon.events import NewMessage

from src.dependencies import redis_service
from src.handlers.handlers_settings import (
    STATE_FILTERS,
    STATE_TAGS,
    STATE_TRACK,
    State,
    api_settings,
    user_states,
)
from src.handlers.is_chat_registrated import is_chat_registrated
from src.schemas.schemas import AddLinkRequest
from src.utils.bot_utils import send_message_from_bot

__all__ = ("track_cmd_handler", "message_handler")


async def track_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if not await is_chat_registrated(event):
        return
    message = event.raw_text
    args = message.split()
    user_id = event.chat_id

    if len(args) > 1:
        link = args[1]
        user_states[user_id] = State(state=STATE_TAGS, link=link)
        await send_message_from_bot(event, "Введите тэги (опционально):")
    else:
        user_states[user_id] = State(state=STATE_TRACK)
        await send_message_from_bot(event, "Введите ссылку для отслеживания:")


async def unknown_command_handler(event: NewMessage.Event) -> None:
    await send_message_from_bot(event, "Не знаю такой команды(")


async def message_handler(event: NewMessage.Event) -> None:
    logger.debug(f"user_states: {user_states}")
    user_id = event.chat_id
    if user_id not in user_states:
        await send_message_from_bot(event, "Не пон")
        return

    current_state = user_states[user_id]

    if current_state.state == STATE_TRACK:
        link = event.raw_text
        user_states[user_id] = State(state=STATE_TAGS, link=link)
        await send_message_from_bot(event, "Введите тэги (опционально):")

    elif current_state.state == STATE_TAGS:
        link = current_state.link
        tags = event.raw_text.split()
        user_states[user_id] = State(STATE_FILTERS, link, tags)
        await send_message_from_bot(event, "Настройте фильтры (опционально):")
    elif current_state.state == STATE_FILTERS:
        link, tags = current_state.link, current_state.tags
        filters = event.raw_text.split()
        try:
            body = AddLinkRequest(link=link, tags=tags, filters=filters)
        except ValueError:
            await send_message_from_bot(
                event,
                "Неверный формат для ссылки. Про форматы смотрите в /help",
            )
            del user_states[user_id]
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=api_settings.url_server + "/links",
                headers={"tg-chat-id": str(event.chat_id)},
                json=body.model_dump(),
            )
            match response.status_code:
                case status.HTTP_200_OK:
                    message = f"Ссылка {link} добавлена с тэгами: {tags} и фильтрами: {filters}"
                    await redis_service.invalidate_cache(event.chat_id)
                case status.HTTP_401_UNAUTHORIZED:
                    message = "Чат не зарегистрирован, для регистрации введите /start"
                case _:
                    message = response.text
            await send_message_from_bot(event, message)

            del user_states[user_id]
