"""
06_feature_engineering.py
--------------------------
Derive analytics features from the merged tables. Every feature here is a
deterministic function of columns that actually exist in the source data —
nothing is randomly generated. Where a "score" is a heuristic (e.g.
adventure_score), the formula is explicit and documented, not a black box.
"""
import numpy as np
import pandas as pd
from common import INTERMEDIATE_DIR, PROCESSED_DIR, get_logger, save_parquet_and_csv, log_decision

log = get_logger("06_feature_engineering")


def load(name: str) -> pd.DataFrame:
    p = INTERMEDIATE_DIR / "05_merged" / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def budget_category(fee):
    if pd.isna(fee):
        return "Unknown"
    if fee == 0:
        return "Free"
    if fee <= 50:
        return "Low"
    if fee <= 300:
        return "Medium"
    return "High"


def keyword_score(haystack: str, keywords: list[str], weight: int = 2) -> int:
    """Simple, transparent 0-10 heuristic: count keyword hits, cap at 10."""
    if not isinstance(haystack, str):
        return 0
    hits = sum(1 for k in keywords if k in haystack.lower())
    return min(10, hits * weight + (2 if hits else 0))


def enrich_attractions(attractions: pd.DataFrame, destination_tags: pd.DataFrame, tags: pd.DataFrame) -> pd.DataFrame:
    df = attractions.copy()
    df["budget_category"] = df["entrance_fee_inr"].map(budget_category)

    haystack = (df["attraction_type"].fillna("") + " " + df["significance"].fillna("")).str.lower()

    df["adventure_score"] = haystack.map(lambda h: keyword_score(h, ["trek", "adventure", "cave", "national park", "wildlife"]))
    df["photography_score"] = haystack.map(lambda h: keyword_score(h, ["fort", "palace", "monument", "scenic", "lake", "waterfall"]))
    df["culture_score"] = haystack.map(lambda h: keyword_score(h, ["museum", "cultural", "artistic", "market"]))
    df["history_score"] = haystack.map(lambda h: keyword_score(h, ["historical", "fort", "palace", "tomb", "archaeological", "monument"]))
    df["nature_score"] = haystack.map(lambda h: keyword_score(h, ["nature", "lake", "waterfall", "national park", "botanical", "wildlife"]))
    df["pilgrimage_score"] = haystack.map(lambda h: keyword_score(h, ["religious", "temple", "spiritual", "pilgrimage"]))

    df["unesco_indicator"] = haystack.str.contains("unesco")
    df["mountain_indicator"] = haystack.str.contains("hill|mountain|trek")
    df["beach_indicator"] = haystack.str.contains("beach")
    df["wildlife_indicator"] = haystack.str.contains("wildlife|national park|sanctuary")
    df["religious_indicator"] = haystack.str.contains("religious|temple|pilgrimage|spiritual")
    df["heritage_indicator"] = haystack.str.contains("historical|heritage|fort|palace|monument|archaeological")
    df["adventure_indicator"] = haystack.str.contains("adventure|trek|cave")

    df["dslr_friendly"] = df["dslr_allowed"].fillna(False)
    df["weekend_friendly"] = df["visit_duration_hrs"].fillna(0) <= 4
    df["road_trip_friendly"] = df["airport_within_50km"].fillna(False) == False  # noqa: E712  remote-ish spots

    df["popularity_tier"] = pd.cut(
        df["google_review_count_lakhs"].fillna(0),
        bins=[-0.01, 0.1, 0.5, 1.5, np.inf],
        labels=["Niche", "Emerging", "Popular", "Iconic"],
    ).astype(str)

    df["recommended_trip_length_hrs"] = df["visit_duration_hrs"]
    df["estimated_daily_cost_inr"] = df["entrance_fee_inr"].fillna(0) + 500  # +500 flat for food/local travel, documented assumption
    log_decision("06_feature_engineering", "attractions", "estimated_daily_cost_inr",
                 "entrance_fee_inr + flat INR 500 (food/local transport placeholder); "
                 "documented assumption, not sourced from data.")

    df["family_score"] = np.where(df["weekend_friendly"] & ~df["adventure_indicator"], 8, 5)
    df["solo_score"] = np.where(df["adventure_indicator"] | df["heritage_indicator"], 8, 5)
    df["couple_score"] = np.where(df["photography_score"] >= 4, 8, 5)
    df["senior_friendly"] = (df["visit_duration_hrs"].fillna(0) <= 3) & (~df["adventure_indicator"])
    df["backpacker_friendly"] = df["budget_category"].isin(["Free", "Low"])
    df["digital_nomad_friendly"] = df["airport_within_50km"].fillna(False)

    df["accessibility_score"] = (
        df["airport_within_50km"].fillna(False).astype(int) * 5
        + (df["visit_duration_hrs"].fillna(5) <= 3).astype(int) * 5
    )

    df["travel_complexity"] = np.select(
        [df["accessibility_score"] >= 8, df["accessibility_score"] >= 4],
        ["Low", "Medium"],
        default="High",
    )

    def season_from_best_time(text):
        if not isinstance(text, str):
            return "Unknown"
        t = text.lower()
        if "morning" in t or "evening" in t:
            return "Any season (time-of-day dependent)"
        return text

    df["suggested_season_note"] = df["best_time_of_day"].map(season_from_best_time)

    return df


def enrich_weather(weather: pd.DataFrame) -> pd.DataFrame:
    df = weather.copy()
    max_cols = [c for c in df.columns if c.endswith("_MaxTemp")]
    min_cols = [c for c in df.columns if c.endswith("_MinTemp")]
    if max_cols and min_cols:
        df["avg_max_temp_c"] = df[max_cols].mean(axis=1, skipna=True)
        df["avg_min_temp_c"] = df[min_cols].mean(axis=1, skipna=True)
        summer_max = df[["APR_MaxTemp", "MAY_MaxTemp", "JUN_MaxTemp"]].mean(axis=1, skipna=True)
        winter_min = df[["DEC_MinTemp", "JAN_MinTemp", "FEB_MinTemp"]].mean(axis=1, skipna=True)
        monsoon_max = df[["JUN_MaxTemp", "JUL_MaxTemp", "AUG_MaxTemp", "SEP_MaxTemp"]].mean(axis=1, skipna=True)

        df["summer_suitability"] = np.select(
            [summer_max <= 30, summer_max <= 38], ["High", "Medium"], default="Low"
        )
        df["winter_suitability"] = np.select(
            [winter_min >= 12, winter_min >= 5], ["High", "Medium"], default="Low"
        )
        df["monsoon_suitability"] = np.select(
            [monsoon_max <= 28, monsoon_max <= 33], ["High", "Medium"], default="Low"
        )
    return df


def run() -> dict[str, pd.DataFrame]:
    attractions = load("attractions")
    destination_tags = load("destination_tags")
    tags = load("tags")
    weather = load("weather")

    attractions_fe = enrich_attractions(attractions, destination_tags, tags)
    weather_fe = enrich_weather(weather)

    save_parquet_and_csv(attractions_fe, PROCESSED_DIR / "06_features", "attractions")
    save_parquet_and_csv(weather_fe, PROCESSED_DIR / "06_features", "weather")
    log.info(f"Feature-engineered attractions: {attractions_fe.shape}")
    log.info(f"Feature-engineered weather: {weather_fe.shape}")

    # pass through untouched tables so 08_generate_database.py has one place to read from
    for name in ["states", "cities", "tags", "destination_tags",
                 "sim_destinations", "sim_users", "sim_reviews", "sim_user_history"]:
        df = load(name)
        save_parquet_and_csv(df, PROCESSED_DIR / "06_features", name)

    return {"attractions": attractions_fe, "weather": weather_fe}


if __name__ == "__main__":
    run()
