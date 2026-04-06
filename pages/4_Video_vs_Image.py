"""Video vs Image -- Format-level comparison."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import CURRENCY_SYMBOL

st.set_page_config(page_title="Video vs Image", page_icon="🎬", layout="wide")
st.title("Video vs Image Performance")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()
video_df = df[df["creative_type"] == "video"]
image_df = df[df["creative_type"] == "image"]

# --- Side-by-side KPI comparison ---
st.subheader("Head-to-Head Comparison")

metrics_compare = [
    ("spend", "Total Spend", CURRENCY_SYMBOL, True),
    ("results", "Total Results", "", True),
    ("cpm", "Avg CPM", CURRENCY_SYMBOL, False),
    ("cpc", "Avg CPC", CURRENCY_SYMBOL, False),
    ("ctr", "Avg CTR (%)", "", False),
    ("cost_per_result", "Avg Cost/Result", CURRENCY_SYMBOL, False),
    ("frequency", "Avg Frequency", "", False),
    ("landing_page_views", "LP Views", "", True),
]

col_v, col_i = st.columns(2)
with col_v:
    st.markdown("### Video Creatives")
    st.caption(f"{len(video_df)} creatives")
with col_i:
    st.markdown("### Image Creatives")
    st.caption(f"{len(image_df)} creatives")

for metric, label, prefix, is_sum in metrics_compare:
    if metric not in df.columns:
        continue
    cv, ci = st.columns(2)
    with cv:
        val = video_df[metric].sum() if is_sum else video_df[metric].mean()
        st.metric(label, f"{prefix}{val:,.2f}" if pd.notna(val) else "N/A")
    with ci:
        val = image_df[metric].sum() if is_sum else image_df[metric].mean()
        st.metric(label, f"{prefix}{val:,.2f}" if pd.notna(val) else "N/A")

st.divider()

# --- Status breakdown per format ---
if "creative_status" in df.columns:
    st.subheader("Creative Status by Format")
    sc1, sc2 = st.columns(2)
    for scol, label, subset in [(sc1, "Video", video_df), (sc2, "Image", image_df)]:
        with scol:
            if not subset.empty:
                st.markdown(f"**{label} ({len(subset)})**")
                status_counts = subset["creative_status"].value_counts()
                status_color_map = {
                    "SCALE": "#10b981", "MONITOR": "#6366f1", "TEST VARIATION": "#eab308",
                    "REPLACE": "#f97316", "PAUSE": "#ef4444", "LEARNING": "#8b5cf6",
                }
                for status_name in ["PAUSE", "REPLACE", "SCALE", "TEST VARIATION", "MONITOR", "LEARNING"]:
                    count = status_counts.get(status_name, 0)
                    if count > 0:
                        color = status_color_map.get(status_name, "#64748b")
                        st.markdown(
                            f'<span style="color:{color};font-weight:600;">{status_name}</span>: {count}',
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"No {label.lower()} creatives.")
    st.divider()

# --- Video Completion Funnel ---
if not video_df.empty:
    st.subheader("Video Completion Funnel")
    funnel_metrics = []
    funnel_labels = []

    if "impressions" in video_df.columns:
        funnel_metrics.append(video_df["impressions"].sum())
        funnel_labels.append("Impressions")
    if "video_2s_continuous" in video_df.columns:
        funnel_metrics.append(video_df["video_2s_continuous"].sum())
        funnel_labels.append("2s Continuous Views")
    if "video_3s_views" in video_df.columns:
        funnel_metrics.append(video_df["video_3s_views"].sum())
        funnel_labels.append("3-sec Views")
    for pct, label in [("video_p25", "25%"), ("video_p50", "50%"), ("video_p75", "75%"), ("video_p95", "95%"), ("video_p100", "100%")]:
        if pct in video_df.columns:
            funnel_metrics.append(video_df[pct].sum())
            funnel_labels.append(f"Watched {label}")
    if "thruplay" in video_df.columns and "video_p25" not in video_df.columns:
        funnel_metrics.append(video_df["thruplay"].sum())
        funnel_labels.append("ThruPlays")

    if len(funnel_metrics) > 1:
        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_metrics,
            textinfo="value+percent initial",
            marker=dict(color=["#4338ca", "#5b21b6", "#7c3aed", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe", "#ede9fe"]),
        ))
        fig.update_layout(height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # Video-specific metrics
    st.subheader("Video Metrics Distribution")
    vcol1, vcol2, vcol3 = st.columns(3)

    with vcol1:
        if "hook_rate" in video_df.columns:
            fig = px.histogram(video_df, x="hook_rate", nbins=15,
                               title="Hook Rate Distribution",
                               color_discrete_sequence=["#4338ca"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with vcol2:
        if "hold_rate" in video_df.columns:
            fig = px.histogram(video_df, x="hold_rate", nbins=15,
                               title="Hold Rate Distribution",
                               color_discrete_sequence=["#7c3aed"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with vcol3:
        if "scroll_stop_rate" in video_df.columns:
            fig = px.histogram(video_df, x="scroll_stop_rate", nbins=15,
                               title="Scroll-Stop Rate Distribution",
                               color_discrete_sequence=["#a855f7"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Image metrics ---
if not image_df.empty:
    st.subheader("Image Metrics Distribution")
    icol1, icol2, icol3 = st.columns(3)

    with icol1:
        if "ctr" in image_df.columns:
            fig = px.histogram(image_df, x="ctr", nbins=15,
                               title="CTR Distribution (Images)",
                               color_discrete_sequence=["#16a34a"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with icol2:
        if "engagement_rate" in image_df.columns:
            fig = px.histogram(image_df, x="engagement_rate", nbins=15,
                               title="Engagement Rate Distribution (Images)",
                               color_discrete_sequence=["#eab308"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)

    with icol3:
        if "conversion_rate" in image_df.columns:
            fig = px.histogram(image_df, x="conversion_rate", nbins=15,
                               title="Conversion Rate Distribution (Images)",
                               color_discrete_sequence=["#0ea5e9"])
            fig.update_layout(height=300, margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
