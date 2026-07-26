# Data Dictionary

## `states`
| Column | Type | Description |
|---|---|---|
| state_id | UUID (PK) | Deterministic UUID5, stable across pipeline re-runs |
| state_name | text | Standardized Indian state/UT name |
| zone | text | Regional zone (Northern/Southern/Eastern/Western/Central), where known |

## `cities`
| Column | Type | Description |
|---|---|---|
| city_id | UUID (PK) | |
| city_name | text | Title-cased city name |
| state_id | UUID (FK -> states) | |

## `weather`
| Column | Type | Description |
|---|---|---|
| weather_id | UUID (PK) | |
| city_id | UUID (FK -> cities, unique) | 213 of 213 cities have a row; only 64 have non-null temperature values (rest are NULL by design — see below) |
| `{MON}_max_temp` / `{MON}_min_temp` | smallint | Monthly average max/min °C, Jan–Dec |
| avg_max_temp_c / avg_min_temp_c | numeric | Mean of monthly values (engineered) |
| summer/winter/monsoon_suitability | text | High/Medium/Low heuristic — see `docs/DATASET_UNDERSTANDING.md` for thresholds |

## `attractions`
Core fact table. 44 columns total; grouped below.

**Source columns**
| Column | Type | Notes |
|---|---|---|
| attraction_id | UUID (PK) | |
| city_id | UUID (FK -> cities) | Nullable if city couldn't be resolved |
| attraction_name | text | Not null |
| attraction_type | text | e.g. Temple, Fort, Beach, Museum |
| significance | text | e.g. Historical, Religious, Nature |
| establishment_year | smallint | NULL where source said "Unknown" |
| visit_duration_hrs | numeric | |
| google_rating | numeric(2,1) | 0–5, clipped if source had impossible values |
| entrance_fee_inr | integer | INR, 0 = free |
| airport_within_50km | boolean | |
| weekly_off_day | text | NULL = open every day (293/325 source rows had no listed off-day) |
| dslr_allowed | boolean | |
| google_review_count_lakhs | numeric | 1 lakh = 100,000 |
| best_time_of_day | text | Morning/Afternoon/Evening |
| zone | text | |

**Engineered columns** (formulas documented in `scripts/06_feature_engineering.py`)
| Column | Type | Notes |
|---|---|---|
| budget_category | text | Free / Low (≤₹50) / Medium (≤₹300) / High |
| adventure_score, photography_score, culture_score, history_score, nature_score, pilgrimage_score | int 0–10 | Keyword-match heuristic against type+significance |
| unesco/mountain/beach/wildlife/religious/heritage/adventure_indicator | boolean | Keyword-derived flags |
| popularity_tier | text | Niche/Emerging/Popular/Iconic, binned on review count |
| estimated_daily_cost_inr | int | entrance_fee_inr + flat ₹500 placeholder (documented assumption, not sourced data) |
| family/solo/couple_score | int | Simple rule-based heuristics |
| senior_friendly, backpacker_friendly, digital_nomad_friendly, weekend_friendly, road_trip_friendly | boolean | Rule-based |
| accessibility_score | int 0–10 | Airport proximity + short visit duration |
| travel_complexity | text | Low/Medium/High, derived from accessibility_score |
| suggested_season_note | text | Passthrough/annotation of best_time_of_day |

## `tags` / `destination_tags`
Controlled vocabulary (23 tags) many-to-many linked to attractions via keyword
matching on type/significance — avoids duplicate near-identical free-text tags.

## `sim_destinations`, `sim_users`, `sim_reviews`, `sim_user_history`
Synthetic Kaggle practice data. Column names preserved 1:1 from source (renamed
to snake_case only). **Do not treat as factual.** Useful for practicing joins,
recommendation-system features, and NLP on `review_text`. See
`docs/DATASET_UNDERSTANDING.md` for full rationale.
