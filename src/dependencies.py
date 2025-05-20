from typing import Literal, Union

from loguru import logger

from src.link_service.link_service import AsyncLinkService, LinkService
from src.repository.async_.link_repository_orm import LinkRepositoryORM
from src.repository.async_.link_repository_sql import LinkRepositoryRawSQL
from src.repository.sync_.link_repository_local import LinkRepositoryLocal

type_service: Literal["sync", "async"] = "async"
type_repository: Literal["orm", "sql"] | None = "orm"


def get_link_repository(
    service_type: Literal["sync", "async"], repo_type: Literal["orm", "sql"] | None = None
) -> Union[LinkRepositoryLocal, LinkRepositoryORM, LinkRepositoryRawSQL]:
    """Get the appropriate link repository based on configuration.

    Args:
        service_type: Either "sync" or "async" service type
        repo_type: For async services, either "orm" or "sql" repository type

    Returns:
        The initialized repository instance

    Raises:
        ValueError: If invalid combination of parameters is provided
    """
    if service_type == "sync":
        return LinkRepositoryLocal()

    if service_type == "async":
        if repo_type == "orm":
            return LinkRepositoryORM()
        if repo_type == "sql":
            return LinkRepositoryRawSQL()

    raise ValueError(
        f"Invalid repository configuration: " f"service_type={service_type}, repo_type={repo_type}"
    )


def get_link_service(
    service_type: Literal["sync", "async"], repo_type: Literal["orm", "sql"] | None = None
) -> Union[LinkService, AsyncLinkService]:
    """Get the appropriate link service based on configuration.

    Args:
        service_type: Either "sync" or "async" service type
        repo_type: For async services, either "orm" or "sql" repository type

    Returns:
        The initialized service instance
    """
    repository = get_link_repository(service_type, repo_type)

    if service_type == "sync":
        return LinkService(repository)
    return AsyncLinkService(repository)


logger.success(
    f"Run link service for type_service: {type_service}, type_repository:{type_repository}"
)

# Initialize services based on configuration
link_service = get_link_service(type_service, type_repository)
