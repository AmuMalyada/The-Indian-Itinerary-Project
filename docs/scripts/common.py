"""
common.py
---------
Shared helpers used across the pipeline (01_ingest.py ... 10_build_documentation.py).

Keeping these in one place means every stage cleans/standardizes/logs the same
way, which is the whole point of a *pipeline* rather than a pile of notebooks.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (single source of truth so scripts never hardcode relative paths)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw_data"
INTERMEDIATE_DIR = ROOT / "intermediate"
PROCESSED_DIR = ROOT / "processed"
FINAL_DIR = ROOT / "final_dataset"
DOCS_DIR = ROOT / "docs"
SQL_DIR = ROOT / "sql"

for d in (INTERMEDIATE_DIR, PROCESSED_DIR, FINAL_DIR, DOCS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ---------------------------------------------------------------------------
# Cleaning-decision log — every cleaning script appends here so the whole
# transformation history is reproducible and auditable (docs/CLEANING_LOG.md
# is generated from this at the end of the pipeline).
# ---------------------------------------------------------------------------
_LOG_PATH = INTERMEDIATE_DIR / "cleaning_log.jsonl"


def log_decision(stage: str, table: str, decision: str, details: str = "") -> None:
    entry = {"stage": stage, "table": table, "decision": decision, "details": details}
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_decision_log() -> list[dict]:
    if not _LOG_PATH.exists():
        return []
    with open(_LOG_PATH, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def reset_decision_log() -> None:
    _LOG_PATH.write_text("", encoding="utf-8")


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
def clean_text(value) -> str | None:
    """Trim whitespace, collapse internal whitespace, fix encoding artefacts."""
    if pd.isna(value):
        return None
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def title_case(value) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    # Keep common Indian-name particles lowercase where they'd normally be
    # (basic Title Case is fine for state/city names in this dataset).
    return text.title()


STATE_NAME_FIXES = {
    "maharastra": "Maharashtra",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "delhi": "Delhi",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "jammu and kashmir": "Jammu and Kashmir",
}


def standardize_state_name(value) -> str | None:
    """Fix known misspellings / legacy names to current official state names."""
    text = clean_text(value)
    if text is None:
        return None
    key = text.lower().strip()
    if key in STATE_NAME_FIXES:
        return STATE_NAME_FIXES[key]
    return text.title()


def parse_establishment_year(value):
    """'Unknown' / blanks -> None, 4-digit strings -> int, out-of-range -> None."""
    text = clean_text(value)
    if text is None or text.lower() == "unknown":
        return None
    match = re.search(r"(\d{3,4})", text)
    if not match:
        return None
    year = int(match.group(1))
    if year < 1 or year > 2026:
        return None
    return year


def yes_no_to_bool(value):
    text = clean_text(value)
    if text is None:
        return None
    return text.strip().lower() in {"yes", "y", "true", "1"}


def slugify(value: str) -> str:
    text = clean_text(value) or ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


# ---------------------------------------------------------------------------
# Great-circle distance placeholder removed: this dataset has no lat/long,
# so we do NOT fabricate coordinates. (See docs/DATASET_UNDERSTANDING.md.)
# ---------------------------------------------------------------------------

def save_parquet_and_csv(df: pd.DataFrame, directory: Path, name: str) -> None:
    """Persist a stage output as both CSV (human-readable/diffable) and
    parquet (fast, typed) — standard practice for analytics-engineering
    pipelines."""
    directory.mkdir(parents=True, exist_ok=True)
    df.to_csv(directory / f"{name}.csv", index=False)
    try:
        df.to_parquet(directory / f"{name}.parquet", index=False)
    except Exception:
        # parquet engine not installed in some environments; CSV is enough
        pass


def get_sqlite_connection(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = db_path or (FINAL_DIR / "indian_itinerary.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
