import os

os.environ["DATABASE_URL"] = "sqlite:////tmp/agentic_returns_pytest.db"
os.environ.setdefault("OPENAI_API_KEY", "")

import pytest

from app.models.database import Base, engine
from scripts.seed_database import seed_database


@pytest.fixture(scope="session", autouse=True)
def synthetic_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database()
    yield
    Base.metadata.drop_all(bind=engine)