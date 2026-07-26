"""
05_merge.py
-----------
Build the normalized relational model from the standardized stage outputs.

Two honest design decisions baked in here (see docs/DATASET_UNDERSTANDING.md):
1. States/Cities are derived from `top_indian_places` (the real dataset) and
   `sim_destinations.state_name` is matched against the SAME states table by
   name — no fabricated FK between sim_destinations and real attractions.
2. Weather joins to Cities by name match only; unmatched cities keep NULL
   climate fields (64/214 matched) rather than an invented average.
"""
import uuid
import pandas as pd
from common import PROCESSED_DIR, INTERMEDIATE_DIR, get_logger, slugify, log_decision, save_parquet_and_csv

log = get_logger("05_merge")


def load(key: str) -> pd.DataFrame:
    p = PROCESSED_DIR / "04_standardized" / f"{key}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def deterministic_uuid(*parts: str) -> str:
    """Stable UUID5 so re-running the pipeline yields identical IDs (important
    for reproducibility and for downstream tools that cache by ID)."""
    name = "|".join(str(p) for p in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, name))


def build_states(tip: pd.DataFrame, sim_dest: pd.DataFrame) -> pd.DataFrame:
    names = sorted(set(tip["state_name"].dropna()) | set(sim_dest["state_name"].dropna()))
    states = pd.DataFrame({"state_name": names})
    states["state_id"] = states["state_name"].map(lambda n: deterministic_uuid("state", n))
    states["zone"] = states["state_name"].map(
        lambda n: tip.loc[tip["state_name"] == n, "zone"].dropna().iloc[0]
        if (tip["state_name"] == n).any() and tip.loc[tip["state_name"] == n, "zone"].notna().any()
        else None
    )
    return states[["state_id", "state_name", "zone"]]


def build_cities(tip: pd.DataFrame, states: pd.DataFrame) -> pd.DataFrame:
    grp = tip[["city_name", "state_name"]].dropna().drop_duplicates()
    grp = grp.merge(states[["state_id", "state_name"]], on="state_name", how="left")
    grp["city_id"] = grp.apply(lambda r: deterministic_uuid("city", r["city_name"], r["state_name"]), axis=1)
    return grp[["city_id", "city_name", "state_id"]]


def build_weather(temp: pd.DataFrame, cities: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (weather_wide, coverage_note_df)."""
    temp = temp.copy()
    temp["_match_key"] = temp["location_name"].str.lower().str.strip()
    cities = cities.copy()
    cities["_match_key"] = cities["city_name"].str.lower().str.strip()

    weather = cities[["city_id", "_match_key"]].merge(temp, on="_match_key", how="left")
    matched = weather["location_name"].notna().sum()
    log_decision("05_merge", "weather", "join_on_city_name",
                 f"{matched}/{len(cities)} cities matched to a temperature record")
    weather["weather_id"] = weather["city_id"].map(lambda c: deterministic_uuid("weather", c))
    month_cols = [c for c in temp.columns if c not in ("location_name", "_match_key")]
    weather = weather[["weather_id", "city_id"] + month_cols]
    return weather.drop(columns=["_match_key"], errors="ignore"), None


def build_tags() -> pd.DataFrame:
    """Controlled vocabulary of tags derived from Type + Significance values
    seen in the source data (not free text -> avoids duplicate near-identical
    tags like 'wildlife' vs 'Wildlife Sanctuary')."""
    tag_names = [
        "Heritage", "Religious", "Nature", "Adventure", "Beach", "Wildlife",
        "Museum", "Fort", "Palace", "Lake", "Waterfall", "Trekking", "Cave",
        "Market", "Food", "Pilgrimage", "UNESCO", "Mountain", "Scenic",
        "Recreational", "Cultural", "Architectural", "Photography",
    ]
    tags = pd.DataFrame({"tag_name": tag_names})
    tags["tag_id"] = tags["tag_name"].map(lambda n: deterministic_uuid("tag", n))
    return tags[["tag_id", "tag_name"]]


TYPE_SIG_TO_TAGS = {
    # attraction_type / significance keyword -> tag_name(s)
    "temple": ["Religious", "Heritage", "Pilgrimage"],
    "fort": ["Heritage", "Architectural", "Photography"],
    "palace": ["Heritage", "Architectural", "Photography"],
    "museum": ["Museum", "Cultural"],
    "beach": ["Beach", "Nature", "Recreational"],
    "lake": ["Lake", "Nature", "Scenic"],
    "waterfall": ["Waterfall", "Nature", "Scenic"],
    "national park": ["Wildlife", "Nature", "Adventure"],
    "cave": ["Cave", "Adventure", "Heritage"],
    "market": ["Market", "Recreational"],
    "religious": ["Religious", "Pilgrimage"],
    "historical": ["Heritage", "Photography"],
    "wildlife": ["Wildlife", "Nature"],
    "scenic": ["Scenic", "Photography", "Nature"],
    "trekking": ["Trekking", "Adventure"],
    "food": ["Food"],
    "architectural": ["Architectural", "Heritage", "Photography"],
}


def build_destination_tags(attractions: pd.DataFrame, tags: pd.DataFrame) -> pd.DataFrame:
    tag_id_by_name = dict(zip(tags["tag_name"], tags["tag_id"]))
    rows = []
    for _, r in attractions.iterrows():
        haystack = f"{r['attraction_type']} {r['significance']}".lower()
        matched_tags = set()
        for keyword, tag_list in TYPE_SIG_TO_TAGS.items():
            if keyword in haystack:
                matched_tags.update(tag_list)
        for t in matched_tags:
            rows.append({"attraction_id": r["attraction_id"], "tag_id": tag_id_by_name[t]})
    return pd.DataFrame(rows).drop_duplicates()


def run() -> dict[str, pd.DataFrame]:
    tip = load("top_indian_places")
    temp = load("temperature_data")
    sim_dest = load("sim_destinations")
    sim_users = load("sim_users")
    sim_reviews = load("sim_reviews")
    sim_history = load("sim_user_history")

    states = build_states(tip, sim_dest)
    cities = build_cities(tip, states)

    attractions = tip.merge(cities[["city_id", "city_name"]], on="city_name", how="left")
    attractions["attraction_id"] = attractions.apply(
        lambda r: deterministic_uuid("attraction", r["attraction_name"], r["city_name"]), axis=1
    )
    attractions = attractions.drop(columns=["state_name", "city_name"])

    weather, _ = build_weather(temp, cities)
    tags = build_tags()
    destination_tags = build_destination_tags(attractions, tags)

    # sim_* domain: FK to states table by name (only real, verifiable link
    # between the two domains), everything else keeps its own ID space.
    sim_dest = sim_dest.merge(states[["state_id", "state_name"]], on="state_name", how="left")
    sim_dest = sim_dest.drop(columns=["state_name"])

    tables = {
        "states": states,
        "cities": cities,
        "attractions": attractions,
        "weather": weather,
        "tags": tags,
        "destination_tags": destination_tags,
        "sim_destinations": sim_dest,
        "sim_users": sim_users,
        "sim_reviews": sim_reviews,
        "sim_user_history": sim_history,
    }
    for name, df in tables.items():
        save_parquet_and_csv(df, INTERMEDIATE_DIR / "05_merged", name)
        log.info(f"Built {name}: {df.shape}")
    return tables


if __name__ == "__main__":
    run()
