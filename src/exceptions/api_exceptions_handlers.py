from fastapi import status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.requests import Request
from starlette.responses import Response

from src.exceptions import (
    EntityAlreadyExistsError,
    LinkNotFoundError,
    LinkTrackerApiError,
    NotRegistratedChatError,
    ServiceError,
)


async def _request_link_tracker_api_exception_handler(
    message: str,
    exc: LinkTrackerApiError,
    status_code: int,
) -> JSONResponse:
    detail = {"detail": message}
    if exc.message:
        detail["detail"] = exc.message
    if exc.name:
        detail["detail"] = f"{detail['detail']} [{exc.name}]"
    return JSONResponse(
        status_code=status_code,
        content=detail,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    logger.exception("Invalid request data: %s", exc)
    return await request_validation_exception_handler(request, exc)


async def server_error_exception_handler(_: Request, exc: ServiceError) -> Response:
    logger.exception(exc)
    return await _request_link_tracker_api_exception_handler(
        message="Server error",
        exc=exc,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def not_registrated_chat_exception_handler(
    _: Request,
    exc: NotRegistratedChatError,
) -> Response:
    logger.warning(exc)
    return await _request_link_tracker_api_exception_handler(
        message="Not registrated chat",
        exc=exc,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


async def entity_already_exist_exception_handler(
    _: Request,
    exc: EntityAlreadyExistsError,
) -> Response:
    logger.warning(exc)
    return await _request_link_tracker_api_exception_handler(
        message="Entity already exist",
        exc=exc,
        status_code=status.HTTP_208_ALREADY_REPORTED,
    )


async def link_not_found_exception_handler(_: Request, exc: LinkNotFoundError) -> Response:
    logger.warning(exc)
    return await _request_link_tracker_api_exception_handler(
        message="Link not found",
        exc=exc,
        status_code=status.HTTP_404_NOT_FOUND,
    )
