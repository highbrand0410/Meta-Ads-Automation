"""Compute derived metrics from raw Meta Ads data."""

import pandas as pd
import numpy as np


def _safe_divide(numerator, denominator):
    """Divide with zero/NaN protection."""
    return np.where(
        (denominator > 0) & pd.notna(denominator) & pd.notna(numerator),
        numerator / denominator,
        np.nan,
    )


def compute_common_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate CPM, CPC, CTR, Cost per Result, Frequency from raw data."""
    if "impressions" in df.columns and "spend" in df.columns:
        df["cpm"] = _safe_divide(df["spend"], df["impressions"]) * 1000

    if "link_clicks" in df.columns and "spend" in df.columns:
        df["cpc"] = _safe_divide(df["spend"], df["link_clicks"])

    if "link_clicks" in df.columns and "impressions" in df.columns:
        df["ctr"] = _safe_divide(df["link_clicks"], df["impressions"]) * 100

    if "clicks_all" in df.columns and "impressions" in df.columns:
        df["ctr_all"] = _safe_divide(df["clicks_all"], df["impressions"]) * 100

    if "results" in df.columns and "spend" in df.columns:
        df["cost_per_result"] = _safe_divide(df["spend"], df["results"])

    if "impressions" in df.columns and "reach" in df.columns:
        df["frequency"] = _safe_divide(df["impressions"], df["reach"])

    if "results" in df.columns and "impressions" in df.columns:
        df["result_rate"] = _safe_divide(df["results"], df["impressions"]) * 100

    # Outbound CTR
    if "outbound_clicks" in df.columns and "impressions" in df.columns:
        df["outbound_ctr"] = _safe_divide(df["outbound_clicks"], df["impressions"]) * 100

    # Landing page conversion rate (results / landing page views)
    if "results" in df.columns and "landing_page_views" in df.columns:
        df["lp_conversion_rate"] = _safe_divide(df["results"], df["landing_page_views"]) * 100

    return df


def compute_video_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate video-specific metrics for video creatives only."""
    video_mask = df.get("creative_type") == "video"
    if not video_mask.any():
        return df

    # Hook Rate: 3-sec views / impressions * 100
    if "video_3s_views" in df.columns and "impressions" in df.columns:
        df.loc[video_mask, "hook_rate"] = (
            _safe_divide(
                df.loc[video_mask, "video_3s_views"],
                df.loc[video_mask, "impressions"],
            ) * 100
        )

    # Scroll-Stop Rate: 2-sec continuous views / impressions * 100
    if "video_2s_continuous" in df.columns and "impressions" in df.columns:
        df.loc[video_mask, "scroll_stop_rate"] = (
            _safe_divide(
                df.loc[video_mask, "video_2s_continuous"],
                df.loc[video_mask, "impressions"],
            ) * 100
        )

    # Hold Rate: ThruPlay / 3-sec views * 100
    if "thruplay" in df.columns and "video_3s_views" in df.columns:
        df.loc[video_mask, "hold_rate"] = (
            _safe_divide(
                df.loc[video_mask, "thruplay"],
                df.loc[video_mask, "video_3s_views"],
            ) * 100
        )

    # Cost per ThruPlay
    if "thruplay" in df.columns and "spend" in df.columns:
        df.loc[video_mask, "cost_per_thruplay"] = _safe_divide(
            df.loc[video_mask, "spend"],
            df.loc[video_mask, "thruplay"],
        )

    # Video Completion Rate: video_p100 / impressions * 100
    if "video_p100" in df.columns and "impressions" in df.columns:
        df.loc[video_mask, "video_completion_rate"] = (
            _safe_divide(
                df.loc[video_mask, "video_p100"],
                df.loc[video_mask, "impressions"],
            ) * 100
        )

    # Completion rates (as % of impressions)
    for pct_col in ["video_p25", "video_p50", "video_p75", "video_p95", "video_p100"]:
        rate_col = f"{pct_col}_rate"
        if pct_col in df.columns and "impressions" in df.columns:
            df.loc[video_mask, rate_col] = (
                _safe_divide(
                    df.loc[video_mask, pct_col],
                    df.loc[video_mask, "impressions"],
                ) * 100
            )

    return df


def compute_image_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate image-specific metrics."""
    image_mask = df.get("creative_type") == "image"
    if not image_mask.any():
        return df

    # Engagement Rate
    if "post_engagements" in df.columns and "impressions" in df.columns:
        df.loc[image_mask, "engagement_rate"] = (
            _safe_divide(
                df.loc[image_mask, "post_engagements"],
                df.loc[image_mask, "impressions"],
            ) * 100
        )

    # Conversion Rate
    if "results" in df.columns and "link_clicks" in df.columns:
        df.loc[image_mask, "conversion_rate"] = (
            _safe_divide(
                df.loc[image_mask, "results"],
                df.loc[image_mask, "link_clicks"],
            ) * 100
        )

    return df


def compute_campaign_specific(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate campaign-type-specific metrics."""
    # App Install campaigns
    install_mask = df.get("campaign_type") == "app_install"
    if install_mask.any():
        if "app_installs" in df.columns and "spend" in df.columns:
            df.loc[install_mask, "cost_per_install"] = _safe_divide(
                df.loc[install_mask, "spend"],
                df.loc[install_mask, "app_installs"],
            )
        elif "results" in df.columns and "spend" in df.columns:
            df.loc[install_mask, "cost_per_install"] = _safe_divide(
                df.loc[install_mask, "spend"],
                df.loc[install_mask, "results"],
            )

    # App Event campaigns
    event_mask = df.get("campaign_type") == "app_event"
    if event_mask.any():
        if "results" in df.columns and "spend" in df.columns:
            df.loc[event_mask, "cost_per_action"] = _safe_divide(
                df.loc[event_mask, "spend"],
                df.loc[event_mask, "results"],
            )
        if "results" in df.columns and "link_clicks" in df.columns:
            df.loc[event_mask, "conversion_rate"] = (
                _safe_divide(
                    df.loc[event_mask, "results"],
                    df.loc[event_mask, "link_clicks"],
                ) * 100
            )

    return df


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Run all metric computations in sequence."""
    df = compute_common_metrics(df)
    df = compute_video_metrics(df)
    df = compute_image_metrics(df)
    df = compute_campaign_specific(df)
    return df
