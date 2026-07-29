# 🇮🇳 The Indian Itinerary Project

### An Open Travel Intelligence Dataset for Analytics, AI & Itinerary Planning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](requirements.txt)
[![Pipeline](https://img.shields.io/badge/pipeline-10--stage%20ETL-brightgreen)](scripts/run_pipeline.py)
[![Data Quality](https://img.shields.io/badge/quality%20checks-11%2F11%20passing-success)](tests/test_data_quality.py)
[![Tables](https://img.shields.io/badge/normalized%20tables-10-informational)](docs/DATA_DICTIONARY.md)

---

## What this is

A production-style data engineering project that takes three raw, messy
Kaggle datasets about Indian tourism and turns them into a documented,
normalized, quality-checked relational database — ready for SQL practice,
Power BI/Tableau dashboards, and ML/RAG prototyping.

It is **not** a naive `pd.concat()` of three CSVs. The three sources
describe genuinely different things at different granularities, and the
project says so honestly instead of faking a merge — see
[`docs/DATASET_UNDERSTANDING.md`](docs/DATASET_UNDERSTANDING.md).

## Architecture

```
raw_data/  →  01_ingest → 02_profile → 03_clean → 04_standardize
           →  05_merge → 06_feature_engineering → 07_quality_checks
           →  08_generate_database → 09_export → 10_build_documentation
           →  final_dataset/ (SQLite DB + CSVs + Power BI export)
```

Full diagrams (pipeline flow, ER diagram, future architecture) in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Folder structure

```
The-Indian-Itinerary-Project/
├── raw_data/            original, untouched Kaggle CSVs
├── intermediate/        ingested + profiled + merged staging outputs
├── processed/           cleaned / standardized / feature-engineered stages
├── final_dataset/        indian_itinerary.db + final CSVs + Power BI export
├── notebooks/            EDA notebook
├── scripts/              10 modular pipeline stages + run_pipeline.py
├── sql/                  schema, indexes, constraints, views, queries
├── docs/                 data dictionary, architecture, roadmap, logs
├── powerbi/               Power BI setup guide + DAX measures
├── tests/                 pytest data-quality suite
├── dashboards/            dashboard-page recommendations
├── .github/                CI workflow, issue/PR templates
├── requirements.txt
└── README.md (you are here)
```

## Data sources

| Domain | Source | Rows (raw → clean) | Nature |
|---|---|---|---|
| Attractions | Kaggle: *Top Indian Places to Visit* | 325 → 323 | Real |
| Climate | Kaggle: India temperature dataset | 264 → 264 | Real |
| Destinations / Reviews / Users / History | Kaggle: *Expanded* travel dataset | ~1,000 each | **Synthetic** (see note below) |

> **Honesty note:** the "Expanded" destination/review/user/history files are
> generated practice data (fake `@example.com` emails, only 5 states, random
> popularity scores). They're genuinely useful for practicing recommendation-
> system and NLP workflows, but they are kept in their own tables rather than
> pretended to be the same 1,000 real places as the attractions table. Full
> writeup: [`docs/DATASET_UNDERSTANDING.md`](docs/DATASET_UNDERSTANDING.md).

## Final dataset

| Table | Rows |
|---|---|
| attractions | 323 |
| cities | 213 |
| states | 32 |
| weather | 213 |
| tags | 23 |
| destination_tags | 722 |
| sim_destinations | 1,000 |
| sim_users | 999 |
| sim_reviews | 999 |
| sim_user_history | 999 |

44 columns on `attractions` alone, including 30+ engineered analytics features
(budget category, adventure/nature/heritage scores, popularity tier,
accessibility score, seasonal suitability, and more — full list in
[`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md)).

## Quick start

```bash
git clone <this-repo>
cd The-Indian-Itinerary-Project
pip install -r requirements.txt

# Run the full pipeline (raw CSVs -> cleaned, normalized, tested database)
python scripts/run_pipeline.py

# Query it
sqlite3 final_dataset/indian_itinerary.db
sqlite> SELECT * FROM vw_state_summary ORDER BY attraction_count DESC LIMIT 5;

# Run the test suite
pytest tests/ -v

# Explore interactively
jupyter notebook notebooks/eda.ipynb
```

## SQL

`sql/schema.sql` (Postgres-flavoured DDL with UUID PKs, FKs, and CHECK
constraints) · `sql/indexes.sql` · `sql/constraints.sql` · `sql/views.sql`
(4 reusable views) · `sql/analytics_queries.sql` (window functions, CTEs,
tag co-occurrence, seasonal filtering) · `sql/sample_queries.sql`
(beginner-friendly).

## Power BI / Tableau

`final_dataset/attractions_flat_powerbi.csv` is a pre-joined, denormalized
export (attraction + city + state + weather + tags in one row) — the shape
BI tools want. The repository now includes a professional Power BI implementation
package under [`powerbi/`](powerbi/) that is designed for recreation inside
Microsoft Power BI Desktop.

### Power BI assets added

- [`powerbi/POWERBI_GUIDE.md`](powerbi/POWERBI_GUIDE.md) — implementation guide and setup instructions
- [`powerbi/assets/theme/indian_itinerary_theme.json`](powerbi/assets/theme/indian_itinerary_theme.json) — executive-grade theme for a polished dark report experience
- [`powerbi/assets/docs/semantic_model.md`](powerbi/assets/docs/semantic_model.md) — semantic model and relationship blueprint
- [`powerbi/assets/docs/dax_measures.md`](powerbi/assets/docs/dax_measures.md) — reusable DAX measure library
- [`powerbi/assets/docs/visual_specifications.md`](powerbi/assets/docs/visual_specifications.md) — page-by-page visual strategy
- [`powerbi/assets/docs/report_blueprint.md`](powerbi/assets/docs/report_blueprint.md) — navigation, storytelling, and interaction blueprint

### Dashboard experience planned

The Power BI report is structured around seven enterprise-style pages:

1. Executive Overview
2. Destination Explorer
3. Budget Intelligence
4. Season & Climate
5. Tourism Insights
6. Recommendation Explorer
7. Data Quality Dashboard

### Power BI setup

1. Open Microsoft Power BI Desktop.
2. Import the flattened export from [`final_dataset/attractions_flat_powerbi.csv`](final_dataset/attractions_flat_powerbi.csv).
3. Apply the theme JSON from [`powerbi/assets/theme/indian_itinerary_theme.json`](powerbi/assets/theme/indian_itinerary_theme.json).
4. Build the semantic model following [`powerbi/assets/docs/semantic_model.md`](powerbi/assets/docs/semantic_model.md).
5. Recreate the report layout and DAX measures from the documentation in [`powerbi/assets/docs/`](powerbi/assets/docs/).

> A .pbix file is not included in this repository snapshot, but the project is now structured so it can be recreated professionally in Power BI Desktop without guesswork.

## Data quality

Every pipeline run executes 11 automated checks (uniqueness, null
constraints, value ranges, referential integrity) before the database is
even written — see [`scripts/07_quality_checks.py`](scripts/07_quality_checks.py)
and the mirrored [`tests/test_data_quality.py`](tests/test_data_quality.py).
CI runs the full pipeline + test suite on every push
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## Documentation

- [Dataset Understanding](docs/DATASET_UNDERSTANDING.md) — Phase 1 deliverable, generated from actual profiling
- [Data Dictionary](docs/DATA_DICTIONARY.md)
- [Architecture](docs/ARCHITECTURE.md) — pipeline diagram, ER diagram, future-state diagram
- [Cleaning Log](docs/CLEANING_LOG.md) — every cleaning decision, auto-generated from the pipeline run
- [Roadmap](docs/ROADMAP.md)
- [Contributing](CONTRIBUTING.md) · [Code of Conduct](CODE_OF_CONDUCT.md) · [Changelog](CHANGELOG.md) · [Citation](CITATION.cff)

## Roadmap highlights

Architected (UUID keys, normalized schema, Postgres-compatible DDL) to later
support a FastAPI REST layer, a vector-DB/RAG travel chatbot, and mobile
clients — without a schema redesign. Full roadmap:
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Paper Trail Automation (n8n)

This repository also contains a modular n8n automation called Paper Trail
for research-paper ingestion and contradiction analysis workflows. The current
workflow assets are in [`workflows/`](workflows/) and are designed around a
single orchestrator with child workflow isolation.

### Workflow architecture

- Master orchestrator: `Paper Trail - Master Pipeline`
- Child workflows:
    - `Paper Trail - Database Setup`
    - `Paper Trail - Ingestion`
    - `Paper Trail - Extraction`
    - `Paper Trail - Validation`
    - `Paper Trail - Storage`
    - `Paper Trail - Contradiction Detection`
    - `Paper Trail - Consensus Engine`
    - `Paper Trail - Notifications`

For current deployment status, environment requirements, credential setup,
known issues, and release checklist, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

## License

[MIT](LICENSE) — see also [`CITATION.cff`](CITATION.cff) if you use this dataset in research or a derivative project.

## Acknowledgements

Built on three public Kaggle datasets (Top Indian Places to Visit; India
temperature/climate data; Expanded Indian Travel Destinations). See
`docs/DATASET_UNDERSTANDING.md` for full source attribution.
