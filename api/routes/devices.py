"""Device management routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.services.device_service import list_devices, reset_devices

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.get("/{user_id}")
def user_devices(user_id: str) -> dict:
    devices = list_devices(user_id)
    return {"meta": {"count": len(devices)}, "data": devices}


@router.post("/{user_id}/reset")
def reset_user_devices(user_id: str) -> dict:
    return {"meta": {}, "data": reset_devices(user_id)}

