import time
import requests
import unittest
import uuid

# Configuration
CONFIG = {
    "RUNTIME_URL": "http://localhost:8000",
    "AI_URL": "http://localhost:8001",
    "POLICY_URL": "http://localhost:8003",
    "LOGIN_PAYLOAD": {"username": "admin", "password": "password123"}
}

class TestExplainAISentinelIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Get Authentication Token
        try:
            resp = requests.post(f"{CONFIG['RUNTIME_URL']}/login", json=CONFIG["LOGIN_PAYLOAD"])
            cls.token = resp.json()["token"]
            cls.headers = {"Authorization": f"Bearer {cls.token}"}
        except Exception:
            cls.token = None
            print("⚠️ Warning: Skipping Auth-dependent tests (Runtime might be in non-auth mode or down)")

    def test_01_runtime_health(self):
        resp = requests.get(f"{CONFIG['RUNTIME_URL']}/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, "OK")

    def test_02_service_registration(self):
        if not hasattr(self, 'token') or not self.token:
            self.skipTest("No auth token")
            
        service_data = {
            "id": str(uuid.uuid4()),
            "name": "integration-test-service",
            "address": "127.0.0.1:9090"
        }
        resp = requests.post(
            f"{CONFIG['RUNTIME_URL']}/api/v1/services/register",
            json=service_data,
            headers=self.headers
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("integration-test-service", resp.text)

    def test_03_ai_detection_pipeline(self):
        event = {
            "event_id": str(uuid.uuid4()),
            "features": {"f1": 1.0, "f2": 0.5},
            "metadata": {"source": "test"}
        }
        resp = requests.post(f"{CONFIG['AI_URL']}/detect", json=event)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("is_anomaly", resp.json())

    def test_04_policy_evaluation(self):
        context = {
            "service_id": "test",
            "action": "READ",
            "resource": "secrets",
            "attributes": {},
            "trust_score": {"score": 0.9}
        }
        resp = requests.post(f"{CONFIG['POLICY_URL']}/evaluate", json=context)
        self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    print("🧪 Running ExplainAI-Sentinel Integration Suite...")
    unittest.main()
