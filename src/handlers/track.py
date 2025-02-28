import httpx
from loguru import logger
from telethon.events import NewMessage

from src.data import STATE_FILTERS, STATE_TAGS, STATE_TRACK, State, user_states
from src.data_classes import AddLinkRequest

__all__ = ("track_cmd_handler", "message_handler")


async def track_cmd_handler(
    event: NewMessage.Event,
) -> None:
    message = event.message.message
    ## TODO add validate links
    args = message.split()
    user_id = event.chat_id

    if len(args) > 1:
        await event.client.send_message(
            entity=event.input_chat,
            message="Введите тэги (опционально):",
            reply_to=event.message,
        )
        link = args[1]
        user_states[user_id] = State(state=STATE_TAGS, link=link)
    else:
        await event.client.send_message(
            entity=event.input_chat,
            message="Введите ссылку для отслеживания:",
            reply_to=event.message,
        )
        user_states[user_id] = State(state=STATE_TRACK)


async def message_handler(event: NewMessage.Event):
    logger.debug(f"user_states: {user_states}")
    user_id = event.chat_id
    if user_id not in user_states:
        await event.client.send_message(
            entity=event.input_chat,
            message="Не пон",
            reply_to=event.message,
        )
        return

    current_state = user_states[user_id]

    if current_state.state == STATE_TRACK:
        link = event.raw_text
        ## TODO add validate links
        user_states[user_id] = State(state=STATE_TAGS, link=link)
        await event.client.send_message(
            entity=event.input_chat,
            message="Введите тэги (опционально):",
            reply_to=event.message,
        )

    elif current_state.state == STATE_TAGS:
        link = current_state.link
        tags = event.raw_text.split()
        ## TODO add validate tags
        user_states[user_id] = State(STATE_FILTERS, link, tags)
        await event.client.send_message(
            entity=event.input_chat,
            message="Настройте фильтры (опционально):",
            reply_to=event.message,
        )
    elif current_state.state == STATE_FILTERS:
        link, tags = current_state.link, current_state.tags
        filters = event.raw_text.split()
        ## TODO add validate filters
        try:
            body = AddLinkRequest(link=link, tags=tags, filters=filters)
        except ValueError:
            await event.client.send_message(
                entity=event.input_chat,
                message="Скорее всего ссылка не поддерживается, попробуйте изменить ее",
                reply_to=event.message,
            )
            del user_states[user_id]
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url="http://0.0.0.0:7777/api/v1/links",
                headers={"id": str(event.chat_id)},
                json=body.model_dump(),
            )
            if response.status_code == 200:
                message = f"Ссылка {link} добавлена с тэгами: {tags} и фильтрами: {filters}"
            elif response.status_code == 400:
                message = "ошибка при добавлении ссылки"
            elif response.status_code == 401:
                message = "Чат не зарегистрирован, для регистрации введите /start"
            else:
                message = response.text

            await event.client.send_message(
                entity=event.input_chat,
                message=message,
                reply_to=event.message,
            )

            del user_states[user_id]
