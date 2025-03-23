from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi import status
from httpx import AsyncClient
from telethon import TelegramClient
from telethon.events import NewMessage

from src.api.links.schemas import AddLinkRequest, RemoveLinkRequest
from src.exceptions import LinkNotFoundError, NotRegistratedChatError
from src.handlers import chat_id_cmd_handler, track_cmd_handler, unknown_command_handler
from src.handlers.handlers_settings import STATE_TRACK, State
from src.handlers.help import help_cmd_handler
from src.handlers.list import list_cmd_handler
from src.handlers.track import message_handler
from src.handlers.untrack import untrack_cmd_handler

# @pytest.fixture(scope="session")
# def mock_event() -> Mock:
#     event = Mock(spec=NewMessage.Event)
#     event.input_chat = "test_chat"
#     event.chat_id = 123456789
#     event.message = MagicMock()
#     event.client = MagicMock(spec=TelegramClient)
#     return event


@pytest.fixture
def httpx_client_mock():
    client = MagicMock(spec=AsyncClient)
    return client


@pytest.mark.asyncio
async def test_chat_id_cmd_handler(mock_event):
    await chat_id_cmd_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message=f"chat_id is: {mock_event.chat_id}",
        reply_to=mock_event.message,
    )


@pytest.mark.asyncio
async def test_track_cmd_handler(mock_event, httpx_client_mock):
    mock_event.message.message = "/track https://example.com"
    with pytest.raises(NotRegistratedChatError):
        await track_cmd_handler(mock_event)


@pytest.mark.asyncio
async def test_unknown_command_handler(mock_event):
    mock_event.message.message = "/unknown_command"
    await unknown_command_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message="Не знаю такой команды(",
    )


@pytest.mark.asyncio
async def test_message_handler(mock_event):
    mock_event.message.raw_text = "https://example.com"
    user_states[mock_event.chat_id] = State(state=STATE_TRACK)
    await message_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message="Введите тэги (опционально):",
    )


@pytest.mark.asyncio
async def test_untrack_cmd_handler(mock_event, httpx_client_mock):
    mock_event.message.message = "/untrack https://example.com"
    httpx_client_mock.delete.return_value.status_code = status.HTTP_200_OK
    await untrack_cmd_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message="Вы прекратили следить за https://example.com",
    )


@pytest.mark.asyncio
async def test_list_cmd_handler(mock_event, httpx_client_mock):
    httpx_client_mock.get.return_value.status_code = status.HTTP_200_OK
    httpx_client_mock.get.return_value.text = '{"links": []}'
    await list_cmd_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message="Список ссылок пуст",
    )


@pytest.mark.asyncio
async def test_help_cmd_handler(mock_event):
    await help_cmd_handler(mock_event)
    mock_event.client.send_message.assert_called_once_with(
        entity=mock_event.input_chat,
        message="""Помощь:
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
