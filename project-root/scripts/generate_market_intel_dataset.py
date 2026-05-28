"""Generate realistic synthetic market-intelligence datasets for TechTrends.

This script regenerates the existing local CSVs with larger, more believable
2025-2026 data while preserving the required columns used by the current
project pipeline. It also creates additional multi-source datasets, metadata
documentation, SQL import assets, JSON samples, and relationship diagrams.

Usage:
    python -m scripts.generate_market_intel_dataset
"""
from __future__ import annotations

import argparse
import json
import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import sys

# Ensure project root is on sys.path so `from config import settings` works
# when this script is executed directly (sys.path[0] is the script's dir).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import settings

# Default RNG seed (can be overridden via CLI)
SEED = 20260526
RNG = np.random.default_rng(SEED)
# Scaling multiplier used to increase generated counts when needed
SCALE = 1.0

BASE_DIR = Path(settings.BASE_DIR)
DATA_DIR = BASE_DIR / "Data"
MARKET_DIR = DATA_DIR / "market_intel"
IMPORT_DIR = BASE_DIR / "imports"
SAMPLES_DIR = BASE_DIR / "samples"
API_SAMPLES_DIR = SAMPLES_DIR / "api"
JSON_SAMPLES_DIR = SAMPLES_DIR / "json"

DATE_START = "2025-01-01"
DATE_END = "2026-04-30"
DATES = pd.date_range(DATE_START, DATE_END, freq="D")

COUNTRIES = [
    {"country": "United States", "code": "US", "region": "North America", "cities": ["San Francisco", "New York", "Seattle", "Austin"], "hiring": 1.25, "social": 1.35, "funding": 1.6},
    {"country": "India", "code": "IN", "region": "Asia", "cities": ["Bengaluru", "Hyderabad", "Delhi", "Mumbai"], "hiring": 1.2, "social": 1.15, "funding": 0.8},
    {"country": "United Kingdom", "code": "UK", "region": "Europe", "cities": ["London", "Manchester"], "hiring": 0.95, "social": 0.9, "funding": 0.9},
    {"country": "Germany", "code": "DE", "region": "Europe", "cities": ["Berlin", "Munich"], "hiring": 0.9, "social": 0.82, "funding": 0.75},
    {"country": "Canada", "code": "CA", "region": "North America", "cities": ["Toronto", "Vancouver"], "hiring": 0.86, "social": 0.8, "funding": 0.72},
    {"country": "Singapore", "code": "SG", "region": "Asia", "cities": ["Singapore"], "hiring": 0.72, "social": 0.66, "funding": 0.78},
    {"country": "United Arab Emirates", "code": "AE", "region": "Middle East", "cities": ["Dubai", "Abu Dhabi"], "hiring": 0.63, "social": 0.61, "funding": 0.7},
    {"country": "Japan", "code": "JP", "region": "Asia", "cities": ["Tokyo", "Osaka"], "hiring": 0.78, "social": 0.72, "funding": 0.68},
    {"country": "China", "code": "CN", "region": "Asia", "cities": ["Beijing", "Shenzhen"], "hiring": 1.02, "social": 0.92, "funding": 0.88},
    {"country": "France", "code": "FR", "region": "Europe", "cities": ["Paris"], "hiring": 0.7, "social": 0.69, "funding": 0.6},
]

COUNTRY_BY_CODE = {c["code"]: c for c in COUNTRIES}

TOPICS: dict[str, dict[str, Any]] = {
    "AI Agents": {"base": 42, "growth": 20, "volatility": 6, "weekend_social": 0.76, "weekend_hiring": 0.52, "sentiment": 0.24, "innovation": 92, "adoption": 67, "github": 0.95, "funding": 1.45, "companies": ["CMP-001", "CMP-002", "CMP-009", "CMP-013", "CMP-014", "CMP-015", "CMP-028", "CMP-031"]},
    "LLM": {"base": 55, "growth": 14, "volatility": 5, "weekend_social": 0.8, "weekend_hiring": 0.58, "sentiment": 0.21, "innovation": 90, "adoption": 72, "github": 0.8, "funding": 1.35, "companies": ["CMP-001", "CMP-002", "CMP-003", "CMP-009", "CMP-017", "CMP-018"]},
    "Generative AI": {"base": 58, "growth": 11, "volatility": 7, "weekend_social": 0.79, "weekend_hiring": 0.55, "sentiment": 0.19, "innovation": 91, "adoption": 70, "github": 0.63, "funding": 1.38, "companies": ["CMP-001", "CMP-003", "CMP-005", "CMP-016", "CMP-017"]},
    "Cybersecurity": {"base": 48, "growth": 8, "volatility": 11, "weekend_social": 0.72, "weekend_hiring": 0.64, "sentiment": 0.05, "innovation": 78, "adoption": 76, "github": 0.56, "funding": 0.92, "companies": ["CMP-021", "CMP-022", "CMP-023", "CMP-032"]},
    "Cloud Computing": {"base": 44, "growth": 5, "volatility": 4, "weekend_social": 0.82, "weekend_hiring": 0.63, "sentiment": 0.11, "innovation": 73, "adoption": 84, "github": 0.45, "funding": 0.85, "companies": ["CMP-004", "CMP-006", "CMP-010", "CMP-011", "CMP-019", "CMP-024"]},
    "DevOps": {"base": 34, "growth": 3, "volatility": 4, "weekend_social": 0.83, "weekend_hiring": 0.6, "sentiment": 0.1, "innovation": 69, "adoption": 81, "github": 0.62, "funding": 0.8, "companies": ["CMP-024", "CMP-026", "CMP-027"]},
    "Edge AI": {"base": 26, "growth": 9, "volatility": 7, "weekend_social": 0.78, "weekend_hiring": 0.56, "sentiment": 0.16, "innovation": 83, "adoption": 54, "github": 0.58, "funding": 1.02, "companies": ["CMP-003", "CMP-022", "CMP-033"]},
    "Robotics": {"base": 24, "growth": 10, "volatility": 8, "weekend_social": 0.77, "weekend_hiring": 0.59, "sentiment": 0.18, "innovation": 86, "adoption": 50, "github": 0.64, "funding": 1.05, "companies": ["CMP-003", "CMP-020", "CMP-034"]},
    "Web3": {"base": 32, "growth": -2, "volatility": 16, "weekend_social": 0.88, "weekend_hiring": 0.47, "sentiment": -0.02, "innovation": 66, "adoption": 38, "github": 0.49, "funding": 0.72, "companies": ["CMP-035", "CMP-036"]},
    "Semiconductors": {"base": 41, "growth": 9, "volatility": 8, "weekend_social": 0.74, "weekend_hiring": 0.61, "sentiment": 0.14, "innovation": 85, "adoption": 73, "github": 0.34, "funding": 1.15, "companies": ["CMP-004", "CMP-020"]},
    "SaaS": {"base": 35, "growth": 1, "volatility": 5, "weekend_social": 0.84, "weekend_hiring": 0.58, "sentiment": 0.09, "innovation": 64, "adoption": 78, "github": 0.31, "funding": 0.78, "companies": ["CMP-011", "CMP-024", "CMP-025", "CMP-037"]},
    "Data Engineering": {"base": 39, "growth": 7, "volatility": 6, "weekend_social": 0.81, "weekend_hiring": 0.67, "sentiment": 0.15, "innovation": 76, "adoption": 80, "github": 0.72, "funding": 0.95, "companies": ["CMP-010", "CMP-011", "CMP-025", "CMP-026", "CMP-027"]},
    "Automation": {"base": 31, "growth": 6, "volatility": 5, "weekend_social": 0.82, "weekend_hiring": 0.55, "sentiment": 0.12, "innovation": 74, "adoption": 71, "github": 0.43, "funding": 0.84, "companies": ["CMP-014", "CMP-015", "CMP-031"]},
    "MLOps": {"base": 33, "growth": 7, "volatility": 5, "weekend_social": 0.8, "weekend_hiring": 0.65, "sentiment": 0.14, "innovation": 79, "adoption": 69, "github": 0.77, "funding": 0.98, "companies": ["CMP-007", "CMP-010", "CMP-011", "CMP-017"]},
    "Open Source AI": {"base": 37, "growth": 12, "volatility": 7, "weekend_social": 0.83, "weekend_hiring": 0.53, "sentiment": 0.22, "innovation": 88, "adoption": 64, "github": 1.2, "funding": 0.9, "companies": ["CMP-005", "CMP-007", "CMP-017", "CMP-018", "CMP-028"]},
    "GPU Infrastructure": {"base": 29, "growth": 12, "volatility": 9, "weekend_social": 0.73, "weekend_hiring": 0.62, "sentiment": 0.17, "innovation": 87, "adoption": 62, "github": 0.41, "funding": 1.22, "companies": ["CMP-004", "CMP-019", "CMP-020"]},
    "Developer Tools": {"base": 38, "growth": 10, "volatility": 7, "weekend_social": 0.85, "weekend_hiring": 0.6, "sentiment": 0.18, "innovation": 82, "adoption": 77, "github": 1.05, "funding": 1.1, "companies": ["CMP-013", "CMP-014", "CMP-015", "CMP-024", "CMP-025", "CMP-028", "CMP-029"]},
    "Vector Databases": {"base": 28, "growth": 8, "volatility": 6, "weekend_social": 0.8, "weekend_hiring": 0.59, "sentiment": 0.16, "innovation": 81, "adoption": 58, "github": 0.88, "funding": 1.02, "companies": ["CMP-025", "CMP-030", "CMP-038"]},
    "Inference Optimization": {"base": 22, "growth": 11, "volatility": 6, "weekend_social": 0.78, "weekend_hiring": 0.57, "sentiment": 0.17, "innovation": 86, "adoption": 55, "github": 0.79, "funding": 1.08, "companies": ["CMP-004", "CMP-018", "CMP-019", "CMP-039"]},
    "Enterprise AI": {"base": 46, "growth": 13, "volatility": 5, "weekend_social": 0.76, "weekend_hiring": 0.66, "sentiment": 0.2, "innovation": 84, "adoption": 79, "github": 0.48, "funding": 1.18, "companies": ["CMP-001", "CMP-002", "CMP-003", "CMP-006", "CMP-008", "CMP-010", "CMP-011", "CMP-012", "CMP-018"]},
}

COMPANIES = [
    {"company_id": "CMP-001", "company": "OpenAI", "country": "US", "sector": "AI Platform", "stage": "private", "reference_type": "real_reference", "topics": ["AI Agents", "LLM", "Generative AI", "Enterprise AI"]},
    {"company_id": "CMP-002", "company": "Anthropic", "country": "US", "sector": "AI Platform", "stage": "private", "reference_type": "real_reference", "topics": ["AI Agents", "LLM", "Enterprise AI"]},
    {"company_id": "CMP-003", "company": "Google DeepMind", "country": "US", "sector": "Research Lab", "stage": "subsidiary", "reference_type": "real_reference", "topics": ["LLM", "Robotics", "Edge AI", "Enterprise AI"]},
    {"company_id": "CMP-004", "company": "NVIDIA", "country": "US", "sector": "Semiconductors", "stage": "public", "reference_type": "real_reference", "topics": ["Semiconductors", "GPU Infrastructure", "Inference Optimization"]},
    {"company_id": "CMP-005", "company": "Meta AI", "country": "US", "sector": "AI Research", "stage": "subsidiary", "reference_type": "real_reference", "topics": ["Generative AI", "Open Source AI", "AI Agents"]},
    {"company_id": "CMP-006", "company": "Microsoft", "country": "US", "sector": "Cloud + Productivity", "stage": "public", "reference_type": "real_reference", "topics": ["Enterprise AI", "Cloud Computing", "Developer Tools"]},
    {"company_id": "CMP-007", "company": "Hugging Face", "country": "US", "sector": "Open Source AI", "stage": "private", "reference_type": "real_reference", "topics": ["Open Source AI", "MLOps", "Developer Tools"]},
    {"company_id": "CMP-008", "company": "Perplexity", "country": "US", "sector": "AI Search", "stage": "private", "reference_type": "real_reference", "topics": ["LLM", "AI Agents", "Enterprise AI"]},
    {"company_id": "CMP-009", "company": "Scale AI", "country": "US", "sector": "Data + AI Infrastructure", "stage": "private", "reference_type": "real_reference", "topics": ["AI Agents", "Enterprise AI"]},
    {"company_id": "CMP-010", "company": "Databricks", "country": "US", "sector": "Data Platform", "stage": "private", "reference_type": "real_reference", "topics": ["Data Engineering", "MLOps", "Enterprise AI"]},
    {"company_id": "CMP-011", "company": "Snowflake", "country": "US", "sector": "Data Platform", "stage": "public", "reference_type": "real_reference", "topics": ["Data Engineering", "Cloud Computing", "Enterprise AI", "SaaS"]},
    {"company_id": "CMP-012", "company": "AWS", "country": "US", "sector": "Cloud", "stage": "subsidiary", "reference_type": "real_reference", "topics": ["Cloud Computing", "Enterprise AI", "Data Engineering"]},
    {"company_id": "CMP-013", "company": "Cursor", "country": "US", "sector": "Developer Tools", "stage": "private", "reference_type": "real_reference", "topics": ["Developer Tools", "AI Agents"]},
    {"company_id": "CMP-014", "company": "Replit", "country": "US", "sector": "Developer Tools", "stage": "private", "reference_type": "real_reference", "topics": ["Developer Tools", "AI Agents", "Automation"]},
    {"company_id": "CMP-015", "company": "Windsurf", "country": "US", "sector": "Developer Tools", "stage": "private", "reference_type": "real_reference", "topics": ["Developer Tools", "AI Agents", "Automation"]},
    {"company_id": "CMP-016", "company": "Midjourney", "country": "US", "sector": "Creative AI", "stage": "private", "reference_type": "real_reference", "topics": ["Generative AI"]},
    {"company_id": "CMP-017", "company": "Stability AI", "country": "UK", "sector": "Open Source AI", "stage": "private", "reference_type": "real_reference", "topics": ["Generative AI", "Open Source AI", "MLOps"]},
    {"company_id": "CMP-018", "company": "Mistral AI", "country": "FR", "sector": "Foundation Models", "stage": "private", "reference_type": "real_reference", "topics": ["LLM", "Open Source AI", "Inference Optimization", "Enterprise AI"]},
    {"company_id": "CMP-019", "company": "CoreWeave", "country": "US", "sector": "Cloud Infrastructure", "stage": "public", "reference_type": "real_reference", "topics": ["GPU Infrastructure", "Inference Optimization", "Cloud Computing"]},
    {"company_id": "CMP-020", "company": "Figure", "country": "US", "sector": "Robotics", "stage": "private", "reference_type": "real_reference", "topics": ["Robotics", "Semiconductors"]},
    {"company_id": "CMP-021", "company": "CrowdStrike", "country": "US", "sector": "Cybersecurity", "stage": "public", "reference_type": "real_reference", "topics": ["Cybersecurity"]},
    {"company_id": "CMP-022", "company": "Palo Alto Networks", "country": "US", "sector": "Cybersecurity", "stage": "public", "reference_type": "real_reference", "topics": ["Cybersecurity", "Edge AI"]},
    {"company_id": "CMP-023", "company": "Cloudflare", "country": "US", "sector": "Network Security", "stage": "public", "reference_type": "real_reference", "topics": ["Cybersecurity", "Edge AI"]},
    {"company_id": "CMP-024", "company": "GitLab", "country": "US", "sector": "DevOps", "stage": "public", "reference_type": "real_reference", "topics": ["DevOps", "Cloud Computing", "Developer Tools", "SaaS"]},
    {"company_id": "CMP-025", "company": "MongoDB", "country": "US", "sector": "Database", "stage": "public", "reference_type": "real_reference", "topics": ["Developer Tools", "Vector Databases", "Data Engineering", "SaaS"]},
    {"company_id": "CMP-026", "company": "Confluent", "country": "US", "sector": "Streaming Data", "stage": "public", "reference_type": "real_reference", "topics": ["Data Engineering", "DevOps"]},
    {"company_id": "CMP-027", "company": "HashiCorp", "country": "US", "sector": "Infrastructure Automation", "stage": "public", "reference_type": "real_reference", "topics": ["DevOps", "Automation", "Cloud Computing"]},
    {"company_id": "CMP-028", "company": "LangChain", "country": "US", "sector": "AI Frameworks", "stage": "private", "reference_type": "real_reference", "topics": ["AI Agents", "Developer Tools", "Open Source AI"]},
    {"company_id": "CMP-029", "company": "Vercel", "country": "US", "sector": "Developer Platform", "stage": "private", "reference_type": "real_reference", "topics": ["Developer Tools", "Cloud Computing"]},
    {"company_id": "CMP-030", "company": "Weaviate", "country": "DE", "sector": "Vector Database", "stage": "private", "reference_type": "real_reference", "topics": ["Vector Databases", "Open Source AI"]},
    {"company_id": "CMP-031", "company": "AgentForge", "country": "SG", "sector": "AI Agents", "stage": "series_b", "reference_type": "synthetic_company", "topics": ["AI Agents", "Automation", "Enterprise AI"]},
    {"company_id": "CMP-032", "company": "SentinelGraph", "country": "UK", "sector": "Cybersecurity", "stage": "series_a", "reference_type": "synthetic_company", "topics": ["Cybersecurity", "AI Agents"]},
    {"company_id": "CMP-033", "company": "EdgeNova", "country": "CN", "sector": "Edge AI", "stage": "series_b", "reference_type": "synthetic_company", "topics": ["Edge AI", "Semiconductors"]},
    {"company_id": "CMP-034", "company": "Helio Robotics", "country": "JP", "sector": "Robotics", "stage": "series_b", "reference_type": "synthetic_company", "topics": ["Robotics", "Edge AI"]},
    {"company_id": "CMP-035", "company": "ChainSignal", "country": "AE", "sector": "Web3", "stage": "series_a", "reference_type": "synthetic_company", "topics": ["Web3"]},
    {"company_id": "CMP-036", "company": "LedgerSpring", "country": "SG", "sector": "Web3", "stage": "seed", "reference_type": "synthetic_company", "topics": ["Web3"]},
    {"company_id": "CMP-037", "company": "OpsFabric", "country": "IN", "sector": "SaaS Automation", "stage": "series_b", "reference_type": "synthetic_company", "topics": ["SaaS", "Automation", "DevOps"]},
    {"company_id": "CMP-038", "company": "VectorNest", "country": "CA", "sector": "AI Database", "stage": "series_a", "reference_type": "synthetic_company", "topics": ["Vector Databases", "Inference Optimization"]},
    {"company_id": "CMP-039", "company": "InferOptics", "country": "US", "sector": "Inference Optimization", "stage": "series_a", "reference_type": "synthetic_company", "topics": ["Inference Optimization", "GPU Infrastructure"]},
]

COMPANY_BY_ID = {c["company_id"]: c for c in COMPANIES}

EVENTS = [
    {"event_id": "EVT-001", "date": "2025-01-22", "window": 10, "title": "Agentic coding workflows move from demos to pilots", "topics": {"AI Agents": 12, "Developer Tools": 8, "Enterprise AI": 6}, "sentiment": 0.07},
    {"event_id": "EVT-002", "date": "2025-03-12", "window": 14, "title": "Robotics model announcement lifts embodied AI interest", "topics": {"Robotics": 18, "Edge AI": 10, "LLM": 4}, "sentiment": 0.05},
    {"event_id": "EVT-003", "date": "2025-05-28", "window": 16, "title": "GPU infrastructure demand accelerates after strong AI compute commentary", "topics": {"GPU Infrastructure": 18, "Semiconductors": 16, "Enterprise AI": 8, "Inference Optimization": 7}, "sentiment": 0.08},
    {"event_id": "EVT-004", "date": "2025-06-04", "window": 10, "title": "Data platform vendors push agentic analytics and AI apps", "topics": {"Data Engineering": 10, "Enterprise AI": 10, "MLOps": 7, "AI Agents": 6}, "sentiment": 0.05},
    {"event_id": "EVT-005", "date": "2025-07-18", "window": 12, "title": "High-profile cloud outage raises reliability concerns", "topics": {"Cloud Computing": 8, "DevOps": 7, "Cybersecurity": 5}, "sentiment": -0.06},
    {"event_id": "EVT-006", "date": "2025-08-11", "window": 18, "title": "Late-stage funding cools and hiring plans tighten", "topics": {"SaaS": -8, "Cloud Computing": -4, "Developer Tools": -3, "Enterprise AI": -2}, "sentiment": -0.08},
    {"event_id": "EVT-007", "date": "2025-09-19", "window": 12, "title": "Major cyber incident drives urgent security demand", "topics": {"Cybersecurity": 20, "AI Agents": 4, "Cloud Computing": 3}, "sentiment": -0.1},
    {"event_id": "EVT-008", "date": "2025-10-09", "window": 12, "title": "Open model releases boost community experimentation", "topics": {"Open Source AI": 14, "LLM": 8, "MLOps": 6, "Developer Tools": 4}, "sentiment": 0.08},
    {"event_id": "EVT-009", "date": "2025-11-18", "window": 16, "title": "Enterprise copilots expand from pilots to budgeted rollouts", "topics": {"Enterprise AI": 18, "AI Agents": 10, "Developer Tools": 6, "Data Engineering": 5}, "sentiment": 0.07},
    {"event_id": "EVT-010", "date": "2026-01-15", "window": 16, "title": "Inference cost pressure increases optimization focus", "topics": {"Inference Optimization": 16, "GPU Infrastructure": 9, "Open Source AI": 5}, "sentiment": 0.03},
    {"event_id": "EVT-011", "date": "2026-02-23", "window": 10, "title": "AI-enabled attack campaigns increase board-level cyber spending", "topics": {"Cybersecurity": 18, "Enterprise AI": 4, "Edge AI": 2}, "sentiment": -0.09},
    {"event_id": "EVT-012", "date": "2026-03-21", "window": 14, "title": "Web3 trading and token activity rebound before another correction", "topics": {"Web3": 14}, "sentiment": 0.04},
    {"event_id": "EVT-013", "date": "2026-04-16", "window": 16, "title": "Enterprise agent platforms mature with audit and governance features", "topics": {"AI Agents": 16, "Enterprise AI": 9, "Automation": 6, "Cybersecurity": 4}, "sentiment": 0.06},
]

MARKET_CONTEXT_VERSION = "2026-05"
MARKET_CONTEXT_SOURCES = [
    {
        "name": "Gartner Top Strategic Technology Trends 2026",
        "url": "https://www.gartner.com/en/articles/top-technology-trends-2026",
        "signals": ["multiagent systems", "AI-native platforms", "digital trust", "AI infrastructure"],
    },
    {
        "name": "McKinsey Technology Trends Outlook 2025",
        "url": "https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights/the-top-trends-in-tech",
        "signals": ["AI", "cloud and edge computing", "robotics", "digital trust and cybersecurity"],
    },
    {
        "name": "GitHub Octoverse 2025",
        "url": "https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/",
        "signals": ["AI projects", "TypeScript", "Python", "developer tooling"],
    },
    {
        "name": "Stack Overflow Developer Survey 2025",
        "url": "https://survey.stackoverflow.co/2025/",
        "signals": ["AI tool adoption", "developer trust concerns", "AI-related technical questions"],
    },
]

MARKET_CONTEXT_ADJUSTMENTS = {
    "AI Agents": {"growth": 1.18, "base": 1.08, "funding": 1.12, "github": 1.08},
    "Enterprise AI": {"growth": 1.14, "base": 1.05, "funding": 1.08},
    "Developer Tools": {"growth": 1.10, "github": 1.16, "sentiment": 1.04},
    "Inference Optimization": {"growth": 1.15, "funding": 1.10, "github": 1.06},
    "GPU Infrastructure": {"growth": 1.14, "funding": 1.12},
    "Cybersecurity": {"growth": 1.10, "base": 1.04, "volatility": 1.10},
    "Open Source AI": {"growth": 1.10, "github": 1.18},
    "Vector Databases": {"growth": 1.06, "github": 1.08},
    "Robotics": {"growth": 1.06, "funding": 1.06},
    "Web3": {"growth": 0.88, "funding": 0.90, "volatility": 1.10},
}
_MARKET_CONTEXT_APPLIED = False

NEWS_SOURCES = ["The Information", "TechCrunch", "Bloomberg", "Reuters", "VentureBeat", "Semafor", "The Verge", "Wired", "InfoQ", "SiliconANGLE"]
BLOG_SOURCES = ["Medium", "Dev.to", "Substack", "InfoQ", "Towards Data Science", "Hugging Face Blog", "Engineering Blog"]
YOUTUBE_CHANNELS = ["The AI Breakdown", "Fireship", "Two Minute Papers", "Machine Learning Street Talk", "MLOps Weekly", "Cloud Native Bytes"]
SUBREDDITS = ["r/MachineLearning", "r/artificial", "r/devops", "r/cybersecurity", "r/datascience", "r/startups"]
HN_DOMAINS = ["github.com", "openai.com", "anthropic.com", "huggingface.co", "databricks.com", "snowflake.com", "nvidia.com", "techcrunch.com"]
PRODUCT_CATEGORIES = ["Developer Tools", "AI Productivity", "Security", "Infrastructure", "Data", "Automation", "Analytics"]
KAGGLE_COMPETITIONS = ["Agent Reasoning Benchmark", "GPU Cost Forecasting", "Cyber Incident Detection", "Open Model Eval", "Startup Growth Forecasting"]

ROLE_LIBRARY = {
    "AI Agents": ["AI Engineer", "Agent Platform Engineer", "Applied Scientist"],
    "LLM": ["LLM Engineer", "Applied Researcher", "Model Evaluation Engineer"],
    "Generative AI": ["Generative AI Product Engineer", "Applied Scientist", "Multimodal Engineer"],
    "Cybersecurity": ["Security Engineer", "Detection Engineer", "Threat Analyst"],
    "Cloud Computing": ["Cloud Architect", "Platform Engineer", "Site Reliability Engineer"],
    "DevOps": ["DevOps Engineer", "Platform Reliability Engineer", "Release Engineer"],
    "Edge AI": ["Edge ML Engineer", "Systems Engineer", "Embedded AI Engineer"],
    "Robotics": ["Robotics Engineer", "Perception Engineer", "Controls Engineer"],
    "Web3": ["Protocol Engineer", "Smart Contract Engineer", "Blockchain Analyst"],
    "Semiconductors": ["Systems Performance Engineer", "GPU Software Engineer", "Compute Architect"],
    "SaaS": ["Product Analyst", "Solutions Engineer", "Growth Engineer"],
    "Data Engineering": ["Data Engineer", "Analytics Engineer", "Streaming Engineer"],
    "Automation": ["Automation Engineer", "Workflow Engineer", "Solution Architect"],
    "MLOps": ["MLOps Engineer", "ML Platform Engineer", "Model Ops Specialist"],
    "Open Source AI": ["Open Source ML Engineer", "Developer Advocate", "Community Engineer"],
    "GPU Infrastructure": ["Infrastructure Engineer", "Capacity Planner", "Cluster Operations Engineer"],
    "Developer Tools": ["Developer Experience Engineer", "Frontend Engineer", "Tooling Engineer"],
    "Vector Databases": ["Database Engineer", "Search Engineer", "Retrieval Engineer"],
    "Inference Optimization": ["Inference Engineer", "Compiler Engineer", "Performance Engineer"],
    "Enterprise AI": ["AI Solutions Architect", "Enterprise AI Consultant", "Platform Product Manager"],
}

TOPIC_SKILLS = {
    "AI Agents": ["Python", "LangChain", "RAG", "OpenAI API", "Tool Calling", "FastAPI"],
    "LLM": ["PyTorch", "Transformers", "Tokenization", "Evaluation", "Fine-tuning"],
    "Generative AI": ["Diffusion", "Prompt Engineering", "Inference", "PyTorch", "Serving"],
    "Cybersecurity": ["SIEM", "Threat Detection", "IAM", "SOAR", "Incident Response"],
    "Cloud Computing": ["AWS", "Kubernetes", "Terraform", "Linux", "Observability"],
    "DevOps": ["CI/CD", "Docker", "Kubernetes", "Terraform", "GitOps"],
    "Edge AI": ["ONNX", "C++", "Computer Vision", "CUDA", "Embedded Linux"],
    "Robotics": ["ROS", "SLAM", "Perception", "Python", "Controls"],
    "Web3": ["Solidity", "Rust", "Smart Contracts", "Tokenomics", "Ethereum"],
    "Semiconductors": ["CUDA", "GPU Profiling", "C++", "Inference", "Distributed Systems"],
    "SaaS": ["Product Analytics", "SQL", "Customer Success", "Billing", "APIs"],
    "Data Engineering": ["Spark", "Kafka", "Airflow", "dbt", "PostgreSQL"],
    "Automation": ["n8n", "Zapier", "Python", "Workflows", "APIs"],
    "MLOps": ["MLflow", "Kubeflow", "Feature Store", "Monitoring", "CI/CD"],
    "Open Source AI": ["Transformers", "Python", "Community", "Benchmarking", "GitHub Actions"],
    "GPU Infrastructure": ["Kubernetes", "NCCL", "Ray", "Monitoring", "Capacity Planning"],
    "Developer Tools": ["TypeScript", "React", "IDE Extensions", "LSP", "Telemetry"],
    "Vector Databases": ["Embeddings", "ANN Search", "PostgreSQL", "Redis", "Rust"],
    "Inference Optimization": ["TensorRT", "ONNX Runtime", "CUDA", "Profiling", "C++"],
    "Enterprise AI": ["Security", "Governance", "Azure", "Snowflake", "Databricks"],
}

DECLINING_TECHNOLOGIES = {
    "PHP",
    "Ruby",
    "Angular",
    "jQuery",
    "Flash",
    "COBOL",
    "Mainframe COBOL",
    "Perl",
    "ColdFusion",
    "Xamarin",
    "Ionic",
    "Bootstrap",
    "Jenkins",
    "RubyOnRails",
    "Laravel",
}

EMERGING_TECHNOLOGIES = {
    "Rust",
    "Go",
    "Julia",
    "Next.js",
    "Svelte",
    "Astro",
    "HTMX",
    "FastAPI",
    "DuckDB",
    "Pinecone",
    "Supabase",
    "Flutter",
    "Vitest",
    "NATS",
    "Zero-Trust Security",
    "WebAssembly",
    "Quantum Computing",
    "Edge Computing",
    "Low-Code/No-Code",
}

CATEGORY_DEFAULTS: dict[str, dict[str, float]] = {
    "Programming Languages": {"github": 0.78, "funding": 0.7, "weekend_social": 0.84, "weekend_hiring": 0.62},
    "Web & Frontend Frameworks": {"github": 0.9, "funding": 0.76, "weekend_social": 0.88, "weekend_hiring": 0.58},
    "Backend & API Frameworks": {"github": 0.76, "funding": 0.74, "weekend_social": 0.84, "weekend_hiring": 0.62},
    "Data & Databases": {"github": 0.66, "funding": 0.88, "weekend_social": 0.81, "weekend_hiring": 0.65},
    "Cloud & Infrastructure": {"github": 0.58, "funding": 0.92, "weekend_social": 0.8, "weekend_hiring": 0.66},
    "Mobile Development": {"github": 0.72, "funding": 0.74, "weekend_social": 0.86, "weekend_hiring": 0.58},
    "Testing & QA": {"github": 0.68, "funding": 0.56, "weekend_social": 0.82, "weekend_hiring": 0.57},
    "DevOps & Monitoring": {"github": 0.62, "funding": 0.82, "weekend_social": 0.8, "weekend_hiring": 0.66},
    "Message Queues & Streaming": {"github": 0.7, "funding": 0.82, "weekend_social": 0.79, "weekend_hiring": 0.63},
    "API & Integration": {"github": 0.58, "funding": 0.64, "weekend_social": 0.83, "weekend_hiring": 0.61},
    "Security & Compliance": {"github": 0.55, "funding": 0.94, "weekend_social": 0.75, "weekend_hiring": 0.68},
    "UI/UX & Design": {"github": 0.5, "funding": 0.66, "weekend_social": 0.9, "weekend_hiring": 0.52},
    "Emerging Technologies": {"github": 0.72, "funding": 0.95, "weekend_social": 0.86, "weekend_hiring": 0.55},
    "AI & Machine Learning": {"github": 0.86, "funding": 1.08, "weekend_social": 0.82, "weekend_hiring": 0.62},
    "Data Science": {"github": 0.74, "funding": 0.7, "weekend_social": 0.84, "weekend_hiring": 0.58},
    "CMS & Commerce": {"github": 0.45, "funding": 0.5, "weekend_social": 0.86, "weekend_hiring": 0.5},
}

CATEGORY_ROLE_TEMPLATES: dict[str, list[str]] = {
    "Programming Languages": ["{topic} Developer", "{topic} Platform Engineer", "{topic} Solutions Engineer"],
    "Web & Frontend Frameworks": ["{topic} Frontend Engineer", "UI Platform Engineer", "Web Application Engineer"],
    "Backend & API Frameworks": ["{topic} Backend Engineer", "API Platform Engineer", "Solutions Architect"],
    "Data & Databases": ["{topic} Database Engineer", "Data Platform Engineer", "Analytics Infrastructure Engineer"],
    "Cloud & Infrastructure": ["{topic} Cloud Engineer", "Infrastructure Engineer", "Platform Architect"],
    "Mobile Development": ["{topic} Mobile Engineer", "Mobile Platform Engineer", "App Performance Engineer"],
    "Testing & QA": ["{topic} Test Automation Engineer", "QA Platform Engineer", "SDET"],
    "DevOps & Monitoring": ["{topic} DevOps Engineer", "Reliability Engineer", "Observability Engineer"],
    "Message Queues & Streaming": ["{topic} Streaming Engineer", "Event Platform Engineer", "Distributed Systems Engineer"],
    "API & Integration": ["{topic} Integration Engineer", "API Architect", "Developer Platform Engineer"],
    "Security & Compliance": ["{topic} Security Engineer", "Identity Platform Engineer", "Compliance Automation Engineer"],
    "UI/UX & Design": ["{topic} Design Systems Engineer", "Product Designer", "Frontend Design Engineer"],
    "Emerging Technologies": ["{topic} Engineer", "Emerging Technology Architect", "R&D Engineer"],
    "AI & Machine Learning": ["{topic} ML Engineer", "Applied AI Engineer", "ML Platform Engineer"],
    "Data Science": ["{topic} Data Scientist", "Analytics Engineer", "Research Engineer"],
    "CMS & Commerce": ["{topic} Developer", "Commerce Platform Engineer", "CMS Solutions Architect"],
}

CATEGORY_SKILL_DEFAULTS: dict[str, list[str]] = {
    "Programming Languages": ["Git", "Linux", "Testing", "Package Management", "APIs"],
    "Web & Frontend Frameworks": ["JavaScript", "TypeScript", "HTML5", "CSS3", "Testing"],
    "Backend & API Frameworks": ["REST APIs", "OpenAPI", "SQL", "Docker", "Observability"],
    "Data & Databases": ["SQL", "Data Modeling", "Indexing", "Query Optimization", "Backup Strategy"],
    "Cloud & Infrastructure": ["Linux", "Networking", "Terraform", "Kubernetes", "Monitoring"],
    "Mobile Development": ["Mobile UI", "App Store Delivery", "API Integration", "Testing", "Performance"],
    "Testing & QA": ["Test Automation", "CI/CD", "Mocking", "Regression Testing", "Quality Metrics"],
    "DevOps & Monitoring": ["CI/CD", "SRE", "Alerting", "Infrastructure as Code", "Incident Response"],
    "Message Queues & Streaming": ["Event-Driven Architecture", "Schema Registry", "Backpressure", "Observability", "Distributed Systems"],
    "API & Integration": ["API Design", "Authentication", "OpenAPI", "SDKs", "Integration Testing"],
    "Security & Compliance": ["Threat Modeling", "IAM", "Secrets Management", "Audit Logs", "Risk Management"],
    "UI/UX & Design": ["Design Systems", "Accessibility", "Prototyping", "User Research", "Frontend"],
    "Emerging Technologies": ["Architecture", "Prototyping", "Risk Assessment", "Research", "Developer Tooling"],
    "AI & Machine Learning": ["Python", "Model Evaluation", "MLOps", "Data Pipelines", "Serving"],
    "Data Science": ["Python", "Statistics", "Visualization", "Experiment Design", "Notebooks"],
    "CMS & Commerce": ["PHP", "Content Modeling", "SEO", "Payments", "Integrations"],
}

EXPANDED_TOPIC_SPECS: list[dict[str, Any]] = [
    # Programming languages
    {"name": "Python", "category": "Programming Languages", "base": 66, "growth": 22, "volatility": 7, "sentiment": 0.24, "skills": ["Python", "Django", "FastAPI", "Pandas", "Pytest"]},
    {"name": "JavaScript", "category": "Programming Languages", "base": 72, "growth": 8, "volatility": 5, "sentiment": 0.08, "skills": ["JavaScript", "Node.js", "React", "Testing", "Bundlers"]},
    {"name": "TypeScript", "category": "Programming Languages", "base": 64, "growth": 8, "volatility": 5, "sentiment": 0.15, "skills": ["TypeScript", "React", "Node.js", "API Types", "Testing"]},
    {"name": "Java", "category": "Programming Languages", "base": 62, "growth": -2, "volatility": 4, "sentiment": 0.02, "maturity": "mature", "skills": ["Java", "Spring Boot", "JVM", "Maven", "Microservices"]},
    {"name": "C# / .NET", "category": "Programming Languages", "base": 48, "growth": 5, "volatility": 5, "sentiment": 0.09, "skills": ["C#", ".NET", "ASP.NET Core", "Azure", "Entity Framework"]},
    {"name": "Go", "category": "Programming Languages", "base": 39, "growth": 14, "volatility": 7, "sentiment": 0.18, "skills": ["Go", "Kubernetes", "gRPC", "Concurrency", "Cloud APIs"]},
    {"name": "Rust", "category": "Programming Languages", "base": 34, "growth": 16, "volatility": 9, "sentiment": 0.2, "skills": ["Rust", "Async Rust", "Systems Programming", "WebAssembly", "Performance"]},
    {"name": "C++", "category": "Programming Languages", "base": 42, "growth": 2, "volatility": 5, "sentiment": 0.05, "skills": ["C++", "Performance", "CUDA", "Embedded", "Concurrency"]},
    {"name": "PHP", "category": "Programming Languages", "base": 38, "growth": -8, "volatility": 12, "sentiment": -0.15, "maturity": "declining", "skills": ["PHP", "Laravel", "WordPress", "Legacy Migration", "MySQL"]},
    {"name": "Ruby", "category": "Programming Languages", "base": 25, "growth": -5, "volatility": 10, "sentiment": -0.08, "maturity": "declining", "skills": ["Ruby", "Rails", "RSpec", "PostgreSQL", "Legacy Modernization"]},
    {"name": "Swift", "category": "Programming Languages", "base": 32, "growth": 6, "volatility": 6, "sentiment": 0.11, "skills": ["Swift", "SwiftUI", "iOS SDK", "Xcode", "Mobile Performance"]},
    {"name": "Kotlin", "category": "Programming Languages", "base": 35, "growth": 7, "volatility": 6, "sentiment": 0.12, "skills": ["Kotlin", "Android", "Spring", "Coroutines", "Jetpack"]},
    {"name": "R", "category": "Programming Languages", "base": 30, "growth": 8, "volatility": 7, "sentiment": 0.1, "skills": ["R", "Statistics", "Shiny", "Tidyverse", "Modeling"]},
    {"name": "Julia", "category": "Programming Languages", "base": 18, "growth": 12, "volatility": 10, "sentiment": 0.15, "skills": ["Julia", "Scientific Computing", "Optimization", "DataFrames", "Performance"]},
    {"name": "COBOL", "category": "Programming Languages", "base": 12, "growth": -12, "volatility": 7, "sentiment": -0.12, "maturity": "legacy", "skills": ["COBOL", "Mainframe", "JCL", "Batch Processing", "Migration"]},
    {"name": "Mainframe COBOL", "category": "Programming Languages", "base": 8, "growth": -6, "volatility": 7, "sentiment": -0.12, "maturity": "legacy", "skills": ["COBOL", "z/OS", "JCL", "DB2", "Legacy Modernization"]},
    {"name": "Perl", "category": "Programming Languages", "base": 11, "growth": -10, "volatility": 8, "sentiment": -0.16, "maturity": "declining", "skills": ["Perl", "Scripting", "Regex", "Linux", "Legacy Automation"]},
    {"name": "Scala", "category": "Programming Languages", "base": 21, "growth": 1, "volatility": 7, "sentiment": 0.03, "skills": ["Scala", "Spark", "Akka", "Functional Programming", "JVM"]},
    {"name": "Dart", "category": "Programming Languages", "base": 25, "growth": 9, "volatility": 7, "sentiment": 0.13, "skills": ["Dart", "Flutter", "Mobile UI", "Async", "Testing"]},
    {"name": "PowerShell", "category": "Programming Languages", "base": 28, "growth": 3, "volatility": 4, "sentiment": 0.04, "skills": ["PowerShell", "Windows Automation", "Azure", "Scripting", "DevOps"]},
    {"name": "Bash", "category": "Programming Languages", "base": 36, "growth": 1, "volatility": 3, "sentiment": 0.03, "skills": ["Bash", "Linux", "Automation", "Shell Scripting", "CI/CD"]},
    {"name": "SQL", "category": "Programming Languages", "base": 58, "growth": 3, "volatility": 3, "sentiment": 0.08, "skills": ["SQL", "Query Optimization", "Data Modeling", "Warehousing", "Analytics"]},
    {"name": "HTML5", "category": "Programming Languages", "base": 45, "growth": 1, "volatility": 2, "sentiment": 0.04, "skills": ["HTML5", "Accessibility", "Semantic HTML", "SEO", "Frontend"]},
    {"name": "CSS3", "category": "Programming Languages", "base": 44, "growth": 2, "volatility": 3, "sentiment": 0.05, "skills": ["CSS3", "Responsive Design", "CSS Grid", "Animation", "Design Systems"]},
    {"name": "Lua", "category": "Programming Languages", "base": 13, "growth": 4, "volatility": 7, "sentiment": 0.06, "skills": ["Lua", "Game Development", "Scripting", "Embedded", "Performance"]},
    # Web and backend frameworks
    {"name": "React", "category": "Web & Frontend Frameworks", "base": 60, "growth": 7, "volatility": 5, "sentiment": 0.12, "skills": ["React", "Hooks", "TypeScript", "State Management", "Testing"]},
    {"name": "Vue.js", "category": "Web & Frontend Frameworks", "base": 36, "growth": 6, "volatility": 5, "sentiment": 0.1, "skills": ["Vue.js", "Nuxt", "Pinia", "TypeScript", "Composition API"]},
    {"name": "Angular", "category": "Web & Frontend Frameworks", "base": 35, "growth": -1, "volatility": 6, "sentiment": 0.02, "maturity": "mature", "skills": ["Angular", "TypeScript", "RxJS", "NgRx", "Enterprise UI"]},
    {"name": "Next.js", "category": "Web & Frontend Frameworks", "base": 42, "growth": 13, "volatility": 8, "sentiment": 0.17, "skills": ["Next.js", "React", "Server Components", "Vercel", "TypeScript"]},
    {"name": "Svelte", "category": "Web & Frontend Frameworks", "base": 21, "growth": 11, "volatility": 8, "sentiment": 0.14, "skills": ["Svelte", "SvelteKit", "TypeScript", "Frontend Performance", "Components"]},
    {"name": "Astro", "category": "Web & Frontend Frameworks", "base": 18, "growth": 15, "volatility": 9, "sentiment": 0.18, "skills": ["Astro", "Static Sites", "Islands Architecture", "Content", "Performance"]},
    {"name": "Blazor", "category": "Web & Frontend Frameworks", "base": 20, "growth": 8, "volatility": 6, "sentiment": 0.1, "skills": ["Blazor", ".NET", "C#", "WebAssembly", "Azure"]},
    {"name": "HTMX", "category": "Web & Frontend Frameworks", "base": 16, "growth": 14, "volatility": 10, "sentiment": 0.16, "skills": ["HTMX", "Server-Rendered UI", "HTML", "Progressive Enhancement", "Django"]},
    {"name": "jQuery", "category": "Web & Frontend Frameworks", "base": 12, "growth": -14, "volatility": 8, "sentiment": -0.22, "maturity": "declining", "skills": ["jQuery", "Legacy UI", "Migration", "JavaScript", "Browser Compatibility"]},
    {"name": "FastAPI", "category": "Backend & API Frameworks", "base": 34, "growth": 14, "volatility": 7, "sentiment": 0.19, "skills": ["FastAPI", "Python", "OpenAPI", "AsyncIO", "Pydantic"]},
    {"name": "Spring Boot", "category": "Backend & API Frameworks", "base": 50, "growth": 4, "volatility": 4, "sentiment": 0.08, "skills": ["Spring Boot", "Java", "Microservices", "JPA", "Cloud"]},
    {"name": "Django", "category": "Backend & API Frameworks", "base": 36, "growth": 3, "volatility": 4, "sentiment": 0.09, "skills": ["Django", "Python", "PostgreSQL", "ORM", "REST Framework"]},
    {"name": "Flask", "category": "Backend & API Frameworks", "base": 31, "growth": 1, "volatility": 4, "sentiment": 0.05, "skills": ["Flask", "Python", "APIs", "SQLAlchemy", "Testing"]},
    {"name": "Express.js", "category": "Backend & API Frameworks", "base": 42, "growth": 2, "volatility": 4, "sentiment": 0.05, "skills": ["Express.js", "Node.js", "REST APIs", "Middleware", "MongoDB"]},
    {"name": "NestJS", "category": "Backend & API Frameworks", "base": 28, "growth": 8, "volatility": 6, "sentiment": 0.12, "skills": ["NestJS", "TypeScript", "Node.js", "Decorators", "Microservices"]},
    {"name": "ASP.NET Core", "category": "Backend & API Frameworks", "base": 39, "growth": 6, "volatility": 5, "sentiment": 0.11, "skills": ["ASP.NET Core", "C#", "Entity Framework", "Azure", "APIs"]},
    {"name": "Laravel", "category": "Backend & API Frameworks", "base": 28, "growth": -3, "volatility": 7, "sentiment": -0.03, "maturity": "declining", "skills": ["Laravel", "PHP", "Eloquent", "MySQL", "Legacy Modernization"]},
    {"name": "RubyOnRails", "category": "Backend & API Frameworks", "base": 22, "growth": -6, "volatility": 8, "sentiment": -0.08, "maturity": "declining", "skills": ["Rails", "Ruby", "ActiveRecord", "PostgreSQL", "Monolith Modernization"]},
    {"name": "ColdFusion", "category": "Backend & API Frameworks", "base": 5, "growth": -13, "volatility": 9, "sentiment": -0.24, "maturity": "legacy", "skills": ["ColdFusion", "Legacy Web", "Migration", "SQL Server", "Security Remediation"]},
    {"name": "Flash", "category": "Web & Frontend Frameworks", "base": 2, "growth": -18, "volatility": 14, "sentiment": -0.45, "maturity": "obsolete", "skills": ["Flash Migration", "Legacy Media", "HTML5", "Security", "Archival Systems"]},
    # Data and databases
    {"name": "PostgreSQL", "category": "Data & Databases", "base": 46, "growth": 4, "volatility": 4, "sentiment": 0.13, "skills": ["PostgreSQL", "SQL", "Indexing", "JSONB", "Performance"]},
    {"name": "MongoDB", "category": "Data & Databases", "base": 38, "growth": 3, "volatility": 5, "sentiment": 0.07, "skills": ["MongoDB", "Document Modeling", "Atlas", "Aggregation", "Indexing"]},
    {"name": "MySQL", "category": "Data & Databases", "base": 42, "growth": 0, "volatility": 3, "sentiment": 0.03, "skills": ["MySQL", "SQL", "Replication", "Performance", "Backups"]},
    {"name": "Redis", "category": "Data & Databases", "base": 40, "growth": 5, "volatility": 5, "sentiment": 0.09, "skills": ["Redis", "Caching", "Redis Streams", "Queues", "Performance"]},
    {"name": "Elasticsearch", "category": "Data & Databases", "base": 34, "growth": 3, "volatility": 5, "sentiment": 0.04, "skills": ["Elasticsearch", "Search", "Indexing", "ELK Stack", "Relevance"]},
    {"name": "DuckDB", "category": "Data & Databases", "base": 18, "growth": 16, "volatility": 9, "sentiment": 0.18, "skills": ["DuckDB", "Analytics", "Parquet", "SQL", "Local OLAP"]},
    {"name": "Pinecone", "category": "Data & Databases", "base": 21, "growth": 18, "volatility": 10, "sentiment": 0.17, "skills": ["Pinecone", "Vector Search", "Embeddings", "RAG", "Indexing"]},
    {"name": "Supabase", "category": "Data & Databases", "base": 24, "growth": 12, "volatility": 7, "sentiment": 0.16, "skills": ["Supabase", "PostgreSQL", "Auth", "Realtime", "Edge Functions"]},
    {"name": "Firebase", "category": "Data & Databases", "base": 35, "growth": 2, "volatility": 5, "sentiment": 0.07, "skills": ["Firebase", "Firestore", "Auth", "Mobile Backend", "Cloud Functions"]},
    {"name": "Graph Databases", "category": "Data & Databases", "base": 22, "growth": 10, "volatility": 7, "sentiment": 0.12, "skills": ["Neo4j", "Graph Modeling", "Cypher", "Knowledge Graphs", "Analytics"]},
    {"name": "Time-series DBs", "category": "Data & Databases", "base": 25, "growth": 11, "volatility": 7, "sentiment": 0.1, "skills": ["InfluxDB", "Prometheus", "Metrics", "Retention Policies", "Observability"]},
    {"name": "ClickHouse", "category": "Data & Databases", "base": 26, "growth": 10, "volatility": 7, "sentiment": 0.11, "skills": ["ClickHouse", "OLAP", "SQL", "Columnar Storage", "Analytics"]},
    {"name": "Snowflake", "category": "Data & Databases", "base": 42, "growth": 5, "volatility": 5, "sentiment": 0.09, "skills": ["Snowflake", "Warehousing", "SQL", "Data Sharing", "Governance"]},
    {"name": "Databricks", "category": "Data & Databases", "base": 41, "growth": 7, "volatility": 6, "sentiment": 0.11, "skills": ["Databricks", "Spark", "Lakehouse", "MLflow", "Delta Lake"]},
    {"name": "Oracle Database", "category": "Data & Databases", "base": 35, "growth": -1, "volatility": 4, "sentiment": 0.0, "maturity": "mature", "skills": ["Oracle", "PL/SQL", "Performance", "Enterprise DB", "Migration"]},
    # Cloud, infrastructure, mobile, testing, DevOps, queues
    {"name": "AWS", "category": "Cloud & Infrastructure", "base": 57, "growth": 3, "volatility": 4, "sentiment": 0.08, "skills": ["AWS", "EC2", "S3", "Lambda", "IAM"]},
    {"name": "Azure", "category": "Cloud & Infrastructure", "base": 49, "growth": 4, "volatility": 4, "sentiment": 0.08, "skills": ["Azure", "Azure Functions", "AKS", "Entra ID", "DevOps"]},
    {"name": "Google Cloud", "category": "Cloud & Infrastructure", "base": 39, "growth": 2, "volatility": 4, "sentiment": 0.06, "skills": ["Google Cloud", "BigQuery", "Cloud Run", "GKE", "Pub/Sub"]},
    {"name": "Kubernetes", "category": "Cloud & Infrastructure", "base": 52, "growth": 5, "volatility": 5, "sentiment": 0.1, "skills": ["Kubernetes", "Helm", "Operators", "Networking", "Observability"]},
    {"name": "Docker", "category": "Cloud & Infrastructure", "base": 50, "growth": 2, "volatility": 3, "sentiment": 0.08, "skills": ["Docker", "Containers", "Compose", "Images", "CI/CD"]},
    {"name": "Terraform", "category": "Cloud & Infrastructure", "base": 44, "growth": 6, "volatility": 5, "sentiment": 0.1, "skills": ["Terraform", "IaC", "AWS", "Modules", "Policy as Code"]},
    {"name": "Ansible", "category": "Cloud & Infrastructure", "base": 30, "growth": 1, "volatility": 4, "sentiment": 0.04, "skills": ["Ansible", "Playbooks", "Linux", "Automation", "Configuration"]},
    {"name": "Pulumi", "category": "Cloud & Infrastructure", "base": 20, "growth": 8, "volatility": 7, "sentiment": 0.11, "skills": ["Pulumi", "IaC", "TypeScript", "Cloud SDKs", "Automation"]},
    {"name": "CloudFormation", "category": "Cloud & Infrastructure", "base": 24, "growth": 0, "volatility": 4, "sentiment": 0.01, "skills": ["CloudFormation", "AWS", "IaC", "Templates", "StackSets"]},
    {"name": "React Native", "category": "Mobile Development", "base": 32, "growth": 4, "volatility": 6, "sentiment": 0.08, "skills": ["React Native", "Expo", "Mobile UI", "TypeScript", "Native Modules"]},
    {"name": "Flutter", "category": "Mobile Development", "base": 34, "growth": 11, "volatility": 8, "sentiment": 0.15, "skills": ["Flutter", "Dart", "Mobile UI", "State Management", "Performance"]},
    {"name": "Swift iOS", "category": "Mobile Development", "base": 33, "growth": 5, "volatility": 5, "sentiment": 0.09, "skills": ["Swift", "SwiftUI", "iOS SDK", "Xcode", "App Store"]},
    {"name": "Kotlin Android", "category": "Mobile Development", "base": 34, "growth": 6, "volatility": 5, "sentiment": 0.1, "skills": ["Kotlin", "Android", "Jetpack Compose", "Coroutines", "Gradle"]},
    {"name": "Xamarin", "category": "Mobile Development", "base": 12, "growth": -4, "volatility": 7, "sentiment": -0.08, "maturity": "declining", "skills": ["Xamarin", ".NET MAUI", "Migration", "C#", "Mobile Apps"]},
    {"name": "Ionic", "category": "Mobile Development", "base": 15, "growth": -1, "volatility": 6, "sentiment": -0.02, "maturity": "mature", "skills": ["Ionic", "Capacitor", "Angular", "Hybrid Apps", "Mobile UI"]},
    {"name": "Jest", "category": "Testing & QA", "base": 34, "growth": 9, "volatility": 5, "sentiment": 0.12, "skills": ["Jest", "JavaScript Testing", "Mocks", "React Testing", "CI"]},
    {"name": "Pytest", "category": "Testing & QA", "base": 31, "growth": 8, "volatility": 5, "sentiment": 0.13, "skills": ["Pytest", "Fixtures", "Python", "Test Automation", "CI"]},
    {"name": "Selenium", "category": "Testing & QA", "base": 29, "growth": 1, "volatility": 4, "sentiment": 0.02, "skills": ["Selenium", "WebDriver", "Automation", "Cross-Browser Testing", "Java"]},
    {"name": "Cypress", "category": "Testing & QA", "base": 27, "growth": 7, "volatility": 5, "sentiment": 0.1, "skills": ["Cypress", "E2E Testing", "JavaScript", "CI", "Frontend QA"]},
    {"name": "JUnit", "category": "Testing & QA", "base": 27, "growth": 0, "volatility": 3, "sentiment": 0.02, "skills": ["JUnit", "Java", "Unit Testing", "Mockito", "CI"]},
    {"name": "TestNG", "category": "Testing & QA", "base": 16, "growth": 0, "volatility": 4, "sentiment": 0.0, "skills": ["TestNG", "Java Testing", "Automation", "Selenium", "CI"]},
    {"name": "Vitest", "category": "Testing & QA", "base": 17, "growth": 12, "volatility": 8, "sentiment": 0.15, "skills": ["Vitest", "Vite", "TypeScript", "Unit Testing", "Frontend"]},
    {"name": "GitHub Actions", "category": "DevOps & Monitoring", "base": 42, "growth": 10, "volatility": 6, "sentiment": 0.14, "skills": ["GitHub Actions", "CI/CD", "YAML", "Security Scanning", "Automation"]},
    {"name": "GitLab CI/CD", "category": "DevOps & Monitoring", "base": 34, "growth": 6, "volatility": 5, "sentiment": 0.08, "skills": ["GitLab CI/CD", "Pipelines", "Docker", "Kubernetes", "DevSecOps"]},
    {"name": "Jenkins", "category": "DevOps & Monitoring", "base": 32, "growth": -2, "volatility": 5, "sentiment": -0.04, "maturity": "mature", "skills": ["Jenkins", "Pipelines", "Groovy", "Legacy CI", "Migration"]},
    {"name": "ArgoCD", "category": "DevOps & Monitoring", "base": 25, "growth": 9, "volatility": 7, "sentiment": 0.12, "skills": ["ArgoCD", "GitOps", "Kubernetes", "Helm", "Deployment"]},
    {"name": "Prometheus", "category": "DevOps & Monitoring", "base": 36, "growth": 5, "volatility": 5, "sentiment": 0.09, "skills": ["Prometheus", "Metrics", "Alertmanager", "Grafana", "SRE"]},
    {"name": "Grafana", "category": "DevOps & Monitoring", "base": 35, "growth": 4, "volatility": 5, "sentiment": 0.1, "skills": ["Grafana", "Dashboards", "Prometheus", "Loki", "Observability"]},
    {"name": "Datadog", "category": "DevOps & Monitoring", "base": 33, "growth": 3, "volatility": 4, "sentiment": 0.06, "skills": ["Datadog", "APM", "Logs", "Metrics", "SLOs"]},
    {"name": "New Relic", "category": "DevOps & Monitoring", "base": 25, "growth": 0, "volatility": 4, "sentiment": 0.01, "skills": ["New Relic", "APM", "Monitoring", "Dashboards", "SLOs"]},
    {"name": "ELK Stack", "category": "DevOps & Monitoring", "base": 30, "growth": 1, "volatility": 5, "sentiment": 0.02, "skills": ["Elasticsearch", "Logstash", "Kibana", "Logs", "Search"]},
    {"name": "Apache Kafka", "category": "Message Queues & Streaming", "base": 41, "growth": 5, "volatility": 5, "sentiment": 0.1, "skills": ["Kafka", "Kafka Streams", "Schema Registry", "Event Streaming", "Distributed Systems"]},
    {"name": "RabbitMQ", "category": "Message Queues & Streaming", "base": 26, "growth": 1, "volatility": 4, "sentiment": 0.03, "skills": ["RabbitMQ", "AMQP", "Queues", "Exchanges", "Reliability"]},
    {"name": "Redis Streams", "category": "Message Queues & Streaming", "base": 22, "growth": 6, "volatility": 6, "sentiment": 0.08, "skills": ["Redis Streams", "Event Processing", "Queues", "Consumer Groups", "Redis"]},
    {"name": "Apache Pulsar", "category": "Message Queues & Streaming", "base": 20, "growth": 8, "volatility": 7, "sentiment": 0.09, "skills": ["Pulsar", "Streaming", "Multi-Tenancy", "Schema Registry", "Messaging"]},
    {"name": "NATS", "category": "Message Queues & Streaming", "base": 17, "growth": 9, "volatility": 8, "sentiment": 0.12, "skills": ["NATS", "JetStream", "Messaging", "Edge", "Distributed Systems"]},
    # API, security, UI, emerging, AI, commerce
    {"name": "GraphQL", "category": "API & Integration", "base": 35, "growth": 6, "volatility": 5, "sentiment": 0.08, "skills": ["GraphQL", "Apollo", "Schema Design", "Federation", "API Security"]},
    {"name": "REST APIs", "category": "API & Integration", "base": 55, "growth": 1, "volatility": 3, "sentiment": 0.04, "skills": ["REST APIs", "HTTP", "OpenAPI", "API Design", "Authentication"]},
    {"name": "OpenAPI/Swagger", "category": "API & Integration", "base": 34, "growth": 4, "volatility": 4, "sentiment": 0.08, "skills": ["OpenAPI", "Swagger", "API Contracts", "Documentation", "SDK Generation"]},
    {"name": "gRPC", "category": "API & Integration", "base": 30, "growth": 7, "volatility": 5, "sentiment": 0.1, "skills": ["gRPC", "Protobuf", "Streaming APIs", "Go", "Microservices"]},
    {"name": "Webhooks", "category": "API & Integration", "base": 31, "growth": 2, "volatility": 4, "sentiment": 0.04, "skills": ["Webhooks", "Event Delivery", "Retries", "API Integrations", "Security"]},
    {"name": "OAuth 2.0 / OpenID Connect", "category": "Security & Compliance", "base": 38, "growth": 2, "volatility": 3, "sentiment": 0.04, "skills": ["OAuth 2.0", "OpenID Connect", "Identity", "JWT", "Security"]},
    {"name": "SAML", "category": "Security & Compliance", "base": 22, "growth": 0, "volatility": 3, "sentiment": 0.0, "skills": ["SAML", "SSO", "Identity", "Enterprise Security", "Federation"]},
    {"name": "Vault", "category": "Security & Compliance", "base": 28, "growth": 5, "volatility": 5, "sentiment": 0.08, "skills": ["HashiCorp Vault", "Secrets Management", "PKI", "Kubernetes", "Security"]},
    {"name": "JWT", "category": "Security & Compliance", "base": 32, "growth": 3, "volatility": 4, "sentiment": 0.04, "skills": ["JWT", "Authentication", "API Security", "Token Rotation", "OAuth"]},
    {"name": "OWASP Security", "category": "Security & Compliance", "base": 34, "growth": 4, "volatility": 5, "sentiment": 0.06, "skills": ["OWASP", "AppSec", "Threat Modeling", "Secure Coding", "Testing"]},
    {"name": "Zero-Trust Security", "category": "Security & Compliance", "base": 29, "growth": 12, "volatility": 8, "sentiment": 0.12, "skills": ["Zero Trust", "IAM", "Network Security", "Policy", "Device Trust"]},
    {"name": "Figma", "category": "UI/UX & Design", "base": 38, "growth": 13, "volatility": 7, "sentiment": 0.18, "skills": ["Figma", "Design Systems", "Prototyping", "Handoff", "User Research"]},
    {"name": "Tailwind CSS", "category": "UI/UX & Design", "base": 37, "growth": 10, "volatility": 7, "sentiment": 0.13, "skills": ["Tailwind CSS", "Responsive Design", "Design Tokens", "React", "Frontend"]},
    {"name": "Material Design", "category": "UI/UX & Design", "base": 28, "growth": 2, "volatility": 4, "sentiment": 0.04, "skills": ["Material Design", "Android", "Design Systems", "Accessibility", "Components"]},
    {"name": "Bootstrap", "category": "UI/UX & Design", "base": 30, "growth": -2, "volatility": 4, "sentiment": -0.04, "maturity": "mature", "skills": ["Bootstrap", "CSS", "Legacy UI", "Responsive Design", "Migration"]},
    {"name": "Chakra UI", "category": "UI/UX & Design", "base": 20, "growth": 8, "volatility": 6, "sentiment": 0.1, "skills": ["Chakra UI", "React", "Design Systems", "Accessibility", "Components"]},
    {"name": "Storybook", "category": "UI/UX & Design", "base": 27, "growth": 6, "volatility": 5, "sentiment": 0.09, "skills": ["Storybook", "Component Testing", "Design Systems", "React", "Documentation"]},
    {"name": "Accessibility", "category": "UI/UX & Design", "base": 31, "growth": 7, "volatility": 5, "sentiment": 0.12, "skills": ["WCAG", "Accessibility Testing", "Semantic HTML", "ARIA", "Inclusive Design"]},
    {"name": "WebAssembly", "category": "Emerging Technologies", "base": 21, "growth": 16, "volatility": 10, "sentiment": 0.16, "skills": ["WebAssembly", "Rust", "WASM Runtime", "Performance", "Browser APIs"]},
    {"name": "Blockchain Dev", "category": "Emerging Technologies", "base": 25, "growth": 4, "volatility": 16, "sentiment": 0.02, "skills": ["Solidity", "Smart Contracts", "Ethereum", "Security", "Web3"]},
    {"name": "Quantum Computing", "category": "Emerging Technologies", "base": 10, "growth": 18, "volatility": 14, "sentiment": 0.14, "skills": ["Qiskit", "Quantum Algorithms", "Python", "Research", "Simulation"]},
    {"name": "AR/VR Development", "category": "Emerging Technologies", "base": 22, "growth": 9, "volatility": 10, "sentiment": 0.08, "skills": ["Unity", "Unreal Engine", "WebXR", "3D Interaction", "Performance"]},
    {"name": "IoT Development", "category": "Emerging Technologies", "base": 28, "growth": 8, "volatility": 7, "sentiment": 0.09, "skills": ["IoT", "MQTT", "Embedded", "Edge", "Security"]},
    {"name": "Edge Computing", "category": "Emerging Technologies", "base": 31, "growth": 11, "volatility": 8, "sentiment": 0.12, "skills": ["Edge Computing", "Kubernetes", "Networking", "Observability", "IoT"]},
    {"name": "Serverless Architecture", "category": "Emerging Technologies", "base": 36, "growth": 7, "volatility": 6, "sentiment": 0.1, "skills": ["Serverless", "AWS Lambda", "Cloud Functions", "Event-Driven", "Cost Optimization"]},
    {"name": "Microservices Architecture", "category": "Emerging Technologies", "base": 43, "growth": 5, "volatility": 5, "sentiment": 0.07, "skills": ["Microservices", "APIs", "Kubernetes", "Observability", "Distributed Systems"]},
    {"name": "Low-Code/No-Code", "category": "Emerging Technologies", "base": 30, "growth": 14, "volatility": 9, "sentiment": 0.11, "skills": ["Low-Code", "Workflow Automation", "Zapier", "Business Apps", "Governance"]},
    {"name": "API-First Development", "category": "Emerging Technologies", "base": 33, "growth": 8, "volatility": 5, "sentiment": 0.1, "skills": ["API Design", "OpenAPI", "Developer Experience", "SDKs", "Governance"]},
    {"name": "PyTorch", "category": "AI & Machine Learning", "base": 42, "growth": 9, "volatility": 7, "sentiment": 0.14, "skills": ["PyTorch", "Deep Learning", "CUDA", "Model Training", "Serving"]},
    {"name": "TensorFlow", "category": "AI & Machine Learning", "base": 36, "growth": 1, "volatility": 5, "sentiment": 0.03, "skills": ["TensorFlow", "Keras", "ML", "Serving", "TensorFlow Lite"]},
    {"name": "Transformers", "category": "AI & Machine Learning", "base": 45, "growth": 12, "volatility": 7, "sentiment": 0.18, "skills": ["Transformers", "NLP", "Hugging Face", "Fine-tuning", "Evaluation"]},
    {"name": "LangChain", "category": "AI & Machine Learning", "base": 34, "growth": 13, "volatility": 10, "sentiment": 0.12, "skills": ["LangChain", "RAG", "Agents", "Vector Stores", "Tool Calling"]},
    {"name": "Pandas", "category": "Data Science", "base": 44, "growth": 4, "volatility": 4, "sentiment": 0.08, "skills": ["Pandas", "DataFrames", "Python", "Analytics", "ETL"]},
    {"name": "Polars", "category": "Data Science", "base": 18, "growth": 15, "volatility": 9, "sentiment": 0.16, "skills": ["Polars", "DataFrames", "Rust", "Python", "Performance"]},
    {"name": "Spark", "category": "Data Science", "base": 39, "growth": 3, "volatility": 5, "sentiment": 0.06, "skills": ["Spark", "PySpark", "Scala", "Data Engineering", "Streaming"]},
    {"name": "WordPress", "category": "CMS & Commerce", "base": 36, "growth": -3, "volatility": 6, "sentiment": -0.03, "maturity": "mature", "skills": ["WordPress", "PHP", "Plugins", "SEO", "WooCommerce"]},
    {"name": "Shopify", "category": "CMS & Commerce", "base": 33, "growth": 5, "volatility": 5, "sentiment": 0.08, "skills": ["Shopify", "Liquid", "Commerce", "Payments", "Apps"]},
    {"name": "Drupal", "category": "CMS & Commerce", "base": 18, "growth": -2, "volatility": 5, "sentiment": -0.03, "maturity": "mature", "skills": ["Drupal", "PHP", "Content Modeling", "Enterprise CMS", "Migration"]},
]

REAL_COMPANY_EXPANSIONS: list[dict[str, Any]] = [
    {"company": "Microsoft", "country": "US", "sector": ".NET, Azure and Developer Platforms", "stage": "public", "reference_type": "real_reference", "topics": ["C# / .NET", "ASP.NET Core", "Blazor", "Azure", "TypeScript", "GitHub Actions", "OAuth 2.0 / OpenID Connect"]},
    {"company": "Telerik", "country": "US", "sector": ".NET UI Components", "stage": "subsidiary", "reference_type": "real_reference", "topics": ["C# / .NET", "Blazor", "ASP.NET Core"]},
    {"company": "Progress Software", "country": "US", "sector": "Enterprise Software", "stage": "public", "reference_type": "real_reference", "topics": ["C# / .NET", "Telerik", "Data & Databases"]},
    {"company": "JetBrains", "country": "DE", "sector": "Developer Tools", "stage": "private", "reference_type": "real_reference", "topics": ["Kotlin", "Java", "Python", "Go", "Rust", "Developer Tools"]},
    {"company": "Meta", "country": "US", "sector": "Social and Open Source", "stage": "public", "reference_type": "real_reference", "topics": ["React", "React Native", "PyTorch", "JavaScript", "TypeScript"]},
    {"company": "Vercel", "country": "US", "sector": "Frontend Cloud", "stage": "private", "reference_type": "real_reference", "topics": ["Next.js", "React", "TypeScript", "Developer Tools"]},
    {"company": "Google", "country": "US", "sector": "Cloud and Mobile", "stage": "public", "reference_type": "real_reference", "topics": ["Angular", "Flutter", "Dart", "Kotlin Android", "Google Cloud", "Firebase", "TensorFlow"]},
    {"company": "Oracle", "country": "US", "sector": "Enterprise Software", "stage": "public", "reference_type": "real_reference", "topics": ["Java", "Oracle Database", "MySQL", "Cloud Computing"]},
    {"company": "Automattic", "country": "US", "sector": "CMS", "stage": "private", "reference_type": "real_reference", "topics": ["PHP", "WordPress", "WooCommerce", "CMS & Commerce"]},
    {"company": "Laravel Holdings", "country": "US", "sector": "PHP Frameworks", "stage": "private", "reference_type": "real_reference", "topics": ["Laravel", "PHP"]},
    {"company": "Shopify", "country": "CA", "sector": "Commerce", "stage": "public", "reference_type": "real_reference", "topics": ["Shopify", "Ruby", "React", "GraphQL"]},
    {"company": "Mozilla", "country": "US", "sector": "Web Platform", "stage": "nonprofit", "reference_type": "real_reference", "topics": ["Rust", "WebAssembly", "JavaScript", "HTML5", "CSS3"]},
    {"company": "Amazon", "country": "US", "sector": "Cloud and Commerce", "stage": "public", "reference_type": "real_reference", "topics": ["AWS", "Java", "Rust", "Go", "Serverless Architecture"]},
    {"company": "CNCF", "country": "US", "sector": "Cloud Native Foundation", "stage": "nonprofit", "reference_type": "real_reference", "topics": ["Kubernetes", "Prometheus", "ArgoCD", "OpenTelemetry", "Cloud & Infrastructure"]},
    {"company": "Docker", "country": "US", "sector": "Container Tooling", "stage": "private", "reference_type": "real_reference", "topics": ["Docker", "Developer Tools", "Cloud & Infrastructure"]},
    {"company": "HashiCorp", "country": "US", "sector": "Infrastructure Automation", "stage": "public", "reference_type": "real_reference", "topics": ["Terraform", "Vault", "Cloud & Infrastructure", "Security & Compliance"]},
    {"company": "Grafana Labs", "country": "US", "sector": "Observability", "stage": "private", "reference_type": "real_reference", "topics": ["Grafana", "Prometheus", "Loki", "DevOps & Monitoring"]},
    {"company": "Confluent", "country": "US", "sector": "Streaming Data", "stage": "public", "reference_type": "real_reference", "topics": ["Apache Kafka", "Data Engineering", "Message Queues & Streaming"]},
    {"company": "Figma", "country": "US", "sector": "Design Tools", "stage": "private", "reference_type": "real_reference", "topics": ["Figma", "UI/UX & Design", "Design Systems"]},
    {"company": "OpenJS Foundation", "country": "US", "sector": "Open Source Foundation", "stage": "nonprofit", "reference_type": "real_reference", "topics": ["JavaScript", "Node.js", "jQuery", "Web & Frontend Frameworks"]},
    {"company": "IBM", "country": "US", "sector": "Enterprise and Mainframe", "stage": "public", "reference_type": "real_reference", "topics": ["COBOL", "Mainframe COBOL", "Java", "Security & Compliance"]},
]

SYNTHETIC_COMPANY_BLUEPRINTS: list[tuple[str, str, str, str, str]] = [
    ("Northstar Web Labs", "US", "Frontend Platforms", "series_a", "Web & Frontend Frameworks"),
    ("MetroUI Systems", "UK", "Design Systems", "series_b", "UI/UX & Design"),
    ("Orbit API Works", "US", "API Platforms", "series_a", "API & Integration"),
    ("Cobalt Integration", "IN", "Enterprise Integration", "series_b", "API & Integration"),
    ("ByteForge Labs", "DE", "Language Tooling", "series_a", "Programming Languages"),
    ("RustBridge Systems", "US", "Systems Software", "series_b", "Programming Languages"),
    ("LegacyLift Consulting", "UK", "Legacy Modernization", "series_a", "Programming Languages"),
    ("Mainframe Renewal Co", "US", "Mainframe Services", "private", "Programming Languages"),
    ("BluePeak .NET Studio", "CA", ".NET Consulting", "series_a", "Backend & API Frameworks"),
    ("SpringGrid Software", "DE", "Enterprise Java", "series_b", "Backend & API Frameworks"),
    ("AsyncRiver", "SG", "Python API Platforms", "seed", "Backend & API Frameworks"),
    ("NodeHarbor", "US", "Node.js Platforms", "series_a", "Backend & API Frameworks"),
    ("DataQuarry", "US", "Analytics Databases", "series_b", "Data & Databases"),
    ("VectorHarbor", "CA", "Vector Search", "series_a", "Data & Databases"),
    ("GraphNexus", "FR", "Graph Data", "series_a", "Data & Databases"),
    ("TimeScaleOps", "DE", "Metrics Data", "series_b", "Data & Databases"),
    ("CloudPilot AI", "US", "Cloud Automation", "series_b", "Cloud & Infrastructure"),
    ("KubeHarbor", "SG", "Kubernetes Platforms", "series_a", "Cloud & Infrastructure"),
    ("InfraMosaic", "IN", "Infrastructure as Code", "series_a", "Cloud & Infrastructure"),
    ("EdgeStack Works", "JP", "Edge Infrastructure", "series_a", "Cloud & Infrastructure"),
    ("MobileForge Asia", "SG", "Mobile Apps", "series_a", "Mobile Development"),
    ("FlutterNorth", "CA", "Cross-Platform Apps", "seed", "Mobile Development"),
    ("NativeSignal", "US", "Native Mobile", "series_b", "Mobile Development"),
    ("QAFlow Labs", "IN", "Test Automation", "series_a", "Testing & QA"),
    ("TestPilot Cloud", "US", "Quality Platforms", "series_b", "Testing & QA"),
    ("VitestWorks", "FR", "Frontend Testing", "seed", "Testing & QA"),
    ("PipelineFoundry", "US", "CI/CD", "series_b", "DevOps & Monitoring"),
    ("ObservaCloud", "DE", "Observability", "series_a", "DevOps & Monitoring"),
    ("GitOpsGarden", "UK", "GitOps Platforms", "seed", "DevOps & Monitoring"),
    ("StreamForge", "US", "Event Streaming", "series_b", "Message Queues & Streaming"),
    ("NATSWorks", "CA", "Edge Messaging", "series_a", "Message Queues & Streaming"),
    ("QueueVista", "IN", "Messaging Middleware", "series_a", "Message Queues & Streaming"),
    ("IdentityMesh", "US", "Identity Security", "series_b", "Security & Compliance"),
    ("ZeroTrustOps", "US", "Zero Trust", "series_a", "Security & Compliance"),
    ("VaultBridge", "DE", "Secrets Automation", "seed", "Security & Compliance"),
    ("DesignOps Studio", "UK", "Design Operations", "series_a", "UI/UX & Design"),
    ("A11yWorks", "CA", "Accessibility Tooling", "seed", "UI/UX & Design"),
    ("TailwindCraft", "IN", "Frontend Design", "series_a", "UI/UX & Design"),
    ("WasmForge", "US", "WebAssembly Tooling", "series_a", "Emerging Technologies"),
    ("QuantumPilot", "US", "Quantum Software", "seed", "Emerging Technologies"),
    ("XRFoundry", "JP", "AR/VR Platforms", "series_a", "Emerging Technologies"),
    ("IoTMesh Labs", "CN", "IoT Platforms", "series_b", "Emerging Technologies"),
    ("EdgeNova Systems", "SG", "Edge Computing", "series_b", "Emerging Technologies"),
    ("NoCodeOps", "US", "Low-Code Automation", "series_a", "Emerging Technologies"),
    ("ModelSignal", "US", "ML Platforms", "series_b", "AI & Machine Learning"),
    ("TorchServeOps", "CA", "ML Serving", "series_a", "AI & Machine Learning"),
    ("PromptOps Labs", "UK", "AI Applications", "seed", "AI & Machine Learning"),
    ("PolarsBench", "DE", "Data Science Tools", "seed", "Data Science"),
    ("NotebookOps", "IN", "Analytics Workspaces", "series_a", "Data Science"),
    ("CommerceMesh", "US", "Commerce Platforms", "series_b", "CMS & Commerce"),
    ("HeadlessWorks", "FR", "Headless CMS", "series_a", "CMS & Commerce"),
    ("LegacyCMS Rescue", "UK", "CMS Modernization", "seed", "CMS & Commerce"),
    ("OpenSourceDesk", "IN", "Developer Communities", "series_a", "Developer Tools"),
    ("RegionalSkill Labs", "AE", "Education Analytics", "seed", "Developer Tools"),
]

ORIGINAL_TOPIC_CATEGORIES = {
    "AI Agents": "AI & Machine Learning",
    "LLM": "AI & Machine Learning",
    "Generative AI": "AI & Machine Learning",
    "Cybersecurity": "Security & Compliance",
    "Cloud Computing": "Cloud & Infrastructure",
    "DevOps": "DevOps & Monitoring",
    "Edge AI": "Emerging Technologies",
    "Robotics": "Emerging Technologies",
    "Web3": "Emerging Technologies",
    "Semiconductors": "Emerging Technologies",
    "SaaS": "CMS & Commerce",
    "Data Engineering": "Data Science",
    "Automation": "Emerging Technologies",
    "MLOps": "AI & Machine Learning",
    "Open Source AI": "AI & Machine Learning",
    "GPU Infrastructure": "Cloud & Infrastructure",
    "Developer Tools": "Emerging Technologies",
    "Vector Databases": "Data & Databases",
    "Inference Optimization": "AI & Machine Learning",
    "Enterprise AI": "AI & Machine Learning",
}


def _topic_names_from_specs() -> set[str]:
    return set(TOPICS) | {str(spec["name"]) for spec in EXPANDED_TOPIC_SPECS}


def _next_company_id() -> str:
    max_id = 0
    for company in COMPANIES:
        try:
            max_id = max(max_id, int(str(company["company_id"]).split("-")[-1]))
        except Exception:
            continue
    return f"CMP-{max_id + 1:03d}"


def _ensure_company(
    company: str,
    country: str,
    sector: str,
    stage: str,
    reference_type: str,
    topics: list[str],
) -> str:
    valid_topics = sorted(set(topics) & _topic_names_from_specs())
    for existing in COMPANIES:
        if existing["company"].lower() == company.lower():
            existing["topics"] = sorted(set(existing.get("topics", [])) | set(valid_topics))
            existing["sector"] = existing.get("sector") or sector
            return existing["company_id"]
    company_id = _next_company_id()
    COMPANIES.append(
        {
            "company_id": company_id,
            "company": company,
            "country": country,
            "sector": sector,
            "stage": stage,
            "reference_type": reference_type,
            "topics": valid_topics,
        }
    )
    return company_id


def _topic_lifecycle(name: str, growth: float, maturity: str | None = None) -> str:
    if maturity:
        return maturity
    if name in DECLINING_TECHNOLOGIES or growth <= -4:
        return "declining"
    if name in EMERGING_TECHNOLOGIES or growth >= 10:
        return "emerging"
    if growth <= 2:
        return "mature"
    return "growth"


def _topic_meta_from_spec(spec: dict[str, Any], company_ids: list[str]) -> dict[str, Any]:
    category = spec["category"]
    defaults = CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["Programming Languages"])
    base = float(spec["base"])
    growth = float(spec["growth"])
    volatility = float(spec["volatility"])
    sentiment = float(spec["sentiment"])
    lifecycle = _topic_lifecycle(str(spec["name"]), growth, spec.get("maturity"))
    innovation_bias = 8 if lifecycle == "emerging" else -8 if lifecycle in {"declining", "obsolete"} else 0
    adoption_bias = 15 if lifecycle == "mature" else -12 if lifecycle == "emerging" else -10 if lifecycle in {"declining", "obsolete"} else 0
    innovation = spec.get("innovation", np.clip(58 + growth * 1.45 + volatility * 0.6 + innovation_bias, 18, 96))
    adoption = spec.get("adoption", np.clip(base + adoption_bias + growth * 0.35, 5, 92))
    github = spec.get("github", defaults["github"] * (1.18 if lifecycle == "emerging" else 0.72 if lifecycle in {"declining", "obsolete"} else 1.0))
    funding = spec.get("funding", defaults["funding"] * (1.22 if lifecycle == "emerging" else 0.52 if lifecycle in {"declining", "obsolete"} else 1.0))
    salary_factor = float(np.clip(1.0 + growth * 0.008 + (float(innovation) - 70) * 0.003, 0.72, 1.28))
    if lifecycle == "legacy":
        salary_factor = max(salary_factor, 0.92)
    return {
        "base": base,
        "growth": growth,
        "volatility": volatility,
        "weekend_social": spec.get("weekend_social", defaults["weekend_social"]),
        "weekend_hiring": spec.get("weekend_hiring", defaults["weekend_hiring"]),
        "sentiment": sentiment,
        "innovation": float(innovation),
        "adoption": float(adoption),
        "github": float(github),
        "funding": float(funding),
        "companies": company_ids,
        "category": category,
        "lifecycle": lifecycle,
        "salary_factor": salary_factor,
    }


def _company_ids_for_topic(topic: str, category: str) -> list[str]:
    direct_ids = [
        c["company_id"]
        for c in COMPANIES
        if topic in c.get("topics", [])
    ]
    category_ids = [
        c["company_id"]
        for c in COMPANIES
        if category in c.get("topics", []) or c.get("sector", "").lower().find(category.split()[0].lower()) >= 0
    ]
    ids = []
    for company_id in direct_ids + category_ids:
        if company_id not in ids:
            ids.append(company_id)
    if len(ids) < 3:
        fallback = [c["company_id"] for c in COMPANIES if c["reference_type"] in {"synthetic_company", "real_reference"}]
        ids.extend([company_id for company_id in fallback if company_id not in ids][: 5 - len(ids)])
    return ids[:8]


def _roles_for_topic(topic: str, category: str, lifecycle: str) -> list[str]:
    if topic in ROLE_LIBRARY:
        return ROLE_LIBRARY[topic]
    templates = CATEGORY_ROLE_TEMPLATES.get(category, CATEGORY_ROLE_TEMPLATES["Programming Languages"])
    roles = [template.format(topic=topic) for template in templates]
    if lifecycle in {"declining", "legacy", "obsolete"}:
        roles.append(f"{topic} Legacy Migration Specialist")
    return roles[:4]


def _skills_for_topic(topic: str, category: str, explicit: list[str] | None = None) -> list[str]:
    if topic in TOPIC_SKILLS:
        return TOPIC_SKILLS[topic]
    skills = list(explicit or [])
    for skill in CATEGORY_SKILL_DEFAULTS.get(category, []):
        if skill not in skills:
            skills.append(skill)
    if topic not in skills and len(skills) < 6:
        skills.insert(0, topic)
    return skills[:7]


def bootstrap_market_catalog() -> None:
    global COMPANY_BY_ID
    for topic, meta in TOPICS.items():
        category = ORIGINAL_TOPIC_CATEGORIES.get(topic, "Emerging Technologies")
        meta.setdefault("category", category)
        meta.setdefault("lifecycle", _topic_lifecycle(topic, float(meta.get("growth", 0))))
        meta.setdefault("salary_factor", float(np.clip(1.0 + float(meta.get("growth", 0)) * 0.006, 0.78, 1.24)))

    topic_names = _topic_names_from_specs()
    for company in REAL_COMPANY_EXPANSIONS:
        _ensure_company(
            company=company["company"],
            country=company["country"],
            sector=company["sector"],
            stage=company["stage"],
            reference_type=company["reference_type"],
            topics=[t for t in company["topics"] if t in topic_names or t in TOPICS],
        )

    topics_by_category: dict[str, list[str]] = {}
    for spec in EXPANDED_TOPIC_SPECS:
        topics_by_category.setdefault(spec["category"], []).append(spec["name"])
    for idx, (company, country, sector, stage, category) in enumerate(SYNTHETIC_COMPANY_BLUEPRINTS):
        category_topics = topics_by_category.get(category, [])
        assigned = category_topics[idx % max(len(category_topics), 1):] + category_topics[: idx % max(len(category_topics), 1)]
        _ensure_company(
            company=company,
            country=country,
            sector=sector,
            stage=stage,
            reference_type="synthetic_company",
            topics=(assigned[:4] + [category]) if assigned else ([category] if category in topic_names else []),
        )

    for spec in EXPANDED_TOPIC_SPECS:
        name = spec["name"]
        category = spec["category"]
        company_ids = _company_ids_for_topic(name, category)
        if name not in TOPICS:
            TOPICS[name] = _topic_meta_from_spec(spec, company_ids)
        else:
            TOPICS[name].setdefault("category", category)
            TOPICS[name].setdefault("lifecycle", _topic_lifecycle(name, float(TOPICS[name].get("growth", 0))))
            TOPICS[name].setdefault("salary_factor", 1.0)
        lifecycle = TOPICS[name].get("lifecycle", _topic_lifecycle(name, float(TOPICS[name].get("growth", 0))))
        ROLE_LIBRARY[name] = _roles_for_topic(name, category, str(lifecycle))
        TOPIC_SKILLS[name] = _skills_for_topic(name, category, spec.get("skills"))

    for company in COMPANIES:
        company["topics"] = sorted(set(t for t in company.get("topics", []) if t in TOPICS))
    COMPANY_BY_ID = {c["company_id"]: c for c in COMPANIES}

    MARKET_CONTEXT_ADJUSTMENTS.update(
        {
            "Python": {"growth": 1.04, "github": 1.05},
            "Rust": {"growth": 1.08, "github": 1.12, "funding": 1.05},
            "Go": {"growth": 1.05, "github": 1.05},
            "TypeScript": {"growth": 1.04, "github": 1.08},
            "Next.js": {"growth": 1.08, "funding": 1.05},
            "FastAPI": {"growth": 1.06, "github": 1.08},
            "DuckDB": {"growth": 1.12, "github": 1.1},
            "Pinecone": {"growth": 1.1, "funding": 1.08},
            "PHP": {"growth": 1.05, "funding": 0.92, "github": 0.9},
            "Perl": {"growth": 1.06, "github": 0.88},
            "COBOL": {"growth": 1.02, "funding": 0.85},
            "jQuery": {"growth": 1.06, "github": 0.82},
            "Flash": {"growth": 1.08, "github": 0.5, "funding": 0.45},
            "Zero-Trust Security": {"growth": 1.1, "funding": 1.08},
            "WebAssembly": {"growth": 1.1, "github": 1.1},
            "Quantum Computing": {"growth": 1.12, "volatility": 1.12},
            "Low-Code/No-Code": {"growth": 1.08, "funding": 1.08},
        }
    )

    existing_event_ids = {event["event_id"] for event in EVENTS}
    expanded_events = [
        {"event_id": "EVT-014", "date": "2025-02-05", "window": 12, "title": "Python 3.12 adoption accelerates data and AI platform modernization", "topics": {"Python": 10, "FastAPI": 6, "Pytest": 4}, "sentiment": 0.05},
        {"event_id": "EVT-015", "date": "2025-02-18", "window": 12, "title": "Java 21 long-term support upgrades drive enterprise JVM refresh cycles", "topics": {"Java": 5, "Spring Boot": 5, "Kotlin": 2}, "sentiment": 0.03},
        {"event_id": "EVT-016", "date": "2025-03-04", "window": 14, "title": "Next.js app-router and React server component adoption moves into mainstream teams", "topics": {"Next.js": 12, "React": 7, "Vercel": 4 if "Vercel" in TOPICS else 0}, "sentiment": 0.06},
        {"event_id": "EVT-017", "date": "2025-03-26", "window": 10, "title": "Vite and Vitest migration wave pressures legacy Webpack-era stacks", "topics": {"Vitest": 10, "React": 4, "Vue.js": 4, "Angular": -3}, "sentiment": 0.04},
        {"event_id": "EVT-018", "date": "2025-04-15", "window": 16, "title": "Flash and jQuery remediation programs continue after browser and security policy changes", "topics": {"Flash": -12, "jQuery": -8, "HTML5": 5, "Accessibility": 4}, "sentiment": -0.08},
        {"event_id": "EVT-019", "date": "2025-05-09", "window": 12, "title": "Go runtime and Kubernetes ecosystem improvements lift cloud-native backend demand", "topics": {"Go": 9, "Kubernetes": 7, "Docker": 3, "gRPC": 4}, "sentiment": 0.05},
        {"event_id": "EVT-020", "date": "2025-05-22", "window": 14, "title": "Rust production safety wins boost adoption in infrastructure and AI serving", "topics": {"Rust": 12, "WebAssembly": 7, "Inference Optimization": 5}, "sentiment": 0.06},
        {"event_id": "EVT-021", "date": "2025-06-17", "window": 12, "title": "Major package vulnerability increases demand for dependency scanning and OWASP practices", "topics": {"OWASP Security": 10, "Zero-Trust Security": 5, "GitHub Actions": 3, "Cybersecurity": 8}, "sentiment": -0.05},
        {"event_id": "EVT-022", "date": "2025-07-02", "window": 12, "title": "Flutter adoption expands across Asia-Pacific fintech and commerce apps", "topics": {"Flutter": 10, "Dart": 6, "Kotlin Android": 3, "React Native": 2}, "sentiment": 0.05},
        {"event_id": "EVT-023", "date": "2025-07-25", "window": 10, "title": "Enterprise PHP and Ruby workloads shift toward modernization and migration budgets", "topics": {"PHP": -6, "Ruby": -5, "Laravel": -3, "RubyOnRails": -4, "FastAPI": 3, "Spring Boot": 3}, "sentiment": -0.04},
        {"event_id": "EVT-024", "date": "2025-08-20", "window": 14, "title": "DuckDB and Polars gain momentum in local analytics and notebook workflows", "topics": {"DuckDB": 12, "Polars": 10, "Pandas": 4, "Data Science": 4}, "sentiment": 0.06},
        {"event_id": "EVT-025", "date": "2025-09-03", "window": 12, "title": "OpenAPI and API-first governance become standard in platform engineering programs", "topics": {"OpenAPI/Swagger": 8, "API-First Development": 9, "REST APIs": 2, "GraphQL": 4}, "sentiment": 0.04},
        {"event_id": "EVT-026", "date": "2025-09-27", "window": 14, "title": "Zero-trust identity rollout wave follows new supply-chain security guidance", "topics": {"Zero-Trust Security": 12, "OAuth 2.0 / OpenID Connect": 5, "SAML": 2, "Vault": 5}, "sentiment": 0.03},
        {"event_id": "EVT-027", "date": "2025-10-14", "window": 12, "title": "Kafka alternatives and edge messaging renew interest in NATS and Pulsar", "topics": {"NATS": 9, "Apache Pulsar": 7, "Apache Kafka": 4, "RabbitMQ": 1}, "sentiment": 0.04},
        {"event_id": "EVT-028", "date": "2025-11-06", "window": 16, "title": "Figma and design-system automation increase frontend platform investment", "topics": {"Figma": 11, "Storybook": 6, "Tailwind CSS": 5, "Chakra UI": 3}, "sentiment": 0.07},
        {"event_id": "EVT-029", "date": "2025-12-02", "window": 16, "title": "Mainframe modernization budgets rise but COBOL hiring remains replacement-driven", "topics": {"COBOL": -4, "Mainframe COBOL": -2, "Java": 2, "C# / .NET": 2}, "sentiment": -0.02},
        {"event_id": "EVT-030", "date": "2026-01-08", "window": 16, "title": "Serverless and edge platforms converge around lower-latency application delivery", "topics": {"Serverless Architecture": 8, "Edge Computing": 10, "Cloudflare" if "Cloudflare" in TOPICS else "Cloud Computing": 4}, "sentiment": 0.05},
        {"event_id": "EVT-031", "date": "2026-02-05", "window": 14, "title": "WebAssembly component tooling matures for browser, server, and plugin runtimes", "topics": {"WebAssembly": 14, "Rust": 5, "Blazor": 3}, "sentiment": 0.06},
        {"event_id": "EVT-032", "date": "2026-03-10", "window": 18, "title": "Low-code automation platforms see enterprise governance adoption", "topics": {"Low-Code/No-Code": 11, "Automation": 6, "API-First Development": 4}, "sentiment": 0.05},
        {"event_id": "EVT-033", "date": "2026-04-02", "window": 16, "title": "Quantum developer conferences lift experimental searches without broad hiring conversion", "topics": {"Quantum Computing": 12, "Python": 2, "Julia": 3}, "sentiment": 0.04},
    ]
    for event in expanded_events:
        event["topics"] = {topic: impact for topic, impact in event["topics"].items() if topic in TOPICS and impact != 0}
        if event["event_id"] not in existing_event_ids and event["topics"]:
            EVENTS.append(event)


bootstrap_market_catalog()

RISK_LABELS = ["low", "moderate", "elevated", "high"]


@dataclass
class TopicDay:
    date: pd.Timestamp
    topic: str
    country_code: str
    trend_score: float
    popularity_growth_pct: float
    volatility_metric: float
    sentiment_score: float
    innovation_score: float
    adoption_score: float
    risk_indicator: str
    event_refs: str
    package_downloads_weekly: int
    github_activity_index: float
    stackoverflow_question_volume: int
    job_market_demand_index: float
    education_enrollment_index: float
    conference_talks: int
    documentation_health_score: float
    community_health_score: float


def ensure_dirs() -> None:
    for path in [DATA_DIR, MARKET_DIR, IMPORT_DIR, API_SAMPLES_DIR, JSON_SAMPLES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def apply_market_context_adjustments() -> None:
    """Bias the synthetic generator with documented 2025-2026 market signals."""
    global _MARKET_CONTEXT_APPLIED
    if _MARKET_CONTEXT_APPLIED:
        return
    for topic, adjustments in MARKET_CONTEXT_ADJUSTMENTS.items():
        if topic not in TOPICS:
            continue
        for field, multiplier in adjustments.items():
            if field in TOPICS[topic]:
                TOPICS[topic][field] = round(float(TOPICS[topic][field]) * float(multiplier), 4)
    _MARKET_CONTEXT_APPLIED = True


def write_market_context() -> None:
    context = {
        "version": MARKET_CONTEXT_VERSION,
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "sources": MARKET_CONTEXT_SOURCES,
        "topic_adjustments": MARKET_CONTEXT_ADJUSTMENTS,
        "note": "Synthetic data only; weights are anchored to public market signals and then randomized for local analytics and ML demos.",
    }
    (MARKET_DIR / "market_context_2026.json").write_text(json.dumps(context, indent=2), encoding="utf-8")


def slugify(text: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "-" for ch in str(text)]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "topic"


def topic_hashtag(topic: str) -> str:
    compact = "".join(ch for ch in str(topic).title() if ch.isalnum())
    return f"#{compact or 'TechTrend'}"


def infer_topic_language(topic: str) -> str:
    skills = {str(skill).lower() for skill in TOPIC_SKILLS.get(topic, [])}
    lowered = topic.lower()
    if "rust" in lowered or "rust" in skills:
        return "Rust"
    if "go" == lowered or "golang" in skills or "go" in skills:
        return "Go"
    if "java" in lowered or "spring boot" in lowered or "java" in skills:
        return "Java"
    if "c#" in lowered or ".net" in lowered or "asp.net" in lowered or "c#" in skills:
        return "C#"
    if "c++" in lowered or "cuda" in skills:
        return "C++"
    if "swift" in lowered:
        return "Swift"
    if "kotlin" in lowered:
        return "Kotlin"
    if "php" in lowered or "wordpress" in lowered or "laravel" in lowered:
        return "PHP"
    if "ruby" in lowered or "rails" in lowered:
        return "Ruby"
    if "type" in lowered or "react" in lowered or "vue" in lowered or "angular" in lowered or "javascript" in skills:
        return "TypeScript"
    if "sql" in lowered or "database" in lowered:
        return "SQL"
    if "python" in lowered or "python" in skills:
        return "Python"
    return "TypeScript"


def is_declining_topic(topic: str) -> bool:
    meta = TOPICS.get(topic, {})
    return topic in DECLINING_TECHNOLOGIES or meta.get("lifecycle") in {"declining", "legacy", "obsolete"} or float(meta.get("growth", 0)) < 0


def is_emerging_topic(topic: str) -> bool:
    meta = TOPICS.get(topic, {})
    return topic in EMERGING_TECHNOLOGIES or meta.get("lifecycle") == "emerging" or float(meta.get("growth", 0)) >= 10


def weighted_choice(items: list[str], weights: list[float]) -> str:
    probs = np.asarray(weights, dtype=float)
    probs = probs / probs.sum()
    return items[int(RNG.choice(len(items), p=probs))]


def maybe_missing(value: Any, probability: float) -> Any:
    return None if RNG.random() < probability else value


def weekend_factor(date: pd.Timestamp, social: float = 0.8, hiring: float = 0.58) -> tuple[float, float]:
    if date.dayofweek >= 5:
        return social, hiring
    return 1.0, 1.0


def event_effects(date: pd.Timestamp, topic: str) -> tuple[float, float, list[str]]:
    boost = 0.0
    sentiment = 0.0
    refs: list[str] = []
    for event in EVENTS:
        center = pd.Timestamp(event["date"])
        days = abs((date - center).days)
        if days > event["window"]:
            continue
        topic_boost = event["topics"].get(topic, 0.0)
        if topic_boost == 0:
            continue
        distance_weight = np.exp(-(days**2) / max(event["window"], 1) ** 2)
        boost += topic_boost * distance_weight
        sentiment += event["sentiment"] * distance_weight
        refs.append(event["event_id"])
    return boost, sentiment, refs


def region_multiplier(topic: str, country_code: str) -> float:
    country = COUNTRY_BY_CODE[country_code]
    meta = TOPICS.get(topic, {})
    category = meta.get("category")
    bias = 1.0
    if topic in {"AI Agents", "LLM", "Enterprise AI"} and country_code in {"US", "UK", "SG"}:
        bias += 0.12
    if topic in {"Data Engineering", "Developer Tools"} and country_code in {"IN", "US"}:
        bias += 0.1
    if topic in {"Cybersecurity"} and country_code in {"US", "UK", "DE"}:
        bias += 0.09
    if topic in {"Robotics", "Semiconductors", "Edge AI"} and country_code in {"JP", "CN"}:
        bias += 0.14
    if topic in {"Web3"} and country_code in {"AE", "SG"}:
        bias += 0.16
    if topic in {"Cloud Computing"} and country_code in {"US", "IN"}:
        bias += 0.05
    if topic in {"Rust", "Go", "WebAssembly"} and country_code in {"US", "DE", "CA"}:
        bias += 0.09
    if topic in {"PHP", "Laravel", "WordPress"} and country_code in {"IN", "FR", "AE"}:
        bias += 0.06
    if topic in {"COBOL", "Mainframe COBOL", "Java", "Oracle Database"} and country_code in {"US", "UK", "JP"}:
        bias += 0.08
    if category == "Mobile Development" and country_code in {"IN", "SG", "JP"}:
        bias += 0.1
    if category == "Security & Compliance" and country_code in {"US", "UK", "DE", "AE"}:
        bias += 0.08
    if category == "UI/UX & Design" and country_code in {"US", "UK", "CA"}:
        bias += 0.07
    if category == "Cloud & Infrastructure" and country_code in {"US", "IN", "SG"}:
        bias += 0.06
    return bias * country["social"]


def topic_curve() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    n_days = len(DATES)
    phase_offsets = {topic: i / max(len(TOPICS), 1) * np.pi for i, topic in enumerate(TOPICS)}
    for topic, meta in TOPICS.items():
        base = meta["base"]
        growth = meta["growth"]
        vol = meta["volatility"]
        innovation = meta["innovation"]
        adoption = meta["adoption"]
        lifecycle = meta.get("lifecycle", "growth")
        prev_scores: dict[str, float] = {}
        for idx, date in enumerate(DATES):
            progress = idx / max(n_days - 1, 1)
            slow_growth = growth * progress
            seasonal = 2.5 * np.sin(2 * np.pi * progress * 4 + phase_offsets[topic])
            weekly = 1.2 * np.sin(2 * np.pi * (date.dayofweek / 7))
            event_boost, event_sentiment, refs = event_effects(date, topic)
            for country in COUNTRIES:
                region_mult = region_multiplier(topic, country["code"])
                noise = RNG.normal(0, vol / 4)
                score = base + slow_growth + seasonal + weekly + event_boost + noise
                score *= region_mult / country["social"]
                min_score = 1 if lifecycle == "obsolete" else 3 if is_declining_topic(topic) else 8
                score = float(np.clip(score, min_score, 100))
                prev = prev_scores.get(country["code"], score - RNG.uniform(0.2, 2.0))
                growth_pct = float(np.clip(((score - prev) / max(prev, 1)) * 100, -45, 65))
                prev_scores[country["code"]] = score
                volatility_metric = float(np.clip(abs(noise) * 1.8 + abs(growth_pct) * 0.22 + vol, 2, 42))
                sentiment = meta["sentiment"] + event_sentiment + RNG.normal(0, 0.12)
                if topic == "Web3":
                    sentiment -= abs(RNG.normal(0.05, 0.06))
                if is_declining_topic(topic):
                    sentiment -= abs(RNG.normal(0.03, 0.04))
                risk_raw = volatility_metric + (15 if topic == "Cybersecurity" and event_sentiment < 0 else 0)
                if lifecycle in {"declining", "legacy", "obsolete"}:
                    risk_raw += 4
                risk = "low" if risk_raw < 9 else "moderate" if risk_raw < 16 else "elevated" if risk_raw < 24 else "high"
                package_multiplier = 1.35 if meta.get("category") in {"Web & Frontend Frameworks", "Backend & API Frameworks", "Programming Languages", "Data Science"} else 0.7
                if lifecycle in {"declining", "legacy", "obsolete"}:
                    package_multiplier *= 0.62
                package_downloads = int(max(50, score * adoption * package_multiplier * RNG.uniform(700, 1600)))
                github_activity_index = float(np.clip(score * meta["github"] * (1.15 if is_emerging_topic(topic) else 0.72 if is_declining_topic(topic) else 1.0), 1, 140))
                stackoverflow_volume = int(max(0, score * (0.9 if meta.get("category") in {"Programming Languages", "Backend & API Frameworks", "Web & Frontend Frameworks", "Testing & QA"} else 0.45) + RNG.normal(0, 12)))
                job_demand = float(np.clip(score * 0.72 + adoption * 0.42 + growth * 0.9, 1, 130))
                if lifecycle in {"declining", "obsolete"}:
                    job_demand *= 0.72
                education_index = float(np.clip(score * 0.55 + max(growth, -6) * 1.3 + innovation * 0.25, 1, 110))
                conference_talks = int(max(0, RNG.normal(score / 8 + max(growth, 0) * 0.35, 2)))
                documentation_health = float(np.clip(45 + adoption * 0.35 + meta["github"] * 12 + RNG.normal(0, 6), 10, 100))
                community_health = float(np.clip(35 + github_activity_index * 0.33 + stackoverflow_volume * 0.08 + sentiment * 18 + RNG.normal(0, 5), 5, 100))
                rows.append(
                    TopicDay(
                        date=date,
                        topic=topic,
                        country_code=country["code"],
                        trend_score=round(score, 2),
                        popularity_growth_pct=round(growth_pct, 2),
                        volatility_metric=round(volatility_metric, 2),
                        sentiment_score=round(float(np.clip(sentiment, -1, 1)), 3),
                        innovation_score=round(float(np.clip(innovation + event_boost * 0.2 + RNG.normal(0, 2.5), 40, 100)), 2),
                        adoption_score=round(float(np.clip(adoption + slow_growth * 0.45 + event_boost * 0.18 + RNG.normal(0, 3), 5 if is_declining_topic(topic) else 25, 100)), 2),
                        risk_indicator=risk,
                        event_refs="|".join(refs),
                        package_downloads_weekly=package_downloads,
                        github_activity_index=round(github_activity_index, 2),
                        stackoverflow_question_volume=stackoverflow_volume,
                        job_market_demand_index=round(job_demand, 2),
                        education_enrollment_index=round(education_index, 2),
                        conference_talks=conference_talks,
                        documentation_health_score=round(documentation_health, 2),
                        community_health_score=round(community_health, 2),
                    ).__dict__
                )
    return pd.DataFrame(rows)


def company_daily_signals(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for company in COMPANIES:
        topic_slice = topic_df[
            (topic_df["topic"].isin(company["topics"]))
            & (topic_df["country_code"] == company["country"])
        ]
        grouped = (
            topic_slice.groupby("date")
            .agg(
                trend_score=("trend_score", "mean"),
                popularity_growth_pct=("popularity_growth_pct", "mean"),
                sentiment_score=("sentiment_score", "mean"),
                volatility_metric=("volatility_metric", "mean"),
                innovation_score=("innovation_score", "mean"),
                adoption_score=("adoption_score", "mean"),
                package_downloads_weekly=("package_downloads_weekly", "mean"),
                github_activity_index=("github_activity_index", "mean"),
                stackoverflow_question_volume=("stackoverflow_question_volume", "mean"),
                job_market_demand_index=("job_market_demand_index", "mean"),
                education_enrollment_index=("education_enrollment_index", "mean"),
                conference_talks=("conference_talks", "mean"),
                documentation_health_score=("documentation_health_score", "mean"),
                community_health_score=("community_health_score", "mean"),
            )
            .reset_index()
        )
        for rec in grouped.to_dict("records"):
            funding_factor = 1.0 + (0.18 if company["stage"] in {"seed", "series_a"} else 0.12 if company["stage"] == "series_b" else 0.05)
            if company["company"] in {"NVIDIA", "CoreWeave"}:
                funding_factor += 0.12
            if company["company"] in {"OpenAI", "Anthropic", "Databricks", "Snowflake"}:
                funding_factor += 0.08
            hiring_index = max(8, rec["trend_score"] * 0.85 + rec["adoption_score"] * 0.35 + RNG.normal(0, 4))
            rows.append(
                {
                    "date": rec["date"],
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country_code": company["country"],
                    "trend_score": round(rec["trend_score"], 2),
                    "popularity_growth_pct": round(rec["popularity_growth_pct"], 2),
                    "sentiment_score": round(rec["sentiment_score"], 3),
                    "volatility_metric": round(rec["volatility_metric"], 2),
                    "innovation_score": round(rec["innovation_score"], 2),
                    "adoption_score": round(rec["adoption_score"], 2),
                    "hiring_index": round(float(hiring_index), 2),
                    "funding_factor": round(float(funding_factor), 2),
                    "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0) or 0),
                    "github_activity_index": round(float(rec.get("github_activity_index", 0) or 0), 2),
                    "stackoverflow_question_volume": int(rec.get("stackoverflow_question_volume", 0) or 0),
                    "job_market_demand_index": round(float(rec.get("job_market_demand_index", hiring_index) or hiring_index), 2),
                    "education_enrollment_index": round(float(rec.get("education_enrollment_index", 0) or 0), 2),
                    "conference_talks": int(rec.get("conference_talks", 0) or 0),
                    "documentation_health_score": round(float(rec.get("documentation_health_score", 0) or 0), 2),
                    "community_health_score": round(float(rec.get("community_health_score", 0) or 0), 2),
                }
            )
    return pd.DataFrame(rows)


def build_companies_dimension() -> pd.DataFrame:
    rows = []
    for company in COMPANIES:
        country = COUNTRY_BY_CODE[company["country"]]
        rows.append(
            {
                "company_id": company["company_id"],
                "company": company["company"],
                "country": country["country"],
                "country_code": company["country"],
                "region": country["region"],
                "sector": company["sector"],
                "stage": company["stage"],
                "reference_type": company["reference_type"],
                "dominant_topics": ", ".join(company["topics"]),
            }
        )
    return pd.DataFrame(rows)


def build_events_dimension() -> pd.DataFrame:
    rows = []
    for event in EVENTS:
        rows.append(
            {
                "event_id": event["event_id"],
                "event_date": event["date"],
                "window_days": event["window"],
                "title": event["title"],
                "topic_impacts": json.dumps(event["topics"]),
                "sentiment_shift": event["sentiment"],
            }
        )
    return pd.DataFrame(rows)


def choose_company_for_topic(topic: str) -> dict[str, Any]:
    company_ids = TOPICS[topic]["companies"]
    weights = []
    for company_id in company_ids:
        company = COMPANY_BY_ID[company_id]
        base = 1.0
        if company["reference_type"] == "real_reference":
            base += 0.7
        if company["stage"] == "public":
            base += 0.3
        if company["company"] in {"NVIDIA", "OpenAI", "Anthropic", "Microsoft"}:
            base += 0.5
        weights.append(base)
    chosen = weighted_choice(company_ids, weights)
    return COMPANY_BY_ID[chosen]


def generate_user_name() -> str:
    prefixes = ["agent", "data", "cloud", "model", "infra", "secure", "vector", "gpu", "founder", "ml"]
    suffix = str(int(RNG.integers(100, 99999)))
    return f"{weighted_choice(prefixes, [1] * len(prefixes))}_{suffix}"


def sentence_case_summary(topic: str, company: str, date: pd.Timestamp, mood: str) -> str:
    trends = [
        f"{company} teams are discussing how {topic.lower()} is moving from experimentation into production buying cycles.",
        f"Developers are comparing tooling choices around {topic.lower()} as budget owners ask for faster ROI and clearer governance.",
        f"Analysts note that {topic.lower()} usage patterns on {date.strftime('%b %d, %Y')} reflect both hype and practical deployment pressure.",
    ]
    risks = {
        "positive": "Demand remains healthy, but platform differentiation now depends on reliability, cost control, and measurable adoption.",
        "neutral": "The conversation is active, though buyers continue to separate pilot noise from repeatable production value.",
        "negative": "Interest is still present, but reliability, cost, and security concerns are slowing near-term expansion for some teams.",
    }
    return f"{RNG.choice(trends)} {risks[mood]}"


def build_linkedin_jobs(company_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    job_id = 100000
    for rec in company_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        company = COMPANY_BY_ID[rec["company_id"]]
        country = COUNTRY_BY_CODE[company["country"]]
        social_wknd, hiring_wknd = weekend_factor(date)
        day_hiring = rec["hiring_index"] * country["hiring"] * hiring_wknd / 22
        count = int(max(0, RNG.poisson(day_hiring / 2.1) * max(1.0, SCALE)))
        for _ in range(count):
            primary_topic = weighted_choice(company["topics"], [TOPICS[t]["adoption"] for t in company["topics"]])
            role = weighted_choice(ROLE_LIBRARY[primary_topic], [1] * len(ROLE_LIBRARY[primary_topic]))
            years = int(np.clip(RNG.normal(4.5 if "Engineer" in role else 6.0, 2.0), 1, 12))
            topic_meta = TOPICS[primary_topic]
            salary_base = (
                72000
                + topic_meta["innovation"] * 620
                + topic_meta["adoption"] * 180
                + years * 5200
            ) * float(topic_meta.get("salary_factor", 1.0))
            geo_multiplier = {
                "US": 1.0, "UK": 0.78, "DE": 0.8, "CA": 0.82, "IN": 0.34, "SG": 0.7, "AE": 0.68, "JP": 0.76, "CN": 0.58, "FR": 0.74
            }[company["country"]]
            salary = int(np.clip(RNG.normal(salary_base * geo_multiplier, 12000), 28000, 340000))
            skills = RNG.choice(TOPIC_SKILLS[primary_topic], size=min(5, len(TOPIC_SKILLS[primary_topic])), replace=False)
            city = weighted_choice(country["cities"], [1] * len(country["cities"]))
            risk = "high" if primary_topic in {"Cybersecurity", "Web3"} and rec["volatility_metric"] > 18 else "moderate" if rec["volatility_metric"] > 12 else "low"
            desc = (
                f"{company['company']} is hiring a {role} in {city} to scale {primary_topic.lower()} initiatives across enterprise and developer workflows. "
                f"The team is focused on {weighted_choice(['cost-efficient inference', 'agent reliability', 'secure deployment', 'data platform integration', 'global availability'], [1,1,1,1,1])} "
                f"while supporting {weighted_choice(['production customers', 'open-source contributors', 'internal platform teams', 'regional go-to-market launches'], [1,1,1,1])}. "
                f"Candidates should be comfortable with {', '.join(skills[:3])} and cross-functional delivery in a fast-moving market."
            )
            rows.append(
                {
                    "job_id": f"JOB-{job_id}",
                    "posted_at": (date + pd.Timedelta(hours=int(RNG.integers(8, 22)))).isoformat(),
                    "company": company["company"],
                    "role": role,
                    "location": city,
                    "salary_usd": salary,
                    "experience_years": years,
                    "skills": ", ".join(skills.tolist()),
                    "job_description": desc,
                    "company_id": company["company_id"],
                    "country": country["country"],
                    "region": country["region"],
                    "tech_category": primary_topic,
                    "hiring_index": round(rec["hiring_index"], 2),
                    "funding_signal": round(rec["funding_factor"], 2),
                    "sentiment_score": round(rec["sentiment_score"], 3),
                    "trend_score": round(rec["trend_score"], 2),
                    "popularity_growth_pct": round(rec["popularity_growth_pct"], 2),
                    "volatility_metric": round(rec["volatility_metric"], 2),
                    "innovation_score": round(rec["innovation_score"], 2),
                    "adoption_score": round(rec["adoption_score"], 2),
                    "risk_indicator": risk,
                    "job_market_demand_index": round(float(rec.get("job_market_demand_index", rec["hiring_index"])), 2),
                    "education_enrollment_index": round(float(rec.get("education_enrollment_index", 0)), 2),
                    "community_health_score": round(float(rec.get("community_health_score", 0)), 2),
                    "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0)),
                    "source_platform": "LinkedIn",
                }
            )
            job_id += 1
    df = pd.DataFrame(rows)
    if not df.empty:
        miss_idx = df.sample(frac=0.015, random_state=SEED).index
        df.loc[miss_idx, "salary_usd"] = np.nan
    return df


def build_twitter_stream(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    tweet_id = 200000
    cached_duplicates: list[dict[str, Any]] = []
    hashtag_map = {
        "AI Agents": "#AIAgents",
        "LLM": "#LLM",
        "Generative AI": "#GenAI",
        "Cybersecurity": "#Cybersecurity",
        "Cloud Computing": "#Cloud",
        "DevOps": "#DevOps",
        "Edge AI": "#EdgeAI",
        "Robotics": "#Robotics",
        "Web3": "#Web3",
        "Semiconductors": "#Semiconductors",
        "SaaS": "#SaaS",
        "Data Engineering": "#DataEngineering",
        "Automation": "#Automation",
        "MLOps": "#MLOps",
        "Open Source AI": "#OpenSourceAI",
        "GPU Infrastructure": "#GPU",
        "Developer Tools": "#DevTools",
        "Vector Databases": "#VectorDB",
        "Inference Optimization": "#Inference",
        "Enterprise AI": "#EnterpriseAI",
    }
    for rec in topic_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        country = COUNTRY_BY_CODE[rec["country_code"]]
        social_wknd, _ = weekend_factor(date, social=TOPICS[rec["topic"]]["weekend_social"])
        intensity = rec["trend_score"] * country["social"] * social_wknd / 130
        count = int(max(0, RNG.poisson(intensity) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            hashtag = hashtag_map.get(rec["topic"], topic_hashtag(rec["topic"]))
            followers = int(np.clip(RNG.lognormal(mean=9.6, sigma=0.9), 150, 420000))
            sentiment_num = float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.23), -1, 1))
            sentiment = "positive" if sentiment_num > 0.18 else "negative" if sentiment_num < -0.16 else "neutral"
            likes = int(max(0, RNG.normal(rec["trend_score"] * 55 + followers * 0.018, 220)))
            retweets = int(max(0, RNG.normal(likes * RNG.uniform(0.18, 0.42), 90)))
            timestamp = date + pd.Timedelta(hours=int(RNG.integers(0, 24)), minutes=int(RNG.integers(0, 60)))
            content = (
                f"{company['company']} keeps showing up in {rec['topic']} discussions as teams focus on "
                f"{weighted_choice(['cost-efficient deployment', 'agent quality', 'governance', 'GPU capacity', 'developer adoption'], [1,1,1,1,1])}. "
                f"{hashtag} #{rec['country_code']} #{slugify(company['company']).replace('-', '')}"
            )
            if rec["risk_indicator"] in {"elevated", "high"} and rec["topic"] in {"Cybersecurity", "Web3"}:
                content = (
                    f"Watching {rec['topic']} sentiment turn choppy after new risk headlines. "
                    f"{company['company']} is still getting attention, but operators are asking harder questions on resilience and trust. "
                    f"{hashtag} #{rec['country_code']}"
                )
            row = {
                "tweet_id": f"TWT-{tweet_id}",
                "created_at": timestamp.isoformat(),
                "username": generate_user_name(),
                "followers": followers,
                "tech_topic": rec["topic"],
                "sentiment": maybe_missing(sentiment, 0.012),
                "likes": likes,
                "retweets": retweets,
                "content": content,
                "company_id": company["company_id"],
                "company": company["company"],
                "country": country["country"],
                "region": country["region"],
                "trend_score": round(rec["trend_score"], 2),
                "sentiment_score": round(sentiment_num, 3),
                "funding_estimate_musd": round(float(rec["adoption_score"] * 2.2 + TOPICS[rec["topic"]]["funding"] * 18 + RNG.normal(0, 8)), 2),
                "hiring_activity_index": round(float(rec["adoption_score"] * 0.8 + RNG.normal(0, 5)), 2),
                "hashtags": f"{hashtag}|#{rec['country_code']}|#{slugify(company['company']).replace('-', '')}",
                "popularity_growth_pct": rec["popularity_growth_pct"],
                "volatility_metric": rec["volatility_metric"],
                "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0)),
                "github_activity_index": rec.get("github_activity_index", 0),
                "stackoverflow_question_volume": int(rec.get("stackoverflow_question_volume", 0)),
                "job_market_demand_index": rec.get("job_market_demand_index", 0),
                "education_enrollment_index": rec.get("education_enrollment_index", 0),
                "conference_talks": int(rec.get("conference_talks", 0)),
                "documentation_health_score": rec.get("documentation_health_score", 0),
                "community_health_score": rec.get("community_health_score", 0),
                "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, sentiment),
                "risk_indicator": rec["risk_indicator"],
                "innovation_score": rec["innovation_score"],
                "adoption_score": rec["adoption_score"],
                "source_reference": f"https://x.example.com/{company['company_id']}/{tweet_id}",
            }
            rows.append(row)
            if RNG.random() < 0.025:
                dup = row.copy()
                dup["tweet_id"] = f"TWT-{tweet_id + 500000}"
                dup["created_at"] = (timestamp + pd.Timedelta(minutes=int(RNG.integers(2, 180)))).isoformat()
                dup["content"] = f"RT {row['username']}: {row['content']}"
                cached_duplicates.append(dup)
            tweet_id += 1
    rows.extend(cached_duplicates)
    return pd.DataFrame(rows)


def build_github_events(company_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    event_id = 300000
    languages = {
        "AI Agents": "Python", "LLM": "Python", "Generative AI": "Python", "Cybersecurity": "Go",
        "Cloud Computing": "Go", "DevOps": "Go", "Edge AI": "C++", "Robotics": "C++",
        "Web3": "Rust", "Semiconductors": "C++", "SaaS": "TypeScript", "Data Engineering": "Python",
        "Automation": "TypeScript", "MLOps": "Python", "Open Source AI": "Python", "GPU Infrastructure": "Python",
        "Developer Tools": "TypeScript", "Vector Databases": "Rust", "Inference Optimization": "C++", "Enterprise AI": "Python",
    }
    event_types = ["push", "pull_request", "release", "issue", "discussion"]
    for rec in company_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        company = COMPANY_BY_ID[rec["company_id"]]
        open_source_weight = 1.25 if "Open Source AI" in company["topics"] or "Developer Tools" in company["topics"] else 1.0
        count = int(max(0, RNG.poisson((rec["trend_score"] / 60) * open_source_weight) * max(1.0, SCALE)))
        for _ in range(count):
            topic = weighted_choice(company["topics"], [TOPICS[t]["github"] for t in company["topics"]])
            event_type = weighted_choice(event_types, [0.42, 0.24, 0.1, 0.14, 0.1])
            stars_added = int(max(0, RNG.normal(rec["trend_score"] * TOPICS[topic]["github"] * 5.2, 75)))
            forks_added = int(max(0, RNG.normal(stars_added * 0.38, 40)))
            contributors = int(max(1, RNG.normal(TOPICS[topic]["github"] * 10 + rec["adoption_score"] * 0.08, 4)))
            repo = f"{slugify(company['company'])}/{slugify(topic)}-{weighted_choice(['platform', 'sdk', 'starter', 'benchmark', 'ops'], [1,1,1,1,1])}"
            rows.append(
                {
                    "event_id": f"GIT-{event_id}",
                    "event_time": date.isoformat(),
                    "repository": repo,
                    "language": languages.get(topic, infer_topic_language(topic)),
                    "stars_added": stars_added,
                    "forks_added": forks_added,
                    "contributors": contributors,
                    "topic": topic,
                    "event_type": event_type,
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "region": COUNTRY_BY_CODE[company["country"]]["region"],
                    "issue_count": int(max(0, RNG.normal(6 + rec["volatility_metric"] * 0.4, 3))),
                    "watchers_added": int(max(0, RNG.normal(stars_added * 0.22, 15))),
                    "release_flag": event_type == "release",
                    "trend_score": round(rec["trend_score"], 2),
                    "popularity_growth_pct": round(rec["popularity_growth_pct"], 2),
                    "volatility_metric": round(rec["volatility_metric"], 2),
                    "innovation_score": round(rec["innovation_score"], 2),
                    "adoption_score": round(rec["adoption_score"], 2),
                    "github_activity_index": round(float(rec.get("github_activity_index", 0)), 2),
                    "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0)),
                    "documentation_health_score": round(float(rec.get("documentation_health_score", 0)), 2),
                    "community_health_score": round(float(rec.get("community_health_score", 0)), 2),
                    "risk_indicator": "elevated" if topic in {"Web3", "Cybersecurity"} and rec["volatility_metric"] > 15 else "low",
                    "ai_summary": sentence_case_summary(topic, company["company"], date, "positive"),
                }
            )
            event_id += 1
    return pd.DataFrame(rows)


def build_tech_blogs(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    article_id = 400000
    for rec in topic_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        country = COUNTRY_BY_CODE[rec["country_code"]]
        count = int(max(0, RNG.poisson(rec["trend_score"] / 750) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            sentiment_bucket = "negative" if rec["sentiment_score"] < -0.1 else "positive" if rec["sentiment_score"] > 0.14 else "neutral"
            title_flavor = weighted_choice(
                ["adoption", "buying signals", "cost pressure", "developer demand", "enterprise rollout", "open-source momentum"],
                [1, 1, 1, 1, 1, 1],
            )
            title = f"{rec['topic']} {title_flavor} in {date.year}: what {company['company']} signals imply"
            views = int(max(2500, RNG.lognormal(mean=10.6, sigma=0.7)))
            rows.append(
                {
                    "article_id": f"ART-{article_id}",
                    "published_at": date.isoformat(),
                    "source": weighted_choice(BLOG_SOURCES, [1] * len(BLOG_SOURCES)),
                    "author": f"{weighted_choice(['Ava', 'Noah', 'Maya', 'Liam', 'Ishaan', 'Priya', 'Sofia', 'Kenji'], [1]*8)} {weighted_choice(['Patel', 'Miller', 'Chen', 'Garcia', 'Wright', 'Tanaka', 'Singh', 'Dubois'], [1]*8)}",
                    "topic": rec["topic"],
                    "title": title,
                    "views": views,
                    "reading_time_minutes": int(np.clip(RNG.normal(8 + rec["volatility_metric"] * 0.18, 3), 4, 18)),
                    "summary": sentence_case_summary(rec["topic"], company["company"], date, sentiment_bucket),
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country": country["country"],
                    "region": country["region"],
                    "trend_score": rec["trend_score"],
                    "sentiment_score": rec["sentiment_score"],
                    "funding_estimate_musd": round(float(TOPICS[rec["topic"]]["funding"] * 22 + RNG.normal(0, 11)), 2),
                    "hiring_activity_index": round(float(TOPICS[rec["topic"]]["adoption"] * 0.84 + RNG.normal(0, 5)), 2),
                    "hashtags": f"#{slugify(rec['topic']).replace('-', '')}|#{country['code']}",
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "risk_indicator": rec["risk_indicator"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "source_reference": f"https://blog.example.com/{article_id}",
                }
            )
            article_id += 1
    df = pd.DataFrame(rows)
    if not df.empty:
        miss_idx = df.sample(frac=0.02, random_state=SEED + 1).index
        df.loc[miss_idx, "summary"] = None
    return df


def build_stackoverflow(topic_df: pd.DataFrame) -> pd.DataFrame:
    dev_categories = {
        "Programming Languages",
        "Web & Frontend Frameworks",
        "Backend & API Frameworks",
        "Data & Databases",
        "Cloud & Infrastructure",
        "Mobile Development",
        "Testing & QA",
        "DevOps & Monitoring",
        "Message Queues & Streaming",
        "API & Integration",
        "Security & Compliance",
        "AI & Machine Learning",
        "Data Science",
        "Emerging Technologies",
    }
    dev_topics = {
        topic
        for topic, meta in TOPICS.items()
        if meta.get("category") in dev_categories
        or topic in {"AI Agents", "LLM", "Data Engineering", "DevOps", "MLOps", "Developer Tools", "Vector Databases", "Inference Optimization", "Open Source AI", "Cloud Computing"}
    }
    rows: list[dict[str, Any]] = []
    qid = 500000
    for rec in topic_df.to_dict("records"):
        if rec["topic"] not in dev_topics:
            continue
        date = pd.Timestamp(rec["date"])
        count = int(max(0, RNG.poisson(rec["trend_score"] / 230) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            answers = int(max(0, RNG.normal(4 + rec["adoption_score"] * 0.07, 2.6)))
            views = int(max(35, RNG.normal(1800 + rec["trend_score"] * 90, 650)))
            score = int(max(-3, RNG.normal(18 + rec["trend_score"] * 0.9, 14)))
            accepted = bool(RNG.random() < np.clip(0.42 + answers * 0.015, 0.1, 0.9))
            title = weighted_choice(
                [
                    f"How to scale {rec['topic']} workloads without runaway cost?",
                    f"Best production pattern for {rec['topic']} with {company['company']} stack?",
                    f"Why is {rec['topic']} latency spiking after deployment?",
                    f"How to monitor quality in {rec['topic']} pipelines?",
                ],
                [1, 1, 1, 1],
            )
            body = (
                f"Our team is deploying {rec['topic'].lower()} workloads and seeing issues around "
                f"{weighted_choice(['latency', 'hallucination risk', 'throughput', 'governance', 'GPU saturation', 'schema drift'], [1,1,1,1,1,1])}. "
                f"We use components similar to {company['company']} and need guidance for production-ready patterns."
            )
            rows.append(
                {
                    "question_id": f"SO-{qid}",
                    "created_at": date.isoformat(),
                    "tag": rec["topic"],
                    "views": views,
                    "answers": answers,
                    "score": score,
                    "accepted_answer": accepted,
                    "title": title,
                    "body_preview": body,
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country": COUNTRY_BY_CODE[rec["country_code"]]["country"],
                    "trend_score": rec["trend_score"],
                    "sentiment_score": rec["sentiment_score"],
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "stackoverflow_question_volume": int(rec.get("stackoverflow_question_volume", 0)),
                    "documentation_health_score": rec.get("documentation_health_score", 0),
                    "community_health_score": rec.get("community_health_score", 0),
                    "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0)),
                    "risk_indicator": rec["risk_indicator"],
                    "source_reference": f"https://stackoverflow.example.com/questions/{qid}",
                }
            )
            qid += 1
    return pd.DataFrame(rows)


def build_google_trends(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rec in topic_df.to_dict("records"):
        country = COUNTRY_BY_CODE[rec["country_code"]]
        rows.append(
            {
                "date": pd.Timestamp(rec["date"]).date().isoformat(),
                "keyword": rec["topic"],
                "trend_score": int(round(rec["trend_score"])),
                "region": country["code"],
                "country": country["country"],
                "tech_category": rec["topic"],
                "sentiment_score": rec["sentiment_score"],
                "popularity_growth_pct": rec["popularity_growth_pct"],
                "volatility_metric": rec["volatility_metric"],
                "innovation_score": rec["innovation_score"],
                "adoption_score": rec["adoption_score"],
                "package_downloads_weekly": int(rec.get("package_downloads_weekly", 0)),
                "github_activity_index": rec.get("github_activity_index", 0),
                "stackoverflow_question_volume": int(rec.get("stackoverflow_question_volume", 0)),
                "job_market_demand_index": rec.get("job_market_demand_index", 0),
                "education_enrollment_index": rec.get("education_enrollment_index", 0),
                "conference_talks": int(rec.get("conference_talks", 0)),
                "documentation_health_score": rec.get("documentation_health_score", 0),
                "community_health_score": rec.get("community_health_score", 0),
                "risk_indicator": rec["risk_indicator"],
                "event_refs": rec["event_refs"],
            }
        )
    return pd.DataFrame(rows)


def build_reddit(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    post_id = 600000
    for rec in topic_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        social_wknd, _ = weekend_factor(date, social=TOPICS[rec["topic"]]["weekend_social"] * 1.08)
        count = int(max(0, RNG.poisson(rec["trend_score"] * social_wknd / 320) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            subreddit = weighted_choice(SUBREDDITS, [1.2 if rec["topic"] in {"AI Agents", "LLM", "Open Source AI"} and s in {"r/MachineLearning", "r/artificial"} else 1 for s in SUBREDDITS])
            upvotes = int(max(0, RNG.normal(rec["trend_score"] * 18, 45)))
            comments = int(max(0, RNG.normal(upvotes * 0.22, 18)))
            body = (
                f"Seeing more teams mention {company['company']} whenever {rec['topic'].lower()} comes up. "
                f"Feels like adoption is real in {COUNTRY_BY_CODE[rec['country_code']]['country']}, but the debate around "
                f"{weighted_choice(['moats', 'pricing', 'latency', 'security', 'open-source lock-in', 'GPU cost'], [1,1,1,1,1,1])} keeps resurfacing."
            )
            rows.append(
                {
                    "reddit_post_id": f"RDT-{post_id}",
                    "created_at": (date + pd.Timedelta(hours=int(RNG.integers(0, 24)), minutes=int(RNG.integers(0, 60)))).isoformat(),
                    "subreddit": subreddit,
                    "username": generate_user_name(),
                    "topic": rec["topic"],
                    "title": f"Is {rec['topic']} still underhyped or already overheating?",
                    "body": maybe_missing(body, 0.03),
                    "upvotes": upvotes,
                    "comments": comments,
                    "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.2), -1, 1)), 3),
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country": COUNTRY_BY_CODE[rec["country_code"]]["country"],
                    "region": COUNTRY_BY_CODE[rec["country_code"]]["region"],
                    "trend_score": rec["trend_score"],
                    "funding_estimate_musd": round(float(TOPICS[rec["topic"]]["funding"] * 15 + RNG.normal(0, 10)), 2),
                    "hiring_activity_index": round(float(TOPICS[rec["topic"]]["adoption"] * 0.65 + RNG.normal(0, 6)), 2),
                    "hashtags": f"#{slugify(rec['topic']).replace('-', '')}|#{rec['country_code']}",
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, "neutral"),
                    "risk_indicator": rec["risk_indicator"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "source_reference": f"https://reddit.example.com/{post_id}",
                }
            )
            post_id += 1
    return pd.DataFrame(rows)


def build_hackernews(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    hn_id = 700000
    for rec in topic_df.to_dict("records"):
        if rec["country_code"] != "US":
            continue
        date = pd.Timestamp(rec["date"])
        hn_categories = {
            "Programming Languages",
            "Web & Frontend Frameworks",
            "Backend & API Frameworks",
            "Data & Databases",
            "Cloud & Infrastructure",
            "DevOps & Monitoring",
            "Message Queues & Streaming",
            "AI & Machine Learning",
            "Data Science",
            "Emerging Technologies",
        }
        if rec["topic"] not in {"AI Agents", "LLM", "Open Source AI", "Developer Tools", "Data Engineering", "GPU Infrastructure", "Inference Optimization"} and TOPICS.get(rec["topic"], {}).get("category") not in hn_categories:
            continue
        count = int(max(0, RNG.poisson(rec["trend_score"] / 220) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            points = int(max(3, RNG.normal(rec["trend_score"] * 4.2, 20)))
            comments = int(max(1, RNG.normal(points * 0.42, 10)))
            rows.append(
                {
                    "hn_post_id": f"HN-{hn_id}",
                    "created_at": (date + pd.Timedelta(hours=int(RNG.integers(6, 23)))).isoformat(),
                    "title": f"{company['company']} and the new economics of {rec['topic'].lower()}",
                    "domain": weighted_choice(HN_DOMAINS, [1] * len(HN_DOMAINS)),
                    "topic": rec["topic"],
                    "points": points,
                    "comments": comments,
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country": "United States",
                    "trend_score": rec["trend_score"],
                    "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.14), -1, 1)), 3),
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "risk_indicator": rec["risk_indicator"],
                    "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, "positive"),
                    "source_reference": f"https://news.ycombinator.com/item?id={hn_id}",
                }
            )
            hn_id += 1
    return pd.DataFrame(rows)


def build_youtube(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    vid_id = 800000
    for rec in topic_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        youtube_categories = {"Web & Frontend Frameworks", "Mobile Development", "UI/UX & Design", "AI & Machine Learning", "Data Science", "Emerging Technologies"}
        if rec["topic"] not in {"AI Agents", "Generative AI", "LLM", "Developer Tools", "Robotics", "GPU Infrastructure"} and TOPICS.get(rec["topic"], {}).get("category") not in youtube_categories:
            continue
        count = int(max(0, RNG.poisson(rec["trend_score"] / 420) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            views = int(max(800, RNG.lognormal(mean=10.9, sigma=0.7)))
            likes = int(max(50, views * RNG.uniform(0.022, 0.09)))
            comments = int(max(5, likes * RNG.uniform(0.08, 0.22)))
            rows.append(
                {
                    "video_id": f"YT-{vid_id}",
                    "published_at": (date + pd.Timedelta(hours=int(RNG.integers(0, 24)))).isoformat(),
                    "channel": weighted_choice(YOUTUBE_CHANNELS, [1] * len(YOUTUBE_CHANNELS)),
                    "topic": rec["topic"],
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "title": f"{rec['topic']} market update: what {company['company']} says about 2026 demand",
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "watch_time_minutes": int(max(200, views * RNG.uniform(0.8, 2.6))),
                    "country": COUNTRY_BY_CODE[rec["country_code"]]["country"],
                    "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.15), -1, 1)), 3),
                    "trend_score": rec["trend_score"],
                    "funding_estimate_musd": round(float(TOPICS[rec["topic"]]["funding"] * 14 + RNG.normal(0, 9)), 2),
                    "hiring_activity_index": round(float(TOPICS[rec["topic"]]["adoption"] * 0.55 + RNG.normal(0, 6)), 2),
                    "hashtags": f"#{slugify(rec['topic']).replace('-', '')}|#AI|#{rec['country_code']}",
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, "positive"),
                    "risk_indicator": rec["risk_indicator"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "source_reference": f"https://youtube.example.com/watch?v={vid_id}",
                }
            )
            vid_id += 1
    return pd.DataFrame(rows)


def build_funding_events(company_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    funding_id = 900000
    stage_ranges = {
        "seed": (2, 8),
        "series_a": (8, 35),
        "series_b": (25, 90),
        "private": (80, 350),
        "public": (120, 800),
        "subsidiary": (150, 700),
        "nonprofit": (3, 25),
    }
    for company in COMPANIES:
        if company["stage"] == "public":
            events_count = 10 if company["company"] in {"NVIDIA", "Snowflake", "MongoDB"} else 6
        elif company["stage"] == "subsidiary":
            events_count = 5
        elif company["stage"] == "private":
            events_count = 7
        else:
            events_count = 4
        # scale funding events moderately but cap to available dates
        events_count = int(min(max(1, round(events_count * max(1.0, SCALE))), len(DATES)))
        chosen_dates = sorted(RNG.choice(DATES.to_numpy(), size=events_count, replace=False))
        for dt in chosen_dates:
            ts = pd.Timestamp(dt)
            topic = weighted_choice(company["topics"], [TOPICS[t]["funding"] for t in company["topics"]])
            low, high = stage_ranges[company["stage"]]
            amount = round(float(np.clip(RNG.lognormal(mean=np.log((low + high) / 2), sigma=0.45), low, high)), 2)
            valuation = round(float(amount * RNG.uniform(7, 28)), 2)
            round_type = {
                "seed": weighted_choice(["Seed", "Pre-Seed", "Strategic Seed"], [0.6, 0.2, 0.2]),
                "series_a": weighted_choice(["Series A", "Series A Extension"], [0.85, 0.15]),
                "series_b": weighted_choice(["Series B", "Series B Extension"], [0.82, 0.18]),
                "private": weighted_choice(["Growth Round", "Strategic Round", "Tender Offer"], [0.45, 0.35, 0.2]),
                "public": weighted_choice(["Follow-on Offering", "Strategic Investment", "Capex Program"], [0.35, 0.3, 0.35]),
                "subsidiary": weighted_choice(["Internal Investment", "Capex Allocation"], [0.55, 0.45]),
                "nonprofit": weighted_choice(["Foundation Grant", "Ecosystem Sponsorship", "Research Grant"], [0.45, 0.35, 0.2]),
            }[company["stage"]]
            rows.append(
                {
                    "funding_event_id": f"FND-{funding_id}",
                    "announced_at": ts.isoformat(),
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "country": COUNTRY_BY_CODE[company["country"]]["country"],
                    "region": COUNTRY_BY_CODE[company["country"]]["region"],
                    "tech_category": topic,
                    "round_type": round_type,
                    "amount_musd": amount,
                    "valuation_musd": valuation,
                    "lead_investor": weighted_choice(["Accel", "Sequoia", "Lightspeed", "General Catalyst", "Coatue", "SoftBank", "Corporate VC"], [1,1,1,1,1,1,1]),
                    "sentiment_score": round(float(np.clip(TOPICS[topic]["sentiment"] + RNG.normal(0, 0.12), -1, 1)), 3),
                    "trend_score": round(float(TOPICS[topic]["base"] + TOPICS[topic]["growth"] * 0.7 + RNG.normal(0, 4)), 2),
                    "estimated_hiring_impact_pct": round(float(np.clip(amount / max(low, 1) * RNG.uniform(0.6, 1.8), 2, 55)), 2),
                    "risk_indicator": "high" if topic == "Web3" else "moderate" if company["stage"] in {"seed", "series_a"} else "low",
                    "innovation_score": round(float(np.clip(TOPICS[topic]["innovation"] + RNG.normal(0, 3), 45, 100)), 2),
                    "adoption_score": round(float(np.clip(TOPICS[topic]["adoption"] + RNG.normal(0, 4), 25, 100)), 2),
                    "source_reference": f"https://funding.example.com/{funding_id}",
                }
            )
            funding_id += 1
    return pd.DataFrame(rows)


def build_producthunt(company_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    launch_id = 950000
    launch_company_ids = [
        company["company_id"]
        for company in COMPANIES
        if company["stage"] in {"seed", "series_a", "series_b", "private"}
        and any(TOPICS.get(topic, {}).get("category") in {"Developer Tools", "Web & Frontend Frameworks", "AI & Machine Learning", "Emerging Technologies", "UI/UX & Design", "CMS & Commerce"} for topic in company.get("topics", []))
    ]
    candidates = company_df[company_df["company_id"].isin(launch_company_ids)]
    sample_n = min(int(2400 * max(1.0, SCALE)), len(candidates))
    sampled = candidates.sample(n=sample_n, random_state=SEED)
    for rec in sampled.to_dict("records"):
        company = COMPANY_BY_ID[rec["company_id"]]
        topic = weighted_choice(company["topics"], [1] * len(company["topics"]))
        upvotes = int(max(20, RNG.normal(rec["trend_score"] * 3.8, 60)))
        comments = int(max(2, RNG.normal(upvotes * 0.16, 8)))
        rows.append(
            {
                "launch_id": f"PH-{launch_id}",
                "launched_at": pd.Timestamp(rec["date"]).isoformat(),
                "company_id": company["company_id"],
                "company": company["company"],
                "product_name": f"{company['company']} {weighted_choice(['Studio', 'Copilot', 'Flow', 'Radar', 'Ops'], [1,1,1,1,1])}",
                "category": weighted_choice(PRODUCT_CATEGORIES, [1.2 if topic in {"Developer Tools", "AI Agents"} and c in {"Developer Tools", "AI Productivity"} else 1 for c in PRODUCT_CATEGORIES]),
                "topic": topic,
                "upvotes": upvotes,
                "comments": comments,
                "country": COUNTRY_BY_CODE[company["country"]]["country"],
                "trend_score": rec["trend_score"],
                "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.12), -1, 1)), 3),
                "popularity_growth_pct": rec["popularity_growth_pct"],
                "volatility_metric": rec["volatility_metric"],
                "funding_estimate_musd": round(float(rec["funding_factor"] * 22 + RNG.normal(0, 6)), 2),
                "innovation_score": rec["innovation_score"],
                "adoption_score": rec["adoption_score"],
                "risk_indicator": "moderate" if topic in {"AI Agents", "Web3"} else "low",
                "ai_summary": sentence_case_summary(topic, company["company"], pd.Timestamp(rec["date"]), "positive"),
                "source_reference": f"https://producthunt.example.com/posts/{launch_id}",
            }
        )
        launch_id += 1
    return pd.DataFrame(rows)


def build_news_mentions(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    nid = 980000
    for rec in topic_df.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        country = COUNTRY_BY_CODE[rec["country_code"]]
        count = int(max(0, RNG.poisson(rec["trend_score"] / 900) * max(1.0, SCALE)))
        for _ in range(count):
            company = choose_company_for_topic(rec["topic"])
            headline_mode = "risk" if rec["risk_indicator"] == "high" and RNG.random() < 0.4 else "growth"
            title = (
                f"{company['company']} sees stronger enterprise pull for {rec['topic'].lower()}"
                if headline_mode == "growth"
                else f"Volatility returns to {rec['topic'].lower()} as buyers reassess risk exposure"
            )
            mentions = int(max(1, RNG.normal(rec["trend_score"] * 0.7, 3)))
            rows.append(
                {
                    "mention_id": f"NEWS-{nid}",
                    "published_at": (date + pd.Timedelta(hours=int(RNG.integers(0, 24)))).isoformat(),
                    "source": weighted_choice(NEWS_SOURCES, [1] * len(NEWS_SOURCES)),
                    "topic": rec["topic"],
                    "company_id": company["company_id"],
                    "company": company["company"],
                    "headline": title,
                    "country": country["country"],
                    "region": country["region"],
                    "mention_count": mentions,
                    "trend_score": rec["trend_score"],
                    "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.18), -1, 1)), 3),
                    "funding_estimate_musd": round(float(TOPICS[rec["topic"]]["funding"] * 19 + RNG.normal(0, 9)), 2),
                    "hiring_activity_index": round(float(TOPICS[rec["topic"]]["adoption"] * 0.72 + RNG.normal(0, 5)), 2),
                    "hashtags": f"#{slugify(rec['topic']).replace('-', '')}|#{country['code']}",
                    "popularity_growth_pct": rec["popularity_growth_pct"],
                    "volatility_metric": rec["volatility_metric"],
                    "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, "neutral" if headline_mode == "growth" else "negative"),
                    "risk_indicator": rec["risk_indicator"],
                    "innovation_score": rec["innovation_score"],
                    "adoption_score": rec["adoption_score"],
                    "source_reference": f"https://news.example.com/{nid}",
                }
            )
            nid += 1
    return pd.DataFrame(rows)


def build_kaggle_activity(topic_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    kid = 990000
    kaggle_categories = {"AI & Machine Learning", "Data Science", "Data & Databases", "Programming Languages"}
    filtered = topic_df[
        topic_df["topic"].isin({"LLM", "Generative AI", "MLOps", "Open Source AI", "Inference Optimization", "Data Engineering", "AI Agents"})
        | topic_df["topic"].map(lambda topic: TOPICS.get(topic, {}).get("category") in kaggle_categories)
    ]
    sample_n = min(int(3200 * max(1.0, SCALE)), len(filtered))
    sampled = filtered.sample(n=sample_n, random_state=SEED)
    for rec in sampled.to_dict("records"):
        date = pd.Timestamp(rec["date"])
        company = choose_company_for_topic(rec["topic"])
        kernels = int(max(2, RNG.normal(rec["trend_score"] * 0.9, 8)))
        medal_rate = round(float(np.clip(RNG.normal(0.11 + rec["innovation_score"] / 1000, 0.03), 0.02, 0.28)), 3)
        rows.append(
            {
                "kaggle_activity_id": f"KGL-{kid}",
                "activity_date": date.isoformat(),
                "competition_name": weighted_choice(KAGGLE_COMPETITIONS, [1] * len(KAGGLE_COMPETITIONS)),
                "topic": rec["topic"],
                "company_id": company["company_id"],
                "company": company["company"],
                "country": COUNTRY_BY_CODE[rec["country_code"]]["country"],
                "kernels_created": kernels,
                "notebook_votes": int(max(10, RNG.normal(kernels * 14, 35))),
                "dataset_downloads": int(max(20, RNG.normal(kernels * 38, 70))),
                "medal_rate": medal_rate,
                "trend_score": rec["trend_score"],
                "sentiment_score": round(float(np.clip(rec["sentiment_score"] + RNG.normal(0, 0.1), -1, 1)), 3),
                "popularity_growth_pct": rec["popularity_growth_pct"],
                "volatility_metric": rec["volatility_metric"],
                "innovation_score": rec["innovation_score"],
                "adoption_score": rec["adoption_score"],
                "risk_indicator": "low" if rec["topic"] != "Web3" else "moderate",
                "ai_summary": sentence_case_summary(rec["topic"], company["company"], date, "positive"),
                "source_reference": f"https://kaggle.example.com/activity/{kid}",
            }
        )
        kid += 1
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def write_parquet(df: pd.DataFrame, path: Path, partition_by_date: bool = False) -> None:
    try:
        df2 = df.copy()
        if partition_by_date:
            # find candidate date columns
            date_candidates = [c for c in ["date", "created_at", "published_at", "event_time", "activity_date", "posted_at", "launched_at", "announced_at"] if c in df2.columns]
            if date_candidates:
                dc = date_candidates[0]
                df2[dc] = pd.to_datetime(df2[dc], errors="coerce")
                df2["year"] = df2[dc].dt.year.fillna(0).astype(int)
                df2["month"] = df2[dc].dt.month.fillna(0).astype(int)
                outdir = path
                # if a file path with extension was supplied, use directory
                if outdir.suffix == ".parquet":
                    outdir = path.with_suffix("")
                outdir.mkdir(parents=True, exist_ok=True)
                df2.to_parquet(outdir, index=False, partition_cols=["year", "month"])
                return
        df2.to_parquet(path, index=False)
    except Exception:
        # fallback: write as gzipped CSV if parquet fails
        try:
            df.to_csv(path.with_suffix('.csv.gz'), index=False, compression='gzip')
        except Exception:
            df.to_csv(path.with_suffix('.csv'), index=False)


def write_ndjson(df: pd.DataFrame, path: Path, id_field: str | None = None) -> None:
    with path.open('w', encoding='utf-8') as fh:
        for rec in df.to_dict('records'):
            fh.write(json.dumps(rec, default=str) + "\n")


def write_es_bulk(df: pd.DataFrame, path: Path, id_field: str | None = None) -> None:
    with path.open('w', encoding='utf-8') as fh:
        for rec in df.to_dict('records'):
            doc_id = rec.get(id_field) if id_field and id_field in rec else None
            action = {"index": {}}
            if doc_id:
                action["index"]["_id"] = str(doc_id)
            fh.write(json.dumps(action) + "\n")
            fh.write(json.dumps(rec, default=str) + "\n")


def validate_datasets(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    """Run quick integrity checks and return a validation report."""
    report: dict[str, Any] = {}
    companies = datasets.get("companies")
    id_sets = {}
    if companies is not None:
        id_sets["companies"] = set(companies["company_id"].dropna().astype(str).unique())

    id_field_map = {
        "twitter_stream": "tweet_id",
        "linkedin_jobs": "job_id",
        "github_events": "event_id",
        "tech_blogs": "article_id",
        "stackoverflow_questions": "question_id",
        "reddit_discussions": "reddit_post_id",
        "hackernews_posts": "hn_post_id",
        "youtube_ai_content": "video_id",
        "startup_funding": "funding_event_id",
        "producthunt_launches": "launch_id",
        "news_media_mentions": "mention_id",
        "kaggle_ml_activity": "kaggle_activity_id",
        "companies": "company_id",
        "market_events": "event_id",
    }

    # primary key uniqueness checks
    pk_issues = {}
    for name, df in datasets.items():
        pk = id_field_map.get(name)
        if pk and pk in df.columns:
            dup_count = int(df[pk].duplicated().sum())
            if dup_count > 0:
                pk_issues[name] = dup_count
    report["duplicate_primary_keys"] = pk_issues

    # cross-dataset company_id checks
    fk_issues = {}
    if "companies" in datasets:
        company_ids = set(datasets["companies"]["company_id"].dropna().astype(str).unique())
        for name, df in datasets.items():
            if "company_id" in df.columns and name != "companies":
                missing = set(df["company_id"].dropna().astype(str).unique()) - company_ids
                if missing:
                    fk_issues[name] = len(missing)
    report["missing_company_refs"] = fk_issues

    # date range checks for google_trends
    if "google_trends" in datasets:
        try:
            g = datasets["google_trends"]
            dates = pd.to_datetime(g["date"], errors="coerce")
            out_of_range = int(((dates < pd.Timestamp(DATE_START)) | (dates > pd.Timestamp(DATE_END))).sum())
            report["google_trends_out_of_range"] = out_of_range
        except Exception:
            report["google_trends_out_of_range"] = "error"

    # simple funding -> hiring directional check
    funding_signal = {"positive_after": 0, "negative_after": 0, "unknown": 0}
    if "startup_funding" in datasets and "linkedin_jobs" in datasets:
        try:
            funding = datasets["startup_funding"].copy()
            jobs = datasets["linkedin_jobs"].copy()
            if "announced_at" in funding.columns and "posted_at" in jobs.columns:
                funding["announced_at"] = pd.to_datetime(funding["announced_at"], errors="coerce")
                jobs["posted_at"] = pd.to_datetime(jobs["posted_at"], errors="coerce")
                for _, fe in funding.iterrows():
                    cid = fe.get("company_id")
                    dt = fe.get("announced_at")
                    if pd.isna(cid) or pd.isna(dt):
                        funding_signal["unknown"] += 1
                        continue
                    before = jobs[(jobs["company_id"] == cid) & (jobs["posted_at"] >= (dt - pd.Timedelta(days=30))) & (jobs["posted_at"] < dt)]
                    after = jobs[(jobs["company_id"] == cid) & (jobs["posted_at"] > dt) & (jobs["posted_at"] <= (dt + pd.Timedelta(days=30)))]
                    if before.empty or after.empty:
                        funding_signal["unknown"] += 1
                        continue
                    before_mean = float(before["hiring_index"].dropna().mean()) if "hiring_index" in before.columns else 0.0
                    after_mean = float(after["hiring_index"].dropna().mean()) if "hiring_index" in after.columns else 0.0
                    if after_mean > before_mean:
                        funding_signal["positive_after"] += 1
                    else:
                        funding_signal["negative_after"] += 1
        except Exception:
            funding_signal["error"] = True
    report["funding_hiring_signal_summary"] = funding_signal

    realism_checks: dict[str, Any] = {
        "topic_count": len(TOPICS),
        "company_count": len(COMPANIES),
        "declining_technologies_checked": [],
        "declining_technology_failures": [],
        "emerging_technologies_checked": [],
        "emerging_technology_failures": [],
        "salary_signal": {},
    }
    if "google_trends" in datasets and not datasets["google_trends"].empty:
        try:
            trends = datasets["google_trends"].copy()
            trends["date"] = pd.to_datetime(trends["date"], errors="coerce")
            early_cutoff = pd.Timestamp(DATE_START) + pd.Timedelta(days=60)
            late_cutoff = pd.Timestamp(DATE_END) - pd.Timedelta(days=60)
            for topic in sorted(DECLINING_TECHNOLOGIES & set(trends["keyword"].astype(str).unique())):
                early = trends[(trends["keyword"] == topic) & (trends["date"] <= early_cutoff)]["trend_score"].mean()
                late = trends[(trends["keyword"] == topic) & (trends["date"] >= late_cutoff)]["trend_score"].mean()
                if pd.notna(early) and pd.notna(late):
                    realism_checks["declining_technologies_checked"].append({"topic": topic, "early": round(float(early), 2), "late": round(float(late), 2)})
                    if late > early * 1.08:
                        realism_checks["declining_technology_failures"].append(topic)
            for topic in sorted(EMERGING_TECHNOLOGIES & set(trends["keyword"].astype(str).unique())):
                early = trends[(trends["keyword"] == topic) & (trends["date"] <= early_cutoff)]["trend_score"].mean()
                late = trends[(trends["keyword"] == topic) & (trends["date"] >= late_cutoff)]["trend_score"].mean()
                if pd.notna(early) and pd.notna(late):
                    realism_checks["emerging_technologies_checked"].append({"topic": topic, "early": round(float(early), 2), "late": round(float(late), 2)})
                    if late < early * 0.92:
                        realism_checks["emerging_technology_failures"].append(topic)
        except Exception:
            realism_checks["trend_curve_error"] = True

    if "linkedin_jobs" in datasets and not datasets["linkedin_jobs"].empty:
        try:
            jobs = datasets["linkedin_jobs"].copy()
            salary_by_topic = jobs.groupby("tech_category")["salary_usd"].mean()
            for high_topic, low_topic in [("Rust", "PHP"), ("Go", "PHP"), ("Python", "Perl"), ("FastAPI", "ColdFusion")]:
                if high_topic in salary_by_topic and low_topic in salary_by_topic:
                    high_salary = float(salary_by_topic[high_topic])
                    low_salary = float(salary_by_topic[low_topic])
                    realism_checks["salary_signal"][f"{high_topic}_vs_{low_topic}"] = {
                        "high_topic_salary": round(high_salary, 2),
                        "low_topic_salary": round(low_salary, 2),
                        "passes": bool(high_salary >= low_salary),
                    }
        except Exception:
            realism_checks["salary_signal_error"] = True
    report["market_realism_checks"] = realism_checks

    # write report
    try:
        (IMPORT_DIR / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        pass
    return report


def write_sql_seed(datasets: dict[str, pd.DataFrame]) -> None:
    """Generate a seed loading SQL file (psql-friendly \copy commands) for all CSVs."""
    lines = ["-- Seed load helper for TechTrends datasets (psql \copy commands)", "-- Update paths if you moved the Data directory:", ""]
    top_level = {"linkedin_jobs", "twitter_stream", "github_events", "tech_blogs", "stackoverflow_questions", "google_trends"}
    for name in datasets.keys():
        if name in top_level:
            rel = Path("Data") / f"{name}.csv"
        else:
            rel = Path("Data") / "market_intel" / f"{name}.csv"
        lines.append(f"\\copy techtrends.{name} FROM '{rel.as_posix()}' CSV HEADER;")

    (IMPORT_DIR / "seed_load.sql").write_text("\n".join(lines), encoding="utf-8")


def write_json_schemas(datasets: dict[str, pd.DataFrame]) -> None:
    """Emit simple JSON schema per dataset by inferring types from dtypes and sample values."""
    schema_dir = MARKET_DIR / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    for name, df in datasets.items():
        fields: dict[str, Any] = {}
        sample = df.head(3)
        for col in df.columns:
            col_dtype = str(df[col].dtype)
            example = None
            try:
                example = sample[col].dropna().iloc[0]
            except Exception:
                example = None
            if pd.api.types.is_integer_dtype(df[col].dtype):
                jtype = "integer"
            elif pd.api.types.is_float_dtype(df[col].dtype):
                jtype = "number"
            elif pd.api.types.is_bool_dtype(df[col].dtype):
                jtype = "boolean"
            else:
                # try datetime
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", UserWarning)
                        pd.to_datetime(df[col].dropna().iloc[:3])
                    jtype = "string"
                except Exception:
                    jtype = "string"
            fields[col] = {"type": jtype, "example": (str(example) if example is not None else None)}
        out = {"$schema": "http://json-schema.org/draft-07/schema#", "title": f"{name}", "type": "object", "properties": fields}
        (schema_dir / f"{name}.schema.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


def build_dataset_summary(datasets: dict[str, pd.DataFrame]) -> dict[str, Any]:
    summary = {name: int(len(df)) for name, df in datasets.items()}
    date_columns = {
        "linkedin_jobs": "posted_at",
        "twitter_stream": "created_at",
        "github_events": "event_time",
        "tech_blogs": "published_at",
        "stackoverflow_questions": "created_at",
        "google_trends": "date",
        "reddit_discussions": "created_at",
        "hackernews_posts": "created_at",
        "youtube_ai_content": "published_at",
        "startup_funding": "announced_at",
        "producthunt_launches": "launched_at",
        "news_media_mentions": "published_at",
        "kaggle_ml_activity": "activity_date",
        "market_events": "event_date",
    }
    mins = []
    maxs = []
    for name, column in date_columns.items():
        if name not in datasets or column not in datasets[name].columns:
            continue
        values = pd.to_datetime(datasets[name][column], errors="coerce").dropna()
        if values.empty:
            continue
        mins.append(values.min())
        maxs.append(values.max())
    if mins and maxs:
        summary["date_range"] = f"{min(mins).date().isoformat()} to {max(maxs).date().isoformat()}"
    else:
        summary["date_range"] = f"{DATE_START} to {DATE_END}"
    summary["total_rows"] = int(sum(len(df) for df in datasets.values()))
    summary["countries"] = [c["country"] for c in COUNTRIES]
    summary["topics"] = list(TOPICS.keys())
    return summary


def dataset_catalog_entry(name: str, df: pd.DataFrame, schema: list[tuple[str, str]], analytics_usage: list[str], ml_use_cases: list[str]) -> str:
    sample = df.head(2).to_dict("records")
    lines = [f"## {name}", "", f"Rows: `{len(df)}`", "", "### Schema", ""]
    lines.append("| Field | Description |")
    lines.append("|---|---|")
    for field, desc in schema:
        lines.append(f"| `{field}` | {desc} |")
    lines.extend(["", "### Sample Records", "", "```json", json.dumps(sample, indent=2, default=str), "```", "", "### Expected Analytics Usage", ""])
    lines.extend([f"- {item}" for item in analytics_usage])
    lines.extend(["", "### Suggested ML Use-Cases", ""])
    lines.extend([f"- {item}" for item in ml_use_cases])
    lines.append("")
    return "\n".join(lines)


def write_metadata_catalog(datasets: dict[str, pd.DataFrame]) -> None:
    schemas = {
        "linkedin_jobs.csv": [
            ("job_id", "Unique job posting identifier"),
            ("posted_at", "Posting timestamp"),
            ("company_id", "Cross-dataset company key"),
            ("company", "Employer or startup name"),
            ("role", "Job title"),
            ("location", "City"),
            ("country", "Country name"),
            ("salary_usd", "Estimated annual compensation in USD"),
            ("skills", "Comma-separated skills and tools"),
            ("tech_category", "Primary technology trend represented by the role"),
            ("hiring_index", "Hiring demand proxy influenced by market conditions"),
            ("risk_indicator", "Operational or market risk label"),
        ],
        "twitter_stream.csv": [
            ("tweet_id", "Unique social post identifier"),
            ("created_at", "Tweet timestamp"),
            ("tech_topic", "Primary technology topic"),
            ("company_id", "Referenced company"),
            ("followers", "Audience size of author"),
            ("likes", "Engagement count"),
            ("retweets", "Reshare count"),
            ("sentiment_score", "Continuous sentiment signal"),
            ("volatility_metric", "Daily instability proxy"),
            ("ai_summary", "Generated digest of conversation context"),
        ],
        "github_events.csv": [
            ("event_id", "Unique repository activity identifier"),
            ("event_time", "Event date"),
            ("repository", "Repository slug"),
            ("language", "Main implementation language"),
            ("stars_added", "Stars gained on event day"),
            ("forks_added", "Forks gained on event day"),
            ("contributors", "Estimated contributor count"),
            ("topic", "Mapped technology trend"),
        ],
        "tech_blogs.csv": [
            ("article_id", "Unique article identifier"),
            ("published_at", "Publication timestamp"),
            ("source", "Blog platform or publication"),
            ("topic", "Primary theme"),
            ("title", "Article headline"),
            ("views", "Estimated article views"),
            ("summary", "Article summary text"),
        ],
        "stackoverflow_questions.csv": [
            ("question_id", "Question identifier"),
            ("created_at", "Question timestamp"),
            ("tag", "Primary technical tag"),
            ("views", "Question views"),
            ("answers", "Answer count"),
            ("accepted_answer", "Whether accepted solution exists"),
        ],
        "google_trends.csv": [
            ("date", "Daily trend observation date"),
            ("keyword", "Tracked topic keyword"),
            ("trend_score", "Normalized interest score"),
            ("region", "Country code"),
            ("popularity_growth_pct", "Day-over-day growth"),
        ],
        "reddit_discussions.csv": [
            ("reddit_post_id", "Discussion identifier"),
            ("subreddit", "Source community"),
            ("upvotes", "Community endorsement count"),
            ("comments", "Reply count"),
            ("company_id", "Referenced company"),
        ],
        "hackernews_posts.csv": [
            ("hn_post_id", "HN item identifier"),
            ("title", "Story title"),
            ("points", "HN points"),
            ("comments", "HN comment count"),
        ],
        "youtube_ai_content.csv": [
            ("video_id", "Video identifier"),
            ("channel", "Channel name"),
            ("views", "Video views"),
            ("watch_time_minutes", "Estimated aggregate watch time"),
        ],
        "startup_funding.csv": [
            ("funding_event_id", "Funding round identifier"),
            ("company_id", "Company key"),
            ("round_type", "Round or capital event type"),
            ("amount_musd", "Announced amount in USD millions"),
            ("valuation_musd", "Synthetic but plausible valuation estimate"),
            ("estimated_hiring_impact_pct", "Expected hiring lift after funding"),
        ],
        "producthunt_launches.csv": [
            ("launch_id", "Launch identifier"),
            ("product_name", "Product Hunt launch name"),
            ("category", "Product category"),
            ("upvotes", "Launch upvotes"),
            ("comments", "Launch comments"),
        ],
        "news_media_mentions.csv": [
            ("mention_id", "News mention identifier"),
            ("headline", "Media headline"),
            ("mention_count", "Burst count proxy"),
            ("source", "News outlet"),
        ],
        "kaggle_ml_activity.csv": [
            ("kaggle_activity_id", "Activity identifier"),
            ("competition_name", "Competition or theme"),
            ("kernels_created", "Notebook creation count"),
            ("dataset_downloads", "Download activity"),
            ("medal_rate", "Top submission share proxy"),
        ],
        "companies.csv": [
            ("company_id", "Primary company key"),
            ("company", "Company name"),
            ("country", "HQ country"),
            ("sector", "Business category"),
            ("dominant_topics", "Main trend themes"),
        ],
        "market_events.csv": [
            ("event_id", "Market event key"),
            ("event_date", "Event anchor date"),
            ("window_days", "Decay window"),
            ("title", "Description"),
            ("topic_impacts", "JSON of topic-specific shocks"),
        ],
    }
    analytics = {
        "linkedin_jobs.csv": ["hiring trend dashboards", "regional salary benchmarking", "funding-to-hiring lag analysis"],
        "twitter_stream.csv": ["sentiment and buzz monitoring", "trend spike detection", "regional share-of-voice reporting"],
        "github_events.csv": ["open-source momentum scoring", "repo health analysis", "developer ecosystem correlation studies"],
        "tech_blogs.csv": ["content engagement dashboards", "topic narrative analysis", "innovation storytelling analysis"],
        "stackoverflow_questions.csv": ["developer pain-point analysis", "question volume forecasting", "support burden estimation"],
        "google_trends.csv": ["time-series trend dashboards", "market seasonality analysis", "country-level momentum comparison"],
        "reddit_discussions.csv": ["community sentiment mining", "hype-cycle monitoring", "anomaly detection on discussion bursts"],
        "hackernews_posts.csv": ["early technical attention tracking", "influencer-domain analysis"],
        "youtube_ai_content.csv": ["creator economy analysis", "education demand tracking", "topic attention mix by format"],
        "startup_funding.csv": ["capital allocation analysis", "funding-to-growth forecasting", "valuation benchmarking"],
        "producthunt_launches.csv": ["launch velocity tracking", "product demand testing", "top-of-funnel product discovery analytics"],
        "news_media_mentions.csv": ["earned media monitoring", "reputation risk dashboards", "topic burst detection"],
        "kaggle_ml_activity.csv": ["ML community activity monitoring", "competition-to-adoption trend analysis"],
        "companies.csv": ["entity resolution", "company segmentation", "master data management"],
        "market_events.csv": ["event-driven analytics", "shock attribution", "change-point explanation"],
    }
    ml_uses = {
        "linkedin_jobs.csv": ["hiring demand forecasting", "salary regression", "location recommendation"],
        "twitter_stream.csv": ["sentiment classification", "engagement prediction", "duplicate detection"],
        "github_events.csv": ["star/fork growth modeling", "repo anomaly detection", "topic popularity forecasting"],
        "tech_blogs.csv": ["summary quality ranking", "topic classification", "engagement prediction"],
        "stackoverflow_questions.csv": ["answer likelihood prediction", "topic difficulty clustering", "support load forecasting"],
        "google_trends.csv": ["multivariate time-series forecasting", "changepoint detection", "volatility classification"],
        "reddit_discussions.csv": ["stance detection", "community segmentation", "engagement forecasting"],
        "hackernews_posts.csv": ["story ranking", "comment volume forecasting"],
        "youtube_ai_content.csv": ["view prediction", "channel recommendation", "topic lifecycle analysis"],
        "startup_funding.csv": ["funding round classification", "post-funding hiring impact modeling", "valuation range estimation"],
        "producthunt_launches.csv": ["launch success prediction", "category recommendation"],
        "news_media_mentions.csv": ["reputation risk scoring", "headline sentiment analysis", "burst forecasting"],
        "kaggle_ml_activity.csv": ["competition popularity forecasting", "talent signal extraction"],
        "companies.csv": ["entity graph features", "cross-source enrichment"],
        "market_events.csv": ["event attribution features", "causal impact analysis"],
    }
    sections = [
        "# Market Intelligence Dataset Catalog",
        "",
        "This catalog documents the synthetic datasets generated for TechTrends. The data is designed to be CSV-ready and realistic enough for analytics, reporting, and ML prototyping while remaining synthetic.",
        "",
    ]
    name_map = {
        "linkedin_jobs": "linkedin_jobs.csv",
        "twitter_stream": "twitter_stream.csv",
        "github_events": "github_events.csv",
        "tech_blogs": "tech_blogs.csv",
        "stackoverflow_questions": "stackoverflow_questions.csv",
        "google_trends": "google_trends.csv",
        "reddit_discussions": "reddit_discussions.csv",
        "hackernews_posts": "hackernews_posts.csv",
        "youtube_ai_content": "youtube_ai_content.csv",
        "startup_funding": "startup_funding.csv",
        "producthunt_launches": "producthunt_launches.csv",
        "news_media_mentions": "news_media_mentions.csv",
        "kaggle_ml_activity": "kaggle_ml_activity.csv",
        "companies": "companies.csv",
        "market_events": "market_events.csv",
    }
    for key, filename in name_map.items():
        sections.append(
            dataset_catalog_entry(
                filename,
                datasets[key],
                schemas[filename],
                analytics[filename],
                ml_uses[filename],
            )
        )
    (MARKET_DIR / "DATASET_CATALOG.md").write_text("\n".join(sections), encoding="utf-8")


def write_relationships_doc() -> None:
    doc = """# Dataset Relationships

```mermaid
erDiagram
    COMPANIES ||--o{ LINKEDIN_JOBS : company_id
    COMPANIES ||--o{ TWITTER_STREAM : company_id
    COMPANIES ||--o{ GITHUB_EVENTS : company_id
    COMPANIES ||--o{ TECH_BLOGS : company_id
    COMPANIES ||--o{ REDDIT_DISCUSSIONS : company_id
    COMPANIES ||--o{ HACKERNEWS_POSTS : company_id
    COMPANIES ||--o{ YOUTUBE_AI_CONTENT : company_id
    COMPANIES ||--o{ STARTUP_FUNDING : company_id
    COMPANIES ||--o{ PRODUCTHUNT_LAUNCHES : company_id
    COMPANIES ||--o{ NEWS_MEDIA_MENTIONS : company_id
    COMPANIES ||--o{ KAGGLE_ML_ACTIVITY : company_id
    MARKET_EVENTS }o--o{ GOOGLE_TRENDS : event_refs
    MARKET_EVENTS }o--o{ NEWS_MEDIA_MENTIONS : source_reference
```

Primary relationships:

- `company_id` is the core entity key across operational and social datasets.
- `tech_topic`, `topic`, `keyword`, and `tag` represent the same trend taxonomy at different source layers.
- `market_events.csv` encodes shock windows that influence trend spikes, sentiment shifts, volatility, hiring, and funding behavior.
- Funding and hiring are intentionally linked through company-level signals rather than strict one-to-one row joins.
"""
    (MARKET_DIR / "RELATIONSHIPS.md").write_text(doc, encoding="utf-8")


def write_import_assets() -> None:
    postgres_sql = """-- PostgreSQL schema and CSV copy examples for TechTrends market intelligence datasets.
-- Adjust file paths to your local environment before running.

CREATE SCHEMA IF NOT EXISTS techtrends;

CREATE TABLE IF NOT EXISTS techtrends.companies (
    company_id TEXT PRIMARY KEY,
    company TEXT,
    country TEXT,
    country_code TEXT,
    region TEXT,
    sector TEXT,
    stage TEXT,
    reference_type TEXT,
    dominant_topics TEXT
);

CREATE TABLE IF NOT EXISTS techtrends.linkedin_jobs (
    job_id TEXT PRIMARY KEY,
    posted_at TIMESTAMP,
    company TEXT,
    role TEXT,
    location TEXT,
    salary_usd NUMERIC,
    experience_years INT,
    skills TEXT,
    job_description TEXT,
    company_id TEXT,
    country TEXT,
    region TEXT,
    tech_category TEXT,
    hiring_index NUMERIC,
    funding_signal NUMERIC,
    sentiment_score NUMERIC,
    trend_score NUMERIC,
    popularity_growth_pct NUMERIC,
    volatility_metric NUMERIC,
    innovation_score NUMERIC,
    adoption_score NUMERIC,
    risk_indicator TEXT,
    source_platform TEXT
);

CREATE TABLE IF NOT EXISTS techtrends.twitter_stream (
    tweet_id TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    username TEXT,
    followers BIGINT,
    tech_topic TEXT,
    sentiment TEXT,
    likes BIGINT,
    retweets BIGINT,
    content TEXT,
    company_id TEXT,
    company TEXT,
    country TEXT,
    region TEXT,
    trend_score NUMERIC,
    sentiment_score NUMERIC,
    funding_estimate_musd NUMERIC,
    hiring_activity_index NUMERIC,
    hashtags TEXT,
    popularity_growth_pct NUMERIC,
    volatility_metric NUMERIC,
    ai_summary TEXT,
    risk_indicator TEXT,
    innovation_score NUMERIC,
    adoption_score NUMERIC,
    source_reference TEXT
);

-- Repeat table patterns as needed for the other CSVs.
-- Example bulk load:
-- \\copy techtrends.companies FROM 'Data/market_intel/companies.csv' CSV HEADER;
-- \\copy techtrends.linkedin_jobs FROM 'Data/linkedin_jobs.csv' CSV HEADER;
-- \\copy techtrends.twitter_stream FROM 'Data/twitter_stream.csv' CSV HEADER;
"""
    mongo_ps1 = """# Example MongoDB import commands for TechTrends datasets
$db = "techtrends_market_intel"
mongoimport --db $db --collection companies --type csv --headerline --file Data\\market_intel\\companies.csv
mongoimport --db $db --collection linkedin_jobs --type csv --headerline --file Data\\linkedin_jobs.csv
mongoimport --db $db --collection twitter_stream --type csv --headerline --file Data\\twitter_stream.csv
mongoimport --db $db --collection github_events --type csv --headerline --file Data\\github_events.csv
mongoimport --db $db --collection reddit_discussions --type csv --headerline --file Data\\market_intel\\reddit_discussions.csv
"""
    elastic_ps1 = """# Example Elasticsearch bulk prep commands for TechTrends datasets
# Convert CSVs to NDJSON first if you want full bulk indexing at scale.
# Example curl commands:
# curl -X PUT http://localhost:9200/techtrends-twitter
# curl -H "Content-Type: application/x-ndjson" -X POST http://localhost:9200/techtrends-twitter/_bulk --data-binary "@samples\\json\\twitter_stream.bulk.ndjson"
"""
    (IMPORT_DIR / "postgres_schema.sql").write_text(postgres_sql, encoding="utf-8")
    (IMPORT_DIR / "mongoimport_examples.ps1").write_text(mongo_ps1, encoding="utf-8")
    (IMPORT_DIR / "elasticsearch_bulk_examples.ps1").write_text(elastic_ps1, encoding="utf-8")


def write_json_samples(datasets: dict[str, pd.DataFrame]) -> None:
    for name, df in datasets.items():
        sample_path = JSON_SAMPLES_DIR / f"{name}.sample.json"
        sample_path.write_text(json.dumps(df.head(5).to_dict("records"), indent=2, default=str), encoding="utf-8")


def write_api_samples(datasets: dict[str, pd.DataFrame]) -> None:
    feature_topics = datasets["google_trends"].groupby("keyword")["trend_score"].mean().sort_values(ascending=False).head(10)
    top_payload = {"top": [{"tech": k, "score": round(float(v), 2)} for k, v in feature_topics.items()]}
    forecast_payload = {
        "technology": "AI Agents",
        "predicted_growth": 0.24,
        "confidence": 0.83,
        "trend": "booming",
        "features": {
            "mentions_7d_mean": 62.3,
            "mentions_growth_pct": 18.4,
            "job_postings_7d_sum": 146.0,
            "github_events_7d_sum": 318.0,
            "technology_popularity_score": 74.6,
        },
        "feature_importances": {
            "mentions_7d_mean": 0.23,
            "job_postings_7d_sum": 0.19,
            "github_events_7d_sum": 0.17,
            "trend_score_avg": 0.14,
        },
    }
    features_payload = {
        "technology": "GPU Infrastructure",
        "features": {
            "trend_score_avg": 81.2,
            "mentions_7d_mean": 48.6,
            "mentions_velocity": 6.8,
            "stars_sum": 1234,
            "contributors_n": 88,
            "job_postings": 64,
            "risk_indicator": "moderate",
        },
    }
    health_payload = {"status": "ok", "time": "2026-05-26T09:00:00Z"}
    (API_SAMPLES_DIR / "trends_top.sample.json").write_text(json.dumps(top_payload, indent=2), encoding="utf-8")
    (API_SAMPLES_DIR / "forecast_ai_agents.sample.json").write_text(json.dumps(forecast_payload, indent=2), encoding="utf-8")
    (API_SAMPLES_DIR / "features_gpu_infrastructure.sample.json").write_text(json.dumps(features_payload, indent=2), encoding="utf-8")
    (API_SAMPLES_DIR / "health.sample.json").write_text(json.dumps(health_payload, indent=2), encoding="utf-8")


def generate_market_intel_datasets(
    min_rows: int = 100000,
    scale: float = 1.0,
    seed: int = SEED,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    global RNG, SEED, SCALE
    formats = formats or ["csv", "parquet", "ndjson"]

    SEED = int(seed)
    RNG = np.random.default_rng(SEED)
    SCALE = float(max(1.0, scale))

    ensure_dirs()
    apply_market_context_adjustments()

    def _generate() -> dict[str, pd.DataFrame]:
        topic_df = topic_curve()
        company_df = company_daily_signals(topic_df)
        return {
            "linkedin_jobs": build_linkedin_jobs(company_df),
            "twitter_stream": build_twitter_stream(topic_df),
            "github_events": build_github_events(company_df),
            "tech_blogs": build_tech_blogs(topic_df),
            "stackoverflow_questions": build_stackoverflow(topic_df),
            "google_trends": build_google_trends(topic_df),
            "reddit_discussions": build_reddit(topic_df),
            "hackernews_posts": build_hackernews(topic_df),
            "youtube_ai_content": build_youtube(topic_df),
            "startup_funding": build_funding_events(company_df),
            "producthunt_launches": build_producthunt(company_df),
            "news_media_mentions": build_news_mentions(topic_df),
            "kaggle_ml_activity": build_kaggle_activity(topic_df),
            "companies": build_companies_dimension(),
            "market_events": build_events_dimension(),
        }

    datasets = _generate()
    total_rows = sum(len(df) for df in datasets.values())
    validation = validate_datasets(datasets)
    if total_rows < min_rows:
        required = math.ceil(min_rows / max(total_rows, 1))
        SCALE = float(max(SCALE, required))
        RNG = np.random.default_rng(SEED)
        datasets = _generate()
        total_rows = sum(len(df) for df in datasets.values())
        validation = validate_datasets(datasets)

    # map some datasets to primary output directories (keep original placement)
    top_level = {"linkedin_jobs", "twitter_stream", "github_events", "tech_blogs", "stackoverflow_questions", "google_trends"}
    id_fields = {
        "twitter_stream": "tweet_id",
        "linkedin_jobs": "job_id",
        "github_events": "event_id",
        "tech_blogs": "article_id",
        "stackoverflow_questions": "question_id",
        "reddit_discussions": "reddit_post_id",
        "hackernews_posts": "hn_post_id",
        "youtube_ai_content": "video_id",
        "startup_funding": "funding_event_id",
        "producthunt_launches": "launch_id",
        "news_media_mentions": "mention_id",
        "kaggle_ml_activity": "kaggle_activity_id",
        "companies": "company_id",
        "market_events": "event_id",
    }

    format_set = set([f.lower() for f in formats])

    for name, df in datasets.items():
        outdir = DATA_DIR if name in top_level else MARKET_DIR
        outdir.mkdir(parents=True, exist_ok=True)
        if "csv" in format_set:
            write_csv(df, outdir / f"{name}.csv")
        if "parquet" in format_set:
            partitionable = {"twitter_stream", "reddit_discussions", "github_events", "google_trends", "youtube_ai_content", "linkedin_jobs", "news_media_mentions"}
            if name in partitionable:
                write_parquet(df, outdir / f"{name}.parquet", partition_by_date=True)
            else:
                write_parquet(df, outdir / f"{name}.parquet")
        if "ndjson" in format_set:
            write_ndjson(df, IMPORT_DIR / f"{name}.ndjson")
        if "es" in format_set:
            write_es_bulk(df, IMPORT_DIR / f"{name}.es.bulk.ndjson", id_field=id_fields.get(name))

    summary = build_dataset_summary(datasets)
    (DATA_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (MARKET_DIR / "dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # write machine-readable JSON schemas and SQL seed loader
    write_json_schemas(datasets)
    write_sql_seed(datasets)

    write_metadata_catalog(datasets)
    write_relationships_doc()
    write_import_assets()
    write_json_samples(datasets)
    write_api_samples(datasets)
    write_market_context()

    return {
        "summary": summary,
        "validation": validation,
        "formats": sorted(format_set),
        "market_context_version": MARKET_CONTEXT_VERSION,
        "market_context_sources": MARKET_CONTEXT_SOURCES,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate market intelligence synthetic datasets")
    parser.add_argument("--min-rows", type=int, default=100000, help="Minimum total rows across all datasets")
    parser.add_argument("--scale", type=float, default=1.0, help="Initial scale multiplier for generation counts")
    parser.add_argument("--seed", type=int, default=SEED, help="RNG seed for deterministic outputs")
    parser.add_argument("--formats", nargs="+", default=["csv", "parquet", "ndjson"], help="Output formats to write (csv, parquet, ndjson, es)")
    args = parser.parse_args()

    result = generate_market_intel_datasets(
        min_rows=args.min_rows,
        scale=args.scale,
        seed=args.seed,
        formats=args.formats,
    )
    print("Validation summary:", json.dumps(result["validation"], indent=2))
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
