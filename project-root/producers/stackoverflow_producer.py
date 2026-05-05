#!/usr/bin/env python3
"""Producer that polls StackOverflow for recent questions and sends to Kafka."""
import time
import logging
from datetime import datetime
import requests

from config import settings
from utils.kafka_utils import create_producer, send_message


class StackOverflowProducer:
    STATE_FILE = settings.STATE_DIR / "stackoverflow_last_id.txt"

    def __init__(self):
        self.producer = create_producer(settings.BOOTSTRAP_SERVERS)
        self.topic = settings.STACKOVERFLOW_TOPIC
        self.interval = settings.STACKOVERFLOW_INTERVAL
        self.page_size = settings.STACKOVERFLOW_PAGE_SIZE
        self.api_url = settings.STACKOVERFLOW_API_URL
        self.last_id = self._load_last_id()

    def _load_last_id(self):
        try:
            if self.STATE_FILE.exists():
                return int(self.STATE_FILE.read_text().strip())
        except Exception:
            pass
        return 0

    def _save_last_id(self, last_id):
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.STATE_FILE.write_text(str(last_id))
        except Exception:
            logging.exception("Failed to write state file")

    def fetch_and_send(self):
        params = {"order": "desc", "sort": "creation", "site": "stackoverflow", "pagesize": self.page_size}
        try:
            r = requests.get(self.api_url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            items = data.get("items", [])
            if not items:
                return
            new_last = self.last_id
            # iterate oldest -> newest
            for item in reversed(items):
                qid = item.get("question_id")
                if not qid or qid <= self.last_id:
                    continue
                payload = {
                    "source": "stackoverflow",
                    "question_id": qid,
                    "title": item.get("title"),
                    "tags": item.get("tags"),
                    "creation_date": datetime.utcfromtimestamp(item.get("creation_date")).isoformat() + "Z",
                    "link": item.get("link")
                }
                send_message(self.producer, self.topic, payload)
                logging.info("Sent StackOverflow question: %s", payload.get("question_id"))
                if qid > new_last:
                    new_last = qid
            if new_last != self.last_id:
                self.last_id = new_last
                self._save_last_id(self.last_id)
        except Exception:
            logging.exception("Error fetching StackOverflow questions")

    def run_forever(self):
        logging.info("Starting StackOverflow producer (interval=%s)", self.interval)
        while True:
            self.fetch_and_send()
            time.sleep(self.interval)


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    StackOverflowProducer().run_forever()
