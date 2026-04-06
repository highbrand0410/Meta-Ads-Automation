"""High/Low performer classification and insight generation."""

import pandas as pd
import numpy as np
from config import PERFORMER_THRESHOLDS, LOWER_IS_BETTER, METRIC_DISPLAY_NAMES


def classify_performers(df: pd.DataFrame, metric: str = "cost_per_result") -> pd.DataFrame:
    """Add 'performance_tier' column based on percentile ranking."""
    if metric not in df.columns or df[metric].dropna().empty:
        df["performance_tier"] = "N/A"
        return df

    valid_mask = df[metric].notna()
    high_pct = PERFORMER_THRESHOLDS["high"]
    low_pct = PERFORMER_THRESHOLDS["low"]

    high_threshold = df.loc[valid_mask, metric].quantile(high_pct / 100)
    low_threshold = df.loc[valid_mask, metric].quantile(low_pct / 100)

    if metric in LOWER_IS_BETTER:
        df["performance_tier"] = np.where(
            ~valid_mask, "N/A",
            np.where(
                df[metric] <= low_threshold, "High Performer",
                np.where(df[metric] >= high_threshold, "Low Performer", "Average")
            )
        )
    else:
        df["performance_tier"] = np.where(
            ~valid_mask, "N/A",
            np.where(
                df[metric] >= high_threshold, "High Performer",
                np.where(df[metric] <= low_threshold, "Low Performer", "Average")
            )
        )

    return df


def get_summary(df: pd.DataFrame) -> dict:
    """Return counts and average metrics per tier."""
    if "performance_tier" not in df.columns:
        return {}

    summary = {}
    for tier in ["High Performer", "Average", "Low Performer"]:
        tier_df = df[df["performance_tier"] == tier]
        summary[tier] = {
            "count": len(tier_df),
            "avg_spend": tier_df["spend"].mean() if "spend" in tier_df.columns else 0,
            "avg_ctr": tier_df["ctr"].mean() if "ctr" in tier_df.columns else 0,
            "avg_cpm": tier_df["cpm"].mean() if "cpm" in tier_df.columns else 0,
            "avg_cost_per_result": tier_df["cost_per_result"].mean() if "cost_per_result" in tier_df.columns else 0,
            "avg_frequency": tier_df["frequency"].mean() if "frequency" in tier_df.columns else 0,
        }
    return summary


def get_insights(df: pd.DataFrame) -> dict:
    """Generate natural-language insights about what's working and what's not."""
    working = []
    not_working = []

    if "performance_tier" not in df.columns or len(df) < 4:
        return {"working": ["Not enough data for insights."], "not_working": []}

    high = df[df["performance_tier"] == "High Performer"]
    low = df[df["performance_tier"] == "Low Performer"]

    if high.empty or low.empty:
        return {"working": ["Not enough variation for insights."], "not_working": []}

    # CTR comparison
    if "ctr" in df.columns:
        high_ctr = high["ctr"].mean()
        low_ctr = low["ctr"].mean()
        if low_ctr > 0 and pd.notna(high_ctr) and pd.notna(low_ctr):
            ratio = high_ctr / low_ctr
            working.append(f"Top performers have {ratio:.1f}x better CTR ({high_ctr:.2f}%) vs low performers ({low_ctr:.2f}%)")

    # Cost per result comparison
    if "cost_per_result" in df.columns:
        high_cpr = high["cost_per_result"].mean()
        low_cpr = low["cost_per_result"].mean()
        if high_cpr > 0 and pd.notna(high_cpr) and pd.notna(low_cpr):
            savings = low_cpr - high_cpr
            working.append(f"Top performers save \u20b9{savings:.2f} per result vs low performers")
            not_working.append(f"Low performers cost \u20b9{low_cpr:.2f}/result -- {low_cpr/high_cpr:.1f}x more than top performers")

    # Video vs Image comparison
    if "creative_type" in df.columns:
        video_df = df[df["creative_type"] == "video"]
        image_df = df[df["creative_type"] == "image"]
        if not video_df.empty and not image_df.empty and "cost_per_result" in df.columns:
            video_cpr = video_df["cost_per_result"].mean()
            image_cpr = image_df["cost_per_result"].mean()
            if pd.notna(video_cpr) and pd.notna(image_cpr) and video_cpr > 0 and image_cpr > 0:
                if video_cpr < image_cpr:
                    pct = ((image_cpr - video_cpr) / image_cpr) * 100
                    working.append(f"Video creatives outperform images by {pct:.0f}% on cost per result")
                else:
                    pct = ((video_cpr - image_cpr) / video_cpr) * 100
                    working.append(f"Image creatives outperform videos by {pct:.0f}% on cost per result")

    # Hook rate insight (video)
    if "hook_rate" in df.columns:
        video_high = high[high["creative_type"] == "video"]
        if not video_high.empty:
            avg_hook = video_high["hook_rate"].mean()
            if pd.notna(avg_hook):
                working.append(f"Top video creatives achieve {avg_hook:.1f}% hook rate")

    # Quality ranking insight
    if "quality_ranking" in df.columns:
        below_avg = df[df["quality_ranking"].astype(str).str.contains("Below", case=False, na=False)]
        if not below_avg.empty:
            not_working.append(f"{len(below_avg)} creatives have Below Average quality ranking -- Meta penalizes these with higher costs")

    # Landing page view drop-off
    if "landing_page_views" in df.columns and "link_clicks" in df.columns:
        total_lp = df["landing_page_views"].sum()
        total_clicks = df["link_clicks"].sum()
        if total_clicks > 0:
            lp_rate = total_lp / total_clicks * 100
            if lp_rate < 60:
                not_working.append(f"Only {lp_rate:.0f}% of link clicks convert to landing page views -- investigate page load speed")

    # Frequency warning
    if "frequency" in df.columns:
        high_freq = df[df["frequency"] > 3]
        if not high_freq.empty:
            not_working.append(f"{len(high_freq)} creatives have frequency > 3.0 -- consider refreshing to avoid ad fatigue")

    # Low CTR warning
    if "ctr" in df.columns:
        low_ctr_creatives = df[df["ctr"] < 0.5]
        if not low_ctr_creatives.empty:
            not_working.append(f"{len(low_ctr_creatives)} creatives have CTR below 0.5% -- review targeting or creative quality")

    if not working:
        working.append("Upload more data for detailed insights.")
    if not not_working:
        not_working.append("No critical issues detected.")

    return {"working": working, "not_working": not_working}
