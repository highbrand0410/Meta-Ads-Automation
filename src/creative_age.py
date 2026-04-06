"""Date extraction from creative names and age-based analysis."""

from datetime import date, datetime
from typing import Optional

import pandas as pd
import numpy as np

from config import CREATIVE_NAME_DATE_PATTERNS


MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def extract_creative_date(name: str) -> Optional[date]:
    """Extract publish date from creative name string."""
    if not isinstance(name, str):
        return None

    # Pattern 1: DDMmmYY / DDMmmYYYY (primary - e.g., 25Sep25, 01Jan2026)
    pattern = CREATIVE_NAME_DATE_PATTERNS[0]
    match = pattern.search(name)
    if match:
        day = int(match.group(1))
        month = MONTH_MAP.get(match.group(2).lower())
        year_str = match.group(3)
        if month:
            year = int(year_str)
            if year < 100:
                year += 2000
            try:
                return date(year, month, day)
            except ValueError:
                pass

    # Pattern 2: DD-MM-YYYY or DD/MM/YYYY
    if len(CREATIVE_NAME_DATE_PATTERNS) > 1:
        pattern = CREATIVE_NAME_DATE_PATTERNS[1]
        match = pattern.search(name)
        if match:
            try:
                return date(int(match.group(3)), int(match.group(2)), int(match.group(1)))
            except ValueError:
                pass

    # Pattern 3: YYYY-MM-DD
    if len(CREATIVE_NAME_DATE_PATTERNS) > 2:
        pattern = CREATIVE_NAME_DATE_PATTERNS[2]
        match = pattern.search(name)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

    return None


def add_age_columns(df: pd.DataFrame, reference_date: date = None, age_threshold: int = 14) -> pd.DataFrame:
    """Add creative_publish_date, creative_age_days, creative_age_bucket columns."""
    if reference_date is None:
        reference_date = date.today()

    if "creative_name" not in df.columns:
        return df

    df["creative_publish_date"] = df["creative_name"].apply(extract_creative_date)

    df["creative_age_days"] = df["creative_publish_date"].apply(
        lambda d: (reference_date - d).days if d is not None else None
    )

    df["creative_age_bucket"] = df["creative_age_days"].apply(
        lambda days: "New" if days is not None and days <= age_threshold
        else ("Old" if days is not None else "Unknown")
    )

    return df


def compare_old_vs_new(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate key metrics by age bucket for comparison."""
    if "creative_age_bucket" not in df.columns:
        return pd.DataFrame()

    comparison_df = df[df["creative_age_bucket"].isin(["New", "Old"])]
    if comparison_df.empty:
        return pd.DataFrame()

    metric_cols = [
        "spend", "impressions", "results", "cpm", "cpc", "ctr",
        "cost_per_result", "frequency", "hook_rate", "hold_rate",
    ]
    available_metrics = [c for c in metric_cols if c in comparison_df.columns]

    agg_dict = {col: "mean" for col in available_metrics}
    agg_dict["creative_name"] = "count"

    result = comparison_df.groupby("creative_age_bucket").agg(agg_dict)
    result = result.rename(columns={"creative_name": "count"})

    return result
