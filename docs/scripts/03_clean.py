"""
03_clean.py
-----------
Industrial-grade cleaning: dedup, fix encodings, remove impossible values.
Standardization of *names/casing* is deliberately deferred to 04_standardize.py
so each stage has one job (clean vs. standardize) and the log stays readable.
"""
import pandas as pd
from common import (
    INTERMEDIATE_DIR, PROCESSED_DIR, get_logger, clean_text,
    parse_establishment_year, log_decision, save_parquet_and_csv,
)

log = get_logger("03_clean")


def load(key: str) -> pd.DataFrame:
    p = INTERMEDIATE_DIR / "01_ingested" / f"{key}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def clean_top_indian_places(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")

    before = len(df)
    df = df.drop_duplicates(subset=["Name", "City", "State"]).copy()
    dropped = before - len(df)
    if dropped:
        log_decision("03_clean", "top_indian_places", "drop_exact_duplicates", f"{dropped} rows")

    for col in ["Zone", "State", "City", "Name", "Type", "Significance", "Best Time to visit",
                "Airport with 50km Radius", "DSLR Allowed", "Weekly Off"]:
        df[col] = df[col].map(clean_text)

    df["Establishment Year"] = df["Establishment Year"].map(parse_establishment_year)
    log_decision("03_clean", "top_indian_places", "parse_establishment_year",
                 "'Unknown'/blank -> NULL instead of magic value 0")

    # Impossible-value guards
    before_rating = df["Google review rating"].copy()
    df.loc[(df["Google review rating"] < 0) | (df["Google review rating"] > 5), "Google review rating"] = None
    if (before_rating.notna() & df["Google review rating"].isna()).sum():
        log_decision("03_clean", "top_indian_places", "clip_invalid_rating", "ratings outside [0,5] -> NULL")

    df.loc[df["Entrance Fee in INR"] < 0, "Entrance Fee in INR"] = None
    df.loc[df["time needed to visit in hrs"] <= 0, "time needed to visit in hrs"] = None

    # "Weekly Off" genuinely NULL for ~90% of rows in source (attraction open every day) —
    # keep as NULL, do NOT invent "Monday" etc. Document explicitly.
    log_decision("03_clean", "top_indian_places", "keep_null_weekly_off",
                 "293/325 rows have no listed weekly-off day in source; left NULL "
                 "(interpreted downstream as 'open all days'), not imputed.")

    return df.reset_index(drop=True)


def clean_temperature_data(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["location"]).copy()
    dropped = before - len(df)
    if dropped:
        log_decision("03_clean", "temperature_data", "drop_exact_duplicates", f"{dropped} rows")
    df["location"] = df["location"].map(clean_text)
    temp_cols = [c for c in df.columns if c != "location"]
    for c in temp_cols:
        # Indian temps: impossible outside roughly -10..55 C
        df.loc[(df[c] < -10) | (df[c] > 55), c] = None
    return df.reset_index(drop=True)


def clean_sim_destinations(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["DestinationID"]).copy()
    if before - len(df):
        log_decision("03_clean", "sim_destinations", "drop_duplicate_ids", f"{before - len(df)} rows")
    for col in ["Name", "State", "Type", "BestTimeToVisit"]:
        df[col] = df[col].map(clean_text)
    df.loc[(df["Popularity"] < 0) | (df["Popularity"] > 10), "Popularity"] = None
    return df.reset_index(drop=True)


def clean_sim_users(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["UserID"]).copy()
    if before - len(df):
        log_decision("03_clean", "sim_users", "drop_duplicate_ids", f"{before - len(df)} rows")
    for col in ["Name", "Email", "Preferences", "Gender"]:
        df[col] = df[col].map(clean_text)
    df.loc[df["NumberOfAdults"] < 0, "NumberOfAdults"] = None
    df.loc[df["NumberOfChildren"] < 0, "NumberOfChildren"] = None
    return df.reset_index(drop=True)


def clean_sim_reviews(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["ReviewID"]).copy()
    if before - len(df):
        log_decision("03_clean", "sim_reviews", "drop_duplicate_ids", f"{before - len(df)} rows")
    df["ReviewText"] = df["ReviewText"].map(clean_text)
    df.loc[(df["Rating"] < 1) | (df["Rating"] > 5), "Rating"] = None
    return df.reset_index(drop=True)


def clean_sim_user_history(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=["HistoryID"]).copy()
    if before - len(df):
        log_decision("03_clean", "sim_user_history", "drop_duplicate_ids", f"{before - len(df)} rows")
    df["VisitDate"] = pd.to_datetime(df["VisitDate"], errors="coerce")
    df.loc[(df["ExperienceRating"] < 1) | (df["ExperienceRating"] > 5), "ExperienceRating"] = None
    return df.reset_index(drop=True)


CLEANERS = {
    "top_indian_places": clean_top_indian_places,
    "temperature_data": clean_temperature_data,
    "sim_destinations": clean_sim_destinations,
    "sim_reviews": clean_sim_reviews,
    "sim_user_history": clean_sim_user_history,
    "sim_users": clean_sim_users,
}


def run() -> dict[str, pd.DataFrame]:
    out = {}
    for key, fn in CLEANERS.items():
        df = fn(load(key))
        save_parquet_and_csv(df, PROCESSED_DIR / "03_cleaned", key)
        log.info(f"Cleaned {key}: {df.shape}")
        out[key] = df
    return out


if __name__ == "__main__":
    run()
