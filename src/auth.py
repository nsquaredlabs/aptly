import hashlib
import secrets
from typing import Annotated
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel

from src.config import settings
from src.supabase_client import supabase


class Customer(BaseModel):
    """Customer model returned from authentication."""

    id: str
    email: str
    company_name: str | None
    plan: str
    compliance_frameworks: list[str]
    retention_days: int
    pii_redaction_mode: str
    metadata: dict
    created_at: datetime


class APIKeyInfo(BaseModel):
    """API key information from database."""

    id: str
    customer_id: str
    key_prefix: str
    name: str | None
    rate_limit_per_hour: int
    is_revoked: bool
    created_at: datetime
    last_used_at: datetime | None


class AuthenticatedCustomer(BaseModel):
    """Combined customer and API key info for authenticated requests."""

    customer: Customer
    api_key: APIKeyInfo


def generate_api_key(environment: str = "live") -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        (full_key, key_hash, key_prefix)
    """
    prefix = f"apt_{environment}_"
    random_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:20]
    return full_key, key_hash, key_prefix


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage/lookup."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_admin_secret(
    x_admin_secret: Annotated[str | None, Header()] = None
) -> bool:
    """
    Verify the admin secret for admin-only endpoints.

    Raises:
        HTTPException: If admin secret is missing or invalid.
    """
    if not x_admin_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Missing X-Admin-Secret header",
                    "code": "INVALID_ADMIN_SECRET",
                }
            },
        )

    if not secrets.compare_digest(x_admin_secret, settings.aptly_admin_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid admin secret",
                    "code": "INVALID_ADMIN_SECRET",
                }
            },
        )

    return True


async def get_current_customer(
    authorization: Annotated[str | None, Header()] = None
) -> AuthenticatedCustomer:
    """
    Authenticate request using API key and return customer info.

    Raises:
        HTTPException: If API key is missing, invalid, or revoked.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Missing Authorization header",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    # Extract Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid Authorization header format. Use: Bearer <api_key>",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    api_key = authorization[7:]  # Remove "Bearer " prefix

    # Validate key format
    if not api_key.startswith(("apt_live_", "apt_test_")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid API key format",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    # Hash the key and look it up
    key_hash = hash_api_key(api_key)

    try:
        # Query API key with customer join
        key_result = (
            supabase.table("api_keys")
            .select("*, customers(*)")
            .eq("key_hash", key_hash)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid API key",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    if not key_result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid API key",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    key_data = key_result.data

    # Check if key is revoked
    if key_data.get("is_revoked"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "API key has been revoked",
                    "code": "INVALID_API_KEY",
                }
            },
        )

    # Update last_used_at (fire and forget, don't block on it)
    try:
        supabase.table("api_keys").update(
            {"last_used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", key_data["id"]).execute()
    except Exception:
        pass  # Don't fail auth if we can't update last_used_at

    # Build customer model
    customer_data = key_data["customers"]
    customer = Customer(
        id=customer_data["id"],
        email=customer_data["email"],
        company_name=customer_data.get("company_name"),
        plan=customer_data["plan"],
        compliance_frameworks=customer_data.get("compliance_frameworks", []),
        retention_days=customer_data.get("retention_days", 2555),
        pii_redaction_mode=customer_data.get("pii_redaction_mode", "mask"),
        metadata=customer_data.get("metadata", {}),
        created_at=customer_data["created_at"],
    )

    # Build API key info
    api_key_info = APIKeyInfo(
        id=key_data["id"],
        customer_id=key_data["customer_id"],
        key_prefix=key_data["key_prefix"],
        name=key_data.get("name"),
        rate_limit_per_hour=key_data.get("rate_limit_per_hour", 1000),
        is_revoked=key_data["is_revoked"],
        created_at=key_data["created_at"],
        last_used_at=key_data.get("last_used_at"),
    )

    return AuthenticatedCustomer(customer=customer, api_key=api_key_info)


# Dependency aliases for cleaner route definitions
AdminAuth = Annotated[bool, Depends(verify_admin_secret)]
CustomerAuth = Annotated[AuthenticatedCustomer, Depends(get_current_customer)]
