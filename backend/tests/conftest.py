import os
import pytest
from pathlib import Path

# Explicitly configure test database for test suite isolation
TEST_DB_PATH = Path("./storage/test_screening.db").resolve()
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    from backend.app.db.session import init_db

    init_db()
    yield
    # Cleanup test db
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except Exception:
            pass
