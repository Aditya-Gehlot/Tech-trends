"""DB-backed analytics service for enterprise dashboard endpoints.

The service is intentionally DB-only for ``/api/v1/*``. Existing non-v1
endpoints keep their file fallback behavior in ``api.app``.
"""
from __future__ import annotations

import itertools
import math
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from db.models import DailyFeature, MLModel, NormalizedRecord, PipelineRun, Prediction
from db.session import db_configured, session_scope


_CACHE: dict[str, tuple[float, Any]] = {}
_FRAME_CACHE: dict[str, tuple[float, tuple[pd.DataFrame, str | None, str | None]]] = {}
ANALYTICS_TTL_SECONDS = 300
FORECAST_TTL_SECONDS = 3600
DB_UNAVAILABLE_TTL_SECONDS = 60
_DB_UNAVAILABLE_UNTIL = 0.0
_DB_UNAVAILABLE_REASON: str | None = None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _num(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None or pd.isna(value):
            return default
    except Exception:
        if value is None:
            return default
    try:
        number = float(value)
    except Exception:
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def _safe_ratio(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    top = _num(numerator, 0.0) or 0.0
    bottom = _num(denominator, 0.0) or 0.0
    if bottom == 0:
        return default
    return top / bottom


def _cached(key: str, ttl_seconds: int, factory: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    now = time.time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < ttl_seconds:
        return cached[1]
    payload = factory()
    cache_time = now - max(0, ttl_seconds - 30) if payload.get("data_available") is False else now
    _CACHE[key] = (cache_time, payload)
    return payload


def _cached_frame(
    key: str,
    ttl_seconds: int,
    factory: Callable[[], tuple[pd.DataFrame, str | None, str | None]],
) -> tuple[pd.DataFrame, str | None, str | None]:
    now = time.time()
    cached = _FRAME_CACHE.get(key)
    if cached and now - cached[0] < ttl_seconds:
        frame, run_id, reason = cached[1]
        return frame.copy(), run_id, reason
    frame, run_id, reason = factory()
    cache_time = now - max(0, ttl_seconds - 30) if reason and frame.empty else now
    _FRAME_CACHE[key] = (cache_time, (frame.copy(), run_id, reason))
    return frame, run_id, reason


def _empty(reason: str, **payload: Any) -> dict[str, Any]:
    base = {"data_available": False, "reason": reason}
    base.update(payload)
    return base


def _ok(**payload: Any) -> dict[str, Any]:
    payload.setdefault("data_available", True)
    return _jsonable(payload)


def _db_unavailable_reason() -> str | None:
    if time.time() < _DB_UNAVAILABLE_UNTIL:
        return _DB_UNAVAILABLE_REASON or "Database is temporarily unavailable"
    return None


def _mark_db_unavailable(reason: str) -> None:
    global _DB_UNAVAILABLE_UNTIL, _DB_UNAVAILABLE_REASON
    _DB_UNAVAILABLE_UNTIL = time.time() + DB_UNAVAILABLE_TTL_SECONDS
    _DB_UNAVAILABLE_REASON = reason


def _tech_key(value: Any) -> str:
    return str(value or "").strip()


def _country_matches(record_country: Any, requested_country: str | None) -> bool:
    if not requested_country:
        return True
    if not record_country:
        return False
    requested = str(requested_country).strip().casefold()
    observed = str(record_country).strip().casefold()
    aliases = {
        "us": {"us", "usa", "u.s.", "u.s.a.", "united states", "united states of america"},
        "usa": {"us", "usa", "u.s.", "u.s.a.", "united states", "united states of america"},
        "uk": {"uk", "u.k.", "united kingdom", "great britain"},
        "uae": {"uae", "u.a.e.", "united arab emirates"},
    }
    return observed in aliases.get(requested, {requested})


def _trend_class(row: dict[str, Any], predictions: dict[str, dict[str, Any]] | None = None) -> str:
    tech = _tech_key(row.get("tech") or row.get("name"))
    pred = (predictions or {}).get(tech.casefold())
    if pred and pred.get("trend_class"):
        return str(pred["trend_class"]).lower()
    growth = _num(row.get("mentions_growth_pct"), None)
    if growth is None:
        growth = _num(row.get("ecosystem_momentum_score"), 0.0)
    if growth >= 0.08:
        return "booming"
    if growth <= -0.05:
        return "declining"
    return "stable"


def _score_column(df: pd.DataFrame, candidates: Iterable[str], default: float = 0.0) -> pd.Series:
    for column in candidates:
        if column in df.columns:
            return pd.to_numeric(df[column], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype="float64")


def _observed_date_filter(df: pd.DataFrame, days: int | None) -> pd.DataFrame:
    if df.empty or days is None or "date" not in df.columns:
        return df
    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.notna().sum() == 0:
        return df
    cutoff = dates.max() - pd.Timedelta(days=max(days - 1, 0))
    return df[dates >= cutoff].copy()


def _latest_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "tech" not in df.columns:
        return pd.DataFrame()
    sort_col = "date" if "date" in df.columns else None
    if sort_col:
        frame = df.copy()
        frame["_sort_date"] = pd.to_datetime(frame[sort_col], errors="coerce")
        return frame.sort_values("_sort_date").groupby("tech", as_index=False).tail(1).drop(columns=["_sort_date"])
    return df.groupby("tech", as_index=False).tail(1)


def _latest_feature_run(session) -> tuple[Any | None, str | None]:
    latest_feature_run = session.execute(
        select(DailyFeature.run_id, func.max(DailyFeature.created_at).label("created_at"))
        .where(DailyFeature.run_id.is_not(None))
        .group_by(DailyFeature.run_id)
        .order_by(func.max(DailyFeature.created_at).desc())
        .limit(1)
    ).first()
    if latest_feature_run and latest_feature_run[0]:
        external = session.scalar(select(PipelineRun.run_id).where(PipelineRun.id == latest_feature_run[0]))
        return latest_feature_run[0], external
    has_features = session.scalar(select(func.count(DailyFeature.id))) or 0
    return (None, None) if has_features else (False, None)


def _daily_feature_rows_to_frame(rows: list[Any]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for row in rows:
        values = row._mapping if hasattr(row, "_mapping") else row
        features = dict(values["features"] or {})
        features["tech"] = values["tech"]
        features["date"] = values["date"]
        features["technology_popularity_score"] = _num(
            values["technology_popularity_score"],
            _num(features.get("technology_popularity_score"), 0.0),
        )
        features["ecosystem_momentum_score"] = _num(
            values["ecosystem_momentum_score"],
            _num(features.get("ecosystem_momentum_score"), 0.0),
        )
        records.append(_jsonable(features))
    df = pd.DataFrame(records)
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    return df


def _load_features(days: int | None = None, techs: Iterable[str] | None = None) -> tuple[pd.DataFrame, str | None, str | None]:
    tech_key = ",".join(sorted([tech.casefold() for tech in techs or []]))
    cache_key = f"features:{days}:{tech_key}"
    return _cached_frame(cache_key, ANALYTICS_TTL_SECONDS, lambda: _load_features_uncached(days=days, techs=techs))


def _load_features_uncached(days: int | None = None, techs: Iterable[str] | None = None) -> tuple[pd.DataFrame, str | None, str | None]:
    if not db_configured():
        return pd.DataFrame(), None, "DATABASE_URL is not configured"
    blocked = _db_unavailable_reason()
    if blocked:
        return pd.DataFrame(), None, blocked
    try:
        with session_scope() as session:
            run_pk, external_run_id = _latest_feature_run(session)
            if run_pk is False:
                return pd.DataFrame(), None, "No daily_features rows found"
            criteria = []
            if run_pk is not None:
                criteria.append(DailyFeature.run_id == run_pk)
            if techs:
                lowered = [tech.casefold() for tech in techs]
                criteria.append(func.lower(DailyFeature.tech).in_(lowered))
            if days:
                max_date_stmt = select(func.max(DailyFeature.date))
                if criteria:
                    max_date_stmt = max_date_stmt.where(and_(*criteria))
                max_feature_date = session.scalar(max_date_stmt)
                if max_feature_date:
                    criteria.append(DailyFeature.date >= max_feature_date - timedelta(days=max(days - 1, 0)))
            stmt = select(
                DailyFeature.tech,
                DailyFeature.date,
                DailyFeature.features,
                DailyFeature.technology_popularity_score,
                DailyFeature.ecosystem_momentum_score,
            )
            if criteria:
                stmt = stmt.where(and_(*criteria))
            rows = session.execute(stmt.order_by(DailyFeature.tech.asc(), DailyFeature.date.asc())).all()
    except SQLAlchemyError as exc:
        reason = f"Database query failed: {exc.__class__.__name__}"
        _mark_db_unavailable(reason)
        return pd.DataFrame(), None, reason

    return _daily_feature_rows_to_frame(rows), external_run_id, None


def _load_latest_features(limit: int | None = None) -> tuple[pd.DataFrame, str | None, str | None]:
    return _cached_frame(f"features_latest:{limit}", ANALYTICS_TTL_SECONDS, lambda: _load_latest_features_uncached(limit=limit))


def _load_latest_features_uncached(limit: int | None = None) -> tuple[pd.DataFrame, str | None, str | None]:
    if not db_configured():
        return pd.DataFrame(), None, "DATABASE_URL is not configured"
    blocked = _db_unavailable_reason()
    if blocked:
        return pd.DataFrame(), None, blocked
    try:
        with session_scope() as session:
            run_pk, external_run_id = _latest_feature_run(session)
            if run_pk is False:
                return pd.DataFrame(), None, "No daily_features rows found"
            criteria = []
            if run_pk is not None:
                criteria.append(DailyFeature.run_id == run_pk)
            max_dates_stmt = select(DailyFeature.tech, func.max(DailyFeature.date).label("max_date"))
            if criteria:
                max_dates_stmt = max_dates_stmt.where(and_(*criteria))
            max_dates = max_dates_stmt.group_by(DailyFeature.tech).subquery()
            stmt = (
                select(
                    DailyFeature.tech,
                    DailyFeature.date,
                    DailyFeature.features,
                    DailyFeature.technology_popularity_score,
                    DailyFeature.ecosystem_momentum_score,
                )
                .join(max_dates, and_(DailyFeature.tech == max_dates.c.tech, DailyFeature.date == max_dates.c.max_date))
                .order_by(DailyFeature.technology_popularity_score.desc().nullslast())
            )
            if criteria:
                stmt = stmt.where(and_(*criteria))
            if limit:
                stmt = stmt.limit(limit)
            rows = session.execute(stmt).all()
    except SQLAlchemyError as exc:
        reason = f"Database query failed: {exc.__class__.__name__}"
        _mark_db_unavailable(reason)
        return pd.DataFrame(), None, reason
    return _daily_feature_rows_to_frame(rows), external_run_id, None


def _load_predictions() -> dict[str, dict[str, Any]]:
    if not db_configured():
        return {}
    if _db_unavailable_reason():
        return {}
    try:
        with session_scope() as session:
            latest = session.scalar(select(Prediction).order_by(Prediction.created_at.desc()).limit(1))
            if latest is None:
                return {}
            criteria = [Prediction.prediction_date == latest.prediction_date]
            if latest.run_id:
                criteria.append(Prediction.run_id == latest.run_id)
            rows = session.scalars(select(Prediction).where(and_(*criteria))).all()
    except SQLAlchemyError as exc:
        _mark_db_unavailable(f"Database query failed: {exc.__class__.__name__}")
        return {}
    payload = {}
    for row in rows:
        payload[row.tech.casefold()] = {
            "tech": row.tech,
            "trend_class": row.trend_class,
            "confidence": _num(row.confidence, None),
            "predicted_growth": _num(row.predicted_growth, None),
            "prediction_date": row.prediction_date,
            "input_feature_date": row.input_feature_date,
            "payload": row.prediction_payload or {},
        }
    return payload


def _load_records(
    days: int | None = None,
    sources: Iterable[str] | None = None,
    max_rows: int = 200_000,
) -> tuple[pd.DataFrame, str | None]:
    source_key = ",".join(sorted(sources or []))
    frame, _, reason = _cached_frame(
        f"records:{days}:{source_key}:{max_rows}",
        ANALYTICS_TTL_SECONDS,
        lambda: (lambda result: (result[0], None, result[1]))(
            _load_records_uncached(days=days, sources=sources, max_rows=max_rows)
        ),
    )
    return frame, reason


def _load_records_uncached(
    days: int | None = None,
    sources: Iterable[str] | None = None,
    max_rows: int = 200_000,
) -> tuple[pd.DataFrame, str | None]:
    if not db_configured():
        return pd.DataFrame(), "DATABASE_URL is not configured"
    blocked = _db_unavailable_reason()
    if blocked:
        return pd.DataFrame(), blocked
    try:
        with session_scope() as session:
            criteria = []
            max_day = session.scalar(select(func.max(NormalizedRecord.date)))
            if max_day and days:
                criteria.append(NormalizedRecord.date >= max_day - timedelta(days=max(days - 1, 0)))
            if sources:
                criteria.append(NormalizedRecord.source.in_(list(sources)))
            stmt = select(
                NormalizedRecord.source,
                NormalizedRecord.source_record_id,
                NormalizedRecord.date,
                NormalizedRecord.title,
                NormalizedRecord.tags,
                NormalizedRecord.techs,
                NormalizedRecord.raw,
            )
            if criteria:
                stmt = stmt.where(and_(*criteria))
            stmt = stmt.order_by(NormalizedRecord.date.desc()).limit(max_rows)
            rows = session.execute(stmt).all()
    except SQLAlchemyError as exc:
        reason = f"Database query failed: {exc.__class__.__name__}"
        _mark_db_unavailable(reason)
        return pd.DataFrame(), reason
    records = [
        {
            "source": row.source,
            "source_record_id": row.source_record_id,
            "date": row.date,
            "title": row.title,
            "tags": row.tags or [],
            "techs": row.techs or [],
            "raw": row.raw or {},
        }
        for row in rows
    ]
    return pd.DataFrame(records), None


def _records_for_tech(records: pd.DataFrame, tech: str) -> pd.DataFrame:
    if records.empty or "techs" not in records.columns:
        return pd.DataFrame()
    wanted = tech.casefold()
    mask = records["techs"].apply(lambda items: any(str(item).casefold() == wanted for item in (items or [])))
    return records[mask].copy()


def _cooccurrence_from_records(days: int | None = 90, limit: int = 30) -> tuple[list[dict[str, Any]], str | None]:
    records, reason = _load_records(days=days, max_rows=200_000)
    if records.empty:
        return [], reason or "No normalized_records rows found"

    pair_counts: Counter[tuple[str, str]] = Counter()
    tech_counts: Counter[str] = Counter()
    salary_totals: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    for row in records.to_dict(orient="records"):
        techs = sorted({_tech_key(item) for item in (row.get("techs") or []) if _tech_key(item)})
        if len(techs) < 2:
            continue
        for tech in techs:
            tech_counts[tech] += 1
        salary = _num((row.get("raw") or {}).get("salary_usd"), None)
        for left, right in itertools.combinations(techs, 2):
            pair_counts[(left, right)] += 1
            if salary is not None:
                salary_totals[(left, right)].append(salary)

    rows = []
    for (left, right), count in pair_counts.most_common(limit):
        denominator = min(tech_counts[left], tech_counts[right]) or count
        rows.append(
            {
                "tech1": left,
                "tech2": right,
                "cooccurrence_count": count,
                "cooccurrence_score": round(min(1.0, _safe_ratio(count, denominator)), 4),
                "percentage_of_stacks": round(100 * _safe_ratio(count, len(records)), 4),
                "avg_salary_combined": float(np.mean(salary_totals[(left, right)])) if salary_totals[(left, right)] else None,
            }
        )
    return rows, None


def _feature_records(limit: int | None = None, days: int | None = None) -> tuple[pd.DataFrame, str | None, str | None]:
    if days is None:
        latest, run_id, reason = _load_latest_features(limit=limit)
        return latest, run_id, reason
    df, run_id, reason = _load_features(days=days)
    if df.empty:
        return df, run_id, reason
    latest = _latest_rows(df)
    if limit:
        latest = latest.sort_values("technology_popularity_score", ascending=False).head(limit)
    return latest, run_id, None


def _with_prediction(row: dict[str, Any], predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tech = _tech_key(row.get("tech") or row.get("name"))
    pred = predictions.get(tech.casefold(), {})
    row["trend_class"] = pred.get("trend_class") or _trend_class(row, predictions)
    row["confidence"] = pred.get("confidence")
    row["predicted_growth"] = pred.get("predicted_growth")
    return row


def market_overview() -> dict[str, Any]:
    return _cached("market_overview", ANALYTICS_TTL_SECONDS, _market_overview_uncached)


def _market_overview_uncached() -> dict[str, Any]:
    latest, run_id, reason = _feature_records()
    if latest.empty:
        return _empty(reason or "No daily feature data available", run_id=run_id)
    predictions = _load_predictions()
    frame = latest.copy()
    frame["growth_rate"] = _score_column(frame, ["mentions_growth_pct", "ecosystem_momentum_score"])
    frame["hiring_demand"] = _score_column(frame, ["hiring_demand_index", "job_postings_7d_sum", "job_postings"])
    frame["avg_salary_resolved"] = _score_column(frame, ["avg_salary_senior", "salary_7d_mean", "avg_salary"])
    frame["opportunity_resolved"] = _score_column(frame, ["opportunity_score", "ecosystem_momentum_score"])
    frame["criticality_resolved"] = _score_column(frame, ["ecosystem_criticality_score", "stack_inclusion_rate"])

    hottest = frame.sort_values("growth_rate", ascending=False).head(1).iloc[0].to_dict()
    highest_paying = frame.sort_values("avg_salary_resolved", ascending=False).head(1).iloc[0].to_dict()
    most_demand = frame.sort_values("hiring_demand", ascending=False).head(1).iloc[0].to_dict()
    opportunity = frame.sort_values("opportunity_resolved", ascending=False).head(1).iloc[0].to_dict()
    critical = frame.sort_values("criticality_resolved", ascending=False).head(1).iloc[0].to_dict()
    declining = frame.sort_values("growth_rate", ascending=True).head(1).iloc[0].to_dict()

    co_pairs, _ = _cooccurrence_from_records(days=90, limit=100)
    dependents = [p["tech2"] for p in co_pairs if p.get("tech1") == critical.get("tech")][:3]
    dependents += [p["tech1"] for p in co_pairs if p.get("tech2") == critical.get("tech")][: max(0, 3 - len(dependents))]

    return _ok(
        run_id=run_id,
        hottest_tech=_with_prediction(
            {
                "name": hottest.get("tech"),
                "growth_7d": _num(hottest.get("growth_rate")),
                "forecast_trend": _trend_class(hottest, predictions),
            },
            predictions,
        ),
        highest_market_opportunity={
            "name": opportunity.get("tech"),
            "opportunity_score": _num(opportunity.get("opportunity_resolved")),
            "market_cap_proxy": _num(opportunity.get("market_cap_proxy"), None),
            "company_count": _num(opportunity.get("company_count"), None),
            "investment_trend": _num(opportunity.get("funding_amount_30d_sum"), None),
        },
        highest_paying={
            "name": highest_paying.get("tech"),
            "avg_salary": _num(highest_paying.get("avg_salary_resolved"), None),
            "growth_mom": _num(highest_paying.get("salary_growth_mom"), None),
            "experience_premium": (
                _num(highest_paying.get("avg_salary_senior"), 0.0) or 0.0
            )
            - (_num(highest_paying.get("avg_salary_entry"), 0.0) or 0.0),
            "regional_variance": _num(highest_paying.get("regional_variance"), None),
        },
        most_in_demand={
            "name": most_demand.get("tech"),
            "job_postings_7d": _num(most_demand.get("job_postings_7d_sum"), None),
            "hiring_velocity": _num(most_demand.get("hiring_demand"), None),
            "unique_company_count": _num(most_demand.get("company_count"), None),
            "salary_range": [
                _num(most_demand.get("avg_salary_entry"), None),
                _num(most_demand.get("avg_salary_senior"), None),
            ],
        },
        critical_dependency={
            "name": critical.get("tech"),
            "ecosystem_dependency_score": _num(critical.get("criticality_resolved")),
            "dependent_techs": dependents[:3],
            "maturity_badge": critical.get("adoption_curve_stage"),
        },
        biggest_declining={
            "name": declining.get("tech"),
            "decline_rate": _num(declining.get("growth_rate")),
            "legacy_adoption_remaining": _num(declining.get("stack_inclusion_rate"), None),
            "migration_target_technologies": [p["tech2"] for p in co_pairs if p.get("tech1") == declining.get("tech")][:3],
        },
    )


def growth_matrix(limit: int = 50) -> dict[str, Any]:
    key = f"growth_matrix:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _growth_matrix_uncached(limit))


def _growth_matrix_uncached(limit: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records(limit=limit)
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    predictions = _load_predictions()
    rows = []
    for row in latest.to_dict(orient="records"):
        payload = {
            "name": row.get("tech"),
            "date": row.get("date"),
            "popularity_score": _num(row.get("technology_popularity_score")),
            "growth_rate": _num(row.get("mentions_growth_pct"), _num(row.get("ecosystem_momentum_score"))),
            "hiring_demand": _num(row.get("hiring_demand_index"), _num(row.get("job_postings_7d_sum"))),
            "trend_class": _trend_class(row, predictions),
            "adoption_count": _num(row.get("mentions_30d_sum"), _num(row.get("mentions"))),
        }
        rows.append(_with_prediction(payload, predictions))
    return _ok(run_id=run_id, technologies=rows)


def salary_analysis(limit: int = 20, sort_by: str = "avg_salary") -> dict[str, Any]:
    key = f"salary:{limit}:{sort_by}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _salary_analysis_uncached(limit, sort_by))


def _salary_analysis_uncached(limit: int, sort_by: str) -> dict[str, Any]:
    latest, run_id, reason = _feature_records()
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    frame = latest.copy()
    frame["avg_salary"] = _score_column(frame, ["salary_7d_mean", "avg_salary_mid", "avg_salary"])
    sort_col = sort_by if sort_by in frame.columns else "avg_salary"
    rows = []
    for row in frame.sort_values(sort_col, ascending=False).head(limit).to_dict(orient="records"):
        rows.append(
            {
                "name": row.get("tech"),
                "salary_entry": _num(row.get("avg_salary_entry"), None),
                "salary_mid": _num(row.get("avg_salary_mid"), None),
                "salary_senior": _num(row.get("avg_salary_senior"), None),
                "avg_salary": _num(row.get("avg_salary"), None),
                "month_over_month_growth": _num(row.get("salary_growth_mom"), None),
                "salary_premium_vs_baseline": _num(row.get("salary_premium_vs_baseline"), None),
                "top_hiring_country": row.get("top_hiring_country"),
                "regional_variance": _num(row.get("regional_variance"), None),
            }
        )
    return _ok(run_id=run_id, technologies=rows)


def hiring_velocity(limit: int = 20, days: int = 60) -> dict[str, Any]:
    key = f"hiring_velocity:{limit}:{days}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _hiring_velocity_uncached(limit, days))


def _hiring_velocity_uncached(limit: int, days: int) -> dict[str, Any]:
    df, run_id, reason = _load_features(days=days)
    if df.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    latest = _latest_rows(df)
    leaders = latest.assign(_demand=_score_column(latest, ["job_postings_7d_sum", "job_postings"])).sort_values("_demand", ascending=False).head(limit)["tech"].tolist()
    rows = []
    for row in df[df["tech"].isin(leaders)].sort_values(["tech", "date"]).to_dict(orient="records"):
        rows.append(
            {
                "name": row.get("tech"),
                "date": row.get("date"),
                "job_postings": _num(row.get("job_postings"), _num(row.get("job_postings_7d_sum"))),
                "hiring_momentum": _num(row.get("hiring_demand_index"), _num(row.get("mentions_velocity"))),
                "unique_companies": _num(row.get("company_count"), None),
                "salary_range": [_num(row.get("avg_salary_entry"), None), _num(row.get("avg_salary_senior"), None)],
            }
        )
    return _ok(run_id=run_id, technologies=rows)


def ecosystem_dependencies(depth: int = 2) -> dict[str, Any]:
    key = f"ecosystem:{depth}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _ecosystem_dependencies_uncached(depth))


def _ecosystem_dependencies_uncached(depth: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records(limit=80)
    if latest.empty:
        return _empty(reason or "No daily feature data available", nodes=[], edges=[], run_id=run_id)
    predictions = _load_predictions()
    pair_rows, pair_reason = _cooccurrence_from_records(days=120, limit=200)
    if pair_reason and not pair_rows:
        pair_rows = []
    nodes = []
    for row in latest.to_dict(orient="records"):
        nodes.append(
            {
                "id": row.get("tech"),
                "label": row.get("tech"),
                "criticality_score": _num(row.get("ecosystem_criticality_score"), _num(row.get("stack_inclusion_rate"))),
                "trend_class": _trend_class(row, predictions),
                "size": _num(row.get("technology_popularity_score")),
            }
        )
    edges = [
        {"source": row["tech1"], "target": row["tech2"], "strength": row["cooccurrence_score"], "count": row["cooccurrence_count"]}
        for row in pair_rows
    ]
    return _ok(run_id=run_id, nodes=nodes, edges=edges, depth=depth)


def leaderboards(metric: str = "growth", period: str = "qoq", limit: int = 15) -> dict[str, Any]:
    key = f"leaderboards:{metric}:{period}:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _leaderboards_uncached(metric, period, limit))


def _period_days(period: str) -> int:
    return {"week": 7, "weekly": 7, "month": 30, "mom": 30, "quarter": 90, "qoq": 90}.get(period.lower(), 90)


def _leaderboards_uncached(metric: str, period: str, limit: int) -> dict[str, Any]:
    days = _period_days(period)
    df, run_id, reason = _load_features(days=days)
    if df.empty:
        return _empty(reason or "No daily feature data available", rankings=[], run_id=run_id, metric=metric, period=period)
    rankings = []
    for tech, group in df.groupby("tech"):
        ordered = group.sort_values("date")
        first = ordered.iloc[0]
        last = ordered.iloc[-1]
        if metric == "salary":
            start = _num(first.get("salary_7d_mean"), _num(first.get("avg_salary"), 0.0)) or 0.0
            end = _num(last.get("salary_7d_mean"), _num(last.get("avg_salary"), 0.0)) or 0.0
        else:
            start = _num(first.get("technology_popularity_score"), 0.0) or 0.0
            end = _num(last.get("technology_popularity_score"), 0.0) or 0.0
        growth_pct = (end / start - 1) if start else 0.0
        rankings.append(
            {
                "name": tech,
                "growth_pct": growth_pct,
                "mention_change": {"from": start, "to": end},
                "source_breakdown": {
                    key: _num(last.get(key), 0.0)
                    for key in ["linkedin_jobs", "github_events", "twitter_stream", "stackoverflow_questions", "google_trends"]
                    if key in last
                },
            }
        )
    rankings = sorted(rankings, key=lambda item: item["growth_pct"], reverse=True)[:limit]
    for idx, row in enumerate(rankings, start=1):
        row["rank"] = idx
    return _ok(run_id=run_id, metric=metric, period=period, rankings=rankings)


def stability(limit: int = 25) -> dict[str, Any]:
    key = f"stability:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _stability_uncached(limit))


def _stability_uncached(limit: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records()
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    rows = []
    for row in latest.to_dict(orient="records"):
        volatility = _num(row.get("volatility_severity"), _num(row.get("volatility_metric_avg"), 0.0)) or 0.0
        stability_score = max(0.0, 1.0 - min(1.0, volatility / 100.0))
        rows.append(
            {
                "name": row.get("tech"),
                "stability_score": stability_score,
                "volatility_metric": volatility,
                "variance_range": f"+/-{round(volatility, 2)}%",
                "trend_reversal_risk": _num(row.get("trend_reversal_risk"), None),
            }
        )
    rows = sorted(rows, key=lambda item: item["stability_score"], reverse=True)[:limit]
    return _ok(run_id=run_id, technologies=rows)


def regional(country: str | None = None, limit: int = 20) -> dict[str, Any]:
    key = f"regional:{country}:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _regional_uncached(country, limit))


def _regional_uncached(country: str | None, limit: int) -> dict[str, Any]:
    records, reason = _load_records(days=180, sources=["linkedin_jobs", "linkedin"], max_rows=200_000)
    if records.empty:
        return _empty(reason or "No normalized LinkedIn records available", country=country, hiring_demand_by_tech=[])
    rows = []
    for record in records.to_dict(orient="records"):
        raw = record.get("raw") or {}
        record_country = raw.get("country") or raw.get("region")
        if not _country_matches(record_country, country):
            continue
        salary = _num(raw.get("salary_usd"), None)
        for tech in record.get("techs") or []:
            rows.append({"name": _tech_key(tech), "country": record_country, "salary": salary, "date": record.get("date")})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return _empty("No regional records matched the requested filters", country=country, hiring_demand_by_tech=[])
    grouped = (
        frame.groupby("name")
        .agg(job_postings=("name", "count"), avg_salary=("salary", "mean"), country_count=("country", lambda s: s.dropna().nunique()))
        .reset_index()
        .sort_values("job_postings", ascending=False)
        .head(limit)
    )
    return _ok(country=country or "all", hiring_demand_by_tech=_jsonable(grouped.to_dict(orient="records")))


def tech_cooccurrence(limit: int = 30) -> dict[str, Any]:
    key = f"cooccurrence:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _tech_cooccurrence_uncached(limit))


def _tech_cooccurrence_uncached(limit: int) -> dict[str, Any]:
    rows, reason = _cooccurrence_from_records(days=180, limit=limit)
    if not rows:
        return _empty(reason or "No co-occurring technology records found", matrix=[])
    return _ok(matrix=rows)


def lifecycle(limit: int = 50) -> dict[str, Any]:
    key = f"lifecycle:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _lifecycle_uncached(limit))


def _lifecycle_uncached(limit: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records(limit=limit)
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    tech_names = [str(tech) for tech in latest["tech"].dropna().unique().tolist()]
    observed_dates: dict[str, tuple[Any, Any]] = {}
    if tech_names and db_configured() and not _db_unavailable_reason():
        try:
            with session_scope() as session:
                run_pk, _ = _latest_feature_run(session)
                criteria = [DailyFeature.tech.in_(tech_names)]
                if run_pk:
                    criteria.append(DailyFeature.run_id == run_pk)
                rows = session.execute(
                    select(
                        DailyFeature.tech,
                        func.min(DailyFeature.date).label("min_date"),
                        func.max(DailyFeature.date).label("max_date"),
                    )
                    .where(and_(*criteria))
                    .group_by(DailyFeature.tech)
                ).all()
                observed_dates = {row.tech: (row.min_date, row.max_date) for row in rows}
        except SQLAlchemyError as exc:
            _mark_db_unavailable(f"Database query failed: {exc.__class__.__name__}")
    predictions = _load_predictions()
    rows = []
    for row in latest.sort_values("technology_popularity_score", ascending=False).head(limit).to_dict(orient="records"):
        tech = row.get("tech")
        observed_years = None
        min_date, max_date = observed_dates.get(str(tech), (None, None))
        if min_date and max_date:
            observed_years = max((pd.Timestamp(max_date) - pd.Timestamp(min_date)).days / 365.25, 0.0)
        rows.append(
            {
                "name": tech,
                "years_in_market": observed_years,
                "hype_score": _num(row.get("ecosystem_momentum_score"), 0.0),
                "adoption_stage": row.get("adoption_curve_stage"),
                "maturity_position": row.get("quadrant_position"),
                "adoption": _num(row.get("technology_popularity_score"), 0.0),
                "trend_class": _trend_class(row, predictions),
                "lifecycle_stage_numeric": _num(row.get("lifecycle_stage_numeric"), None),
            }
        )
    return _ok(run_id=run_id, technologies=rows)


def risk_opportunity(limit: int = 50) -> dict[str, Any]:
    key = f"risk_opportunity:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _risk_opportunity_uncached(limit))


def _risk_opportunity_uncached(limit: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records(limit=limit)
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    rows = []
    for row in latest.to_dict(orient="records"):
        rows.append(
            {
                "name": row.get("tech"),
                "risk_score": _num(row.get("risk_score"), _num(row.get("volatility_severity"), 0.0)),
                "opportunity_score": _num(row.get("opportunity_score"), _num(row.get("ecosystem_momentum_score"), 0.0)),
                "market_size": _num(row.get("technology_popularity_score"), 0.0),
                "quadrant": row.get("quadrant_position"),
            }
        )
    return _ok(run_id=run_id, technologies=rows)


def skill_gap(limit: int = 20) -> dict[str, Any]:
    key = f"skill_gap:{limit}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _skill_gap_uncached(limit))


def _skill_gap_uncached(limit: int) -> dict[str, Any]:
    latest, run_id, reason = _feature_records()
    if latest.empty:
        return _empty(reason or "No daily feature data available", technologies=[], run_id=run_id)
    frame = latest.copy()
    frame["job_demand"] = _score_column(frame, ["job_postings_30d_sum", "job_postings_7d_sum", "job_postings"])
    rows = []
    for row in frame.sort_values("job_demand", ascending=False).head(limit).to_dict(orient="records"):
        shortage = _num(row.get("shortage_percentage"), None)
        rows.append(
            {
                "name": row.get("tech"),
                "job_demand": _num(row.get("job_demand"), 0.0),
                "developer_supply": _num(row.get("contributors_n"), _num(row.get("github_authors_30d_sum"), None)),
                "shortage_percentage": shortage,
                "avg_salary": _num(row.get("salary_7d_mean"), _num(row.get("avg_salary"), None)),
                "gap_severity": "critical" if shortage is not None and shortage >= 70 else "elevated" if shortage is not None and shortage >= 35 else "normal",
            }
        )
    return _ok(run_id=run_id, technologies=rows)


def forecast_leaderboards(period: str = "6_months", limit: int = 15) -> dict[str, Any]:
    key = f"forecast_leaderboards:{period}:{limit}"
    return _cached(key, FORECAST_TTL_SECONDS, lambda: _forecast_leaderboards_uncached(period, limit))


def _forecast_leaderboards_uncached(period: str, limit: int) -> dict[str, Any]:
    predictions = _load_predictions()
    if not predictions:
        return _empty("No predictions rows found", biggest_gainers_predicted=[], biggest_losers_predicted=[], period=period)
    latest, _, _ = _feature_records()
    score_by_tech = {}
    if not latest.empty:
        for row in latest.to_dict(orient="records"):
            score_by_tech[str(row.get("tech")).casefold()] = _num(row.get("technology_popularity_score"), 0.0)
    rows = []
    for key, pred in predictions.items():
        current_score = score_by_tech.get(key, 0.0)
        growth = _num(pred.get("predicted_growth"), 0.0) or 0.0
        rows.append(
            {
                "name": pred["tech"],
                "current_score": current_score,
                "predicted_score": current_score * (1 + growth),
                "growth_projection": growth,
                "confidence": pred.get("confidence"),
            }
        )
    return _ok(
        period=period,
        biggest_gainers_predicted=sorted(rows, key=lambda item: item["growth_projection"], reverse=True)[:limit],
        biggest_losers_predicted=sorted(rows, key=lambda item: item["growth_projection"])[:limit],
    )


def events_timeline(days: int = 90) -> dict[str, Any]:
    key = f"events:{days}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _events_timeline_uncached(days))


def _events_timeline_uncached(days: int) -> dict[str, Any]:
    records, reason = _load_records(days=days, sources=["market_events"], max_rows=20_000)
    if records.empty:
        return _empty(reason or "No market event records available", events=[])
    events = []
    for row in records.sort_values("date", ascending=False).to_dict(orient="records"):
        raw = row.get("raw") or {}
        events.append(
            {
                "date": row.get("date"),
                "title": row.get("title") or raw.get("event_name") or raw.get("title"),
                "impact": _num(raw.get("impact_score"), _num(raw.get("sentiment_shift"), None)),
                "affected_techs": row.get("techs") or [],
                "source": row.get("source"),
                "discussion_count": _num(raw.get("discussion_count"), _num(raw.get("mention_count"), None)),
                "sentiment_shift": _num(raw.get("sentiment_shift"), None),
            }
        )
    return _ok(events=events)


def compare(techs: list[str], metrics: list[str] | None = None) -> dict[str, Any]:
    metrics = metrics or ["salary", "growth", "hiring", "github", "sentiment", "stability", "adoption", "maturity"]
    key = f"compare:{','.join(sorted(techs))}:{','.join(metrics)}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _compare_uncached(techs, metrics))


def _compare_uncached(techs: list[str], metrics: list[str]) -> dict[str, Any]:
    df, run_id, reason = _load_features(techs=techs)
    if df.empty:
        return _empty(reason or "No matching feature data available", comparison={}, radar_data={}, run_id=run_id)
    latest = _latest_rows(df)
    comparison: dict[str, dict[str, Any]] = {metric: {} for metric in metrics}
    for row in latest.to_dict(orient="records"):
        tech = row.get("tech")
        values = {
            "salary": _num(row.get("salary_7d_mean"), _num(row.get("avg_salary"), None)),
            "growth": _num(row.get("mentions_growth_pct"), None),
            "hiring": _num(row.get("job_postings_30d_sum"), _num(row.get("job_postings_7d_sum"), None)),
            "github": _num(row.get("github_events_30d_sum"), _num(row.get("github_events_7d_sum"), None)),
            "sentiment": _num(row.get("sentiment_score_avg"), None),
            "stability": 1.0 - min(1.0, (_num(row.get("volatility_severity"), 0.0) or 0.0) / 100.0),
            "adoption": _num(row.get("technology_popularity_score"), None),
            "maturity": _num(row.get("lifecycle_stage_numeric"), None),
        }
        for metric in metrics:
            comparison.setdefault(metric, {})[tech] = values.get(metric)
    return _ok(run_id=run_id, comparison=comparison, radar_data=comparison)


def technology_detail(name: str) -> dict[str, Any]:
    key = f"technology_detail:{name.casefold()}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _technology_detail_uncached(name))


def _technology_detail_uncached(name: str) -> dict[str, Any]:
    df, run_id, reason = _load_features(techs=[name])
    if df.empty:
        return _empty(reason or "No matching feature data available", name=name)
    latest = _latest_rows(df).iloc[0].to_dict()
    predictions = _load_predictions()
    records, _ = _load_records(days=90, max_rows=100_000)
    tech_records = _records_for_tech(records, name)
    regional_payload = _regional_for_records(tech_records)
    combinations = _skill_combinations_for_records(tech_records, name, limit=10)
    events = [event for event in events_timeline(days=90).get("events", []) if name.casefold() in {str(t).casefold() for t in event.get("affected_techs", [])}]
    history = _jsonable(df.sort_values("date").tail(90).to_dict(orient="records"))
    return _ok(
        run_id=run_id,
        name=latest.get("tech"),
        summary=_with_prediction({"name": latest.get("tech"), "trend_class": _trend_class(latest, predictions)}, predictions),
        current_metrics={
            "popularity_score": _num(latest.get("technology_popularity_score")),
            "growth_rate": _num(latest.get("mentions_growth_pct"), None),
            "volatility": _num(latest.get("volatility_severity"), _num(latest.get("volatility_metric_avg"), None)),
            "hiring_velocity": _num(latest.get("hiring_demand_index"), _num(latest.get("job_postings_7d_sum"), None)),
            "avg_salary": _num(latest.get("salary_7d_mean"), _num(latest.get("avg_salary"), None)),
            "job_postings_7d": _num(latest.get("job_postings_7d_sum"), None),
            "github_activity": {
                "stars_7d": _num(latest.get("stars_sum"), None),
                "contributors": _num(latest.get("contributors_n"), None),
                "events_7d": _num(latest.get("github_events_7d_sum"), None),
            },
        },
        historical_trend=history,
        regional_breakdown=regional_payload,
        skill_demand={"top_combinations": combinations},
        ecosystem={
            "dependency_count": _num(latest.get("dependency_count"), None),
            "stack_inclusion_rate": _num(latest.get("stack_inclusion_rate"), None),
        },
        market_position={
            "trend_class": _trend_class(latest, predictions),
            "lifecycle_stage": latest.get("adoption_curve_stage"),
            "risk_level": latest.get("quadrant_position"),
            "opportunity_level": _num(latest.get("opportunity_score"), None),
        },
        recent_events=events,
        forecast=predictions.get(name.casefold(), {}),
    )


def technology_timeseries(name: str, days: int = 90, metrics: str | None = None) -> dict[str, Any]:
    key = f"timeseries:{name.casefold()}:{days}:{metrics}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _technology_timeseries_uncached(name, days, metrics))


def _technology_timeseries_uncached(name: str, days: int, metrics: str | None) -> dict[str, Any]:
    requested = [item.strip() for item in (metrics or "popularity,growth,hiring").split(",") if item.strip()]
    df, run_id, reason = _load_features(days=days, techs=[name])
    if df.empty:
        return _empty(reason or "No matching feature data available", technology=name, data=[], run_id=run_id)
    mapping = {
        "popularity": "technology_popularity_score",
        "growth": "mentions_growth_pct",
        "hiring": "job_postings_7d_sum",
        "salary": "salary_7d_mean",
        "sentiment": "sentiment_score_avg",
        "risk": "risk_score",
        "opportunity": "opportunity_score",
    }
    rows = []
    for row in df.sort_values("date").to_dict(orient="records"):
        payload = {"date": row.get("date"), "tech": row.get("tech")}
        for metric in requested:
            payload[metric] = _num(row.get(mapping.get(metric, metric)), None)
        rows.append(payload)
    return _ok(run_id=run_id, technology=name, metrics=requested, data=rows)


def _regional_for_records(records: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if records.empty:
        return {}
    rows = []
    for row in records.to_dict(orient="records"):
        raw = row.get("raw") or {}
        country = raw.get("country") or raw.get("region")
        salary = _num(raw.get("salary_usd"), None)
        if country:
            rows.append({"country": country, "salary": salary})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return {}
    grouped = frame.groupby("country").agg(job_postings=("country", "count"), avg_salary=("salary", "mean")).reset_index()
    return {row["country"]: {"job_postings": int(row["job_postings"]), "avg_salary": _jsonable(row["avg_salary"])} for row in grouped.to_dict(orient="records")}


def technology_regional_comparison(name: str) -> dict[str, Any]:
    key = f"technology_regional:{name.casefold()}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _technology_regional_comparison_uncached(name))


def _technology_regional_comparison_uncached(name: str) -> dict[str, Any]:
    records, reason = _load_records(days=180, sources=["linkedin_jobs", "linkedin"], max_rows=200_000)
    records = _records_for_tech(records, name)
    if records.empty:
        return _empty(reason or "No matching regional records available", technology=name, regions={})
    return _ok(technology=name, regions=_regional_for_records(records))


def _skill_combinations_for_records(records: pd.DataFrame, name: str, limit: int = 20) -> list[dict[str, Any]]:
    if records.empty:
        return []
    combos: Counter[tuple[str, ...]] = Counter()
    salaries: defaultdict[tuple[str, ...], list[float]] = defaultdict(list)
    for row in records.to_dict(orient="records"):
        raw = row.get("raw") or {}
        skills = raw.get("skills") or row.get("tags") or []
        if isinstance(skills, str):
            skills = [part.strip() for part in skills.replace("|", ",").split(",") if part.strip()]
        skills = sorted({_tech_key(skill) for skill in skills if _tech_key(skill) and _tech_key(skill).casefold() != name.casefold()})
        if not skills:
            continue
        selected = tuple([name, *skills[:2]])
        combos[selected] += 1
        salary = _num(raw.get("salary_usd"), None)
        if salary is not None:
            salaries[selected].append(salary)
    rows = []
    for combo, count in combos.most_common(limit):
        rows.append(
            {
                "combination": " + ".join(combo),
                "job_count": count,
                "avg_salary": float(np.mean(salaries[combo])) if salaries[combo] else None,
                "growth": None,
            }
        )
    return rows


def technology_skill_combinations(name: str) -> dict[str, Any]:
    key = f"technology_skills:{name.casefold()}"
    return _cached(key, ANALYTICS_TTL_SECONDS, lambda: _technology_skill_combinations_uncached(name))


def _technology_skill_combinations_uncached(name: str) -> dict[str, Any]:
    records, reason = _load_records(days=180, sources=["linkedin_jobs", "linkedin"], max_rows=200_000)
    records = _records_for_tech(records, name)
    if records.empty:
        return _empty(reason or "No matching skill records available", technology=name, top_combinations=[])
    return _ok(technology=name, top_combinations=_skill_combinations_for_records(records, name))


def latest_model_artifacts() -> dict[str, Any]:
    if not db_configured():
        return _empty("DATABASE_URL is not configured", model=None)
    blocked = _db_unavailable_reason()
    if blocked:
        return _empty(blocked, model=None)
    try:
        with session_scope() as session:
            row = session.scalar(select(MLModel).order_by(MLModel.created_at.desc()).limit(1))
            if not row:
                return _empty("No ml_models rows found", model=None)
            return _ok(
                model={
                    "id": str(row.id),
                    "run_id": str(row.run_id) if row.run_id else None,
                    "model_path": row.model_path,
                    "model_name": row.model_name,
                    "model_type": row.model_type,
                    "training_timestamp": row.training_timestamp,
                    "feature_count": row.feature_count,
                    "accuracy": row.accuracy,
                    "regression_mae": row.regression_mae,
                    "regression_r2": row.regression_r2,
                    "metrics": row.metrics or {},
                }
            )
    except SQLAlchemyError as exc:
        reason = f"Database query failed: {exc.__class__.__name__}"
        _mark_db_unavailable(reason)
        return _empty(reason, model=None)
