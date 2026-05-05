#!/usr/bin/env python3
"""Simple base consumer to subscribe and print messages from Kafka topics."""
import logging
import argparse

from config import settings
from utils.kafka_utils import create_consumer


class BaseConsumer:
    def __init__(self, topics=None, group_id="tech-trends-consumer"):
        self.topics = topics or [settings.GOOGLE_TRENDS_TOPIC, settings.STACKOVERFLOW_TOPIC, settings.GITHUB_TOPIC, settings.BLOG_TOPIC]
        self.group_id = group_id
        self.consumer = create_consumer(self.topics, group_id=self.group_id, bootstrap_servers=settings.BOOTSTRAP_SERVERS)

    def run(self):
        logging.info("Starting consumer for topics: %s", self.topics)
        try:
            for msg in self.consumer:
                logging.info("Consumed %s:%d:%d %s", msg.topic, msg.partition, msg.offset, msg.value)
        except Exception:
            logging.exception("Consumer error")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", help="Comma-separated topics", default=None)
    args = parser.parse_args()
    topics = args.topics.split(",") if args.topics else None
    c = BaseConsumer(topics=topics)
    c.run()
