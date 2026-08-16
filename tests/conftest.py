"""
Shared pytest bootstrap.

`api.config.Settings` and `api.database.engine` are both built at import time, so the
database has to be redirected *before* any `api.*` module is imported. Environment
variables outrank the `.env` file in pydantic-settings, so setting DATABASE_URL here
keeps the suite on a throwaway SQLite file even when a developer has a real Postgres
URL configured locally.
"""

import os
import shutil
import tempfile

_TEST_DB_DIR = tempfile.mkdtemp(prefix="bidforge-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TEST_DB_DIR, 'test.db')}"

import pytest  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    """Create all tables once per session and drop the scratch database afterwards."""
    from api.database import Base, engine
    from api.models import EstimateModel, LineItemModel, SpecChunkModel  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
