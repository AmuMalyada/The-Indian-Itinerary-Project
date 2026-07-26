## Summary


## Related issue
Closes #

## Type of change
- [ ] Bug fix
- [ ] New feature (table/column/query/doc)
- [ ] Pipeline refactor (no data change)
- [ ] Documentation only

## Checklist
- [ ] `python scripts/run_pipeline.py` runs clean end to end
- [ ] `pytest tests/ -v` passes
- [ ] `ruff check scripts/ tests/` passes
- [ ] Updated `docs/DATA_DICTIONARY.md` if columns changed
- [ ] Added a `log_decision(...)` call if a new assumption/cleaning rule was introduced
- [ ] Did not add a foreign key between the real and synthetic domains beyond `state_id`
