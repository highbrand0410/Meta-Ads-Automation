"""Old vs New — Creative age analysis."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from src.creative_age import compare_old_vs_new, add_age_columns
from config import CURRENCY_SYMBOL

st.set_page_config(page_title="Old vs New", page_icon="📅", layout="wide")
st.title("Old vs New Creatives")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()

# --- Age threshold slider ---
age_threshold = st.slider(
    "Define 'Old' as creatives older than (days):",
    min_value=3, max_value=60, value=14,
)

# Re-compute age buckets with new threshold
df = add_age_columns(df, age_threshold=age_threshold)

# --- Summary ---
new_df = df[df["creative_age_bucket"] == "New"]
old_df = df[df["creative_age_bucket"] == "Old"]
unknown_df = df[df["creative_age_bucket"] == "Unknown"]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("New Creatives", len(new_df))
with col2:
    st.metric("Old Creatives", len(old_df))
with col3:
    st.metric("Unknown Date", len(unknown_df))

st.divider()

# --- Side-by-side comparison ---
if not new_df.empty and not old_df.empty:
    st.subheader("Performance Comparison")

    comparison = compare_old_vs_new(df)

    if not comparison.empty:
        st.dataframe(comparison.round(2), use_container_width=True)

    st.divider()

    # Status breakdown per age bucket
    if "creative_status" in df.columns:
        st.subheader("Status by Age Bucket")
        scol_new, scol_old = st.columns(2)
        status_color_map = {
            "SCALE": "#10b981", "MONITOR": "#6366f1", "TEST VARIATION": "#eab308",
            "REPLACE": "#f97316", "PAUSE": "#ef4444", "LEARNING": "#8b5cf6",
        }
        for scol, label, subset in [(scol_new, "New", new_df), (scol_old, "Old", old_df)]:
            with scol:
                st.markdown(f"**{label} Creatives**")
                if not subset.empty and "creative_status" in subset.columns:
                    for status_name in ["PAUSE", "REPLACE", "SCALE", "TEST VARIATION", "MONITOR", "LEARNING"]:
                        cnt = len(subset[subset["creative_status"] == status_name])
                        if cnt > 0:
                            color = status_color_map.get(status_name, "#64748b")
                            st.markdown(
                                f'<span style="color:{color};font-weight:600;">{status_name}</span>: {cnt}',
                                unsafe_allow_html=True,
                            )
        st.divider()

    # KPI cards side by side
    metrics = [
        ("cpm", "Avg CPM", CURRENCY_SYMBOL),
        ("cpc", "Avg CPC", CURRENCY_SYMBOL),
        ("ctr", "Avg CTR (%)", ""),
        ("cost_per_result", "Avg Cost/Result", CURRENCY_SYMBOL),
        ("frequency", "Avg Frequency", ""),
    ]

    col_new, col_old = st.columns(2)
    with col_new:
        st.markdown("### New Creatives")
        for metric, label, prefix in metrics:
            if metric in new_df.columns:
                val = new_df[metric].mean()
                st.metric(label, f"{prefix}{val:,.2f}" if pd.notna(val) else "N/A")

    with col_old:
        st.markdown("### Old Creatives")
        for metric, label, prefix in metrics:
            if metric in old_df.columns:
                val = old_df[metric].mean()
                st.metric(label, f"{prefix}{val:,.2f}" if pd.notna(val) else "N/A")

    st.divider()

    # --- Scatter plot: Age vs Cost per Result ---
    if "creative_age_days" in df.columns and "cost_per_result" in df.columns:
        st.subheader("Creative Age vs Cost per Result")
        scatter_df = df[df["creative_age_days"].notna() & df["cost_per_result"].notna()]

        if not scatter_df.empty:
            fig = px.scatter(
                scatter_df,
                x="creative_age_days",
                y="cost_per_result",
                color="creative_age_bucket",
                hover_data=["creative_name", "creative_status", "ctr", "spend"],
                color_discrete_map={"New": "#10b981", "Old": "#ef4444", "Unknown": "#94a3b8"},
                labels={"creative_age_days": "Creative Age (Days)", "cost_per_result": "Cost per Result"},
            )
            fig.update_layout(height=400, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # --- Recommendation ---
    st.divider()
    if not old_df.empty and "cost_per_result" in old_df.columns and "cost_per_result" in new_df.columns:
        old_cpr = old_df["cost_per_result"].mean()
        new_cpr = new_df["cost_per_result"].mean()
        if pd.notna(old_cpr) and pd.notna(new_cpr) and new_cpr > 0:
            if old_cpr > new_cpr:
                pct = ((old_cpr - new_cpr) / new_cpr) * 100
                st.warning(f"Old creatives cost {pct:.0f}% more per result than new ones. Consider refreshing creatives older than {age_threshold} days.")
            else:
                st.success("Old creatives are still performing well! No urgent need to refresh.")
else:
    if new_df.empty and old_df.empty:
        st.info("Could not extract dates from creative names. Ensure names contain dates in DDMmmYY format (e.g., 25Sep25).")
    elif new_df.empty:
        st.info("All creatives with extractable dates are older than the threshold.")
    else:
        st.info("All creatives with extractable dates are newer than the threshold.")
