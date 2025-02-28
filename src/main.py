import asyncio
import logging

from telethon import TelegramClient, events
from telethon.events import NewMessage

__all__ = ("track_cmd_handler",)


from src.handlers import (
    chat_id_cmd_handler,
    help_cmd_handler,
    list_cmd_handler,
    message_handler,
    start_cmd_handler,
    track_cmd_handler,
    untrack_cmd_handler,
)
from src.settings import TGBotSettings

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


settings = TGBotSettings()  # type: ignore[call-arg]

client = TelegramClient("bot_session", settings.api_id, settings.api_hash).start(
    bot_token=settings.token,
)


client.add_event_handler(
    chat_id_cmd_handler,
    events.NewMessage(pattern="/chat_id"),
)
client.add_event_handler(
    start_cmd_handler,
    events.NewMessage(pattern="/start"),
)
client.add_event_handler(
    help_cmd_handler,
    events.NewMessage(pattern="/help"),
)
client.add_event_handler(
    list_cmd_handler,
    events.NewMessage(pattern="/list"),
)
client.add_event_handler(
    track_cmd_handler,
    events.NewMessage(pattern="/track"),
)
client.add_event_handler(
    message_handler,
    events.NewMessage(pattern=r"^(?!\/)", incoming=True),
)
client.add_event_handler(
    untrack_cmd_handler,
    events.NewMessage(pattern="/untrack"),
)


async def dummy_func() -> None:
    await asyncio.sleep(1)


async def main() -> None:
    while True:
        await asyncio.gather(
            asyncio.create_task(dummy_func()),
        )


# Run the event loop to start receiving messages
logger.info("Run the event loop to start receiving messages")

with client:
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logger.exception(
            "Main loop raised error.",
            extra={"exc": exc},
        )
