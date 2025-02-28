import httpx
from loguru import logger
from telethon.events import NewMessage

from src.data import user_states

__all__ = ("start_cmd_handler",)


async def start_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f"http://0.0.0.0:7777/api/v1/tg-chat/{event.chat_id}",
        )
        if response.status_code == 200:
            message = "Чат зарегистрирован!\nДля добавления ссылки введите /track"
        elif response.status_code == 500:
            message = "Проблема на сервере"
        elif response.status_code == 422:
            message = "Ошибка"
        await event.client.send_message(
            entity=event.input_chat,
            message=message,
            reply_to=event.message,
        )
