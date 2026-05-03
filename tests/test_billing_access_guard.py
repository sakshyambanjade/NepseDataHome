from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app
from api.services.api_key_service import signup_user
from api.services.credit_service import add_credits, get_balance
from api.services.khalti_service import KhaltiService


client = TestClient(app)


def test_signup_returns_raw_api_key_once():
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": f"signup-{uuid4()}@example.com", "name": "Ram"},
    )

    assert response.status_code == 200
    api_key = response.json()["data"]["api_key"]
    assert api_key["api_key"].startswith("ndh_live_")
    assert "key_hash" not in api_key


def test_credits_deduct_after_paid_request(paid_api_headers):
    response = client.get("/api/v1/prices/NABIL?limit=1", headers=paid_api_headers)

    assert response.status_code == 200
    assert response.headers["X-Credits-Used"] == "1"
    assert int(response.headers["X-Credits-Remaining"]) == 9999


def test_zero_credit_key_gets_402():
    result = signup_user(email=f"zero-{uuid4()}@example.com")
    response = client.get(
        "/api/v1/prices/NABIL?limit=1",
        headers={"X-API-Key": result["api_key"]["api_key"]},
    )

    assert response.status_code == 402
    assert response.json()["error"]["code"] == "INSUFFICIENT_CREDITS"


def test_device_limit_blocks_second_device():
    result = signup_user(email=f"device-{uuid4()}@example.com")
    user_id = result["user"]["id"]

    first = client.post(
        "/api/v1/auth/device-session",
        json={"user_id": user_id, "device_id": "ram-laptop", "device_name": "Ram Laptop"},
    )
    second = client.post(
        "/api/v1/auth/device-session",
        json={"user_id": user_id, "device_id": "shyam-laptop", "device_name": "Shyam Laptop"},
    )

    assert first.status_code == 200
    assert second.status_code == 403
    assert second.json()["error"]["code"] == "DEVICE_LIMIT_REACHED"


def test_khalti_verify_is_idempotent():
    result = signup_user(email=f"khalti-{uuid4()}@example.com")
    api_key_id = result["api_key"]["id"]
    service = KhaltiService(secret_key="test")
    # Create the pending order without hitting Khalti by inserting a realistic initiate result.
    from api.services.billing_db import connect, iso_now, new_id

    order_id = new_id()
    pidx = f"pidx-{uuid4()}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO payment_orders
                (id, user_id, gateway, amount, credits, status, purchase_order_id, gateway_payment_id, raw_response, created_at)
            VALUES (?, ?, 'khalti', 50, 5000, 'pending', ?, ?, '{}', ?)
            """,
            (order_id, result["user"]["id"], f"NDH-{uuid4()}", pidx, iso_now()),
        )

    lookup = {"pidx": pidx, "total_amount": 5000, "status": "Completed", "transaction_id": "txn-1"}
    first = service.verify_payment(pidx, lookup_response=lookup)
    second = service.verify_payment(pidx, lookup_response=lookup)

    assert first["status"] == "paid"
    assert second["idempotent"] is True
    assert get_balance(api_key_id)["credits_remaining"] == 5000
