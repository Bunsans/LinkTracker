import sys
from typing import List

from fastapi import HTTPException
from loguru import logger

from src.api.links.schemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest
from src.data import chat_id_links_mapper, links_chat_id_mapper
from src.exceptions import LinkNotFoundError, NotRegistratedChat


def get_links(tg_chat_id: int) -> ListLinksResponse:
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id not in chat_id_links_mapper:
        raise NotRegistratedChat(message="Not registrated chat. While getting links")
    links = chat_id_links_mapper[tg_chat_id]
    logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
    return ListLinksResponse(links=links, size=sys.getsizeof(links))


def add_link(
    tg_chat_id: int,
    link_request: AddLinkRequest,
) -> LinkResponse:
    """Добавить отслеживание ссылки."""
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")
    if tg_chat_id not in chat_id_links_mapper:
        raise NotRegistratedChat(message="Not registrated chat. While adding link")
    list_links = chat_id_links_mapper[tg_chat_id]
    # link_request : AddLinkRequest -> link_response LinkResponse
    link_response = LinkResponse(
        id=tg_chat_id,
        link=link_request.link,
        tags=link_request.tags,
        filters=link_request.filters,
    )
    for link_ in list_links:
        if link_response.link == link_.link:
            list_links.remove(link_)

    list_links.append(link_response)
    chat_id_links_mapper[tg_chat_id] = list_links

    if link_response.link not in links_chat_id_mapper:
        links_chat_id_mapper[link_response.link] = {tg_chat_id}
    else:
        list_ids = links_chat_id_mapper[link_response.link]
        list_ids.add(tg_chat_id)
        links_chat_id_mapper[link_response.link] = list_ids

    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")
    return LinkResponse(
        id=tg_chat_id,
        link=link_request.link,
        tags=link_request.tags,
        filters=link_request.filters,
    )


def remove_link(
    tg_chat_id: int,
    link_request: RemoveLinkRequest,
) -> LinkResponse:
    """Убрать отслеживание ссылки."""
    logger.debug(f"Before: chat_id_links_mapper: {chat_id_links_mapper}")

    if tg_chat_id not in chat_id_links_mapper:
        raise NotRegistratedChat(message="Not registrated chat.")
    logger.debug(f"Before: links_chat_id_mapper: {links_chat_id_mapper}")
    if link_request.link in links_chat_id_mapper:
        set_ids = links_chat_id_mapper[link_request.link]
        set_ids.remove(tg_chat_id)
        if set_ids:
            links_chat_id_mapper[link_request.link] = set_ids
        else:
            del links_chat_id_mapper[link_request.link]
    logger.debug(f"After: links_chat_id_mapper: {links_chat_id_mapper}")
    list_links: List[LinkResponse] = chat_id_links_mapper[tg_chat_id]
    for link_ in list_links:
        if link_.link == link_request.link:
            list_links.remove(link_)
            logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
            return LinkResponse(
                id=tg_chat_id,
                link=link_request.link,
                tags=link_.tags,
                filters=link_.filters,
            )
    logger.debug(f"After: chat_id_links_mapper: {chat_id_links_mapper}")
    raise LinkNotFoundError(
        message="Link not found. While trying to remove it."
    )  # HTTPException(status_code=404, detail="Ссылка не найдена")
