from unittest.mock import MagicMock, Mock, patch

import pytest

from src.handlers.is_chat_registrated import is_chat_registrated


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response_status", "expected_result"),
    [
        (401, False),  # Unauthorized, expect False
        (500, False),  # Internal server error, expect False
        (200, True),  # OK, expect True
    ],
)
async def test_track_cmd_handler(
    mock_event: Mock,
    response_status: int,
    expected_result: bool,
) -> None:
    mock_response = MagicMock()
    mock_response.status_code = response_status
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        result = await is_chat_registrated(mock_event)
    assert result is expected_result
