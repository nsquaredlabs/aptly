"""Tests for admin endpoints - BOOTSTRAP FLOW."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from tests.conftest import TEST_ADMIN_SECRET, TEST_CUSTOMER


@pytest.mark.asyncio
async def test_admin_create_customer(client, mock_supabase, admin_headers):
    """Admin can create customer and receives API key."""
    mock_table = mock_supabase.table.return_value

    # First call: check if customer exists (should return empty)
    # Second call: create customer
    # Third call: create API key
    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Check existing - not found
            return MagicMock(data=[])
        elif call_count == 2:
            # Create customer
            return MagicMock(
                data=[
                    {
                        "id": "cus_new123",
                        "email": "new@example.com",
                        "company_name": "New Company",
                        "plan": "pro",
                        "compliance_frameworks": ["HIPAA"],
                        "retention_days": 2555,
                        "pii_redaction_mode": "mask",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            )
        else:
            # Create API key
            return MagicMock(
                data=[
                    {
                        "id": "key_new123",
                        "key_prefix": "apt_live_abc123",
                        "name": "Default API Key",
                        "rate_limit_per_hour": 1000,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            )

    mock_table.execute.side_effect = mock_execute

    response = await client.post(
        "/v1/admin/customers",
        headers=admin_headers,
        json={
            "email": "new@example.com",
            "company_name": "New Company",
            "plan": "pro",
            "compliance_frameworks": ["HIPAA"],
        },
    )

    assert response.status_code == 201
    data = response.json()

    # Verify customer data
    assert data["customer"]["email"] == "new@example.com"
    assert data["customer"]["company_name"] == "New Company"
    assert data["customer"]["plan"] == "pro"

    # Verify API key is returned
    assert "api_key" in data
    assert data["api_key"]["key"].startswith("apt_live_")
    assert data["api_key"]["name"] == "Default API Key"


@pytest.mark.asyncio
async def test_admin_create_customer_invalid_secret(client, mock_supabase):
    """Returns 401 for invalid admin secret."""
    response = await client.post(
        "/v1/admin/customers",
        headers={"X-Admin-Secret": "wrong-secret"},
        json={
            "email": "new@example.com",
            "company_name": "New Company",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_ADMIN_SECRET"


@pytest.mark.asyncio
async def test_admin_create_customer_missing_secret(client, mock_supabase):
    """Returns 401 for missing admin secret."""
    response = await client.post(
        "/v1/admin/customers",
        json={
            "email": "new@example.com",
            "company_name": "New Company",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_create_customer_duplicate_email(client, mock_supabase, admin_headers):
    """Returns 409 for duplicate email."""
    mock_table = mock_supabase.table.return_value

    # Return existing customer
    mock_table.execute.return_value = MagicMock(
        data=[{"id": "cus_existing", "email": "existing@example.com"}]
    )

    response = await client.post(
        "/v1/admin/customers",
        headers=admin_headers,
        json={
            "email": "existing@example.com",
            "company_name": "Duplicate Company",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["detail"]["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_admin_create_customer_invalid_email(client, mock_supabase, admin_headers):
    """Returns 422 for invalid email format."""
    response = await client.post(
        "/v1/admin/customers",
        headers=admin_headers,
        json={
            "email": "not-an-email",
            "company_name": "Company",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_list_customers(client, mock_supabase, admin_headers):
    """Admin can list all customers."""
    mock_table = mock_supabase.table.return_value

    mock_table.execute.return_value = MagicMock(
        data=[
            {
                "id": "cus_1",
                "email": "one@example.com",
                "company_name": "Company One",
                "plan": "free",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "cus_2",
                "email": "two@example.com",
                "company_name": "Company Two",
                "plan": "pro",
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ],
        count=2,
    )

    response = await client.get(
        "/v1/admin/customers",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["customers"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_admin_get_customer(client, mock_supabase, admin_headers):
    """Admin can get customer details."""
    mock_table = mock_supabase.table.return_value

    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Get customer
            return MagicMock(data=TEST_CUSTOMER)
        else:
            # Get API keys
            return MagicMock(
                data=[
                    {
                        "id": "key_1",
                        "key_prefix": "apt_live_abc",
                        "name": "Default Key",
                        "is_revoked": False,
                        "rate_limit_per_hour": 1000,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "last_used_at": None,
                    }
                ]
            )

    mock_table.execute.side_effect = mock_execute

    # Mock audit logger usage stats
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_usage_stats = MagicMock(
            return_value={"requests": 100, "tokens": 50000}
        )

        # Make it async
        import asyncio

        async def async_usage(*args, **kwargs):
            return {"requests": 100, "tokens": 50000}

        mock_audit.get_usage_stats = async_usage

        response = await client.get(
            f"/v1/admin/customers/{TEST_CUSTOMER['id']}",
            headers=admin_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["id"] == TEST_CUSTOMER["id"]
    assert "api_keys" in data
    assert "usage" in data


@pytest.mark.asyncio
async def test_admin_get_customer_not_found(client, mock_supabase, admin_headers):
    """Returns 404 for non-existent customer."""
    mock_table = mock_supabase.table.return_value
    mock_table.execute.side_effect = Exception("Not found")

    response = await client.get(
        "/v1/admin/customers/cus_nonexistent",
        headers=admin_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_create_api_key_for_customer(client, mock_supabase, admin_headers):
    """Admin can create API key for a customer."""
    mock_table = mock_supabase.table.return_value

    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Verify customer exists
            return MagicMock(data={"id": "cus_test123"})
        else:
            # Create API key
            return MagicMock(
                data=[
                    {
                        "id": "key_new456",
                        "key_prefix": "apt_live_xyz789",
                        "name": "Production Key",
                        "rate_limit_per_hour": 5000,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            )

    mock_table.execute.side_effect = mock_execute

    response = await client.post(
        "/v1/admin/customers/cus_test123/api-keys",
        headers=admin_headers,
        json={
            "name": "Production Key",
            "rate_limit_per_hour": 5000,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Production Key"
    assert data["key"].startswith("apt_live_")
    assert data["rate_limit_per_hour"] == 5000
