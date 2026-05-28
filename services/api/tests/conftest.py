import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models import Menu, Profile, Recipe, User  # noqa: F401  (register metadata)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE TABLE menus, profiles, recipes, users RESTART IDENTITY CASCADE")
        )


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
