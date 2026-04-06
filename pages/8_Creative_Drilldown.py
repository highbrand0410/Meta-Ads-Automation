"""Creative Drilldown -- Single creative deep dive."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.db import get_creative_history
from src.metrics_engine import _safe_divide
from config import CURRENCY_SYMBOL

st.set_page_config(page_title="Creative Drilldown", page_icon="🔍", layout="wide")
st.title("Creative Drilldown")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()

# --- Creative selector ---
creative_names = sorted(df["creative_name"].unique().tolist())
selected = st.selectbox("Select a creative", creative_names)

if not selected:
    st.stop()

creative = df[df["creative_name"] == selected].iloc[0]

# --- Status banner ---
status = creative.get("creative_status", "")
status_colors = {
    "SCALE": ("#10b981", "#ecfdf5", "Increase budget and create similar variations."),
    "MONITOR": ("#6366f1", "#eef2ff", "No action needed right now. Keep watching."),
    "TEST VARIATION": ("#eab308", "#fefce8", "Has potential. Test new angles/hooks to improve."),
    "REPLACE": ("#f97316", "#fff7ed", "Old or fatigued. Prepare a fresh replacement."),
    "PAUSE": ("#ef4444", "#fef2f2", "Wasting budget. Stop spend immediately."),
    "LEARNING": ("#8b5cf6", "#f5f3ff", "Too new/limited data. Let Meta's algorithm learn."),
}
if status in status_colors:
    border_c, bg_c, desc = status_colors[status]
    st.markdown(
        f'<div style="padding:12px 20px;border-left:5px solid {border_c};background:{bg_c};'
        f'border-radius:6px;margin-bottom:16px;">'
        f'<span style="font-size:1.3em;font-weight:700;color:{border_c};">{status}</span>'
        f'<span style="margin-left:12px;color:#475569;">{desc}</span></div>',
        unsafe_allow_html=True,
    )

# --- Creative info header ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"**Creative:** {selected}")
    if "campaign_name" in creative.index:
        st.caption(f"Campaign: {creative.get('campaign_name', 'N/A')}")
with col2:
    st.markdown(f"**Type:** {creative.get('creative_type', 'N/A')}")
    st.caption(f"Campaign Type: {creative.get('campaign_type', 'N/A')}")
with col3:
    st.markdown(f"**Tier:** {creative.get('performance_tier', 'N/A')}")
    age = creative.get("creative_age_days")
    st.caption(f"Age: {int(age)} days" if pd.notna(age) else "Age: Unknown")
with col4:
    # Quality rankings
    qr = creative.get("quality_ranking", "N/A")
    er = creative.get("engagement_rate_ranking", "N/A")
    cr = creative.get("conversion_rate_ranking", "N/A")
    st.markdown(f"**Quality:** {qr}")
    st.caption(f"Engagement: {er} | Conversion: {cr}")

st.divider()

# --- Suggestion ---
suggestion = creative.get("suggestion", "")
if suggestion:
    st.subheader("Suggestion")
    st.markdown(f'<div class="suggestion-text">{suggestion}</div>', unsafe_allow_html=True)
    st.divider()

# --- KPI Cards Row 1 ---
st.subheader("Performance Metrics")

metrics_row1 = [
    ("spend", "Spend", CURRENCY_SYMBOL),
    ("impressions", "Impressions", ""),
    ("reach", "Reach", ""),
    ("results", "Results", ""),
    ("cpm", "CPM", CURRENCY_SYMBOL),
    ("cpc", "CPC", CURRENCY_SYMBOL),
    ("ctr", "CTR (%)", ""),
    ("cost_per_result", "Cost/Result", CURRENCY_SYMBOL),
    ("frequency", "Frequency", ""),
]

cols = st.columns(5)
for i, (key, label, prefix) in enumerate(metrics_row1):
    val = creative.get(key)
    with cols[i % 5]:
        if pd.notna(val):
            st.metric(label, f"{prefix}{val:,.2f}")
        else:
            st.metric(label, "N/A")

# --- KPI Cards Row 2 (App & Engagement) ---
metrics_row2 = [
    ("link_clicks", "Link Clicks", ""),
    ("outbound_clicks", "Outbound Clicks", ""),
    ("landing_page_views", "LP Views", ""),
    ("lp_conversion_rate", "LP Conv Rate (%)", ""),
    ("app_installs", "App Installs", ""),
    ("cost_per_install", "Cost/Install", CURRENCY_SYMBOL),
    ("leads", "Leads", ""),
    ("registrations", "Registrations", ""),
    ("post_engagements", "Engagements", ""),
    ("post_saves", "Saves", ""),
    ("px_otp_initiated", "OTP Initiated", ""),
    ("partner_onboarding_success", "Success Screen", ""),
]

available_row2 = [(k, l, p) for k, l, p in metrics_row2 if k in creative.index and pd.notna(creative.get(k))]
if available_row2:
    st.divider()
    cols2 = st.columns(5)
    for i, (key, label, prefix) in enumerate(available_row2):
        val = creative.get(key)
        with cols2[i % 5]:
            st.metric(label, f"{prefix}{val:,.2f}")

st.divider()

# --- Video-specific section ---
if creative.get("creative_type") == "video":
    st.subheader("Video Metrics")

    vcols = st.columns(5)
    video_metrics = [
        ("hook_rate", "Hook Rate (%)", ""),
        ("hold_rate", "Hold Rate (%)", ""),
        ("scroll_stop_rate", "Scroll-Stop (%)", ""),
        ("cost_per_thruplay", "Cost/ThruPlay", CURRENCY_SYMBOL),
        ("video_completion_rate", "Completion Rate (%)", ""),
    ]
    for i, (key, label, prefix) in enumerate(video_metrics):
        val = creative.get(key)
        with vcols[i]:
            if pd.notna(val):
                st.metric(label, f"{prefix}{val:,.2f}")
            else:
                st.metric(label, "N/A")

    # Additional video stats
    vcols2 = st.columns(4)
    extra_video = [
        ("video_3s_views", "3s Views", ""),
        ("video_2s_continuous", "2s Continuous", ""),
        ("thruplay", "ThruPlays", ""),
        ("video_avg_play_time", "Avg Play Time", ""),
    ]
    for i, (key, label, prefix) in enumerate(extra_video):
        val = creative.get(key)
        with vcols2[i]:
            if pd.notna(val):
                st.metric(label, f"{prefix}{val:,.2f}")
            else:
                st.metric(label, "N/A")

    # Completion funnel
    funnel_data = []
    funnel_labels = []
    for col, label in [
        ("impressions", "Impressions"),
        ("video_2s_continuous", "2s Continuous"),
        ("video_3s_views", "3s Views"),
        ("video_p25", "25% Watched"),
        ("video_p50", "50% Watched"),
        ("video_p75", "75% Watched"),
        ("video_p95", "95% Watched"),
        ("video_p100", "100% Watched"),
    ]:
        val = creative.get(col)
        if pd.notna(val) and val > 0:
            funnel_data.append(val)
            funnel_labels.append(label)

    if len(funnel_data) > 1:
        st.subheader("Completion Funnel")
        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_data,
            textinfo="value+percent initial",
            marker=dict(color=["#4338ca", "#5b21b6", "#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe"]),
        ))
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Daily Performance Trend (from current CSV data) ---
st.subheader("Daily Performance (Current Upload)")

df_daily = st.session_state.get("df_daily")
if df_daily is not None and "day" in df_daily.columns:
    creative_daily = df_daily[df_daily["creative_name"] == selected].copy()
    creative_daily = creative_daily.sort_values("day")

    if len(creative_daily) >= 2:
        trend_metric = st.selectbox(
            "Metric to track (daily)",
            ["spend", "results", "impressions", "link_clicks", "app_installs",
             "cost_per_result_raw", "ctr_raw", "cpm_raw", "cpc_raw"],
            format_func=lambda x: x.replace("_raw", "").replace("_", " ").title(),
            key="drilldown_daily_metric",
        )

        if trend_metric in creative_daily.columns:
            fig = px.line(
                creative_daily, x="day", y=trend_metric,
                markers=True,
                title=f"{trend_metric.replace('_raw', '').replace('_', ' ').title()} by Day",
                color_discrete_sequence=["#4338ca"],
            )
            fig.update_layout(height=350, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"Metric '{trend_metric}' not available for this creative.")

        # Daily data table
        with st.expander("View Daily Data"):
            daily_display_cols = ["day", "spend", "impressions", "results", "link_clicks",
                                  "ctr_raw", "cpm_raw", "cpc_raw"]
            avail_cols = [c for c in daily_display_cols if c in creative_daily.columns]
            st.dataframe(
                creative_daily[avail_cols].round(2),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Only 1 day of data for this creative. Daily trends need 2+ days.")
else:
    st.info("Daily data not available. Upload a CSV with a 'Day' column for daily trends.")

st.divider()

# --- Historical trend (from SQLite, across uploads) ---
st.subheader("Historical Performance (Across Uploads)")
history = get_creative_history(selected)

if history.empty or len(history) < 2:
    st.info("Historical data will appear here after multiple daily uploads containing this creative.")
else:
    history["snapshot_date"] = pd.to_datetime(history["snapshot_date"])

    trend_metric = st.selectbox(
        "Metric to track",
        ["cost_per_result", "ctr", "cpm", "cpc", "spend", "results",
         "hook_rate", "hold_rate", "frequency"],
        format_func=lambda x: x.replace("_", " ").title(),
        key="drilldown_trend_metric",
    )

    if trend_metric in history.columns:
        fig = px.line(
            history, x="snapshot_date", y=trend_metric,
            markers=True,
            title=f"{trend_metric.replace('_', ' ').title()} Over Time",
            color_discrete_sequence=["#4338ca"],
        )
        fig.update_layout(height=350, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
