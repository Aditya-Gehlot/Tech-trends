#!/usr/bin/env python3
"""Entrypoint to run producers and consumers.

Allows running all producers (in separate threads) or individual ones.
"""
import threading
import argparse
import logging

from config import settings
from producers.google_trends_producer import GoogleTrendsProducer
from producers.stackoverflow_producer import StackOverflowProducer
from producers.github_producer import GitHubProducer
from producers.blog_producer import BlogProducer
from consumers.base_consumer import BaseConsumer
from consumers.s3_raw_consumer import S3RawConsumer


def run_producer_class(cls):
    instance = cls()
    instance.run_forever()


def main():
    logging.basicConfig(level=settings.LOG_LEVEL)
    parser = argparse.ArgumentParser(description="Tech Trends Producers Runner")
    parser.add_argument("--all", action="store_true", help="Run all producers")
    parser.add_argument("--google", action="store_true")
    parser.add_argument("--stackoverflow", action="store_true")
    parser.add_argument("--github", action="store_true")
    parser.add_argument("--blogs", action="store_true")
    parser.add_argument("--consumer", action="store_true", help="Run a consumer that prints messages")
    parser.add_argument("--s3-raw-consumer", action="store_true", help="Run a consumer that writes raw Kafka messages to S3")
    args = parser.parse_args()

    threads = []
    if args.all or args.google:
        t = threading.Thread(target=run_producer_class, args=(GoogleTrendsProducer,), daemon=True)
        threads.append(t)
    if args.all or args.stackoverflow:
        t = threading.Thread(target=run_producer_class, args=(StackOverflowProducer,), daemon=True)
        threads.append(t)
    if args.all or args.github:
        t = threading.Thread(target=run_producer_class, args=(GitHubProducer,), daemon=True)
        threads.append(t)
    if args.all or args.blogs:
        t = threading.Thread(target=run_producer_class, args=(BlogProducer,), daemon=True)
        threads.append(t)
    if args.consumer:
        t = threading.Thread(target=lambda: BaseConsumer().run(), daemon=True)
        threads.append(t)
    if args.s3_raw_consumer:
        t = threading.Thread(target=lambda: S3RawConsumer().run(), daemon=True)
        threads.append(t)

    if not threads:
        parser.print_help()
        return

    for t in threads:
        t.start()
    try:
        while True:
            for t in threads:
                if not t.is_alive():
                    logging.warning("Thread %s died", t)
            threading.Event().wait(1)
    except KeyboardInterrupt:
        logging.info("Shutting down")


if __name__ == "__main__":
    main()
