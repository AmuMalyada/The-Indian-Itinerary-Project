# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] — 2026-07-24
### Added
- Initial public release.
- 10-stage ETL pipeline (`scripts/01_ingest.py` → `10_build_documentation.py`).
- Normalized schema: `states`, `cities`, `attractions`, `weather`, `tags`,
  `destination_tags`, plus synthetic-domain tables `sim_destinations`,
  `sim_users`, `sim_reviews`, `sim_user_history`.
- 30+ engineered analytics features on `attractions`.
- SQL layer: schema, indexes, constraints, views, analytics + sample queries.
- 11-check automated data quality gate + pytest suite.
- Power BI-ready flattened export.
- Full documentation set (data dictionary, architecture/ER diagrams, roadmap,
  auto-generated cleaning log).
- GitHub Actions CI, issue/PR templates.
