# Deployment & Orchestration

This directory contains the scripts and manifests for deploying the **ExplainAI-Sentinel** platform.

## 📁 Structure

- **`/scripts`**: Ruby orchestrator for container lifecycle.
- **`/kubernetes`**: Production K8s manifests (Namespace, Deployments, Services).
- **`docker-compose.yml`**: Unified stack for all 9 polyglot services + infra.
- **`prometheus.yml`**: Metrics scraping configuration.
- **`grafana-dashboard.json`**: Pre-configured visualization dashboard.

## 🚀 Quick Start

From the root directory:

```bash
# 1. Build everything
make build

# 2. Launch the stack
make up

# 3. Verify services
make status

# 4. Run the Demonstration Script
python demo_sentinel.py
```

## 🛠 Kubernetes Deployment

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/
```

## 📊 Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (Admin / admin123)
