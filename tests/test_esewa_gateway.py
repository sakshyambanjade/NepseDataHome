from uuid import uuid4

from api.services.api_key_service import signup_user
from api.services.billing_db import connect, iso_now, new_id
from api.services.credit_service import get_balance
from api.services.esewa_service import EsewaService, generate_esewa_signature


def test_esewa_initiate_builds_signed_payload():
    result = signup_user(email=f"esewa-init-{uuid4()}@example.com")
    service = EsewaService(merchant_code="EPAYTEST", secret_key="secret", init_url="https://example.com/form")
    result = service.initiate_payment(
        user_id=result["user"]["id"],
        plan_id="starter_50",
        customer_info={"name": "Ram", "email": "ram@example.com", "phone": "9800000000"},
    )

    form_data = result["form_data"]
    assert result["payment_url"] == "https://example.com/form"
    assert form_data["product_code"] == "EPAYTEST"
    assert form_data["signature"] == generate_esewa_signature("secret", f"50,{form_data['transaction_uuid']},EPAYTEST")


def test_esewa_verify_is_idempotent():
    result = signup_user(email=f"esewa-{uuid4()}@example.com")
    api_key_id = result["api_key"]["id"]
    service = EsewaService(merchant_code="EPAYTEST", secret_key="secret")

    order_id = new_id()
    transaction_uuid = f"txn-{uuid4()}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO payment_orders
                (id, user_id, gateway, amount, credits, status, purchase_order_id, gateway_payment_id, raw_response, created_at)
            VALUES (?, ?, 'esewa', 50, 5000, 'pending', ?, ?, '{}', ?)
            """,
            (order_id, result["user"]["id"], f"NDH-{uuid4()}", transaction_uuid, iso_now()),
        )

    lookup = {"transaction_uuid": transaction_uuid, "total_amount": 50, "status": "Completed", "ref_id": "ref-1"}
    first = service.verify_payment(transaction_uuid, lookup_response=lookup)
    second = service.verify_payment(transaction_uuid, lookup_response=lookup)

    assert first["status"] == "paid"
    assert second["idempotent"] is True
    assert get_balance(api_key_id)["credits_remaining"] == 5000