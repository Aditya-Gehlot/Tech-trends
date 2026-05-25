#!/usr/bin/env python3
"""Producer for Google Trends using pytrends.

Sends summarized interest_over_time to Kafka topic defined in config.
"""
import time
import logging
from pytrends.request import TrendReq

from config import settings
from utils.kafka_utils import create_producer, send_message


class GoogleTrendsProducer:
    def __init__(self):
        self.producer = create_producer(settings.BOOTSTRAP_SERVERS)
        self.topic = settings.GOOGLE_TRENDS_TOPIC
        self.keywords = settings.PYTRENDS_KEYWORDS
        self.interval = settings.GOOGLE_TRENDS_INTERVAL
        self.pytrends = None

    def _get_client(self):
        if self.pytrends is None:
            self.pytrends = TrendReq(
                hl="en-US",
                tz=360,
                timeout=(10, settings.PYTRENDS_TIMEOUT_SECONDS),
            )
        return self.pytrends

    def fetch(self):
        attempts = max(1, settings.PYTRENDS_RETRIES + 1)
        for attempt in range(1, attempts + 1):
            try:
                pytrends = self._get_client()
                pytrends.build_payload(self.keywords, cat=0, timeframe='now 1-H', geo='', gprop='')
                df = pytrends.interest_over_time()
                if df is None or df.empty:
                    logging.info("pytrends returned no data")
                    return None
                latest = df.iloc[-1]
                ts = latest.name.isoformat()
                terms = []
                for kw in self.keywords:
                    val = int(latest.get(kw, 0)) if kw in df.columns else 0
                    terms.append({"term": kw, "value": val})
                return {"source": "google_trends", "timestamp": ts, "values": terms}
            except Exception as e:
                self.pytrends = None
                if attempt == attempts:
                    logging.exception("Error fetching Google Trends: %s", e)
                    return None
                sleep_seconds = settings.PYTRENDS_BACKOFF_FACTOR * attempt
                logging.warning(
                    "Google Trends attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt,
                    attempts,
                    e,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)

    def run_forever(self):
        logging.info("Starting Google Trends producer (interval=%s)", self.interval)
        while True:
            payload = self.fetch()
            if payload:
                send_message(self.producer, self.topic, payload)
                logging.info("Sent google_trends payload: %s", payload)
            time.sleep(self.interval)


if __name__ == "__main__":
    logging.basicConfig(level=settings.LOG_LEVEL)
    GoogleTrendsProducer().run_forever()
