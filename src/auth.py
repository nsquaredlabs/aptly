import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Header, status

from src.config import settings


async def verify_api_secret(
    authorization: Annotated[str | None, Header()] = None
) -> bool:
    """
    Verify the API secret for all authenticated endpoints.

    Expects: Authorization: Bearer <APTLY_API_SECRET>

    Raises:
        HTTPException: If secret is missing or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Missing Authorization header",
                    "code": "UNAUTHORIZED",
                }
            },
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid Authorization header format. Use: Bearer <api_secret>",
                    "code": "UNAUTHORIZED",
                }
            },
        )

    token = authorization[7:]

    if not secrets.compare_digest(token, settings.aptly_api_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid API secret",
                    "code": "UNAUTHORIZED",
                }
            },
        )

    return True


# Dependency alias for cleaner route definitions
ApiAuth = Annotated[bool, Depends(verify_api_secret)]
