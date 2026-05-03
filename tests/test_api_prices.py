from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_prices_returns_valid_data_with_filters_and_limit(paid_api_headers):
    response = client.get(
        "/api/v1/prices/NABIL?start=2015-01-01&end=2026-05-02&limit=5",
        headers=paid_api_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["symbol"] == "NABIL"
    assert body["meta"]["count"] <= 5
    assert body["data"]
    assert body["data"][0]["date"] >= "2015-01-01"
    assert response.headers["X-Credits-Used"] == "1"


def test_invalid_symbol_returns_standard_error(paid_api_headers):
    response = client.get("/api/v1/prices/INVALID", headers=paid_api_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SYMBOL_NOT_FOUND"


def test_missing_api_key_returns_401():
    response = client.get("/api/v1/prices/NABIL")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "API_KEY_REQUIRED"
