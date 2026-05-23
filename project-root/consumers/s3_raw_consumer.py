#!/usr/bin/env python3
"""Consume Kafka messages and persist raw payloads into S3-compatible storage."""
import argparse
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone

import boto3

from config import settings
from utils.kafka_utils import create_consumer


class S3RawConsumer:
    def __init__(self, topics=None, group_id="tech-trends-s3-raw-consumer"):
        if not settings.RAW_S3_BUCKET:
            raise ValueError("RAW_S3_BUCKET must be set before running the S3 raw consumer")

        self.topics = topics or [
            settings.GOOGLE_TRENDS_TOPIC,
            settings.STACKOVERFLOW_TOPIC,
            settings.GITHUB_TOPIC,
            settings.BLOG_TOPIC,
        ]
        self.group_id = group_id
        self.batch_size = settings.RAW_S3_BATCH_SIZE
        self.flush_interval = settings.RAW_S3_FLUSH_INTERVAL
        self.bucket = settings.RAW_S3_BUCKET
        self.prefix = settings.RAW_S3_PREFIX.strip("/")
        self.buffers = defaultdict(list)
        self.last_flush_at = time.time()
        self.consumer = create_consumer(
            self.topics,
            group_id=self.group_id,
            bootstrap_servers=settings.BOOTSTRAP_SERVERS,
        )
        self.s3 = boto3.client(
            "s3",
            region_name=settings.RAW_S3_REGION,
            endpoint_url=settings.RAW_S3_ENDPOINT_URL,
            aws_access_key_id=settings.RAW_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.RAW_S3_SECRET_ACCESS_KEY,
        )

    def _object_key(self, topic):
        now = datetime.now(timezone.utc)
        date_path = now.strftime("%Y/%m/%d")
        timestamp = now.strftime("%H%M%S")
        return f"{self.prefix}/{topic}/{date_path}/{timestamp}-{int(now.timestamp() * 1000)}.jsonl"

    def _serialize_record(self, msg):
        record = {
            "topic": msg.topic,
            "partition": msg.partition,
            "offset": msg.offset,
            "timestamp": msg.timestamp,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "payload": msg.value,
        }
        return json.dumps(record, separators=(",", ":"))

    def _flush_topic(self, topic):
        records = self.buffers.get(topic)
        if not records:
            return

        body = "\n".join(records) + "\n"
        key = self._object_key(topic)
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/x-ndjson",
        )
        logging.info("Uploaded %d records to s3://%s/%s", len(records), self.bucket, key)
        self.buffers[topic].clear()

    def flush_all(self):
        for topic in list(self.buffers):
            self._flush_topic(topic)
        self.last_flush_at = time.time()

    def run(self):
        logging.info("Starting S3 raw consumer for topics: %s", self.topics)
        try:
            for msg in self.consumer:
                self.buffers[msg.topic].append(self._serialize_record(msg))
                buffer_count = len(self.buffers[msg.topic])
                elapsed = time.time() - self.last_flush_at

                if buffer_count >= self.batch_size or elapsed >= self.flush_interval:
                    self.flush_all()
        except Exception:
            logging.exception("S3 raw consumer error")
            raise
        finally:
            try:
                self.flush_all()
            finally:
                self.consumer.close()


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    parser = argparse.ArgumentParser()
    parser.add_argument("--topics", help="Comma-separated topics", default=None)
    args = parser.parse_args()
    topics = args.topics.split(",") if args.topics else None
    consumer = S3RawConsumer(topics=topics)
    consumer.run()
