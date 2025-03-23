import asyncio
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import Body, FastAPI
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError

from src.api import router
from src.data_classes import LinkUpdate
from src.exceptions import EntityAlreadyExistsError, NotRegistratedChatError, ServiceError
from src.exceptions.api_exceptions_handlers import (
    entity_already_exist_exception_handler,
    link_not_found_exception_handler,
    not_registrated_chat_exception_handler,
    server_error_exception_handler,
    validation_exception_handler,
)
from src.exceptions.exceptions import LinkNotFoundError
from src.scrapper.scrapper import scrapper
from src.settings import APIServerSettings, TGBotSettings


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


api_settings = APIServerSettings()
app = FastAPI(
    title="telegram_bot_app",
    lifespan=default_lifespan,
)

app.exception_handler(RequestValidationError)(validation_exception_handler)
app.exception_handler(ServiceError)(server_error_exception_handler)
app.exception_handler(NotRegistratedChatError)(not_registrated_chat_exception_handler)
app.exception_handler(LinkNotFoundError)(link_not_found_exception_handler)
app.exception_handler(EntityAlreadyExistsError)(entity_already_exist_exception_handler)

app.include_router(router=router, prefix=api_settings.prefix_server)


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
        host=api_settings.host_server,
        port=api_settings.port_server,
        log_level=os.getenv("LOGGING_LEVEL", "info").lower(),
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
