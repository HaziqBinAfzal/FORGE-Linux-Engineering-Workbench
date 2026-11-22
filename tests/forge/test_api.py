from fastapi.testclient import TestClient

from forge.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_system_snapshot():
    response = client.get("/api/system")
    assert response.status_code == 200

    data = response.json()

    assert "hostname" in data
    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data

    assert 0 <= data["memory"]["usage_percent"] <= 100
    assert 0 <= data["disk"]["usage_percent"] <= 100


def test_processes():
    response = client.get("/api/processes")
    assert response.status_code == 200

    processes = response.json()["processes"]

    assert isinstance(processes, list)
    assert len(processes) <= 8
