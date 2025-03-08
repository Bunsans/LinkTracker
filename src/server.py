import asyncio
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import Body, FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
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
from src.scrapper import scrapper
from src.settings import TGBotSettings


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    logger.exception("Invalid request data: %s", exc)
    return await request_validation_exception_handler(request, exc)


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
