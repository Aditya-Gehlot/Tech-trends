import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
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

# Pytrends keywords (comma separated list). The default catalog is deliberately
# broad so local/demo streaming paths cover mature, emerging, and declining
# technologies without requiring an environment override.
DEFAULT_PYTRENDS_KEYWORDS = [
    # Programming languages
    "python programming", "python development", "python tutorials",
    "javascript development", "javascript frameworks", "vanilla javascript",
    "typescript programming", "typescript development", "typescript types",
    "java enterprise", "java development", "spring java",
    "csharp dotnet", "c# development", ".net framework", ".net core",
    "go programming language", "golang development", "go concurrency",
    "rust programming", "rust systems", "rust async",
    "php development", "php frameworks", "php 8",
    "ruby development", "ruby on rails", "sinatra ruby",
    "swift ios development", "swift programming", "ios development swift",
    "kotlin android", "kotlin development", "android kotlin",
    "r programming language", "r statistical", "r data science",
    "julia programming", "julia data science", "julia performance",
    "perl programming", "perl scripting", "perl legacy",
    "lua programming", "lua game development", "roblox lua",
    "scala programming", "scala functional", "spark scala",
    "clojure programming", "clojure functional", "clojure lisp",
    "elixir programming", "erlang elixir", "elixir phoenix",
    "haskell programming", "haskell functional", "haskell types",
    "groovy programming", "groovy jvm", "gradle groovy",
    "dart programming", "dart flutter", "dart web",
    "vb.net development", "visual basic", "vb.net frameworks",
    "powershell scripting", "powershell automation", "powershell devops",
    "bash scripting", "shell scripting", "linux bash",
    "sql programming", "tsql development", "plsql oracle",
    "html5 development", "html5 web", "semantic html",
    "css3 styling", "css animations", "css grid",
    "cobol programming", "mainframe cobol", "cobol legacy",
    "lisp programming", "ada programming", "delphi development",
    # Frontend and backend frameworks
    "react framework", "react hooks", "react components", "next.js framework",
    "vue.js framework", "vue 3 composition", "nuxt.js framework",
    "angular framework", "angular typescript", "angular enterprise",
    "svelte framework", "svelte components", "sveltekit",
    "astro framework", "astro static", "astro islands",
    "remix framework", "remix loaders", "remix actions",
    "qwik framework", "qwik resumable", "solidjs framework",
    "lit framework", "web components lit", "alpine.js",
    "htmx framework", "turbo hotwire", "stimulus.js",
    "ember.js framework", "backbone.js", "preact framework",
    "django framework", "django rest framework", "django orm",
    "flask framework", "werkzeug flask", "jinja2 templating",
    "fastapi", "fastapi async", "fastapi openapi",
    "spring boot", "spring mvc", "spring cloud",
    "express.js", "express middleware", "nodejs express",
    "nestjs framework", "nestjs typescript", "nestjs decorators",
    "asp.net core", "asp.net mvc", "entity framework",
    "laravel framework", "laravel eloquent", "laravel blade",
    "rails active record", "rails routes", "hanami framework",
    "actix web", "rocket framework", "axum rust",
    "coldfusion", "adobe coldfusion", "classic asp",
    # Styling, UI, and state
    "tailwind css", "bootstrap framework", "material design",
    "chakra ui", "ant design", "semantic ui",
    "bulma css", "pico css", "open props",
    "postcss", "sass preprocessing", "less preprocessing",
    "styled components", "emotion css", "css modules",
    "headless ui", "radix ui", "storybook development",
    "chromatic testing", "component docs", "design systems",
    "redux state management", "zustand state", "jotai atoms",
    "recoil facebook", "mobx reactive", "xstate machines",
    "pinia vue", "vuex state", "ngrx effects",
    # Databases and data platforms
    "postgresql database", "postgres sql", "postgresql json",
    "mysql database", "mariadb sql", "percona mysql",
    "oracle database", "oracle enterprise", "plsql oracle",
    "sql server", "mssql database", "sqlite database",
    "mongodb", "mongo documents", "mongodb atlas",
    "couchdb", "couchbase", "rethinkdb",
    "firebase firestore", "firestore real-time", "firebase database",
    "dynamodb", "aws dynamodb", "nosql dynamodb",
    "cassandra database", "scylladb cassandra", "apache cassandra",
    "redis", "redis cache", "redis streams",
    "memcached", "hazelcast", "aerospike database",
    "elasticsearch", "opensearch fork", "elastic stack",
    "solr search", "apache solr", "lucene search",
    "algolia search", "meilisearch", "typesense search",
    "duckdb", "duckdb analytics", "olap duckdb",
    "clickhouse", "timescale database", "influxdb time-series",
    "prometheus metrics", "graphite monitoring", "victoria metrics",
    "qdrant vector database", "weaviate vectors", "milvus embeddings",
    "pinecone embeddings", "vector database", "langchain vector",
    "chroma embeddings", "supabase postgres", "neon postgres",
    "planetscale mysql", "cockroachdb distributed", "fauna database",
    "neo4j graph database", "dgraph distributed", "aws neptune",
    "arangodb multimodel", "janusgraph", "knowledge graph database",
    "snowflake data warehouse", "databricks lakehouse", "delta lake",
    # Cloud and infrastructure
    "aws cloud", "amazon aws services", "aws lambda",
    "aws ec2", "aws s3", "aws rds", "aws dynamodb",
    "azure cloud", "microsoft azure", "azure devops",
    "azure functions", "azure container", "azure kubernetes",
    "google cloud", "gcp bigquery", "google cloud platform",
    "firebase google", "cloud run", "cloud functions",
    "heroku platform", "vercel hosting", "netlify hosting",
    "digitalocean", "linode cloud", "vultr cloud",
    "kubernetes", "k8s orchestration", "kubernetes ecosystem",
    "docker containers", "docker compose", "containerd",
    "podman containers", "container runtime", "openshift kubernetes",
    "rancher kubernetes", "helm charts", "kustomize",
    "argocd gitops", "flux gitops", "gitops deployment",
    "terraform infrastructure", "terraform aws", "hcl language",
    "ansible automation", "ansible playbooks", "saltstack",
    "puppet infrastructure", "chef configuration", "pulumi infrastructure",
    "cloudformation aws", "cdk aws", "bicep azure",
    "istio service mesh", "linkerd service mesh", "consul service mesh",
    "nginx reverse proxy", "traefik routing", "envoy proxy",
    "haproxy load balancing", "caddy web server", "apache httpd",
    # CI/CD and observability
    "github actions", "github workflows", "github ci/cd",
    "gitlab ci/cd", "gitlab pipelines", "gitlab devops",
    "jenkins ci", "jenkins pipeline", "jenkins groovy",
    "circleci", "travis ci", "azure pipelines",
    "drone ci", "buildkite", "gocd continuous delivery",
    "prometheus metrics", "grafana dashboards", "monitoring prometheus",
    "datadog monitoring", "new relic apm", "dynatrace monitoring",
    "elastic apm", "jaeger tracing", "zipkin tracing",
    "opentelemetry", "tempo loki", "loki logs",
    "splunk enterprise", "sumologic monitoring", "logz.io elk",
    # Mobile and desktop
    "react native development", "expo react native", "react native cli",
    "flutter framework", "flutter dart", "flutter mobile",
    "swiftui development", "ios sdk", "android studio",
    "android development", "xamarin", "maui dotnet",
    "ionic framework", "capacitor mobile", "cordova phonegap",
    "nativescript", "electron framework", "electron apps",
    "tauri framework", "tauri rust", "qt framework",
    "pyqt python", "wpf csharp", "windows forms",
    "javafx java", "swing java", "native macos",
    # Testing and QA
    "jest testing", "jest react testing", "jest unit tests",
    "vitest testing", "vitest vite", "vitest typescript",
    "mocha testing", "chai assertions", "sinon mocking",
    "jasmine testing", "karma test runner", "protractor e2e",
    "cypress testing", "cypress e2e", "cypress acceptance",
    "playwright automation", "puppeteer headless", "nightwatch e2e",
    "selenium webdriver", "webdriver io", "testcafe",
    "pytest testing", "pytest fixtures", "pytest plugins",
    "unittest python", "tox testing", "hypothesis testing",
    "testng testing", "junit testing", "mockito mocking",
    "rspec testing", "ruby testing", "cucumber bdd",
    "go testing", "testify go", "ginkgo bdd go",
    "standard rust", "proptest rust", "quickcheck rust",
    "loadimpact k6", "jmeter testing", "locust performance",
    "gatling scala", "chaos testing", "chaos engineering",
    # API, streaming, analytics
    "graphql api", "graphql server", "apollo graphql",
    "rest api development", "rest principles", "rest conventions",
    "openapi specification", "swagger api", "swagger ui",
    "grpc protocol", "protobuf messages", "protobuf language",
    "webhooks", "webhook events", "webhook delivery",
    "oauth 2.0", "oauth authentication", "openid connect",
    "saml authentication", "jwt tokens", "json web tokens",
    "api gateway", "kong api gateway", "apigee api management",
    "apache kafka", "kafka streams", "kafka ecosystem",
    "rabbitmq", "amqp protocol", "rabbitmq management",
    "activemq", "jms messaging", "message queue",
    "apache pulsar", "pulsar streaming", "nats messaging",
    "nats jetstream", "aws sqs", "aws sns",
    "gcp pubsub", "azure service bus", "service bus queues",
    "apache spark", "spark sql", "pyspark",
    "hadoop ecosystem", "hdfs distributed", "mapreduce",
    "apache flink", "flink streaming", "flink batch",
    "apache beam", "dataflow pipeline", "beam pipeline",
    "dbt data engineering", "dbt transformations", "dbt models",
    "airflow dag", "airflow scheduler", "prefect workflows",
    "dagster pipelines", "datahub data catalog", "data governance",
    # AI, ML, and data science
    "tensorflow machine learning", "tensorflow keras", "tensorflow lite",
    "pytorch machine learning", "pytorch lightning", "pytorch hub",
    "scikit-learn", "sklearn classification", "sklearn regression",
    "xgboost gradient", "lightgbm", "catboost",
    "hugging face transformers", "transformer models", "bert nlp",
    "langchain framework", "llamaindex vector", "semantic kernel",
    "openai api", "openai models", "chatgpt api",
    "anthropic claude", "claude api", "cohere nlp",
    "stable diffusion", "image generation", "dall-e image",
    "pandas data analysis", "polars dataframe", "dask parallel",
    "numpy numerical", "scipy scientific", "matplotlib visualization",
    "plotly interactive", "seaborn statistical", "jupyter notebooks",
    "jupyterlab", "anaconda python", "conda packages",
    # Emerging technologies
    "web3 development", "web3 blockchain", "web3 ethereum",
    "solidity smart contracts", "solidity language", "smart contract dev",
    "ethereum development", "web3.js", "ethers.js library",
    "hardhat ethereum", "truffle suite", "bitcoin development",
    "edge computing", "edge devices", "edge ai",
    "iot development", "mqtt protocol", "iot sensors",
    "raspberry pi", "arduino development", "embedded systems",
    "jetson nvidia", "tensorrt inference", "edge inference",
    "augmented reality", "virtual reality", "ar/vr development",
    "unity game engine", "unreal engine", "webxr development",
    "babylon.js 3d", "three.js webgl", "metaverse development",
    "quantum computing", "quantum algorithms", "qiskit quantum",
    "cirq google quantum", "aws braket", "web assembly",
    "wasm webassembly", "webassembly binary", "emscripten wasm",
    "wasm-bindgen rust", "wasmtime runtime", "wasmer runtime",
    "low code platforms", "no code development", "zapier automation",
    "make automation", "workflow automation", "airtable base",
    "notion database", "bubble low code", "webflow designer",
    # Security, CMS, and commerce
    "owasp security", "web security", "application security",
    "hashicorp vault", "secrets management", "key management",
    "snyk security", "dependabot updates", "security scanning",
    "sonarqube code quality", "codeql analysis", "trivy vulnerability",
    "waf web firewall", "kms encryption", "zero trust security",
    "wordpress cms", "wordpress plugins", "wordpress development",
    "drupal cms", "drupal modules", "headless drupal",
    "joomla cms", "umbraco cms", "ghost blog",
    "hugo static site", "jekyll github pages", "headless cms",
    "shopify platform", "woocommerce wordpress", "bigcommerce platform",
    "magento commerce", "prestashop ecommerce", "saleor ecommerce",
    "medusa ecommerce", "vendure ecommerce",
    # Original keywords preserved
    "AI Agents", "LLM", "Generative AI", "Cybersecurity",
    "Cloud Computing", "DevOps", "Edge AI", "Robotics",
    "Web3", "Semiconductors", "SaaS", "Data Engineering",
    "Automation", "MLOps", "Open Source AI", "GPU Infrastructure",
    "Developer Tools", "Vector Databases", "Inference Optimization",
    "Enterprise AI", "AI Agents trends", "large language models",
    "generative AI models", "cybersecurity threats", "cloud security",
    "devops practices", "edge computing deployment", "robotics automation",
    "blockchain technology", "semiconductor manufacturing", "saas platforms",
    "data pipelines", "workflow automation", "machine learning operations",
    "open source projects", "gpu computing", "developer experience",
    "vector embeddings", "model inference", "enterprise adoption",
]

PYTRENDS_KEYWORDS = [
    item.strip()
    for item in os.environ.get("PYTRENDS_KEYWORDS", ",".join(DEFAULT_PYTRENDS_KEYWORDS)).split(",")
    if item.strip()
]
PYTRENDS_TIMEOUT_SECONDS = int(os.environ.get("PYTRENDS_TIMEOUT_SECONDS", 10))
PYTRENDS_RETRIES = int(os.environ.get("PYTRENDS_RETRIES", 2))
PYTRENDS_BACKOFF_FACTOR = float(os.environ.get("PYTRENDS_BACKOFF_FACTOR", 0.5))

# Optional tokens
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

# S3 / object storage
RAW_S3_BUCKET = os.environ.get("RAW_S3_BUCKET")
RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "raw")
RAW_S3_REGION = os.environ.get("RAW_S3_REGION", "us-east-1")
RAW_S3_ENDPOINT_URL = os.environ.get("RAW_S3_ENDPOINT_URL")
RAW_S3_ACCESS_KEY_ID = os.environ.get("RAW_S3_ACCESS_KEY_ID")
RAW_S3_SECRET_ACCESS_KEY = os.environ.get("RAW_S3_SECRET_ACCESS_KEY")
RAW_S3_BATCH_SIZE = int(os.environ.get("RAW_S3_BATCH_SIZE", 100))
RAW_S3_FLUSH_INTERVAL = int(os.environ.get("RAW_S3_FLUSH_INTERVAL", 60))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Helper: treat unset and empty env vars the same for path settings
def _path_from_env(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return Path(default)
    return Path(raw)


def _bool_from_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}

# Processed data, feature store and ML paths
PROCESSED_DIR = _path_from_env("PROCESSED_DIR", BASE_DIR / "processed")
FEATURE_STORE_DIR = _path_from_env("FEATURE_STORE_DIR", BASE_DIR / "feature_store")
ML_MODELS_DIR = _path_from_env("ML_MODELS_DIR", BASE_DIR / "ml" / "models")
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
FEATURE_WINDOW_DAYS = int(os.environ.get("FEATURE_WINDOW_DAYS", 7))
FEATURE_WRITE_DAILY_PARTITIONS = _bool_from_env("FEATURE_WRITE_DAILY_PARTITIONS", False)
ML_TRAIN_XGBOOST = _bool_from_env("ML_TRAIN_XGBOOST", False)
ML_TRAIN_PROPHET = _bool_from_env("ML_TRAIN_PROPHET", False)
ML_RANDOM_FOREST_ESTIMATORS = int(os.environ.get("ML_RANDOM_FOREST_ESTIMATORS", 100))
ML_CV_SPLITS = int(os.environ.get("ML_CV_SPLITS", 3))
ML_MAX_TRAINING_ROWS = int(os.environ.get("ML_MAX_TRAINING_ROWS", 0))

# PostgreSQL persistence. Raw generated files remain local; DB persistence starts
# at normalized processed records and pipeline metadata.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/techtrends",
)
ENABLE_DB_PERSISTENCE = _bool_from_env("ENABLE_DB_PERSISTENCE", False)
STORE_NORMALIZED_RECORDS = _bool_from_env("STORE_NORMALIZED_RECORDS", False)
STORE_NORMALIZED_RECORDS_MAX_ROWS = int(os.environ.get("STORE_NORMALIZED_RECORDS_MAX_ROWS", 0))
CLEAN_DB_LATEST_ONLY = _bool_from_env("CLEAN_DB_LATEST_ONLY", False)
DB_BATCH_SIZE = int(os.environ.get("DB_BATCH_SIZE", 1000))
DB_ECHO = _bool_from_env("DB_ECHO", False)
DB_CONNECT_TIMEOUT_SECONDS = int(os.environ.get("DB_CONNECT_TIMEOUT_SECONDS", 5))

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
