import pytest

from src.data_classes import (
    AddLinkRequest,
    ApiErrorResponse,
    LinkResponse,
    LinkUpdate,
    ListLinksResponse,
    RemoveLinkRequest,
    _validate_link,
)


@pytest.mark.parametrize(
    "valid_url", ["https://github.com/owner/repo", "https://stackoverflow.com/questions/123456"]
)
def test_validate_link_valid(valid_url):
    assert _validate_link(valid_url) == valid_url


@pytest.mark.parametrize(
    "invalid_url,expected_message",
    [
        ("https://github.com/owner", "GitHub URL must contain both owner and repo"),
        (
            "https://stackoverflow.com/questions/abc",
            "StackOverflow URL must contain a question number",
        ),
        (
            "https://example.com/questions/123456",
            "The URL must point to either GitHub or StackOverflow",
        ),
        (
            "https://stackoverflow.com/questions/",
            "StackOverflow URL must contain a question number",
        ),
        ("https://github.com/owner/", "GitHub URL must contain both owner and repo"),
    ],
)
def test_validate_link_invalid(invalid_url, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        _validate_link(invalid_url)


@pytest.mark.parametrize(
    "data",
    [
        {
            "id": 1,
            "link": "https://github.com/owner/repo",
            "tags": ["work", "project"],
            "filters": ["user:dummy", "type:comment"],
        },
        {
            "id": 2,
            "link": "https://stackoverflow.com/questions/123456",
            "tags": ["python", "help"],
            "filters": ["type:question"],
        },
    ],
)
def test_link_response(data):
    link_response = LinkResponse(**data)
    assert link_response.id == data["id"]
    assert link_response.link == data["link"]
    assert link_response.tags == data["tags"]
    assert link_response.filters == data["filters"]


@pytest.mark.parametrize(
    "data",
    [
        {
            "link": "https://stackoverflow.com/questions/123456",
            "tags": ["python", "help"],
            "filters": ["type:question"],
        }
    ],
)
def test_add_link_request(data):
    add_link_request = AddLinkRequest(**data)
    assert add_link_request.link == data["link"]
    assert add_link_request.tags == data["tags"]
    assert add_link_request.filters == data["filters"]


@pytest.mark.parametrize("data", [{"link": "https://github.com/owner/repo"}])
def test_remove_link_request(data):
    remove_link_request = RemoveLinkRequest(**data)
    assert remove_link_request.link == data["link"]


@pytest.mark.parametrize(
    "data",
    [
        {
            "id": 42,
            "link": "https://stackoverflow.com/questions/123456",
            "description": "New answer available",
            "tg_chat_ids": [123456789, 987654321],
        }
    ],
)
def test_link_update(data):
    link_update = LinkUpdate(**data)
    assert link_update.id == data["id"]
    assert link_update.link == data["link"]
    assert link_update.description == data["description"]
    assert link_update.tg_chat_ids == data["tg_chat_ids"]


@pytest.mark.parametrize(
    "data",
    [
        {
            "description": "Not Found",
            "code": "404",
            "exceptionName": "ResourceNotFound",
            "exceptionMessage": "The requested resource could not be found.",
            "stacktrace": ["Traceback (most recent call last): ..."],
        }
    ],
)
def test_api_error_response(data):
    api_error_response = ApiErrorResponse(**data)
    assert api_error_response.description == data["description"]
    assert api_error_response.code == data["code"]
    assert api_error_response.exceptionName == data["exceptionName"]
    assert api_error_response.exceptionMessage == data["exceptionMessage"]
    assert api_error_response.stacktrace == data["stacktrace"]


@pytest.mark.parametrize(
    "links_data",
    [
        [
            {
                "id": 1,
                "link": "https://github.com/owner/repo",
                "tags": ["work"],
                "filters": ["user:dummy"],
            },
            {
                "id": 2,
                "link": "https://stackoverflow.com/questions/123456",
                "tags": ["python"],
                "filters": ["type:question"],
            },
        ]
    ],
)
def test_list_links_response(links_data):
    data = {"links": [LinkResponse(**link) for link in links_data], "size": len(links_data)}
    list_links_response = ListLinksResponse(**data)
    assert list_links_response.links == data["links"]
    assert list_links_response.size == data["size"]
