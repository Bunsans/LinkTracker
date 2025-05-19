import asyncio
import json
import os
from dataclasses import asdict
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger
from pydantic import ValidationError
from testcontainers.compose import DockerCompose
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.kafka import KafkaContainer

from src.data_classes import LinkUpdate
from src.kafka.kafka_consumer import KafkaConsumerService
from src.kafka.kafka_dlq_producer import DLQMessage, KafkaDLQProducer
from src.scrapper.update_notifier import KafkaUpdateNotifier
from src.settings import MessageBrokerSettings, TransportType


# Mock TelegramClient для тестов
class MockTelegramClient:
    async def send_message(self, entity, message):
        pass


@pytest.fixture(scope="module")
def kafka_container():
    with (
        KafkaContainer(image="confluentinc/cp-kafka:latest")
        .with_env("KAFKA_AUTO_CREATE_TOPICS_ENABLE", "true")
        .with_env(
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP", "BROKER:PLAINTEXT,PLAINTEXT:SASL_PLAINTEXT"
        )
        .with_env("KAFKA_SASL_MECHANISM_INTER_BROKER_PROTOCOL", "PLAIN")
        .with_env("KAFKA_SASL_ENABLED_MECHANISMS", "PLAIN")
        .with_env(
            "KAFKA_LISTENER_NAME_PLAINTEXT_PLAIN_SASL_JAAS_CONFIG",
            "org.apache.kafka.common.security.plain.PlainLoginModule required "
            'username="test" password="testpass" '
            'user_test="testpass";',
        )
    ) as kafka:
        yield kafka


@pytest.fixture
def kafka_bootstrap_servers(kafka_container):
    return kafka_container.get_bootstrap_server()


@pytest.fixture
def kafka_settings_test(kafka_bootstrap_servers):
    settings = MessageBrokerSettings(
        transport_type=TransportType.kafka,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_topic_notifications="schedule_send_updates_test",
        kafka_security_protocol="SASL_PLAINTEXT",
        kafka_sasl_mechanism="PLAIN",
        kafka_sasl_username="test",
        kafka_sasl_password="testpass",
        kafka_group_id="test_tg_bot",
    )
    return settings


@pytest.fixture
async def kafka_consumer_service(kafka_settings_test):
    tg_client = MockTelegramClient()
    service = KafkaConsumerService(tg_client, settings=kafka_settings_test)

    # Даём Kafka время на инициализацию
    await asyncio.sleep(5)
    await service.setup()
    asyncio.create_task(service.start_consuming())
    yield service
    await service.stop()


def _serialize_message(message: DLQMessage) -> bytes:
    """Serialize DLQ message to bytes for Kafka."""
    return message.model_dump_json().encode("utf-8")


@pytest.fixture
async def kafka_producer(kafka_settings_test):
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_settings_test.kafka_bootstrap_servers,
        security_protocol=kafka_settings_test.kafka_security_protocol,
        sasl_mechanism=kafka_settings_test.kafka_sasl_mechanism,
        sasl_plain_username=kafka_settings_test.kafka_sasl_username,
        sasl_plain_password=kafka_settings_test.kafka_sasl_password,
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest.fixture
async def dlq_producer(kafka_settings_test):
    producer = KafkaDLQProducer(settings=kafka_settings_test)
    await producer.start()
    yield producer
    await producer.stop()


@pytest.fixture
async def kafka_notifier(kafka_settings_test):
    notifier = KafkaUpdateNotifier(setting=kafka_settings_test)
    await notifier.start()
    yield notifier
    await notifier.stop()


@pytest.mark.asyncio
async def test_valid_message_processing(kafka_consumer_service, kafka_notifier, mocker):
    mock_send = mocker.patch.object(
        kafka_consumer_service,
        "kafka_message_sending_to_bot",
        new_callable=mocker.AsyncMock,
        return_value=None,
    )
    valid_message = {
        "id": 1,
        "description": "Test message",
        "link": "https://stackoverflow.com/questions/42393259",
        "tg_chat_ids": [12345],
    }

    # Отправка сообщения в очередь
    res_of_send = await kafka_notifier.send_one_notification(LinkUpdate(**valid_message))
    assert res_of_send is True

    await asyncio.sleep(1)
    mock_send.assert_called_once()
    args, _ = mock_send.call_args
    logger.debug(f"args: {args}")
    received_message = args[0]

    assert received_message["id"] == valid_message["id"]
    assert received_message["description"] == valid_message["description"]
    assert received_message["link"] == valid_message["link"]
    assert received_message["tg_chat_ids"] == valid_message["tg_chat_ids"]


@pytest.mark.asyncio
async def test_invalid_json_handling(
    kafka_consumer_service, kafka_producer, dlq_producer, kafka_settings_test, mocker
):
    """Тест обработки невалидного JSON"""
    await kafka_producer.send_and_wait(
        topic=kafka_settings_test.kafka_topic_notifications, value=b"{invalid: json}"
    )

    await asyncio.sleep(1)

    # Мокируем DLQ producer для проверки
    mock = mocker.patch.object(
        kafka_consumer_service.dlq_producer,
        "send_to_dlq",
        new_callable=mocker.AsyncMock,
        return_value=True,
    )

    # Проверяем, что сообщение попало в DLQ
    mock.assert_awaited_once()
    args, _ = mock.await_args
    assert "invalid: json" in args[0]
    assert "JSONDecodeError" in args[1]

    kafka_consumer_service.is_running = False
