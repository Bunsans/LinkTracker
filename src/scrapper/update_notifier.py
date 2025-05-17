from abc import ABC, abstractmethod

import httpx
from fastapi import status
from loguru import logger

from src.data_classes import LinkUpdate
from src.scrapper.scrapper import api_settings


class AbstractUpdateNotifier(ABC):
    @abstractmethod
    async def send_notification(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        pass


class HTTPUpdateNotifier(AbstractUpdateNotifier):
    async def send_notification(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        async with httpx.AsyncClient() as http_client:
            for link_update in link_updates:
                response = await http_client.post(
                    url=api_settings.url_server + "/updates",
                    json=link_update.model_dump(),
                )
                if response.status_code == status.HTTP_200_OK:
                    logger.success("All send good")
                else:
                    logger.warning(f"Something wrong\n{response.text}")


class KafkaUpdateNotifier(AbstractUpdateNotifier):
    async def send_notification(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        async with httpx.AsyncClient() as http_client:
            for link_update in link_updates:
                response = await http_client.post(
                    url=api_settings.url_server + "/updates",
                    json=link_update.model_dump(),
                )
                if response.status_code == status.HTTP_200_OK:
                    logger.success("All send good")
                else:
                    logger.warning(f"Something wrong\n{response.text}")
