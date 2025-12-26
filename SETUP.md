# 🚀 ExplainAI-Sentinel: Production Setup Guide

Welcome to the production setup guide for **ExplainAI-Sentinel**. This document provides step-by-step instructions for deploying the platform in different environments.

## 🛠 Prerequisites

Ensure you have the following installed:
- **Docker** and **Docker Compose**
- **Kubectl** (for Kubernetes deployment)
- **Make** (optional, for using the Makefile)
- **Python 3.10+** (for local AI engine testing)
- **JDK 17+** (for local Java/Scala/Kotlin testing)
- **Go 1.21+** (for local runtime testing)

---

## 📦 Deployment Options

### Option 1: Docker Compose (Quickest)
Ideal for development, testing, and single-node production.

1.  **Build all images**:
    ```bash
    make build
    ```
2.  **Start the stack**:
    ```bash
    make up
    ```
3.  **Monitor services**:
    ```bash
    make status
    ```
4.  **Access the Dashboard**:
    Open `http://localhost:3000` in your browser.

---

### Option 2: Kubernetes (Enterprise)
Ideal for high availability and scalable production.

1.  **Create Namespace**:
    ```bash
    kubectl apply -f deployment/kubernetes/namespace.yaml
    ```
2.  **Deploy Infrastructure (Mock)**:
    Ensure you have Postgres, Redis, and Neo4j running in your cluster or update the manifests to point to your managed instances.
3.  **Deploy Application Tiers**:
    ```bash
    kubectl apply -f deployment/kubernetes/
    ```
4.  **Verify Rollout**:
    ```bash
    kubectl get pods -n explainai-sentinel
    ```

---

## 🔍 Service Inventory

| Service | Port | Description |
|---------|------|-------------|
| **Runtime** | 8000 | Orchestration, Service Registry |
| **AI Engine** | 8001 | Anomaly Detection, XAI |
| **KG Engine** | 8002 | Knowledge Graph, Causal Reasoning |
| **Policy Engine** | 8003 | Zero-Trust Enforcement |
| **Networking** | 8080 | Secure Message Broker |
| **Logging** | 8082 | Lock-free Metrics Collection |
| **Data Pipeline** | 8083 | Kafka Streams / ETL |
| **Dashboard** | 3000 | Visualization UI |

---

## 📈 Monitoring & Observability

### Prometheus
Access raw metrics at `http://localhost:9090`. All services are pre-configured for scraping.

### Grafana
Access visualization at `http://localhost:3001`.
- **Default Login**: `admin / admin123`
- Pre-loaded dashboards are available for each platform component.

---

## 🧪 Verification & Testing

### Health Checks
Verify the health of individual components:
```bash
curl http://localhost:8000/health  # Runtime
curl http://localhost:8001/health  # AI Engine
curl http://localhost:8003/health  # Policy Engine
```

### Integration Test
Register a mock service with the Runtime:
```bash
curl -X POST http://localhost:8000/services/register \
     -H "Content-Type: application/json" \
     -d '{"name": "test-service", "address": "127.0.0.1:9999"}'
```

---

---

## 🛡 Security Hardening

### 1. Secrets Management
Do **not** store production passwords in the `docker-compose.yml`. Instead:
1.  **Use Environment Files**: Create a `.env` file (ensure it's in `.dockerignore` and `.gitignore`).
2.  **Vault Integration**: In enterprise environments, integrate with HashiCorp Vault or AWS Secrets Manager.
3.  **K8s Secrets**: Use Kubernetes Secrets for sensitive data:
    ```bash
    kubectl create secret generic sentinel-secrets \
      --from-literal=postgres-pass=your_secure_pass \
      --from-literal=neo4j-pass=your_secure_pass
    ```

### 2. Mutual TLS (mTLS)
For secure inter-service communication:
-   **Service Mesh**: We recommended deploying **Istio** or **Linkerd** on your Kubernetes cluster.
-   **Manual Certs**: Generate certificates for each service and mount them into the containers:
    ```yaml
    volumes:
      - ./certs/runtime.crt:/etc/ssl/certs/sentinel.crt
      - ./certs/runtime.key:/etc/ssl/private/sentinel.key
    ```

### 3. Network Policies
Restrict traffic between services using Kubernetes NetworkPolicies. For example, only the `Data Pipeline` should be able to talk to the `AI Engine`.

---

## 🆘 Troubleshooting
- **Logs**: Use `make logs` or `kubectl logs <pod_name>` to view real-time traces.
- **Resources**: The Knowledge Graph (Scala) and AI Engine (Python) are memory-intensive. Ensure nodes have at least 4GB of RAM available.
- **Networking**: If services cannot connect, verify they are on the same Docker network (`sentinel-network`).
