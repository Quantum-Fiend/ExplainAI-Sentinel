use crate::models::*;
use crate::evaluator::{PolicyEvaluator, TrustScoreCalculator};
use anyhow::Result;
use dashmap::DashMap;
use std::sync::Arc;
use tracing::{info, warn};
use uuid::Uuid;

/// Main policy engine
pub struct PolicyEngine {
    policies: Arc<DashMap<String, Policy>>,
    trust_scores: Arc<DashMap<String, TrustScore>>,
    violations: Arc<DashMap<String, Violation>>,
    evaluator: PolicyEvaluator,
    trust_calculator: TrustScoreCalculator,
    trust_threshold: f64,
}

impl PolicyEngine {
    pub fn new(conflict_resolution: ConflictResolution, trust_threshold: f64) -> Self {
        Self {
            policies: Arc::new(DashMap::new()),
            trust_scores: Arc::new(DashMap::new()),
            violations: Arc::new(DashMap::new()),
            evaluator: PolicyEvaluator::new(conflict_resolution),
            trust_calculator: TrustScoreCalculator::new(),
            trust_threshold,
        }
    }

    /// Add a new policy
    pub fn add_policy(&self, policy: Policy) -> Result<()> {
        info!(
            policy_id = %policy.id,
            policy_name = %policy.name,
            "Adding policy"
        );
        
        self.policies.insert(policy.id.clone(), policy);
        Ok(())
    }

    /// Remove a policy
    pub fn remove_policy(&self, policy_id: &str) -> Result<()> {
        self.policies.remove(policy_id)
            .ok_or_else(|| anyhow::anyhow!("Policy not found: {}", policy_id))?;
        
        info!(policy_id = %policy_id, "Policy removed");
        Ok(())
    }

    /// Get a policy by ID
    pub fn get_policy(&self, policy_id: &str) -> Option<Policy> {
        self.policies.get(policy_id).map(|p| p.clone())
    }

    /// List all policies
    pub fn list_policies(&self) -> Vec<Policy> {
        self.policies.iter().map(|entry| entry.value().clone()).collect()
    }

    /// Update a policy
    pub fn update_policy(&self, policy: Policy) -> Result<()> {
        let mut existing = self.policies.get_mut(&policy.id)
            .ok_or_else(|| anyhow::anyhow!("Policy not found: {}", policy.id))?;
        
        let mut updated = policy;
        updated.version = existing.version + 1;
        updated.updated_at = chrono::Utc::now();
        
        *existing = updated;
        
        info!(policy_id = %existing.id, version = existing.version, "Policy updated");
        Ok(())
    }

    /// Enable/disable a policy
    pub fn set_policy_enabled(&self, policy_id: &str, enabled: bool) -> Result<()> {
        let mut policy = self.policies.get_mut(policy_id)
            .ok_or_else(|| anyhow::anyhow!("Policy not found: {}", policy_id))?;
        
        policy.enabled = enabled;
        policy.updated_at = chrono::Utc::now();
        
        info!(
            policy_id = %policy_id,
            enabled = enabled,
            "Policy enabled status changed"
        );
        
        Ok(())
    }

    /// Evaluate policies against a context
    pub fn evaluate(&self, context: &EvaluationContext) -> Result<Vec<EvaluationResult>> {
        let policies: Vec<Policy> = self.policies.iter()
            .map(|entry| entry.value().clone())
            .collect();

        let results = self.evaluator.evaluate_policies(&policies, context)?;
        
        // Record violations for matched deny actions
        for result in &results {
            if result.matched {
                if let Some(policy) = self.get_policy(&result.policy_id) {
                    if result.actions.iter().any(|a| matches!(a, Action::Deny | Action::Isolate)) {
                        self.record_violation(&policy, context, &result.actions[0]);
                    }
                }
            }
        }

        Ok(results)
    }

    /// Evaluate and resolve conflicts
    pub fn evaluate_and_resolve(&self, context: &EvaluationContext) -> Result<Option<EvaluationResult>> {
        let results = self.evaluate(context)?;
        Ok(self.evaluator.resolve_conflicts(results))
    }

    /// Check if entity is trusted
    pub fn is_trusted(&self, entity_id: &str) -> bool {
        self.trust_scores.get(entity_id)
            .map(|score| score.is_trusted(self.trust_threshold) && !score.is_expired())
            .unwrap_or(false)
    }

    /// Get trust score for an entity
    pub fn get_trust_score(&self, entity_id: &str) -> Option<TrustScore> {
        self.trust_scores.get(entity_id).map(|s| s.clone())
    }

    /// Update trust score
    pub fn update_trust_score(
        &self,
        entity_id: &str,
        factors: &std::collections::HashMap<String, f64>,
    ) -> TrustScore {
        let score = self.trust_calculator.calculate_trust_score(entity_id, factors);
        self.trust_scores.insert(entity_id.to_string(), score.clone());
        
        info!(
            entity_id = %entity_id,
            score = score.score,
            "Trust score updated"
        );
        
        score
    }

    /// Adjust trust score based on event
    pub fn adjust_trust_score(&self, entity_id: &str, event: &str, impact: f64) {
        if let Some(mut entry) = self.trust_scores.get_mut(entity_id) {
            let updated = self.trust_calculator.update_trust_score(
                entry.clone(),
                event,
                impact,
            );
            *entry = updated;
            
            info!(
                entity_id = %entity_id,
                event = %event,
                impact = impact,
                new_score = entry.score,
                "Trust score adjusted"
            );
        }
    }

    /// Record a policy violation
    fn record_violation(
        &self,
        policy: &Policy,
        context: &EvaluationContext,
        action: &Action,
    ) {
        let violation = Violation {
            id: Uuid::new_v4().to_string(),
            policy_id: policy.id.clone(),
            context: context.clone(),
            action_taken: action.clone(),
            timestamp: chrono::Utc::now(),
            severity: match policy.priority {
                Priority::Critical => "critical".to_string(),
                Priority::High => "high".to_string(),
                Priority::Medium => "medium".to_string(),
                Priority::Low => "low".to_string(),
            },
        };

        warn!(
            violation_id = %violation.id,
            policy_id = %policy.id,
            severity = %violation.severity,
            "Policy violation recorded"
        );

        self.violations.insert(violation.id.clone(), violation);
    }

    /// Get violations
    pub fn get_violations(&self, limit: Option<usize>) -> Vec<Violation> {
        let mut violations: Vec<Violation> = self.violations.iter()
            .map(|entry| entry.value().clone())
            .collect();
        
        violations.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
        
        if let Some(limit) = limit {
            violations.truncate(limit);
        }
        
        violations
    }

    /// Get violations for a specific policy
    pub fn get_violations_for_policy(&self, policy_id: &str) -> Vec<Violation> {
        self.violations.iter()
            .filter(|entry| entry.value().policy_id == policy_id)
            .map(|entry| entry.value().clone())
            .collect()
    }

    /// Clear old violations
    pub fn clear_old_violations(&self, older_than_hours: i64) {
        let cutoff = chrono::Utc::now() - chrono::Duration::hours(older_than_hours);
        
        self.violations.retain(|_, violation| violation.timestamp > cutoff);
        
        info!(
            cutoff_hours = older_than_hours,
            "Old violations cleared"
        );
    }

    /// Get engine statistics
    pub fn get_statistics(&self) -> EngineStatistics {
        let total_policies = self.policies.len();
        let enabled_policies = self.policies.iter()
            .filter(|entry| entry.value().enabled)
            .count();
        
        let total_violations = self.violations.len();
        let total_entities = self.trust_scores.len();
        
        let trusted_entities = self.trust_scores.iter()
            .filter(|entry| entry.value().is_trusted(self.trust_threshold))
            .count();

        EngineStatistics {
            total_policies,
            enabled_policies,
            total_violations,
            total_entities,
            trusted_entities,
            trust_threshold: self.trust_threshold,
        }
    }
}

/// Engine statistics
#[derive(Debug, Clone, serde::Serialize)]
pub struct EngineStatistics {
    pub total_policies: usize,
    pub enabled_policies: usize,
    pub total_violations: usize,
    pub total_entities: usize,
    pub trusted_entities: usize,
    pub trust_threshold: f64,
}

impl Default for PolicyEngine {
    fn default() -> Self {
        Self::new(ConflictResolution::HighestPriority, 0.7)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_add_and_get_policy() {
        let engine = PolicyEngine::default();
        
        let policy = Policy::new(
            "policy-1".to_string(),
            "Test Policy".to_string(),
            Expression::Condition(Condition {
                field: "user".to_string(),
                operator: Operator::Equals,
                value: json!("admin"),
            }),
            vec![Action::Allow],
        );

        engine.add_policy(policy.clone()).unwrap();
        
        let retrieved = engine.get_policy("policy-1").unwrap();
        assert_eq!(retrieved.id, policy.id);
        assert_eq!(retrieved.name, policy.name);
    }

    #[test]
    fn test_trust_score_management() {
        let engine = PolicyEngine::default();
        
        let mut factors = std::collections::HashMap::new();
        factors.insert("authentication_success".to_string(), 1.0);
        
        let score = engine.update_trust_score("user-123", &factors);
        assert!(score.score > 0.0);
        
        let retrieved = engine.get_trust_score("user-123").unwrap();
        assert_eq!(retrieved.entity_id, "user-123");
    }
}
