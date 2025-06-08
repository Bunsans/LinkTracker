import httpx
from fastapi import status
from telethon.events import NewMessage

from src.handlers.handlers_settings import api_settings, user_states
from src.utils.bot_utils import send_message_from_bot

__all__ = ("start_cmd_handler",)


async def start_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=api_settings.url_server + f"/tg-chat/{event.chat_id}",
        )
        match response.status_code:
            case status.HTTP_200_OK:
                message = "Чат зарегистрирован!\nДля добавления ссылки введите /track"
            case status.HTTP_208_ALREADY_REPORTED:
                message = "Чат уже зарегистрирован\nДля добавления ссылки введите /track"
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                message = "Проблема на сервере"
            case status.HTTP_422_UNPROCESSABLE_ENTITY:
                message = "Ошибка валидации"
            case _:
                message = f"Неизвестная ошибка:{response.text}"
        await send_message_from_bot(event, message)
