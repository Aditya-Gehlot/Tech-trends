#!/usr/bin/env python3
"""Producer that polls RSS/Atom feeds (e.g., dev.to) and sends new posts to Kafka."""
import time
import logging
import feedparser

from config import settings
from utils.kafka_utils import create_producer, send_message


class BlogProducer:
    STATE_FILE = settings.STATE_DIR / "blog_seen_ids.txt"

    def __init__(self):
        self.producer = create_producer(settings.BOOTSTRAP_SERVERS)
        self.topic = settings.BLOG_TOPIC
        self.interval = settings.BLOG_INTERVAL
        self.feeds = settings.BLOG_FEEDS
        self.seen = self._load_seen_ids()

    def _load_seen_ids(self):
        try:
            if self.STATE_FILE.exists():
                text = self.STATE_FILE.read_text()
                return set([l.strip() for l in text.splitlines() if l.strip()])
        except Exception:
            pass
        return set()

    def _save_seen_ids(self):
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.STATE_FILE.write_text("\n".join(sorted(self.seen)))
        except Exception:
            logging.exception("Failed to write state file")

    def fetch_and_send(self):
        try:
            for feed in self.feeds:
                parsed = feedparser.parse(feed)
                entries = parsed.entries or []
                for entry in reversed(entries):
                    eid = getattr(entry, "id", None) or getattr(entry, "link", None)
                    if not eid or eid in self.seen:
                        continue
                    payload = {
                        "source": "tech_blogs",
                        "id": eid,
                        "title": getattr(entry, "title", None),
                        "summary": getattr(entry, "summary", None),
                        "link": getattr(entry, "link", None),
                        "published": getattr(entry, "published", None),
                    }
                    send_message(self.producer, self.topic, payload)
                    logging.info("Sent blog entry id=%s title=%s", eid, payload.get("title"))
                    self.seen.add(eid)
            self._save_seen_ids()
        except Exception:
            logging.exception("Error fetching blog feeds")

    def run_forever(self):
        logging.info("Starting Blog producer (interval=%s)", self.interval)
        while True:
            self.fetch_and_send()
            time.sleep(self.interval)


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    BlogProducer().run_forever()
