# Contributing

Thanks for considering a contribution.

## Setup
```bash
pip install -r requirements.txt
python scripts/run_pipeline.py   # generates final_dataset/ locally
pytest tests/ -v
```

## Ground rules
- Never hardcode a value the source data doesn't support — if you must
  assume something (e.g. a default cost), document it with `log_decision(...)`
  in `scripts/common.py` so it shows up in `docs/CLEANING_LOG.md`.
- Any new cleaning/standardization step goes in the matching numbered stage
  (`03_clean.py` for cleaning, `04_standardize.py` for naming/casing/units).
- Add or update a `tests/test_data_quality.py` check for any new invariant
  you're relying on.
- Run `ruff check .` before opening a PR (see `.github/workflows/ci.yml` for
  the exact command CI runs).
- Keep the "real" (`attractions`, `cities`, `states`, `weather`) and
  "synthetic" (`sim_*`) domains separate — do not add foreign keys between
  them beyond `state_id`, which is the only verified real link.

## Pull requests
Use the PR template. Link an issue if one exists. CI must pass (pipeline run
+ pytest + ruff) before review.
