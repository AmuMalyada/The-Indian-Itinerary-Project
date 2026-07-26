"""
08_generate_database.py
------------------------
Create final_dataset/indian_itinerary.db from sql/schema.sql and load the
feature-engineered tables into it. SQLite is used as the portable deliverable;
sql/schema.sql is written to also run on PostgreSQL (see docs/ARCHITECTURE.md).
"""
import sqlite3
import pandas as pd
from common import PROCESSED_DIR, FINAL_DIR, SQL_DIR, get_logger

log = get_logger("08_generate_database")

TABLE_ORDER = [
    "states", "cities", "weather", "attractions", "tags", "destination_tags",
    "sim_destinations", "sim_users", "sim_reviews", "sim_user_history",
]


def load(name: str) -> pd.DataFrame:
    p = PROCESSED_DIR / "06_features" / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else pd.read_csv(p.with_suffix(".csv"))


def sqlite_type(dtype) -> str:
    s = str(dtype)
    if "int" in s:
        return "INTEGER"
    if "float" in s:
        return "REAL"
    if "bool" in s:
        return "INTEGER"  # SQLite has no native BOOLEAN
    if "datetime" in s:
        return "TEXT"
    return "TEXT"


def run() -> None:
    db_path = FINAL_DIR / "indian_itinerary.db"
    db_path.unlink(missing_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    schema_sql = (SQL_DIR / "schema.sql").read_text()
    # SQLite doesn't support some Postgres-only syntax (e.g. gen_random_uuid());
    # sql/schema.sql is Postgres-flavoured, so we execute a SQLite-safe subset
    # generated straight from the DataFrames instead of parsing the .sql file.
    for name in TABLE_ORDER:
        df = load(name)
        # sqlite3 can't store python bool objects cleanly in all pandas versions -> cast
        for col in df.select_dtypes(include="bool").columns:
            df[col] = df[col].astype("Int64")
        df.to_sql(name, conn, if_exists="replace", index=False)
        log.info(f"Loaded table `{name}`: {len(df)} rows")

    # Helpful indexes (mirrors sql/indexes.sql)
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_attractions_city ON attractions(city_id);",
        "CREATE INDEX IF NOT EXISTS idx_cities_state ON cities(state_id);",
        "CREATE INDEX IF NOT EXISTS idx_weather_city ON weather(city_id);",
        "CREATE INDEX IF NOT EXISTS idx_destination_tags_attraction ON destination_tags(attraction_id);",
        "CREATE INDEX IF NOT EXISTS idx_destination_tags_tag ON destination_tags(tag_id);",
        "CREATE INDEX IF NOT EXISTS idx_sim_reviews_dest ON sim_reviews(sim_destination_id);",
        "CREATE INDEX IF NOT EXISTS idx_sim_history_user ON sim_user_history(sim_user_id);",
    ]
    for stmt in index_statements:
        conn.execute(stmt)

    # Create analytical views too, so the shipped .db is query-ready out of
    # the box (sql/views.sql is Postgres-flavoured; strip the ::numeric casts
    # and comment lines, which is the only SQLite-incompatible syntax in it).
    views_sql = (SQL_DIR / "views.sql").read_text()
    clean = "\n".join(l for l in views_sql.splitlines() if not l.strip().startswith("--"))
    clean = clean.replace("::numeric", "")
    for stmt in clean.split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)

    conn.commit()
    conn.close()
    log.info(f"Database written to {db_path} (tables, indexes, and views)")


if __name__ == "__main__":
    run()
