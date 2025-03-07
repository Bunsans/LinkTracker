from typing import Optional

from fastapi import APIRouter, Path

from src.api.tg_chat import crud

router = APIRouter(prefix="/tg-chat")


@router.post("/{id}", status_code=200)
async def register_chat(tg_chat_id: int = Path(..., description="ID чата")) -> Optional[str]:
    """Зарегистрировать чат."""
    return crud.register_chat(tg_chat_id)


@router.delete("/{id}", status_code=200)
async def delete_chat(tg_chat_id: int = Path(..., description="ID чата")) -> str | None:
    """Удалить чат."""
    return crud.delete_chat(tg_chat_id)
