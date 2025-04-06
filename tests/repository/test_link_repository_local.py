import pytest

from src.api.shemas import AddLinkRequest, LinkResponse, RemoveLinkRequest
from src.exceptions import LinkNotFoundError, NotRegistratedChatError
from src.exceptions.exceptions import EntityAlreadyExistsError
from src.repository.sync.link_repository_local import LinkRepositoryLocal


@pytest.fixture
def link_repository() -> LinkRepositoryLocal:
    repo = LinkRepositoryLocal()
    repo.register_chat(1)
    return repo


@pytest.mark.usefixtures("link_repository")
def test_not_registrated_chat(link_repository: LinkRepositoryLocal) -> None:
    with pytest.raises(NotRegistratedChatError):
        link_repository.add_link(
            2,
            AddLinkRequest(link="https://github.com/owner/repo", tags=[], filters=[]),
        )
    with pytest.raises(NotRegistratedChatError):
        link_repository.delete_chat(2)
    with pytest.raises(NotRegistratedChatError):
        link_repository.get_links(2)
    with pytest.raises(NotRegistratedChatError):
        link_repository.remove_link(2, RemoveLinkRequest(link="https://github.com/owner/repo"))
    with pytest.raises(NotRegistratedChatError):
        link_repository.is_chat_registrated(2)


def test_already_registrated_chat(link_repository: LinkRepositoryLocal) -> None:
    link_repository.register_chat(2)
    with pytest.raises(EntityAlreadyExistsError):
        link_repository.register_chat(2)


@pytest.mark.parametrize(
    ("tg_chat_id", "link_request", "expected"),
    [
        (
            1,
            AddLinkRequest(
                link="https://stackoverflow.com/questions/123456",
                tags=["tag1"],
                filters=["filter1"],
            ),
            LinkResponse(
                id=1,
                link="https://stackoverflow.com/questions/123456",
                tags=["tag1"],
                filters=["filter1"],
            ),
        ),
        (
            1,
            AddLinkRequest(link="https://github.com/owner/repo", tags=[], filters=[]),
            LinkResponse(id=1, link="https://github.com/owner/repo", tags=[], filters=[]),
        ),
    ],
)
def test_add_link_happy_path(
    link_repository: LinkRepositoryLocal,
    tg_chat_id: int,
    link_request: AddLinkRequest,
    expected: LinkResponse,
) -> None:
    response = link_repository.add_link(tg_chat_id, link_request)
    assert response == expected
    assert response in link_repository.get_links(tg_chat_id)
    assert link_repository.chat_id_links_mapper == {tg_chat_id: [response]}
    assert link_repository.links_chat_id_mapper == {response.link: {tg_chat_id}}


@pytest.mark.parametrize(
    ("tg_chat_id", "remove_link_request", "expected"),
    [
        (
            1,
            RemoveLinkRequest(link="https://stackoverflow.com/questions/123456"),
            LinkResponse(
                id=1,
                link="https://stackoverflow.com/questions/123456",
                tags=["tag1"],
                filters=["filter1"],
            ),
        ),
        (
            1,
            RemoveLinkRequest(link="https://github.com/owner/repo"),
            LinkResponse(id=1, link="https://github.com/owner/repo", tags=[], filters=[]),
        ),
    ],
)
def test_remove_link_happy_path(
    link_repository: LinkRepositoryLocal,
    tg_chat_id: int,
    remove_link_request: RemoveLinkRequest,
    expected: LinkResponse,
) -> None:
    link_repository.add_link(
        tg_chat_id,
        AddLinkRequest(link=remove_link_request.link, tags=expected.tags, filters=expected.filters),
    )
    response = link_repository.remove_link(tg_chat_id, remove_link_request)
    assert response == expected
    assert response not in link_repository.get_links(tg_chat_id)


def test_remove_link_not_found(link_repository: LinkRepositoryLocal) -> None:
    link_repository.add_link(
        1,
        AddLinkRequest(link="https://github.com/owner/repo", tags=[], filters=[]),
    )
    with pytest.raises(LinkNotFoundError):
        link_repository.remove_link(
            1,
            RemoveLinkRequest(link="https://github.com/nonexistent_owner/nonexistent_repo"),
        )


def test_add_link_duplicate(link_repository: LinkRepositoryLocal) -> None:
    link_request = AddLinkRequest(link="https://github.com/owner/repo", tags=[], filters=[])
    link_request_duplicate = AddLinkRequest(
        link="https://github.com/owner/repo",
        tags=["duplicate"],
        filters=["duplicate"],
    )
    link_response_duplicate = LinkResponse(
        id=1,
        link="https://github.com/owner/repo",
        tags=["duplicate"],
        filters=["duplicate"],
    )

    link_repository.add_link(1, link_request)
    link_repository.add_link(1, link_request_duplicate)
    links = link_repository.get_links(1)
    assert len(links) == 1
    assert links[0] == link_response_duplicate
