from fastapi import APIRouter, Body, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db_helper
from src.dependencies import link_service
from src.schemas.schemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest

router = APIRouter(prefix="/links")


@router.post("", response_model=LinkResponse)
async def add_link(
    tg_chat_id: int = Header(..., description="ID чата"),
    link_request: AddLinkRequest = Body(..., description="Данные для добавления ссылки"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> LinkResponse:
    """Добавить отслеживание ссылки."""
    return await link_service.add_link(  # type: ignore
        tg_chat_id=tg_chat_id,
        link_request=link_request,
        session=session,
    )


@router.delete("", response_model=LinkResponse)
async def remove_link(
    tg_chat_id: int = Header(..., description="ID чата"),
    link_request: RemoveLinkRequest = Query(..., description="Данные для удаления ссылки"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> LinkResponse:
    return await link_service.remove_link(  # type: ignore
        tg_chat_id=tg_chat_id,
        link_request=link_request,
        session=session,
    )


@router.get("", response_model=ListLinksResponse)
async def get_links(
    tg_chat_id: int = Header(..., description="ID чата"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> ListLinksResponse:
    """Получить все отслеживаемые ссылки."""
    result = await link_service.get_links(  # type: ignore
        tg_chat_id,
        session,
    )
    return ListLinksResponse(links=result.links, size=result.size)
