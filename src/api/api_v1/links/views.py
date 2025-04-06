from fastapi import APIRouter, Body, Header, Query

from src.api.shemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest
from src.dependencies import link_service

router = APIRouter(prefix="/links")


@router.post("", response_model=LinkResponse)
async def add_link(
    tg_chat_id: int = Header(..., description="ID чата"),
    link_request: AddLinkRequest = Body(..., description="Данные для добавления ссылки"),
) -> LinkResponse:
    """Добавить отслеживание ссылки."""
    return link_service.add_link(tg_chat_id=tg_chat_id, link_request=link_request)


@router.delete("", response_model=LinkResponse)
async def remove_link(
    tg_chat_id: int = Header(..., description="ID чата"),
    link_request: RemoveLinkRequest = Query(..., description="Данные для удаления ссылки"),
) -> LinkResponse:
    return link_service.remove_link(tg_chat_id=tg_chat_id, link_request=link_request)


@router.get("", response_model=ListLinksResponse)
async def get_links(
    tg_chat_id: int = Header(..., description="ID чата"),
) -> ListLinksResponse:
    """Получить все отслеживаемые ссылки."""
    return link_service.get_links(
        tg_chat_id,
    )  # ListLinksResponse(links=links, size=sys.getsizeof(links))
