import unittest

from config import settings
from scripts.generate_market_intel_dataset import (
    COMPANIES,
    DECLINING_TECHNOLOGIES,
    EMERGING_TECHNOLOGIES,
    EVENTS,
    ROLE_LIBRARY,
    TOPIC_SKILLS,
    TOPICS,
)


class MarketIntelCatalogTests(unittest.TestCase):
    def test_catalog_has_broad_technology_coverage(self) -> None:
        self.assertGreaterEqual(len(TOPICS), 100)
        self.assertGreaterEqual(len(COMPANIES), 90)

        for topic in [
            "Python",
            "React",
            "C# / .NET",
            "FastAPI",
            "PostgreSQL",
            "Flutter",
            "Jest",
            "Apache Kafka",
            "Zero-Trust Security",
            "WebAssembly",
        ]:
            self.assertIn(topic, TOPICS)
            self.assertIn(topic, ROLE_LIBRARY)
            self.assertIn(topic, TOPIC_SKILLS)

    def test_declining_and_emerging_topics_are_configured_realistically(self) -> None:
        for topic in ["PHP", "Ruby", "COBOL", "Perl", "jQuery", "Flash"]:
            self.assertIn(topic, DECLINING_TECHNOLOGIES)
            self.assertLess(TOPICS[topic]["growth"], 0)
            self.assertLess(TOPICS[topic]["sentiment"], 0)

        for topic in ["Rust", "Go", "Next.js", "DuckDB", "Quantum Computing"]:
            self.assertIn(topic, EMERGING_TECHNOLOGIES)
            self.assertGreater(TOPICS[topic]["growth"], 8)

    def test_expanded_keywords_and_market_events_are_available(self) -> None:
        self.assertGreaterEqual(len(settings.PYTRENDS_KEYWORDS), 300)
        self.assertIn("python programming", settings.PYTRENDS_KEYWORDS)
        self.assertIn("mainframe cobol", settings.PYTRENDS_KEYWORDS)
        self.assertIn("AI Agents", settings.PYTRENDS_KEYWORDS)
        self.assertGreaterEqual(len(EVENTS), 30)


if __name__ == "__main__":
    unittest.main()
