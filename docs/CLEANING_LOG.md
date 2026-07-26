# Cleaning & Transformation Log

_Auto-generated from every `log_decision(...)` call made during the pipeline run._


## 01_ingest

- **top_indian_places** — loaded_raw: Top Indian Places to Visit.csv -> (325, 16)
- **temperature_data** — loaded_raw: temperatureData.csv -> (264, 25)
- **sim_destinations** — loaded_raw: Expanded_Destinations.csv -> (1000, 6)
- **sim_reviews** — loaded_raw: Final_Updated_Expanded_Reviews.csv -> (999, 5)
- **sim_user_history** — loaded_raw: Final_Updated_Expanded_UserHistory.csv -> (999, 5)
- **sim_users** — loaded_raw: Final_Updated_Expanded_Users.csv -> (999, 7)

## 03_clean

- **top_indian_places** — drop_exact_duplicates: 2 rows
- **top_indian_places** — parse_establishment_year: 'Unknown'/blank -> NULL instead of magic value 0
- **top_indian_places** — keep_null_weekly_off: 293/325 rows have no listed weekly-off day in source; left NULL (interpreted downstream as 'open all days'), not imputed.

## 04_standardize

- **top_indian_places** — standardize_state_names: ['Andaman and Nicobar Islands', 'Daman and Diu', 'Maharastra'] -> corrected
- **top_indian_places** — rename_to_snake_case: all columns renamed to snake_case for SQL/BI consistency

## 05_merge

- **weather** — join_on_city_name: 64/213 cities matched to a temperature record

## 06_feature_engineering

- **attractions** — estimated_daily_cost_inr: entrance_fee_inr + flat INR 500 (food/local transport placeholder); documented assumption, not sourced from data.