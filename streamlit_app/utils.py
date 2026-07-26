from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "final_dataset" / "indian_itinerary.db"
CSV_PATH = ROOT / "final_dataset" / "attractions_flat_powerbi.csv"

THEME_COLORS = {
    "background": "#0F172A",
    "panel": "#111827",
    "text": "#F8FAFC",
    "muted": "#CBD5E1",
    "accent": "#10B981",
    "amber": "#F59E0B",
    "blue": "#0EA5E9",
}

STATE_COORDS = {
    "Andhra Pradesh": (15.9129, 79.7400),
    "Arunachal Pradesh": (27.1004, 93.6160),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Delhi": (28.6139, 77.2090),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Andaman And Nicobar Islands": (11.7401, 92.6586),
    "Puducherry": (11.9416, 79.8083),
    "Daman And Diu": (20.4283, 72.8397),
    "Chandigarh": (30.7333, 76.7794),
}


def load_dataset() -> pd.DataFrame:
    if CSV_PATH.exists():
        return pd.read_csv(CSV_PATH)
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM attractions", conn)
    conn.close()
    return df


def style_plot(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0F172A",
        plot_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="#0F172A", font=dict(color="#F8FAFC")),
    )
    return fig


def build_metric_card(title: str, value: str | int | float, subtitle: str = "") -> None:
    return None


@st.cache_data(show_spinner=False)
def load_city_weather() -> pd.DataFrame:
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    query = (
        "SELECT c.city_name, "
        "w.JAN_MaxTemp, w.JAN_MinTemp, "
        "w.FEB_MaxTemp, w.FEB_MinTemp, "
        "w.MAR_MaxTemp, w.MAR_MinTemp, "
        "w.APR_MaxTemp, w.APR_MinTemp, "
        "w.MAY_MaxTemp, w.MAY_MinTemp, "
        "w.JUN_MaxTemp, w.JUN_MinTemp, "
        "w.JUL_MaxTemp, w.JUL_MinTemp, "
        "w.AUG_MaxTemp, w.AUG_MinTemp, "
        "w.SEP_MaxTemp, w.SEP_MinTemp, "
        "w.OCT_MaxTemp, w.OCT_MinTemp, "
        "w.NOV_MaxTemp, w.NOV_MinTemp, "
        "w.DEC_MaxTemp, w.DEC_MinTemp "
        "FROM weather w "
        "JOIN cities c ON c.city_id = w.city_id"
    )
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def get_climate_summary(city_name: str, weather_df: pd.DataFrame) -> dict | None:
    monthly_columns = [
        ("January", "JAN_MaxTemp", "JAN_MinTemp"),
        ("February", "FEB_MaxTemp", "FEB_MinTemp"),
        ("March", "MAR_MaxTemp", "MAR_MinTemp"),
        ("April", "APR_MaxTemp", "APR_MinTemp"),
        ("May", "MAY_MaxTemp", "MAY_MinTemp"),
        ("June", "JUN_MaxTemp", "JUN_MinTemp"),
        ("July", "JUL_MaxTemp", "JUL_MinTemp"),
        ("August", "AUG_MaxTemp", "AUG_MinTemp"),
        ("September", "SEP_MaxTemp", "SEP_MinTemp"),
        ("October", "OCT_MaxTemp", "OCT_MinTemp"),
        ("November", "NOV_MaxTemp", "NOV_MinTemp"),
        ("December", "DEC_MaxTemp", "DEC_MinTemp"),
    ]

    city_rows = weather_df[weather_df["city_name"] == city_name]
    if city_rows.empty:
        return None

    row = city_rows.iloc[0]
    all_values = [row[max_col] for _, max_col, _ in monthly_columns] + [row[min_col] for _, _, min_col in monthly_columns]
    if all(pd.isna(value) for value in all_values):
        return None

    monthly = []
    high_candidates: list[tuple[str, float]] = []
    low_candidates: list[tuple[str, float]] = []
    annual_values: list[float] = []
    best_months: list[str] = []
    available_months = 0

    for month_name, max_col, min_col in monthly_columns:
        high_raw = row[max_col]
        low_raw = row[min_col]
        high = None if pd.isna(high_raw) else float(high_raw)
        low = None if pd.isna(low_raw) else float(low_raw)
        missing = high is None or low is None

        if not missing:
            available_months += 1

        if high is not None:
            high_candidates.append((month_name, high))
            annual_values.append(high)
        if low is not None:
            low_candidates.append((month_name, low))
            annual_values.append(low)

        if high is not None and low is not None and 20 <= high <= 30 and low >= 10:
            best_months.append(month_name)

        monthly.append({
            "month": month_name,
            "high": high,
            "low": low,
            "missing": missing,
        })

    hottest_month = max(high_candidates, key=lambda item: item[1])[0] if high_candidates else None
    coldest_month = min(low_candidates, key=lambda item: item[1])[0] if low_candidates else None
    annual_avg_c = round(sum(annual_values) / len(annual_values), 1) if annual_values else None

    return {
        "monthly": monthly,
        "hottest_month": hottest_month,
        "coldest_month": coldest_month,
        "annual_avg_c": annual_avg_c,
        "best_months": best_months,
        "data_completeness": f"{available_months}/12 months available",
    }
