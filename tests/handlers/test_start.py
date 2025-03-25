from unittest.mock import MagicMock, Mock, patch

import pytest

from src.handlers.handlers_settings import (
    STATE_FILTERS,
    STATE_TAGS,
    STATE_TRACK,
    State,
    user_states,
)
from src.handlers.start import start_cmd_handler


@pytest.mark.parametrize(
    ("init_state", "expected_message_reply", "response_code"),
    [
        (
            State(state=STATE_TRACK),
            "Чат зарегистрирован!\nДля добавления ссылки введите /track",
            200,
        ),
        (
            State(state=STATE_TAGS, link="https://example.com"),
            "Чат уже зарегистрирован\nДля добавления ссылки введите /track",
            208,
        ),
        (
            State(state=STATE_TAGS, link="https://example.com"),
            "Ошибка валидации",
            422,
        ),
        (
            State(state=STATE_FILTERS, link="https://example.com", tags=["tag1", "tag2"]),
            "Проблема на сервере",
            500,
        ),
    ],
)
@pytest.mark.asyncio
async def test_untrack_cmd_handler(
    init_state: State,
    expected_message_reply: str,
    response_code: int,
    mock_event: Mock,
) -> None:
    user_states[mock_event.chat_id] = init_state

    mock_response = MagicMock()
    mock_response.status_code = response_code

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        await start_cmd_handler(mock_event)
        mock_event.client.send_message.assert_called_with(
            entity=mock_event.input_chat,
            message=expected_message_reply,
            reply_to=mock_event.message,
        )
        assert mock_event.chat_id not in user_states
