"""FastAPI dependencies for authenticated user-facing routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends
from fastapi import Header

from api.services.csv_service import ApiError
from api.services.session_auth import decode_access_token


def require_user_session(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(
            "AUTH_REQUIRED",
            "Authorization header with Bearer token is required",
            status_code=401,
        )
    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def require_user_match(target_user_id: str) -> Callable:
    def dependency(claims: dict[str, Any] = Depends(require_user_session)) -> dict[str, Any]:
        if str(claims.get("sub")) != str(target_user_id):
            raise ApiError(
                "AUTH_FORBIDDEN",
                "This session cannot access another user's data",
                status_code=403,
            )
        return claims

    return dependency
