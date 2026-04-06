"""CSV ingestion, column normalization, type detection, and creative-level aggregation."""

import re
import pandas as pd
import numpy as np
from config import COLUMN_MAP, REQUIRED_COLUMNS, VIDEO_METRIC_COLUMNS, CAMPAIGN_TYPE_KEYWORDS


def parse(uploaded_file) -> pd.DataFrame:
    """Read CSV, normalize column names, coerce numeric types."""
    df = pd.read_csv(uploaded_file)

    # Normalize column names using COLUMN_MAP
    df = _normalize_columns(df)

    # Unify results column: Results if numeric, else Mobile app installs
    df = _unify_results(df)

    # Coerce numeric columns
    df = _coerce_numerics(df)

    # Parse date columns
    df = _parse_dates(df)

    # Detect creative and campaign types (per-row, before aggregation)
    df = detect_creative_type(df)
    df = detect_campaign_type(df)

    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map Meta CSV headers to internal canonical names."""
    rename_map = {}
    for original_col in df.columns:
        col_lower = original_col.strip().lower()
        # Exact match first
        if col_lower in COLUMN_MAP:
            rename_map[original_col] = COLUMN_MAP[col_lower]
        else:
            # Substring match (handles currency suffixes like "Amount Spent (INR)")
            for key, canonical in COLUMN_MAP.items():
                if key in col_lower:
                    rename_map[original_col] = canonical
                    break

    df = df.rename(columns=rename_map)
    return df


def _unify_results(df: pd.DataFrame) -> pd.DataFrame:
    """Unify results: use results_raw if numeric, else fall back to app_installs.

    Business rule: if the Results column has a numeric value for a creative,
    treat that as the install/result count. Otherwise, use Mobile app installs.
    """
    if "results_raw" not in df.columns:
        # If there's no results column at all, try app_installs
        if "app_installs" in df.columns:
            df["results"] = pd.to_numeric(df["app_installs"], errors="coerce")
        return df

    # Try to coerce results_raw to numeric
    results_numeric = pd.to_numeric(
        df["results_raw"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    )

    if "app_installs" in df.columns:
        installs_numeric = pd.to_numeric(
            df["app_installs"].astype(str).str.replace(",", "").str.strip(),
            errors="coerce"
        )
        # Use results_raw if it's a valid number, otherwise use app_installs
        df["results"] = np.where(
            results_numeric.notna() & (results_numeric > 0),
            results_numeric,
            installs_numeric,
        )
    else:
        df["results"] = results_numeric

    return df


def _coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Convert string numbers (with commas, currency symbols) to float."""
    numeric_cols = [
        # Core
        "spend", "impressions", "reach", "link_clicks", "clicks_all",
        "results", "frequency_raw", "cost_per_result_raw", "ctr_raw",
        "ctr_all_raw", "cpc_raw", "cpc_all_raw", "cpm_raw",
        # Video
        "video_3s_views", "video_2s_continuous", "thruplay", "video_plays",
        "video_p25", "video_p50", "video_p75", "video_p95", "video_p100",
        "video_avg_play_time", "video_pct_watched",
        "cost_per_thruplay_raw", "cost_per_3s_play", "cost_per_2s_play",
        "unique_3s_views", "unique_2s_continuous",
        # Engagement
        "post_engagements", "post_reactions", "post_comments",
        "post_shares", "post_saves", "page_engagement", "page_likes",
        # Clicks extended
        "unique_link_clicks", "unique_clicks_all",
        "outbound_clicks", "unique_outbound_clicks",
        "outbound_ctr_raw", "cost_per_outbound_click",
        "unique_ctr", "unique_ctr_all",
        "cost_per_unique_click_all", "cost_per_unique_link_click",
        "cost_per_1k_reached",
        # App
        "app_installs", "cost_per_install_raw", "app_store_clicks",
        "mobile_app_actions", "mobile_app_roas",
        "mobile_app_purchases", "mobile_app_purchase_value",
        "desktop_app_installs",
        # Conversions
        "result_rate_raw", "leads", "cost_per_lead",
        "registrations", "cost_per_registration",
        "purchases", "cost_per_purchase", "purchase_value", "purchase_roas",
        "add_to_cart", "cost_per_add_to_cart",
        "checkouts_initiated", "cost_per_checkout",
        "adds_payment_info", "cost_per_add_payment_info",
        "content_views", "cost_per_content_view",
        # Attribution
        "results_1d_click", "results_7d_click", "results_1d_view", "results_28d_click",
        # Landing page
        "landing_page_views", "cost_per_lpv", "unique_landing_page_views",
        # Custom events
        "px_otp_initiated", "partner_onboarding_success",
        # New 2025-2026
        "engaged_view_conversions", "cost_per_engaged_view",
        "incremental_conversions", "conversion_leads", "cost_per_conversion_lead",
        "ig_profile_visits", "messaging_conversations",
        # Other
        "ad_recall_lift", "ad_recall_lift_rate",
        "campaign_budget", "ad_set_budget", "bid_amount",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("\u20b9", "", regex=False)
                .str.replace("$", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse date columns into datetime."""
    date_cols = ["reporting_starts", "reporting_ends", "day",
                 "campaign_start_date", "campaign_end_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def detect_creative_type(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'creative_type' column: 'video' or 'image'."""
    def _classify(row):
        for col in VIDEO_METRIC_COLUMNS:
            if col in df.columns and pd.notna(row.get(col)) and row.get(col, 0) > 0:
                return "video"
        return "image"

    df["creative_type"] = df.apply(_classify, axis=1)
    return df


def detect_campaign_type(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'campaign_type' column based on campaign name, objective, or result type."""
    def _classify(row):
        text = ""
        if "campaign_name" in df.columns and pd.notna(row.get("campaign_name")):
            text += str(row["campaign_name"]).lower()
        if "objective" in df.columns and pd.notna(row.get("objective")):
            text += " " + str(row["objective"]).lower()
        if "optimization_goal" in df.columns and pd.notna(row.get("optimization_goal")):
            text += " " + str(row["optimization_goal"]).lower()

        for ctype, keywords in CAMPAIGN_TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return ctype

        # Fallback: use result_type to infer campaign type
        result_type = row.get("result_type")
        if pd.notna(result_type):
            rt_lower = str(result_type).lower()
            if "install" in rt_lower:
                return "app_install"
            elif "otp" in rt_lower or "success" in rt_lower or "onboarding" in rt_lower:
                return "app_event"

        return "other"

    df["campaign_type"] = df.apply(_classify, axis=1)
    return df


def aggregate_to_creative_level(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily rows to creative-level summary.

    Volume metrics are SUMMED. Ratio metrics are RECALCULATED from summed volumes.
    Text/categorical columns take the first non-null value.
    Quality rankings take the most common (mode) value.
    """
    if df.empty:
        return df

    # --- Define column groups ---
    sum_cols = [
        "spend", "impressions", "reach", "results", "link_clicks", "clicks_all",
        "outbound_clicks", "unique_outbound_clicks",
        "unique_link_clicks", "unique_clicks_all",
        "video_3s_views", "video_2s_continuous", "thruplay", "video_plays",
        "video_p25", "video_p50", "video_p75", "video_p95", "video_p100",
        "post_engagements", "post_reactions", "post_comments",
        "post_shares", "post_saves", "page_engagement", "page_likes",
        "app_installs", "app_store_clicks", "mobile_app_actions",
        "leads", "registrations", "purchases", "purchase_value",
        "landing_page_views", "unique_landing_page_views",
        "add_to_cart", "checkouts_initiated", "adds_payment_info",
        "content_views",
        "px_otp_initiated", "partner_onboarding_success",
        "engaged_view_conversions", "incremental_conversions",
        "conversion_leads",
    ]

    # Text/categorical - take first non-null
    text_cols = [
        "campaign_name", "ad_set_name", "campaign_type", "creative_type",
        "campaign_id", "ad_set_id", "ad_id",
        "objective", "attribution_setting", "delivery_status",
        "result_type",
    ]

    # Quality rankings - take mode (most common value)
    ranking_cols = ["quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]

    # Build aggregation dict
    agg_dict = {}
    for col in sum_cols:
        if col in df.columns:
            agg_dict[col] = "sum"

    # Weighted average for video_avg_play_time
    if "video_avg_play_time" in df.columns:
        agg_dict["video_avg_play_time"] = "mean"

    for col in text_cols:
        if col in df.columns:
            agg_dict[col] = "first"

    for col in ranking_cols:
        if col in df.columns:
            agg_dict[col] = _safe_mode

    # Count days (for reference)
    if "day" in df.columns:
        agg_dict["day"] = "nunique"

    # Aggregate
    available_agg = {k: v for k, v in agg_dict.items() if k in df.columns}
    agg_df = df.groupby("creative_name", as_index=False).agg(available_agg)

    # Rename day count
    if "day" in agg_df.columns:
        agg_df = agg_df.rename(columns={"day": "days_active"})

    # --- Weighted average for video_avg_play_time ---
    if "video_avg_play_time" in df.columns and "impressions" in df.columns:
        weighted = df.dropna(subset=["video_avg_play_time", "impressions"])
        if not weighted.empty and weighted["impressions"].sum() > 0:
            wavg = weighted.groupby("creative_name").apply(
                lambda g: np.average(g["video_avg_play_time"], weights=g["impressions"])
                if g["impressions"].sum() > 0 else np.nan,
                include_groups=False,
            ).reset_index()
            wavg.columns = ["creative_name", "video_avg_play_time"]
            agg_df = agg_df.drop(columns=["video_avg_play_time"], errors="ignore")
            agg_df = agg_df.merge(wavg, on="creative_name", how="left")

    # --- Detect creative type from aggregated data ---
    # A creative is "video" if it has ANY video metric > 0 across all days
    video_indicators = ["video_3s_views", "thruplay", "video_p25", "video_2s_continuous", "video_plays"]
    available_video = [c for c in video_indicators if c in agg_df.columns]
    if available_video:
        video_mask = agg_df[available_video].fillna(0).sum(axis=1) > 0
        agg_df["creative_type"] = np.where(video_mask, "video", "image")

    return agg_df


def _safe_mode(series):
    """Return mode of series, falling back to first value."""
    cleaned = series.dropna()
    if cleaned.empty:
        return None
    mode = cleaned.mode()
    if not mode.empty:
        return mode.iloc[0]
    return cleaned.iloc[0]


def validate(df: pd.DataFrame) -> tuple:
    """Check for required columns. Returns (is_valid, warnings)."""
    warnings = []
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]

    if missing:
        warnings.append(f"Missing required columns: {', '.join(missing)}")
        return False, warnings

    if df.empty:
        warnings.append("CSV file is empty (no data rows).")
        return False, warnings

    # Check for video columns
    has_video_cols = any(c in df.columns for c in VIDEO_METRIC_COLUMNS)
    if not has_video_cols:
        warnings.append("No video metric columns found. Video-specific analysis will be unavailable.")

    if "results" not in df.columns:
        warnings.append("'Results' column not found. Cost per result analysis will be unavailable.")

    # Check for quality ranking columns
    quality_cols = ["quality_ranking", "engagement_rate_ranking", "conversion_rate_ranking"]
    has_quality = any(c in df.columns for c in quality_cols)
    if not has_quality:
        warnings.append("Quality ranking columns not found. Add them in Meta Ads Manager for ad quality insights.")

    # Check for landing page views
    if "landing_page_views" not in df.columns:
        warnings.append("Landing page views column not found. Add it for post-click analysis.")

    return True, warnings
