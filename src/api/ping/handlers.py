import sys
import traceback
from typing import List

from fastapi import APIRouter, Body, Header, HTTPException, Path, Query, Request
from loguru import logger

from src.data import chat_id_links_mapper, links_chat_id_mapper
from src.data_classes import (
    AddLinkRequest,
    ApiErrorResponse,
    LinkResponse,
    ListLinksResponse,
    RemoveLinkRequest,
)

router = APIRouter()


def validate_link(link: str) -> None:
    pass


@router.get("/ping", response_model=None)
async def ping_handler(
    _: Request,
) -> dict[str, str]:
    return {"pong": "ok"}


@router.post("/tg-chat/{id}", status_code=200)
async def register_chat(id: int = Path(..., description="ID чата")):
    """
    Зарегистрировать чат
    """
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")

    try:
        if id in chat_id_links_mapper:
            return "Чат уже зарегистрирован"
        chat_id_links_mapper[id] = []
        return "Чат зарегистрирован"
    except Exception as e:
        response = ApiErrorResponse(
            description="Ошибка при запросе к внешнему API",
            code="API_ERROR",
            exceptionName=type(e).__name__,
            exceptionMessage=str(e),
            stacktrace=traceback.format_exc().splitlines(),
        ).model_dump()
        raise HTTPException(status_code=500, detail=response)


@router.delete("/tg-chat/{id}", status_code=200)
async def delete_chat(id: int = Path(..., description="ID чата")) -> None:
    """
    Удалить чат
    """
    logger.debug(f"chat_id_links_mapper: {chat_id_links_mapper}")

    if id not in chat_id_links_mapper:
        raise HTTPException(status_code=401, detail="Чат не зарегистрирован")

    try:
        del chat_id_links_mapper[id]
        return "Чат успешно удалён"
    except Exception as e:
        response = ApiErrorResponse(
            description="Ошибка при запросе к внешнему API",
            code="API_ERROR",
            exceptionName=type(e).__name__,
            exceptionMessage=str(e),
            stacktrace=traceback.format_exc().splitlines(),
        ).model_dump()
        raise HTTPException(status_code=500, detail=response)


@router.get("/links", response_model=ListLinksResponse)
async def get_links(id: int = Header(..., description="ID чата")) -> ListLinksResponse:
    """
    Получить все отслеживаемые ссылки
    """
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")
    if id not in chat_id_links_mapper:
        raise HTTPException(status_code=401, detail="Чат не зарегистрирован")

    try:
        links = chat_id_links_mapper[id]
        logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
        return ListLinksResponse(links=links, size=sys.getsizeof(links))
    except Exception as e:
        response = ApiErrorResponse(
            description="Ошибка при запросе к внешнему API",
            code="API_ERROR",
            exceptionName=type(e).__name__,
            exceptionMessage=str(e),
            stacktrace=traceback.format_exc().splitlines(),
        ).model_dump()
        raise HTTPException(status_code=500, detail=response)


@router.post("/links", response_model=LinkResponse)
async def add_link(
    id: int = Header(..., description="ID чата"),
    link_request: AddLinkRequest = Body(..., description="Данные для добавления ссылки"),
) -> LinkResponse:
    """
    Добавить отслеживание ссылки
    """
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")

    if id not in chat_id_links_mapper:
        raise HTTPException(status_code=401, detail="Чат не зарегистрирован")
    try:
        list_links = chat_id_links_mapper[id]
        # link_request : AddLinkRequest -> link_response LinkResponse
        link_response = LinkResponse(
            id=id,
            link=link_request.link,
            tags=link_request.tags,
            filters=link_request.filters,
        )

        for link_ in list_links:
            if link_response.link == link_.link:
                list_links.remove(link_)

        list_links.append(link_response)
        chat_id_links_mapper[id] = list_links

        if link_response.link not in links_chat_id_mapper:
            links_chat_id_mapper[link_response.link] = set([id])
        else:
            list_ids = links_chat_id_mapper[link_response.link]
            list_ids.add(id)
            links_chat_id_mapper[link_response.link] = list_ids

        logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")

        return LinkResponse(
            id=id,
            link=link_request.link,
            tags=link_request.tags,
            filters=link_request.filters,
        )
    except Exception as e:
        response = ApiErrorResponse(
            description="Ошибка при запросе к внешнему API",
            code="API_ERROR",
            exceptionName=type(e).__name__,
            exceptionMessage=str(e),
            stacktrace=traceback.format_exc().splitlines(),
        ).model_dump()
        raise HTTPException(status_code=500, detail=response)


@router.delete("/links", response_model=LinkResponse)
async def remove_link(
    id: int = Header(..., description="ID чата"),
    link_request: RemoveLinkRequest = Query(..., description="Данные для удаления ссылки"),
) -> LinkResponse:
    """
    Убрать отслеживание ссылки
    """
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")

    if id not in chat_id_links_mapper:
        raise HTTPException(status_code=401, detail="Чат не зарегистрирован")
    try:
        logger.debug(f"Before: links_chat_id_mapper: {links_chat_id_mapper}")
        if link_request.link in links_chat_id_mapper:
            set_ids = links_chat_id_mapper[link_request.link]
            set_ids.remove(id)
            if set_ids:
                links_chat_id_mapper[link_request.link] = set_ids
            else:
                del links_chat_id_mapper[link_request.link]
        logger.debug(f"After: links_chat_id_mapper: {links_chat_id_mapper}")

        list_links: List[LinkResponse] = chat_id_links_mapper[id]
        for link_ in list_links:
            if link_.link == link_request.link:
                list_links.remove(link_)
                logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
                return LinkResponse(
                    id=id,
                    link=link_request.link,
                    tags=link_.tags,
                    filters=link_.filters,
                )
    except Exception as e:
        response = ApiErrorResponse(
            description="Ошибка при запросе к внешнему API",
            code="API_ERROR",
            exceptionName=type(e).__name__,
            exceptionMessage=str(e),
            stacktrace=traceback.format_exc().splitlines(),
        ).model_dump()
        raise HTTPException(status_code=500, detail=response)
    logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
    raise HTTPException(status_code=404, detail="Ссылка не найдена")
