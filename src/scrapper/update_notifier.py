from abc import ABC, abstractmethod

import httpx
from aiokafka import AIOKafkaProducer
from fastapi import status
from loguru import logger
from pydantic import ValidationError

from src.data_classes import LinkUpdate
from src.settings import APIServerSettings, MessageBrokerSettings, TransportType

kafka_settings = MessageBrokerSettings()
api_settings = APIServerSettings()


class AbstractUpdateNotifier(ABC):
    @abstractmethod
    async def send_notifications(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        pass


class HTTPUpdateNotifier(AbstractUpdateNotifier):
    async def send_notifications(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        logger.debug(f"Start send to API link_update{link_updates}")

        async with httpx.AsyncClient() as http_client:
            for link_update in link_updates:
                response = await http_client.post(
                    url=api_settings.url_server + "/updates",
                    json=link_update.model_dump(),
                )
                logger.debug(f"send to API: {link_update}")

                if response.status_code == status.HTTP_200_OK:
                    logger.success("All send good")
                else:
                    logger.warning(f"Something wrong\n{response.text}")


class KafkaUpdateNotifier(AbstractUpdateNotifier):
    def __init__(self, setting: MessageBrokerSettings = kafka_settings) -> None:
        self.kafka_settings = setting
        self.topic = self.kafka_settings.kafka_topic_notifications

    # aka kafka producer
    async def send_notifications(
        self,
        link_updates: list[LinkUpdate],
    ) -> None:
        for link_update in link_updates:
            is_good_send = await self.send_one_notification(link_update)
            if is_good_send:
                logger.success("All send good")
            else:
                logger.warning("Something wrong")

    async def start(self) -> None:
        """Start and configure the Kafka producer."""
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_settings.kafka_bootstrap_servers,
                security_protocol=self.kafka_settings.kafka_security_protocol,
                sasl_mechanism=self.kafka_settings.kafka_sasl_mechanism,
                sasl_plain_username=self.kafka_settings.kafka_sasl_username,
                sasl_plain_password=self.kafka_settings.kafka_sasl_password,
                value_serializer=self._serialize_message,
                key_serializer=lambda x: str(x).encode("utf-8"),
            )

            await self._producer.start()
            logger.success("Kafka producer started successfully")

        except Exception as e:
            logger.critical(f"Failed to start Kafka producer {e}")
            raise RuntimeError("Failed to start Kafka producer") from e

    async def stop(self) -> None:
        if self._producer is None:
            logger.warning("Attempted to stop non-existent producer")
            return

        try:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop Kafka producer {e}")
            raise RuntimeError("Failed to stop Kafka producer") from e

    async def send_one_notification(self, link_updates: LinkUpdate) -> bool:
        try:
            await self._producer.send_and_wait(
                topic=self.topic,
                value=link_updates,
                key=link_updates.id,
            )

        except ValidationError as e:
            logger.error(f"Invalid notification data format{e}")
            return False

        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to send notification to Kafka{e}")
            return False
        return True

    @staticmethod
    def _serialize_message(value: LinkUpdate) -> bytes:
        """Serialize LinkUpdate object to bytes for Kafka."""
        return value.model_dump_json().encode("utf-8")


class NotifierFactory:
    def get_notifier(self, type_: TransportType) -> AbstractUpdateNotifier:
        match type_:
            case TransportType.http:
                return HTTPUpdateNotifier()
            case TransportType.kafka:
                return KafkaUpdateNotifier()
            case _:
                return HTTPUpdateNotifier()
