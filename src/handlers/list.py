import httpx
from telethon.events import NewMessage

from src.data import user_states
from src.data_classes import ListLinksResponse

__all__ = ("list_cmd_handler",)


async def list_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url="http://0.0.0.0:7777/api/v1/links",
            headers={"id": str(event.chat_id)},
        )
        if response.status_code == 200:
            list_link_response = ListLinksResponse.model_validate_json(response.text)
            if not list_link_response.links:
                message = "Список ссылок пуст"
            else:
                message = "\n".join(
                    [
                        f"Url: {link.link}\nTags: {link.tags}\nFilters: {link.filters}\n"
                        for link in list_link_response.links
                    ]
                )
        elif response.status_code == 401:
            message = "Чат не зарегистрирован, для регистрации введите /start"
        elif response.status_code == 500:
            message = f"Ошибка сервера:\n{response.text}"
        else:
            message = "Неизвестная ошибка"
    await event.client.send_message(
        entity=event.input_chat,
        message=message,
        reply_to=event.message,
    )
