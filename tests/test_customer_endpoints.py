"""Tests for customer-facing endpoints (/v1/me, /v1/api-keys)."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from tests.conftest import (
    TEST_CUSTOMER,
    TEST_API_KEY,
    TEST_API_KEY_DATA,
    setup_auth_mocks,
)


@pytest.mark.asyncio
async def test_get_profile(client, mock_supabase):
    """Can get customer profile with usage stats."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.get_usage_stats = AsyncMock(
            return_value={"requests": 100, "tokens": 50000}
        )

        with patch("src.main.rate_limiter") as mock_rate:
            mock_rate.get_current_usage = AsyncMock(return_value=42)

            response = await client.get(
                "/v1/me",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == TEST_CUSTOMER["id"]
    assert data["email"] == TEST_CUSTOMER["email"]
    assert "usage" in data
    assert data["usage"]["requests_this_month"] == 100
    assert data["usage"]["tokens_this_month"] == 50000
    assert data["usage"]["requests_this_hour"] == 42


@pytest.mark.asyncio
async def test_update_profile_pii_mode(client, mock_supabase):
    """Can update PII redaction mode."""
    mock_table = mock_supabase.table.return_value
    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth calls
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Update call returns updated customer
            return MagicMock(data=[{**TEST_CUSTOMER, "pii_redaction_mode": "hash"}])

    mock_table.execute.side_effect = mock_execute

    response = await client.patch(
        "/v1/me",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"pii_redaction_mode": "hash"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["pii_redaction_mode"] == "hash"


@pytest.mark.asyncio
async def test_update_profile_compliance_frameworks(client, mock_supabase):
    """Can update compliance frameworks."""
    mock_table = mock_supabase.table.return_value
    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth calls
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Update call returns updated customer
            return MagicMock(data=[{**TEST_CUSTOMER, "compliance_frameworks": ["HIPAA", "GDPR"]}])

    mock_table.execute.side_effect = mock_execute

    response = await client.patch(
        "/v1/me",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"compliance_frameworks": ["HIPAA", "GDPR"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert "GDPR" in data["compliance_frameworks"]


@pytest.mark.asyncio
async def test_update_profile_invalid_pii_mode(client, mock_supabase):
    """Returns 400 for invalid PII redaction mode."""
    setup_auth_mocks(mock_supabase)

    response = await client.patch(
        "/v1/me",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"pii_redaction_mode": "invalid_mode"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_update_profile_no_fields(client, mock_supabase):
    """Returns 400 when no valid fields provided."""
    setup_auth_mocks(mock_supabase)

    response = await client.patch(
        "/v1/me",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_api_keys(client, mock_supabase):
    """Can list customer's API keys."""
    mock_table = mock_supabase.table.return_value
    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth calls
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # List API keys call
            return MagicMock(
                data=[
                    {
                        "id": "key_1",
                        "key_prefix": "apt_live_abc",
                        "name": "Key 1",
                        "rate_limit_per_hour": 1000,
                        "is_revoked": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "last_used_at": None,
                    },
                    {
                        "id": "key_2",
                        "key_prefix": "apt_live_xyz",
                        "name": "Key 2",
                        "rate_limit_per_hour": 500,
                        "is_revoked": False,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "last_used_at": datetime.now(timezone.utc).isoformat(),
                    },
                ]
            )

    mock_table.execute.side_effect = mock_execute

    response = await client.get(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["api_keys"]) == 2


@pytest.mark.asyncio
async def test_create_api_key(client, mock_supabase):
    """Can create a new API key."""
    mock_table = mock_supabase.table.return_value
    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth calls
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Create API key call
            return MagicMock(
                data=[
                    {
                        "id": "key_new123",
                        "key_prefix": "apt_live_new",
                        "name": "New Key",
                        "rate_limit_per_hour": 1000,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            )

    mock_table.execute.side_effect = mock_execute

    response = await client.post(
        "/v1/api-keys",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={"name": "New Key"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Key"
    assert data["key"].startswith("apt_live_")


@pytest.mark.asyncio
async def test_revoke_api_key(client, mock_supabase):
    """Can revoke an API key."""
    setup_auth_mocks(mock_supabase)

    mock_table = mock_supabase.table.return_value

    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth lookups return the API key data
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Key lookup for revocation
            return MagicMock(data={"id": "key_other123", "customer_id": TEST_CUSTOMER["id"]})

    mock_table.execute.side_effect = mock_execute

    response = await client.delete(
        "/v1/api-keys/key_other123",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_revoke_api_key_not_found(client, mock_supabase):
    """Returns 404 when API key not found."""
    setup_auth_mocks(mock_supabase)

    mock_table = mock_supabase.table.return_value

    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth lookups
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Key not found
            raise Exception("Not found")

    mock_table.execute.side_effect = mock_execute

    response = await client.delete(
        "/v1/api-keys/key_nonexistent",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_revoke_current_api_key(client, mock_supabase):
    """Cannot revoke the API key currently in use."""
    setup_auth_mocks(mock_supabase)

    mock_table = mock_supabase.table.return_value

    call_count = 0

    def mock_execute():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # Auth lookups
            return MagicMock(data={**TEST_API_KEY_DATA, "customers": TEST_CUSTOMER})
        else:
            # Trying to revoke the current key
            return MagicMock(data={"id": TEST_API_KEY_DATA["id"], "customer_id": TEST_CUSTOMER["id"]})

    mock_table.execute.side_effect = mock_execute

    response = await client.delete(
        f"/v1/api-keys/{TEST_API_KEY_DATA['id']}",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
    )

    assert response.status_code == 409
    data = response.json()
    assert "currently using" in data["detail"]["error"]["message"].lower()
