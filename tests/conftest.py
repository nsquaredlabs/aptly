import os
import pytest

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import fakeredis.aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set environment variables before importing anything else
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["APTLY_API_SECRET"] = "test-secret-12345"
os.environ["ENVIRONMENT"] = "test"

from src.models import Base, AuditLog

# Test data
TEST_API_SECRET = "test-secret-12345"


@pytest.fixture
def fake_redis_server():
    """Create a shared fake Redis server for tests."""
    return fakeredis.FakeServer()


@pytest_asyncio.fixture
async def fake_redis(fake_redis_server):
    """Provide a fake Redis instance for testing."""
    redis_client = fakeredis.aioredis.FakeRedis(
        server=fake_redis_server,
        encoding="utf-8",
        decode_responses=True,
    )
    yield redis_client
    await redis_client.aclose()


@pytest_asyncio.fixture
async def db_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Provide a test database session."""
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session, fake_redis):
    """Test client with SQLAlchemy test session and fake Redis."""
    from src.main import app
    from src.db import get_db
    from src.rate_limiter import rate_limiter

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Replace the rate limiter's redis with our fake
    original_redis = rate_limiter._redis
    original_disabled = rate_limiter._disabled
    rate_limiter._redis = fake_redis
    rate_limiter._disabled = False

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Restore
    app.dependency_overrides.clear()
    rate_limiter._redis = original_redis
    rate_limiter._disabled = original_disabled


@pytest_asyncio.fixture
async def authenticated_client(client):
    """Client with valid API secret authentication set up."""
    client.headers["Authorization"] = f"Bearer {TEST_API_SECRET}"
    yield client
