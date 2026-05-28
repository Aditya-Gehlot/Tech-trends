"""Streamlit operations dashboard for TechTrends."""
from __future__ import annotations

import os
import time
from typing import Any, Dict
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

DEFAULT_API_URL = os.environ.get("API_URL", "http://127.0.0.1:8001")


def _fallback_url(url: str) -> str | None:
    if "8001" in url:
        return url.replace("8001", "8000")
    if "8000" in url:
        return url.replace("8000", "8001")
    return None


def api_request(method: str, path: str, **kwargs):
    url = f"{st.session_state.api_url}{path}"
    try:
        response = requests.request(method, url, timeout=kwargs.pop("timeout", 15), **kwargs)
        response.raise_for_status()
        return response.json()
    except Exception:
        fallback = _fallback_url(st.session_state.api_url)
        if fallback:
            response = requests.request(method, f"{fallback}{path}", timeout=15, **kwargs)
            response.raise_for_status()
            st.session_state.api_url = fallback
            return response.json()
        raise


def api_get(path: str, timeout: int = 15):
    return api_request("GET", path, timeout=timeout)


def api_post(path: str, payload: Dict[str, Any], timeout: int = 15):
    return api_request("POST", path, json=payload, timeout=timeout)


def rerun() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def value(value_: Any, default: str = "-") -> str:
    if value_ is None or value_ == "":
        return default
    if isinstance(value_, float):
        return f"{value_:,.4f}"
    if isinstance(value_, int):
        return f"{value_:,}"
    return str(value_)


def percent(value_: Any) -> str:
    try:
        return f"{float(value_) * 100:.2f}%"
    except Exception:
        return "-"


def as_number(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def add_percent_column(df: pd.DataFrame, source: str, target: str) -> pd.DataFrame:
    frame = df.copy()
    if source in frame.columns:
        values = as_number(frame[source])
        frame[target] = values.where(values.abs() > 1, values * 100)
    return frame


def add_salary_k_column(df: pd.DataFrame, source: str, target: str) -> pd.DataFrame:
    frame = df.copy()
    if source in frame.columns:
        frame[target] = as_number(frame[source]) / 1000
    return frame


def style_chart(fig: go.Figure, x_title: str | None = None, y_title: str | None = None) -> go.Figure:
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend_title_text="",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def horizontal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    x_title: str,
    color: str | None = None,
    text: str | None = None,
):
    frame = df.sort_values(x, ascending=True)
    fig = px.bar(frame, x=x, y=y, orientation="h", color=color, text=text, title=title)
    if text:
        fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
    return style_chart(fig, x_title=x_title, y_title="")


def donut(df: pd.DataFrame, names: str, values_col: str, title: str):
    fig = px.pie(df, names=names, values=values_col, hole=0.45, title=title)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return style_chart(fig)


def metric_cards(items: list[tuple[str, Any]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, (label, item_value) in enumerate(items):
        cols[idx % columns].metric(label, value(item_value))


def status_color(status: str) -> str:
    return {
        "Pending": "#6b7280",
        "Running": "#2563eb",
        "Completed": "#16a34a",
        "Failed": "#dc2626",
        "Warning": "#f97316",
    }.get(status, "#6b7280")


def stage_table(run: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for stage in run.get("stages", []):
        rows.append(
            {
                "Stage": stage.get("name"),
                "Status": stage.get("status"),
                "Progress": stage.get("progress"),
                "Start": stage.get("start_time"),
                "End": stage.get("end_time"),
                "Duration": stage.get("duration_seconds"),
                "Records": stage.get("records_processed"),
                "Inserted": stage.get("records_inserted"),
                "Rejected": stage.get("records_rejected"),
                "Duplicates": stage.get("duplicates_removed"),
                "Missing": stage.get("missing_values_found"),
                "Outliers": stage.get("outliers_detected"),
                "Input shape": stage.get("input_shape"),
                "Output shape": stage.get("output_shape"),
                "Error": stage.get("error_details"),
            }
        )
    return pd.DataFrame(rows)


def render_stage_cards(run: Dict[str, Any]) -> None:
    for stage in run.get("stages", []):
        color = status_color(stage.get("status"))
        badge_background = {
            "Pending": "#e5e7eb",
            "Running": "#dbeafe",
            "Completed": "#dcfce7",
            "Failed": "#fee2e2",
            "Warning": "#ffedd5",
        }.get(stage.get("status"), "#e5e7eb")
        st.markdown(
            f"""
            <div style="border:1px solid #e5e7eb;border-left:5px solid {color};border-radius:6px;padding:10px 12px;margin-bottom:8px;background:#fff;">
              <div style="display:flex;justify-content:space-between;gap:12px;">
                <span style="color:#111827;font-weight:700;">{stage.get('name')}</span>
                <span style="color:{color};background:{badge_background};font-weight:700;padding:2px 8px;border-radius:999px;">
                  {stage.get('status')}
                </span>
              </div>
              <div style="font-size:0.88rem;color:#374151;margin-top:4px;">
                {value(stage.get('progress'))}% | records {value(stage.get('records_processed'))} | duration {value(stage.get('duration_seconds'))}s
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_run_detail(run: Dict[str, Any]) -> None:
    top_metrics = [
        ("Status", run.get("status")),
        ("Progress", f"{int(run.get('overall_progress', 0) or 0)}%"),
        ("Records processed", run.get("records_processed")),
        ("Duration seconds", run.get("duration_seconds")),
        ("Features created", run.get("features_created")),
        ("Model score", run.get("model_score")),
        ("Triggered by", run.get("triggered_by")),
        ("Trigger type", run.get("trigger_type")),
    ]
    metric_cards(top_metrics, columns=4)

    meta_left, meta_right = st.columns([1.2, 1.8])
    with meta_left:
        st.markdown("**Run Metadata**")
        meta_rows = [
            {"Field": "Run ID", "Value": run.get("run_id")},
            {"Field": "Started", "Value": run.get("start_time")},
            {"Field": "Ended", "Value": run.get("end_time")},
            {"Field": "Current stage", "Value": run.get("current_stage")},
            {"Field": "Error", "Value": run.get("error_message")},
        ]
        st.dataframe(pd.DataFrame(meta_rows), use_container_width=True, hide_index=True)
    with meta_right:
        parameters = run.get("parameters") or {}
        if parameters:
            st.markdown("**Run Parameters**")
            st.dataframe(
                pd.DataFrame(
                    [{"Parameter": key, "Value": value(item)} for key, item in parameters.items()]
                ),
                use_container_width=True,
                hide_index=True,
            )

    stages = run.get("stages", [])
    if stages:
        st.markdown("**Stage Timeline**")
        render_stage_cards(run)

        stage_df = stage_table(run)
        if not stage_df.empty:
            chart_df = stage_df[["Stage", "Duration", "Progress", "Status"]].copy()
            chart_df["Duration"] = pd.to_numeric(chart_df["Duration"], errors="coerce").fillna(0.0)
            st.plotly_chart(
                px.bar(
                    chart_df,
                    x="Stage",
                    y="Duration",
                    color="Status",
                    title="Stage duration by run",
                    color_discrete_map={
                        "Pending": "#6b7280",
                        "Running": "#2563eb",
                        "Completed": "#16a34a",
                        "Failed": "#dc2626",
                        "Warning": "#f97316",
                    },
                ),
                use_container_width=True,
            )
            st.dataframe(stage_df, use_container_width=True, hide_index=True)

    lower_left, lower_right = st.columns(2)
    with lower_left:
        dims = run.get("dataset_dimensions") or {}
        if dims:
            st.markdown("**Dataset Dimensions**")
            st.dataframe(
                pd.DataFrame([{"Layer": key, "Shape": value(item)} for key, item in dims.items()]),
                use_container_width=True,
                hide_index=True,
            )

        metrics_payload = run.get("metrics") or {}
        if metrics_payload:
            st.markdown("**Pipeline Metrics**")
            st.dataframe(
                pd.DataFrame([{"Metric": key, "Value": value(item)} for key, item in metrics_payload.items()]),
                use_container_width=True,
                hide_index=True,
            )

    with lower_right:
        feature_tracking = run.get("feature_tracking") or {}
        if feature_tracking:
            st.markdown("**Feature Tracking**")
            st.dataframe(
                pd.DataFrame([{"Metric": key, "Value": value(item)} for key, item in feature_tracking.items()]),
                use_container_width=True,
                hide_index=True,
            )

        ml_tracking = run.get("ml_tracking") or {}
        if ml_tracking:
            st.markdown("**ML Tracking**")
            st.dataframe(
                pd.DataFrame([{"Metric": key, "Value": value(item)} for key, item in ml_tracking.items()]),
                use_container_width=True,
                hide_index=True,
            )

    logs = pd.DataFrame(run.get("logs", []))
    if not logs.empty:
        st.markdown("**Run Logs**")
        st.dataframe(logs, use_container_width=True, hide_index=True)


def latest_run_or_status():
    try:
        status_payload = api_get("/pipeline/status")
        return status_payload.get("run"), status_payload.get("status")
    except Exception:
        return None, "Unavailable"


def api_v1_get(path: str, timeout: int = 30) -> Dict[str, Any]:
    return api_get(f"/api/v1{path}", timeout=timeout)


def api_v1_post(path: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    return api_post(f"/api/v1{path}", payload=payload, timeout=timeout)


def show_unavailable(payload: Dict[str, Any]) -> bool:
    if payload and payload.get("data_available") is False:
        st.info(f"{payload.get('reason') or 'Analytics data is not available yet.'} Run the pipeline with DB persistence enabled to populate this view.")
        return True
    return False


def records_df(payload: Dict[str, Any], key: str) -> pd.DataFrame:
    rows = payload.get(key) if payload else []
    if isinstance(rows, dict):
        rows = list(rows.values())
    return pd.DataFrame(rows or [])


def render_analytics_error(exc: Exception) -> None:
    st.error(f"Analytics API is unavailable: {exc}")


def render_overview_card(title: str, item: Dict[str, Any], value_key: str = "name", detail_keys: list[str] | None = None) -> None:
    detail_keys = detail_keys or []
    st.metric(title, value(item.get(value_key)))
    labels = {
        "growth_7d": "7d growth",
        "growth_mom": "salary MoM",
        "confidence": "confidence",
        "opportunity_score": "opportunity score",
        "market_cap_proxy": "market proxy",
        "company_count": "companies",
        "avg_salary": "avg salary",
        "experience_premium": "senior premium",
        "job_postings_7d": "jobs in 7d",
        "hiring_velocity": "hiring index",
        "unique_company_count": "hiring companies",
        "ecosystem_dependency_score": "dependency score",
        "maturity_badge": "maturity",
        "decline_rate": "decline",
        "legacy_adoption_remaining": "legacy adoption",
        "trend_class": "trend",
    }
    percent_keys = {"growth_7d", "growth_mom", "confidence", "decline_rate", "legacy_adoption_remaining"}
    money_keys = {"avg_salary", "experience_premium", "market_cap_proxy"}
    details = {}
    for key in detail_keys:
        raw = item.get(key)
        if raw is None:
            continue
        if key in percent_keys:
            details[labels.get(key, key)] = percent(raw)
        elif key in money_keys:
            details[labels.get(key, key)] = f"${float(raw):,.0f}"
        else:
            details[labels.get(key, key)] = value(raw)
    if details:
        st.caption(" | ".join(f"{key}: {val}" for key, val in details.items()))


def plotly_empty_notice(df: pd.DataFrame, message: str) -> bool:
    if df.empty:
        st.info(message)
        return True
    return False


if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL

st.set_page_config(page_title="TechTrends Control Center", layout="wide")
st.title("TechTrends Control Center")

with st.sidebar:
    st.header("Connection")
    st.session_state.api_url = st.text_input("API URL", value=st.session_state.api_url)
    auto_refresh = st.toggle("Auto refresh while running", value=True)
    if st.button("Refresh"):
        rerun()

current_run, api_status = latest_run_or_status()
running = bool(current_run and current_run.get("status") == "Running")

try:
    metrics_payload = api_get("/pipeline/metrics")
except Exception:
    metrics_payload = {"metrics": {}, "feature_tracking": {}, "ml_tracking": {}, "dataset_dimensions": {}}

metrics = metrics_payload.get("metrics", {})
feature_tracking = metrics_payload.get("feature_tracking", {})
ml_tracking = metrics_payload.get("ml_tracking", {})
dataset_dimensions = metrics_payload.get("dataset_dimensions", {})

tabs = st.tabs([
    "Pipeline Control",
    "Live Insights",
    "Feature Layer",
    "ML & Predictions",
    "Run History",
    "Market Trends",
    "Executive Dashboard",
    "Growth & Momentum",
    "Business Impact",
    "Ecosystem",
    "Lifecycle",
    "Risk & Opportunity",
    "Geographic Insights",
    "Benchmarking",
    "Talent & Skills",
    "Forecasts",
    "Events",
    "Tech Deep Dive",
])

with tabs[0]:
    st.subheader("Pipeline Control Center")
    progress = int(current_run.get("overall_progress", 0)) if current_run else 0
    metric_cards(
        [
            ("Status", current_run.get("status") if current_run else api_status),
            ("Overall progress", f"{progress}%"),
            ("Current stage", current_run.get("current_stage") if current_run else None),
            ("Runtime seconds", current_run.get("duration_seconds") if current_run else None),
        ],
        columns=4,
    )
    st.progress(progress / 100)

    with st.form("pipeline_run_form"):
        left, mid, right = st.columns(3)
        clean = left.checkbox("Clean derived outputs", value=True)
        regenerate_data = mid.checkbox("Regenerate realistic sample data", value=False)
        confirmed = right.checkbox("Confirm full pipeline run", value=True)
        min_rows = left.number_input("Minimum generated rows", min_value=10000, max_value=1000000, value=100000, step=10000)
        scale = mid.number_input("Generation scale", min_value=1.0, max_value=10.0, value=1.0, step=0.5)
        seed = right.number_input("Generation seed", min_value=1, max_value=99999999, value=20260526, step=1)
        submitted = st.form_submit_button("Run Full Pipeline", disabled=running)

    if submitted:
        if not confirmed:
            st.warning("Confirm the full pipeline run before starting.")
        else:
            payload = {
                "trigger_type": "Full",
                "triggered_by": "streamlit-ui",
                "clean": clean,
                "regenerate_data": regenerate_data,
                "min_rows": int(min_rows),
                "scale": float(scale),
                "seed": int(seed),
                "formats": ["csv", "parquet", "ndjson", "es"],
            }
            try:
                result = api_post("/pipeline/run", payload)
                st.success(f"Pipeline started: {result.get('run_id')}")
                time.sleep(1)
                rerun()
            except requests.HTTPError as exc:
                st.error(exc.response.text)
            except Exception as exc:
                st.error(f"Could not start pipeline: {exc}")

    if current_run:
        st.subheader("Stage Progress")
        render_stage_cards(current_run)
        st.dataframe(stage_table(current_run), use_container_width=True, hide_index=True)
        logs = pd.DataFrame(current_run.get("logs", [])[-50:])
        if not logs.empty:
            st.subheader("Live Logs")
            st.dataframe(logs, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("Live Pipeline Insights")
    metric_cards(
        [
            ("Progress", f"{metrics.get('overall_pipeline_progress', 0)}%"),
            ("Current stage", metrics.get("current_running_stage")),
            ("Records processed", metrics.get("total_records_processed")),
            ("Records inserted", metrics.get("total_records_inserted")),
            ("Records rejected", metrics.get("total_records_rejected")),
            ("Duplicates removed", metrics.get("total_duplicate_records_removed")),
            ("Missing values found", metrics.get("total_missing_values_found")),
            ("Missing values handled", metrics.get("total_missing_values_handled")),
            ("Outliers detected", metrics.get("total_outliers_detected")),
            ("Features created", metrics.get("total_features_created")),
            ("Features selected", metrics.get("total_features_selected_applied")),
            ("Prediction count", metrics.get("prediction_output_count")),
        ],
        columns=4,
    )
    dim_rows = [{"Layer": k, "Shape": v} for k, v in dataset_dimensions.items()]
    if dim_rows:
        st.subheader("Dataset Dimensions")
        st.dataframe(pd.DataFrame(dim_rows), use_container_width=True, hide_index=True)

    totals = pd.DataFrame(
        [
            {"Metric": "Processed", "Value": metrics.get("total_records_processed", 0)},
            {"Metric": "Inserted", "Value": metrics.get("total_records_inserted", 0)},
            {"Metric": "Rejected", "Value": metrics.get("total_records_rejected", 0)},
            {"Metric": "Duplicates", "Value": metrics.get("total_duplicate_records_removed", 0)},
            {"Metric": "Missing handled", "Value": metrics.get("total_missing_values_handled", 0)},
            {"Metric": "Outliers", "Value": metrics.get("total_outliers_detected", 0)},
        ]
    )
    fig = px.bar(totals, x="Metric", y="Value", title="Pipeline data quality counters")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("Feature Engineering Tracking")
    metric_cards(
        [
            ("Original columns", feature_tracking.get("original_column_count")),
            ("New features", feature_tracking.get("new_feature_count")),
            ("Features used", feature_tracking.get("features_used_count")),
            ("Features dropped", feature_tracking.get("features_dropped_count")),
        ],
        columns=4,
    )
    created = feature_tracking.get("created_features", [])
    used = feature_tracking.get("features_used", [])
    dropped = feature_tracking.get("features_dropped", [])
    transformations = feature_tracking.get("transformation_summary", {})
    correlations = feature_tracking.get("correlation_insights", [])

    f1, f2 = st.columns(2)
    with f1:
        st.markdown("**Created Features**")
        st.dataframe(pd.DataFrame({"feature": created}), use_container_width=True, hide_index=True)
    with f2:
        st.markdown("**Features Used In Model**")
        st.dataframe(pd.DataFrame({"feature": used}), use_container_width=True, hide_index=True)

    if dropped:
        st.markdown("**Dropped Features**")
        st.dataframe(pd.DataFrame(dropped), use_container_width=True, hide_index=True)

    if transformations:
        rows = []
        for transform, names in transformations.items():
            rows.append({"Transformation": transform, "Feature count": len(names), "Examples": ", ".join(names[:8])})
        st.markdown("**Feature Transformations Applied**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    if correlations:
        corr_df = pd.DataFrame(correlations)
        st.plotly_chart(px.bar(corr_df.head(15), x="correlation", y="feature", orientation="h", title="Top correlations to future growth"), use_container_width=True)
        st.dataframe(corr_df, use_container_width=True, hide_index=True)

    nulls = feature_tracking.get("null_percentage_per_feature", {})
    dtypes = feature_tracking.get("data_type_per_feature", {})
    if nulls or dtypes:
        profile_df = pd.DataFrame(
            [
                {"feature": feature, "null_percent": nulls.get(feature), "dtype": dtypes.get(feature)}
                for feature in sorted(set(nulls) | set(dtypes))
            ]
        )
        st.markdown("**Feature Profile**")
        st.dataframe(profile_df, use_container_width=True, hide_index=True)

with tabs[3]:
    st.subheader("ML Tracking")
    metric_cards(
        [
            ("Model", ml_tracking.get("model_used")),
            ("Target", ml_tracking.get("target_variable")),
            ("Training rows", ml_tracking.get("training_dataset_size")),
            ("Testing rows", ml_tracking.get("testing_dataset_size")),
            ("Accuracy", ml_tracking.get("accuracy")),
            ("MAE", ml_tracking.get("mae")),
            ("R2", ml_tracking.get("r2")),
            ("Predictions", ml_tracking.get("prediction_count")),
        ],
        columns=4,
    )
    st.write("Model file:", ml_tracking.get("model_file_path") or "-")
    st.write("Last trained:", ml_tracking.get("last_trained_date") or "-")
    st.write("Improved vs previous:", value(ml_tracking.get("model_improved_vs_previous_run")))

    try:
        model_payload = api_get("/models/latest")
        importances = model_payload.get("feature_importances") or {}
    except Exception:
        importances = {}
    if importances:
        fi_df = pd.DataFrame([{"feature": k, "importance": v} for k, v in importances.items()])
        fi_df = fi_df.sort_values("importance", ascending=False).head(20)
        st.plotly_chart(px.bar(fi_df, x="importance", y="feature", orientation="h", title="Model feature importance"), use_container_width=True)

    try:
        predictions = api_get("/pipeline/predictions/latest").get("predictions", [])
    except Exception:
        predictions = []
    if predictions:
        pred_df = pd.DataFrame(predictions)
        st.subheader("Latest Predictions")
        st.dataframe(pred_df, use_container_width=True, hide_index=True)
        if {"tech", "predicted_growth"}.issubset(pred_df.columns):
            st.plotly_chart(px.bar(pred_df.sort_values("predicted_growth", ascending=False).head(20), x="tech", y="predicted_growth", color="trend", title="Predicted growth by technology"), use_container_width=True)

with tabs[4]:
    st.subheader("Pipeline Run History")
    try:
        history = api_get("/pipeline/runs?limit=50").get("runs", [])
    except Exception:
        history = []
    history_df = pd.DataFrame(history)
    if history_df.empty:
        st.info("No pipeline runs recorded yet.")
    else:
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        selected_run = st.selectbox("View details", options=history_df["run_id"].tolist())
        if selected_run:
            detail = api_get(f"/pipeline/runs/{selected_run}")
            render_run_detail(detail)

with tabs[5]:
    st.subheader("Market Intelligence")
    try:
        summary = api_get("/sources/summary")
        dataset_summary = summary.get("dataset", {})
        feature_summary = summary.get("features", {})
        model_summary = summary.get("model", {})
        metric_cards(
            [
                ("Sample rows", dataset_summary.get("total_rows")),
                ("Feature rows", feature_summary.get("feature_rows")),
                ("Technologies", feature_summary.get("technologies")),
                ("Model horizon", model_summary.get("horizon_days")),
            ],
            columns=4,
        )
    except Exception:
        st.warning("Source summary is unavailable.")

    try:
        context = api_get("/sources/market-context").get("context")
        if context:
            st.markdown("**Market Context Sources**")
            st.dataframe(pd.DataFrame(context.get("sources", [])), use_container_width=True, hide_index=True)
    except Exception:
        pass

    limit = st.slider("Top technologies", 5, 50, 10)
    top_df = pd.DataFrame()
    try:
        top = api_get(f"/trends/top?limit={limit}").get("top", [])
        top_df = pd.DataFrame(top)
        if not top_df.empty:
            st.plotly_chart(px.bar(top_df, x="tech", y="score", color="momentum", hover_data=["date", "mentions_7d_mean", "trend_score_avg"], title="Top technologies by popularity score"), use_container_width=True)
            st.dataframe(top_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"Could not load top trends: {exc}")

    options = top_df["tech"].tolist() if not top_df.empty and "tech" in top_df.columns else []
    selected = st.selectbox("Technology", options=options) if options else ""
    typed = st.text_input("Technology name", value="" if selected else "AI Agents")
    tech = typed.strip() or selected
    if tech:
        encoded = quote(tech, safe="")
        try:
            forecast = api_get(f"/forecast/{encoded}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Trend", forecast.get("trend"))
            c2.metric("Predicted growth", percent(forecast.get("predicted_growth")))
            c3.metric("Confidence", percent(forecast.get("confidence")))
            history = api_get(f"/trends/history/{encoded}?limit=180").get("history", [])
            hist_df = pd.DataFrame(history)
            if not hist_df.empty:
                hist_df["date"] = pd.to_datetime(hist_df["date"])
                st.plotly_chart(px.line(hist_df, x="date", y=["technology_popularity_score", "ecosystem_momentum_score"], title=f"{tech} history"), use_container_width=True)
        except Exception as exc:
            st.error(f"Could not load forecast for {tech}: {exc}")

with tabs[6]:
    st.subheader("Executive Dashboard")
    try:
        overview = api_v1_get("/market/overview")
        if not show_unavailable(overview):
            card_cols = st.columns(6)
            cards = [
                ("Hottest Technology", overview.get("hottest_tech", {}), ["growth_7d", "trend_class", "confidence"]),
                ("Market Opportunity", overview.get("highest_market_opportunity", {}), ["opportunity_score", "market_cap_proxy", "company_count"]),
                ("Highest Paying", overview.get("highest_paying", {}), ["avg_salary", "growth_mom", "experience_premium"]),
                ("Most In-Demand", overview.get("most_in_demand", {}), ["job_postings_7d", "hiring_velocity", "unique_company_count"]),
                ("Critical Dependency", overview.get("critical_dependency", {}), ["ecosystem_dependency_score", "maturity_badge"]),
                ("Biggest Decline", overview.get("biggest_declining", {}), ["decline_rate", "legacy_adoption_remaining"]),
            ]
            for col, (title, payload, details) in zip(card_cols, cards):
                with col:
                    render_overview_card(title, payload, detail_keys=details)

        growth_payload = api_v1_get("/analytics/growth-matrix?limit=60")
        growth_df = add_percent_column(records_df(growth_payload, "technologies"), "growth_rate", "growth_percent")
        if not plotly_empty_notice(growth_df, "No growth matrix rows are available from the database."):
            left, right = st.columns([2, 1])
            with left:
                top_growth = growth_df.sort_values("growth_percent", ascending=False).head(12).copy()
                top_growth["growth_label"] = top_growth["growth_percent"].map(lambda v: f"{v:.1f}%")
                st.plotly_chart(
                    horizontal_bar(
                        top_growth,
                        x="growth_percent",
                        y="name",
                        color="trend_class",
                        text="growth_label",
                        title="Fastest-growing technologies",
                        x_title="Growth over latest period (%)",
                    ),
                    use_container_width=True,
                )
            with right:
                trend_counts = growth_df["trend_class"].fillna("unknown").value_counts().reset_index()
                trend_counts.columns = ["trend", "technologies"]
                st.plotly_chart(donut(trend_counts, "trend", "technologies", "Trend mix"), use_container_width=True)
            st.dataframe(growth_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[7]:
    st.subheader("Growth & Momentum")
    try:
        limit = st.slider("Growth matrix technologies", 10, 120, 50, key="growth_limit")
        growth_payload = api_v1_get(f"/analytics/growth-matrix?limit={limit}")
        growth_df = add_percent_column(records_df(growth_payload, "technologies"), "growth_rate", "growth_percent")
        if not plotly_empty_notice(growth_df, "No growth data is available from PostgreSQL."):
            top_popularity = growth_df.sort_values("popularity_score", ascending=False).head(15).copy()
            st.plotly_chart(
                horizontal_bar(
                    top_popularity,
                    x="popularity_score",
                    y="name",
                    color="trend_class",
                    title="Most popular technologies",
                    x_title="Popularity score (0-100 index)",
                ),
                use_container_width=True,
            )

        leaders = api_v1_get("/analytics/leaderboards?metric=growth&period=qoq&limit=20")
        leader_df = add_percent_column(records_df(leaders, "rankings"), "growth_pct", "growth_percent")
        if not leader_df.empty:
            leader_df["growth_label"] = leader_df["growth_percent"].map(lambda v: f"{v:.1f}%")
            st.plotly_chart(
                horizontal_bar(
                    leader_df.sort_values("growth_percent"),
                    x="growth_percent",
                    y="name",
                    color="growth_percent",
                    text="growth_label",
                    title="Quarter-over-quarter growth leaders",
                    x_title="Quarter-over-quarter growth (%)",
                ),
                use_container_width=True,
            )
            st.dataframe(leader_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[8]:
    st.subheader("Business Impact")
    try:
        salary_payload = api_v1_get("/analytics/salary?limit=25&sort_by=avg_salary")
        salary_df = records_df(salary_payload, "technologies")
        if not plotly_empty_notice(salary_df, "No salary analytics are available from PostgreSQL."):
            salary_cols = [col for col in ["salary_entry", "salary_mid", "salary_senior"] if col in salary_df.columns]
            if salary_cols:
                salary_melt = salary_df.melt(id_vars=["name"], value_vars=salary_cols, var_name="experience_level", value_name="salary")
                salary_melt["salary_k"] = as_number(salary_melt["salary"]) / 1000
                st.plotly_chart(
                    style_chart(
                        px.bar(
                            salary_melt,
                            x="name",
                            y="salary_k",
                            color="experience_level",
                            barmode="group",
                            title="Average salary by experience level",
                        ),
                        x_title="Technology",
                        y_title="Average salary (USD thousands)",
                    ),
                    use_container_width=True,
                )
            st.dataframe(salary_df, use_container_width=True, hide_index=True)

        velocity_payload = api_v1_get("/analytics/hiring-velocity?limit=8&days=60")
        velocity_df = records_df(velocity_payload, "technologies")
        if not velocity_df.empty:
            velocity_df["date"] = pd.to_datetime(velocity_df["date"], errors="coerce")
            hiring_totals = velocity_df.groupby("name", as_index=False)["job_postings"].sum().sort_values("job_postings", ascending=False)
            st.plotly_chart(
                horizontal_bar(
                    hiring_totals,
                    x="job_postings",
                    y="name",
                    title="Hiring demand in the selected period",
                    x_title="Job postings",
                ),
                use_container_width=True,
            )
    except Exception as exc:
        render_analytics_error(exc)

with tabs[9]:
    st.subheader("Ecosystem")
    try:
        eco_payload = api_v1_get("/analytics/ecosystem-dependencies?depth=2")
        if not show_unavailable(eco_payload):
            nodes_df = records_df(eco_payload, "nodes")
            edges_df = records_df(eco_payload, "edges")
            if not nodes_df.empty:
                st.plotly_chart(
                    horizontal_bar(
                        nodes_df.sort_values("criticality_score", ascending=False).head(25),
                        x="criticality_score",
                        y="label",
                        color="trend_class",
                        title="Critical ecosystem components",
                        x_title="Dependency score (higher means more central)",
                    ),
                    use_container_width=True,
                )
            if not edges_df.empty:
                st.markdown("**Dependency edges from co-occurrence**")
                st.dataframe(edges_df.sort_values("strength", ascending=False), use_container_width=True, hide_index=True)

        co_payload = api_v1_get("/analytics/tech-cooccurrence?limit=50")
        co_df = records_df(co_payload, "matrix")
        if not co_df.empty:
            co_df["pair"] = co_df["tech1"].astype(str) + " + " + co_df["tech2"].astype(str)
            co_df = add_percent_column(co_df, "cooccurrence_score", "cooccurrence_percent")
            st.plotly_chart(
                horizontal_bar(
                    co_df.sort_values("cooccurrence_percent", ascending=False).head(20),
                    x="cooccurrence_percent",
                    y="pair",
                    title="Most common technology pairings",
                    x_title="Co-occurrence strength (%)",
                ),
                use_container_width=True,
            )
    except Exception as exc:
        render_analytics_error(exc)

with tabs[10]:
    st.subheader("Lifecycle")
    try:
        lifecycle_payload = api_v1_get("/analytics/lifecycle?limit=80")
        lifecycle_df = records_df(lifecycle_payload, "technologies")
        if not plotly_empty_notice(lifecycle_df, "No lifecycle analytics are available from PostgreSQL."):
            left, right = st.columns([1, 2])
            with left:
                stage_counts = lifecycle_df["adoption_stage"].fillna("unknown").value_counts().reset_index()
                stage_counts.columns = ["stage", "technologies"]
                st.plotly_chart(donut(stage_counts, "stage", "technologies", "Lifecycle stage mix"), use_container_width=True)
            with right:
                top_adoption = lifecycle_df.sort_values("adoption", ascending=False).head(15)
                st.plotly_chart(
                    horizontal_bar(
                        top_adoption,
                        x="adoption",
                        y="name",
                        color="adoption_stage",
                        title="Highest-adoption technologies",
                        x_title="Adoption score (0-100 index)",
                    ),
                    use_container_width=True,
                )
            st.dataframe(lifecycle_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[11]:
    st.subheader("Risk & Opportunity")
    try:
        risk_payload = api_v1_get("/analytics/risk-opportunity?limit=80")
        risk_df = records_df(risk_payload, "technologies")
        if not plotly_empty_notice(risk_df, "No risk/opportunity analytics are available from PostgreSQL."):
            display = risk_df.sort_values("opportunity_score", ascending=False).head(15)
            score_df = display.melt(id_vars=["name"], value_vars=["risk_score", "opportunity_score"], var_name="score_type", value_name="score")
            st.plotly_chart(
                style_chart(
                    px.bar(score_df, x="name", y="score", color="score_type", barmode="group", title="Risk and opportunity by technology"),
                    x_title="Technology",
                    y_title="Score (0-100 index)",
                ),
                use_container_width=True,
            )
            quadrant_counts = risk_df["quadrant"].fillna("unknown").value_counts().reset_index()
            quadrant_counts.columns = ["quadrant", "technologies"]
            st.plotly_chart(donut(quadrant_counts, "quadrant", "technologies", "Risk/opportunity category mix"), use_container_width=True)

        stability_payload = api_v1_get("/analytics/stability?limit=25")
        stability_df = records_df(stability_payload, "technologies")
        if not stability_df.empty:
            st.plotly_chart(
                horizontal_bar(
                    stability_df.sort_values("stability_score"),
                    x="stability_score",
                    y="name",
                    title="Most stable technologies",
                    x_title="Stability score (0-100 index)",
                ),
                use_container_width=True,
            )
    except Exception as exc:
        render_analytics_error(exc)

with tabs[12]:
    st.subheader("Geographic Insights")
    try:
        country = st.text_input("Country filter", value="", key="country_filter").strip()
        country_query = f"&country={quote(country, safe='')}" if country else ""
        regional_payload = api_v1_get(f"/analytics/regional?limit=30{country_query}")
        regional_df = records_df(regional_payload, "hiring_demand_by_tech")
        if not plotly_empty_notice(regional_df, "No regional hiring analytics are available from PostgreSQL."):
            regional_df = add_salary_k_column(regional_df, "avg_salary", "avg_salary_k")
            st.plotly_chart(
                horizontal_bar(
                    regional_df.sort_values("job_postings", ascending=False).head(20),
                    x="job_postings",
                    y="name",
                    title="Hiring demand by technology",
                    x_title="Job postings",
                ),
                use_container_width=True,
            )
            st.plotly_chart(
                horizontal_bar(
                    regional_df.sort_values("avg_salary_k", ascending=False).head(20),
                    x="avg_salary_k",
                    y="name",
                    title="Average salary by technology",
                    x_title="Average salary (USD thousands)",
                ),
                use_container_width=True,
            )
            st.dataframe(regional_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[13]:
    st.subheader("Benchmarking")
    try:
        growth_payload = api_v1_get("/analytics/growth-matrix?limit=80")
        tech_options = records_df(growth_payload, "technologies")
        options = tech_options["name"].dropna().tolist() if not tech_options.empty and "name" in tech_options.columns else []
        selected_techs = st.multiselect("Compare technologies", options=options, default=options[:3], key="benchmark_techs")
        metrics_choice = st.multiselect(
            "Metrics",
            ["salary", "growth", "hiring", "github", "sentiment", "stability", "adoption", "maturity"],
            default=["salary", "growth", "hiring", "stability", "adoption"],
            key="benchmark_metrics",
        )
        if selected_techs:
            compare_payload = api_v1_post("/analytics/compare", {"techs": selected_techs, "metrics": metrics_choice})
            if not show_unavailable(compare_payload):
                comparison = compare_payload.get("comparison", {})
                comp_df = pd.DataFrame(comparison).T
                st.dataframe(comp_df, use_container_width=True)
                if not comp_df.empty:
                    selected_metric = st.selectbox("Metric to chart", options=comp_df.index.tolist(), key="benchmark_chart_metric")
                    metric_df = comp_df.loc[selected_metric].reset_index()
                    metric_df.columns = ["technology", "raw_value"]
                    metric_df["chart_value"] = as_number(metric_df["raw_value"])
                    x_title = selected_metric
                    if selected_metric in {"growth", "sentiment", "stability", "adoption", "maturity"}:
                        metric_df = add_percent_column(metric_df, "chart_value", "chart_value")
                        x_title = f"{selected_metric.title()} (%)"
                    if selected_metric == "salary":
                        metric_df = add_salary_k_column(metric_df, "chart_value", "chart_value")
                        x_title = "Salary (USD thousands)"
                    st.plotly_chart(
                        horizontal_bar(
                            metric_df,
                            x="chart_value",
                            y="technology",
                            title=f"{selected_metric.title()} comparison",
                            x_title=x_title,
                        ),
                        use_container_width=True,
                    )
    except Exception as exc:
        render_analytics_error(exc)

with tabs[14]:
    st.subheader("Talent & Skills")
    try:
        skill_payload = api_v1_get("/analytics/skill-gap?limit=40")
        skill_df = add_percent_column(records_df(skill_payload, "technologies"), "shortage_percentage", "shortage_percent")
        if not plotly_empty_notice(skill_df, "No skill gap analytics are available from PostgreSQL."):
            st.plotly_chart(
                horizontal_bar(
                    skill_df.sort_values("shortage_percent", ascending=False).head(20),
                    x="shortage_percent",
                    y="name",
                    color="gap_severity",
                    title="Largest talent shortages",
                    x_title="Estimated shortage (%)",
                ),
                use_container_width=True,
            )
            demand_df = skill_df.sort_values("job_demand", ascending=False).head(20)
            st.plotly_chart(
                horizontal_bar(
                    demand_df,
                    x="job_demand",
                    y="name",
                    color="gap_severity",
                    title="Most requested skills",
                    x_title="Job postings",
                ),
                use_container_width=True,
            )
            severity_counts = skill_df["gap_severity"].fillna("unknown").value_counts().reset_index()
            severity_counts.columns = ["severity", "technologies"]
            st.plotly_chart(donut(severity_counts, "severity", "technologies", "Skill gap severity mix"), use_container_width=True)
            st.dataframe(skill_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[15]:
    st.subheader("Forecasts")
    try:
        forecast_payload = api_v1_get("/analytics/forecast-leaderboards?period=6_months&limit=15")
        if not show_unavailable(forecast_payload):
            gainers = pd.DataFrame(forecast_payload.get("biggest_gainers_predicted", []))
            losers = pd.DataFrame(forecast_payload.get("biggest_losers_predicted", []))
            left, right = st.columns(2)
            with left:
                if not gainers.empty:
                    gainers = add_percent_column(gainers, "growth_projection", "growth_projection_percent")
                    st.plotly_chart(
                        horizontal_bar(
                            gainers,
                            x="growth_projection_percent",
                            y="name",
                            title="Predicted gainers",
                            x_title="Projected growth (%)",
                        ),
                        use_container_width=True,
                    )
                    st.dataframe(gainers, use_container_width=True, hide_index=True)
            with right:
                if not losers.empty:
                    losers = add_percent_column(losers, "growth_projection", "growth_projection_percent")
                    st.plotly_chart(
                        horizontal_bar(
                            losers.sort_values("growth_projection_percent", ascending=False),
                            x="growth_projection_percent",
                            y="name",
                            title="Predicted decliners",
                            x_title="Projected growth (%)",
                        ),
                        use_container_width=True,
                    )
                    st.dataframe(losers, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[16]:
    st.subheader("Events")
    try:
        event_payload = api_v1_get("/analytics/events-timeline?days=90")
        event_df = records_df(event_payload, "events")
        if not plotly_empty_notice(event_df, "No market-event records are available from PostgreSQL."):
            event_df["date"] = pd.to_datetime(event_df["date"], errors="coerce")
            event_df["event"] = event_df["title"].astype(str).str.slice(0, 60)
            st.plotly_chart(
                horizontal_bar(
                    event_df.sort_values("impact").tail(20),
                    x="impact",
                    y="event",
                    color="source",
                    title="Market events by sentiment impact",
                    x_title="Sentiment impact score",
                ),
                use_container_width=True,
            )
            st.dataframe(event_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

with tabs[17]:
    st.subheader("Tech Deep Dive")
    try:
        growth_payload = api_v1_get("/analytics/growth-matrix?limit=100")
        tech_options_df = records_df(growth_payload, "technologies")
        options = tech_options_df["name"].dropna().tolist() if not tech_options_df.empty and "name" in tech_options_df.columns else []
        selected_name = st.selectbox("Technology", options=options, key="deep_dive_select") if options else ""
        typed_name = st.text_input("Or type technology name", value="", key="deep_dive_typed").strip()
        tech_name = typed_name or selected_name
        if tech_name:
            encoded_name = quote(tech_name, safe="")
            detail_payload = api_v1_get(f"/technology/{encoded_name}/detail")
            if not show_unavailable(detail_payload):
                metric_cards(
                    [
                        ("Popularity", detail_payload.get("current_metrics", {}).get("popularity_score")),
                        ("Growth", percent(detail_payload.get("current_metrics", {}).get("growth_rate"))),
                        ("Volatility", detail_payload.get("current_metrics", {}).get("volatility")),
                        ("Avg salary", detail_payload.get("current_metrics", {}).get("avg_salary")),
                    ],
                    columns=4,
                )
                st.dataframe(pd.DataFrame([detail_payload.get("market_position", {})]), use_container_width=True, hide_index=True)

            ts_payload = api_v1_get(f"/technology/{encoded_name}/timeseries?days=90&metrics=popularity,growth,hiring,salary")
            ts_df = records_df(ts_payload, "data")
            if not ts_df.empty:
                ts_df["date"] = pd.to_datetime(ts_df["date"], errors="coerce")
                if "popularity" in ts_df.columns:
                    st.plotly_chart(
                        style_chart(px.line(ts_df, x="date", y="popularity", title=f"{tech_name} popularity trend"), "Date", "Popularity score (0-100 index)"),
                        use_container_width=True,
                    )
                if "growth" in ts_df.columns:
                    ts_growth = add_percent_column(ts_df, "growth", "growth_percent")
                    st.plotly_chart(
                        style_chart(px.line(ts_growth, x="date", y="growth_percent", title=f"{tech_name} growth trend"), "Date", "Growth (%)"),
                        use_container_width=True,
                    )
                if "hiring" in ts_df.columns:
                    st.plotly_chart(
                        style_chart(px.bar(ts_df, x="date", y="hiring", title=f"{tech_name} hiring demand"), "Date", "Job postings"),
                        use_container_width=True,
                    )
                if "salary" in ts_df.columns:
                    ts_salary = add_salary_k_column(ts_df, "salary", "salary_k")
                    st.plotly_chart(
                        style_chart(px.line(ts_salary, x="date", y="salary_k", title=f"{tech_name} salary trend"), "Date", "Average salary (USD thousands)"),
                        use_container_width=True,
                    )

            regional_payload = api_v1_get(f"/technology/{encoded_name}/regional-comparison")
            regions = regional_payload.get("regions", {}) if regional_payload else {}
            if regions:
                region_df = pd.DataFrame([{"region": key, **val} for key, val in regions.items()])
                st.markdown("**Regional comparison**")
                st.dataframe(region_df, use_container_width=True, hide_index=True)

            combos_payload = api_v1_get(f"/technology/{encoded_name}/skill-combinations")
            combos_df = records_df(combos_payload, "top_combinations")
            if not combos_df.empty:
                st.markdown("**Skill combinations**")
                st.dataframe(combos_df, use_container_width=True, hide_index=True)
    except Exception as exc:
        render_analytics_error(exc)

if auto_refresh and running:
    time.sleep(3)
    rerun()
