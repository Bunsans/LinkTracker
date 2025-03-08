import httpx
from telethon.events import NewMessage

from src.api.links.schemas import ListLinksResponse
from src.constants import ResponseCode
from src.data import user_states
from src.utils import send_message_from_bot

__all__ = ("list_cmd_handler",)


async def list_cmd_handler(
    event: NewMessage.Event,
) -> None:

    if event.chat_id in user_states:
        del user_states[event.chat_id]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url="http://0.0.0.0:7777/api/v1/links",
            headers={"tg-chat-id": str(event.chat_id)},
        )
        if response.status_code == ResponseCode.SUCCESS.value:
            list_link_response = ListLinksResponse.model_validate_json(response.text)
            if not list_link_response.links:
                message = "Список ссылок пуст"
            else:
                message = "\n".join(
                    [
                        f"Url: {link.link}\nTags: {link.tags}\nFilters: {link.filters}\n"
                        for link in list_link_response.links
                    ],
                )
        elif response.status_code == ResponseCode.UNAUTHORIZED.value:
            message = "Чат не зарегистрирован, для регистрации введите /start"
        elif response.status_code == ResponseCode.SERVER_ERROR.value:
            message = f"Ошибка сервера:\n{response.text}"
        else:
            message = "Неизвестная ошибка"
    await send_message_from_bot(event, message)
