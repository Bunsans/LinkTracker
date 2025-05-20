from __future__ import annotations
from datetime import datetime

from aiokafka import AIOKafkaProducer
from loguru import logger
from pydantic import BaseModel

from src.settings import TIMEZONE, MessageBrokerSettings


class DLQMessage(BaseModel):
    """Model for Dead Letter Queue messages."""

    original_message: str
    error: str
    timestamp: str


kafka_settings = MessageBrokerSettings()


class KafkaDLQProducer:
    """Producer for sending failed messages to a Dead Letter Queue."""

    def __init__(self, settings: MessageBrokerSettings = kafka_settings) -> None:
        """Initialize the DLQ producer."""
        self._producer: AIOKafkaProducer | None = None
        self.kafka_settings = settings
        self._dlq_topic = f"{self.kafka_settings.kafka_topic_notifications}.DLQ"

    async def start(self) -> None:
        """Initialize and start the DLQ producer."""
        if self._producer is not None:
            logger.warning("DLQ producer already started")
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.kafka_settings.kafka_bootstrap_servers,
                security_protocol=self.kafka_settings.kafka_security_protocol,
                sasl_mechanism=self.kafka_settings.kafka_sasl_mechanism,
                sasl_plain_username=self.kafka_settings.kafka_sasl_username,
                sasl_plain_password=self.kafka_settings.kafka_sasl_password,
                value_serializer=self._serialize_message,
            )

            await self._producer.start()
            logger.info(f"DLQ producer started successfully, {self._dlq_topic}")

        except Exception as e:
            logger.critical(f"Failed to start DLQ producer{e}")
            raise RuntimeError("Failed to start DLQ producer") from e

    async def send_to_dlq(self, original_message: str, error_info: str) -> bool:
        """Send a failed message to the Dead Letter Queue.

        Args:
            original_message: The original message that failed processing
            error_info: Description of the failure reason

        Returns:
            bool: True if message was successfully delivered to DLQ

        """
        if self._producer is None:
            logger.error("Cannot send to DLQ - producer not initialized")
            return False

        try:
            dlq_message = DLQMessage(
                original_message=original_message,
                error=error_info,
                timestamp=datetime.now(tz=TIMEZONE).isoformat(),
            )
            logger.debug(f"dlq_message: {dlq_message}")
            await self._producer.send_and_wait(topic=self._dlq_topic, value=dlq_message)

            logger.info(f"Message successfully sent to DLQ: {error_info[:100]}")

        except Exception as e:  # noqa: BLE001
            logger.exception(f"Failed to send message to DLQ: {error_info}\n\n{e}")
            return False
        return True

    async def stop(self) -> None:
        """Gracefully stop the DLQ producer."""
        if self._producer is None:
            logger.warning("Attempted to stop non-existent producer")
            return
        try:
            await self._producer.stop()
            self._producer = None
            logger.info("DLQ producer stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop DLQ producer{e}")
            raise RuntimeError("Failed to stop DLQ producer") from e

    @staticmethod
    def _serialize_message(value: DLQMessage) -> bytes:
        """Serialize LinkUpdate object to bytes for Kafka."""
        return value.model_dump_json().encode("utf-8")
