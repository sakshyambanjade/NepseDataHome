"""Signup and device-session routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from api.services.api_key_service import get_default_api_key, get_user_by_email, signup_user
from api.services.device_service import register_device_session
from api.services.session_auth import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    name: str | None = None


class DeviceLoginRequest(BaseModel):
    user_id: str
    device_id: str
    device_name: str | None = None


class LoginRequest(BaseModel):
    email: str


@router.post("/signup")
def signup(payload: SignupRequest) -> dict:
    result = signup_user(email=payload.email, name=payload.name)
    user = result["user"]
    token = create_access_token(user_id=user["id"], email=user["email"])
    return {
        "meta": {"api_key_visible_once": True, "session_token": True},
        "data": {**result, "access_token": token, "token_type": "bearer"},
    }


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    user = get_user_by_email(payload.email)
    api_key = get_default_api_key(user["id"])
    safe_key = {
        key: value
        for key, value in api_key.items()
        if key not in {"key_hash", "api_key"}
    }
    token = create_access_token(user_id=user["id"], email=user["email"])
    return {
        "meta": {"session_token": True},
        "data": {
            "user": user,
            "api_key": safe_key,
            "access_token": token,
            "token_type": "bearer",
        },
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
