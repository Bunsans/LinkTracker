from telethon import TelegramClient, events

from src.handlers import (
    chat_id_cmd_handler,
    help_cmd_handler,
    list_cmd_handler,
    message_handler,
    start_cmd_handler,
    track_cmd_handler,
    unknown_command_handler,
    untrack_cmd_handler,
)
from src.settings import TGBotSettings


def make_tg_client(settings: TGBotSettings) -> TelegramClient:
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
        ## TODO add check for commands not in list |^(\/[chat_id|start|track||untrack|help|list])\b
        events.NewMessage(pattern=r"^(?!\/)", incoming=True),
    )
    client.add_event_handler(
        untrack_cmd_handler,
        events.NewMessage(pattern="/untrack"),
    )
    client.add_event_handler(
        unknown_command_handler,
        events.NewMessage(pattern=r"^/(?!start|help|track|untrack|list|chat_id).*"),
    )
    return client
