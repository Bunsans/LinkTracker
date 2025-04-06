from fastapi import APIRouter, Depends, Path
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.db import db_helper
from src.dependencies import link_service

router = APIRouter(prefix="/tg-chat")


@router.delete("/{tg_chat_id}", status_code=200)
async def delete_chat(
    tg_chat_id: int = Path(..., description="ID чата"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> None:
    """Удалить чат."""
    return await link_service.delete_chat(tg_chat_id, session)


@router.post("/{tg_chat_id}", status_code=200)
async def register_chat(
    tg_chat_id: int = Path(..., description="ID чата"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> None:
    """Зарегистрировать чат."""
    logger.debug(f"View Register chat :{tg_chat_id}")
    return await link_service.register_chat(tg_chat_id, session)


@router.get("/{tg_chat_id}", status_code=200)
async def is_chat_registrated(
    tg_chat_id: int = Path(..., description="ID чата"),
    session: AsyncSession = Depends(db_helper.session_getter),
) -> bool:
    return await link_service.is_chat_registrated(tg_chat_id, session)
