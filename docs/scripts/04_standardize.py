"""
04_standardize.py
------------------
Standardize state names, casing, categorical vocabularies, and units so that
"Maharastra"/"Maharashtra" or "beach"/"Beach" never appear as two different
values in the final dataset.
"""
import pandas as pd
from common import (
    PROCESSED_DIR, get_logger, standardize_state_name, title_case,
    yes_no_to_bool, log_decision, save_parquet_and_csv,
)

log = get_logger("04_standardize")


def load(key: str) -> pd.DataFrame:
    p = PROCESSED_DIR / "03_cleaned" / f"{key}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def standardize_top_indian_places(df: pd.DataFrame) -> pd.DataFrame:
    before_states = set(df["State"].unique())
    df["State"] = df["State"].map(standardize_state_name)
    after_states = set(df["State"].unique())
    if before_states != after_states:
        log_decision("04_standardize", "top_indian_places", "standardize_state_names",
                     f"{sorted(before_states - after_states)} -> corrected")

    df["City"] = df["City"].map(title_case)
    df["Name"] = df["Name"].map(lambda v: v.strip() if isinstance(v, str) else v)
    df["Type"] = df["Type"].map(title_case)
    df["Significance"] = df["Significance"].map(title_case)
    df["Zone"] = df["Zone"].map(title_case)

    df["DSLR Allowed"] = df["DSLR Allowed"].map(yes_no_to_bool)
    df["Airport with 50km Radius"] = df["Airport with 50km Radius"].map(yes_no_to_bool)

    df = df.rename(columns={
        "Zone": "zone",
        "State": "state_name",
        "City": "city_name",
        "Name": "attraction_name",
        "Type": "attraction_type",
        "Establishment Year": "establishment_year",
        "time needed to visit in hrs": "visit_duration_hrs",
        "Google review rating": "google_rating",
        "Entrance Fee in INR": "entrance_fee_inr",
        "Airport with 50km Radius": "airport_within_50km",
        "Weekly Off": "weekly_off_day",
        "Significance": "significance",
        "DSLR Allowed": "dslr_allowed",
        "Number of google review in lakhs": "google_review_count_lakhs",
        "Best Time to visit": "best_time_of_day",
    })
    log_decision("04_standardize", "top_indian_places", "rename_to_snake_case",
                 "all columns renamed to snake_case for SQL/BI consistency")
    return df


def standardize_temperature_data(df: pd.DataFrame) -> pd.DataFrame:
    df["location"] = df["location"].map(title_case)
    df = df.rename(columns={"location": "location_name"})
    return df


def standardize_sim_destinations(df: pd.DataFrame) -> pd.DataFrame:
    df["State"] = df["State"].map(standardize_state_name)
    df["Name"] = df["Name"].map(lambda v: v.strip() if isinstance(v, str) else v)
    df["Type"] = df["Type"].map(title_case)
    df = df.rename(columns={
        "DestinationID": "sim_destination_id",
        "Name": "destination_name",
        "State": "state_name",
        "Type": "destination_type",
        "Popularity": "popularity_score",
        "BestTimeToVisit": "best_time_to_visit",
    })
    return df


def standardize_sim_users(df: pd.DataFrame) -> pd.DataFrame:
    df["Gender"] = df["Gender"].map(title_case)
    df = df.rename(columns={
        "UserID": "sim_user_id",
        "Name": "user_name",
        "Email": "email",
        "Preferences": "preferences_raw",
        "Gender": "gender",
        "NumberOfAdults": "num_adults",
        "NumberOfChildren": "num_children",
    })
    return df


def standardize_sim_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "ReviewID": "sim_review_id",
        "DestinationID": "sim_destination_id",
        "UserID": "sim_user_id",
        "Rating": "rating",
        "ReviewText": "review_text",
    })
    return df


def standardize_sim_user_history(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "HistoryID": "sim_history_id",
        "UserID": "sim_user_id",
        "DestinationID": "sim_destination_id",
        "VisitDate": "visit_date",
        "ExperienceRating": "experience_rating",
    })
    return df


STANDARDIZERS = {
    "top_indian_places": standardize_top_indian_places,
    "temperature_data": standardize_temperature_data,
    "sim_destinations": standardize_sim_destinations,
    "sim_reviews": standardize_sim_reviews,
    "sim_user_history": standardize_sim_user_history,
    "sim_users": standardize_sim_users,
}


def run() -> dict[str, pd.DataFrame]:
    out = {}
    for key, fn in STANDARDIZERS.items():
        df = fn(load(key))
        save_parquet_and_csv(df, PROCESSED_DIR / "04_standardized", key)
        log.info(f"Standardized {key}: {df.shape}")
        out[key] = df
    return out


if __name__ == "__main__":
    run()
