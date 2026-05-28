from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from feature_store.engineer import FeatureEngineer


class FeatureEngineeringEnterpriseMetricTests(unittest.TestCase):
    def test_enterprise_metrics_are_added_to_feature_output(self) -> None:
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        records = []
        for offset in range(12):
            day = start + timedelta(days=offset)
            for exp, salary, country in [(1, 90000, "United States"), (4, 130000, "India"), (7, 175000, "Germany")]:
                records.append(
                    {
                        "source": "linkedin_jobs",
                        "id": f"job-{offset}-{exp}",
                        "timestamp": day,
                        "title": "Platform Engineer",
                        "text": "Python FastAPI cloud role",
                        "tags": ["python", "fastapi"],
                        "techs": ["Python", "FastAPI"],
                        "url": None,
                        "raw": {
                            "salary_usd": salary + offset * 1000,
                            "experience_years": exp,
                            "country": country,
                            "skills": ["Python", "FastAPI", "PostgreSQL"],
                            "hiring_index": 70 + offset,
                            "funding_signal": 20 + offset,
                            "trend_score": 60 + offset,
                            "sentiment_score": 0.25,
                            "adoption_score": 65,
                            "popularity_growth_pct": 8 + offset,
                            "volatility_metric": 14,
                            "job_market_demand_index": 75,
                            "community_health_score": 80,
                            "package_downloads_weekly": 50000 + offset,
                        },
                    }
                )
            records.append(
                {
                    "source": "github_events",
                    "id": f"gh-{offset}",
                    "timestamp": day,
                    "title": "Repository event",
                    "text": "Python FastAPI release",
                    "tags": ["python", "fastapi"],
                    "techs": ["Python", "FastAPI"],
                    "url": None,
                    "raw": {
                        "stars_added": 50 + offset,
                        "forks_added": 5,
                        "contributors": 8,
                        "release_flag": 1,
                        "trend_score": 65,
                        "sentiment_score": 0.35,
                        "adoption_score": 70,
                        "volatility_metric": 10,
                        "community_health_score": 85,
                    },
                }
            )
            records.append(
                {
                    "source": "market_events",
                    "id": f"event-{offset}",
                    "timestamp": day,
                    "title": "Framework adoption event",
                    "text": "Enterprise adoption increased",
                    "tags": ["python", "fastapi"],
                    "techs": ["Python", "FastAPI"],
                    "url": None,
                    "raw": {"impact_score": 4, "sentiment_shift": 0.1},
                }
            )

        with tempfile.TemporaryDirectory(dir=Path.cwd()) as temp_dir:
            root = Path(temp_dir)
            processed_dir = root / "processed"
            source_dir = processed_dir / "fixture"
            source_dir.mkdir(parents=True)
            pd.DataFrame(records).to_parquet(source_dir / "records.parquet", index=False)

            with patch("feature_store.engineer.db_repo", None):
                features = FeatureEngineer(processed_dir=processed_dir, feature_dir=root / "feature_store").generate_daily_features(
                    write_partitions=False
                )

        expected_columns = {
            "avg_salary_entry",
            "avg_salary_mid",
            "avg_salary_senior",
            "salary_growth_mom",
            "salary_premium_vs_baseline",
            "hiring_demand_index",
            "market_cap_proxy",
            "opportunity_score",
            "risk_score",
            "quadrant_position",
            "ecosystem_criticality_score",
            "dependency_count",
            "stack_inclusion_rate",
            "volatility_severity",
            "trend_reversal_risk",
            "mentions_spike_detected",
            "adoption_curve_stage",
            "lifecycle_stage_numeric",
            "shortage_percentage",
            "event_mention_count",
            "sentiment_impact_from_events",
        }
        self.assertTrue(expected_columns.issubset(set(features.columns)))
        self.assertGreater(float(features["avg_salary_senior"].max()), float(features["avg_salary_entry"].max()))
        self.assertTrue(features["opportunity_score"].between(0, 100).all())
        self.assertTrue(features["risk_score"].between(0, 100).all())
        self.assertTrue(features["shortage_percentage"].between(0, 100).all())
        self.assertGreater(float(features["ecosystem_criticality_score"].max()), 0.0)


if __name__ == "__main__":
    unittest.main()
