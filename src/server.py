import asyncio
import os
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import Body, FastAPI
from fastapi.exceptions import RequestValidationError
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ApiIdInvalidError

from src.api.api_v2 import router_v2
from src.data_classes import LinkUpdate
from src.db import db_helper
from src.db.base import Base
from src.exceptions import EntityAlreadyExistsError, NotRegistratedChatError, ServiceError
from src.exceptions.api_exceptions_handlers import (
    entity_already_exist_exception_handler,
    link_not_found_exception_handler,
    not_registrated_chat_exception_handler,
    server_error_exception_handler,
    validation_exception_handler,
)
from src.exceptions.exceptions import LinkNotFoundError
from src.kafka.kafka_consumer import KafkaConsumerService
from src.settings import (
    PREFIX_API,
    APIServerSettings,
    MessageBrokerSettings,
    TGBotSettings,
    TransportType,
)


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
    tg_client = TelegramClient(
        "fastapi_bot_session",
        application.settings.api_id,  # type: ignore[attr-defined]
        application.settings.api_hash,  # type: ignore[attr-defined]
    ).start(
        bot_token=application.settings.token,  # type: ignore[attr-defined]
    )

    kafka_settings = MessageBrokerSettings()  # type: ignore[attr-defined,call-arg]
    kafka_consumer = KafkaConsumerService(tg_client=tg_client)  # type: ignore[attr-defined,call-arg]

    async with AsyncExitStack() as stack:
        try:
            application.tg_client = await stack.enter_async_context(await tg_client)  # type: ignore[attr-defined]
        except ApiIdInvalidError:
            logger.info("Working without telegram client inside.")

        async with db_helper.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        if kafka_settings.transport_type == TransportType.kafka:
            kafka_consumer = KafkaConsumerService(tg_client=application.tg_client)  # type: ignore[attr-defined,call-arg]
            await kafka_consumer.setup()
            asyncio.create_task(kafka_consumer.start_consuming())  # type: ignore[attr-defined,call-arg]
            logger.info("Kafka consumer started successfully")

        yield
        await db_helper.dispose()
        await stack.aclose()
        await kafka_consumer.stop()

    await loop.shutdown_default_executor()


app = FastAPI(
    title="telegram_bot_app",
    lifespan=default_lifespan,
)

app.exception_handler(RequestValidationError)(validation_exception_handler)
app.exception_handler(ServiceError)(server_error_exception_handler)
app.exception_handler(NotRegistratedChatError)(not_registrated_chat_exception_handler)
app.exception_handler(LinkNotFoundError)(link_not_found_exception_handler)
app.exception_handler(EntityAlreadyExistsError)(entity_already_exist_exception_handler)

# was  app.include_router(router=router_v1, prefix="/api/v1")
app.include_router(router=router_v2, prefix="/api/v2")


app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(PREFIX_API + "/updates", status_code=200)
async def updates(
    link_update: LinkUpdate = Body(..., description="Отправить обновление"),
) -> str:
    tg_client = app.tg_client  # type: ignore[attr-defined]
    for chat_id in link_update.tg_chat_ids:
        await tg_client.send_message(entity=chat_id, message=link_update.description)
    return "Обновление обработано"


async def main() -> None:
    await asyncio.gather(run_server())  # , scrapper())


async def run_server() -> None:
    api_settings = APIServerSettings()  # type: ignore[attr-defined,call-arg]

    config = uvicorn.Config(
        "server:app",
        host=api_settings.host_server,  # type: ignore[attr-defined]
        port=api_settings.port_server,  # type: ignore[attr-defined]
        log_level=os.getenv("LOGGING_LEVEL", "info").lower(),
        reload=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
