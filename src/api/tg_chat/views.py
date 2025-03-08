from typing import Optional

from fastapi import APIRouter, Path

from src.api.tg_chat import crud

router = APIRouter(prefix="/tg-chat")


@router.get("/{tg_chat_id}", status_code=200)
async def is_registered_chat(tg_chat_id: int = Path(..., description="ID чата")) -> None:
    """Проверка наличия чата."""
    return crud.is_registered_chat(tg_chat_id)


@router.post("/{tg_chat_id}", status_code=200)
async def register_chat(tg_chat_id: int = Path(..., description="ID чата")) -> Optional[str]:
    """Зарегистрировать чат."""
    return crud.register_chat(tg_chat_id)


@router.delete("/{tg_chat_id}", status_code=200)
async def delete_chat(tg_chat_id: int = Path(..., description="ID чата")) -> str | None:
    """Удалить чат."""
    return crud.delete_chat(tg_chat_id)
