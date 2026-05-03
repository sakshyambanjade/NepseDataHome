"""API key management routes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from api.services.api_key_service import rotate_api_key

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


class RotateKeyRequest(BaseModel):
    user_id: str


@router.post("/rotate")
def rotate_key(payload: RotateKeyRequest) -> dict:
    key = rotate_api_key(payload.user_id)
    return {"meta": {"api_key_visible_once": True}, "data": key}

