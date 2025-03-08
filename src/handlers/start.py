import httpx
from telethon.events import NewMessage

from src.constants import ResponseCode
from src.data import user_states
from src.utils import send_message_from_bot

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
        match response.status_code:
            case ResponseCode.SUCCESS.value:
                message = "Чат зарегистрирован!\nДля добавления ссылки введите /track"
            case ResponseCode.ALREADY_REPORTED.value:
                message = "Чат уже зарегистрирован\nДля добавления ссылки введите /track"
            case ResponseCode.SERVER_ERROR.value:
                message = "Проблема на сервере"
            case ResponseCode.VALIDATION_ERROR.value:
                message = "Ошибка валидации"
            case _:
                message = f"Неизвестная ошибка:{response.text}"
        await send_message_from_bot(event, message)
