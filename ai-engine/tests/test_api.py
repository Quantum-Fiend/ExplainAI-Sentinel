import pytest
import json
from src.api.model_server import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_anomaly_detection_endpoint():
    payload = {
        "event_id": "test-event-123",
        "features": {
            "failed_auth_count": 0,
            "network_latency": 20.5,
            "payload_size": 500,
            "ssh_connection_attempts": 1
        },
        "metadata": {"source_ip": "127.0.0.1"}
    }
    response = client.post("/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_anomaly" in data
    assert "confidence" in data
    assert "explanation" in data

def test_threat_classification_endpoint():
    payload = {
        "event_type": "ssh_brute_force",
        "severity": 0.9,
        "source": "192.168.1.1"
    }
    response = client.post("/threat/classify", json=payload)
    assert response.status_code == 200
    assert "classification" in response.json()
