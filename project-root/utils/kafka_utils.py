"""Utility helpers for Kafka producer/consumer creation and JSON (de)serialization."""
import json
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic

logger = logging.getLogger(__name__)


def create_producer(bootstrap_servers):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        retries=5,
    )


def create_consumer(topics, group_id, bootstrap_servers, auto_offset_reset='earliest'):
    if isinstance(topics, (list, tuple)):
        topics = list(topics)
    return KafkaConsumer(
        *topics if isinstance(topics, (list, tuple)) else topics,
        group_id=group_id,
        bootstrap_servers=bootstrap_servers,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")) if v else None,
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=True,
    )


def create_topics(bootstrap_servers, topics):
    try:
        admin = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
        new_topics = [NewTopic(name=t, num_partitions=1, replication_factor=1) for t in topics]
        admin.create_topics(new_topics=new_topics, validate_only=False)
        admin.close()
        logger.info("Created topics: %s", topics)
    except Exception as e:
        logger.warning("Could not create topics (they may already exist): %s", e)


def send_message(producer, topic, message, key=None):
    try:
        future = producer.send(topic, value=message, key=key.encode('utf-8') if key else None)
        producer.flush()
        return future.get(timeout=10)
    except Exception as e:
        logger.exception("Failed to send message to %s: %s", topic, e)
