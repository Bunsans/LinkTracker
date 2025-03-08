import httpx
from telethon.events import NewMessage

from src.constants import ResponseCode


async def send_message_from_bot(event: NewMessage.Event, message: str) -> None:
    await event.client.send_message(
        entity=event.input_chat,
        message=message,
        reply_to=event.message,
    )


async def not_registrated(event: NewMessage.Event) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f"http://0.0.0.0:7777/api/v1/tg-chat/{event.chat_id}",
        )
        match response.status_code:
            case ResponseCode.UNAUTHORIZED.value:
                message_auth = "Чат не зарегистрирован, для регистрации введите /start"
            case ResponseCode.SERVER_ERROR.value:
                message_auth = f"Ошибка сервера:\n{response.text}"
            case _:
                message_auth = ""
        if message_auth:
            await send_message_from_bot(event, message_auth)
            return True
        return False
