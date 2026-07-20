from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sample():
    response = client.post("/api/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "sample"
    assert data["resident"]["deadline"]
    assert data["resident"]["actions"]
