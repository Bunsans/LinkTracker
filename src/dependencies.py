from typing import Literal

from loguru import logger

from src.repository.async_.link_repository_orm import LinkRepositoryORM
from src.repository.link_services import AsyncLinkService, LinkService
from src.repository.sync_.link_repository_local import LinkRepositoryLocal

type_service: Literal["sync", "async"] = "async"
type_repository: Literal["orm", "sql"] | None = "orm"

if type_service == "sync":
    link_repository = LinkRepositoryLocal()
    link_service = LinkService(link_repository)
else:
    if type_repository == "orm":
        link_repository = LinkRepositoryORM()

    link_service = AsyncLinkService(link_repository)

logger.info(f"Run link service for type_service: {type_service}, type_repository:{type_repository}")
