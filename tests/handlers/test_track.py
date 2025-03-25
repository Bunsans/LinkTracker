from unittest.mock import MagicMock, Mock, patch

import pytest

from src.handlers.handlers_settings import (
    STATE_FILTERS,
    STATE_TAGS,
    STATE_TRACK,
    State,
    user_states,
)
from src.handlers.track import message_handler, track_cmd_handler


@pytest.mark.parametrize(
    ("message_text", "expected_state", "expected_message_reply"),
    [
        (
            "/track https://example.com",
            State(state=STATE_TAGS, link="https://example.com"),
            "Введите тэги (опционально):",
        ),
        (
            "/track",
            State(state=STATE_TRACK),
            "Введите ссылку для отслеживания:",
        ),
    ],
)
@pytest.mark.asyncio
async def test_track_cmd_handler_init_track(
    message_text: str,
    expected_state: State,
    expected_message_reply: str,
    mock_event: Mock,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        mock_event.raw_text = message_text
        await track_cmd_handler(mock_event)
        mock_event.client.send_message.assert_called_with(
            entity=mock_event.input_chat,
            message=expected_message_reply,
            reply_to=mock_event.message,
        )
        assert user_states[mock_event.chat_id] == expected_state


@pytest.mark.asyncio
async def test_message_handler_user_id_not_in_user_states(mock_event: Mock) -> None:
    user_states.clear()
    await message_handler(mock_event)
    mock_event.client.send_message.assert_called_with(
        entity=mock_event.input_chat,
        message="Не пон",
        reply_to=mock_event.message,
    )


@pytest.mark.asyncio
async def test_message_handler_user_state_track_add_link(mock_event: Mock) -> None:
    user_states[mock_event.chat_id] = State(state=STATE_TRACK)
    mock_event.raw_text = "https://example.com"
    await message_handler(mock_event)
    mock_event.client.send_message.assert_called_with(
        entity=mock_event.input_chat,
        message="Введите тэги (опционально):",
        reply_to=mock_event.message,
    )
    assert user_states[mock_event.chat_id] == State(state=STATE_TAGS, link="https://example.com")


@pytest.mark.asyncio
async def test_message_handler_user_state_tags_add_tags(mock_event: Mock) -> None:
    user_states[mock_event.chat_id] = State(state=STATE_TAGS, link="https://example.com")
    mock_event.raw_text = "tag1 tag2"
    await message_handler(mock_event)
    mock_event.client.send_message.assert_called_with(
        entity=mock_event.input_chat,
        message="Настройте фильтры (опционально):",
        reply_to=mock_event.message,
    )
    assert user_states[mock_event.chat_id] == State(
        state=STATE_FILTERS,
        link="https://example.com",
        tags=["tag1", "tag2"],
    )


@pytest.mark.asyncio
async def test_message_handler_user_state_filters_add_bad_link(mock_event: Mock) -> None:
    user_states[mock_event.chat_id] = State(
        state=STATE_FILTERS,
        link="https://example.com",
        tags=["tag1", "tag2"],
    )
    mock_event.raw_text = "filter1 filter2"
    await message_handler(mock_event)
    mock_event.client.send_message.assert_called_with(
        entity=mock_event.input_chat,
        message="Неверный формат для ссылки. Про форматы смотрите в /help",
        reply_to=mock_event.message,
    )
    assert mock_event.chat_id not in user_states


@pytest.mark.asyncio
async def test_message_handler_user_state_filters_add_good_link(mock_event: Mock) -> None:
    tags = ["tag1", "tag2"]
    link = "https://stackoverflow.com/questions/70633584"
    user_states[mock_event.chat_id] = State(state=STATE_FILTERS, link=link, tags=tags)
    mock_event.raw_text = "filter1 filter2"

    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        await message_handler(mock_event)
    filters = mock_event.raw_text.split()
    mock_event.client.send_message.assert_called_with(
        entity=mock_event.input_chat,
        message=f"Ссылка {link} добавлена с тэгами: {tags} и фильтрами: {filters}",
        reply_to=mock_event.message,
    )
    assert mock_event.chat_id not in user_states
