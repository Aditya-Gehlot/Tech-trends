"""Simple smoke test: create a topic, produce one message, and consume it."""
import time
import logging
from datetime import datetime

from config import settings
from utils.kafka_utils import create_producer, create_consumer, create_topics, send_message


def run_smoke_test():
    logging.basicConfig(level=settings.LOG_LEVEL)
    topic = "smoke_test"
    logging.info("Creating topic '%s' (if not exists)", topic)
    create_topics(settings.BOOTSTRAP_SERVERS, [topic])

    prod = create_producer(settings.BOOTSTRAP_SERVERS)
    payload = {"test": "hello", "ts": datetime.utcnow().isoformat() + "Z"}
    logging.info("Sending test message to %s: %s", topic, payload)
    send_message(prod, topic, payload)

    logging.info("Consuming from topic %s", topic)
    cons = create_consumer([topic], group_id="smoke-test-group", bootstrap_servers=settings.BOOTSTRAP_SERVERS, auto_offset_reset="earliest")
    start = time.time()
    try:
        for msg in cons:
            logging.info("Received message: %s", msg.value)
            break
            if time.time() - start > 15:
                logging.warning("Timed out waiting for message")
                break
    except Exception:
        logging.exception("Error while consuming smoke test message")
    finally:
        try:
            cons.close()
        except Exception:
            pass


if __name__ == "__main__":
    run_smoke_test()
