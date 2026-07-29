# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] — 2026-07-29
### Added
- Paper Trail n8n workflow set added under `workflows/` with 9 workflow JSON
    assets (master plus 8 child workflows).
- Deployment runbook and status tracking document added in `DEPLOYMENT.md`.

### Changed
- README updated with Paper Trail automation architecture and deployment-doc
    pointer.

### Fixed
- Resolved missing Postgres credential bindings across multiple Paper Trail
    workflows in n8n Cloud by standardizing on `Paper Trail PostgreSQL`.
- Added required environment variable `PAPER_TRAIL_NOTIFICATION_WEBHOOK_URL`
    for the notifications webhook node.

### Known Issues
- `Paper Trail - Master Pipeline` previously failed in node
    `Call Database Setup` with `Cannot convert undefined or null to object` due
    to stale Execute Workflow input mapping metadata; mapping was refreshed by
    reselecting the child workflow in n8n.
- Final rerun confirmation may be required in a stable n8n Cloud session if
    UI interruptions (toast overlays or plan redirect) recur.

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
