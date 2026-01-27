from kafka import KafkaProducer, KafkaConsumer
import json
import socket
from common.utils.logging import logger


class KafkaAudit:
    def __init__(self, topic="helix-log-events"):
        self.topic = topic
        self.bootstrap_servers = ["10.0.16.5:9092", "10.0.16.7:9092", "10.0.16.6:9092"]
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                retries=3,
            )
        except Exception as e:
            logger.error(f"Kafka producer init failed: {e}")
            self.producer = None

    def publish(self, message: dict):
        if not self.producer:
            logger.warning("Kafka producer not initialized.")
            return

        try:
            message["host"] = socket.gethostname()
            self.producer.send(self.topic, message)
            self.producer.flush()
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {str(e)}")

    def consume(self):
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                group_id="audit_log_group",
            )

            logger.info(f"Kafka consumer started for topic: {self.topic}")

            for message in consumer:
                if message is None:
                    continue
                data = message.value
                logger.info(f"[KafkaAudit] Received audit log: {data}")

        except Exception as e:
            logger.error(f"Kafka consumer failed: {str(e)}")
