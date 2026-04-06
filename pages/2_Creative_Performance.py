"""Creative Performance -- Full interactive table with filters and suggestions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from config import METRIC_DISPLAY_NAMES

st.set_page_config(page_title="Creative Performance", page_icon="📋", layout="wide")
st.title("Creative Performance Table")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()

# --- Filters ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    campaign_filter = st.multiselect(
        "Campaign Type",
        options=df["campaign_type"].unique().tolist() if "campaign_type" in df.columns else [],
        default=df["campaign_type"].unique().tolist() if "campaign_type" in df.columns else [],
    )

with col2:
    creative_filter = st.multiselect(
        "Creative Type",
        options=df["creative_type"].unique().tolist() if "creative_type" in df.columns else [],
        default=df["creative_type"].unique().tolist() if "creative_type" in df.columns else [],
    )

with col3:
    tier_filter = st.multiselect(
        "Performance Tier",
        options=df["performance_tier"].unique().tolist() if "performance_tier" in df.columns else [],
        default=df["performance_tier"].unique().tolist() if "performance_tier" in df.columns else [],
    )

with col4:
    if "quality_ranking" in df.columns:
        quality_filter = st.multiselect(
            "Quality Ranking",
            options=df["quality_ranking"].dropna().unique().tolist(),
            default=df["quality_ranking"].dropna().unique().tolist(),
        )
    else:
        quality_filter = None

# Apply filters
filtered = df.copy()
if campaign_filter and "campaign_type" in filtered.columns:
    filtered = filtered[filtered["campaign_type"].isin(campaign_filter)]
if creative_filter and "creative_type" in filtered.columns:
    filtered = filtered[filtered["creative_type"].isin(creative_filter)]
if tier_filter and "performance_tier" in filtered.columns:
    filtered = filtered[filtered["performance_tier"].isin(tier_filter)]
if quality_filter is not None and "quality_ranking" in filtered.columns:
    filtered = filtered[filtered["quality_ranking"].isin(quality_filter)]

# --- Status filter ---
if "creative_status" in df.columns:
    status_filter = st.multiselect(
        "Creative Status",
        options=sorted(df["creative_status"].dropna().unique().tolist()),
        default=sorted(df["creative_status"].dropna().unique().tolist()),
    )
    if status_filter:
        filtered = filtered[filtered["creative_status"].isin(status_filter)]

# --- Column selector ---
all_columns = [
    "creative_name", "campaign_name", "ad_set_name", "campaign_type", "creative_type",
    "spend", "impressions", "reach", "results", "link_clicks", "clicks_all",
    "cpm", "cpc", "ctr", "cost_per_result", "frequency",
    "outbound_clicks", "outbound_ctr", "landing_page_views", "cost_per_lpv", "lp_conversion_rate",
    "hook_rate", "hold_rate", "scroll_stop_rate", "cost_per_thruplay", "video_completion_rate",
    "video_3s_views", "video_2s_continuous", "thruplay",
    "video_p25", "video_p50", "video_p75", "video_p95", "video_p100",
    "video_avg_play_time", "video_pct_watched",
    "engagement_rate", "conversion_rate", "post_engagements",
    "post_reactions", "post_comments", "post_shares", "post_saves",
    "app_installs", "cost_per_install", "cost_per_action",
    "leads", "cost_per_lead", "registrations", "cost_per_registration",
    "purchases", "cost_per_purchase", "purchase_value", "purchase_roas",
    "px_otp_initiated", "partner_onboarding_success",
    "quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking",
    "performance_tier", "creative_status", "creative_age_days", "creative_age_bucket",
    "days_active",
    "platform", "placement",
    "suggestion",
]

available_columns = [c for c in all_columns if c in filtered.columns]

default_columns = [
    "creative_name", "creative_status", "campaign_type", "creative_type", "spend", "results",
    "cpm", "cpc", "ctr", "cost_per_result", "frequency",
    "quality_ranking", "performance_tier", "suggestion",
]
default_selected = [c for c in default_columns if c in available_columns]

selected_columns = st.multiselect(
    "Columns to display",
    options=available_columns,
    default=default_selected,
)

# --- Sort options ---
sort_col = st.selectbox(
    "Sort by",
    options=selected_columns if selected_columns else ["creative_name"],
    index=0,
)
sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True, index=1)

# --- Display table ---
st.subheader(f"Showing {len(filtered)} creatives")

if selected_columns:
    display_df = filtered[selected_columns].reset_index(drop=True)
    if sort_col in display_df.columns:
        display_df = display_df.sort_values(sort_col, ascending=(sort_order == "Ascending"), na_position="last")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=600,
    )

    # --- Export ---
    csv_data = filtered[selected_columns].to_csv(index=False)
    st.download_button(
        "Download as CSV",
        data=csv_data,
        file_name="creative_performance.csv",
        mime="text/csv",
    )
else:
    st.info("Select at least one column to display.")
