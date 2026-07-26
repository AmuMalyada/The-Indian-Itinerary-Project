"""
10_build_documentation.py
---------------------------
Turn the machine-recorded cleaning decisions (intermediate/cleaning_log.jsonl)
into docs/CLEANING_LOG.md, and write a final run summary.
"""
from common import DOCS_DIR, FINAL_DIR, get_logger, read_decision_log
import sqlite3

log = get_logger("10_build_documentation")


def run() -> None:
    entries = read_decision_log()
    lines = ["# Cleaning & Transformation Log\n",
             "_Auto-generated from every `log_decision(...)` call made during the pipeline run._\n"]
    stage = None
    for e in entries:
        if e["stage"] != stage:
            stage = e["stage"]
            lines.append(f"\n## {stage}\n")
        lines.append(f"- **{e['table']}** — {e['decision']}: {e['details']}")
    (DOCS_DIR / "CLEANING_LOG.md").write_text("\n".join(lines), encoding="utf-8")
    log.info("Wrote docs/CLEANING_LOG.md")

    db_path = FINAL_DIR / "indian_itinerary.db"
    summary = ["# Final Dataset Summary\n"]
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")]
        summary.append("| Table | Rows |")
        summary.append("|---|---|")
        for t in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            summary.append(f"| {t} | {n} |")
        conn.close()
    (DOCS_DIR / "FINAL_DATASET_SUMMARY.md").write_text("\n".join(summary), encoding="utf-8")
    log.info("Wrote docs/FINAL_DATASET_SUMMARY.md")


if __name__ == "__main__":
    run()
