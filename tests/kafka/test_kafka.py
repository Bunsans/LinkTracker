import asyncio
import json

import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger
from testcontainers.kafka import KafkaContainer

from src.data_classes import LinkUpdate
from src.kafka.consumer import KafkaConsumerService
from src.kafka.producer_dlq import DLQMessage, KafkaDLQProducer
from src.scrapper.update_notifier import KafkaUpdateNotifier
from src.settings import MessageBrokerSettings, TransportType


# Mock TelegramClient для тестов
class MockTelegramClient:
    async def send_message(self, entity, message) -> None:  # noqa: ANN001
        pass


@pytest.fixture(scope="module")
def kafka_container():  # noqa: ANN201
    with (
        KafkaContainer(image="confluentinc/cp-kafka:latest")
        .with_env("KAFKA_AUTO_CREATE_TOPICS_ENABLE", "true")
        .with_env(
            "KAFKA_LISTENER_SECURITY_PROTOCOL_MAP",
            "BROKER:PLAINTEXT,PLAINTEXT:SASL_PLAINTEXT",
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
def kafka_bootstrap_servers(kafka_container):  # noqa: ANN001, ANN201
    return kafka_container.get_bootstrap_server()


@pytest.fixture
def kafka_settings_test(kafka_bootstrap_servers):  # noqa: ANN001, ANN201
    return MessageBrokerSettings(
        transport_type=TransportType.kafka,
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        kafka_topic_notifications="schedule_send_updates_test",
        kafka_security_protocol="SASL_PLAINTEXT",
        kafka_sasl_mechanism="PLAIN",
        kafka_sasl_username="test",
        kafka_sasl_password="testpass",  # noqa: S106
        kafka_group_id="test_tg_bot",
    )


@pytest.fixture
async def dlq_producer(kafka_settings_test):  # noqa: ANN001, ANN201
    return KafkaDLQProducer(settings=kafka_settings_test)


@pytest.fixture
async def kafka_consumer_service(kafka_settings_test, dlq_producer):  # noqa: ANN001, ANN201
    tg_client = MockTelegramClient()
    service = KafkaConsumerService(
        tg_client,
        settings=kafka_settings_test,
        dlq_producer=dlq_producer,
    )

    # Даём Kafka время на инициализацию
    await asyncio.sleep(5)
    await service.setup()
    task = asyncio.create_task(service.start_consuming())
    yield service
    await service.stop()
    await task  # may be can broke


def _serialize_message(message: DLQMessage) -> bytes:
    """Serialize DLQ message to bytes for Kafka."""
    return message.model_dump_json().encode("utf-8")


@pytest.fixture
async def kafka_producer(kafka_settings_test):  # noqa: ANN001, ANN201
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
async def kafka_notifier(kafka_settings_test):  # noqa: ANN001, ANN201
    notifier = KafkaUpdateNotifier(setting=kafka_settings_test)
    await notifier.start()
    yield notifier
    await notifier.stop()


@pytest.mark.asyncio
async def test_valid_message_processing(
    kafka_consumer_service,  # noqa: ANN001
    kafka_notifier,  # noqa: ANN001
    mocker,  # noqa: ANN001
) -> None:
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
    res_of_send = await kafka_notifier.send_one_notification(LinkUpdate(**valid_message))  # type: ignore
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
    kafka_consumer_service,  # noqa: ANN001, ARG001 # type: ignore
    kafka_producer,  # noqa: ANN001
    kafka_settings_test,  # noqa: ANN001
) -> None:
    """Тест обработки невалидного JSON."""
    invalid_json = b"{invalid: json}"
    await kafka_producer.send_and_wait(
        topic=kafka_settings_test.kafka_topic_notifications,
        value=b"{invalid: json}",
    )

    await asyncio.sleep(1)
    # Check DLQ topic for the invalid message

    dlq_consumer = AIOKafkaConsumer(
        kafka_settings_test.kafka_topic_notifications + ".DLQ",
        bootstrap_servers=kafka_settings_test.kafka_bootstrap_servers,
        group_id=kafka_settings_test.kafka_group_id + "_test_dlq",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        security_protocol=kafka_settings_test.kafka_security_protocol,
        sasl_mechanism=kafka_settings_test.kafka_sasl_mechanism,
        sasl_plain_username=kafka_settings_test.kafka_sasl_username,
        sasl_plain_password=kafka_settings_test.kafka_sasl_password,
    )
    await dlq_consumer.start()

    await asyncio.sleep(1)

    try:
        msg = await dlq_consumer.getone()
        dlq_message = json.loads(msg.value.decode())

        assert "error" in dlq_message
        assert "original_message" in dlq_message
        assert dlq_message["original_message"] == invalid_json.decode("utf-8", errors="replace")
    finally:
        await dlq_consumer.stop()


@pytest.mark.asyncio
async def test_invalid_message_handling(
    kafka_consumer_service,  # noqa: ANN001, ARG001 # type: ignore
    kafka_producer,  # noqa: ANN001
    kafka_settings_test,  # noqa: ANN001
) -> None:
    """Тест обработки невалидного JSON."""
    invalid_message = {
        "id": 1,
        # Missing description
        "link": "https://example.com",
        # Missing tg_chat_ids
    }

    await kafka_producer.send_and_wait(
        topic=kafka_settings_test.kafka_topic_notifications,
        value=json.dumps(invalid_message).encode("utf-8"),
    )

    await asyncio.sleep(1)
    # Check DLQ topic for the invalid message

    dlq_consumer = AIOKafkaConsumer(
        kafka_settings_test.kafka_topic_notifications + ".DLQ",
        bootstrap_servers=kafka_settings_test.kafka_bootstrap_servers,
        group_id=kafka_settings_test.kafka_group_id + "_test_dlq",
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        security_protocol=kafka_settings_test.kafka_security_protocol,
        sasl_mechanism=kafka_settings_test.kafka_sasl_mechanism,
        sasl_plain_username=kafka_settings_test.kafka_sasl_username,
        sasl_plain_password=kafka_settings_test.kafka_sasl_password,
    )
    await dlq_consumer.start()

    await asyncio.sleep(1)

    try:
        msg = await dlq_consumer.getone()
        dlq_message = json.loads(msg.value.decode())
        logger.debug(f"tested: dlq_message: {dlq_message}")
        assert "error" in dlq_message
        assert "original_message" in dlq_message
        assert json.loads(dlq_message["original_message"]) == invalid_message
    finally:
        await dlq_consumer.stop()
