"""
Threat Intelligence and Classification Module
Real-time threat detection and classification with confidence scoring
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import torch
import torch.nn as nn
from sklearn.ensemble import GradientBoostingClassifier
from loguru import logger
import json


class ThreatLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatCategory(Enum):
    MALWARE = "malware"
    INTRUSION = "intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    DOS = "denial_of_service"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    LATERAL_MOVEMENT = "lateral_movement"
    RECONNAISSANCE = "reconnaissance"
    UNKNOWN = "unknown"


@dataclass
class ThreatDetection:
    """Threat detection result"""
    threat_id: str
    category: ThreatCategory
    level: ThreatLevel
    confidence: float
    description: str
    indicators: Dict[str, any]
    recommended_actions: List[str]
    timestamp: datetime
    metadata: Dict[str, any]


class ThreatIntelligence:
    """
    Threat Intelligence and Classification Engine
    Uses ML models and rule-based systems for threat detection
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.classifier = None
        self.feature_names = None
        self.threat_patterns = self._load_threat_patterns()
        self.threat_history = []
        
        logger.info("Threat Intelligence module initialized")
        
    def _load_threat_patterns(self) -> Dict[ThreatCategory, List[Dict]]:
        """Load known threat patterns"""
        return {
            ThreatCategory.MALWARE: [
                {
                    'pattern': 'high_cpu_network_combo',
                    'indicators': ['cpu_usage > 80', 'network_connections > 100'],
                    'confidence': 0.85
                },
                {
                    'pattern': 'suspicious_process',
                    'indicators': ['unknown_process', 'high_memory'],
                    'confidence': 0.75
                }
            ],
            ThreatCategory.INTRUSION: [
                {
                    'pattern': 'failed_auth_attempts',
                    'indicators': ['failed_logins > 5', 'short_time_window'],
                    'confidence': 0.90
                },
                {
                    'pattern': 'port_scanning',
                    'indicators': ['multiple_ports', 'sequential_access'],
                    'confidence': 0.80
                }
            ],
            ThreatCategory.DATA_EXFILTRATION: [
                {
                    'pattern': 'unusual_data_transfer',
                    'indicators': ['large_outbound_traffic', 'unusual_destination'],
                    'confidence': 0.85
                }
            ],
            ThreatCategory.DOS: [
                {
                    'pattern': 'traffic_flood',
                    'indicators': ['request_rate > 1000', 'single_source'],
                    'confidence': 0.95
                }
            ]
        }
        
    def train_classifier(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: List[str]
    ):
        """
        Train threat classification model
        
        Args:
            X_train: Training features
            y_train: Training labels (threat categories)
            feature_names: Names of features
        """
        logger.info(f"Training threat classifier on {len(X_train)} samples")
        
        self.classifier = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        self.classifier.fit(X_train, y_train)
        self.feature_names = feature_names
        
        # Calculate feature importance
        self.feature_importance = dict(zip(
            feature_names,
            self.classifier.feature_importances_
        ))
        
        logger.info("Threat classifier training completed")
        
    def detect_threat(
        self,
        features: Dict[str, float],
        context: Optional[Dict] = None
    ) -> Optional[ThreatDetection]:
        """
        Detect and classify threats
        
        Args:
            features: Feature dictionary
            context: Additional context information
            
        Returns:
            ThreatDetection if threat found, None otherwise
        """
        # Convert features to array
        feature_array = np.array([features.get(name, 0.0) for name in self.feature_names])
        
        # ML-based classification
        ml_prediction = None
        ml_confidence = 0.0
        
        if self.classifier is not None:
            ml_prediction = self.classifier.predict(feature_array.reshape(1, -1))[0]
            ml_proba = self.classifier.predict_proba(feature_array.reshape(1, -1))[0]
            ml_confidence = float(np.max(ml_proba))
            
        # Rule-based detection
        rule_matches = self._match_threat_patterns(features)
        
        # Combine ML and rule-based results
        if ml_confidence > 0.7 or rule_matches:
            # Determine threat category
            if rule_matches:
                category = rule_matches[0]['category']
                confidence = max(ml_confidence, rule_matches[0]['confidence'])
            else:
                category = ThreatCategory(ml_prediction)
                confidence = ml_confidence
                
            # Determine threat level
            level = self._calculate_threat_level(confidence, category)
            
            # Generate threat ID
            threat_id = self._generate_threat_id(category)
            
            # Get indicators
            indicators = self._extract_indicators(features, category)
            
            # Generate description
            description = self._generate_threat_description(category, indicators)
            
            # Get recommended actions
            actions = self._get_recommended_actions(category, level)
            
            detection = ThreatDetection(
                threat_id=threat_id,
                category=category,
                level=level,
                confidence=confidence,
                description=description,
                indicators=indicators,
                recommended_actions=actions,
                timestamp=datetime.now(),
                metadata={
                    'ml_prediction': ml_prediction,
                    'ml_confidence': ml_confidence,
                    'rule_matches': len(rule_matches),
                    'context': context or {}
                }
            )
            
            self.threat_history.append(detection)
            
            logger.warning(
                f"Threat detected: {category.value} - "
                f"Level: {level.value} - "
                f"Confidence: {confidence:.2f}"
            )
            
            return detection
            
        return None
        
    def _match_threat_patterns(
        self,
        features: Dict[str, float]
    ) -> List[Dict]:
        """Match features against known threat patterns"""
        matches = []
        
        for category, patterns in self.threat_patterns.items():
            for pattern in patterns:
                # Simple pattern matching (in production, use more sophisticated logic)
                match_score = self._evaluate_pattern(features, pattern)
                
                if match_score > 0.6:
                    matches.append({
                        'category': category,
                        'pattern': pattern['pattern'],
                        'confidence': pattern['confidence'] * match_score
                    })
                    
        return sorted(matches, key=lambda x: x['confidence'], reverse=True)
        
    def _evaluate_pattern(
        self,
        features: Dict[str, float],
        pattern: Dict
    ) -> float:
        """Evaluate how well features match a pattern"""
        # Simplified pattern matching
        # In production, implement proper rule evaluation
        
        score = 0.0
        indicators = pattern['indicators']
        
        # Check for key indicators in features
        for indicator in indicators:
            if any(key in indicator for key in features.keys()):
                score += 1.0 / len(indicators)
                
        return score
        
    def _calculate_threat_level(
        self,
        confidence: float,
        category: ThreatCategory
    ) -> ThreatLevel:
        """Calculate threat level based on confidence and category"""
        
        # Critical categories
        critical_categories = [
            ThreatCategory.DATA_EXFILTRATION,
            ThreatCategory.PRIVILEGE_ESCALATION
        ]
        
        if category in critical_categories and confidence > 0.8:
            return ThreatLevel.CRITICAL
        elif confidence > 0.9:
            return ThreatLevel.CRITICAL
        elif confidence > 0.75:
            return ThreatLevel.HIGH
        elif confidence > 0.6:
            return ThreatLevel.MEDIUM
        elif confidence > 0.4:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.INFO
            
    def _generate_threat_id(self, category: ThreatCategory) -> str:
        """Generate unique threat ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"THR-{category.value.upper()}-{timestamp}"
        
    def _extract_indicators(
        self,
        features: Dict[str, float],
        category: ThreatCategory
    ) -> Dict[str, any]:
        """Extract relevant indicators for threat"""
        
        # Get top features by value
        sorted_features = sorted(
            features.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]
        
        return {
            'top_features': dict(sorted_features),
            'category_specific': self._get_category_indicators(category, features)
        }
        
    def _get_category_indicators(
        self,
        category: ThreatCategory,
        features: Dict[str, float]
    ) -> Dict[str, any]:
        """Get category-specific indicators"""
        
        indicators = {}
        
        if category == ThreatCategory.MALWARE:
            indicators['suspicious_processes'] = features.get('process_count', 0)
            indicators['cpu_usage'] = features.get('cpu_usage', 0)
            
        elif category == ThreatCategory.INTRUSION:
            indicators['failed_attempts'] = features.get('failed_auth', 0)
            indicators['source_ips'] = features.get('unique_ips', 0)
            
        elif category == ThreatCategory.DATA_EXFILTRATION:
            indicators['data_transferred'] = features.get('outbound_bytes', 0)
            indicators['external_connections'] = features.get('external_conn', 0)
            
        return indicators
        
    def _generate_threat_description(
        self,
        category: ThreatCategory,
        indicators: Dict[str, any]
    ) -> str:
        """Generate human-readable threat description"""
        
        descriptions = {
            ThreatCategory.MALWARE: "Potential malware activity detected based on suspicious process behavior and resource usage patterns.",
            ThreatCategory.INTRUSION: "Intrusion attempt detected with multiple failed authentication attempts from suspicious sources.",
            ThreatCategory.DATA_EXFILTRATION: "Unusual data transfer patterns suggest potential data exfiltration to external destinations.",
            ThreatCategory.DOS: "Denial of service attack detected with abnormally high request rates.",
            ThreatCategory.PRIVILEGE_ESCALATION: "Unauthorized privilege escalation attempt detected.",
            ThreatCategory.LATERAL_MOVEMENT: "Lateral movement detected across network segments.",
            ThreatCategory.RECONNAISSANCE: "Network reconnaissance activity detected.",
            ThreatCategory.UNKNOWN: "Unknown threat pattern detected requiring further investigation."
        }
        
        return descriptions.get(category, "Threat detected.")
        
    def _get_recommended_actions(
        self,
        category: ThreatCategory,
        level: ThreatLevel
    ) -> List[str]:
        """Get recommended remediation actions"""
        
        actions = {
            ThreatCategory.MALWARE: [
                "Isolate affected system from network",
                "Run full antivirus scan",
                "Analyze suspicious processes",
                "Check for persistence mechanisms"
            ],
            ThreatCategory.INTRUSION: [
                "Block source IP addresses",
                "Reset compromised credentials",
                "Review access logs",
                "Enable MFA if not already active"
            ],
            ThreatCategory.DATA_EXFILTRATION: [
                "Block external connections",
                "Review data access logs",
                "Identify compromised accounts",
                "Implement DLP policies"
            ],
            ThreatCategory.DOS: [
                "Enable rate limiting",
                "Block attacking IPs",
                "Scale resources if possible",
                "Contact ISP for upstream filtering"
            ]
        }
        
        base_actions = actions.get(category, ["Investigate further", "Monitor closely"])
        
        if level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            base_actions.insert(0, "IMMEDIATE ACTION REQUIRED")
            base_actions.append("Notify security team")
            
        return base_actions
        
    def get_threat_statistics(self) -> Dict[str, any]:
        """Get threat detection statistics"""
        
        if not self.threat_history:
            return {'total_threats': 0}
            
        stats = {
            'total_threats': len(self.threat_history),
            'by_category': {},
            'by_level': {},
            'avg_confidence': np.mean([t.confidence for t in self.threat_history]),
            'recent_threats': len([
                t for t in self.threat_history
                if (datetime.now() - t.timestamp).seconds < 3600
            ])
        }
        
        # Count by category
        for threat in self.threat_history:
            cat = threat.category.value
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            
            level = threat.level.value
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            
        return stats


if __name__ == "__main__":
    # Example usage
    config = {}
    
    # Initialize threat intelligence
    ti = ThreatIntelligence(config)
    
    # Generate synthetic training data
    np.random.seed(42)
    X_train = np.random.randn(1000, 15)
    y_train = np.random.randint(0, 4, 1000)  # 4 threat categories
    
    feature_names = [
        'cpu_usage', 'memory_usage', 'network_connections',
        'failed_auth', 'process_count', 'outbound_bytes',
        'inbound_bytes', 'unique_ips', 'port_scans',
        'file_modifications', 'registry_changes', 'external_conn',
        'privilege_changes', 'lateral_moves', 'data_access'
    ]
    
    # Train classifier
    ti.train_classifier(X_train, y_train, feature_names)
    
    # Test detection
    test_features = {
        'cpu_usage': 85.0,
        'memory_usage': 75.0,
        'network_connections': 150.0,
        'failed_auth': 10.0,
        'process_count': 50.0,
        'outbound_bytes': 1000000.0,
        'inbound_bytes': 50000.0,
        'unique_ips': 5.0,
        'port_scans': 0.0,
        'file_modifications': 20.0,
        'registry_changes': 5.0,
        'external_conn': 3.0,
        'privilege_changes': 1.0,
        'lateral_moves': 0.0,
        'data_access': 100.0
    }
    
    detection = ti.detect_threat(test_features)
    
    if detection:
        print(f"Threat ID: {detection.threat_id}")
        print(f"Category: {detection.category.value}")
        print(f"Level: {detection.level.value}")
        print(f"Confidence: {detection.confidence:.2f}")
        print(f"Description: {detection.description}")
        print(f"\nRecommended Actions:")
        for action in detection.recommended_actions:
            print(f"  - {action}")
            
    # Get statistics
    stats = ti.get_threat_statistics()
    print(f"\nThreat Statistics: {json.dumps(stats, indent=2)}")
