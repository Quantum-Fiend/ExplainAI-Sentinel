# 📖 ExplainAI-Sentinel API Documentation

This document describes the primary REST API endpoints for the **ExplainAI-Sentinel** platform.

## 🔐 Authentication

All secured endpoints require a JWT Bearer token in the `Authorization` header.

### 1. Login
- **Endpoint**: `POST /login`
- **Description**: Authenticates a user and returns a JWT token.
- **Request Body**: `{"username": "admin", "password": "..."}`
- **Response**: `{"token": "eyJhbG..."}`

---

## 🏛️ Core Runtime API

### 2. Service Registration
- **Endpoint**: `POST /api/v1/services/register`
- **Auth**: Required
- **Description**: Registers a new polyglot service with the orchestrator.
- **Request Body**:
  ```json
  {
    "name": "ai-engine",
    "address": "127.0.0.1:8001"
  }
  ```

### 3. List Services
- **Endpoint**: `GET /api/v1/services`
- **Auth**: Required
- **Description**: Returns a list of all currently registered services.

---

## 🤖 AI Security Engine

### 4. Anomaly Detection
- **Endpoint**: `POST /detect`
- **Description**: Analyzes security events for anomalies.
- **Request Body**:
  ```json
  {
    "event_id": "uuid",
    "features": { ... }
  }
  ```

### 5. Threat Intelligence
- **Endpoint**: `POST /threat/classify`
- **Description**: Classifies detected threats and suggests remediation.

---

## 🔐 Policy Engine (Zero-Trust)

### 6. Evaluate Policy
- **Endpoint**: `POST /evaluate`
- **Description**: Evaluates a request against security policies.

### 7. Global Trust Scores
- **Endpoint**: `GET /trust/scores`
- **Description**: Returns trust scores for all system entities.

---

## 🔗 Knowledge Graph

### 8. Causal Analysis
- **Endpoint**: `POST /graph/causal/trace`
- **Description**: Traces the root cause of an event using temporal correlation.

---

## 📊 Logging & Metrics

### 9. System Metrics
- **Endpoint**: `GET /metrics`
- **Description**: Standard Prometheus metrics endpoint.
