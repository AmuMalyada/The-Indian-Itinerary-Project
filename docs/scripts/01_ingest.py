"""
01_ingest.py
------------
Load every raw CSV exactly as provided, do NOT clean anything here.
The only job of this stage is: read raw bytes -> typed DataFrame -> intermediate/.

Keeping ingestion separate from cleaning means we always have an untouched
snapshot of "what the source data actually said" to compare against later.
"""
import pandas as pd
from common import RAW_DIR, INTERMEDIATE_DIR, get_logger, save_parquet_and_csv, reset_decision_log, log_decision

log = get_logger("01_ingest")

SOURCES = {
    "top_indian_places": "Top Indian Places to Visit.csv",
    "temperature_data": "temperatureData.csv",
    "sim_destinations": "Expanded_Destinations.csv",
    "sim_reviews": "Final_Updated_Expanded_Reviews.csv",
    "sim_user_history": "Final_Updated_Expanded_UserHistory.csv",
    "sim_users": "Final_Updated_Expanded_Users.csv",
}


def run() -> dict[str, pd.DataFrame]:
    reset_decision_log()
    frames = {}
    for key, filename in SOURCES.items():
        path = RAW_DIR / filename
        df = pd.read_csv(path)
        log.info(f"Loaded {filename}: {df.shape[0]} rows x {df.shape[1]} cols")
        save_parquet_and_csv(df, INTERMEDIATE_DIR / "01_ingested", key)
        log_decision("01_ingest", key, "loaded_raw", f"{path.name} -> {df.shape}")
        frames[key] = df
    return frames


if __name__ == "__main__":
    run()
