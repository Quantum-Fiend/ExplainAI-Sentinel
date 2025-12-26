# 📘 ExplainAI-Sentinel User Manual

Welcome to the official user manual for **ExplainAI-Sentinel**. This guide covers platform operation, monitoring, and troubleshooting for end-users and security officers.

## 🏁 Introduction
ExplainAI-Sentinel is an AI-driven zero-trust security platform. It monitors your distributed environment, detects anomalies, explains AI decisions, and automatically enforces security policies.

---

## 🚀 Getting Started

### 1. Accessing the Dashboard
The primary interface is the **Sentinel Dashboard**, accessible at `http://localhost:3000` (or via the Ingress IP in Kubernetes).

### 2. User Authentication
By default, the platform uses JWT-based authentication.
- **Role**: `Security Officer`
- **Permissions**: Full access to service registry, policy logs, and AI explanations.

---

## 🛡️ Security Operations

### Monitoring Real-Time Threats
Navigate to the **Alerts** tab to see a stream of detected anomalies. Each alert includes:
- **Severity**: Critical, High, Medium, Low
- **Explainability**: Click the "Why?" button to see SHAP/LIME plots explaining the AI's decision.
- **Root Cause**: The Knowledge Graph tab shows a causal chain of the attack.

### Managing Policies
You can define zero-trust policies in the **Policy Engine** view:
- **Trust Scores**: View the current trust rating of every microservice.
- **Quarantine**: Manually trigger service isolation if a threat is confirmed.

---

## 📊 Analytics & Reporting

### System Health
View global metrics in the pre-configured **Grafana Dashboards**:
- **Throughput**: Monitor events per second.
- **Latency**: Check AI inference and network broker performance.

### Causal Forensics
Use the **Forensics** tool to upload past logs and generate a causal reasoning report. This helps in post-mortem analysis of security incidents.

---

## 🛠 Troubleshooting

| Issue | Possible Cause | Solution |
| :--- | :--- | :--- |
| **No Alerts appearing** | Networking Broker down | Check `make status` or `kubectl get pods`. |
| **Auth Failures** | Expired JWT | Re-login via the Dashboard or Demo Script. |
| **High Memory Usage** | Knowledge Graph | Scaling: Increase memory limits in `knowledge-graph.yaml`. |

---

## 🆘 Support
For technical support, please contact the DevOps team at `support@explainai-sentinel.io` or visit our internal wiki.
