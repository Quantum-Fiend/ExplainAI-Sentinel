"""
Explainable AI Module
Provides interpretable explanations for AI decisions using SHAP, LIME, and custom methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import shap
from lime import lime_tabular
from loguru import logger
import json


@dataclass
class Explanation:
    """Structured explanation for AI decision"""
    decision: str
    confidence: float
    method: str
    feature_importance: Dict[str, float]
    natural_language: str
    visualizations: Optional[Dict[str, str]] = None
    counterfactuals: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None


class ExplainableAI:
    """
    Provides multiple explanation methods for AI/ML model decisions
    Supports SHAP, LIME, and custom rule-based explanations
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.shap_explainer = None
        self.lime_explainer = None
        self.background_data = None
        self.feature_names = None
        
        logger.info("ExplainableAI module initialized")
        
    def initialize_shap(
        self, 
        model: Any, 
        background_data: np.ndarray,
        feature_names: List[str]
    ):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained model with predict method
            background_data: Representative background dataset
            feature_names: Names of features
        """
        try:
            # Use appropriate explainer based on model type
            if hasattr(model, 'predict_proba'):
                self.shap_explainer = shap.KernelExplainer(
                    model.predict_proba,
                    background_data[:self.config.get('background_samples', 100)]
                )
            else:
                self.shap_explainer = shap.KernelExplainer(
                    model.predict,
                    background_data[:self.config.get('background_samples', 100)]
                )
                
            self.background_data = background_data
            self.feature_names = feature_names
            
            logger.info("SHAP explainer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            
    def initialize_lime(
        self,
        training_data: np.ndarray,
        feature_names: List[str],
        class_names: List[str] = None
    ):
        """
        Initialize LIME explainer
        
        Args:
            training_data: Training dataset for LIME
            feature_names: Names of features
            class_names: Names of classes (for classification)
        """
        try:
            self.lime_explainer = lime_tabular.LimeTabularExplainer(
                training_data,
                feature_names=feature_names,
                class_names=class_names or ['normal', 'anomaly'],
                mode='classification',
                discretize_continuous=True
            )
            
            self.feature_names = feature_names
            
            logger.info("LIME explainer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LIME explainer: {e}")
            
    def explain_with_shap(
        self, 
        instance: np.ndarray,
        model: Any = None
    ) -> Explanation:
        """
        Generate SHAP-based explanation
        
        Args:
            instance: Single instance to explain
            model: Optional model override
            
        Returns:
            Explanation object
        """
        if self.shap_explainer is None:
            raise RuntimeError("SHAP explainer not initialized")
            
        try:
            # Calculate SHAP values
            shap_values = self.shap_explainer.shap_values(
                instance.reshape(1, -1),
                nsamples=self.config.get('max_evals', 1000)
            )
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class
                
            # Get feature importance
            feature_importance = {
                name: float(value)
                for name, value in zip(self.feature_names, shap_values[0])
            }
            
            # Sort by absolute importance
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            # Generate natural language explanation
            nl_explanation = self._generate_shap_narrative(
                sorted_features[:5],
                instance
            )
            
            # Calculate confidence (based on magnitude of SHAP values)
            confidence = float(np.abs(shap_values).sum() / len(shap_values[0]))
            
            explanation = Explanation(
                decision="anomaly" if shap_values.sum() > 0 else "normal",
                confidence=confidence,
                method="SHAP",
                feature_importance=dict(sorted_features[:10]),
                natural_language=nl_explanation,
                metadata={
                    'base_value': float(self.shap_explainer.expected_value),
                    'prediction_value': float(shap_values.sum() + self.shap_explainer.expected_value)
                }
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            raise
            
    def explain_with_lime(
        self,
        instance: np.ndarray,
        model: Any,
        num_features: int = None
    ) -> Explanation:
        """
        Generate LIME-based explanation
        
        Args:
            instance: Single instance to explain
            model: Model with predict_proba method
            num_features: Number of top features to include
            
        Returns:
            Explanation object
        """
        if self.lime_explainer is None:
            raise RuntimeError("LIME explainer not initialized")
            
        try:
            num_features = num_features or self.config.get('num_features', 10)
            
            # Generate explanation
            exp = self.lime_explainer.explain_instance(
                instance,
                model.predict_proba,
                num_features=num_features,
                num_samples=self.config.get('num_samples', 5000)
            )
            
            # Extract feature importance
            feature_importance = dict(exp.as_list())
            
            # Get prediction
            prediction = model.predict_proba(instance.reshape(1, -1))[0]
            predicted_class = int(np.argmax(prediction))
            confidence = float(prediction[predicted_class])
            
            # Generate natural language explanation
            nl_explanation = self._generate_lime_narrative(
                feature_importance,
                predicted_class,
                confidence
            )
            
            explanation = Explanation(
                decision="anomaly" if predicted_class == 1 else "normal",
                confidence=confidence,
                method="LIME",
                feature_importance=feature_importance,
                natural_language=nl_explanation,
                metadata={
                    'prediction_probabilities': prediction.tolist(),
                    'local_prediction': exp.local_pred[0]
                }
            )
            
            return explanation
            
        except Exception as e:
            logger.error(f"LIME explanation failed: {e}")
            raise
            
    def explain_with_rules(
        self,
        instance: np.ndarray,
        decision: str,
        confidence: float,
        feature_values: Dict[str, float]
    ) -> Explanation:
        """
        Generate rule-based explanation
        
        Args:
            instance: Input instance
            decision: Model decision
            confidence: Decision confidence
            feature_values: Named feature values
            
        Returns:
            Explanation object
        """
        # Analyze which features triggered the decision
        triggered_rules = []
        feature_importance = {}
        
        for feature_name, value in feature_values.items():
            # Define thresholds (in production, these would be learned)
            if abs(value) > 2.0:  # Example threshold
                importance = abs(value) / 10.0  # Normalize
                feature_importance[feature_name] = importance
                triggered_rules.append({
                    'feature': feature_name,
                    'value': value,
                    'threshold': 2.0,
                    'condition': 'exceeded' if value > 2.0 else 'below'
                })
                
        # Generate narrative
        nl_explanation = self._generate_rule_narrative(
            triggered_rules,
            decision,
            confidence
        )
        
        explanation = Explanation(
            decision=decision,
            confidence=confidence,
            method="Rule-Based",
            feature_importance=feature_importance,
            natural_language=nl_explanation,
            metadata={
                'triggered_rules': triggered_rules,
                'num_rules_triggered': len(triggered_rules)
            }
        )
        
        return explanation
        
    def generate_counterfactuals(
        self,
        instance: np.ndarray,
        model: Any,
        desired_outcome: int,
        num_counterfactuals: int = 3
    ) -> List[Dict]:
        """
        Generate counterfactual explanations
        
        Args:
            instance: Original instance
            model: Trained model
            desired_outcome: Desired prediction
            num_counterfactuals: Number of counterfactuals to generate
            
        Returns:
            List of counterfactual instances with changes
        """
        counterfactuals = []
        
        try:
            # Simple gradient-based counterfactual generation
            current_instance = instance.copy()
            
            for _ in range(num_counterfactuals):
                # Perturb features slightly
                perturbation = np.random.randn(len(instance)) * 0.1
                candidate = current_instance + perturbation
                
                # Check if it produces desired outcome
                prediction = model.predict(candidate.reshape(1, -1))[0]
                
                if prediction == desired_outcome:
                    changes = {
                        self.feature_names[i]: {
                            'original': float(instance[i]),
                            'counterfactual': float(candidate[i]),
                            'change': float(candidate[i] - instance[i])
                        }
                        for i in range(len(instance))
                        if abs(candidate[i] - instance[i]) > 0.01
                    }
                    
                    counterfactuals.append({
                        'instance': candidate.tolist(),
                        'changes': changes,
                        'num_changes': len(changes)
                    })
                    
        except Exception as e:
            logger.warning(f"Counterfactual generation failed: {e}")
            
        return counterfactuals
        
    def _generate_shap_narrative(
        self,
        top_features: List[tuple],
        instance: np.ndarray
    ) -> str:
        """Generate natural language explanation from SHAP values"""
        
        if not top_features:
            return "No significant features contributed to this decision."
            
        narrative_parts = ["The decision was primarily influenced by:"]
        
        for feature_name, importance in top_features:
            direction = "increased" if importance > 0 else "decreased"
            narrative_parts.append(
                f"- {feature_name} {direction} the anomaly score by {abs(importance):.3f}"
            )
            
        return "\n".join(narrative_parts)
        
    def _generate_lime_narrative(
        self,
        feature_importance: Dict[str, float],
        predicted_class: int,
        confidence: float
    ) -> str:
        """Generate natural language explanation from LIME"""
        
        class_name = "anomaly" if predicted_class == 1 else "normal"
        
        narrative = f"The model predicts this instance as {class_name} with {confidence*100:.1f}% confidence.\n\n"
        narrative += "Key contributing factors:\n"
        
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        for feature, importance in sorted_features:
            direction = "supports" if importance > 0 else "contradicts"
            narrative += f"- {feature} {direction} this classification (weight: {importance:.3f})\n"
            
        return narrative
        
    def _generate_rule_narrative(
        self,
        triggered_rules: List[Dict],
        decision: str,
        confidence: float
    ) -> str:
        """Generate natural language explanation from rules"""
        
        if not triggered_rules:
            return f"Decision: {decision} (confidence: {confidence:.2f}). No specific rules triggered."
            
        narrative = f"Decision: {decision} (confidence: {confidence:.2f})\n\n"
        narrative += f"{len(triggered_rules)} rule(s) triggered:\n"
        
        for rule in triggered_rules:
            narrative += f"- {rule['feature']} = {rule['value']:.3f} "
            narrative += f"({rule['condition']} threshold of {rule['threshold']})\n"
            
        return narrative
        
    def to_json(self, explanation: Explanation) -> str:
        """Convert explanation to JSON format"""
        return json.dumps({
            'decision': explanation.decision,
            'confidence': explanation.confidence,
            'method': explanation.method,
            'feature_importance': explanation.feature_importance,
            'natural_language': explanation.natural_language,
            'counterfactuals': explanation.counterfactuals,
            'metadata': explanation.metadata
        }, indent=2)


if __name__ == "__main__":
    # Example usage
    from sklearn.ensemble import RandomForestClassifier
    
    # Generate synthetic data
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)
    y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)
    
    # Train a simple model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Initialize explainer
    config = {
        'background_samples': 100,
        'max_evals': 1000,
        'num_features': 5,
        'num_samples': 5000
    }
    
    explainer = ExplainableAI(config)
    
    # Initialize SHAP
    feature_names = [f"feature_{i}" for i in range(10)]
    explainer.initialize_shap(model, X_train, feature_names)
    
    # Initialize LIME
    explainer.initialize_lime(X_train, feature_names)
    
    # Test instance
    test_instance = np.random.randn(10)
    
    # Get SHAP explanation
    shap_exp = explainer.explain_with_shap(test_instance, model)
    print("=== SHAP Explanation ===")
    print(shap_exp.natural_language)
    print(f"\nTop features: {list(shap_exp.feature_importance.keys())[:5]}")
    
    # Get LIME explanation
    lime_exp = explainer.explain_with_lime(test_instance, model)
    print("\n=== LIME Explanation ===")
    print(lime_exp.natural_language)
