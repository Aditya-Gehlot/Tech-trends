from __future__ import annotations

import unittest
from unittest.mock import patch

from api import app as api_app


class ApiV1AnalyticsRouteTests(unittest.TestCase):
    def test_api_v1_routes_are_registered(self) -> None:
        paths = {route.path for route in api_app.app.routes}
        expected = {
            "/api/v1/market/overview",
            "/api/v1/analytics/growth-matrix",
            "/api/v1/analytics/salary",
            "/api/v1/analytics/hiring-velocity",
            "/api/v1/analytics/ecosystem-dependencies",
            "/api/v1/analytics/leaderboards",
            "/api/v1/analytics/stability",
            "/api/v1/analytics/regional",
            "/api/v1/analytics/tech-cooccurrence",
            "/api/v1/analytics/lifecycle",
            "/api/v1/analytics/risk-opportunity",
            "/api/v1/analytics/skill-gap",
            "/api/v1/analytics/forecast-leaderboards",
            "/api/v1/analytics/events-timeline",
            "/api/v1/analytics/compare",
            "/api/v1/technology/{name}/detail",
            "/api/v1/technology/{name}/timeseries",
            "/api/v1/technology/{name}/regional-comparison",
            "/api/v1/technology/{name}/skill-combinations",
        }
        self.assertTrue(expected.issubset(paths))

    def test_endpoint_functions_return_service_payloads(self) -> None:
        route_expectations = [
            ("api.analytics_service.market_overview", api_app.api_v1_market_overview, {}, {"data_available": False}),
            ("api.analytics_service.growth_matrix", api_app.api_v1_growth_matrix, {"limit": 10}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.salary_analysis", api_app.api_v1_salary, {"limit": 10, "sort_by": "avg_salary"}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.hiring_velocity", api_app.api_v1_hiring_velocity, {"limit": 10, "days": 30}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.ecosystem_dependencies", api_app.api_v1_ecosystem_dependencies, {"depth": 2}, {"data_available": True, "nodes": [], "edges": []}),
            ("api.analytics_service.leaderboards", api_app.api_v1_leaderboards, {"metric": "growth", "period": "qoq", "limit": 10}, {"data_available": True, "rankings": []}),
            ("api.analytics_service.stability", api_app.api_v1_stability, {"limit": 10}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.regional", api_app.api_v1_regional, {"country": None, "limit": 10}, {"data_available": True, "hiring_demand_by_tech": []}),
            ("api.analytics_service.tech_cooccurrence", api_app.api_v1_tech_cooccurrence, {"limit": 10}, {"data_available": True, "matrix": []}),
            ("api.analytics_service.lifecycle", api_app.api_v1_lifecycle, {"limit": 10}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.risk_opportunity", api_app.api_v1_risk_opportunity, {"limit": 10}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.skill_gap", api_app.api_v1_skill_gap, {"limit": 10}, {"data_available": True, "technologies": []}),
            ("api.analytics_service.forecast_leaderboards", api_app.api_v1_forecast_leaderboards, {"period": "6_months", "limit": 10}, {"data_available": True, "biggest_gainers_predicted": [], "biggest_losers_predicted": []}),
            ("api.analytics_service.events_timeline", api_app.api_v1_events_timeline, {"days": 30}, {"data_available": True, "events": []}),
            ("api.analytics_service.technology_detail", api_app.api_v1_technology_detail, {"name": "Python"}, {"data_available": True, "name": "Python"}),
            ("api.analytics_service.technology_timeseries", api_app.api_v1_technology_timeseries, {"name": "Python", "days": 30, "metrics": "popularity"}, {"data_available": True, "data": []}),
            ("api.analytics_service.technology_regional_comparison", api_app.api_v1_technology_regional_comparison, {"name": "Python"}, {"data_available": True, "regions": {}}),
            ("api.analytics_service.technology_skill_combinations", api_app.api_v1_technology_skill_combinations, {"name": "Python"}, {"data_available": True, "top_combinations": []}),
        ]

        for patch_target, function, kwargs, payload in route_expectations:
            with self.subTest(function=function.__name__), patch(patch_target, return_value=payload):
                body = function(**kwargs)
                self.assertEqual(body.get("data_available"), payload.get("data_available"))

    def test_compare_route_uses_request_body(self) -> None:
        payload = {"data_available": True, "comparison": {"growth": {"Python": 1.0}}, "radar_data": {}}
        with patch("api.analytics_service.compare", return_value=payload) as mocked:
            body = api_app.api_v1_compare(api_app.AnalyticsCompareRequest(techs=["Python"], metrics=["growth"]))
        self.assertEqual(body["comparison"]["growth"]["Python"], 1.0)
        mocked.assert_called_once_with(techs=["Python"], metrics=["growth"])


if __name__ == "__main__":
    unittest.main()
