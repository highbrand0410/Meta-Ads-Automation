"""Trends — Daily performance charts from current upload + historical data."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.db import load_historical, get_available_dates
from src.metrics_engine import _safe_divide

st.set_page_config(page_title="Trends", page_icon="📈", layout="wide")
st.title("Performance Trends")

# =====================================================================
# SECTION 1: Daily Trends from Current Upload
# =====================================================================
st.subheader("Daily Trends (Current Upload)")

df_daily = st.session_state.get("df_daily")
if df_daily is not None and "day" in df_daily.columns:
    # Aggregate all creatives by day
    daily_agg = df_daily.groupby("day").agg(
        total_spend=("spend", "sum"),
        total_impressions=("impressions", "sum"),
        total_results=("results", "sum"),
        total_link_clicks=("link_clicks", "sum"),
        total_reach=("reach", "sum"),
        creatives_active=("creative_name", "nunique"),
    ).reset_index()

    # Compute daily ratio metrics from sums
    daily_agg["cpm"] = _safe_divide(daily_agg["total_spend"], daily_agg["total_impressions"]) * 1000
    daily_agg["cpc"] = _safe_divide(daily_agg["total_spend"], daily_agg["total_link_clicks"])
    daily_agg["ctr"] = _safe_divide(daily_agg["total_link_clicks"], daily_agg["total_impressions"]) * 100
    daily_agg["cost_per_result"] = _safe_divide(daily_agg["total_spend"], daily_agg["total_results"])

    # --- Metric selector ---
    metric_options = {
        "total_spend": "Total Spend",
        "total_results": "Total Results",
        "total_impressions": "Total Impressions",
        "total_link_clicks": "Total Link Clicks",
        "cpm": "CPM",
        "cpc": "CPC",
        "ctr": "CTR (%)",
        "cost_per_result": "Cost per Result",
        "creatives_active": "Active Creatives",
    }

    daily_metric = st.selectbox(
        "Portfolio metric",
        list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        key="daily_trend_metric",
    )

    fig = px.line(
        daily_agg, x="day", y=daily_metric,
        title=f"{metric_options[daily_metric]} by Day",
        markers=True,
        color_discrete_sequence=["#4338ca"],
    )
    fig.update_layout(height=400, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # --- Per-creative daily trend ---
    st.subheader("Per-Creative Daily Trend")
    all_creatives = sorted(df_daily["creative_name"].unique().tolist())
    selected_creatives = st.multiselect(
        "Select creatives to compare",
        options=all_creatives,
        default=all_creatives[:3] if len(all_creatives) >= 3 else all_creatives,
        key="daily_creative_select",
    )

    if selected_creatives:
        per_creative_metric = st.selectbox(
            "Metric",
            ["spend", "results", "impressions", "link_clicks", "ctr_raw", "cpm_raw", "cpc_raw"],
            format_func=lambda x: x.replace("_raw", "").replace("_", " ").title(),
            key="daily_per_creative_metric",
        )
        creative_subset = df_daily[df_daily["creative_name"].isin(selected_creatives)]
        if per_creative_metric in creative_subset.columns:
            fig = px.line(
                creative_subset, x="day", y=per_creative_metric,
                color="creative_name",
                title=f"{per_creative_metric.replace('_raw', '').replace('_', ' ').title()} by Day",
                markers=True,
            )
            fig.update_layout(height=450, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # --- Daily summary table ---
    with st.expander("Daily Summary Table"):
        display_daily = daily_agg.copy()
        display_daily["day"] = display_daily["day"].dt.strftime("%d %b %Y")
        st.dataframe(display_daily.round(2), use_container_width=True, hide_index=True)

else:
    st.info("Upload a CSV with a 'Day' column to see daily trends from the current report.")

st.divider()

# =====================================================================
# SECTION 2: Historical Trends (across uploads)
# =====================================================================
st.subheader("Historical Trends (Across Uploads)")

available_dates = get_available_dates()

if len(available_dates) < 2:
    st.info(
        f"Historical trends require at least 2 daily snapshots. Currently have {len(available_dates)}. "
        "Upload CSV reports on different days to build trend data."
    )
    if len(available_dates) == 1:
        st.caption(f"First snapshot: {available_dates[0]}")
    st.stop()

hist_df = load_historical()

if hist_df.empty:
    st.warning("No historical data available.")
    st.stop()

hist_df["snapshot_date"] = pd.to_datetime(hist_df["snapshot_date"])

# --- Date range filter ---
col1, col2 = st.columns(2)
min_date = hist_df["snapshot_date"].min().date()
max_date = hist_df["snapshot_date"].max().date()

with col1:
    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

mask = (hist_df["snapshot_date"].dt.date >= start_date) & (hist_df["snapshot_date"].dt.date <= end_date)
filtered = hist_df[mask]

# --- Creative selector ---
all_creatives = sorted(filtered["creative_name"].unique().tolist())
selected_creatives = st.multiselect(
    "Select creatives to track (leave empty for portfolio average)",
    options=all_creatives,
    key="hist_creative_select",
)

st.divider()

# --- Metric selector ---
metric = st.selectbox(
    "Metric to trend",
    ["cost_per_result", "ctr", "cpm", "cpc", "spend", "results", "frequency",
     "hook_rate", "hold_rate"],
    format_func=lambda x: x.replace("_", " ").title(),
    key="hist_metric",
)

if metric not in filtered.columns:
    st.warning(f"Metric '{metric}' not available in historical data.")
    st.stop()

# --- Portfolio trend ---
if not selected_creatives:
    daily_avg = filtered.groupby("snapshot_date")[metric].mean().reset_index()
    fig = px.line(
        daily_avg, x="snapshot_date", y=metric,
        title=f"Portfolio Average: {metric.replace('_', ' ').title()}",
        markers=True,
        color_discrete_sequence=["#667eea"],
    )
    fig.update_layout(height=400, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    creative_data = filtered[filtered["creative_name"].isin(selected_creatives)]
    fig = px.line(
        creative_data, x="snapshot_date", y=metric,
        color="creative_name",
        title=f"Creative Trends: {metric.replace('_', ' ').title()}",
        markers=True,
    )
    fig.update_layout(height=450, margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Summary stats table ---
st.subheader("Daily Snapshot Summary")
daily_summary = filtered.groupby("snapshot_date").agg(
    creatives=("creative_name", "nunique"),
    total_spend=("spend", "sum"),
    total_results=("results", "sum"),
    avg_cpm=("cpm", "mean"),
    avg_ctr=("ctr", "mean"),
    avg_cost_per_result=("cost_per_result", "mean"),
).reset_index()
daily_summary = daily_summary.sort_values("snapshot_date", ascending=False)
st.dataframe(daily_summary.round(2), use_container_width=True, hide_index=True)
