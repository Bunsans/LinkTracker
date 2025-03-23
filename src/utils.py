from telethon.events import NewMessage


async def send_message_from_bot(event: NewMessage.Event, message: str) -> None:
    await event.client.send_message(
        entity=event.input_chat,
        message=message,
        reply_to=event.message,
    )
