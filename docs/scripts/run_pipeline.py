"""
run_pipeline.py
----------------
Runs the full ETL pipeline end to end, stage by stage, stopping immediately
if a quality check fails. This is what `.github/workflows/ci.yml` calls.

Usage:
    python scripts/run_pipeline.py
"""
import importlib
import sys
import time

STAGES = [
    "01_ingest", "02_profile", "03_clean", "04_standardize", "05_merge",
    "06_feature_engineering", "07_quality_checks", "08_generate_database",
    "09_export", "11_integrate_climate", "10_build_documentation",
]


def main():
    start = time.time()
    for stage in STAGES:
        mod = importlib.import_module(stage)
        t0 = time.time()
        mod.run()
        print(f">>> {stage} finished in {time.time() - t0:.2f}s\n")
    print(f"Pipeline complete in {time.time() - start:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
