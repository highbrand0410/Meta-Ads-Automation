# Meta Ads Creative Performance Dashboard — Project Handoff

## Project Location
`C:\Users\Rahul\Downloads\Claude Master\Meta_Automation`

## What This Is
A Streamlit dashboard for **WeRize** that automates daily Meta Ads creative performance analysis. The user downloads CSV reports from Meta Ads Manager, uploads them to this dashboard, and gets automated metric computation, creative classification, status assignment, suggestions, and historical comparison.

## How to Run
```bash
cd "C:\Users\Rahul\Downloads\Claude Master\Meta_Automation"
python -m streamlit run app.py
```
Dependencies: `streamlit>=1.39.0`, `pandas>=2.0.0`, `plotly>=5.18.0`

---

## Architecture

### File Structure
```
Meta_Automation/
  app.py                          # Main Streamlit entry point + CSV upload + processing pipeline
  config.py                       # 135+ column mappings, metric classifications, thresholds
  requirements.txt                # streamlit, pandas, plotly
  src/
    csv_parser.py                 # CSV ingestion, column normalization, results unification, creative-level aggregation
    metrics_engine.py             # Derived metrics (CPM, CPC, CTR, hook rate, hold rate, etc.)
    classifier.py                 # Percentile-based performer classification (High/Average/Low)
    suggestions.py                # Per-creative suggestions + creative_status assignment (SCALE/MONITOR/TEST/REPLACE/PAUSE/LEARNING)
    creative_age.py               # Extract publish dates from creative names (DDMmmYY format)
    comparator.py                 # Date range comparison for historical analysis
    db.py                         # SQLite persistence for historical tracking (data/historical.db)
  pages/
    1_Overview.py                 # KPI cards, status distribution chart, top/bottom 5 creatives
    2_Creative_Performance.py     # Full interactive table with filters (status, tier, quality, campaign type)
    3_High_Low_Performers.py      # Three-column tier view + insights (what's working / not working)
    4_Video_vs_Image.py           # Format comparison, video funnel, status by format
    5_Old_vs_New.py               # Age analysis, status by age bucket, scatter plot
    6_Trends.py                   # Daily trends from current upload + historical trends across uploads
    7_Comparison_Mode.py          # Period A vs Period B comparison (requires 2+ uploads)
    8_Creative_Drilldown.py       # Single creative deep dive with status banner, metrics, video funnel, daily trend
  styles/
    custom.css                    # White sidebar, dark text, indigo accents, insight cards
  data/
    historical.db                 # SQLite database (auto-created on first run)
```

### Data Processing Pipeline (app.py)
1. **Parse CSV** -> `csv_parser.parse()` — normalize columns, unify results, coerce numerics, parse dates, detect creative/campaign types
2. **Aggregate** -> `csv_parser.aggregate_to_creative_level()` — group by creative_name, SUM volume metrics, take first/mode for text/rankings
3. **Compute Metrics** -> `metrics_engine.compute_all()` — CPM, CPC, CTR, cost/result, frequency, hook rate, hold rate, scroll-stop rate, completion rate, etc.
4. **Add Age** -> `creative_age.add_age_columns()` — extract dates from creative names, compute age in days
5. **Classify** -> `classifier.classify_performers()` — percentile-based High/Average/Low Performer tiers
6. **Suggestions + Status** -> `suggestions.generate_suggestions()` — per-creative actionable suggestions + creative_status column

### Two-Layer Data Architecture
- `st.session_state.df` = Aggregated creative-level data (one row per creative)
- `st.session_state.df_daily` = Raw daily data (for trends and drilldown charts)

---

## Key Business Rules

### Results Unification
Business rule from user: "against the creative if the result entry is 'yes' consider that as an install else take 'mobile app install' as the no. of results"

Implementation in `csv_parser._unify_results()`:
- The Meta CSV has a `Results` column that may contain numeric values or text like "yes"
- If `Results` has a valid numeric value > 0, use it as the result count
- Otherwise, fall back to the `Mobile app installs` column
- The `Results` column is first mapped to `results_raw` in COLUMN_MAP, then unified into `results`

### Creative Status (suggestions.py)
Six statuses assigned per creative, ordered by priority:
1. **PAUSE** — Zero results with spend, OR cost/result > 2.5x median (with spend > 50)
2. **LEARNING** — Creative age <= 5 days with spend < 200, OR <= 2 days active with spend < 100
3. **REPLACE** — Age > 30 days with above-median cost, OR frequency > 3 with poor efficiency, OR below-average quality with high CPR
4. **SCALE** — High Performer tier with frequency < 2, OR CPR < 0.5x median with CTR > 1.3x median
5. **TEST VARIATION** — Good CTR but poor conversion, OR High Performer with frequency >= 2, OR Average with decent metrics, OR Low Performer with good CTR
6. **MONITOR** — Everything else (no red/green flags)

### Campaign Type Detection
Based on campaign name keywords:
- `app_install` — keywords: install, app install, mai, mobile app install
- `app_event` — keywords: app event, optimization event, otp, onboarding, ssf, success screen
- `other` — fallback

### Creative Type Detection
- `video` — if any video metric column (3s views, thruplay, video_p25, 2s continuous, video plays) has value > 0
- `image` — otherwise

### Performer Classification
- Percentile-based: 75th percentile = High Performer, 25th = Low Performer
- Respects LOWER_IS_BETTER metrics (cost_per_result, cpm, cpc, frequency, cost_per_install)

---

## CSV Format Expected
The user downloads reports from Meta Ads Manager. The preferred format (Mar1-14.csv) has these columns:
```
Campaign name, Ad set name, Ad name, Day, Campaign ID, Ad set ID, Ad ID,
Delivery status, Delivery level, Reach, Impressions, Frequency, Attribution setting,
Result Type, Results, Amount spent (INR), Cost per result, Starts, Ends,
Reporting starts, Reporting ends, CPM, CTR, CPC, Result rate, Link clicks,
Outbound clicks, Quality ranking, Engagement rate ranking, Conversion rate ranking,
3-second video plays, 2-second continuous video plays, Video average play time,
Video plays at 25/50/75/95/100%, ThruPlays, Cost per ThruPlay,
Cost per 3-second video play, Cost per App Install, Landing page views,
Cost per landing page view, Mobile app installs, px_onboarding_otp_initiated,
Partner Onboarding Success Screen
```

No age/gender breakdowns in this format. Day-level breakdown only. Custom event columns: `px_onboarding_otp_initiated` and `Partner Onboarding Success Screen`.

---

## Current Data State (Mar 1-14, 2026)
- 391 daily rows -> 39 unique creatives after aggregation
- Status distribution: PAUSE=16, SCALE=7, TEST VARIATION=7, REPLACE=5, MONITOR=4
- Total spend: ~3.3L INR across 39 creatives
- 16 creatives with zero results (wasting budget)
- Top performer: SSF_IMG_M1_T3_HIN_27JAN2026 at 1.05 INR/result
- Worst performer: SSF App Hindi UGC-SSC01-15Jan2026 at 134.18 INR/result

---

## What Has Been Completed
1. Full CSV parser with 135+ column mappings for Meta Ads
2. Results unification logic (Results column vs Mobile app installs)
3. Creative-level aggregation (SUM volumes, RECALCULATE ratios)
4. All derived metrics (CPM, CPC, CTR, hook rate, hold rate, scroll-stop rate, completion rate, LP conversion rate, etc.)
5. Percentile-based performer classification
6. Creative status assignment (SCALE/MONITOR/TEST VARIATION/REPLACE/PAUSE/LEARNING)
7. Per-creative suggestion engine with quality ranking, frequency, video funnel, cost efficiency insights
8. SQLite persistence for historical tracking
9. 8 dashboard pages fully functional
10. CSS styling (white sidebar, dark text, proper contrast)
11. Daily trend charts from current CSV upload
12. Historical trend charts across multiple uploads
13. Period comparison mode

## Pending / Future Improvements
1. **Auto-download from Meta API** — User currently downloads CSV manually. Could integrate Meta Marketing API for automated data pull.
2. **Enhanced daily trend suggestions** — Use daily data to detect "CPR spiked on Day X, should have paused 3 days ago" type insights.
3. **Budget reallocation recommendations** — Based on creative status, suggest how to redistribute budget from PAUSE/REPLACE to SCALE creatives.
4. **Automated email/Slack alerts** — When a creative should be paused or scaled, send notification.
5. **A/B test tracking** — Compare creative variations systematically.
6. **Custom event funnel** — OTP Initiated -> Partner Onboarding Success Screen conversion funnel.

---

## Important Notes for New Session
- Project folder: `C:\Users\Rahul\Downloads\Claude Master\Meta_Automation`
- CSV test file: `C:\Users\Rahul\Downloads\Mar1-14.csv`
- Currency: INR (Indian Rupees), symbol: INR
- Company: WeRize (Partner App)
- App type: Financial app (App Install + App Event campaigns)
- The old folder `C:\Users\Rahul\Downloads\Meta_Automation` may still exist (couldn't delete due to session lock) — it's the same code, can be safely deleted.
