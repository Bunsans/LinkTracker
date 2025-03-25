from unittest.mock import MagicMock, Mock, patch

import pytest

from src.handlers.handlers_settings import (
    STATE_FILTERS,
    STATE_TAGS,
    STATE_TRACK,
    State,
    user_states,
)
from src.handlers.untrack import untrack_cmd_handler


@pytest.mark.parametrize(
    ("message_text", "init_state", "expected_message_reply", "response_code"),
    [
        (
            "/untrack",
            State(state=STATE_TRACK),
            """Пожалуйста, введите ссылку от которой хотите отписаться
(/untrack <ссылка>)""",
            1,
        ),
        (
            "/untrack https://example.com",
            State(state=STATE_TAGS, link="https://example.com"),
            "Неверный формат для ссылки. Про форматы смотрите в /help",
            422,
        ),
        (
            "/untrack https://stackoverflow.com/questions/70633584",
            State(state=STATE_FILTERS, link="https://example.com", tags=["tag1", "tag2"]),
            """Ссылка не найдена. Проверьте правильность введенной ссылки.
Список имеющихся ссылок можно посмотреть в /list""",
            404,
        ),
        (
            "/untrack https://stackoverflow.com/questions/70633584",
            State(state=STATE_TAGS, link="https://example.com"),
            "Вы прекратили следить за https://stackoverflow.com/questions/70633584",
            200,
        ),
    ],
)
@pytest.mark.asyncio
async def test_untrack_cmd_handler(
    message_text: str,
    init_state: State,
    expected_message_reply: str,
    response_code: int,
    mock_event: Mock,
) -> None:
    user_states[mock_event.chat_id] = init_state
    mock_event.raw_text = message_text

    mock_response = MagicMock()
    mock_response.status_code = response_code

    mock_response_for_is_chat_registrated = MagicMock()
    mock_response_for_is_chat_registrated.status_code = 200
    with (
        patch("httpx.AsyncClient.get", return_value=mock_response_for_is_chat_registrated),
        patch("httpx.AsyncClient.delete", return_value=mock_response),
    ):
        await untrack_cmd_handler(mock_event)
        mock_event.client.send_message.assert_called_with(
            entity=mock_event.input_chat,
            message=expected_message_reply,
            reply_to=mock_event.message,
        )
        assert mock_event.chat_id not in user_states
