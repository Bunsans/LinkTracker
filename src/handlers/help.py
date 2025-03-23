from telethon.events import NewMessage

from src.handlers.handlers_settings import user_states
from src.utils import send_message_from_bot

__all__ = ("help_cmd_handler",)


async def help_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]
    await send_message_from_bot(
        event,
        """Помощь:
/chat_id --> текущий идентификатор чата
/start --> запустить бота
/help --> помощь
/untrack --> прекратить отслеживание ссылки
/list --> список отслеживаемых ссылок
/track --> начать отслеживание ссылки
Поддерживаемые форматы ссылок:
1. https://stackoverflow.com/questions/<номер_вопроса>
2. https://github.com/<владелец>/<название_репозитория>
        """,
    )
