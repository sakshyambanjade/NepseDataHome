"""Signup and device-session routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.services.api_key_service import signup_user
from api.services.device_service import register_device_session

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    name: str | None = None


class DeviceLoginRequest(BaseModel):
    user_id: str
    device_id: str
    device_name: str | None = None


@router.post("/signup")
def signup(payload: SignupRequest) -> dict:
    result = signup_user(email=payload.email, name=payload.name)
    return {
        "meta": {"api_key_visible_once": True},
        "data": result,
    }


@router.post("/device-session")
def create_device_session(payload: DeviceLoginRequest, request: Request) -> dict:
    session = register_device_session(
        user_id=payload.user_id,
        device_id=payload.device_id,
        device_name=payload.device_name,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("User-Agent"),
    )
    return {"meta": {"session_token_visible_once": True}, "data": session}
