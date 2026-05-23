# Tech Trend Analytics — Real-Time Starter

This repository provides a minimal, production-minded starter for real-time tech trend ingestion using Python, Kafka and Docker.

Quick features
- Docker Compose to run Kafka + Zookeeper
- 4 producers: Google Trends, StackOverflow, GitHub events, Tech blog RSS
- Kafka utils (producer/consumer factories)
- Simple consumer to verify messages
- Raw ingestion consumer that writes newline-delimited JSON to S3/MinIO

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

3. Create local environment file

```powershell
Copy-Item .env.example .env
```

Then edit `.env` with your AWS and S3 values. The app now loads `.env` automatically on startup.

4. Configure (optional)
- See `config/settings.py` for environment variables. Common ones:
  - `BOOTSTRAP_SERVERS` (default: localhost:9092)
  - `GITHUB_TOKEN` (optional, avoid rate limits)
  - `RAW_S3_BUCKET` (required for S3 raw ingestion)
  - `RAW_S3_PREFIX` (default: `raw`)
  - `RAW_S3_REGION` (default: `us-east-1`)
  - `RAW_S3_ENDPOINT_URL` (use for MinIO or non-AWS S3)
  - `RAW_S3_ACCESS_KEY_ID` / `RAW_S3_SECRET_ACCESS_KEY`
  - `RAW_S3_BATCH_SIZE` (default: `100`)
  - `RAW_S3_FLUSH_INTERVAL` (default: `60` seconds)

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

Raw data ingestion to S3

1. Export your object-store settings.

You can either place these in `.env` or export them in the shell.

AWS S3:

```bash
export RAW_S3_BUCKET=my-techtrends-raw
export RAW_S3_REGION=us-east-1
export RAW_S3_PREFIX=raw
```

Windows PowerShell:

```powershell
$env:RAW_S3_BUCKET="my-techtrends-raw"
$env:RAW_S3_REGION="us-east-1"
$env:RAW_S3_PREFIX="raw"
```

MinIO / local S3-compatible storage:

```powershell
$env:RAW_S3_BUCKET="techtrends-raw"
$env:RAW_S3_REGION="us-east-1"
$env:RAW_S3_PREFIX="raw"
$env:RAW_S3_ENDPOINT_URL="http://localhost:9000"
$env:RAW_S3_ACCESS_KEY_ID="minioadmin"
$env:RAW_S3_SECRET_ACCESS_KEY="minioadmin"
```

2. Start producers:

```bash
python main.py --all
```

3. Start the raw-ingestion consumer in another terminal:

```bash
python main.py --s3-raw-consumer
```

This writes `.jsonl` objects like:

```text
raw/github_events/2026/05/23/143015-1748001015123.jsonl
```

Each line contains Kafka metadata plus the original producer payload:

```json
{"topic":"github_events","partition":0,"offset":12,"timestamp":1748001014000,"ingested_at":"2026-05-23T14:30:15.123456+00:00","payload":{"id":"123","type":"PushEvent"}}
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
- Partition S3 keys further by source/hour if downstream Athena queries are planned
