from fastapi import APIRouter, Path

from src.dependencies import link_service

router = APIRouter(prefix="/tg-chat")


@router.delete("/{tg_chat_id}", status_code=200)
async def delete_chat(tg_chat_id: int = Path(..., description="ID чата")) -> None:
    """Удалить чат."""
    return link_service.delete_chat(tg_chat_id)


@router.post("/{tg_chat_id}", status_code=200)
async def register_chat(tg_chat_id: int = Path(..., description="ID чата")) -> None:
    """Зарегистрировать чат."""
    return link_service.register_chat(tg_chat_id)


@router.get("/{tg_chat_id}", status_code=200)
async def is_chat_registrated(tg_chat_id: int = Path(..., description="ID чата")) -> bool:
    return link_service.is_chat_registrated(tg_chat_id)
