"""SQLite persistence layer for historical data tracking."""

import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "historical.db"


def _get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date DATE NOT NULL,
            creative_name TEXT NOT NULL,
            campaign_name TEXT,
            ad_set_name TEXT,
            campaign_type TEXT,
            creative_type TEXT,
            -- Raw metrics
            impressions REAL,
            reach REAL,
            spend REAL,
            link_clicks REAL,
            clicks_all REAL,
            results REAL,
            frequency_raw REAL,
            cost_per_result_raw REAL,
            ctr_raw REAL,
            cpc_raw REAL,
            cpm_raw REAL,
            -- Video raw
            video_3s_views REAL,
            video_2s_continuous REAL,
            thruplay REAL,
            video_plays REAL,
            video_p25 REAL,
            video_p50 REAL,
            video_p75 REAL,
            video_p95 REAL,
            video_p100 REAL,
            video_avg_play_time REAL,
            video_pct_watched REAL,
            -- Engagement
            post_engagements REAL,
            post_reactions REAL,
            post_comments REAL,
            post_shares REAL,
            post_saves REAL,
            -- Clicks extended
            outbound_clicks REAL,
            landing_page_views REAL,
            unique_link_clicks REAL,
            -- App
            app_installs REAL,
            app_store_clicks REAL,
            mobile_app_actions REAL,
            -- Conversions
            leads REAL,
            registrations REAL,
            purchases REAL,
            purchase_value REAL,
            purchase_roas REAL,
            -- Computed metrics
            cpm REAL,
            cpc REAL,
            ctr REAL,
            ctr_all REAL,
            frequency REAL,
            cost_per_result REAL,
            result_rate REAL,
            outbound_ctr REAL,
            lp_conversion_rate REAL,
            hook_rate REAL,
            hold_rate REAL,
            scroll_stop_rate REAL,
            cost_per_thruplay REAL,
            video_completion_rate REAL,
            engagement_rate REAL,
            conversion_rate REAL,
            cost_per_install REAL,
            cost_per_action REAL,
            cost_per_lead REAL,
            cost_per_registration REAL,
            cost_per_purchase REAL,
            -- Quality rankings
            quality_ranking TEXT,
            engagement_rate_ranking TEXT,
            conversion_rate_ranking TEXT,
            -- Classification
            performance_tier TEXT,
            creative_status TEXT,
            creative_publish_date DATE,
            creative_age_days INTEGER,
            creative_age_bucket TEXT,
            -- Custom events
            px_otp_initiated REAL,
            partner_onboarding_success REAL,
            result_type TEXT,
            days_active INTEGER,
            -- Placement/Demographics
            platform TEXT,
            placement TEXT,
            UNIQUE(snapshot_date, creative_name)
        );

        CREATE TABLE IF NOT EXISTS upload_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_name TEXT,
            row_count INTEGER,
            snapshot_date DATE
        );

        CREATE INDEX IF NOT EXISTS idx_snapshot_date ON daily_snapshots(snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_creative_name ON daily_snapshots(creative_name);
    """)
    conn.close()


def save_daily_snapshot(df: pd.DataFrame, snapshot_date: date = None, file_name: str = ""):
    if snapshot_date is None:
        snapshot_date = date.today()

    conn = _get_connection()
    init_db()

    df_to_save = df.copy()
    df_to_save["snapshot_date"] = snapshot_date

    # Get columns that exist in both DataFrame and table
    cursor = conn.execute("PRAGMA table_info(daily_snapshots)")
    table_columns = {row[1] for row in cursor.fetchall()} - {"id"}

    available_columns = [c for c in df_to_save.columns if c in table_columns]
    df_subset = df_to_save[available_columns]

    for _, row in df_subset.iterrows():
        cols = list(row.index)
        placeholders = ", ".join(["?"] * len(cols))
        col_names = ", ".join(cols)
        update_clause = ", ".join([f"{c}=excluded.{c}" for c in cols if c not in ("snapshot_date", "creative_name")])

        sql = f"""
            INSERT INTO daily_snapshots ({col_names})
            VALUES ({placeholders})
            ON CONFLICT(snapshot_date, creative_name)
            DO UPDATE SET {update_clause}
        """
        conn.execute(sql, tuple(row.values))

    # Log the upload
    conn.execute(
        "INSERT INTO upload_log (file_name, row_count, snapshot_date) VALUES (?, ?, ?)",
        (file_name, len(df), snapshot_date),
    )

    conn.commit()
    conn.close()


def load_historical(start_date: date = None, end_date: date = None) -> pd.DataFrame:
    init_db()
    conn = _get_connection()

    query = "SELECT * FROM daily_snapshots WHERE 1=1"
    params = []

    if start_date:
        query += " AND snapshot_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND snapshot_date <= ?"
        params.append(end_date)

    query += " ORDER BY snapshot_date DESC, creative_name"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_available_dates() -> list:
    init_db()
    conn = _get_connection()
    cursor = conn.execute("SELECT DISTINCT snapshot_date FROM daily_snapshots ORDER BY snapshot_date DESC")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dates


def get_creative_history(creative_name: str) -> pd.DataFrame:
    init_db()
    conn = _get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM daily_snapshots WHERE creative_name = ? ORDER BY snapshot_date",
        conn,
        params=(creative_name,),
    )
    conn.close()
    return df


def get_all_creative_names() -> list:
    init_db()
    conn = _get_connection()
    cursor = conn.execute("SELECT DISTINCT creative_name FROM daily_snapshots ORDER BY creative_name")
    names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return names
