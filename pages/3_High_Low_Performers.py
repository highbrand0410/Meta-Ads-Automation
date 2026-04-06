"""High/Low Performers — Automated categorization and insights."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.classifier import get_summary, get_insights, classify_performers
from config import CURRENCY_SYMBOL

st.set_page_config(page_title="High/Low Performers", page_icon="🏆", layout="wide")
st.title("High / Low Performers")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()

# --- Metric selector ---
metric = st.selectbox(
    "Classify performers by",
    ["cost_per_result", "ctr", "cpm", "cpc", "hook_rate"],
    format_func=lambda x: {
        "cost_per_result": "Cost per Result",
        "ctr": "CTR",
        "cpm": "CPM",
        "cpc": "CPC",
        "hook_rate": "Hook Rate (Video)",
    }.get(x, x),
)

# Re-classify with selected metric
df = classify_performers(df, metric=metric)

# --- Three-column layout ---
col_high, col_avg, col_low = st.columns(3)

for col, tier, color in [
    (col_high, "High Performer", "#10b981"),
    (col_avg, "Average", "#6366f1"),
    (col_low, "Low Performer", "#ef4444"),
]:
    tier_df = df[df["performance_tier"] == tier]
    with col:
        st.markdown(f"### {tier} ({len(tier_df)})")
        st.markdown(f'<div style="height:4px;background:{color};border-radius:2px;margin-bottom:12px;"></div>',
                    unsafe_allow_html=True)

        if not tier_df.empty:
            display_cols = ["creative_name", "creative_status", "cost_per_result", "ctr", "spend", "results"]
            available = [c for c in display_cols if c in tier_df.columns]
            st.dataframe(
                tier_df[available].reset_index(drop=True),
                use_container_width=True,
                hide_index=True,
                height=300,
            )

            # Averages
            if "spend" in tier_df.columns:
                st.caption(f"Avg Spend: {CURRENCY_SYMBOL}{tier_df['spend'].mean():,.2f}")
            if "cost_per_result" in tier_df.columns:
                st.caption(f"Avg Cost/Result: {CURRENCY_SYMBOL}{tier_df['cost_per_result'].mean():,.2f}")
        else:
            st.info("No creatives in this tier.")

st.divider()

# --- Bar chart comparison ---
st.subheader("Tier Comparison")
summary = get_summary(df)
if summary:
    metrics_to_compare = ["avg_ctr", "avg_cpm", "avg_cost_per_result"]
    for metric_key in metrics_to_compare:
        display_name = metric_key.replace("avg_", "Avg ").replace("_", " ").title()
        values = {tier: summary[tier][metric_key] for tier in ["High Performer", "Average", "Low Performer"]}
        chart_df = pd.DataFrame({"Tier": values.keys(), display_name: values.values()})
        fig = px.bar(chart_df, x="Tier", y=display_name,
                     color="Tier",
                     color_discrete_map={"High Performer": "#10b981", "Average": "#6366f1", "Low Performer": "#ef4444"})
        fig.update_layout(showlegend=False, height=250, margin=dict(t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Insights ---
insights = get_insights(df)

col_w, col_nw = st.columns(2)

with col_w:
    st.subheader("What's Working")
    for insight in insights.get("working", []):
        st.markdown(
            f'<div class="insight-card-working">{insight}</div>',
            unsafe_allow_html=True,
        )

with col_nw:
    st.subheader("What's Not Working")
    for insight in insights.get("not_working", []):
        st.markdown(
            f'<div class="insight-card-not-working">{insight}</div>',
            unsafe_allow_html=True,
        )
