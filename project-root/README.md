# Tech Trend Analytics — Real-Time Starter

This repository provides a minimal, production-minded starter for real-time tech trend ingestion using Python, Kafka and Docker.

Quick features
- Docker Compose to run Kafka + Zookeeper
- 4 producers: Google Trends, StackOverflow, GitHub events, Tech blog RSS
- Kafka utils (producer/consumer factories)
- Simple consumer to verify messages

Prerequisites
- Python 3.10+
- Docker & Docker Compose

Setup
1. Start Kafka locally (one command):

```bash
# from project root
docker-compose up -d
```

2. Install Python dependencies (recommended virtualenv)

```bash
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

3. Configure (optional)
- See `config/settings.py` for environment variables. Common ones:
  - `BOOTSTRAP_SERVERS` (default: localhost:9092)
  - `GITHUB_TOKEN` (optional, avoid rate limits)

Running producers

- Run all producers together:

```bash
python main.py --all
```

- Run individual producers:

```bash
python main.py --google
python main.py --stackoverflow
python main.py --github
python main.py --blogs
```

Consuming messages (verify)

```bash
python main.py --consumer
# or use the consumer module directly
python consumers/base_consumer.py --topics google_trends
```

Smoke test

You can run a quick programmatic smoke test that creates a topic, sends a message, and consumes it:

```bash
python smoke_test.py
```

Notes
- The docker-compose file creates the required topics automatically.
- Producers persist simple state in `.state/` to reduce duplicates while running.
- This starter keeps things small and framework-free so it can be extended with Spark/ML later.

Next steps (suggested)
- Add schema validation (pydantic) before publishing messages
- Add retries and backoff for producers (tenacity)
- Add a simple processing consumer that writes raw messages to local storage (S3/MinIO)
