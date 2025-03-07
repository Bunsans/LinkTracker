from fastapi import APIRouter

from . import ping
from .links import views as links_views
from .tg_chat import views as tg_chat_views

__all__ = ("router",)

router = APIRouter()
router.include_router(ping.router, tags=["ping"])
router.include_router(links_views.router, tags=["tg_chat"])
router.include_router(tg_chat_views.router, tags=["links"])
