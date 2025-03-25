import httpx
from fastapi import status
from loguru import logger
from telethon.events import NewMessage

from src.handlers.handlers_settings import api_settings, user_states
from src.handlers.is_chat_registrated import is_chat_registrated
from src.utils import send_message_from_bot

__all__ = ("untrack_cmd_handler",)


async def untrack_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    if not await is_chat_registrated(event):
        return
    message = event.raw_text
    args = message.split()
    chat_id = event.chat_id
    if len(args) == 1:
        await send_message_from_bot(
            event,
            """Пожалуйста, введите ссылку от которой хотите отписаться
(/untrack <ссылка>)""",
        )
        return
    else:
        link = args[1]
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url=api_settings.url_server + "/links",
                headers={"tg-chat-id": str(chat_id)},
                params={"link": link},
            )
            status_code = response.status_code
            match status_code:
                case status.HTTP_200_OK:
                    message = f"Вы прекратили следить за {link}"
                case status.HTTP_422_UNPROCESSABLE_ENTITY:
                    message = "Неверный формат для ссылки. Про форматы смотрите в /help"
                case status.HTTP_404_NOT_FOUND:
                    message = """Ссылка не найдена. Проверьте правильность введенной ссылки.
Список имеющихся ссылок можно посмотреть в /list"""
                case _:
                    message = f"{response.text}"

            logger.debug(f"message {message}")
            await send_message_from_bot(event, message)
