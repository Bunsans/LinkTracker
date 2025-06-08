from fastapi import APIRouter

from .links import views as links_views
from .ping import handlers
from .tg_chat import views as tg_chat_views

router_v1 = APIRouter()
router_v1.include_router(handlers.router, tags=["ping"])
router_v1.include_router(links_views.router, tags=["links"])
router_v1.include_router(tg_chat_views.router, tags=["tg_chat"])

__all__ = ("router_v1",)
