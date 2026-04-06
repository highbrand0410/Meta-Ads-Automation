"""Configuration constants for Meta Ads Creative Performance Dashboard."""

import re

# --- Column Mapping ---
# Maps Meta Ads CSV header variations (lowercase) to internal canonical names.
COLUMN_MAP = {
    # === Identification ===
    "campaign name": "campaign_name",
    "campaign id": "campaign_id",
    "ad set name": "ad_set_name",
    "ad set id": "ad_set_id",
    "ad name": "creative_name",
    "ad id": "ad_id",
    "campaign objective": "objective",
    "objective": "objective",
    "campaign budget": "campaign_budget",
    "ad set budget": "ad_set_budget",
    "ad set budget type": "ad_set_budget_type",
    "attribution setting": "attribution_setting",
    "bid strategy": "bid_strategy",
    "bid amount": "bid_amount",
    "optimization goal": "optimization_goal",
    "buying type": "buying_type",
    "delivery status": "delivery_status",
    "delivery": "delivery_status",
    "delivery level": "delivery_level",
    "starts": "campaign_start_date",
    "ends": "campaign_end_date",
    "campaign start date": "campaign_start_date",
    "campaign end date": "campaign_end_date",

    # === Date / Time ===
    "reporting starts": "reporting_starts",
    "reporting ends": "reporting_ends",
    "day": "day",
    "week": "week",
    "month": "month",

    # === Delivery & Reach ===
    "impressions": "impressions",
    "reach": "reach",
    "frequency": "frequency_raw",
    "estimated ad recall lift (people)": "ad_recall_lift",
    "estimated ad recall lift rate (%)": "ad_recall_lift_rate",

    # === Cost & Spend ===
    "amount spent": "spend",
    "cpm (cost per 1,000 impressions)": "cpm_raw",
    "cpc (cost per link click)": "cpc_raw",
    "cpc (all)": "cpc_all_raw",
    "cost per result": "cost_per_result_raw",
    "cost per 1,000 people reached": "cost_per_1k_reached",
    "cost per thruplay": "cost_per_thruplay_raw",
    "cost per unique click (all)": "cost_per_unique_click_all",
    "cost per unique link click": "cost_per_unique_link_click",

    # === Click & Engagement ===
    "link clicks": "link_clicks",
    "clicks (all)": "clicks_all",
    "unique link clicks": "unique_link_clicks",
    "unique clicks (all)": "unique_clicks_all",
    "ctr (link click-through rate)": "ctr_raw",
    "ctr (all)": "ctr_all_raw",
    "unique link click-through rate (ctr)": "unique_ctr",
    "unique ctr (all)": "unique_ctr_all",
    "outbound clicks": "outbound_clicks",
    "unique outbound clicks": "unique_outbound_clicks",
    "outbound ctr": "outbound_ctr_raw",
    "cost per outbound click": "cost_per_outbound_click",
    "post engagements": "post_engagements",
    "post engagement": "post_engagements",
    "post reactions": "post_reactions",
    "post comments": "post_comments",
    "post shares": "post_shares",
    "post saves": "post_saves",
    "page engagement": "page_engagement",
    "page likes": "page_likes",

    # === Video Metrics ===
    "video plays": "video_plays",
    "3-second video plays": "video_3s_views",
    "2-second continuous video plays": "video_2s_continuous",
    "thruplay": "thruplay",
    "thruplays": "thruplay",
    "video plays at 25%": "video_p25",
    "video plays at 50%": "video_p50",
    "video plays at 75%": "video_p75",
    "video plays at 95%": "video_p95",
    "video plays at 100%": "video_p100",
    "video watches at 100%": "video_p100",
    "video average play time": "video_avg_play_time",
    "cost per 3-second video play": "cost_per_3s_play",
    "cost per 2-second continuous video play": "cost_per_2s_play",
    "video percentage watched": "video_pct_watched",
    "unique 3-second video plays": "unique_3s_views",
    "unique 2-second continuous video plays": "unique_2s_continuous",

    # === App-Specific ===
    "app installs": "app_installs",
    "mobile app installs": "app_installs",
    "cost per app install": "cost_per_install_raw",
    "cost per mobile app install": "cost_per_install_raw",
    "app store clicks": "app_store_clicks",
    "app engagement": "app_engagement",
    "mobile app actions": "mobile_app_actions",
    "mobile app purchase roas": "mobile_app_roas",
    "mobile app purchases": "mobile_app_purchases",
    "mobile app purchase conversion value": "mobile_app_purchase_value",
    "desktop app installs": "desktop_app_installs",
    "desktop app engagement": "desktop_app_engagement",

    # === Result Type ===
    "result type": "result_type",

    # === Custom Event Columns ===
    "px_onboarding_otp_initiated": "px_otp_initiated",
    "partner onboarding success screen": "partner_onboarding_success",

    # === Conversion & Results ===
    "results": "results_raw",
    "result rate": "result_rate_raw",
    "leads": "leads",
    "cost per lead": "cost_per_lead",
    "registrations completed": "registrations",
    "cost per registration completed": "cost_per_registration",
    "purchases": "purchases",
    "cost per purchase": "cost_per_purchase",
    "purchase conversion value": "purchase_value",
    "purchase roas (return on ad spend)": "purchase_roas",
    "add to cart": "add_to_cart",
    "cost per add to cart": "cost_per_add_to_cart",
    "checkouts initiated": "checkouts_initiated",
    "cost per checkout initiated": "cost_per_checkout",
    "adds of payment info": "adds_payment_info",
    "cost per add of payment info": "cost_per_add_payment_info",
    "content views": "content_views",
    "cost per content view": "cost_per_content_view",

    # === Attribution Window Results ===
    "results (1-day click)": "results_1d_click",
    "results (7-day click)": "results_7d_click",
    "results (1-day view)": "results_1d_view",
    "results (28-day click)": "results_28d_click",

    # === Quality & Relevance Rankings ===
    "quality ranking": "quality_ranking",
    "engagement rate ranking": "engagement_rate_ranking",
    "conversion rate ranking": "conversion_rate_ranking",

    # === Placement & Demographics ===
    "platform": "platform",
    "placement": "placement",
    "device platform": "device_platform",
    "impression device": "impression_device",
    "age": "age_group",
    "gender": "gender",
    "region": "region",
    "country": "country",

    # === Newer Metrics (2025-2026) ===
    "engaged-view conversions": "engaged_view_conversions",
    "cost per engaged-view conversion": "cost_per_engaged_view",
    "incremental conversions (estimated)": "incremental_conversions",
    "conversion leads": "conversion_leads",
    "cost per conversion lead": "cost_per_conversion_lead",
    "instagram profile visits": "ig_profile_visits",
    "on-facebook workflow completions": "on_fb_workflow_completions",
    "messaging conversations started": "messaging_conversations",
    "landing page views": "landing_page_views",
    "cost per landing page view": "cost_per_lpv",
    "unique landing page views": "unique_landing_page_views",
    "instant experience clicks to open": "ix_clicks_open",
    "instant experience clicks to start": "ix_clicks_start",
    "instant experience outbound clicks": "ix_outbound_clicks",
}

# Columns that must be present for basic analysis
REQUIRED_COLUMNS = ["creative_name", "spend", "impressions"]

# --- Creative Name Date Patterns ---
CREATIVE_NAME_DATE_PATTERNS = [
    re.compile(
        r"(\d{1,2})(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2,4})",
        re.IGNORECASE,
    ),
    re.compile(r"(\d{2})[-/](\d{2})[-/](\d{4})"),
    re.compile(r"(\d{4})[-/](\d{2})[-/](\d{2})"),
]

# --- Thresholds ---
CREATIVE_AGE_THRESHOLD_DAYS = 14
PERFORMER_THRESHOLDS = {"high": 75, "low": 25}

# --- Video Detection ---
VIDEO_METRIC_COLUMNS = [
    "video_3s_views", "thruplay", "video_p25", "video_p50",
    "video_2s_continuous", "video_plays",
]

# --- Campaign Type Keywords ---
CAMPAIGN_TYPE_KEYWORDS = {
    "app_install": ["app install", "app_install", "app ins", "installs", "mai", "aci"],
    "app_event": [
        "conversion", "app event", "app_event", "purchase", "registration",
        "aeo", "app engagement",
        "otp initiated", "otp_initiated", "success screen", "success_screen",
    ],
}

# --- Metrics where lower is better ---
LOWER_IS_BETTER = [
    "cpm", "cpc", "cost_per_result", "cost_per_thruplay",
    "cost_per_install", "cost_per_action", "frequency",
    "cost_per_lead", "cost_per_registration", "cost_per_purchase",
    "cost_per_3s_play", "cost_per_2s_play",
    "cost_per_outbound_click", "cost_per_lpv",
    "cost_per_engaged_view", "cost_per_conversion_lead",
    "cost_per_add_to_cart", "cost_per_checkout",
    "cost_per_content_view", "cost_per_add_payment_info",
]

# --- Metrics where higher is better ---
HIGHER_IS_BETTER = [
    "ctr", "hook_rate", "hold_rate", "engagement_rate",
    "conversion_rate", "results", "impressions", "reach",
    "outbound_ctr", "landing_page_views", "purchase_roas",
    "mobile_app_roas", "app_installs", "leads", "registrations",
    "video_completion_rate",
]

# --- Display formatting ---
METRIC_DISPLAY_NAMES = {
    "spend": "Spend", "impressions": "Impressions", "reach": "Reach",
    "results": "Results", "result_rate": "Result Rate (%)",
    "cpm": "CPM", "cpc": "CPC", "ctr": "CTR (%)", "ctr_all": "CTR All (%)",
    "cost_per_result": "Cost/Result", "frequency": "Frequency",
    "link_clicks": "Link Clicks", "clicks_all": "Clicks (All)",
    "outbound_clicks": "Outbound Clicks", "outbound_ctr": "Outbound CTR (%)",
    "cost_per_outbound_click": "Cost/Outbound Click",
    "unique_link_clicks": "Unique Link Clicks", "unique_ctr": "Unique CTR (%)",
    "hook_rate": "Hook Rate (%)", "hold_rate": "Hold Rate (%)",
    "cost_per_thruplay": "Cost/ThruPlay",
    "video_3s_views": "3s Video Views", "video_2s_continuous": "2s Continuous Views",
    "thruplay": "ThruPlays", "video_plays": "Video Plays",
    "video_p25": "Video 25%", "video_p50": "Video 50%",
    "video_p75": "Video 75%", "video_p95": "Video 95%", "video_p100": "Video 100%",
    "video_avg_play_time": "Avg Play Time", "video_pct_watched": "Avg % Watched",
    "cost_per_3s_play": "Cost/3s Play", "cost_per_2s_play": "Cost/2s Play",
    "video_completion_rate": "Completion Rate (%)",
    "scroll_stop_rate": "Scroll-Stop Rate (%)",
    "engagement_rate": "Engagement Rate (%)",
    "post_engagements": "Post Engagements", "post_reactions": "Post Reactions",
    "post_comments": "Post Comments", "post_shares": "Post Shares",
    "post_saves": "Post Saves",
    "app_installs": "App Installs", "cost_per_install": "Cost/Install",
    "cost_per_action": "Cost/Action", "app_store_clicks": "App Store Clicks",
    "mobile_app_actions": "Mobile App Actions", "mobile_app_roas": "Mobile App ROAS",
    "conversion_rate": "Conversion Rate (%)",
    "leads": "Leads", "cost_per_lead": "Cost/Lead",
    "registrations": "Registrations", "cost_per_registration": "Cost/Registration",
    "purchases": "Purchases", "cost_per_purchase": "Cost/Purchase",
    "purchase_value": "Purchase Value", "purchase_roas": "ROAS",
    "add_to_cart": "Add to Cart", "content_views": "Content Views",
    "landing_page_views": "Landing Page Views",
    "cost_per_lpv": "Cost/Landing Page View",
    "lp_conversion_rate": "LP Conversion Rate (%)",
    "quality_ranking": "Quality Ranking",
    "engagement_rate_ranking": "Engagement Ranking",
    "conversion_rate_ranking": "Conversion Ranking",
    "engaged_view_conversions": "Engaged-View Conversions",
    "cost_per_engaged_view": "Cost/Engaged-View Conv",
    "incremental_conversions": "Incremental Conversions",
    "conversion_leads": "Conversion Leads",
    "ig_profile_visits": "IG Profile Visits",
}

CURRENCY_SYMBOL = "\u20b9"  # Indian Rupee

# --- Quality Ranking Values (ordered best to worst) ---
QUALITY_RANKING_ORDER = [
    "Above Average",
    "Average",
    "Below Average (Bottom 35% of ads)",
    "Below Average (Bottom 20% of ads)",
    "Below Average (Bottom 10% of ads)",
]
