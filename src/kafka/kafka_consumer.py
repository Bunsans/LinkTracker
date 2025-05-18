import datetime
import json
from typing import Callable

from aiokafka import AIOKafkaConsumer
from loguru import logger
from pydantic import ValidationError
from telethon import TelegramClient

from src.data_classes import LinkUpdate
from src.kafka.kafka_dlq_producer import KafkaDLQProducer
from src.settings import MessageBrokerSettings, TransportType

kafka_settings = MessageBrokerSettings()


class KafkaConsumerService:
    def __init__(self, tg_client: TelegramClient):
        self.consumer = None
        self.dlq_producer = KafkaDLQProducer()
        self.is_running = False
        self.tg_client = tg_client

    async def kafka_message_sending_to_bot(self, message: dict):
        try:
            link_update = LinkUpdate(**message)
            for chat_id in link_update.tg_chat_ids:
                await self.tg_client.send_message(entity=chat_id, message=link_update.description)
                logger.info("Kafka notification sent")
        except Exception as e:
            logger.exception(f"Error processing Kafka notification{e}")

    async def setup(self):
        if kafka_settings.transport_type != TransportType.kafka:
            return

        self.consumer = AIOKafkaConsumer(
            kafka_settings.kafka_topic_notifications,
            bootstrap_servers=kafka_settings.kafka_bootstrap_servers,
            group_id=kafka_settings.kafka_group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            security_protocol=kafka_settings.kafka_security_protocol,
            sasl_mechanism=kafka_settings.kafka_sasl_mechanism,
            sasl_plain_username=kafka_settings.kafka_sasl_username,
            sasl_plain_password=kafka_settings.kafka_sasl_password,
        )

        try:
            await self.consumer.start()
            await self.dlq_producer.start()
            logger.info("Kafka consumer started successfully")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer{e}")
            raise

    async def start_consuming(self):
        if not self.consumer:
            return
        self.is_running = True
        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                try:
                    value = json.loads(msg.value.decode("utf-8"))
                    await self.kafka_message_sending_to_bot(value)
                    logger.info("Message processed successfully")
                except Exception as e:
                    error_info = f"Processing error: {str(e)}"
                    logger.exception("Error processing Kafka message")
                    await self.dlq_producer.send_to_dlq(msg.value.decode("utf-8"), error_info)
        finally:
            await self.stop()

    async def stop(self):
        self.is_running = False
        try:
            if self.consumer:
                await self.consumer.stop()
            await self.dlq_producer.stop()
            logger.success("Kafka consumer stopped")
        except Exception as e:
            logger.error(f"Failed to stop Kafka consumer{e}")
