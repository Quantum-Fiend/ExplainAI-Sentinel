# ExplainAI-Sentinel AI Engine

Production-ready AI/ML security engine with explainable AI, federated learning, and threat intelligence.

## Features

- **Ensemble Anomaly Detection**: Multiple algorithms (Isolation Forest, One-Class SVM, Autoencoder, LSTM VAE)
- **Explainable AI**: SHAP, LIME, and rule-based explanations with natural language narratives
- **Federated Learning**: Privacy-preserving distributed learning with differential privacy
- **Threat Intelligence**: ML-based threat classification with automated remediation
- **Model Serving**: FastAPI-based REST API with Prometheus metrics

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Start AI Model Server

```bash
python src/api/model_server.py
```

The API will be available at `http://localhost:8001`

### API Endpoints

#### Health Check
```bash
curl http://localhost:8001/health
```

#### Detect Anomalies
```bash
curl -X POST http://localhost:8001/detect \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "cpu_usage": 85.0,
      "memory_usage": 75.0,
      "network_connections": 150.0,
      "failed_auth": 10.0
    },
    "explain": true
  }'
```

#### Get Metrics
```bash
curl http://localhost:8001/metrics
```

## Usage Examples

### Anomaly Detection

```python
from src.core.anomaly_detector import EnsembleAnomalyDetector
import numpy as np

# Initialize detector
config = {
    'algorithms': ['isolation_forest', 'one_class_svm', 'autoencoder'],
    'ensemble_voting': 'soft',
    'confidence_threshold': 0.75
}

detector = EnsembleAnomalyDetector(config)

# Train on normal data
X_train = np.random.randn(1000, 10)
detector.train(X_train)

# Detect anomalies
X_test = np.random.randn(10) * 5
result = detector.detect(X_test)

print(f"Anomaly: {result.is_anomaly}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Explanation: {result.explanation}")
```

### Explainable AI

```python
from src.core.explainer import ExplainableAI
from sklearn.ensemble import RandomForestClassifier

# Train a model
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Initialize explainer
config = {'background_samples': 100, 'max_evals': 1000}
explainer = ExplainableAI(config)

# Initialize SHAP
feature_names = [f"feature_{i}" for i in range(10)]
explainer.initialize_shap(model, X_train, feature_names)

# Get explanation
test_instance = np.random.randn(10)
explanation = explainer.explain_with_shap(test_instance, model)

print(explanation.natural_language)
```

### Federated Learning

```python
from src.core.federated_learning import FederatedLearningServer, FederatedLearningClient

# Initialize server
config = {
    'strategy': 'FedAvg',
    'num_rounds': 10,
    'min_clients': 3,
    'privacy': {
        'differential_privacy': True,
        'epsilon': 1.0,
        'secure_aggregation': True
    }
}

server = FederatedLearningServer(config)

# Initialize global model
model_arch = {
    'layer1': (10, 64),
    'layer2': (64, 32),
    'layer3': (32, 2)
}
server.initialize_global_model(model_arch)

# Create clients
clients = []
for i in range(5):
    data = np.random.randn(100, 10)
    labels = np.random.randint(0, 2, 100)
    client = FederatedLearningClient(f"client_{i}", data, labels)
    clients.append(client)

# Run federated learning
for round_num in range(3):
    selected_ids = server.select_clients([c.client_id for c in clients])
    selected_clients = [c for c in clients if c.client_id in selected_ids]
    
    updates = []
    global_weights = server.get_global_model()
    
    for client in selected_clients:
        update = client.train(global_weights, epochs=5)
        updates.append(update)
    
    round_result = server.aggregate_updates(updates)
    print(f"Round {round_num + 1} - Loss: {round_result.avg_loss:.4f}")
```

### Threat Intelligence

```python
from src.core.threat_intelligence import ThreatIntelligence

# Initialize threat intelligence
ti = ThreatIntelligence({})

# Train classifier
ti.train_classifier(X_train, y_train, feature_names)

# Detect threats
features = {
    'cpu_usage': 85.0,
    'failed_auth': 10.0,
    'outbound_bytes': 1000000.0,
    'external_conn': 3.0
}

detection = ti.detect_threat(features)

if detection:
    print(f"Threat: {detection.category.value}")
    print(f"Level: {detection.level.value}")
    print(f"Actions: {detection.recommended_actions}")
```

## Configuration

Edit `config/ai_config.yaml` to customize:

- Model algorithms and parameters
- Explainability methods
- Federated learning settings
- Privacy parameters
- API configuration

## Monitoring

Prometheus metrics available at `/metrics`:

- `ai_requests_total`: Total inference requests
- `anomalies_detected_total`: Total anomalies detected
- `request_latency_seconds`: Request latency histogram
- `explanation_latency_seconds`: Explanation generation latency

## Architecture

```
ai-engine/
├── src/
│   ├── core/
│   │   ├── anomaly_detector.py    # Ensemble anomaly detection
│   │   ├── explainer.py           # Explainable AI (SHAP, LIME)
│   │   ├── federated_learning.py  # Federated learning
│   │   └── threat_intelligence.py # Threat classification
│   ├── api/
│   │   └── model_server.py        # FastAPI server
│   └── __init__.py
├── config/
│   └── ai_config.yaml             # Configuration
├── models/                        # Saved models
├── requirements.txt
└── README.md
```

## License

MIT License
