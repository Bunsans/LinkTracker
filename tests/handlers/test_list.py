from unittest.mock import MagicMock, Mock, patch

import pytest

from src.handlers.handlers_settings import (
    STATE_FILTERS,
    STATE_TAGS,
    STATE_TRACK,
    State,
    user_states,
)
from src.handlers.list import list_cmd_handler


@pytest.mark.parametrize(
    ("init_state", "expected_message_reply", "response_text", "response_code"),
    [
        (
            State(state=STATE_TAGS, link="https://example.com"),
            "Ошибка сервера:\nошибка",
            "ошибка",
            500,
        ),
        (
            State(state=STATE_FILTERS, link="https://example.com", tags=["tag1", "tag2"]),
            "Чат не зарегистрирован, для регистрации введите /start",
            "",
            401,
        ),
        (
            State(state=STATE_TAGS, link="https://example.com"),
            "Список ссылок пуст",
            """
{
    "links": [],
    "size": 0
}
""",
            200,
        ),
        (
            State(state=STATE_TRACK),
            """Url: https://github.com/user/repo
Tags: python, web
Filters: github

Url: https://stackoverflow.com/questions/1234567
Tags: python, error
Filters: stackoverflow, aboba
""",
            """
{
    "links": [
        {
            "id": 1,
            "link": "https://github.com/user/repo",
            "tags": ["python", "web"],
            "filters": ["github"]
        },
        {
            "id": 2,
            "link": "https://stackoverflow.com/questions/1234567",
            "tags": ["python", "error"],
            "filters": ["stackoverflow", "aboba"]
        }
    ],
    "size": 2
}
""",
            200,
        ),
    ],
)
@pytest.mark.asyncio
async def test_list_cmd_handler(
    init_state: State,
    expected_message_reply: str,
    response_text: str,
    response_code: int,
    mock_event: Mock,
) -> None:
    user_states[mock_event.chat_id] = init_state

    mock_response = MagicMock()
    mock_response.status_code = response_code
    mock_response.text = response_text
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        await list_cmd_handler(mock_event)
        mock_event.client.send_message.assert_called_with(
            entity=mock_event.input_chat,
            message=expected_message_reply,
            reply_to=mock_event.message,
        )
        assert mock_event.chat_id not in user_states
