import httpx
from telethon.events import NewMessage

from src.data import user_states

__all__ = ("untrack_cmd_handler",)


async def untrack_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    message = event.message.message
    ## TODO add validate links
    args = message.split()
    chat_id = event.chat_id
    if len(args) == 1:
        await event.client.send_message(
            entity=event.input_chat,
            message="Пожалуйста, введите ссылку от которой хотите отписаться(/untrack <ссылка>)",
            reply_to=event.message,
        )
        return
    else:
        link = args[1]
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url="http://0.0.0.0:7777/api/v1/links",
                headers={"id": str(chat_id)},
                params={"link": link},
            )
            print(f"######################\n{response.text}\n######################")

            if response.status_code == 200:
                await event.client.send_message(
                    entity=event.input_chat,
                    message=f"Вы прекратили следить за {link}",
                    reply_to=event.message,
                )
            else:
                await event.client.send_message(
                    entity=event.input_chat,
                    message=f"{response.text}",
                    reply_to=event.message,
                )
