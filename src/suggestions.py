"""Per-creative suggestion engine aligned with Meta's creative-focused targeting.

Meta's Advantage+ and creative-focused targeting means the algorithm optimizes
delivery based on creative quality. Suggestions focus on actionable creative
improvements rather than audience/targeting changes.
"""

import pandas as pd
import numpy as np


# --- Creative Status Definitions ---
# Each status is a clear action signal for the user:
#   SCALE         -> Performing great. Increase budget, create similar variations.
#   MONITOR       -> Doing okay. Keep watching, no action needed right now.
#   TEST VARIATION-> Has potential but needs iteration to unlock it.
#   REPLACE       -> Old/fatigued creative. Prepare a fresh replacement.
#   PAUSE         -> Burning money with poor/no results. Stop spend immediately.
#   LEARNING      -> Too new/too little data. Let Meta's algorithm learn.

STATUS_SCALE = "SCALE"
STATUS_MONITOR = "MONITOR"
STATUS_TEST = "TEST VARIATION"
STATUS_REPLACE = "REPLACE"
STATUS_PAUSE = "PAUSE"
STATUS_LEARNING = "LEARNING"


def generate_suggestions(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'suggestion' and 'creative_status' columns with per-creative analysis."""
    if df.empty:
        return df

    suggestions = []
    statuses = []

    # Pre-compute medians for benchmarking
    medians = {}
    for col in ["ctr", "cpm", "cpc", "cost_per_result", "frequency",
                 "hook_rate", "hold_rate", "engagement_rate", "conversion_rate",
                 "scroll_stop_rate", "video_completion_rate", "lp_conversion_rate"]:
        if col in df.columns:
            medians[col] = df[col].median()

    for _, row in df.iterrows():
        s = _suggest_for_creative(row, medians, df)
        status = _determine_status(row, medians, df)
        suggestions.append(s)
        statuses.append(status)

    df["suggestion"] = suggestions
    df["creative_status"] = statuses
    return df


def _determine_status(row: pd.Series, medians: dict, df: pd.DataFrame) -> str:
    """Determine the actionable status for a creative.

    Priority order (highest to lowest):
      1. PAUSE    - zero results with spend, or extreme cost inefficiency
      2. LEARNING - too new / too little data for Meta to optimize
      3. REPLACE  - old + declining, or fatigued
      4. SCALE    - clearly winning
      5. TEST VARIATION - has potential but needs work
      6. MONITOR  - everything else
    """
    spend = row.get("spend", 0)
    results = row.get("results")
    cpr = row.get("cost_per_result")
    cpr_med = medians.get("cost_per_result")
    ctr = row.get("ctr")
    ctr_med = medians.get("ctr")
    freq = row.get("frequency")
    age = row.get("creative_age_days")
    quality = row.get("quality_ranking")
    tier = row.get("performance_tier", "")
    days_active = row.get("days_active")

    # ------------------------------------------------------------------
    # 1. PAUSE - spending with zero results or extreme cost blowout
    # ------------------------------------------------------------------
    if pd.notna(spend) and spend > 0 and (pd.isna(results) or results == 0):
        return STATUS_PAUSE

    if (pd.notna(cpr) and pd.notna(cpr_med) and cpr_med > 0
            and cpr > cpr_med * 2.5
            and pd.notna(spend) and spend > 50):
        return STATUS_PAUSE

    # ------------------------------------------------------------------
    # 2. LEARNING - very new creative or very little data
    # ------------------------------------------------------------------
    if pd.notna(age) and age <= 5:
        # New creative, let algorithm learn
        if pd.notna(spend) and spend < 200:
            return STATUS_LEARNING

    if pd.notna(days_active) and days_active <= 2:
        if pd.notna(spend) and spend < 100:
            return STATUS_LEARNING

    # ------------------------------------------------------------------
    # 3. REPLACE - old creative with poor/declining performance
    # ------------------------------------------------------------------
    if pd.notna(age) and age > 30:
        # Old creative with above-median cost or high frequency
        if pd.notna(cpr) and pd.notna(cpr_med) and cpr > cpr_med:
            return STATUS_REPLACE
        if pd.notna(freq) and freq > 2.5:
            return STATUS_REPLACE

    if pd.notna(freq) and freq > 3.0:
        # Frequency fatigue regardless of age
        if pd.notna(cpr) and pd.notna(cpr_med) and cpr > cpr_med * 1.2:
            return STATUS_REPLACE

    # Below-average quality ranking with high CPR = Meta is penalizing
    if isinstance(quality, str) and "below" in quality.lower():
        if pd.notna(cpr) and pd.notna(cpr_med) and cpr > cpr_med * 1.5:
            return STATUS_REPLACE

    # ------------------------------------------------------------------
    # 4. SCALE - clearly winning creative
    # ------------------------------------------------------------------
    if tier == "High Performer":
        if pd.notna(freq) and freq < 2.0:
            return STATUS_SCALE
        # Even with rising frequency, if cost is still great, scale
        if pd.notna(cpr) and pd.notna(cpr_med) and cpr < cpr_med * 0.6:
            return STATUS_SCALE

    # Strong metrics even if not formally "High Performer" tier
    if (pd.notna(cpr) and pd.notna(cpr_med) and cpr_med > 0
            and cpr < cpr_med * 0.5
            and pd.notna(ctr) and pd.notna(ctr_med) and ctr_med > 0
            and ctr > ctr_med * 1.3):
        return STATUS_SCALE

    # ------------------------------------------------------------------
    # 5. TEST VARIATION - has some strengths but needs iteration
    # ------------------------------------------------------------------
    # Good CTR but poor conversion (people click but don't convert)
    if (pd.notna(ctr) and pd.notna(ctr_med) and ctr_med > 0
            and ctr > ctr_med * 1.2
            and pd.notna(cpr) and pd.notna(cpr_med) and cpr > cpr_med):
        return STATUS_TEST

    # High Performer with rising frequency - create variation before fatigue
    if tier == "High Performer" and pd.notna(freq) and freq >= 2.0:
        return STATUS_TEST

    # Average tier with some positive signal (decent CTR or decent CPR)
    if tier == "Average":
        has_decent_ctr = pd.notna(ctr) and pd.notna(ctr_med) and ctr >= ctr_med * 0.9
        has_decent_cpr = pd.notna(cpr) and pd.notna(cpr_med) and cpr <= cpr_med * 1.1
        if has_decent_ctr and has_decent_cpr:
            return STATUS_TEST

    # Low Performer but with decent CTR - the creative hooks but doesn't convert
    if tier == "Low Performer":
        if pd.notna(ctr) and pd.notna(ctr_med) and ctr > ctr_med:
            return STATUS_TEST

    # ------------------------------------------------------------------
    # 6. MONITOR - no red flags, no green flags
    # ------------------------------------------------------------------
    return STATUS_MONITOR


def _suggest_for_creative(row: pd.Series, medians: dict, df: pd.DataFrame) -> str:
    """Generate a suggestion string for a single creative."""
    tips = []
    creative_type = row.get("creative_type", "")

    # --- Quality Ranking Insights ---
    quality = row.get("quality_ranking")
    if isinstance(quality, str) and "below" in quality.lower():
        tips.append(f"Quality Ranking: {quality} -- Meta penalizes low-quality ads with higher CPM. Improve visual quality and relevance.")

    eng_ranking = row.get("engagement_rate_ranking")
    if isinstance(eng_ranking, str) and "below" in eng_ranking.lower():
        tips.append(f"Engagement Ranking: {eng_ranking} -- Ad is less engaging than competitors. Test new hooks/CTAs.")

    conv_ranking = row.get("conversion_rate_ranking")
    if isinstance(conv_ranking, str) and "below" in conv_ranking.lower():
        tips.append(f"Conversion Ranking: {conv_ranking} -- Post-click experience may be weak. Review landing page and app store listing.")

    # --- Frequency fatigue ---
    freq = row.get("frequency")
    if pd.notna(freq) and freq > 3.0:
        tips.append(f"High frequency ({freq:.1f}) -- creative fatigue likely. Refresh or create new variation.")
    elif pd.notna(freq) and freq > 2.0:
        tips.append(f"Frequency rising ({freq:.1f}) -- monitor for fatigue, prepare replacement creative.")

    # --- Cost efficiency ---
    cpr = row.get("cost_per_result")
    cpr_med = medians.get("cost_per_result")
    if pd.notna(cpr) and pd.notna(cpr_med) and cpr_med > 0:
        if cpr > cpr_med * 1.5:
            tips.append("Cost/result is 50%+ above median -- consider pausing or reworking creative messaging.")
        elif cpr < cpr_med * 0.7:
            tips.append("Strong cost efficiency -- scale spend on this creative. Test similar variations.")

    # --- CTR ---
    ctr = row.get("ctr")
    ctr_med = medians.get("ctr")
    if pd.notna(ctr) and pd.notna(ctr_med):
        if ctr < 0.5:
            tips.append("Very low CTR (<0.5%) -- weak CTA or irrelevant messaging. Rework headline/CTA copy.")
        elif ctr_med > 0 and ctr < ctr_med * 0.6:
            tips.append("CTR well below average -- test different hooks, headlines, or visual elements.")
        elif ctr_med > 0 and ctr > ctr_med * 1.5:
            tips.append("Excellent CTR -- leverage this creative hook style in new variations.")

    # --- CPM ---
    cpm = row.get("cpm")
    cpm_med = medians.get("cpm")
    if pd.notna(cpm) and pd.notna(cpm_med) and cpm_med > 0:
        if cpm > cpm_med * 1.5:
            tips.append("High CPM -- Meta may be limiting reach due to low relevance. Improve creative quality score.")

    # --- Landing Page View drop-off ---
    lp_views = row.get("landing_page_views")
    link_clicks = row.get("link_clicks")
    if pd.notna(lp_views) and pd.notna(link_clicks) and link_clicks > 0:
        lp_rate = lp_views / link_clicks
        if lp_rate < 0.5:
            tips.append(f"Only {lp_rate*100:.0f}% of link clicks result in landing page views -- slow load time or redirect issues.")

    # --- Video-specific ---
    if creative_type == "video":
        hook = row.get("hook_rate")
        hold = row.get("hold_rate")
        hook_med = medians.get("hook_rate")
        hold_med = medians.get("hold_rate")
        scroll_stop = row.get("scroll_stop_rate")

        if pd.notna(scroll_stop) and scroll_stop < 10:
            tips.append(f"Low scroll-stop rate ({scroll_stop:.1f}%) -- first 2 seconds fail to grab attention. Use bold visuals/text overlay.")

        if pd.notna(hook):
            if hook < 15:
                tips.append(f"Low hook rate ({hook:.1f}%) -- first 3 seconds not engaging. Use stronger opening: text overlay, motion, or problem statement.")
            elif pd.notna(hook_med) and hook_med > 0 and hook > hook_med * 1.3:
                tips.append(f"Strong hook rate ({hook:.1f}%) -- opening is effective. Maintain this style.")

        if pd.notna(hold):
            if hold < 20:
                tips.append(f"Low hold rate ({hold:.1f}%) -- viewers drop off after hook. Shorten video or improve mid-section pacing.")
            elif pd.notna(hold_med) and hold_med > 0 and hold > hold_med * 1.3:
                tips.append(f"Great hold rate ({hold:.1f}%) -- content retains attention well.")

        # Completion funnel drop-off
        p25 = row.get("video_p25")
        p75 = row.get("video_p75")
        if pd.notna(p25) and pd.notna(p75) and p25 > 0:
            drop_off = (1 - p75 / p25) * 100
            if drop_off > 70:
                tips.append("Severe drop-off between 25%-75% -- tighten the middle section or add pattern interrupts.")

        # Video completion rate
        comp_rate = row.get("video_completion_rate")
        if pd.notna(comp_rate) and comp_rate < 2:
            tips.append(f"Very low completion rate ({comp_rate:.1f}%) -- video may be too long or loses interest. Consider shorter format.")

    # --- Image-specific ---
    if creative_type == "image":
        eng = row.get("engagement_rate")
        eng_med = medians.get("engagement_rate")
        if pd.notna(eng) and pd.notna(eng_med) and eng_med > 0:
            if eng < eng_med * 0.5:
                tips.append("Low engagement -- try bolder visuals, social proof, or user-generated content style.")
            elif eng > eng_med * 1.5:
                tips.append("High engagement -- this visual style resonates. Create more variations.")

        # Post saves (strong signal)
        saves = row.get("post_saves")
        if pd.notna(saves) and saves > 0:
            tips.append(f"{int(saves)} post saves -- strong intent signal. This creative resonates deeply.")

    # --- Creative age ---
    age = row.get("creative_age_days")
    if pd.notna(age) and age > 30 and pd.notna(cpr) and pd.notna(cpr_med) and cpr > cpr_med:
        tips.append(f"Creative is {int(age)} days old with declining performance -- replace with fresh creative.")
    elif pd.notna(age) and age > 21:
        tips.append(f"Creative is {int(age)} days old -- monitor closely for performance decay.")

    # --- Spending with zero results ---
    spend = row.get("spend", 0)
    results = row.get("results", 0)
    if pd.notna(spend) and spend > 0 and (pd.isna(results) or results == 0):
        tips.append("Spending with zero results -- Meta's algorithm has no conversion signal. Pause or restructure.")

    if not tips:
        if pd.notna(cpr) and pd.notna(cpr_med) and cpr <= cpr_med:
            tips.append("Performing well -- maintain current spend and monitor.")
        else:
            tips.append("Performance is average -- test new creative angles to find winning variations.")

    return " | ".join(tips)
