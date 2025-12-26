"""
Advanced Anomaly Detection Engine with Ensemble Methods
Supports multiple algorithms and provides explainable results
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from pyod.models.auto_encoder import AutoEncoder
from loguru import logger
import json


class AnomalyType(Enum):
    NETWORK = "network"
    SYSTEM = "system"
    BEHAVIORAL = "behavioral"
    SECURITY = "security"


@dataclass
class AnomalyResult:
    """Result of anomaly detection"""
    is_anomaly: bool
    confidence: float
    anomaly_score: float
    anomaly_type: AnomalyType
    features: Dict[str, float]
    explanation: Dict[str, any]
    timestamp: float
    metadata: Dict[str, any]


class LSTMAutoencoder(nn.Module):
    """LSTM-based Autoencoder for time-series anomaly detection"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        super(LSTMAutoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.LSTM(
            input_dim, hidden_dim, num_layers, 
            batch_first=True, dropout=0.2
        )
        
        # Decoder
        self.decoder = nn.LSTM(
            hidden_dim, hidden_dim, num_layers,
            batch_first=True, dropout=0.2
        )
        
        # Output layer
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def forward(self, x):
        # Encode
        encoded, (hidden, cell) = self.encoder(x)
        
        # Decode
        decoded, _ = self.decoder(encoded, (hidden, cell))
        
        # Reconstruct
        reconstructed = self.output_layer(decoded)
        
        return reconstructed


class EnsembleAnomalyDetector:
    """
    Ensemble-based anomaly detector combining multiple algorithms
    Provides explainable results with confidence scores
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self.is_trained = False
        self.feature_importance = {}
        
        # Initialize models
        self._initialize_models()
        
        logger.info("Ensemble Anomaly Detector initialized")
        
    def _initialize_models(self):
        """Initialize all detection models"""
        algorithms = self.config.get('algorithms', [])
        
        if 'isolation_forest' in algorithms:
            self.models['isolation_forest'] = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_estimators=100
            )
            
        if 'one_class_svm' in algorithms:
            self.models['one_class_svm'] = OneClassSVM(
                kernel='rbf',
                gamma='auto',
                nu=0.1
            )
            
        if 'autoencoder' in algorithms:
            self.models['autoencoder'] = AutoEncoder(
                hidden_neurons=[64, 32, 32, 64],
                contamination=0.1,
                epochs=50,
                batch_size=32
            )
            
        if 'lstm_vae' in algorithms:
            # Will be initialized during training with proper dimensions
            self.models['lstm_vae'] = None
            
    def train(self, X: np.ndarray, feature_names: List[str] = None):
        """
        Train all models on normal data
        
        Args:
            X: Training data (normal behavior)
            feature_names: Names of features
        """
        logger.info(f"Training anomaly detector on {X.shape[0]} samples")
        
        # Train traditional models
        for name, model in self.models.items():
            if model is not None and name != 'lstm_vae':
                try:
                    model.fit(X)
                    logger.info(f"Trained {name} successfully")
                except Exception as e:
                    logger.error(f"Failed to train {name}: {e}")
                    
        # Train LSTM VAE if enabled
        if 'lstm_vae' in self.models:
            self._train_lstm_vae(X)
            
        self.is_trained = True
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X.shape[1])]
        
        logger.info("Anomaly detector training completed")
        
    def _train_lstm_vae(self, X: np.ndarray, sequence_length: int = 10):
        """Train LSTM Variational Autoencoder"""
        try:
            # Reshape data for LSTM (samples, sequence_length, features)
            n_samples = X.shape[0] - sequence_length + 1
            n_features = X.shape[1]
            
            sequences = np.array([
                X[i:i+sequence_length] 
                for i in range(n_samples)
            ])
            
            # Initialize model
            model = LSTMAutoencoder(n_features)
            optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
            criterion = nn.MSELoss()
            
            # Convert to tensor
            X_tensor = torch.FloatTensor(sequences)
            
            # Training loop
            model.train()
            epochs = 50
            batch_size = 32
            
            for epoch in range(epochs):
                total_loss = 0
                for i in range(0, len(X_tensor), batch_size):
                    batch = X_tensor[i:i+batch_size]
                    
                    optimizer.zero_grad()
                    reconstructed = model(batch)
                    loss = criterion(reconstructed, batch)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                    
                if (epoch + 1) % 10 == 0:
                    logger.info(f"LSTM VAE Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")
                    
            model.eval()
            self.models['lstm_vae'] = {
                'model': model,
                'sequence_length': sequence_length
            }
            
            logger.info("LSTM VAE training completed")
            
        except Exception as e:
            logger.error(f"Failed to train LSTM VAE: {e}")
            self.models['lstm_vae'] = None
            
    def detect(self, X: np.ndarray, threshold: float = None) -> AnomalyResult:
        """
        Detect anomalies in input data
        
        Args:
            X: Input features
            threshold: Custom confidence threshold
            
        Returns:
            AnomalyResult with detection details
        """
        if not self.is_trained:
            raise RuntimeError("Detector must be trained before detection")
            
        threshold = threshold or self.config.get('confidence_threshold', 0.75)
        
        # Get predictions from all models
        predictions = {}
        scores = {}
        
        for name, model in self.models.items():
            if model is not None and name != 'lstm_vae':
                try:
                    pred = model.predict(X.reshape(1, -1))[0]
                    score = model.score_samples(X.reshape(1, -1))[0]
                    
                    predictions[name] = pred
                    scores[name] = score
                except Exception as e:
                    logger.warning(f"Detection failed for {name}: {e}")
                    
        # Ensemble voting
        voting_method = self.config.get('ensemble_voting', 'soft')
        
        if voting_method == 'soft':
            # Weighted average of scores
            avg_score = np.mean(list(scores.values()))
            is_anomaly = avg_score < -threshold
            confidence = abs(avg_score)
        else:
            # Hard voting
            anomaly_votes = sum(1 for p in predictions.values() if p == -1)
            is_anomaly = anomaly_votes > len(predictions) / 2
            confidence = anomaly_votes / len(predictions)
            avg_score = -confidence if is_anomaly else confidence
            
        # Generate explanation
        explanation = self._generate_explanation(X, scores, predictions)
        
        # Create result
        result = AnomalyResult(
            is_anomaly=is_anomaly,
            confidence=float(confidence),
            anomaly_score=float(avg_score),
            anomaly_type=AnomalyType.SECURITY,  # Can be determined by feature analysis
            features={name: float(val) for name, val in zip(self.feature_names, X)},
            explanation=explanation,
            timestamp=np.datetime64('now').astype(float),
            metadata={
                'model_predictions': predictions,
                'model_scores': {k: float(v) for k, v in scores.items()}
            }
        )
        
        return result
        
    def _generate_explanation(
        self, 
        X: np.ndarray, 
        scores: Dict[str, float],
        predictions: Dict[str, int]
    ) -> Dict[str, any]:
        """Generate human-readable explanation for detection"""
        
        # Feature contribution analysis
        feature_contributions = {}
        
        # Simple feature importance based on deviation from mean
        for i, (name, value) in enumerate(zip(self.feature_names, X)):
            # Placeholder - in production, use SHAP or LIME
            contribution = abs(value)
            feature_contributions[name] = float(contribution)
            
        # Sort by contribution
        top_features = sorted(
            feature_contributions.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        explanation = {
            'summary': self._generate_summary(predictions, scores),
            'top_contributing_features': dict(top_features),
            'model_agreement': len([p for p in predictions.values() if p == -1]) / len(predictions),
            'confidence_breakdown': {k: float(v) for k, v in scores.items()}
        }
        
        return explanation
        
    def _generate_summary(
        self, 
        predictions: Dict[str, int],
        scores: Dict[str, float]
    ) -> str:
        """Generate natural language summary"""
        
        anomaly_count = sum(1 for p in predictions.values() if p == -1)
        total_models = len(predictions)
        
        if anomaly_count == 0:
            return "All models indicate normal behavior"
        elif anomaly_count == total_models:
            return f"All {total_models} models detected anomalous behavior with high confidence"
        else:
            return f"{anomaly_count} out of {total_models} models detected anomalous behavior"
            
    def save_model(self, path: str):
        """Save trained models"""
        import joblib
        
        save_data = {
            'models': {k: v for k, v in self.models.items() if k != 'lstm_vae'},
            'config': self.config,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        joblib.dump(save_data, path)
        logger.info(f"Model saved to {path}")
        
    def load_model(self, path: str):
        """Load trained models"""
        import joblib
        
        save_data = joblib.load(path)
        self.models.update(save_data['models'])
        self.config = save_data['config']
        self.feature_names = save_data['feature_names']
        self.is_trained = save_data['is_trained']
        
        logger.info(f"Model loaded from {path}")


if __name__ == "__main__":
    # Example usage
    config = {
        'algorithms': ['isolation_forest', 'one_class_svm', 'autoencoder'],
        'ensemble_voting': 'soft',
        'confidence_threshold': 0.75
    }
    
    # Create detector
    detector = EnsembleAnomalyDetector(config)
    
    # Generate synthetic training data (normal behavior)
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)
    
    # Train
    detector.train(X_train)
    
    # Test with normal data
    X_normal = np.random.randn(10)
    result_normal = detector.detect(X_normal)
    print(f"Normal data - Anomaly: {result_normal.is_anomaly}, Confidence: {result_normal.confidence:.3f}")
    
    # Test with anomalous data
    X_anomaly = np.random.randn(10) * 5 + 10
    result_anomaly = detector.detect(X_anomaly)
    print(f"Anomaly data - Anomaly: {result_anomaly.is_anomaly}, Confidence: {result_anomaly.confidence:.3f}")
    print(f"Explanation: {json.dumps(result_anomaly.explanation, indent=2)}")
