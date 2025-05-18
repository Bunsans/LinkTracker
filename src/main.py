import asyncio
import logging

from src.bot import make_tg_client
from src.settings import TGBotSettings

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


settings = TGBotSettings()  # type: ignore[call-arg]
client = make_tg_client(settings)


async def dummy_func() -> None:
    await asyncio.sleep(1)


async def main() -> None:
    while True:
        await asyncio.gather(
            asyncio.create_task(dummy_func()),
        )


logger.info("Run the event loop to start receiving messages")

with client:
    try:
        client.loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logger.exception(
            "Main loop raised error.",
            extra={"exc": exc},
        )
