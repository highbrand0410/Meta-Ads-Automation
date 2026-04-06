"""Meta Ads Creative Performance Dashboard -- Main Entry Point."""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
from datetime import date

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.csv_parser import parse, validate, aggregate_to_creative_level
from src.metrics_engine import compute_all
from src.classifier import classify_performers
from src.creative_age import add_age_columns
from src.suggestions import generate_suggestions
from src.db import init_db, save_daily_snapshot

# --- Page Config ---
st.set_page_config(
    page_title="WeRize Meta Ads Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load CSS ---
css_path = Path(__file__).parent / "styles" / "custom.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# --- Initialize DB ---
init_db()

# --- Sidebar ---
with st.sidebar:
    st.title("WeRize Meta Ads")
    st.caption("Creative Performance Dashboard")
    st.divider()

    # CSV Upload
    uploaded_file = st.file_uploader(
        "Upload Meta Ads CSV Report",
        type=["csv"],
        help="Export your campaign report from Meta Ads Manager as CSV",
    )

    st.divider()

    # Filters (only show when data is loaded)
    if "df" in st.session_state and st.session_state.df is not None:
        df = st.session_state.df

        # Campaign type filter
        campaign_types = ["All"] + sorted(df["campaign_type"].unique().tolist())
        selected_campaign = st.selectbox("Campaign Type", campaign_types)

        # Creative type filter
        creative_types = ["All"] + sorted(df["creative_type"].unique().tolist())
        selected_creative = st.selectbox("Creative Type", creative_types)

        # Platform filter (if available)
        if "platform" in df.columns:
            platforms = ["All"] + sorted(df["platform"].dropna().unique().tolist())
            selected_platform = st.selectbox("Platform", platforms)
            st.session_state.selected_platform = selected_platform

        # Classification metric
        classify_metric = st.selectbox(
            "Classify Performers By",
            ["cost_per_result", "ctr", "cpm", "cpc", "hook_rate", "cost_per_install"],
            format_func=lambda x: {
                "cost_per_result": "Cost per Result",
                "ctr": "CTR",
                "cpm": "CPM",
                "cpc": "CPC",
                "hook_rate": "Hook Rate (Video)",
                "cost_per_install": "Cost per Install",
            }.get(x, x),
        )

        # Age threshold
        age_threshold = st.slider(
            "Creative Age Threshold (days)",
            min_value=3, max_value=60, value=14,
            help="Creatives older than this are 'Old'",
        )

        # Store filter state
        st.session_state.selected_campaign = selected_campaign
        st.session_state.selected_creative = selected_creative
        st.session_state.classify_metric = classify_metric
        st.session_state.age_threshold = age_threshold

    st.divider()
    st.caption("WeRize Partner App | Meta Ads Analyzer")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply sidebar filters to DataFrame."""
    filtered = df.copy()
    if hasattr(st.session_state, "selected_campaign") and st.session_state.selected_campaign != "All":
        filtered = filtered[filtered["campaign_type"] == st.session_state.selected_campaign]
    if hasattr(st.session_state, "selected_creative") and st.session_state.selected_creative != "All":
        filtered = filtered[filtered["creative_type"] == st.session_state.selected_creative]
    if hasattr(st.session_state, "selected_platform") and st.session_state.selected_platform != "All":
        if "platform" in filtered.columns:
            filtered = filtered[filtered["platform"] == st.session_state.selected_platform]
    return filtered


# --- Process uploaded CSV ---
if uploaded_file is not None:
    with st.spinner("Processing CSV..."):
        # Step 1: Parse raw daily data
        df_daily = parse(uploaded_file)
        is_valid, warnings = validate(df_daily)

        if not is_valid:
            st.error("CSV validation failed:")
            for w in warnings:
                st.warning(w)
        else:
            if warnings:
                for w in warnings:
                    st.info(w)

            # Step 2: Aggregate to creative level (SUM volumes, then recalculate ratios)
            df = aggregate_to_creative_level(df_daily)

            # Step 3: Compute derived metrics from aggregated sums
            df = compute_all(df)

            # Step 4: Add age columns
            threshold = getattr(st.session_state, "age_threshold", 14)
            df = add_age_columns(df, age_threshold=threshold)

            # Step 5: Classify performers
            metric = getattr(st.session_state, "classify_metric", "cost_per_result")
            df = classify_performers(df, metric=metric)

            # Step 6: Generate suggestions
            df = generate_suggestions(df)

            # Store BOTH in session state
            st.session_state.df = df                  # Aggregated creative-level
            st.session_state.df_daily = df_daily      # Raw daily data (for trends/drilldown)
            st.session_state.upload_date = date.today()

            # Count unique creatives and date range
            n_creatives = len(df)
            n_daily_rows = len(df_daily)
            date_range = ""
            if "day" in df_daily.columns:
                min_d = df_daily["day"].min()
                max_d = df_daily["day"].max()
                if pd.notna(min_d) and pd.notna(max_d):
                    date_range = f" ({min_d.strftime('%d %b')} - {max_d.strftime('%d %b %Y')})"

            # Save to historical DB (save aggregated creative data)
            save_daily_snapshot(
                df,
                snapshot_date=date.today(),
                file_name=uploaded_file.name,
            )

            st.success(
                f"Loaded **{n_creatives} creatives** from {n_daily_rows} daily rows{date_range}"
            )


# --- Main page content ---
if "df" not in st.session_state or st.session_state.df is None:
    st.title("WeRize Meta Ads Creative Performance Dashboard")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1. Upload CSV")
        st.markdown("Download your campaign report from Meta Ads Manager and upload it via the sidebar.")
    with col2:
        st.markdown("### 2. Auto-Analysis")
        st.markdown("Metrics are computed, creatives classified, and suggestions generated automatically.")
    with col3:
        st.markdown("### 3. Explore Pages")
        st.markdown("Navigate through 8 analysis pages using the sidebar navigation.")

    st.markdown("---")
    st.info("Upload a CSV file from the sidebar to get started.")
else:
    st.title("WeRize Meta Ads Creative Performance Dashboard")
    st.caption(f"Data uploaded: {st.session_state.get('upload_date', 'N/A')}")
    st.markdown("Use the sidebar navigation to explore detailed analysis pages.")

    # Quick summary
    df = apply_filters(st.session_state.df)

    # Row 1: Core KPIs
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("Total Spend", f"\u20b9{df['spend'].sum():,.0f}" if "spend" in df.columns else "N/A")
    with c2:
        st.metric("Total Results", f"{df['results'].sum():,.0f}" if "results" in df.columns else "N/A")
    with c3:
        st.metric("Avg CPM", f"\u20b9{df['cpm'].mean():,.2f}" if "cpm" in df.columns else "N/A")
    with c4:
        st.metric("Avg CTR", f"{df['ctr'].mean():,.2f}%" if "ctr" in df.columns else "N/A")
    with c5:
        st.metric("Avg CPC", f"\u20b9{df['cpc'].mean():,.2f}" if "cpc" in df.columns else "N/A")
    with c6:
        st.metric("Avg Cost/Result", f"\u20b9{df['cost_per_result'].mean():,.2f}" if "cost_per_result" in df.columns else "N/A")

    # Row 2: App + Quality KPIs
    c7, c8, c9, c10, c11 = st.columns(5)
    with c7:
        st.metric("Avg Frequency", f"{df['frequency'].mean():,.2f}" if "frequency" in df.columns else "N/A")
    with c8:
        if "app_installs" in df.columns:
            st.metric("App Installs", f"{df['app_installs'].sum():,.0f}")
        elif "results" in df.columns:
            st.metric("Total Impressions", f"{df['impressions'].sum():,.0f}")
    with c9:
        if "landing_page_views" in df.columns:
            st.metric("Landing Page Views", f"{df['landing_page_views'].sum():,.0f}")
        else:
            st.metric("Reach", f"{df['reach'].sum():,.0f}" if "reach" in df.columns else "N/A")
    with c10:
        if "quality_ranking" in df.columns:
            below = df["quality_ranking"].astype(str).str.contains("Below", case=False, na=False).sum()
            st.metric("Below Avg Quality", f"{below} ads")
        else:
            st.metric("Total Creatives", len(df))
    with c11:
        # Custom events summary
        otp_col = "px_otp_initiated"
        ss_col = "partner_onboarding_success"
        if otp_col in df.columns and df[otp_col].sum() > 0:
            st.metric("OTP Initiated", f"{df[otp_col].sum():,.0f}")
        elif ss_col in df.columns and df[ss_col].sum() > 0:
            st.metric("Success Screen", f"{df[ss_col].sum():,.0f}")
        else:
            st.metric("Total Creatives", len(df))

    # Row 3: Creative Status summary
    if "creative_status" in df.columns:
        st.divider()
        st.subheader("Action Required")
        status_cols = st.columns(6)
        status_config = [
            ("PAUSE", "#ef4444", "Pause"),
            ("REPLACE", "#f97316", "Replace"),
            ("SCALE", "#10b981", "Scale"),
            ("TEST VARIATION", "#eab308", "Test"),
            ("MONITOR", "#6366f1", "Monitor"),
            ("LEARNING", "#8b5cf6", "Learning"),
        ]
        for i, (status, color, label) in enumerate(status_config):
            count = len(df[df["creative_status"] == status])
            with status_cols[i]:
                st.markdown(
                    f'<div style="text-align:center;padding:8px;border-radius:8px;'
                    f'border:2px solid {color};background:{color}10;">'
                    f'<div style="font-size:1.8em;font-weight:700;color:{color};">{count}</div>'
                    f'<div style="font-size:0.85em;color:#475569;">{label}</div></div>',
                    unsafe_allow_html=True,
                )

    # Row 4: Daily data info
    if "df_daily" in st.session_state and st.session_state.df_daily is not None:
        df_daily = st.session_state.df_daily
        if "day" in df_daily.columns:
            n_days = df_daily["day"].nunique()
            st.caption(f"Data covers {n_days} days | {len(df)} unique creatives | {len(df_daily)} daily rows aggregated")
