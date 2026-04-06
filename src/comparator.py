"""Date-range comparison logic for historical analysis."""

from datetime import date
import pandas as pd
import numpy as np


def filter_by_date_range(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """Filter DataFrame to rows within the given date range."""
    if "snapshot_date" not in df.columns:
        return df

    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.date
    mask = (df["snapshot_date"] >= start_date) & (df["snapshot_date"] <= end_date)
    return df[mask].copy()


def compare_periods(
    df: pd.DataFrame,
    period_a: tuple,
    period_b: tuple,
) -> pd.DataFrame:
    """Compare aggregated metrics between two time periods.

    Args:
        df: Historical DataFrame with snapshot_date column.
        period_a: (start_date, end_date) for period A.
        period_b: (start_date, end_date) for period B.

    Returns:
        DataFrame with Period A, Period B, Delta, and % Change columns.
    """
    df_a = filter_by_date_range(df, period_a[0], period_a[1])
    df_b = filter_by_date_range(df, period_b[0], period_b[1])

    if df_a.empty or df_b.empty:
        return pd.DataFrame()

    metric_cols = [
        "spend", "impressions", "reach", "results", "cpm", "cpc", "ctr",
        "cost_per_result", "frequency", "hook_rate", "hold_rate",
        "cost_per_thruplay", "engagement_rate", "conversion_rate",
    ]
    available = [c for c in metric_cols if c in df_a.columns and c in df_b.columns]

    agg_a = df_a[available].mean()
    agg_b = df_b[available].mean()

    comparison = pd.DataFrame({
        "Period A": agg_a,
        "Period B": agg_b,
    })
    comparison["Delta"] = comparison["Period B"] - comparison["Period A"]
    comparison["% Change"] = np.where(
        comparison["Period A"] != 0,
        (comparison["Delta"] / comparison["Period A"].abs()) * 100,
        np.nan,
    )

    return comparison


def compare_creatives_across_periods(
    df: pd.DataFrame,
    period_a: tuple,
    period_b: tuple,
) -> pd.DataFrame:
    """Compare each creative's metrics between two periods."""
    df_a = filter_by_date_range(df, period_a[0], period_a[1])
    df_b = filter_by_date_range(df, period_b[0], period_b[1])

    if df_a.empty or df_b.empty:
        return pd.DataFrame()

    metric_cols = ["spend", "cpm", "cpc", "ctr", "cost_per_result", "results"]
    available = [c for c in metric_cols if c in df_a.columns and c in df_b.columns]

    agg_a = df_a.groupby("creative_name")[available].mean()
    agg_b = df_b.groupby("creative_name")[available].mean()

    # Only include creatives present in both periods
    common = agg_a.index.intersection(agg_b.index)
    if common.empty:
        return pd.DataFrame()

    result_rows = []
    for creative in common:
        row = {"creative_name": creative}
        for col in available:
            val_a = agg_a.loc[creative, col]
            val_b = agg_b.loc[creative, col]
            row[f"{col}_A"] = val_a
            row[f"{col}_B"] = val_b
            row[f"{col}_delta"] = val_b - val_a
            if val_a != 0 and pd.notna(val_a):
                row[f"{col}_pct_change"] = ((val_b - val_a) / abs(val_a)) * 100
            else:
                row[f"{col}_pct_change"] = np.nan
        result_rows.append(row)

    return pd.DataFrame(result_rows)
