# Power BI Guide

## Source
Import `final_dataset/attractions_flat_powerbi.csv` (one row per attraction,
pre-joined with city/state/weather/tags — the shape Power BI wants). You can
also connect directly to `final_dataset/indian_itinerary.db` via an ODBC
SQLite driver if you want the normalized model with relationships instead.

## Suggested data model (if using the normalized DB)
Load `attractions`, `cities`, `states`, `weather`, `tags`, `destination_tags`
as separate tables and build relationships:
- `cities[state_id]` → `states[state_id]` (many-to-one)
- `attractions[city_id]` → `cities[city_id]` (many-to-one)
- `weather[city_id]` → `cities[city_id]` (one-to-one)
- `destination_tags` as a bridge table between `attractions` and `tags`
  (many-to-many)

## Suggested calculated columns
```DAX
Fee Bucket =
SWITCH(
    TRUE(),
    attractions[entrance_fee_inr] = 0, "Free",
    attractions[entrance_fee_inr] <= 50, "Low",
    attractions[entrance_fee_inr] <= 300, "Medium",
    "High"
)

Rating Stars = FORMAT(attractions[google_rating], "0.0") & " ★"
```

## Suggested DAX measures
```DAX
Total Attractions = COUNTROWS(attractions)

Avg Rating = AVERAGE(attractions[google_rating])

Avg Entrance Fee = AVERAGE(attractions[entrance_fee_inr])

% Free Attractions =
DIVIDE(
    CALCULATE(COUNTROWS(attractions), attractions[entrance_fee_inr] = 0),
    COUNTROWS(attractions)
)

Heritage Site Count =
CALCULATE(COUNTROWS(attractions), attractions[heritage_indicator] = TRUE)

Top State by Attractions =
CALCULATE(
    COUNTROWS(attractions),
    ALLEXCEPT(attractions, attractions[state_name])
)
```

## Suggested dashboard pages

1. **Overview** — KPI cards (Total Attractions, Avg Rating, % Free, Heritage
   Count) + India map (state_name choropleth) sized/colored by attraction
   count or avg rating.
2. **Budget Analysis** — Fee Bucket breakdown (donut), avg estimated daily
   cost by popularity_tier (bar), free-vs-paid by state (stacked bar).
3. **Season & Climate** — monsoon/summer/winter suitability by state
   (matrix/heatmap), avg_max_temp_c vs. attraction density (scatter).
4. **Destination Popularity** — treemap of attraction_type sized by
   google_review_count_lakhs, top 20 by popularity_tier table.
5. **Trip Planning** — slicers for budget_category, travel_complexity,
   family/solo/couple_score, filtered attraction table + map.

## Suggested visuals
- **Map**: state_name / city_name with lat-long *not available in source
  data* — use a filled/choropleth map keyed on state name instead of a
  point map (see `docs/ROADMAP.md` for the planned geocoding follow-up).
- **Treemap**: attraction_type × significance
- **KPI cards**: Total Attractions, Avg Rating, % Free, Heritage Count
- **Matrix/heatmap**: state × season suitability

## Suggested filters (report-level)
`state_name`, `budget_category`, `popularity_tier`, `travel_complexity`,
`heritage_indicator`, `wildlife_indicator`, `religious_indicator`
