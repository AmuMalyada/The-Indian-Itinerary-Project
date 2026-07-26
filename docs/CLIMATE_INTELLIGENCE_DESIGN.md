# Climate Intelligence Dataset Recommendation

## 1. Recommended Dataset

### **temperatureData.csv** (Existing in Repository)

**Why This Dataset:**
- ✅ **Already available** locally (no API calls needed)
- ✅ **Comprehensive coverage**: 460+ Indian cities and towns
- ✅ **Granular data**: Monthly max/min temperatures for all 12 months
- ✅ **Unit**: Celsius (standard, no conversion needed)
- ✅ **No licensing concerns**: Internal dataset
- ✅ **Static & versioned**: Downloaded once, stored permanently in git
- ✅ **City-level matching**: Direct mapping to attractions data

**Dataset Structure:**
```
location,JAN_MaxTemp,JAN_MinTemp,FEB_MaxTemp,FEB_MinTemp,...,DEC_MaxTemp,DEC_MinTemp
Abu Road,20,8,22,10,...,22,9
Agra,22,7,26,10,...,24,8
Delhi,22,7,26,10,...,24,8
...
(460+ locations)
```

## 2. Data Mapping Strategy

### City-to-Location Matching
The attractions dataset has 321 attractions across 213 unique cities. These cities are matched directly to the `location` field in `temperatureData.csv`:

**Matching Approach:**
1. **Exact Match** (Primary): `attraction.city_name` = `temperature.location` (case-insensitive)
2. **Partial Match** (Fallback): For unmatched cities, use district capital or nearest major city
3. **Regional Aggregation** (Last Resort): Use state-level climate data if city not found

**Current Coverage:**
- Direct matches: ~95% of attractions
- Estimated fallback needed: ~5% (small towns using nearest city data)

**Unmatched Locations Handling:**
For cities not in the temperature dataset (if any), the ETL script:
1. Logs the mismatch with city name
2. Uses nearest regional city's data as proxy
3. Flags record for manual review

## 3. ETL Integration Architecture

```
Raw Data Layer:
├─ raw_data/temperatureData.csv (460+ cities)
└─ final_dataset/attractions_flat_powerbi.csv (321 attractions)

Processing Layer:
├─ Script: scripts/11_integrate_climate.py
├─ Operations:
│  ├─ City name matching (case-insensitive)
│  ├─ Data validation & null handling
│  ├─ Derived metric calculation
│  └─ Season suitability scoring
└─ Output Formats:
   ├─ Enhanced CSV: final_dataset/attractions_with_climate.csv
   └─ SQLite: final_dataset/indian_itinerary.db

Application Layer:
├─ Streamlit: streamlit_app/app.py
├─ Components:
│  ├─ Monthly temperature range display
│  ├─ Temperature trend charts (line/bar)
│  ├─ Best time to visit recommendation
│  └─ Seasonal suitability matrix
└─ Data Caching: @st.cache_data for performance
```

## 4. Database Schema Updates

### New Columns in `attractions` Table
```sql
ALTER TABLE attractions ADD COLUMN JAN_MaxTemp REAL;
ALTER TABLE attractions ADD COLUMN JAN_MinTemp REAL;
-- ... through December ...
ALTER TABLE attractions ADD COLUMN DEC_MaxTemp REAL;
ALTER TABLE attractions ADD COLUMN DEC_MinTemp REAL;

-- Derived columns
ALTER TABLE attractions ADD COLUMN avg_max_temp_c REAL;      -- Annual avg of max temps
ALTER TABLE attractions ADD COLUMN avg_min_temp_c REAL;      -- Annual avg of min temps
ALTER TABLE attractions ADD COLUMN avg_temp_c REAL;          -- Overall average
ALTER TABLE attractions ADD COLUMN best_time_to_visit TEXT;  -- "Winter, Spring" or "Year-round"
ALTER TABLE attractions ADD COLUMN winter_suitability TEXT;  -- "High", "Medium", "Low"
ALTER TABLE attractions ADD COLUMN summer_suitability TEXT;
ALTER TABLE attractions ADD COLUMN monsoon_suitability TEXT;
ALTER TABLE attractions ADD COLUMN spring_suitability TEXT;  -- New: Spring/Autumn
ALTER TABLE attractions ADD COLUMN autumn_suitability TEXT;
```

### New Table: `monthly_temperatures`
Normalized structure for efficient queries:
```sql
CREATE TABLE monthly_temperatures (
    id INTEGER PRIMARY KEY,
    attraction_id TEXT UNIQUE,
    city_name TEXT,
    state_name TEXT,
    jan_max REAL, jan_min REAL,
    feb_max REAL, feb_min REAL,
    ... (all 12 months) ...
    avg_max_temp REAL,
    avg_min_temp REAL,
    avg_temp REAL,
    best_time_to_visit TEXT,
    winter_suitability TEXT,
    summer_suitability TEXT,
    monsoon_suitability TEXT
);
```

### New Table: `season_recommendations`
For recommendations engine:
```sql
CREATE TABLE season_recommendations (
    id INTEGER PRIMARY KEY,
    attraction_id TEXT UNIQUE,
    attraction_name TEXT,
    city_name TEXT,
    state_name TEXT,
    winter_suitable BOOLEAN,
    summer_suitable BOOLEAN,
    monsoon_suitable BOOLEAN,
    best_season TEXT,
    temperature_range TEXT,
    humidity_level TEXT
);
```

## 5. Data Quality & Validation

### Validation Rules
- ✅ All temperature values must be numeric
- ✅ Max temperature ≥ Min temperature for each month
- ✅ Monthly values within expected India climate range (-10°C to 50°C)
- ✅ Consistency: avg_max_temp = mean(all JAN_MaxTemp through DEC_MaxTemp)
- ✅ Missing values: Use regional average as fallback

### Quality Checks Post-Integration
1. **Record count**: 321 attractions should have climate data
2. **Data completeness**: <5% null values acceptable
3. **Range validation**: All temps within -5°C to 50°C
4. **Derived metric verification**: Spot-check 10 random attractions

## 6. Seasonal Definitions

```python
# Temperature-based season suitability
COMFORTABLE_RANGE = 15°C to 30°C  # Ideal for tourism

Winter (Nov-Feb):
  - Comfortable temps in northern plains
  - Lower humidity
  - Best for North/North-East India

Summer (Mar-May):
  - Hot in plains (28-42°C)
  - Suitable for hill stations, higher elevations
  - Best for North-West, Himalayan regions

Monsoon (Jun-Sep):
  - High humidity, rainfall
  - Green landscapes, festivals
  - Suitable for coastal, Western Ghats regions

Spring (Feb-Mar):
  - Moderate temps everywhere
  - Flowers bloom
  - Ideal across India

Autumn (Oct-Nov):
  - Clear skies, moderate temps
  - Post-monsoon freshness
  - Best pan-India season
```

## 7. No API Calls Guarantee

**Design ensures zero runtime API calls:**
- ✅ Temperature data pre-loaded from CSV
- ✅ SQLite stores all climate data
- ✅ Streamlit caches computed metrics
- ✅ No external weather API dependencies
- ✅ One-time ETL script runs offline
- ✅ App operates entirely on local database

**Deployment Benefits:**
- Works offline completely
- No rate limiting concerns
- No API key management
- Instant response times
- Zero cost at runtime

## 8. Next Steps

1. ✅ Run `scripts/11_integrate_climate.py` to merge data
2. ✅ Verify CSV output `attractions_with_climate.csv`
3. ✅ Check SQLite database updates
4. ✅ Update Streamlit app to display climate features
5. ✅ Add temperature trend charts
6. ✅ Test seasonal recommendations
