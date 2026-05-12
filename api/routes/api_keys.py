"""API key management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.services.api_key_service import rotate_api_key
from api.services.csv_service import ApiError
from api.services.session_dependency import require_user_session

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


class RotateKeyRequest(BaseModel):
    user_id: str


@router.post("/rotate")
def rotate_key(payload: RotateKeyRequest, claims: dict = Depends(require_user_session)) -> dict:
    if str(claims.get("sub")) != str(payload.user_id):
        raise ApiError("AUTH_FORBIDDEN", "Cannot rotate another user's API key", status_code=403)
    key = rotate_api_key(payload.user_id)
    return {"meta": {"api_key_visible_once": True}, "data": key}

