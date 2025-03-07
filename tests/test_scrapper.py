
import httpx
import pytest

from src.scrapper import GitHubClient


@pytest.mark.parametrize(
    ("url", "expected_owner", "expected_repo"),
    [
        ("https://github.com/owner/repo", "owner", "repo"),
        ("https://github.com/another_owner/another_repo", "another_owner", "another_repo"),
        ("https://github.com/user/project", "user", "project"),
    ],
)
@pytest.mark.asyncio
async def test_github_client_parse_url(url: str, expected_owner: str, expected_repo: str) -> None:
    client = GitHubClient(client=httpx.AsyncClient())
    owner, repo = client.parse_url(url)
    assert owner == expected_owner
    assert repo == expected_repo


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
    client = GitHubClient(client=httpx.AsyncClient())
    with pytest.raises(ValueError, match="Invalid GitHub URL format"):
        _, _ = client.parse_url(invalid_url)


"""
@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_github_client_get_repo_last_updated(mock_get: MagicMock) -> None:
    mock_response = AsyncMock()
    mock_response.json.return_value = {"updated_at": "2023-10-01T12:34:56Z"}
    mock_get.return_value = mock_response

    client = GitHubClient(client=httpx.AsyncClient())
    last_updated = await client.get_repo_last_updated("https://github.com/owner/repo")
    assert last_updated == datetime.fromisoformat("2023-10-01T12:34:56+00:00")
"""

"""
@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_stackoverflow_client_get_question_last_updated(mock_get: MagicMock) -> None:
    mock_response = AsyncMock()
    mock_response.json.return_value = {"items": [{"last_activity_date": "2023-10-01T12:34:56Z"}]}
    mock_get.return_value = mock_response

    client = StackOverflowClient(client=httpx.AsyncClient())
    last_updated = await client.get_question_last_updated(123456)
    assert last_updated == datetime.fromisoformat("2023-10-01T12:34:56+00:00").replace(
        tzinfo=TIMEZONE,
    )


def test_check_type() -> None:
    assert check_type("https://github.com/owner/repo") == "github"
    assert check_type("https://stackoverflow.com/questions/123456") == "stackoverflow"
    assert check_type("https://invalid.url") is None
"""
