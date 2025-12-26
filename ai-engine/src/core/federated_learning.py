"""
Federated Learning Module
Privacy-preserving distributed learning with differential privacy and secure aggregation
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import torch
import torch.nn as nn
from loguru import logger
import hashlib
import json


@dataclass
class ClientUpdate:
    """Update from a federated learning client"""
    client_id: str
    model_weights: Dict[str, np.ndarray]
    num_samples: int
    loss: float
    metrics: Dict[str, float]
    round_number: int


@dataclass
class FederatedRound:
    """Results from a federated learning round"""
    round_number: int
    num_clients: int
    aggregated_weights: Dict[str, np.ndarray]
    avg_loss: float
    avg_metrics: Dict[str, float]
    convergence_score: float


class DifferentialPrivacy:
    """Implements differential privacy mechanisms"""
    
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
        
    def add_noise(self, data: np.ndarray, sensitivity: float = 1.0) -> np.ndarray:
        """
        Add Gaussian noise for differential privacy
        
        Args:
            data: Original data
            sensitivity: Sensitivity of the query
            
        Returns:
            Noisy data
        """
        # Calculate noise scale using Gaussian mechanism
        sigma = np.sqrt(2 * np.log(1.25 / self.delta)) * sensitivity / self.epsilon
        
        noise = np.random.normal(0, sigma, data.shape)
        return data + noise
        
    def clip_gradients(
        self, 
        gradients: Dict[str, np.ndarray],
        max_norm: float = 1.0
    ) -> Dict[str, np.ndarray]:
        """
        Clip gradients to bound sensitivity
        
        Args:
            gradients: Model gradients
            max_norm: Maximum L2 norm
            
        Returns:
            Clipped gradients
        """
        clipped = {}
        
        for name, grad in gradients.items():
            grad_norm = np.linalg.norm(grad)
            
            if grad_norm > max_norm:
                clipped[name] = grad * (max_norm / grad_norm)
            else:
                clipped[name] = grad
                
        return clipped


class SecureAggregation:
    """Implements secure aggregation protocol"""
    
    def __init__(self):
        self.client_keys = {}
        
    def generate_client_key(self, client_id: str) -> str:
        """Generate encryption key for client"""
        key = hashlib.sha256(f"{client_id}_{np.random.rand()}".encode()).hexdigest()
        self.client_keys[client_id] = key
        return key
        
    def encrypt_update(
        self,
        update: Dict[str, np.ndarray],
        client_id: str
    ) -> Dict[str, np.ndarray]:
        """
        Encrypt model update (simplified version)
        In production, use proper homomorphic encryption
        """
        if client_id not in self.client_keys:
            raise ValueError(f"No key found for client {client_id}")
            
        encrypted = {}
        key_int = int(self.client_keys[client_id][:8], 16)
        
        for name, weights in update.items():
            # Simple XOR-based encryption (use proper encryption in production)
            encrypted[name] = weights + (key_int % 100) / 100.0
            
        return encrypted
        
    def decrypt_and_aggregate(
        self,
        encrypted_updates: List[Tuple[str, Dict[str, np.ndarray]]],
        num_samples: List[int]
    ) -> Dict[str, np.ndarray]:
        """
        Decrypt and aggregate updates
        
        Args:
            encrypted_updates: List of (client_id, encrypted_weights)
            num_samples: Number of samples per client
            
        Returns:
            Aggregated weights
        """
        # Decrypt all updates
        decrypted_updates = []
        
        for client_id, encrypted in encrypted_updates:
            if client_id not in self.client_keys:
                logger.warning(f"Cannot decrypt update from {client_id}")
                continue
                
            key_int = int(self.client_keys[client_id][:8], 16)
            decrypted = {
                name: weights - (key_int % 100) / 100.0
                for name, weights in encrypted.items()
            }
            decrypted_updates.append(decrypted)
            
        # Weighted aggregation
        total_samples = sum(num_samples)
        aggregated = {}
        
        for name in decrypted_updates[0].keys():
            weighted_sum = sum(
                update[name] * (n / total_samples)
                for update, n in zip(decrypted_updates, num_samples)
            )
            aggregated[name] = weighted_sum
            
        return aggregated


class FederatedLearningServer:
    """
    Federated Learning Server
    Coordinates training across distributed clients with privacy preservation
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.current_round = 0
        self.global_model_weights = None
        self.round_history = []
        
        # Privacy components
        self.dp = DifferentialPrivacy(
            epsilon=config.get('privacy', {}).get('epsilon', 1.0),
            delta=config.get('privacy', {}).get('delta', 1e-5)
        )
        
        self.secure_agg = SecureAggregation() if config.get('privacy', {}).get('secure_aggregation') else None
        
        logger.info("Federated Learning Server initialized")
        
    def initialize_global_model(self, model_architecture: Dict[str, tuple]):
        """
        Initialize global model weights
        
        Args:
            model_architecture: Dict mapping layer names to shapes
        """
        self.global_model_weights = {
            name: np.random.randn(*shape) * 0.01
            for name, shape in model_architecture.items()
        }
        
        logger.info(f"Global model initialized with {len(self.global_model_weights)} layers")
        
    def select_clients(self, available_clients: List[str]) -> List[str]:
        """
        Select clients for current round
        
        Args:
            available_clients: List of available client IDs
            
        Returns:
            Selected client IDs
        """
        fraction = self.config.get('fraction_fit', 0.5)
        min_clients = self.config.get('min_clients', 3)
        
        num_clients = max(min_clients, int(len(available_clients) * fraction))
        selected = np.random.choice(
            available_clients,
            size=min(num_clients, len(available_clients)),
            replace=False
        )
        
        logger.info(f"Selected {len(selected)} clients for round {self.current_round + 1}")
        return selected.tolist()
        
    def aggregate_updates(
        self,
        client_updates: List[ClientUpdate]
    ) -> FederatedRound:
        """
        Aggregate client updates using FedAvg or secure aggregation
        
        Args:
            client_updates: List of client updates
            
        Returns:
            Federated round results
        """
        if not client_updates:
            raise ValueError("No client updates to aggregate")
            
        logger.info(f"Aggregating updates from {len(client_updates)} clients")
        
        # Apply differential privacy if enabled
        if self.config.get('privacy', {}).get('differential_privacy'):
            client_updates = self._apply_differential_privacy(client_updates)
            
        # Secure aggregation if enabled
        if self.secure_agg:
            aggregated_weights = self._secure_aggregate(client_updates)
        else:
            aggregated_weights = self._fedavg_aggregate(client_updates)
            
        # Calculate metrics
        avg_loss = np.mean([update.loss for update in client_updates])
        
        avg_metrics = {}
        if client_updates[0].metrics:
            for metric_name in client_updates[0].metrics.keys():
                avg_metrics[metric_name] = np.mean([
                    update.metrics[metric_name] 
                    for update in client_updates
                ])
                
        # Calculate convergence score
        convergence_score = self._calculate_convergence(aggregated_weights)
        
        # Update global model
        self.global_model_weights = aggregated_weights
        self.current_round += 1
        
        round_result = FederatedRound(
            round_number=self.current_round,
            num_clients=len(client_updates),
            aggregated_weights=aggregated_weights,
            avg_loss=avg_loss,
            avg_metrics=avg_metrics,
            convergence_score=convergence_score
        )
        
        self.round_history.append(round_result)
        
        logger.info(
            f"Round {self.current_round} completed - "
            f"Loss: {avg_loss:.4f}, Convergence: {convergence_score:.4f}"
        )
        
        return round_result
        
    def _fedavg_aggregate(
        self,
        client_updates: List[ClientUpdate]
    ) -> Dict[str, np.ndarray]:
        """Standard FedAvg aggregation"""
        
        total_samples = sum(update.num_samples for update in client_updates)
        aggregated = {}
        
        for layer_name in client_updates[0].model_weights.keys():
            weighted_sum = sum(
                update.model_weights[layer_name] * (update.num_samples / total_samples)
                for update in client_updates
            )
            aggregated[layer_name] = weighted_sum
            
        return aggregated
        
    def _secure_aggregate(
        self,
        client_updates: List[ClientUpdate]
    ) -> Dict[str, np.ndarray]:
        """Secure aggregation with encryption"""
        
        # Encrypt updates
        encrypted_updates = [
            (update.client_id, self.secure_agg.encrypt_update(
                update.model_weights,
                update.client_id
            ))
            for update in client_updates
        ]
        
        # Decrypt and aggregate
        num_samples = [update.num_samples for update in client_updates]
        aggregated = self.secure_agg.decrypt_and_aggregate(
            encrypted_updates,
            num_samples
        )
        
        return aggregated
        
    def _apply_differential_privacy(
        self,
        client_updates: List[ClientUpdate]
    ) -> List[ClientUpdate]:
        """Apply differential privacy to client updates"""
        
        noisy_updates = []
        
        for update in client_updates:
            # Clip gradients
            clipped_weights = self.dp.clip_gradients(update.model_weights)
            
            # Add noise
            noisy_weights = {
                name: self.dp.add_noise(weights)
                for name, weights in clipped_weights.items()
            }
            
            noisy_update = ClientUpdate(
                client_id=update.client_id,
                model_weights=noisy_weights,
                num_samples=update.num_samples,
                loss=update.loss,
                metrics=update.metrics,
                round_number=update.round_number
            )
            
            noisy_updates.append(noisy_update)
            
        return noisy_updates
        
    def _calculate_convergence(
        self,
        new_weights: Dict[str, np.ndarray]
    ) -> float:
        """Calculate convergence score based on weight changes"""
        
        if not self.round_history:
            return 1.0
            
        prev_weights = self.round_history[-1].aggregated_weights
        
        total_change = 0.0
        total_norm = 0.0
        
        for name in new_weights.keys():
            change = np.linalg.norm(new_weights[name] - prev_weights[name])
            norm = np.linalg.norm(prev_weights[name])
            
            total_change += change
            total_norm += norm
            
        # Normalized change (lower is better)
        convergence_score = 1.0 - min(total_change / (total_norm + 1e-8), 1.0)
        
        return float(convergence_score)
        
    def get_global_model(self) -> Dict[str, np.ndarray]:
        """Get current global model weights"""
        return self.global_model_weights.copy()
        
    def save_checkpoint(self, path: str):
        """Save server state"""
        checkpoint = {
            'round': self.current_round,
            'global_weights': {k: v.tolist() for k, v in self.global_model_weights.items()},
            'config': self.config
        }
        
        with open(path, 'w') as f:
            json.dump(checkpoint, f)
            
        logger.info(f"Checkpoint saved to {path}")
        
    def load_checkpoint(self, path: str):
        """Load server state"""
        with open(path, 'r') as f:
            checkpoint = json.load(f)
            
        self.current_round = checkpoint['round']
        self.global_model_weights = {
            k: np.array(v) for k, v in checkpoint['global_weights'].items()
        }
        self.config = checkpoint['config']
        
        logger.info(f"Checkpoint loaded from {path}")


class FederatedLearningClient:
    """Federated Learning Client"""
    
    def __init__(self, client_id: str, local_data: np.ndarray, local_labels: np.ndarray):
        self.client_id = client_id
        self.local_data = local_data
        self.local_labels = local_labels
        self.model_weights = None
        
        logger.info(f"Client {client_id} initialized with {len(local_data)} samples")
        
    def train(
        self,
        global_weights: Dict[str, np.ndarray],
        epochs: int = 5,
        batch_size: int = 32
    ) -> ClientUpdate:
        """
        Train on local data
        
        Args:
            global_weights: Current global model weights
            epochs: Number of local epochs
            batch_size: Batch size
            
        Returns:
            Client update
        """
        # Initialize with global weights
        self.model_weights = {k: v.copy() for k, v in global_weights.items()}
        
        # Simulate training (in production, use actual model training)
        num_batches = len(self.local_data) // batch_size
        total_loss = 0.0
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            for i in range(num_batches):
                # Simulate gradient update
                for name in self.model_weights.keys():
                    gradient = np.random.randn(*self.model_weights[name].shape) * 0.01
                    self.model_weights[name] -= 0.01 * gradient
                    
                epoch_loss += np.random.rand()
                
            total_loss += epoch_loss / num_batches
            
        avg_loss = total_loss / epochs
        
        update = ClientUpdate(
            client_id=self.client_id,
            model_weights=self.model_weights,
            num_samples=len(self.local_data),
            loss=avg_loss,
            metrics={'accuracy': 0.85 + np.random.rand() * 0.1},
            round_number=0
        )
        
        logger.info(f"Client {self.client_id} training completed - Loss: {avg_loss:.4f}")
        
        return update


if __name__ == "__main__":
    # Example usage
    config = {
        'strategy': 'FedAvg',
        'num_rounds': 10,
        'min_clients': 3,
        'fraction_fit': 0.5,
        'privacy': {
            'differential_privacy': True,
            'epsilon': 1.0,
            'delta': 1e-5,
            'secure_aggregation': True
        }
    }
    
    # Initialize server
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
        
        # Register with secure aggregation
        if server.secure_agg:
            server.secure_agg.generate_client_key(f"client_{i}")
    
    # Run federated learning rounds
    for round_num in range(3):
        print(f"\n=== Round {round_num + 1} ===")
        
        # Select clients
        selected_ids = server.select_clients([c.client_id for c in clients])
        selected_clients = [c for c in clients if c.client_id in selected_ids]
        
        # Train clients
        updates = []
        global_weights = server.get_global_model()
        
        for client in selected_clients:
            update = client.train(global_weights, epochs=5)
            updates.append(update)
            
        # Aggregate
        round_result = server.aggregate_updates(updates)
        print(f"Average Loss: {round_result.avg_loss:.4f}")
        print(f"Convergence Score: {round_result.convergence_score:.4f}")
