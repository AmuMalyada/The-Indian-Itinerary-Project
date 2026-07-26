from pathlib import Path
import importlib.util

import pandas as pd
import plotly.express as px
import streamlit as st

_utils_path = Path(__file__).resolve().parent / "utils.py"
_utils_spec = importlib.util.spec_from_file_location("streamlit_local_utils", _utils_path)
_utils = importlib.util.module_from_spec(_utils_spec)
_utils_spec.loader.exec_module(_utils)

CSV_PATH = _utils.CSV_PATH
DB_PATH = _utils.DB_PATH
STATE_COORDS = _utils.STATE_COORDS
get_climate_summary = _utils.get_climate_summary
load_city_weather = _utils.load_city_weather
load_dataset = _utils.load_dataset
style_plot = _utils.style_plot

ROOT = Path(__file__).resolve().parent.parent

if not CSV_PATH.exists() and not DB_PATH.exists():
    raise FileNotFoundError(
        "No dataset found. Expected either:\n"
        f"  CSV: {CSV_PATH}\n"
        f"  DB:  {DB_PATH}\n"
        "load_dataset() looks for the CSV first, then falls back to the DB."
    )

st.set_page_config(page_title="The Indian Itinerary Dashboard", page_icon="🗺️", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .stTabs [data-testid="stTab"] { color: #CBD5E1; }
    .stTabs [data-testid="stTab"][aria-selected="true"] { color: #10B981; }
    div[data-testid="stMetric"] { background-color: #111827; border: 1px solid #334155; border-radius: 12px; padding: 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_data():
    return load_dataset()


def build_sidebar_filters(df: pd.DataFrame):
    st.sidebar.header("Global Filters")
    state_filter = st.sidebar.multiselect("State or UT", sorted(df["state_name"].dropna().unique()), default=[], key="state_filter")
    complexity_filter = st.sidebar.multiselect("Travel Complexity", sorted(df["travel_complexity"].dropna().unique()), default=[], key="complexity_filter")
    popularity_filter = st.sidebar.multiselect("Popularity Tier", sorted(df["popularity_tier"].dropna().unique()), default=[], key="popularity_filter")
    search_term = st.sidebar.text_input("Search Destination", key="search_term")

    filtered = df.copy()
    if state_filter:
        filtered = filtered[filtered["state_name"].isin(state_filter)]
    if complexity_filter:
        filtered = filtered[filtered["travel_complexity"].isin(complexity_filter)]
    if popularity_filter:
        filtered = filtered[filtered["popularity_tier"].isin(popularity_filter)]
    if search_term:
        filtered = filtered[filtered["attraction_name"].str.contains(search_term, case=False, na=False)]
    return filtered


st.title("The Indian Itinerary Dashboard")
st.caption("Executive travel analytics built on the repository's curated dataset")

df = load_data()
filtered = build_sidebar_filters(df)
weather_df = load_city_weather()
temp_columns = [col for col in weather_df.columns if col != "city_name"]
usable_city_mask = weather_df[temp_columns].notna().any(axis=1)
usable_city_names = set(weather_df.loc[usable_city_mask, "city_name"].dropna())
matched_destinations = int(filtered["city_name"].isin(usable_city_names).sum())
print(f"[climate-coverage] filtered_city_matches={matched_destinations}/{len(filtered)}")

if filtered.empty:
    st.warning("No matching destinations for the current filters.")
    st.stop()

pages = st.tabs([
    "Executive Dashboard",
    "Destination Explorer",
    "Climate & Temperatures",
    "Season & Climate",
    "Tourism Insights",
    "Recommendation Explorer",
    "Data Quality Dashboard",
])

with pages[0]:
    st.subheader("Executive Dashboard")

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    metrics = [
        ("Total Attractions", filtered["attraction_name"].nunique()),
        ("Total Cities", filtered["city_name"].nunique()),
        ("Total States & UTs", filtered["state_name"].nunique()),
        ("Avg Rating", round(filtered["google_rating"].mean(), 1)),
        ("Avg Visit Duration", round(filtered["visit_duration_hrs"].mean(), 1)),
        ("Popularity Index", round(filtered["google_review_count_lakhs"].mean(), 2)),
    ]
    for col, (label, value) in zip([col1, col2, col3, col4, col5, col6], metrics):
        col.metric(label, value)

    left, right = st.columns([2, 1])
    with left:
        state_summary = filtered.groupby("state_name", as_index=False).agg(
            attractions=("attraction_name", "nunique"),
            avg_rating=("google_rating", "mean"),
        )
        state_summary["lat"] = state_summary["state_name"].map(lambda value: STATE_COORDS.get(value, (None, None))[0])
        state_summary["lon"] = state_summary["state_name"].map(lambda value: STATE_COORDS.get(value, (None, None))[1])
        state_summary = state_summary.dropna(subset=["lat", "lon"])
        fig_map = px.scatter_mapbox(
            state_summary,
            lat="lat",
            lon="lon",
            size="attractions",
            color="avg_rating",
            hover_name="state_name",
            hover_data={"attractions": True, "avg_rating": True},
            color_continuous_scale="Viridis",
            size_max=40,
            zoom=3,
        )
        fig_map.update_layout(
            mapbox_style="carto-positron",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            mapbox=dict(center=dict(lat=22.5, lon=78.96), zoom=3),
            title="Attractions by State & UT",
        )
        fig_map = style_plot(fig_map)
        st.plotly_chart(fig_map, use_container_width=True)
    with right:
        top_states = state_summary.sort_values("attractions", ascending=False).head(10)
        fig_bar = px.bar(
            top_states,
            x="attractions",
            y="state_name",
            orientation="h",
            text="attractions",
            color="attractions",
            color_continuous_scale="Viridis",
        )
        fig_bar = style_plot(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        category_counts = filtered["attraction_type"].value_counts().head(12)
        fig_pie = px.pie(category_counts, values=category_counts.values, names=category_counts.index, hole=0.4)
        fig_pie = style_plot(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_b:
        fig_hist = px.histogram(filtered, x="google_rating", nbins=15, color_discrete_sequence=["#10B981"])
        fig_hist = style_plot(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)

    st.success("Executive summary: the current filter selection highlights the most attractive destinations by state/UT density, budget fit, and rating quality.")
    st.subheader("Top destinations in this view")
    top_destinations = filtered.sort_values(["google_rating", "google_review_count_lakhs"], ascending=[False, False]).head(10)
    st.dataframe(
        top_destinations[["attraction_name", "city_name", "state_name", "google_rating", "visit_duration_hrs"]],
        use_container_width=True,
    )
    csv = filtered[["attraction_name", "city_name", "state_name", "attraction_type", "google_rating"]].to_csv(index=False)
    st.download_button("Download filtered results", csv, file_name="executive_dashboard.csv", mime="text/csv")

with pages[1]:
    st.subheader("Destination Explorer")
    table = filtered[[
        "attraction_name",
        "city_name",
        "state_name",
        "attraction_type",
        "google_rating",
        "visit_duration_hrs",
        "popularity_tier",
    ]].sort_values("google_rating", ascending=False).head(200)
    st.dataframe(table, use_container_width=True)
    csv = table.to_csv(index=False)
    st.download_button("Download destination table", csv, file_name="destination_explorer.csv", mime="text/csv")

with pages[2]:
    st.subheader("Climate & Temperatures")
    st.info("Monthly temperature patterns and climate suitability for selected destinations.")

    destination_options = sorted(filtered["attraction_name"].dropna().unique())
    selected_destination = st.selectbox("Select destination", destination_options, key="climate_destination")
    selected_row = filtered[filtered["attraction_name"] == selected_destination].iloc[0]
    climate_summary = get_climate_summary(selected_row["city_name"], weather_df)

    if climate_summary is None:
        st.info("Monthly climate data is not yet available for this destination's city. Coverage currently spans a subset of cities in the dataset.")
    else:
        monthly_df = pd.DataFrame(climate_summary["monthly"])
        monthly_table = monthly_df.copy()
        monthly_table["High (deg C)"] = monthly_table["high"].apply(lambda value: "—" if pd.isna(value) else f"{value:.1f}")
        monthly_table["Low (deg C)"] = monthly_table["low"].apply(lambda value: "—" if pd.isna(value) else f"{value:.1f}")
        monthly_table["Missing"] = monthly_table["missing"].apply(lambda value: "Yes" if value else "No")

        st.subheader("Monthly High/Low by City")
        st.dataframe(monthly_table[["month", "High (deg C)", "Low (deg C)", "Missing"]], use_container_width=True)

        chart_df = monthly_df[~(monthly_df["high"].isna() & monthly_df["low"].isna())].copy()
        if not chart_df.empty:
            chart_long = chart_df.melt(
                id_vars=["month"],
                value_vars=["high", "low"],
                var_name="Series",
                value_name="Temperature (deg C)",
            )
            chart_long = chart_long.dropna(subset=["Temperature (deg C)"])
            chart_long["Series"] = chart_long["Series"].map({"high": "High", "low": "Low"})
            fig_temp = px.line(
                chart_long,
                x="month",
                y="Temperature (deg C)",
                color="Series",
                markers=True,
                color_discrete_map={"High": "#F59E0B", "Low": "#0EA5E9"},
            )
            fig_temp = style_plot(fig_temp)
            st.plotly_chart(fig_temp, use_container_width=True)

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Hottest Month", climate_summary["hottest_month"] or "N/A")
        metric_col2.metric("Coldest Month", climate_summary["coldest_month"] or "N/A")
        annual_avg_display = "N/A" if climate_summary["annual_avg_c"] is None else f"{climate_summary['annual_avg_c']:.1f}"
        metric_col3.metric("Annual Average (deg C)", annual_avg_display)

        if climate_summary["best_months"]:
            st.write("Best months to visit:", ", ".join(climate_summary["best_months"]))
        else:
            st.write("Best months to visit: no month currently meets the 20-30 deg C high and >=10 deg C low threshold.")

        st.caption(f"{climate_summary['data_completeness']} | Source: temperatureData.csv (Kaggle India temperature dataset)")

with pages[3]:
    st.subheader("Season & Climate")
    st.info("Seasonal suitability is derived from weather and attraction metadata in the shipped dataset.")
    st.dataframe(filtered[["attraction_name", "state_name", "summer_suitability", "winter_suitability", "monsoon_suitability", "suggested_season_note"]].head(200), use_container_width=True)
    csv = filtered[["attraction_name", "state_name", "summer_suitability", "winter_suitability", "monsoon_suitability", "suggested_season_note"]].to_csv(index=False)
    st.download_button("Download season view", csv, file_name="season_climate.csv", mime="text/csv")

with pages[4]:
    st.subheader("Tourism Insights")
    fig = px.treemap(filtered, path=[px.Constant("All"), "state_name", "attraction_type"], values="google_review_count_lakhs", color="google_rating")
    fig = style_plot(fig)
    st.plotly_chart(fig, use_container_width=True)
    csv = filtered[["state_name", "attraction_type", "google_review_count_lakhs", "google_rating"]].to_csv(index=False)
    st.download_button("Download tourism insights", csv, file_name="tourism_insights.csv", mime="text/csv")

with pages[5]:
    st.subheader("Recommendation Explorer")
    st.dataframe(filtered[["attraction_name", "family_score", "solo_score", "couple_score", "backpacker_friendly", "digital_nomad_friendly", "senior_friendly"]].sort_values("family_score", ascending=False).head(200), use_container_width=True)
    csv = filtered[["attraction_name", "family_score", "solo_score", "couple_score", "backpacker_friendly", "digital_nomad_friendly", "senior_friendly"]].to_csv(index=False)
    st.download_button("Download recommendation view", csv, file_name="recommendations.csv", mime="text/csv")

with pages[6]:
    st.subheader("Data Quality Dashboard")
    st.metric("Rows Loaded", len(df))
    st.metric("Missing Values", int(df.isna().sum().sum()))
    st.metric("Duplicate Attraction Names", int(df["attraction_name"].duplicated().sum()))
    st.dataframe(df.isna().sum().reset_index().rename(columns={"index": "field", 0: "missing_values"}).sort_values("missing_values", ascending=False).head(20), use_container_width=True)
