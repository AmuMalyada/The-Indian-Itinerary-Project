"""
11_integrate_climate.py
-----------------------
Build destination-level monthly climate intelligence from public APIs.

Primary weather source:
    Open-Meteo Historical Weather API, aggregated from daily observations.

Supplementary UV source:
    NASA POWER monthly radiation API, parameter ALLSKY_SFC_UV_INDEX.

Fallback:
    raw_data/temperatureData.csv is used only when API temperature fields are
    missing. Every fallback is marked in `data_quality_note`.
"""

from __future__ import annotations

import json
import math
import sqlite3
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "raw_data"
PROCESSED_DIR = ROOT / "processed" / "06_features"
FINAL_DIR = ROOT / "final_dataset"
CACHE_DIR = RAW_DIR / "climate_cache"
DB_PATH = FINAL_DIR / "indian_itinerary.db"

HISTORICAL_START = "2015-01-01"
HISTORICAL_END = "2024-12-31"
RAINY_DAY_THRESHOLD_MM = 1.0
REQUEST_SLEEP_SECONDS = 0.15

MONTHS = [
    (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"), (5, "May"), (6, "Jun"),
    (7, "Jul"), (8, "Aug"), (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec"),
]


def log(message: str) -> None:
    print(f"[11_integrate_climate] {message}")


def read_json(url: str, cache_path: Path) -> dict | list:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    with urlopen(url, timeout=90) as response:
        payload = json.loads(response.read().decode("utf-8"))
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    time.sleep(REQUEST_SLEEP_SECONDS)
    return payload


def load_city_frame() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    cities = pd.read_sql_query(
        """
        SELECT c.city_id, c.city_name, s.state_id, s.state_name
        FROM cities c
        JOIN states s ON c.state_id = s.state_id
        ORDER BY s.state_name, c.city_name
        """,
        conn,
    )
    conn.close()
    return cities


def normalize_text(value: str | None) -> str:
    return "" if value is None else "".join(ch.lower() for ch in str(value) if ch.isalnum())


def geocode_city(city_name: str, state_name: str) -> dict:
    query = quote(f"{city_name}, {state_name}, India")
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=10&language=en&format=json"
    cache = CACHE_DIR / "geocoding" / f"{normalize_text(state_name)}_{normalize_text(city_name)}.json"
    payload = read_json(url, cache)
    results = payload.get("results", []) if isinstance(payload, dict) else []
    india_results = [r for r in results if r.get("country_code") == "IN"] or results
    state_key = normalize_text(state_name)

    def score(result: dict) -> tuple[int, int]:
        admin = normalize_text(result.get("admin1", ""))
        name = normalize_text(result.get("name", ""))
        return (int(state_key in admin), int(normalize_text(city_name) == name))

    if not india_results:
        return {
            "latitude": None,
            "longitude": None,
            "matched_place": None,
            "geocode_method": "unmatched",
        }

    best = sorted(india_results, key=score, reverse=True)[0]
    return {
        "latitude": best.get("latitude"),
        "longitude": best.get("longitude"),
        "matched_place": ", ".join(
            str(v) for v in [best.get("name"), best.get("admin1"), best.get("country")] if v
        ),
        "geocode_method": "state_matched" if score(best)[0] else "country_matched",
    }


def build_city_locations(cities: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, city in cities.iterrows():
        geo = geocode_city(city["city_name"], city["state_name"])
        rows.append({**city.to_dict(), **geo})
    locations = pd.DataFrame(rows)
    matched = locations["latitude"].notna().sum()
    log(f"Geocoded {matched}/{len(locations)} cities")
    return locations


def historical_url(batch: pd.DataFrame) -> str:
    params = {
        "latitude": ",".join(str(round(v, 5)) for v in batch["latitude"]),
        "longitude": ",".join(str(round(v, 5)) for v in batch["longitude"]),
        "start_date": HISTORICAL_START,
        "end_date": HISTORICAL_END,
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "relative_humidity_2m_mean",
            ]
        ),
        "timezone": "Asia/Kolkata",
    }
    return "https://archive-api.open-meteo.com/v1/archive?" + urlencode(params)


def iter_batches(df: pd.DataFrame, size: int = 20):
    for start in range(0, len(df), size):
        yield start // size + 1, df.iloc[start:start + size].copy()


def parse_historical_payload(payload: dict | list, batch: pd.DataFrame) -> list[dict]:
    records = payload if isinstance(payload, list) else [payload]
    rows: list[dict] = []
    for city, data in zip(batch.to_dict("records"), records):
        daily = data.get("daily", {}) if isinstance(data, dict) else {}
        if not daily or "time" not in daily:
            continue
        frame = pd.DataFrame(daily)
        frame["date"] = pd.to_datetime(frame["time"])
        frame["month_number"] = frame["date"].dt.month
        frame["rainy_flag"] = frame["precipitation_sum"].fillna(0) >= RAINY_DAY_THRESHOLD_MM
        grouped = frame.groupby("month_number", as_index=False).agg(
            avg_high_temp_c=("temperature_2m_max", "mean"),
            avg_low_temp_c=("temperature_2m_min", "mean"),
            avg_rainfall_mm=("precipitation_sum", "mean"),
            total_rainfall_mm=("precipitation_sum", "sum"),
            relative_humidity_pct=("relative_humidity_2m_mean", "mean"),
            rainy_day_observations=("rainy_flag", "sum"),
            observed_days=("rainy_flag", "count"),
        )
        for row in grouped.to_dict("records"):
            month_days = 31 if row["month_number"] in {1, 3, 5, 7, 8, 10, 12} else 30
            if row["month_number"] == 2:
                month_days = 28.25
            rainy_days = row["rainy_day_observations"] / row["observed_days"] * month_days
            rows.append(
                {
                    **city,
                    "month_number": int(row["month_number"]),
                    "avg_high_temp_c": round(row["avg_high_temp_c"], 1),
                    "avg_low_temp_c": round(row["avg_low_temp_c"], 1),
                    "avg_rainfall_mm": round(row["avg_rainfall_mm"] * month_days, 1),
                    "relative_humidity_pct": round(row["relative_humidity_pct"], 0),
                    "rainy_days": round(rainy_days, 1),
                    "source_primary": "Open-Meteo Historical Weather API",
                    "data_quality_note": "open_meteo_daily_2015_2024_climatology",
                }
            )
    return rows


def fetch_historical_monthly(locations: pd.DataFrame) -> pd.DataFrame:
    usable = locations.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    all_rows: list[dict] = []
    for batch_id, batch in iter_batches(usable):
        url = historical_url(batch)
        payload = read_json(url, CACHE_DIR / "open_meteo_historical" / f"batch_{batch_id}.json")
        all_rows.extend(parse_historical_payload(payload, batch))
        log(f"Processed Open-Meteo historical batch {batch_id}")
    return pd.DataFrame(all_rows)


def fetch_nasa_uv(row: pd.Series) -> dict[int, float | None]:
    if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
        return {m: None for m, _ in MONTHS}
    params = {
        "parameters": "ALLSKY_SFC_UV_INDEX",
        "community": "RE",
        "longitude": round(float(row["longitude"]), 5),
        "latitude": round(float(row["latitude"]), 5),
        "format": "JSON",
        "start": "2015",
        "end": "2024",
    }
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point?" + urlencode(params)
    cache = CACHE_DIR / "nasa_power_uv" / f"{row['city_id']}.json"
    try:
        payload = read_json(url, cache)
        values = payload["properties"]["parameter"]["ALLSKY_SFC_UV_INDEX"]
    except Exception as exc:
        log(f"NASA UV unavailable for {row['city_name']}: {exc}")
        return {m: None for m, _ in MONTHS}

    month_values: dict[int, list[float]] = {m: [] for m, _ in MONTHS}
    for key, value in values.items():
        if len(key) == 6 and key[-2:].isdigit() and value != -999:
            month_values[int(key[-2:])].append(float(value))
    return {
        month: round(sum(vals) / len(vals), 1) if vals else None
        for month, vals in month_values.items()
    }


def add_uv_index(monthly: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    uv_rows = []
    for _, row in locations.iterrows():
        for month, value in fetch_nasa_uv(row).items():
            uv_rows.append({"city_id": row["city_id"], "month_number": month, "uv_index": value})
    uv = pd.DataFrame(uv_rows)
    return monthly.merge(uv, on=["city_id", "month_number"], how="left")


def apply_temperature_fallback(monthly: pd.DataFrame, cities: pd.DataFrame) -> pd.DataFrame:
    fallback_path = RAW_DIR / "temperatureData.csv"
    if not fallback_path.exists():
        return monthly
    fallback = pd.read_csv(fallback_path)
    fallback["location_key"] = fallback["location"].map(normalize_text)
    city_keys = cities[["city_id", "city_name"]].copy()
    city_keys["location_key"] = city_keys["city_name"].map(normalize_text)
    fallback = city_keys.merge(fallback, on="location_key", how="left")
    df = monthly.copy()
    for month_num, month_name in MONTHS:
        mask = df["month_number"] == month_num
        max_col = f"{month_name.upper()}_MaxTemp"
        min_col = f"{month_name.upper()}_MinTemp"
        lookup = fallback[["city_id", max_col, min_col]].dropna(subset=[max_col, min_col])
        df = df.merge(
            lookup.rename(columns={max_col: "fallback_high", min_col: "fallback_low"}),
            on="city_id",
            how="left",
        )
        fill_high = mask & df["avg_high_temp_c"].isna() & df["fallback_high"].notna()
        fill_low = mask & df["avg_low_temp_c"].isna() & df["fallback_low"].notna()
        df.loc[fill_high, "avg_high_temp_c"] = df.loc[fill_high, "fallback_high"]
        df.loc[fill_low, "avg_low_temp_c"] = df.loc[fill_low, "fallback_low"]
        df.loc[fill_high | fill_low, "data_quality_note"] = "temperature_fallback_existing_csv"
        df = df.drop(columns=["fallback_high", "fallback_low"])
    return df


def weather_category(row: pd.Series) -> str:
    if row["rainy_days"] >= 12 or row["avg_rainfall_mm"] >= 180:
        return "Rainy"
    if row["avg_high_temp_c"] >= 40:
        return "Very Hot"
    if row["avg_high_temp_c"] >= 34:
        return "Hot"
    if row["avg_low_temp_c"] <= 8:
        return "Cold"
    return "Pleasant"


def month_range(months: list[int]) -> str:
    if not months:
        return "No ideal month"
    names = {num: name for num, name in MONTHS}
    runs = []
    start = prev = months[0]
    for month in months[1:]:
        if month == prev + 1:
            prev = month
        else:
            runs.append((start, prev))
            start = prev = month
    runs.append((start, prev))
    return ", ".join(names[a] if a == b else f"{names[a]}-{names[b]}" for a, b in runs)


def add_derived_fields(monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = monthly.copy()
    month_names = dict(MONTHS)
    df["month_name"] = df["month_number"].map(month_names)
    df["weather_category"] = df.apply(weather_category, axis=1)
    df["comfort_score"] = (
        100
        - (df[["avg_high_temp_c", "avg_low_temp_c"]].mean(axis=1) - 24).abs() * 4
        - df["rainy_days"].fillna(0) * 2
        - df["relative_humidity_pct"].fillna(60).sub(60).clip(lower=0) * 0.4
    ).clip(lower=0, upper=100).round(1)

    summaries = []
    for city_id, group in df.groupby("city_id"):
        group = group.sort_values("month_number")
        best_months = group[group["comfort_score"] >= max(55, group["comfort_score"].quantile(0.7))]["month_number"].tolist()
        avg_temp = ((group["avg_high_temp_c"] + group["avg_low_temp_c"]) / 2).mean()
        summaries.append(
            {
                "city_id": city_id,
                "best_months_to_visit": month_range(best_months),
                "warmest_month": group.loc[group["avg_high_temp_c"].idxmax(), "month_name"],
                "coldest_month": group.loc[group["avg_low_temp_c"].idxmin(), "month_name"],
                "wettest_month": group.loc[group["avg_rainfall_mm"].idxmax(), "month_name"],
                "average_annual_temp_c": round(avg_temp, 1),
                "average_annual_rainfall_mm": round(group["avg_rainfall_mm"].sum(), 1),
                "average_humidity_pct": round(group["relative_humidity_pct"].mean(), 0),
                "source_summary": "Open-Meteo daily climatology 2015-2024; NASA POWER UV 2015-2024 where available",
            }
        )
    return df, pd.DataFrame(summaries)


def infer_missing_cities(monthly: pd.DataFrame, locations: pd.DataFrame) -> pd.DataFrame:
    present = set(monthly["city_id"].unique()) if not monthly.empty else set()
    missing = locations[~locations["city_id"].isin(present)]
    if missing.empty:
        return monthly
    candidates = locations[locations["city_id"].isin(present)].copy()
    inferred_rows = []
    for _, city in missing.iterrows():
        if candidates.empty or pd.isna(city["latitude"]) or pd.isna(city["longitude"]):
            continue
        distances = candidates.apply(
            lambda r: math.dist([float(city["latitude"]), float(city["longitude"])], [float(r["latitude"]), float(r["longitude"])]),
            axis=1,
        )
        nearest = candidates.loc[distances.idxmin()]
        proxy = monthly[monthly["city_id"] == nearest["city_id"]].copy()
        proxy["city_id"] = city["city_id"]
        proxy["city_name"] = city["city_name"]
        proxy["state_id"] = city["state_id"]
        proxy["state_name"] = city["state_name"]
        proxy["matched_place"] = nearest["matched_place"]
        proxy["geocode_method"] = "nearest_city_inference"
        proxy["data_quality_note"] = f"inferred_from_nearest_city:{nearest['city_name']}"
        inferred_rows.append(proxy)
    if inferred_rows:
        monthly = pd.concat([monthly, *inferred_rows], ignore_index=True)
    return monthly


def create_destination_climate(summary: pd.DataFrame) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    attractions = pd.read_sql_query(
        """
        SELECT attraction_id, attraction_name, city_id
        FROM attractions
        ORDER BY attraction_name
        """,
        conn,
    )
    conn.close()
    return attractions.merge(summary, on="city_id", how="left")


def write_outputs(monthly: pd.DataFrame, destination: pd.DataFrame) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(PROCESSED_DIR / "climate_monthly.csv", index=False)
    destination.to_csv(PROCESSED_DIR / "destination_climate.csv", index=False)
    monthly.to_csv(FINAL_DIR / "climate_monthly.csv", index=False)
    destination.to_csv(FINAL_DIR / "destination_climate.csv", index=False)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("DROP TABLE IF EXISTS destination_climate;")
    conn.execute("DROP TABLE IF EXISTS climate_monthly;")
    conn.execute(
        """
        CREATE TABLE climate_monthly (
            climate_monthly_id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id TEXT NOT NULL,
            month_number INTEGER NOT NULL CHECK (month_number BETWEEN 1 AND 12),
            month_name TEXT NOT NULL,
            avg_high_temp_c REAL,
            avg_low_temp_c REAL,
            avg_rainfall_mm REAL,
            relative_humidity_pct REAL,
            rainy_days REAL,
            uv_index REAL,
            weather_category TEXT CHECK (weather_category IN ('Pleasant','Hot','Very Hot','Cold','Rainy')),
            comfort_score REAL,
            source_primary TEXT,
            data_quality_note TEXT,
            matched_place TEXT,
            geocode_method TEXT,
            FOREIGN KEY (city_id) REFERENCES cities(city_id),
            UNIQUE (city_id, month_number)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE destination_climate (
            attraction_id TEXT PRIMARY KEY,
            attraction_name TEXT NOT NULL,
            city_id TEXT,
            best_months_to_visit TEXT,
            warmest_month TEXT,
            coldest_month TEXT,
            wettest_month TEXT,
            average_annual_temp_c REAL,
            average_annual_rainfall_mm REAL,
            average_humidity_pct REAL,
            source_summary TEXT,
            FOREIGN KEY (attraction_id) REFERENCES attractions(attraction_id),
            FOREIGN KEY (city_id) REFERENCES cities(city_id)
        )
        """
    )
    monthly[[
        "city_id", "month_number", "month_name", "avg_high_temp_c", "avg_low_temp_c",
        "avg_rainfall_mm", "relative_humidity_pct", "rainy_days", "uv_index",
        "weather_category", "comfort_score", "source_primary", "data_quality_note",
        "matched_place", "geocode_method",
    ]].to_sql("climate_monthly", conn, if_exists="append", index=False)
    destination.to_sql("destination_climate", conn, if_exists="append", index=False)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_climate_monthly_city ON climate_monthly(city_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_destination_climate_city ON destination_climate(city_id);")
    conn.commit()
    conn.close()


def run() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    cities = load_city_frame()
    locations = build_city_locations(cities)
    monthly = fetch_historical_monthly(locations)
    monthly = infer_missing_cities(monthly, locations)
    monthly = add_uv_index(monthly, locations)
    monthly = apply_temperature_fallback(monthly, cities)
    monthly, summary = add_derived_fields(monthly)
    destination = create_destination_climate(summary)
    write_outputs(monthly, destination)
    log(f"Wrote {len(monthly)} monthly climate rows and {len(destination)} destination climate rows")


if __name__ == "__main__":
    run()
