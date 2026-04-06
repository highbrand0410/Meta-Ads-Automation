"""Overview page -- KPI cards, summary charts, top/bottom creatives."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import CURRENCY_SYMBOL


st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
st.title("Overview")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please upload a CSV file from the main page.")
    st.stop()

df = st.session_state.df.copy()

# --- KPI Cards Row 1 ---
st.subheader("Key Performance Indicators")
c1, c2, c3, c4, c5, c6 = st.columns(6)

with c1:
    st.metric("Total Spend", f"{CURRENCY_SYMBOL}{df['spend'].sum():,.0f}" if "spend" in df.columns else "N/A")
with c2:
    st.metric("Total Results", f"{df['results'].sum():,.0f}" if "results" in df.columns else "N/A")
with c3:
    st.metric("Avg CPM", f"{CURRENCY_SYMBOL}{df['cpm'].mean():,.2f}" if "cpm" in df.columns else "N/A")
with c4:
    st.metric("Avg CTR", f"{df['ctr'].mean():,.2f}%" if "ctr" in df.columns else "N/A")
with c5:
    st.metric("Avg CPC", f"{CURRENCY_SYMBOL}{df['cpc'].mean():,.2f}" if "cpc" in df.columns else "N/A")
with c6:
    st.metric("Avg Cost/Result", f"{CURRENCY_SYMBOL}{df['cost_per_result'].mean():,.2f}" if "cost_per_result" in df.columns else "N/A")

# --- KPI Cards Row 2 ---
c7, c8, c9, c10, c11, c12 = st.columns(6)
with c7:
    st.metric("Avg Frequency", f"{df['frequency'].mean():,.2f}" if "frequency" in df.columns else "N/A")
with c8:
    if "app_installs" in df.columns and df["app_installs"].sum() > 0:
        st.metric("App Installs", f"{df['app_installs'].sum():,.0f}")
    else:
        st.metric("Total Reach", f"{df['reach'].sum():,.0f}" if "reach" in df.columns else "N/A")
with c9:
    if "landing_page_views" in df.columns:
        st.metric("LP Views", f"{df['landing_page_views'].sum():,.0f}")
    else:
        st.metric("Link Clicks", f"{df['link_clicks'].sum():,.0f}" if "link_clicks" in df.columns else "N/A")
with c10:
    if "outbound_clicks" in df.columns:
        st.metric("Outbound Clicks", f"{df['outbound_clicks'].sum():,.0f}")
    else:
        st.metric("Clicks (All)", f"{df['clicks_all'].sum():,.0f}" if "clicks_all" in df.columns else "N/A")
with c11:
    if "quality_ranking" in df.columns:
        above = df["quality_ranking"].astype(str).str.contains("Above", case=False, na=False).sum()
        st.metric("Above Avg Quality", f"{above}")
    else:
        st.metric("--", "N/A")
with c12:
    # Custom events
    if "px_otp_initiated" in df.columns and df["px_otp_initiated"].sum() > 0:
        st.metric("OTP Initiated", f"{df['px_otp_initiated'].sum():,.0f}")
    elif "partner_onboarding_success" in df.columns and df["partner_onboarding_success"].sum() > 0:
        st.metric("Success Screen", f"{df['partner_onboarding_success'].sum():,.0f}")
    elif "purchase_roas" in df.columns and df["purchase_roas"].notna().any():
        st.metric("Avg ROAS", f"{df['purchase_roas'].mean():,.2f}x")
    else:
        st.metric("Post Engagements", f"{df['post_engagements'].sum():,.0f}" if "post_engagements" in df.columns else "N/A")

st.divider()

# --- Charts Row ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Spend by Campaign Type")
    if "campaign_type" in df.columns and "spend" in df.columns:
        spend_by_type = df.groupby("campaign_type")["spend"].sum().reset_index()
        fig = px.pie(spend_by_type, values="spend", names="campaign_type",
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     hole=0.4)
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Results by Creative Type")
    if "creative_type" in df.columns and "results" in df.columns:
        results_by_type = df.groupby("creative_type")["results"].sum().reset_index()
        fig = px.bar(results_by_type, x="creative_type", y="results",
                     color="creative_type",
                     color_discrete_sequence=["#4338ca", "#7c3aed"])
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300,
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Quality Rankings Distribution ---
if "quality_ranking" in df.columns:
    st.subheader("Ad Quality Rankings")
    qcol1, qcol2, qcol3 = st.columns(3)
    for col_widget, col_name, label in [
        (qcol1, "quality_ranking", "Quality Ranking"),
        (qcol2, "engagement_rate_ranking", "Engagement Ranking"),
        (qcol3, "conversion_rate_ranking", "Conversion Ranking"),
    ]:
        with col_widget:
            if col_name in df.columns:
                rank_counts = df[col_name].value_counts().reset_index()
                rank_counts.columns = ["Ranking", "Count"]
                fig = px.bar(rank_counts, x="Ranking", y="Count", title=label,
                             color="Ranking",
                             color_discrete_map={
                                 "Above Average": "#16a34a",
                                 "Average": "#eab308",
                             })
                fig.update_layout(height=250, margin=dict(t=40, b=20), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    st.divider()

# --- Creative Status Distribution ---
if "creative_status" in df.columns:
    st.subheader("Creative Status Overview")

    status_color_map = {
        "SCALE": "#10b981",
        "MONITOR": "#6366f1",
        "TEST VARIATION": "#eab308",
        "REPLACE": "#f97316",
        "PAUSE": "#ef4444",
        "LEARNING": "#8b5cf6",
    }

    col_chart, col_counts = st.columns([2, 1])
    with col_chart:
        status_counts = df["creative_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.bar(status_counts, x="Status", y="Count",
                     color="Status",
                     color_discrete_map=status_color_map)
        fig.update_layout(height=280, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_counts:
        for status in ["PAUSE", "REPLACE", "SCALE", "TEST VARIATION", "MONITOR", "LEARNING"]:
            count = len(df[df["creative_status"] == status])
            if count > 0:
                color = status_color_map.get(status, "#64748b")
                st.markdown(
                    f'<div style="padding:6px 12px;margin:4px 0;border-left:4px solid {color};'
                    f'background:{color}15;border-radius:4px;">'
                    f'<strong>{status}</strong>: {count} creative{"s" if count > 1 else ""}</div>',
                    unsafe_allow_html=True,
                )

    # Action items summary
    pause_count = len(df[df["creative_status"] == "PAUSE"])
    replace_count = len(df[df["creative_status"] == "REPLACE"])
    scale_count = len(df[df["creative_status"] == "SCALE"])
    if pause_count > 0:
        st.error(f"**Immediate Action:** {pause_count} creative{'s' if pause_count > 1 else ''} should be PAUSED (wasting budget).")
    if replace_count > 0:
        st.warning(f"**Upcoming:** {replace_count} creative{'s' if replace_count > 1 else ''} need REPLACEMENT (old/fatigued).")
    if scale_count > 0:
        st.success(f"**Opportunity:** {scale_count} creative{'s' if scale_count > 1 else ''} are ready to SCALE (increase budget).")

    st.divider()

# --- Top 5 / Bottom 5 ---
if "cost_per_result" in df.columns and "creative_name" in df.columns:
    col_top, col_bottom = st.columns(2)

    valid_df = df[df["cost_per_result"].notna()].copy()

    with col_top:
        st.subheader("Top 5 Creatives (Lowest Cost/Result)")
        top5 = valid_df.nsmallest(5, "cost_per_result")
        display_cols = ["creative_name", "creative_status", "cost_per_result", "ctr", "results", "spend",
                        "frequency", "quality_ranking"]
        available = [c for c in display_cols if c in top5.columns]
        st.dataframe(top5[available].reset_index(drop=True), use_container_width=True, hide_index=True)

    with col_bottom:
        st.subheader("Bottom 5 Creatives (Highest Cost/Result)")
        bottom5 = valid_df.nlargest(5, "cost_per_result")
        st.dataframe(bottom5[available].reset_index(drop=True), use_container_width=True, hide_index=True)

# --- Creatives Count Summary ---
st.divider()
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Total Creatives", len(df))
with c2:
    st.metric("Video Creatives", len(df[df["creative_type"] == "video"]) if "creative_type" in df.columns else 0)
with c3:
    st.metric("Image Creatives", len(df[df["creative_type"] == "image"]) if "creative_type" in df.columns else 0)
with c4:
    if "performance_tier" in df.columns:
        high_count = len(df[df["performance_tier"] == "High Performer"])
        st.metric("High Performers", high_count)
with c5:
    if "performance_tier" in df.columns:
        low_count = len(df[df["performance_tier"] == "Low Performer"])
        st.metric("Low Performers", low_count)
