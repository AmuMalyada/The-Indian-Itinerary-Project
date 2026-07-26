"""
07_quality_checks.py
---------------------
Automated validation gate. Raises AssertionError (and fails CI) if any check
fails. This is the same logic used in tests/test_data_quality.py, wired here
so the pipeline itself refuses to publish a broken dataset.
"""
import pandas as pd
from common import PROCESSED_DIR, get_logger

log = get_logger("07_quality_checks")


def load(name: str) -> pd.DataFrame:
    p = PROCESSED_DIR / "06_features" / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def run() -> list[str]:
    results = []

    attractions = load("attractions")
    states = load("states")
    cities = load("cities")
    weather = load("weather")
    destination_tags = load("destination_tags")
    tags = load("tags")

    def check(name, condition):
        status = "PASS" if condition else "FAIL"
        results.append(f"[{status}] {name}")
        log.info(f"{status}: {name}")

    check("attractions: no duplicate attraction_id",
          attractions["attraction_id"].is_unique)
    check("attractions: attraction_name never null",
          attractions["attraction_name"].notna().all())
    check("attractions: google_rating within [0,5]",
          attractions["google_rating"].dropna().between(0, 5).all())
    check("attractions: entrance_fee_inr non-negative",
          (attractions["entrance_fee_inr"].dropna() >= 0).all())
    check("attractions: referential integrity to cities",
          attractions["city_id"].dropna().isin(cities["city_id"]).all())
    check("cities: referential integrity to states",
          cities["state_id"].dropna().isin(states["state_id"]).all())
    check("weather: referential integrity to cities",
          weather["city_id"].isin(cities["city_id"]).all())
    check("destination_tags: referential integrity to attractions",
          destination_tags["attraction_id"].isin(attractions["attraction_id"]).all())
    check("destination_tags: referential integrity to tags",
          destination_tags["tag_id"].isin(tags["tag_id"]).all())
    check("states: no duplicate state_id", states["state_id"].is_unique)
    check("cities: no duplicate city_id", cities["city_id"].is_unique)

    n_fail = sum(1 for r in results if r.startswith("[FAIL"))
    log.info(f"Quality checks complete: {len(results) - n_fail}/{len(results)} passed")
    if n_fail:
        raise AssertionError(f"{n_fail} data quality check(s) failed:\n" + "\n".join(r for r in results if "FAIL" in r))

    return results


if __name__ == "__main__":
    run()
