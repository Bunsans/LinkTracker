from src.api.links.schemas import AddLinkRequest, LinkResponse, ListLinksResponse, RemoveLinkRequest
from src.data import link_service


def get_links(tg_chat_id: int) -> ListLinksResponse:
    """If tg_chat_id not in chat_id_links_mapper:
       raise NotRegistratedChatError(message="Not registrated chat. While getting links")
    links = chat_id_links_mapper[tg_chat_id].
    """
    return link_service.get_links(tg_chat_id)


def add_link(
    tg_chat_id: int,
    link_request: AddLinkRequest,
) -> LinkResponse:
    """Добавить отслеживание ссылки."""
    return link_service.add_link(tg_chat_id, link_request)


def remove_link(
    tg_chat_id: int,
    link_request: RemoveLinkRequest,
) -> LinkResponse:
    """Убрать отслеживание ссылки.
    if tg_chat_id not in chat_id_links_mapper:
        raise NotRegistratedChatError(message="Not registrated chat.")
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
            ).
    """
    return link_service.remove_link(tg_chat_id, link_request)
