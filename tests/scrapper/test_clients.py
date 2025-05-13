import pytest

from src.scrapper.clients import GitHubClient, StackOverflowClient
from src.settings import ScrapperSettings

scrapper_settings = ScrapperSettings()


@pytest.mark.parametrize(
    ("url", "expected_parsed_url"),
    [
        ("https://github.com/owner/repo", "https://api.github.com/repos/owner/repo/issues"),
        (
            "https://github.com/another_owner/another_repo",
            "https://api.github.com/repos/another_owner/another_repo/issues",
        ),
        ("https://github.com/user/project", "https://api.github.com/repos/user/project/issues"),
    ],
)
@pytest.mark.asyncio
async def test_github_client_parse_url(url: str, expected_parsed_url: str) -> None:
    client = GitHubClient()
    url_result = client.get_api_url(url)
    assert url_result == expected_parsed_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "https://invalid.url/owner/repo",
        "ftp://github.com/owner/repo",
        "https://github.com/",
        "https://github.com/owner",
    ],
)
@pytest.mark.asyncio
async def test_github_client_parse_invalid_url(invalid_url: str) -> None:
    client = GitHubClient()
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        client.get_api_url(invalid_url)


"""@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response_json", "expected_last_update"),
    [
        (
            {"updated_at": "2025-03-25T20:13:03Z"},
            datetime.fromisoformat("2025-03-25 20:13:03+00:00").replace(
                tzinfo=TIMEZONE,
            ),
        ),
    ],
)
@pytest.mark.asyncio
async def test_github_client_extract_last_update_good(
    response_json: dict[str, str],
    expected_last_update: datetime,
) -> None:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    update_client = GitHubClient()
    last_updated = update_client.extract_info(
        mock_response,
        last_seen_dt=datetime(year=2000, month=5, day=25, tzinfo=TIMEZONE),
    )
    assert last_updated == expected_last_update
"""

"""@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response_json", "expected_exception", "expected_exception_message"),
    [
        ({"updated": "2025-03-25T20:13:03Z"}, ValueError, "No updated_at in response"),
        (
            {"updated_at": "202"},
            ValueError,
            "time data {!r} does not match format {!r}".format("202", "%Y-%m-%dT%H:%M:%SZ"),
        ),
    ],
)
@pytest.mark.asyncio
async def test_github_client_extract_last_update_bad(
    response_json: dict[str, str],
    expected_exception: type[Exception],
    expected_exception_message: str,
) -> None:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    update_client = GitHubClient()
    with pytest.raises(expected_exception, match=expected_exception_message):
        update_client.extract_info(
            mock_response,
            last_seen_dt=datetime(year=2000, month=5, day=25, tzinfo=TIMEZONE),
        )
"""


@pytest.mark.parametrize(
    ("url", "expected_parsed_url"),
    [
        (
            "https://stackoverflow.com/questions/12345",
            f"https://api.stackexchange.com/2.3/questions/12345/{scrapper_settings.stack_query}",
        ),
        (
            "https://stackoverflow.com/questions/67890",
            f"https://api.stackexchange.com/2.3/questions/67890/{scrapper_settings.stack_query}",
        ),
        (
            "https://stackoverflow.com/questions/123",
            f"https://api.stackexchange.com/2.3/questions/123/{scrapper_settings.stack_query}",
        ),
    ],
)
@pytest.mark.asyncio
async def test_stackoverflow_client_parse_url(url: str, expected_parsed_url: str) -> None:
    client = StackOverflowClient()
    url_result = client.get_api_url(url)
    assert url_result == expected_parsed_url


@pytest.mark.parametrize(
    "invalid_url",
    [
        "https://stackoverflow.com/",
        "https://stackoverflow.com/users/12345",
        "https://invalid.url/questions/12345",
    ],
)
@pytest.mark.asyncio
async def test_stackoverflow_client_parse_invalid_url(invalid_url: str) -> None:
    client = StackOverflowClient()
    with pytest.raises(ValueError, match="Invalid StackOverflow URL format"):
        client.get_api_url(invalid_url)


"""
@pytest.mark.parametrize(
    ("response_json", "expected_last_update"),
    [
        (
            {
                "items": [{"last_activity_date": 1684908800}],
            },  # Unix timestamp for 2023-05-25 12:13:20 UTC
            datetime.fromtimestamp(1684908800, tz=TIMEZONE),
        ),
    ],
)
@pytest.mark.asyncio
async def test_stackoverflow_client_extract_last_update_good(
    response_json: dict[str, str],
    expected_last_update: datetime,
) -> None:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    update_client = StackOverflowClient()
    last_updated = update_client.extract_info(
        mock_response,
        last_seen_dt=datetime(year=2000, month=5, day=25, tzinfo=TIMEZONE),
    )
    assert last_updated == expected_last_update
"""

"""@pytest.mark.parametrize(
    ("response_json", "expected_exception", "expected_exception_message"),
    [
        ({}, ValueError, "No items in response"),
        ({"items": []}, ValueError, "No items in response"),
        (
            {"items": [{"date": 1684908800}]},
            ValueError,
            "No last_activity_date in response",
        ),
    ],
)
@pytest.mark.asyncio
async def test_stackoverflow_client_extract_last_update_bad(
    response_json: dict[str, str],
    expected_exception: type[Exception],
    expected_exception_message: str,
) -> None:
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = response_json
    update_client = StackOverflowClient()
    with pytest.raises(expected_exception, match=expected_exception_message):
        update_client.extract_info(
            mock_response,
            last_seen_dt=datetime(year=2000, month=5, day=25, tzinfo=TIMEZONE),
        )
"""
