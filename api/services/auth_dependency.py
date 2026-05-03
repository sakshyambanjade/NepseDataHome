"""FastAPI dependencies for credit-protected endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Header, Request, Response

from api.services.abuse_detection_service import evaluate_request
from api.services.api_key_service import validate_api_key
from api.services.credit_service import deduct_credits


def require_credits(cost: int) -> Callable:
    def dependency(
        request: Request,
        response: Response,
        x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict[str, Any]:
        api_key = validate_api_key(x_api_key, credits_required=cost)
        client_ip = request.client.host if request.client else "unknown"
        evaluate_request(api_key, client_ip, request.headers.get("User-Agent"))
        usage = deduct_credits(api_key, cost, request.url.path)
        response.headers["X-Credits-Remaining"] = str(usage["credits_remaining"])
        response.headers["X-Credits-Used"] = str(usage["credits_used"])
        if usage.get("expires_at"):
            response.headers["X-Plan-Expires-At"] = usage["expires_at"]
        return api_key

    return dependency
