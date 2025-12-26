"""
AI Engine Package Initialization
"""

from .core.anomaly_detector import EnsembleAnomalyDetector, AnomalyResult, AnomalyType
from .core.explainer import ExplainableAI, Explanation
from .core.federated_learning import (
    FederatedLearningServer,
    FederatedLearningClient,
    ClientUpdate,
    FederatedRound
)
from .core.threat_intelligence import (
    ThreatIntelligence,
    ThreatDetection,
    ThreatLevel,
    ThreatCategory
)

__version__ = "1.0.0"
__all__ = [
    'EnsembleAnomalyDetector',
    'AnomalyResult',
    'AnomalyType',
    'ExplainableAI',
    'Explanation',
    'FederatedLearningServer',
    'FederatedLearningClient',
    'ClientUpdate',
    'FederatedRound',
    'ThreatIntelligence',
    'ThreatDetection',
    'ThreatLevel',
    'ThreatCategory'
]
