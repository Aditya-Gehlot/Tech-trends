# Market Intelligence Dataset Catalog

This catalog documents the synthetic datasets generated for TechTrends. The data is designed to be CSV-ready and realistic enough for analytics, reporting, and ML prototyping while remaining synthetic.

## linkedin_jobs.csv

Rows: `60106`

### Schema

| Field | Description |
|---|---|
| `job_id` | Unique job posting identifier |
| `posted_at` | Posting timestamp |
| `company_id` | Cross-dataset company key |
| `company` | Employer or startup name |
| `role` | Job title |
| `location` | City |
| `country` | Country name |
| `salary_usd` | Estimated annual compensation in USD |
| `skills` | Comma-separated skills and tools |
| `tech_category` | Primary technology trend represented by the role |
| `hiring_index` | Hiring demand proxy influenced by market conditions |
| `risk_indicator` | Operational or market risk label |

### Sample Records

```json
[
  {
    "job_id": "JOB-100000",
    "posted_at": "2025-01-01T08:00:00",
    "company": "OpenAI",
    "role": "Applied Scientist",
    "location": "New York",
    "salary_usd": 169683.0,
    "experience_years": 2,
    "skills": "FastAPI, RAG, Tool Calling, OpenAI API, LangChain",
    "job_description": "OpenAI is hiring a Applied Scientist in New York to scale ai agents initiatives across enterprise and developer workflows. The team is focused on agent reliability while supporting production customers. Candidates should be comfortable with FastAPI, RAG, Tool Calling and cross-functional delivery in a fast-moving market.",
    "company_id": "CMP-001",
    "country": "United States",
    "region": "North America",
    "tech_category": "AI Agents",
    "hiring_index": 75.33,
    "funding_signal": 1.13,
    "sentiment_score": 0.225,
    "trend_score": 57.87,
    "popularity_growth_pct": 1.79,
    "volatility_metric": 7.63,
    "innovation_score": 89.21,
    "adoption_score": 71.09,
    "risk_indicator": "low",
    "job_market_demand_index": 86.18,
    "education_enrollment_index": 74.75,
    "community_health_score": 61.69,
    "package_downloads_weekly": 3549401,
    "source_platform": "LinkedIn"
  },
  {
    "job_id": "JOB-100001",
    "posted_at": "2025-01-01T20:00:00",
    "company": "OpenAI",
    "role": "AI Solutions Architect",
    "location": "Seattle",
    "salary_usd": 190914.0,
    "experience_years": 6,
    "skills": "Snowflake, Databricks, Governance, Security, Azure",
    "job_description": "OpenAI is hiring a AI Solutions Architect in Seattle to scale enterprise ai initiatives across enterprise and developer workflows. The team is focused on agent reliability while supporting open-source contributors. Candidates should be comfortable with Snowflake, Databricks, Governance and cross-functional delivery in a fast-moving market.",
    "company_id": "CMP-001",
    "country": "United States",
    "region": "North America",
    "tech_category": "Enterprise AI",
    "hiring_index": 75.33,
    "funding_signal": 1.13,
    "sentiment_score": 0.225,
    "trend_score": 57.87,
    "popularity_growth_pct": 1.79,
    "volatility_metric": 7.63,
    "innovation_score": 89.21,
    "adoption_score": 71.09,
    "risk_indicator": "low",
    "job_market_demand_index": 86.18,
    "education_enrollment_index": 74.75,
    "community_health_score": 61.69,
    "package_downloads_weekly": 3549401,
    "source_platform": "LinkedIn"
  }
]
```

### Expected Analytics Usage

- hiring trend dashboards
- regional salary benchmarking
- funding-to-hiring lag analysis

### Suggested ML Use-Cases

- hiring demand forecasting
- salary regression
- location recommendation

## twitter_stream.csv

Rows: `174620`

### Schema

| Field | Description |
|---|---|
| `tweet_id` | Unique social post identifier |
| `created_at` | Tweet timestamp |
| `tech_topic` | Primary technology topic |
| `company_id` | Referenced company |
| `followers` | Audience size of author |
| `likes` | Engagement count |
| `retweets` | Reshare count |
| `sentiment_score` | Continuous sentiment signal |
| `volatility_metric` | Daily instability proxy |
| `ai_summary` | Generated digest of conversation context |

### Sample Records

```json
[
  {
    "tweet_id": "TWT-200000",
    "created_at": "2025-01-01T10:55:00",
    "username": "vector_32127",
    "followers": 4209,
    "tech_topic": "AI Agents",
    "sentiment": null,
    "likes": 2676,
    "retweets": 701,
    "content": "Scale AI keeps showing up in AI Agents discussions as teams focus on GPU capacity. #AIAgents #US #scaleai",
    "company_id": "CMP-009",
    "company": "Scale AI",
    "country": "United States",
    "region": "North America",
    "trend_score": 51.72,
    "sentiment_score": 0.19,
    "funding_estimate_musd": 172.12,
    "hiring_activity_index": 49.7,
    "hashtags": "#AIAgents|#US|#scaleai",
    "popularity_growth_pct": 0.6,
    "volatility_metric": 6.76,
    "package_downloads_weekly": 2071173,
    "github_activity_index": 61.03,
    "stackoverflow_question_volume": 9,
    "job_market_demand_index": 86.62,
    "education_enrollment_index": 82.13,
    "conference_talks": 15,
    "documentation_health_score": 87.47,
    "community_health_score": 59.66,
    "ai_summary": "Analysts note that ai agents usage patterns on Jan 01, 2025 reflect both hype and practical deployment pressure. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "risk_indicator": "low",
    "innovation_score": 88.51,
    "adoption_score": 67.29,
    "source_reference": "https://x.example.com/CMP-009/200000"
  },
  {
    "tweet_id": "TWT-200001",
    "created_at": "2025-01-01T16:00:00",
    "username": "ml_88901",
    "followers": 4652,
    "tech_topic": "AI Agents",
    "sentiment": "positive",
    "likes": 2528,
    "retweets": 771,
    "content": "OpenAI keeps showing up in AI Agents discussions as teams focus on cost-efficient deployment. #AIAgents #JP #openai",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "Japan",
    "region": "Asia",
    "trend_score": 45.74,
    "sentiment_score": 0.215,
    "funding_estimate_musd": 165.53,
    "hiring_activity_index": 53.28,
    "hashtags": "#AIAgents|#JP|#openai",
    "popularity_growth_pct": 4.32,
    "volatility_metric": 8.36,
    "package_downloads_weekly": 2828318,
    "github_activity_index": 53.97,
    "stackoverflow_question_volume": 28,
    "job_market_demand_index": 82.32,
    "education_enrollment_index": 78.84,
    "conference_talks": 13,
    "documentation_health_score": 78.55,
    "community_health_score": 63.84,
    "ai_summary": "OpenAI teams are discussing how ai agents is moving from experimentation into production buying cycles. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "risk_indicator": "low",
    "innovation_score": 90.55,
    "adoption_score": 69.94,
    "source_reference": "https://x.example.com/CMP-001/200001"
  }
]
```

### Expected Analytics Usage

- sentiment and buzz monitoring
- trend spike detection
- regional share-of-voice reporting

### Suggested ML Use-Cases

- sentiment classification
- engagement prediction
- duplicate detection

## github_events.csv

Rows: `38552`

### Schema

| Field | Description |
|---|---|
| `event_id` | Unique repository activity identifier |
| `event_time` | Event date |
| `repository` | Repository slug |
| `language` | Main implementation language |
| `stars_added` | Stars gained on event day |
| `forks_added` | Forks gained on event day |
| `contributors` | Estimated contributor count |
| `topic` | Mapped technology trend |

### Sample Records

```json
[
  {
    "event_id": "GIT-300000",
    "event_time": "2025-01-01T00:00:00",
    "repository": "openai/ai-agents-ops",
    "language": "Python",
    "stars_added": 343,
    "forks_added": 141,
    "contributors": 21,
    "topic": "AI Agents",
    "event_type": "push",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "region": "North America",
    "issue_count": 7,
    "watchers_added": 102,
    "release_flag": false,
    "trend_score": 57.87,
    "popularity_growth_pct": 1.79,
    "volatility_metric": 7.63,
    "innovation_score": 89.21,
    "adoption_score": 71.09,
    "github_activity_index": 48.34,
    "package_downloads_weekly": 3549401,
    "documentation_health_score": 83.59,
    "community_health_score": 61.69,
    "risk_indicator": "low",
    "ai_summary": "Developers are comparing tooling choices around ai agents as budget owners ask for faster ROI and clearer governance. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption."
  },
  {
    "event_id": "GIT-300001",
    "event_time": "2025-01-03T00:00:00",
    "repository": "openai/generative-ai-platform",
    "language": "Python",
    "stars_added": 228,
    "forks_added": 133,
    "contributors": 18,
    "topic": "Generative AI",
    "event_type": "pull_request",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "region": "North America",
    "issue_count": 12,
    "watchers_added": 27,
    "release_flag": false,
    "trend_score": 56.38,
    "popularity_growth_pct": 0.57,
    "volatility_metric": 8.73,
    "innovation_score": 88.09,
    "adoption_score": 71.27,
    "github_activity_index": 47.58,
    "package_downloads_weekly": 2663788,
    "documentation_health_score": 75.36,
    "community_health_score": 59.01,
    "risk_indicator": "low",
    "ai_summary": "OpenAI teams are discussing how generative ai is moving from experimentation into production buying cycles. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption."
  }
]
```

### Expected Analytics Usage

- open-source momentum scoring
- repo health analysis
- developer ecosystem correlation studies

### Suggested ML Use-Cases

- star/fork growth modeling
- repo anomaly detection
- topic popularity forecasting

## tech_blogs.csv

Rows: `36350`

### Schema

| Field | Description |
|---|---|
| `article_id` | Unique article identifier |
| `published_at` | Publication timestamp |
| `source` | Blog platform or publication |
| `topic` | Primary theme |
| `title` | Article headline |
| `views` | Estimated article views |
| `summary` | Article summary text |

### Sample Records

```json
[
  {
    "article_id": "ART-400000",
    "published_at": "2025-01-05T00:00:00",
    "source": "Medium",
    "author": "Noah Wright",
    "topic": "AI Agents",
    "title": "AI Agents buying signals in 2025: what Replit signals imply",
    "views": 28863,
    "reading_time_minutes": 5,
    "summary": "Developers are comparing tooling choices around ai agents as budget owners ask for faster ROI and clearer governance. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "company_id": "CMP-014",
    "company": "Replit",
    "country": "Germany",
    "region": "Europe",
    "trend_score": 44.49,
    "sentiment_score": 0.272,
    "funding_estimate_musd": 50.42,
    "hiring_activity_index": 59.7,
    "hashtags": "#aiagents|#DE",
    "popularity_growth_pct": -3.76,
    "volatility_metric": 7.98,
    "risk_indicator": "low",
    "innovation_score": 90.5,
    "adoption_score": 65.12,
    "source_reference": "https://blog.example.com/400000"
  },
  {
    "article_id": "ART-400001",
    "published_at": "2025-01-05T00:00:00",
    "source": "Substack",
    "author": "Ava Patel",
    "topic": "AI Agents",
    "title": "AI Agents enterprise rollout in 2025: what OpenAI signals imply",
    "views": 70680,
    "reading_time_minutes": 10,
    "summary": "Developers are comparing tooling choices around ai agents as budget owners ask for faster ROI and clearer governance. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "Singapore",
    "region": "Asia",
    "trend_score": 48.53,
    "sentiment_score": 0.169,
    "funding_estimate_musd": 44.24,
    "hiring_activity_index": 53.47,
    "hashtags": "#aiagents|#SG",
    "popularity_growth_pct": -3.39,
    "volatility_metric": 9.99,
    "risk_indicator": "moderate",
    "innovation_score": 86.86,
    "adoption_score": 62.21,
    "source_reference": "https://blog.example.com/400001"
  }
]
```

### Expected Analytics Usage

- content engagement dashboards
- topic narrative analysis
- innovation storytelling analysis

### Suggested ML Use-Cases

- summary quality ranking
- topic classification
- engagement prediction

## stackoverflow_questions.csv

Rows: `109885`

### Schema

| Field | Description |
|---|---|
| `question_id` | Question identifier |
| `created_at` | Question timestamp |
| `tag` | Primary technical tag |
| `views` | Question views |
| `answers` | Answer count |
| `accepted_answer` | Whether accepted solution exists |

### Sample Records

```json
[
  {
    "question_id": "SO-500000",
    "created_at": "2025-01-02T00:00:00",
    "tag": "AI Agents",
    "views": 6439,
    "answers": 10,
    "score": 56,
    "accepted_answer": true,
    "title": "Best production pattern for AI Agents with Anthropic stack?",
    "body_preview": "Our team is deploying ai agents workloads and seeing issues around hallucination risk. We use components similar to Anthropic and need guidance for production-ready patterns.",
    "company_id": "CMP-002",
    "company": "Anthropic",
    "country": "United Arab Emirates",
    "trend_score": 48.58,
    "sentiment_score": 0.053,
    "popularity_growth_pct": 7.01,
    "volatility_metric": 12.08,
    "innovation_score": 95.83,
    "adoption_score": 65.58,
    "stackoverflow_question_volume": 42,
    "documentation_health_score": 78.94,
    "community_health_score": 54.82,
    "package_downloads_weekly": 3032290,
    "risk_indicator": "moderate",
    "source_reference": "https://stackoverflow.example.com/questions/500000"
  },
  {
    "question_id": "SO-500001",
    "created_at": "2025-01-02T00:00:00",
    "tag": "AI Agents",
    "views": 6018,
    "answers": 5,
    "score": 35,
    "accepted_answer": true,
    "title": "Why is AI Agents latency spiking after deployment?",
    "body_preview": "Our team is deploying ai agents workloads and seeing issues around schema drift. We use components similar to OpenAI and need guidance for production-ready patterns.",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "Japan",
    "trend_score": 44.61,
    "sentiment_score": 0.272,
    "popularity_growth_pct": -2.47,
    "volatility_metric": 9.15,
    "innovation_score": 92.86,
    "adoption_score": 67.28,
    "stackoverflow_question_volume": 19,
    "documentation_health_score": 83.78,
    "community_health_score": 47.87,
    "package_downloads_weekly": 3275359,
    "risk_indicator": "moderate",
    "source_reference": "https://stackoverflow.example.com/questions/500001"
  }
]
```

### Expected Analytics Usage

- developer pain-point analysis
- question volume forecasting
- support burden estimation

### Suggested ML Use-Cases

- answer likelihood prediction
- topic difficulty clustering
- support load forecasting

## google_trends.csv

Rows: `746900`

### Schema

| Field | Description |
|---|---|
| `date` | Daily trend observation date |
| `keyword` | Tracked topic keyword |
| `trend_score` | Normalized interest score |
| `region` | Country code |
| `popularity_growth_pct` | Day-over-day growth |

### Sample Records

```json
[
  {
    "date": "2025-01-01",
    "keyword": "AI Agents",
    "trend_score": 52,
    "region": "US",
    "country": "United States",
    "tech_category": "AI Agents",
    "sentiment_score": 0.132,
    "popularity_growth_pct": 0.6,
    "volatility_metric": 6.76,
    "innovation_score": 88.51,
    "adoption_score": 67.29,
    "package_downloads_weekly": 2071173,
    "github_activity_index": 61.03,
    "stackoverflow_question_volume": 9,
    "job_market_demand_index": 86.62,
    "education_enrollment_index": 82.13,
    "conference_talks": 15,
    "documentation_health_score": 87.47,
    "community_health_score": 59.66,
    "risk_indicator": "low",
    "event_refs": ""
  },
  {
    "date": "2025-01-01",
    "keyword": "AI Agents",
    "trend_score": 48,
    "region": "IN",
    "country": "India",
    "tech_category": "AI Agents",
    "sentiment_score": 0.21,
    "popularity_growth_pct": 3.98,
    "volatility_metric": 9.47,
    "innovation_score": 94.6,
    "adoption_score": 67.77,
    "package_downloads_weekly": 2239482,
    "github_activity_index": 56.6,
    "stackoverflow_question_volume": 14,
    "job_market_demand_index": 83.92,
    "education_enrollment_index": 80.06,
    "conference_talks": 14,
    "documentation_health_score": 85.58,
    "community_health_score": 49.23,
    "risk_indicator": "moderate",
    "event_refs": ""
  }
]
```

### Expected Analytics Usage

- time-series trend dashboards
- market seasonality analysis
- country-level momentum comparison

### Suggested ML Use-Cases

- multivariate time-series forecasting
- changepoint detection
- volatility classification

## reddit_discussions.csv

Rows: `81426`

### Schema

| Field | Description |
|---|---|
| `reddit_post_id` | Discussion identifier |
| `subreddit` | Source community |
| `upvotes` | Community endorsement count |
| `comments` | Reply count |
| `company_id` | Referenced company |

### Sample Records

```json
[
  {
    "reddit_post_id": "RDT-600000",
    "created_at": "2025-01-01T20:29:00",
    "subreddit": "r/startups",
    "username": "cloud_89685",
    "topic": "AI Agents",
    "title": "Is AI Agents still underhyped or already overheating?",
    "body": "Seeing more teams mention Replit whenever ai agents comes up. Feels like adoption is real in Canada, but the debate around moats keeps resurfacing.",
    "upvotes": 923,
    "comments": 236,
    "sentiment_score": 0.408,
    "company_id": "CMP-014",
    "company": "Replit",
    "country": "Canada",
    "region": "North America",
    "trend_score": 47.5,
    "funding_estimate_musd": 17.46,
    "hiring_activity_index": 41.27,
    "hashtags": "#aiagents|#CA",
    "popularity_growth_pct": 4.17,
    "volatility_metric": 8.66,
    "ai_summary": "Analysts note that ai agents usage patterns on Jan 01, 2025 reflect both hype and practical deployment pressure. The conversation is active, though buyers continue to separate pilot noise from repeatable production value.",
    "risk_indicator": "low",
    "innovation_score": 89.37,
    "adoption_score": 65.75,
    "source_reference": "https://reddit.example.com/600000"
  },
  {
    "reddit_post_id": "RDT-600001",
    "created_at": "2025-01-01T23:51:00",
    "subreddit": "r/datascience",
    "username": "model_37853",
    "topic": "AI Agents",
    "title": "Is AI Agents still underhyped or already overheating?",
    "body": "Seeing more teams mention Scale AI whenever ai agents comes up. Feels like adoption is real in United Arab Emirates, but the debate around moats keeps resurfacing.",
    "upvotes": 749,
    "comments": 160,
    "sentiment_score": 0.239,
    "company_id": "CMP-009",
    "company": "Scale AI",
    "country": "United Arab Emirates",
    "region": "Middle East",
    "trend_score": 45.4,
    "funding_estimate_musd": 34.79,
    "hiring_activity_index": 44.85,
    "hashtags": "#aiagents|#AE",
    "popularity_growth_pct": 0.54,
    "volatility_metric": 8.15,
    "ai_summary": "Scale AI teams are discussing how ai agents is moving from experimentation into production buying cycles. The conversation is active, though buyers continue to separate pilot noise from repeatable production value.",
    "risk_indicator": "low",
    "innovation_score": 92.33,
    "adoption_score": 68.25,
    "source_reference": "https://reddit.example.com/600001"
  }
]
```

### Expected Analytics Usage

- community sentiment mining
- hype-cycle monitoring
- anomaly detection on discussion bursts

### Suggested ML Use-Cases

- stance detection
- community segmentation
- engagement forecasting

## hackernews_posts.csv

Rows: `9750`

### Schema

| Field | Description |
|---|---|
| `hn_post_id` | HN item identifier |
| `title` | Story title |
| `points` | HN points |
| `comments` | HN comment count |

### Sample Records

```json
[
  {
    "hn_post_id": "HN-700000",
    "created_at": "2025-01-01T07:00:00",
    "title": "Replit and the new economics of ai agents",
    "domain": "databricks.com",
    "topic": "AI Agents",
    "points": 189,
    "comments": 76,
    "company_id": "CMP-014",
    "company": "Replit",
    "country": "United States",
    "trend_score": 51.72,
    "sentiment_score": 0.349,
    "popularity_growth_pct": 0.6,
    "volatility_metric": 6.76,
    "innovation_score": 88.51,
    "adoption_score": 67.29,
    "risk_indicator": "low",
    "ai_summary": "Developers are comparing tooling choices around ai agents as budget owners ask for faster ROI and clearer governance. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://news.ycombinator.com/item?id=700000"
  },
  {
    "hn_post_id": "HN-700001",
    "created_at": "2025-01-04T15:00:00",
    "title": "OpenAI and the new economics of ai agents",
    "domain": "huggingface.co",
    "topic": "AI Agents",
    "points": 249,
    "comments": 103,
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "United States",
    "trend_score": 53.53,
    "sentiment_score": 0.05,
    "popularity_growth_pct": 0.68,
    "volatility_metric": 11.68,
    "innovation_score": 93.38,
    "adoption_score": 75.4,
    "risk_indicator": "moderate",
    "ai_summary": "Analysts note that ai agents usage patterns on Jan 04, 2025 reflect both hype and practical deployment pressure. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://news.ycombinator.com/item?id=700001"
  }
]
```

### Expected Analytics Usage

- early technical attention tracking
- influencer-domain analysis

### Suggested ML Use-Cases

- story ranking
- comment volume forecasting

## youtube_ai_content.csv

Rows: `22992`

### Schema

| Field | Description |
|---|---|
| `video_id` | Video identifier |
| `channel` | Channel name |
| `views` | Video views |
| `watch_time_minutes` | Estimated aggregate watch time |

### Sample Records

```json
[
  {
    "video_id": "YT-800000",
    "published_at": "2025-01-01T13:00:00",
    "channel": "Fireship",
    "topic": "AI Agents",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "title": "AI Agents market update: what OpenAI says about 2026 demand",
    "views": 33505,
    "likes": 2215,
    "comments": 379,
    "watch_time_minutes": 55546,
    "country": "Canada",
    "sentiment_score": 0.299,
    "trend_score": 47.5,
    "funding_estimate_musd": 25.13,
    "hiring_activity_index": 35.62,
    "hashtags": "#aiagents|#AI|#CA",
    "popularity_growth_pct": 4.17,
    "volatility_metric": 8.66,
    "ai_summary": "Analysts note that ai agents usage patterns on Jan 01, 2025 reflect both hype and practical deployment pressure. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "risk_indicator": "low",
    "innovation_score": 89.37,
    "adoption_score": 65.75,
    "source_reference": "https://youtube.example.com/watch?v=800000"
  },
  {
    "video_id": "YT-800001",
    "published_at": "2025-01-02T23:00:00",
    "channel": "Two Minute Papers",
    "topic": "AI Agents",
    "company_id": "CMP-009",
    "company": "Scale AI",
    "title": "AI Agents market update: what Scale AI says about 2026 demand",
    "views": 49118,
    "likes": 3372,
    "comments": 473,
    "watch_time_minutes": 112832,
    "country": "Canada",
    "sentiment_score": -0.169,
    "trend_score": 47.04,
    "funding_estimate_musd": 37.28,
    "hiring_activity_index": 31.76,
    "hashtags": "#aiagents|#AI|#CA",
    "popularity_growth_pct": -0.96,
    "volatility_metric": 7.98,
    "ai_summary": "Scale AI teams are discussing how ai agents is moving from experimentation into production buying cycles. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "risk_indicator": "low",
    "innovation_score": 91.55,
    "adoption_score": 68.3,
    "source_reference": "https://youtube.example.com/watch?v=800001"
  }
]
```

### Expected Analytics Usage

- creator economy analysis
- education demand tracking
- topic attention mix by format

### Suggested ML Use-Cases

- view prediction
- channel recommendation
- topic lifecycle analysis

## startup_funding.csv

Rows: `561`

### Schema

| Field | Description |
|---|---|
| `funding_event_id` | Funding round identifier |
| `company_id` | Company key |
| `round_type` | Round or capital event type |
| `amount_musd` | Announced amount in USD millions |
| `valuation_musd` | Synthetic but plausible valuation estimate |
| `estimated_hiring_impact_pct` | Expected hiring lift after funding |

### Sample Records

```json
[
  {
    "funding_event_id": "FND-900000",
    "announced_at": "2025-02-09T00:00:00",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "United States",
    "region": "North America",
    "tech_category": "Generative AI",
    "round_type": "Growth Round",
    "amount_musd": 194.0,
    "valuation_musd": 1717.88,
    "lead_investor": "SoftBank",
    "sentiment_score": 0.162,
    "trend_score": 63.58,
    "estimated_hiring_impact_pct": 4.02,
    "risk_indicator": "low",
    "innovation_score": 93.57,
    "adoption_score": 67.28,
    "source_reference": "https://funding.example.com/900000"
  },
  {
    "funding_event_id": "FND-900001",
    "announced_at": "2025-04-01T00:00:00",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "United States",
    "region": "North America",
    "tech_category": "AI Agents",
    "round_type": "Growth Round",
    "amount_musd": 88.19,
    "valuation_musd": 2331.8,
    "lead_investor": "Sequoia",
    "sentiment_score": 0.38,
    "trend_score": 56.1,
    "estimated_hiring_impact_pct": 2.0,
    "risk_indicator": "low",
    "innovation_score": 90.01,
    "adoption_score": 62.91,
    "source_reference": "https://funding.example.com/900001"
  }
]
```

### Expected Analytics Usage

- capital allocation analysis
- funding-to-growth forecasting
- valuation benchmarking

### Suggested ML Use-Cases

- funding round classification
- post-funding hiring impact modeling
- valuation range estimation

## producthunt_launches.csv

Rows: `2400`

### Schema

| Field | Description |
|---|---|
| `launch_id` | Launch identifier |
| `product_name` | Product Hunt launch name |
| `category` | Product category |
| `upvotes` | Launch upvotes |
| `comments` | Launch comments |

### Sample Records

```json
[
  {
    "launch_id": "PH-950000",
    "launched_at": "2025-04-04T00:00:00",
    "company_id": "CMP-097",
    "company": "XRFoundry",
    "product_name": "XRFoundry Flow",
    "category": "Security",
    "topic": "Blockchain Dev",
    "upvotes": 61,
    "comments": 10,
    "country": "Japan",
    "trend_score": 22.96,
    "sentiment_score": 0.063,
    "popularity_growth_pct": -14.49,
    "volatility_metric": 20.2,
    "funding_estimate_musd": 24.94,
    "innovation_score": 87.17,
    "adoption_score": 25.0,
    "risk_indicator": "low",
    "ai_summary": "XRFoundry teams are discussing how blockchain dev is moving from experimentation into production buying cycles. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://producthunt.example.com/posts/950000"
  },
  {
    "launch_id": "PH-950001",
    "launched_at": "2025-06-03T00:00:00",
    "company_id": "CMP-101",
    "company": "ModelSignal",
    "product_name": "ModelSignal Flow",
    "category": "Automation",
    "topic": "LangChain",
    "upvotes": 145,
    "comments": 11,
    "country": "United States",
    "trend_score": 41.62,
    "sentiment_score": 0.293,
    "popularity_growth_pct": 3.12,
    "volatility_metric": 11.23,
    "funding_estimate_musd": 20.27,
    "innovation_score": 77.36,
    "adoption_score": 38.41,
    "risk_indicator": "low",
    "ai_summary": "Analysts note that langchain usage patterns on Jun 03, 2025 reflect both hype and practical deployment pressure. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://producthunt.example.com/posts/950001"
  }
]
```

### Expected Analytics Usage

- launch velocity tracking
- product demand testing
- top-of-funnel product discovery analytics

### Suggested ML Use-Cases

- launch success prediction
- category recommendation

## news_media_mentions.csv

Rows: `30303`

### Schema

| Field | Description |
|---|---|
| `mention_id` | News mention identifier |
| `headline` | Media headline |
| `mention_count` | Burst count proxy |
| `source` | News outlet |

### Sample Records

```json
[
  {
    "mention_id": "NEWS-980000",
    "published_at": "2025-01-05T07:00:00",
    "source": "VentureBeat",
    "topic": "AI Agents",
    "company_id": "CMP-001",
    "company": "OpenAI",
    "headline": "OpenAI sees stronger enterprise pull for ai agents",
    "country": "United Arab Emirates",
    "region": "Middle East",
    "mention_count": 28,
    "trend_score": 43.73,
    "sentiment_score": 0.556,
    "funding_estimate_musd": 22.55,
    "hiring_activity_index": 38.47,
    "hashtags": "#aiagents|#AE",
    "popularity_growth_pct": 3.4,
    "volatility_metric": 9.26,
    "ai_summary": "OpenAI teams are discussing how ai agents is moving from experimentation into production buying cycles. The conversation is active, though buyers continue to separate pilot noise from repeatable production value.",
    "risk_indicator": "moderate",
    "innovation_score": 92.31,
    "adoption_score": 67.98,
    "source_reference": "https://news.example.com/980000"
  },
  {
    "mention_id": "NEWS-980001",
    "published_at": "2025-01-06T00:00:00",
    "source": "VentureBeat",
    "topic": "AI Agents",
    "company_id": "CMP-028",
    "company": "LangChain",
    "headline": "LangChain sees stronger enterprise pull for ai agents",
    "country": "Canada",
    "region": "North America",
    "mention_count": 33,
    "trend_score": 45.21,
    "sentiment_score": -0.051,
    "funding_estimate_musd": 21.39,
    "hiring_activity_index": 50.1,
    "hashtags": "#aiagents|#CA",
    "popularity_growth_pct": -2.32,
    "volatility_metric": 8.37,
    "ai_summary": "Developers are comparing tooling choices around ai agents as budget owners ask for faster ROI and clearer governance. The conversation is active, though buyers continue to separate pilot noise from repeatable production value.",
    "risk_indicator": "low",
    "innovation_score": 94.11,
    "adoption_score": 69.64,
    "source_reference": "https://news.example.com/980001"
  }
]
```

### Expected Analytics Usage

- earned media monitoring
- reputation risk dashboards
- topic burst detection

### Suggested ML Use-Cases

- reputation risk scoring
- headline sentiment analysis
- burst forecasting

## kaggle_ml_activity.csv

Rows: `3200`

### Schema

| Field | Description |
|---|---|
| `kaggle_activity_id` | Activity identifier |
| `competition_name` | Competition or theme |
| `kernels_created` | Notebook creation count |
| `dataset_downloads` | Download activity |
| `medal_rate` | Top submission share proxy |

### Sample Records

```json
[
  {
    "kaggle_activity_id": "KGL-990000",
    "activity_date": "2025-06-06T00:00:00",
    "competition_name": "Agent Reasoning Benchmark",
    "topic": "TypeScript",
    "company_id": "CMP-043",
    "company": "Meta",
    "country": "United Kingdom",
    "kernels_created": 60,
    "notebook_votes": 841,
    "dataset_downloads": 2224,
    "medal_rate": 0.211,
    "trend_score": 68.58,
    "sentiment_score": -0.012,
    "popularity_growth_pct": 1.9,
    "volatility_metric": 6.32,
    "innovation_score": 68.54,
    "adoption_score": 66.11,
    "risk_indicator": "low",
    "ai_summary": "Meta teams are discussing how typescript is moving from experimentation into production buying cycles. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://kaggle.example.com/activity/990000"
  },
  {
    "kaggle_activity_id": "KGL-990001",
    "activity_date": "2025-12-10T00:00:00",
    "competition_name": "Agent Reasoning Benchmark",
    "topic": "Swift",
    "company_id": "CMP-002",
    "company": "Anthropic",
    "country": "United Kingdom",
    "kernels_created": 39,
    "notebook_votes": 512,
    "dataset_downloads": 1504,
    "medal_rate": 0.182,
    "trend_score": 35.88,
    "sentiment_score": 0.153,
    "popularity_growth_pct": 3.84,
    "volatility_metric": 7.76,
    "innovation_score": 71.23,
    "adoption_score": 35.07,
    "risk_indicator": "low",
    "ai_summary": "Analysts note that swift usage patterns on Dec 10, 2025 reflect both hype and practical deployment pressure. Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
    "source_reference": "https://kaggle.example.com/activity/990001"
  }
]
```

### Expected Analytics Usage

- ML community activity monitoring
- competition-to-adoption trend analysis

### Suggested ML Use-Cases

- competition popularity forecasting
- talent signal extraction

## companies.csv

Rows: `110`

### Schema

| Field | Description |
|---|---|
| `company_id` | Primary company key |
| `company` | Company name |
| `country` | HQ country |
| `sector` | Business category |
| `dominant_topics` | Main trend themes |

### Sample Records

```json
[
  {
    "company_id": "CMP-001",
    "company": "OpenAI",
    "country": "United States",
    "country_code": "US",
    "region": "North America",
    "sector": "AI Platform",
    "stage": "private",
    "reference_type": "real_reference",
    "dominant_topics": "AI Agents, Enterprise AI, Generative AI, LLM"
  },
  {
    "company_id": "CMP-002",
    "company": "Anthropic",
    "country": "United States",
    "country_code": "US",
    "region": "North America",
    "sector": "AI Platform",
    "stage": "private",
    "reference_type": "real_reference",
    "dominant_topics": "AI Agents, Enterprise AI, LLM"
  }
]
```

### Expected Analytics Usage

- entity resolution
- company segmentation
- master data management

### Suggested ML Use-Cases

- entity graph features
- cross-source enrichment

## market_events.csv

Rows: `33`

### Schema

| Field | Description |
|---|---|
| `event_id` | Market event key |
| `event_date` | Event anchor date |
| `window_days` | Decay window |
| `title` | Description |
| `topic_impacts` | JSON of topic-specific shocks |

### Sample Records

```json
[
  {
    "event_id": "EVT-001",
    "event_date": "2025-01-22",
    "window_days": 10,
    "title": "Agentic coding workflows move from demos to pilots",
    "topic_impacts": "{\"AI Agents\": 12, \"Developer Tools\": 8, \"Enterprise AI\": 6}",
    "sentiment_shift": 0.07
  },
  {
    "event_id": "EVT-002",
    "event_date": "2025-03-12",
    "window_days": 14,
    "title": "Robotics model announcement lifts embodied AI interest",
    "topic_impacts": "{\"Robotics\": 18, \"Edge AI\": 10, \"LLM\": 4}",
    "sentiment_shift": 0.05
  }
]
```

### Expected Analytics Usage

- event-driven analytics
- shock attribution
- change-point explanation

### Suggested ML Use-Cases

- event attribution features
- causal impact analysis
