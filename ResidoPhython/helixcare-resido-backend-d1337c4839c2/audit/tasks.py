from resido.celery import app
from audit.kafka_audit import KafkaAudit
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@app.task
def listen_to_kafka_logs():
    logger.info("Listening... Kafka topic")
    kafka = KafkaAudit()
    kafka.consume()
