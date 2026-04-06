"""Comparison Mode — Custom date-range comparison."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.db import load_historical, get_available_dates
from src.comparator import compare_periods, compare_creatives_across_periods
from config import CURRENCY_SYMBOL, LOWER_IS_BETTER

st.set_page_config(page_title="Comparison Mode", page_icon="🔄", layout="wide")
st.title("Period Comparison")

available_dates = get_available_dates()

if len(available_dates) < 2:
    st.info(
        f"Comparison requires at least 2 daily snapshots. Currently have {len(available_dates)}. "
        "Upload CSV reports on different days to enable comparison."
    )
    st.stop()

hist_df = load_historical()
hist_df["snapshot_date"] = pd.to_datetime(hist_df["snapshot_date"])
min_date = hist_df["snapshot_date"].min().date()
max_date = hist_df["snapshot_date"].max().date()

# --- Date pickers ---
st.subheader("Select Two Periods to Compare")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**Period A**")
    a_start = st.date_input("Period A Start", value=min_date, min_value=min_date, max_value=max_date, key="a_start")
    a_end = st.date_input("Period A End", value=min_date, min_value=min_date, max_value=max_date, key="a_end")

with col_b:
    st.markdown("**Period B**")
    b_start = st.date_input("Period B Start", value=max_date, min_value=min_date, max_value=max_date, key="b_start")
    b_end = st.date_input("Period B End", value=max_date, min_value=min_date, max_value=max_date, key="b_end")

if st.button("Compare", type="primary"):
    st.divider()

    # --- Aggregate comparison ---
    comparison = compare_periods(hist_df, (a_start, a_end), (b_start, b_end))

    if comparison.empty:
        st.warning("No data available for one or both selected periods.")
    else:
        st.subheader("Aggregate Metrics Comparison")

        # KPI cards with deltas
        metrics_to_show = comparison.index.tolist()
        cols = st.columns(min(len(metrics_to_show), 4))

        for i, metric in enumerate(metrics_to_show):
            col = cols[i % len(cols)]
            val_a = comparison.loc[metric, "Period A"]
            val_b = comparison.loc[metric, "Period B"]
            delta = comparison.loc[metric, "Delta"]
            pct = comparison.loc[metric, "% Change"]

            # For cost metrics, negative delta is good
            is_cost = metric in LOWER_IS_BETTER
            delta_str = f"{delta:+.2f}"
            if pd.notna(pct):
                delta_str += f" ({pct:+.1f}%)"

            with col:
                st.metric(
                    metric.replace("_", " ").title(),
                    f"{val_b:,.2f}",
                    delta=delta_str,
                    delta_color="inverse" if is_cost else "normal",
                )

        # Table view
        st.dataframe(comparison.round(2), use_container_width=True)

        st.divider()

        # --- Per-creative comparison ---
        st.subheader("Per-Creative Changes")
        creative_comp = compare_creatives_across_periods(hist_df, (a_start, a_end), (b_start, b_end))

        if creative_comp.empty:
            st.info("No common creatives found across both periods.")
        else:
            # Highlight significant changes
            display_cols = ["creative_name"]
            for m in ["cost_per_result", "ctr", "cpm"]:
                for suffix in ["_A", "_B", "_pct_change"]:
                    col_name = f"{m}{suffix}"
                    if col_name in creative_comp.columns:
                        display_cols.append(col_name)

            available_display = [c for c in display_cols if c in creative_comp.columns]
            st.dataframe(
                creative_comp[available_display].round(2),
                use_container_width=True,
                hide_index=True,
            )
