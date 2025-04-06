from fastapi import APIRouter

from .links import views as links_views
from .ping import handlers
from .tg_chat import views as tg_chat_views

__all__ = ("router_v2",)

router_v2 = APIRouter()
router_v2.include_router(handlers.router, tags=["ping", "db"])
router_v2.include_router(links_views.router, tags=["links", "db"])

router_v2.include_router(tg_chat_views.router, tags=["tg_chat", "db"])
