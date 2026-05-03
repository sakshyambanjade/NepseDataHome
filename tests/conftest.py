from uuid import uuid4

import pytest

from api.services.api_key_service import signup_user
from api.services.credit_service import add_credits


@pytest.fixture
def paid_api_headers():
    result = signup_user(email=f"test-{uuid4()}@example.com", name="Test User")
    api_key = result["api_key"]
    add_credits(api_key["id"], credits=10000, valid_days=30, plan_id="starter_50")
    return {"X-API-Key": api_key["api_key"]}

