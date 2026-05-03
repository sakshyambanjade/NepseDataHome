from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_market_daily_returns_companies_for_date(paid_api_headers):
    response = client.get("/api/v1/market/daily/2026-05-02", headers=paid_api_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["date"] == "2026-05-02"
    assert body["data"]
    assert response.headers["X-Credits-Used"] == "3"


def test_coverage_endpoint_returns_dataset_summary():
    response = client.get("/api/v1/coverage")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["symbols"] >= 100
    assert data["date_range"]["start"] <= "2007-01-01"
