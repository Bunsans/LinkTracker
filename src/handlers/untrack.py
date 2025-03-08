import httpx
from loguru import logger
from telethon.events import NewMessage

from src.constants import ResponseCode
from src.data import user_states
from src.utils import not_registrated, send_message_from_bot

__all__ = ("untrack_cmd_handler",)


async def untrack_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    if await not_registrated(event):
        return
    message = event.message.message
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
                url="http://0.0.0.0:7777/api/v1/links",
                headers={"tg-chat-id": str(chat_id)},
                params={"link": link},
            )
            status_code = response.status_code
            match status_code:
                case ResponseCode.SUCCESS.value:
                    message = f"Вы прекратили следить за {link}"
                case ResponseCode.VALIDATION_ERROR.value:
                    message = "Неверный формат для ссылки. Про форматы смотрите в /help"
                case ResponseCode.NOT_FOUND.value:
                    message = """Ссылка не найдена. Проверьте правильность введенной ссылки.
Список имеющихся ссылок можно посмотреть в /list"""
                case _:
                    message = f"{response.text}"

            logger.debug(f"message {message}")
            await send_message_from_bot(event, message)
