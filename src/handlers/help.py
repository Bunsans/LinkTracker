from telethon.events import NewMessage

from src.data import user_states

__all__ = ("help_cmd_handler",)


async def help_cmd_handler(
    event: NewMessage.Event,
) -> None:
    if event.chat_id in user_states:
        del user_states[event.chat_id]

    await event.client.send_message(
        entity=event.input_chat,
        message="""Help:
/chat_id --> current chat id
/start --> start bot
/help --> help
/track --> begin tracking url
    Possible format of links:
        1. https://stackoverflow.com/questions/<number_of_question>
        2. https://github.com/<owner>/<name_of_repo>
/untrack --> stop tracking url
/list --> list of tracked urls
        """,
        reply_to=event.message,
    )
