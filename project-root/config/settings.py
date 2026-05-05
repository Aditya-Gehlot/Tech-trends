import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = Path(os.environ.get("STATE_DIR", BASE_DIR / ".state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Kafka
BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092")

# Topics
GOOGLE_TRENDS_TOPIC = os.environ.get("GOOGLE_TRENDS_TOPIC", "google_trends")
STACKOVERFLOW_TOPIC = os.environ.get("STACKOVERFLOW_TOPIC", "stackoverflow")
GITHUB_TOPIC = os.environ.get("GITHUB_TOPIC", "github_events")
BLOG_TOPIC = os.environ.get("BLOG_TOPIC", "tech_blogs")

# Intervals (seconds)
GOOGLE_TRENDS_INTERVAL = int(os.environ.get("GOOGLE_TRENDS_INTERVAL", 300))
STACKOVERFLOW_INTERVAL = int(os.environ.get("STACKOVERFLOW_INTERVAL", 60))
GITHUB_INTERVAL = int(os.environ.get("GITHUB_INTERVAL", 30))
BLOG_INTERVAL = int(os.environ.get("BLOG_INTERVAL", 300))

# APIs
STACKOVERFLOW_PAGE_SIZE = int(os.environ.get("STACKOVERFLOW_PAGE_SIZE", 50))
STACKOVERFLOW_API_URL = os.environ.get("STACKOVERFLOW_API_URL", "https://api.stackexchange.com/2.3/questions")
GITHUB_EVENTS_URL = os.environ.get("GITHUB_EVENTS_URL", "https://api.github.com/events")
BLOG_FEEDS = os.environ.get("BLOG_FEEDS", "https://dev.to/feed").split(",")

# Pytrends keywords (comma separated list)
PYTRENDS_KEYWORDS = os.environ.get("PYTRENDS_KEYWORDS", "python,rust,go,kubernetes,docker,spark").split(",")

# Optional tokens
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
