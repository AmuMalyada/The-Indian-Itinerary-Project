"""
Data validation test suite. Run with: pytest tests/
Assumes the pipeline has already been run (python scripts/run_pipeline.py)
so final_dataset/indian_itinerary.db exists.
"""
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "final_dataset" / "indian_itinerary.db"


@pytest.fixture(scope="module")
def conn():
    if not DB_PATH.exists():
        pytest.skip("Run scripts/run_pipeline.py first to generate the database.")
    c = sqlite3.connect(DB_PATH)
    yield c
    c.close()


def scalar(conn, query):
    return conn.execute(query).fetchone()[0]


def test_no_duplicate_attraction_ids(conn):
    total = scalar(conn, "SELECT COUNT(*) FROM attractions")
    distinct = scalar(conn, "SELECT COUNT(DISTINCT attraction_id) FROM attractions")
    assert total == distinct


def test_no_duplicate_state_ids(conn):
    total = scalar(conn, "SELECT COUNT(*) FROM states")
    distinct = scalar(conn, "SELECT COUNT(DISTINCT state_id) FROM states")
    assert total == distinct


def test_attraction_names_not_null(conn):
    n = scalar(conn, "SELECT COUNT(*) FROM attractions WHERE attraction_name IS NULL")
    assert n == 0


def test_google_rating_in_range(conn):
    n = scalar(conn, "SELECT COUNT(*) FROM attractions WHERE google_rating < 0 OR google_rating > 5")
    assert n == 0


def test_entrance_fee_non_negative(conn):
    n = scalar(conn, "SELECT COUNT(*) FROM attractions WHERE entrance_fee_inr < 0")
    assert n == 0


def test_attractions_city_referential_integrity(conn):
    n = scalar(conn, """
        SELECT COUNT(*) FROM attractions a
        LEFT JOIN cities c ON a.city_id = c.city_id
        WHERE a.city_id IS NOT NULL AND c.city_id IS NULL
    """)
    assert n == 0


def test_cities_state_referential_integrity(conn):
    n = scalar(conn, """
        SELECT COUNT(*) FROM cities c
        LEFT JOIN states s ON c.state_id = s.state_id
        WHERE s.state_id IS NULL
    """)
    assert n == 0


def test_destination_tags_referential_integrity(conn):
    n = scalar(conn, """
        SELECT COUNT(*) FROM destination_tags dt
        LEFT JOIN attractions a ON dt.attraction_id = a.attraction_id
        LEFT JOIN tags t ON dt.tag_id = t.tag_id
        WHERE a.attraction_id IS NULL OR t.tag_id IS NULL
    """)
    assert n == 0


def test_sim_reviews_referential_integrity(conn):
    n = scalar(conn, """
        SELECT COUNT(*) FROM sim_reviews r
        LEFT JOIN sim_destinations d ON r.sim_destination_id = d.sim_destination_id
        LEFT JOIN sim_users u ON r.sim_user_id = u.sim_user_id
        WHERE d.sim_destination_id IS NULL OR u.sim_user_id IS NULL
    """)
    assert n == 0


def test_sim_review_rating_in_range(conn):
    n = scalar(conn, "SELECT COUNT(*) FROM sim_reviews WHERE rating < 1 OR rating > 5")
    assert n == 0


def test_expected_row_counts_are_reasonable(conn):
    # Guards against a pipeline regression silently dropping most of the data.
    assert scalar(conn, "SELECT COUNT(*) FROM attractions") > 300
    assert scalar(conn, "SELECT COUNT(*) FROM states") > 25
    assert scalar(conn, "SELECT COUNT(*) FROM sim_destinations") == 1000
