import asyncio
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Callable, Literal, Optional

import uvicorn
from fastapi import Body, FastAPI, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError

from src.api import router
from src.constants import HOST_API_SERVER, PORT_API_SERVER, PREFIX_API_SERVER
from src.data_classes import LinkUpdate
from src.exceptions import (
    EntityAlreadyExistsError,
    LinkTrackerApiError,
    NotRegistratedChat,
    ServiceError,
)
from src.exceptions.exceptions import LinkNotFoundError
from src.scrapper import scrapper
from src.settings import TGBotSettings


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    logger.exception("Invalid request data: %s", exc)
    return await request_validation_exception_handler(request, exc)


def create_exception_handler(
    status_code: int, initial_detail: str, logger_level: Literal["warning", "error"] = "warning"
) -> Callable[[Request, LinkTrackerApiError], JSONResponse]:
    detail = {"message": initial_detail}  # Using a dictionary to hold the detail

    async def exception_handler(_: Request, exc: LinkTrackerApiError) -> JSONResponse:
        if exc.message:
            detail["message"] = exc.message

        if exc.name:
            detail["message"] = f"{detail['message']} [{exc.name}]"
        if logger_level == "warning":
            logger.warning(exc)
        elif logger_level == "error":
            logger.error(exc)
        else:
            logger.debug(exc)
        return JSONResponse(status_code=status_code, content={"detail": detail["message"]})

    return exception_handler


@asynccontextmanager
async def default_lifespan(application: FastAPI) -> AsyncIterator[None]:
    logger.debug("Running application lifespan ...")

    loop = asyncio.get_event_loop()
    loop.set_default_executor(
        ThreadPoolExecutor(
            max_workers=4,
        ),
    )
    application.settings = TGBotSettings()  # type: ignore[attr-defined,call-arg]

    client = TelegramClient(
        "fastapi_bot_session",
        application.settings.api_id,  # type: ignore[attr-defined]
        application.settings.api_hash,  # type: ignore[attr-defined]
    ).start(
        bot_token=application.settings.token,  # type: ignore[attr-defined]
    )

    async with AsyncExitStack() as stack:
        try:
            application.tg_client = await stack.enter_async_context(await client)  # type: ignore[attr-defined]
        except ApiIdInvalidError:
            logger.info("Working without telegram client inside.")
        yield
        await stack.aclose()

    await loop.shutdown_default_executor()


app = FastAPI(
    title="telegram_bot_app",
    lifespan=default_lifespan,
)

app.exception_handler(RequestValidationError)(validation_exception_handler)

app.add_exception_handler(
    exc_class_or_status_code=ServiceError,
    handler=create_exception_handler(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Server error.", logger_level="error"
    ),
)
app.add_exception_handler(
    exc_class_or_status_code=NotRegistratedChat,
    handler=create_exception_handler(status.HTTP_401_UNAUTHORIZED, "Not registrated chat."),
)
app.add_exception_handler(
    exc_class_or_status_code=EntityAlreadyExistsError,
    handler=create_exception_handler(status.HTTP_208_ALREADY_REPORTED, "Entity already exist."),
)
app.add_exception_handler(
    exc_class_or_status_code=LinkNotFoundError,
    handler=create_exception_handler(status.HTTP_404_NOT_FOUND, "Link not found."),
)
app.include_router(router=router, prefix=PREFIX_API_SERVER)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/updates", status_code=200)
async def updates(
    link_update: LinkUpdate = Body(..., description="Отправить обновление"),
) -> Optional[str]:
    tg_client = app.tg_client  # type: ignore[attr-defined]
    logger.info(f"tg_client :{tg_client}")
    for chat_id in link_update.tg_chat_ids:
        await tg_client.send_message(
            entity=chat_id,
            message=f"Обновление по ссылке: {link_update.link}\n{link_update.description}",
        )
    return "Обновление обработано"


async def main() -> None:
    await asyncio.gather(run_server(), scrapper())


async def run_server() -> None:
    config = uvicorn.Config(
        "server:app",
        host=HOST_API_SERVER,
        port=PORT_API_SERVER,
        log_level=os.getenv("LOGGING_LEVEL", "info").lower(),
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
