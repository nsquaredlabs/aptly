import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import fakeredis.aioredis

# Set environment variables before importing anything else
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["APTLY_ADMIN_SECRET"] = "test-admin-secret-12345"
os.environ["ENVIRONMENT"] = "test"

# Test data
TEST_CUSTOMER = {
    "id": "cus_test123",
    "email": "test@example.com",
    "company_name": "Test Company",
    "plan": "pro",
    "compliance_frameworks": ["HIPAA"],
    "retention_days": 2555,
    "pii_redaction_mode": "mask",
    "metadata": {},
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
}

TEST_API_KEY = "apt_test_abc123def456ghi789jkl012mno345"
TEST_API_KEY_HASH = "a" * 64  # Simplified hash for testing

TEST_API_KEY_DATA = {
    "id": "key_test123",
    "customer_id": TEST_CUSTOMER["id"],
    "key_hash": TEST_API_KEY_HASH,
    "key_prefix": "apt_test_abc123",
    "name": "Test API Key",
    "rate_limit_per_hour": 1000,
    "is_revoked": False,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "last_used_at": None,
}

TEST_ADMIN_SECRET = "test-admin-secret-12345"


def create_mock_supabase():
    """Create a mock Supabase client."""
    mock = MagicMock()
    mock_table = MagicMock()
    mock.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.neq.return_value = mock_table
    mock_table.gte.return_value = mock_table
    mock_table.lte.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.range.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.single.return_value = mock_table
    return mock


def setup_auth_mocks(mock_supabase, include_customer=True):
    """Helper to set up authentication mocks."""
    mock_table = mock_supabase.table.return_value

    if include_customer:
        # Mock API key lookup with nested customer
        api_key_with_customer = {
            **TEST_API_KEY_DATA,
            "customers": TEST_CUSTOMER,
        }
        mock_result = MagicMock()
        mock_result.data = api_key_with_customer
        mock_table.execute.return_value = mock_result
    else:
        # Mock not found
        mock_table.execute.side_effect = Exception("Not found")


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    return create_mock_supabase()


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
async def client(mock_supabase, fake_redis):
    """Test client with mocked dependencies."""
    # Import after environment is set
    import src.supabase_client
    import src.auth
    import src.main
    import src.compliance.audit_logger
    import src.analytics
    from src.main import app
    from src.rate_limiter import rate_limiter

    # Replace supabase in all modules that import it
    original_supabase_client = src.supabase_client.supabase
    original_auth = src.auth.supabase
    original_main = src.main.supabase
    original_audit = src.compliance.audit_logger.supabase
    original_analytics = src.analytics.supabase

    src.supabase_client.supabase = mock_supabase
    src.auth.supabase = mock_supabase
    src.main.supabase = mock_supabase
    src.compliance.audit_logger.supabase = mock_supabase
    src.analytics.supabase = mock_supabase

    # Replace the rate limiter's redis with our fake
    original_redis = rate_limiter._redis
    rate_limiter._redis = fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    # Restore
    src.supabase_client.supabase = original_supabase_client
    src.auth.supabase = original_auth
    src.main.supabase = original_main
    src.compliance.audit_logger.supabase = original_audit
    src.analytics.supabase = original_analytics
    rate_limiter._redis = original_redis


@pytest_asyncio.fixture
async def authenticated_client(client, mock_supabase):
    """Client with valid API key authentication set up."""
    setup_auth_mocks(mock_supabase, include_customer=True)
    client.headers["Authorization"] = f"Bearer {TEST_API_KEY}"
    yield client


@pytest.fixture
def test_customer():
    """Return test customer data."""
    return TEST_CUSTOMER.copy()


@pytest.fixture
def test_api_key():
    """Return test API key."""
    return TEST_API_KEY


@pytest.fixture
def test_api_key_data():
    """Return test API key data."""
    return TEST_API_KEY_DATA.copy()


@pytest.fixture
def admin_headers():
    """Return admin authentication headers."""
    return {"X-Admin-Secret": TEST_ADMIN_SECRET}
