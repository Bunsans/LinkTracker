import logging

from telethon.events import NewMessage

from src.data import user_states

__all__ = ("chat_id_cmd_handler",)
logger = logging.getLogger(__name__)


async def chat_id_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    logger.info(f"Chat ID: {event.chat_id}\n entity: {event.input_chat}")
    await event.client.send_message(
        entity=event.input_chat,
        message=f"chat_id is: {event.chat_id}",
        reply_to=event.message,
    )
