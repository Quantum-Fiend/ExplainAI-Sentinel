import requests
import json
import time
import random
import uuid

BASE_URLS = {
    "runtime": "http://localhost:8000",
    "ai_engine": "http://localhost:8001",
    "kg_engine": "http://localhost:8002",
    "policy_engine": "http://localhost:8003"
}

def print_header(msg):
    print(f"\n{'='*60}")
    print(f"🚀 {msg}")
    print(f"{'='*60}")

def demo_register_services():
    print_header("Registering Polyglot Services with Go Runtime")
    services = [
        {"name": "networking-java", "address": "127.0.0.1:8080"},
        {"name": "ai-engine-python", "address": "127.0.0.1:8001"},
        {"name": "policy-engine-rust", "address": "127.0.0.1:8003"},
        {"name": "logging-c", "address": "127.0.0.1:8082"}
    ]
    
    for s in services:
        try:
            resp = requests.post(f"{BASE_URLS['runtime']}/services/register", json=s)
            if resp.status_code == 200:
                print(f"✅ Registered: {s['name']} -> {resp.json().get('id')}")
        except Exception as e:
            print(f"❌ Failed to register {s['name']}: {e}")

def demo_trigger_anomaly():
    print_header("Triggering AI Anomaly Detection")
    payload = {
        "event_id": str(uuid.uuid4()),
        "features": {
            "failed_auth_count": 15,
            "network_latency": 450.5,
            "payload_size": 10240,
            "ssh_connection_attempts": 25
        },
        "metadata": {"source_ip": "192.168.1.105", "target": "auth-service"}
    }
    
    try:
        resp = requests.post(f"{BASE_URLS['ai_engine']}/detect", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            print(f"🤖 AI Response: Anomaly Detected? {data.get('is_anomaly')}")
            print(f"🧠 Confidence: {data.get('confidence')}")
            print(f"📜 Explanation: {data.get('explanation', {}).get('summary')}")
    except Exception as e:
        print(f"❌ AI Engine error: {e}")

def main():
    print_header("ExplainAI-Sentinel Platform Demo")
    print("This script simulates platform-wide interaction across the polyglot stack.")
    
    demo_register_services()
    time.sleep(1)
    demo_trigger_anomaly()
    
    print_header("Demo Complete!")
    print("Check the Dashboard at http://localhost:3000 to see real-time updates.")

if __name__ == "__main__":
    main()
