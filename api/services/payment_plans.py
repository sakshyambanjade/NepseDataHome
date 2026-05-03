"""Credit packs available for one-time payment checkout."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentPlan:
    id: str
    amount: int
    credits: int
    valid_days: int
    name: str

    @property
    def amount_paisa(self) -> int:
        return self.amount * 100


PAYMENT_PLANS: dict[str, PaymentPlan] = {
    "starter_50": PaymentPlan(
        id="starter_50",
        amount=50,
        credits=5000,
        valid_days=30,
        name="Rs. 50 Starter Pack",
    ),
    "student_100": PaymentPlan(
        id="student_100",
        amount=100,
        credits=12000,
        valid_days=30,
        name="Rs. 100 Student Pack",
    ),
    "developer_500": PaymentPlan(
        id="developer_500",
        amount=500,
        credits=75000,
        valid_days=30,
        name="Rs. 500 Developer Pack",
    ),
}


def get_plan(plan_id: str) -> PaymentPlan:
    try:
        return PAYMENT_PLANS[plan_id]
    except KeyError as exc:
        from api.services.csv_service import ApiError

        raise ApiError(
            "PLAN_NOT_FOUND",
            f"No payment plan found for {plan_id}",
            {"plan_id": plan_id},
            status_code=404,
        ) from exc

