"""
Shared test fixtures for NomosFlow backend.

Uses an in-memory SQLite database so tests never need a real PostgreSQL instance
or any environment variables.  The Gemini API is always mocked.
"""
import os
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String, JSON, types
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Patch environment before any app code is imported so Settings validation
# and genai.configure() never fail in CI / local runs without .env
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("GEMINI_API_KEY", "test-key-not-real")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
import app.services.gemini_quota as _quota_mod  # noqa: E402
from app.models.partner import Partner  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.payment import Payment  # noqa: E402
from app.models.dunning_action import DunningAction  # noqa: E402
from app.models.churn_score import ChurnScore  # noqa: E402


# ---------------------------------------------------------------------------
# SQLite-compatible UUID type: stores as VARCHAR(36), accepts uuid.UUID objects
# ---------------------------------------------------------------------------
class _UUIDStr(types.TypeDecorator):
    impl = types.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return value  # keep as string; SQLAlchemy models use as_uuid=True only for PG


# ---------------------------------------------------------------------------
# Override Postgres-only column types for SQLite compatibility.
# This patches the metadata in-memory and does NOT affect migrations or models.
# ---------------------------------------------------------------------------
for table in Base.metadata.tables.values():
    for col in table.columns:
        type_name = type(col.type).__name__
        if type_name == "JSONB":
            col.type = JSON()
        elif type_name == "UUID":
            col.type = _UUIDStr()

# ---------------------------------------------------------------------------
# SQLite test engine — schema rebuilt per test for full isolation
# ---------------------------------------------------------------------------
SQLITE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    # StaticPool forces all threads/connections to share one in-memory SQLite instance
    # so schema created in reset_db is visible to the TestClient's worker thread.
    poolclass=StaticPool,
    # Disable insertmanyvalues — it breaks with custom UUID TypeDecorators
    # because sentinel comparison fails when the decorator returns strings vs uuid.UUID.
    use_insertmanyvalues=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_quota():
    """Reset the in-process Gemini quota counter before every test."""
    from datetime import datetime, timezone
    _quota_mod._call_count = 0
    _quota_mod._window_start = datetime.now(timezone.utc)
    yield


@pytest.fixture(autouse=True)
def reset_db():
    """Drop and recreate all tables before each test for full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Return a test database session and close it after each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db):
    """FastAPI TestClient with the real DB dependency overridden to use SQLite."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Reusable model factories
# ---------------------------------------------------------------------------

def make_partner(db, **kwargs) -> Partner:
    defaults = dict(
        id=uuid.uuid4(),
        name="Test Partner",
        slug="test-partner",
        device_type="ev",
        brand_color="#3D6B2C",
    )
    partner = Partner(**{**defaults, **kwargs})
    db.add(partner)
    db.flush()
    return partner


def make_customer(db, partner_id, **kwargs) -> Customer:
    defaults = dict(
        id=uuid.uuid4(),
        partner_id=partner_id,
        name="Test Customer",
        email="test@example.com",
        device_type="ev",
        tariff_type="dynamic",
        monthly_kwh=350,
        annual_saving_eur=480,
        salary_day=15,
        contract_start=date.today() - timedelta(days=200),
        contract_status="active",
        city="Berlin",
    )
    customer = Customer(**{**defaults, **kwargs})
    db.add(customer)
    db.flush()
    return customer


def make_payment(db, customer_id, **kwargs) -> Payment:
    defaults = dict(
        id=uuid.uuid4(),
        customer_id=customer_id,
        amount_eur=89.50,
        period_month=date.today().replace(day=1),
        due_date=date.today(),
        status="failed",
        retry_count=0,
        max_retries=3,
    )
    payment = Payment(**{**defaults, **kwargs})
    db.add(payment)
    db.flush()
    return payment


def make_churn_score(db, customer_id, **kwargs) -> ChurnScore:
    defaults = dict(
        id=uuid.uuid4(),
        customer_id=customer_id,
        score=60,
        risk_level="high",
        reasoning="Test reasoning.",
        factors={"failed_payments_30d": 2},
        action_suggested="Contact customer.",
    )
    score = ChurnScore(**{**defaults, **kwargs})
    db.add(score)
    db.flush()
    return score
