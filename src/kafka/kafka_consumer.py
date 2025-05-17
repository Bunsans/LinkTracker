from aiokafka import AIOKafkaConsumer
import json
from typing import Callable
from src.settings import app_settings, CommunicationType
from src.struct_logger import StructuredLogger
from src.kafka_dlq_producer import KafkaDLQProducer
import datetime
from pydantic import ValidationError

logger = StructuredLogger("kafka_consumer")

class KafkaConsumerService:
    def __init__(self):
        self.consumer = None
        self.dlq_producer = KafkaDLQProducer()
        self.running = False
        
    async def setup(self):
        if app_settings.transport.message_transport != CommunicationType.KAFKA:
            return
            
        self.consumer = AIOKafkaConsumer(
            app_settings.transport.kafka_topic_notifications,
            bootstrap_servers=app_settings.transport.kafka_bootstrap_servers,
            group_id=app_settings.transport.kafka_group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            security_protocol=app_settings.transport.kafka_security_protocol,
            sasl_mechanism=app_settings.transport.kafka_sasl_mechanism,
            sasl_plain_username=app_settings.transport.kafka_sasl_username,
            sasl_plain_password=app_settings.transport.kafka_sasl_password
        )
        
        try:
            await self.consumer.start()
            await self.dlq_producer.start()
            logger.info(
                "Kafka consumer started successfully",
                event="kafka_consumer_start"
            )
        except Exception as e:
            logger.error(
                "Failed to start Kafka consumer",
                event="kafka_consumer_start_error",
                error=str(e)
            )
            raise
        
    async def start_consuming(self, message_handler: Callable):
        if not self.consumer:
            return
            
        self.running = True
        
        try:
            async for msg in self.consumer:
                if not self.running:
                    break
                try:
                    value = json.loads(msg.value.decode('utf-8'))
                    await message_handler(value)
                    logger.info(
                        "Message processed successfully",
                        event="kafka_message_processed",
                        topic=msg.topic,
                        partition=msg.partition,
                        offset=msg.offset
                    )
                except json.JSONDecodeError as e:
                    error_info = f"JSON decode error: {str(e)}"
                    logger.error(
                        "Failed to decode message",
                        event="kafka_message_decode_error",
                        error=error_info
                    )
                    await self.dlq_producer.send_to_dlq(msg.value.decode('utf-8'), error_info)
                except ValidationError as e:
                    error_info = f"Validation error: {str(e)}"
                    logger.error(
                        "Failed to validate message",
                        event="kafka_message_validation_error",
                        error=error_info
                    )
                    await self.dlq_producer.send_to_dlq(msg.value.decode('utf-8'), error_info)
                except Exception as e:
                    error_info = f"Processing error: {str(e)}"
                    logger.exception(
                        "Error processing Kafka message",
                        event="kafka_message_processing_error",
                        error=error_info
                    )
                    await self.dlq_producer.send_to_dlq(msg.value.decode('utf-8'), error_info)
        finally:
            await self.stop()
                
    async def stop(self):
        self.running = False
        try:
            if self.consumer:
                await self.consumer.stop()
            await self.dlq_producer.stop()
            logger.info("Kafka consumer stopped", event="kafka_consumer_stop")
        except Exception as e:
            logger.error(
                "Failed to stop Kafka consumer",
                event="kafka_consumer_stop_error",
                error=str(e)
            )