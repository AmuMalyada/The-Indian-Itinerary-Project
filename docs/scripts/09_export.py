"""
09_export.py
-------------
Export final, flattened CSVs for Power BI / Tableau / Kaggle-republish use
(these tools work best against denormalized-but-tidy tables, not raw
snake-case FK-only exports).
"""
import pandas as pd
from common import PROCESSED_DIR, FINAL_DIR, get_logger

log = get_logger("09_export")


def load(name: str) -> pd.DataFrame:
    p = PROCESSED_DIR / "06_features" / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def run() -> None:
    states = load("states")
    cities = load("cities")
    attractions = load("attractions")
    weather = load("weather")
    tags = load("tags")
    destination_tags = load("destination_tags")

    # Normalized exports (for SQL practice / ML)
    for name, df in [("states", states), ("cities", cities), ("attractions", attractions),
                      ("weather", weather), ("tags", tags), ("destination_tags", destination_tags),
                      ("sim_destinations", load("sim_destinations")), ("sim_users", load("sim_users")),
                      ("sim_reviews", load("sim_reviews")), ("sim_user_history", load("sim_user_history"))]:
        df.to_csv(FINAL_DIR / f"{name}.csv", index=False)

    # BI-friendly flattened view: one row per attraction with state/city/weather joined in
    flat = (
        attractions
        .merge(cities, on="city_id", how="left")
        .merge(states, on="state_id", how="left", suffixes=("", "_state"))
        .merge(weather, on="city_id", how="left", suffixes=("", "_weather"))
    )
    tag_agg = (
        destination_tags.merge(tags, on="tag_id")
        .groupby("attraction_id")["tag_name"].apply(lambda s: ", ".join(sorted(s)))
        .rename("tags")
    )
    flat = flat.merge(tag_agg, on="attraction_id", how="left")
    flat.to_csv(FINAL_DIR / "attractions_flat_powerbi.csv", index=False)
    log.info(f"Wrote attractions_flat_powerbi.csv: {flat.shape}")

    for name in ["climate_monthly", "destination_climate"]:
        p = PROCESSED_DIR / "06_features" / f"{name}.csv"
        if p.exists():
            df = pd.read_csv(p)
            df.to_csv(FINAL_DIR / f"{name}.csv", index=False)
            log.info(f"Wrote {name}.csv: {df.shape}")

    log.info(f"All final CSVs written to {FINAL_DIR}")


if __name__ == "__main__":
    run()
