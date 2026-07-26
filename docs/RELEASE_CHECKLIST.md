# Release Checklist

- [ ] `python scripts/run_pipeline.py` runs clean, 11/11 quality checks pass
- [ ] `pytest tests/ -v` all green
- [ ] `ruff check scripts/ tests/` clean
- [ ] `docs/DATA_DICTIONARY.md` matches current schema
- [ ] `docs/CLEANING_LOG.md` regenerated (stage 10 of the pipeline)
- [ ] `CHANGELOG.md` updated with the new version entry
- [ ] `CITATION.cff` version/date bumped
- [ ] README badges reflect current state (row counts, check count)
- [ ] `final_dataset/` files committed and match the latest pipeline run
- [ ] Tag release in git (`git tag vX.Y.Z && git push --tags`)
- [ ] If publishing to Kaggle: re-export `final_dataset/*.csv`, update the
      Kaggle dataset description/metadata to match `README.md`
