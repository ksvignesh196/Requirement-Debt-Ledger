"""
Pytest configuration and test database fixtures
"""
import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.database import init_db, get_connection, get_db
from app.main import app
from seed_data import seed_database

TEST_DB_PATH = Path(__file__).resolve().parent / "test_rdl.db"

@pytest.fixture(autouse=True)
def setup_test_db():
    """Creates a clean, seeded test database for each test."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    seed_database(str(TEST_DB_PATH))
    yield
    import gc
    gc.collect()
    try:
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()
    except PermissionError:
        pass

@pytest.fixture
def db_conn():
    """Returns a direct connection to the test database."""
    conn = get_connection(str(TEST_DB_PATH))
    yield conn
    conn.close()

@pytest.fixture
def client():
    """FastAPI TestClient with overridden DB dependency."""
    def override_get_db():
        conn = get_connection(str(TEST_DB_PATH))
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
