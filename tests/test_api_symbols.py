from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_symbols_returns_list():
    response = client.get("/api/v1/symbols")

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["count"] >= 100
    assert any(row["symbol"] == "NABIL" for row in body["data"])


def test_symbol_profile_returns_coverage_dates():
    response = client.get("/api/v1/symbols/NABIL")

    assert response.status_code == 200
    profile = response.json()["data"]
    assert profile["symbol"] == "NABIL"
    assert profile["first_trade_date"] <= profile["last_trade_date"]

