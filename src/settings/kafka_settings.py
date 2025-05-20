import enum
import typing
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TransportType(enum.Enum):
    kafka = "kafka"
    http = "http"


class MessageBrokerSettings(BaseSettings):
    transport_type: TransportType = Field(
        default=TransportType.kafka,
        description="Отправка сообщений от API до бота через kafka или http",
    )
    http_url: str = Field(default="http://127.0.0.1:8002", description="URL для HTTP-коммуникации")
    kafka_bootstrap_servers: str = Field(default="127.0.0.1:9092", description="Серверы Kafka")
    kafka_topic_notifications: str = Field(
        default="schedule_send_updates", description="Топик Kafka для уведомлений"
    )
    kafka_security_protocol: str = Field(
        default="SASL_PLAINTEXT", description="Протокол безопасности для Kafka"
    )
    kafka_sasl_mechanism: str = Field(default="PLAIN")
    kafka_sasl_username: str = Field(default="kafka")
    kafka_sasl_password: str = Field(default="kafka")
    kafka_group_id: str = Field(default="tg-bot")

    model_config: typing.ClassVar[SettingsConfigDict] = SettingsConfigDict(
        extra="ignore",
        frozen=False,
        case_sensitive=False,
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_prefix="APP_",
    )
