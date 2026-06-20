from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_returns_ready_status():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "calo-coach",
        "database": "configured",
        "ai_provider": "not_configured",
        "no_api_key_mode": True,
    }
