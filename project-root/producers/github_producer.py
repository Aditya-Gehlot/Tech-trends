#!/usr/bin/env python3
"""Producer that polls GitHub public events and streams them to Kafka."""
import time
import logging
import requests

from config import settings
from utils.kafka_utils import create_producer, send_message


class GitHubProducer:
    STATE_FILE = settings.STATE_DIR / "github_last_event_id.txt"

    def __init__(self):
        self.producer = create_producer(settings.BOOTSTRAP_SERVERS)
        self.topic = settings.GITHUB_TOPIC
        self.interval = settings.GITHUB_INTERVAL
        self.url = settings.GITHUB_EVENTS_URL
        self.token = settings.GITHUB_TOKEN
        self.last_id = self._load_last_id()

    def _load_last_id(self):
        try:
            if self.STATE_FILE.exists():
                return self.STATE_FILE.read_text().strip()
        except Exception:
            pass
        return None

    def _save_last_id(self, last_id):
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.STATE_FILE.write_text(str(last_id))
        except Exception:
            logging.exception("Failed to write state file")

    def fetch_and_send(self):
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        try:
            r = requests.get(self.url, headers=headers, timeout=15)
            r.raise_for_status()
            events = r.json()
            if not events:
                return
            new_last = self.last_id
            for ev in reversed(events):
                eid = ev.get("id")
                if not eid:
                    continue
                if self.last_id and eid <= self.last_id:
                    continue
                send_message(self.producer, self.topic, ev)
                logging.info("Sent GitHub event id=%s type=%s", ev.get("id"), ev.get("type"))
                new_last = eid
            if new_last and new_last != self.last_id:
                self.last_id = new_last
                self._save_last_id(self.last_id)
        except Exception:
            logging.exception("Error fetching GitHub events")

    def run_forever(self):
        logging.info("Starting GitHub producer (interval=%s)", self.interval)
        while True:
            self.fetch_and_send()
            time.sleep(self.interval)


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    GitHubProducer().run_forever()
