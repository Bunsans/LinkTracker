import httpx
from fastapi import status
from telethon.events import NewMessage

from src.handlers.handlers_settings import api_settings
from src.utils.bot_utils import send_message_from_bot


async def is_chat_registrated(event: NewMessage.Event) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=api_settings.url_server + f"/tg-chat/{event.chat_id}",
        )
        match response.status_code:
            case status.HTTP_401_UNAUTHORIZED:
                message_auth = "Чат не зарегистрирован, для регистрации введите /start"
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                message_auth = f"Ошибка сервера:\n{response.text}"
            case _:
                message_auth = ""
        if message_auth:
            await send_message_from_bot(event, message_auth)
            return False
        return True
