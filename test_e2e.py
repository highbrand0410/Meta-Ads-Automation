"""End-to-end test of the full data pipeline."""

import sys, os, io
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from src.csv_parser import parse, validate
from src.metrics_engine import compute_all
from src.classifier import classify_performers, get_insights
from src.creative_age import add_age_columns, extract_creative_date
from src.suggestions import generate_suggestions
from src.db import init_db, save_daily_snapshot, load_historical
from datetime import date

# Sample CSV mimicking Meta Ads export
SAMPLE_CSV = """Campaign name,Ad set name,Ad name,Amount spent (INR),Impressions,Reach,Link clicks,Results,3-second video plays,ThruPlays,Video plays at 25%,Video plays at 50%,Video plays at 75%,Video plays at 95%,Video watches at 100%,Post engagements
BGL App Install,DSA Lookalike,BGL|DSA|Hn-Vid12-25Sep25,15000,120000,80000,1500,200,45000,12000,35000,25000,15000,8000,5000,3200
BGL App Install,DSA Broad,BGL|DSA|En-Vid08-10Aug25,8000,60000,40000,800,90,20000,5000,14000,10000,6000,3000,1500,1800
WeRize Conversion,LAL Purchase,WR|LAL|Hn-Img05-01Mar26,12000,90000,65000,1200,150,,,,,,,,2500
WeRize Conversion,LAL Register,WR|LAL|En-Img11-15Feb26,5000,45000,30000,600,80,,,,,,,,1200
BGL App Install,Interest,BGL|INT|Hn-Vid15-01Mar26,20000,150000,100000,2000,350,55000,18000,42000,30000,20000,12000,7000,4500
WeRize Conversion,Retarget,WR|RT|Hn-Img02-20Jul25,3000,25000,18000,300,25,,,,,,,,800
"""

print("=" * 60)
print("META ADS DASHBOARD - END-TO-END TEST")
print("=" * 60)

# Step 1: Parse CSV
print("\n[1] Parsing CSV...")
df = parse(io.StringIO(SAMPLE_CSV))
is_valid, warnings = validate(df)
print(f"    Valid: {is_valid}")
print(f"    Rows: {len(df)}")
print(f"    Columns: {list(df.columns)[:10]}...")
print(f"    Warnings: {warnings}")
print(f"    Creative types: {df['creative_type'].value_counts().to_dict()}")
print(f"    Campaign types: {df['campaign_type'].value_counts().to_dict()}")

# Step 2: Compute metrics
print("\n[2] Computing metrics...")
df = compute_all(df)
computed_cols = ["cpm", "cpc", "ctr", "cost_per_result", "frequency", "hook_rate", "hold_rate"]
for col in computed_cols:
    if col in df.columns:
        print(f"    {col}: {df[col].dropna().values[:3].round(2)}")

# Step 3: Add age columns
print("\n[3] Adding creative age...")
df = add_age_columns(df, reference_date=date(2026, 3, 15), age_threshold=14)
print(f"    Age buckets: {df['creative_age_bucket'].value_counts().to_dict()}")
print(f"    Sample ages: {df[['creative_name', 'creative_age_days', 'creative_age_bucket']].to_string(index=False)}")

# Step 4: Classify performers
print("\n[4] Classifying performers...")
df = classify_performers(df, metric="cost_per_result")
print(f"    Tiers: {df['performance_tier'].value_counts().to_dict()}")

# Step 5: Generate suggestions
print("\n[5] Generating suggestions...")
df = generate_suggestions(df)
for _, row in df.iterrows():
    print(f"    {row['creative_name'][:30]:30s} -> {row['suggestion'][:80]}...")

# Step 6: Get insights
print("\n[6] Generating insights...")
insights = get_insights(df)
print("    WORKING:")
for i in insights["working"]:
    print(f"      - {i}")
print("    NOT WORKING:")
for i in insights["not_working"]:
    print(f"      - {i}")

# Step 7: Save to DB
print("\n[7] Saving to database...")
init_db()
save_daily_snapshot(df, snapshot_date=date(2026, 3, 15), file_name="test.csv")
print("    Saved successfully!")

# Step 8: Load historical
print("\n[8] Loading historical data...")
hist = load_historical()
print(f"    Historical rows: {len(hist)}")
print(f"    Dates: {hist['snapshot_date'].unique().tolist()}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
