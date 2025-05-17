from aiokafka import AIOKafkaProducer
import json
from src.settings import app_settings
from src.struct_logger import StructuredLogger
import datetime

logger = StructuredLogger("kafka_dlq_producer")

class KafkaDLQProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        """Инициализация и запуск DLQ producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=app_settings.transport.kafka_bootstrap_servers,
            security_protocol=app_settings.transport.kafka_security_protocol,
            sasl_mechanism=app_settings.transport.kafka_sasl_mechanism,
            sasl_plain_username=app_settings.transport.kafka_sasl_username,
            sasl_plain_password=app_settings.transport.kafka_sasl_password
        )
        
        try:
            await self.producer.start()
            logger.info("DLQ producer started successfully", event="dlq_producer_start")
        except Exception as e:
            logger.error(
                "Failed to start DLQ producer",
                event="dlq_producer_start_error",
                error=str(e)
            )
            raise

    async def send_to_dlq(self, original_message, error_info: str):
        """Отправка сообщения в DLQ топик."""
        if not self.producer:
            return

        dlq_message = {
            "original_message": original_message,
            "error": error_info,
            "timestamp": datetime.datetime.now().isoformat()
        }

        try:
            await self.producer.send_and_wait(
                topic=f"{app_settings.transport.kafka_topic_notifications}.DLQ",
                value=json.dumps(dlq_message).encode('utf-8')
            )
            logger.info(
                "Message sent to DLQ",
                event="dlq_message_sent",
                error=error_info
            )
        except Exception as e:
            logger.error(
                "Failed to send message to DLQ",
                event="dlq_send_error",
                error=str(e)
            )

    async def stop(self):
        """Остановка DLQ producer."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("DLQ producer stopped", event="dlq_producer_stop")
            except Exception as e:
                logger.error(
                    "Failed to stop DLQ producer",
                    event="dlq_producer_stop_error",
                    error=str(e)
                ) 