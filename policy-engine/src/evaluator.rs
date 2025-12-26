use crate::models::*;
use anyhow::{Result, anyhow};
use std::time::Instant;
use tracing::{info, debug, warn};

/// Policy evaluator engine
pub struct PolicyEvaluator {
    conflict_resolution: ConflictResolution,
}

impl PolicyEvaluator {
    pub fn new(conflict_resolution: ConflictResolution) -> Self {
        Self {
            conflict_resolution,
        }
    }

    /// Evaluate a single policy against a context
    pub fn evaluate_policy(
        &self,
        policy: &Policy,
        context: &EvaluationContext,
    ) -> Result<EvaluationResult> {
        let start = Instant::now();

        if !policy.enabled {
            return Ok(EvaluationResult {
                policy_id: policy.id.clone(),
                matched: false,
                actions: vec![],
                reason: "Policy is disabled".to_string(),
                confidence: 0.0,
                evaluation_time_ms: start.elapsed().as_millis() as u64,
            });
        }

        let matched = self.evaluate_expression(&policy.conditions, context)?;
        let evaluation_time = start.elapsed().as_millis() as u64;

        let result = EvaluationResult {
            policy_id: policy.id.clone(),
            matched,
            actions: if matched { policy.actions.clone() } else { vec![] },
            reason: if matched {
                format!("Policy '{}' conditions satisfied", policy.name)
            } else {
                "Conditions not satisfied".to_string()
            },
            confidence: if matched { 1.0 } else { 0.0 },
            evaluation_time_ms: evaluation_time,
        };

        if matched {
            info!(
                policy_id = %policy.id,
                policy_name = %policy.name,
                evaluation_time_ms = evaluation_time,
                "Policy matched"
            );
        }

        Ok(result)
    }

    /// Evaluate multiple policies and resolve conflicts
    pub fn evaluate_policies(
        &self,
        policies: &[Policy],
        context: &EvaluationContext,
    ) -> Result<Vec<EvaluationResult>> {
        let mut results: Vec<EvaluationResult> = policies
            .iter()
            .filter_map(|policy| self.evaluate_policy(policy, context).ok())
            .collect();

        // Sort by priority for conflict resolution
        results.sort_by(|a, b| {
            let policy_a = policies.iter().find(|p| p.id == a.policy_id);
            let policy_b = policies.iter().find(|p| p.id == b.policy_id);
            
            match (policy_a, policy_b) {
                (Some(pa), Some(pb)) => pb.priority.cmp(&pa.priority),
                _ => std::cmp::Ordering::Equal,
            }
        });

        Ok(results)
    }

    /// Resolve conflicting policy results
    pub fn resolve_conflicts(
        &self,
        results: Vec<EvaluationResult>,
    ) -> Option<EvaluationResult> {
        let matched_results: Vec<_> = results.into_iter()
            .filter(|r| r.matched)
            .collect();

        if matched_results.is_empty() {
            return None;
        }

        match self.conflict_resolution {
            ConflictResolution::FirstMatch => {
                matched_results.into_iter().next()
            }
            ConflictResolution::HighestPriority => {
                // Already sorted by priority
                matched_results.into_iter().next()
            }
            ConflictResolution::DenyOverrides => {
                // Find first deny action
                matched_results.into_iter().find(|r| {
                    r.actions.iter().any(|a| matches!(a, Action::Deny))
                }).or_else(|| matched_results.into_iter().next())
            }
            ConflictResolution::AllowOverrides => {
                // Find first allow action
                matched_results.into_iter().find(|r| {
                    r.actions.iter().any(|a| matches!(a, Action::Allow))
                }).or_else(|| matched_results.into_iter().next())
            }
            ConflictResolution::MostSpecific => {
                // Most specific = most conditions
                matched_results.into_iter().max_by_key(|r| {
                    r.reason.len() // Simplified - in production, count actual conditions
                })
            }
        }
    }

    /// Evaluate an expression tree
    fn evaluate_expression(
        &self,
        expr: &Expression,
        context: &EvaluationContext,
    ) -> Result<bool> {
        match expr {
            Expression::Condition(cond) => self.evaluate_condition(cond, context),
            Expression::And(exprs) => {
                for expr in exprs {
                    if !self.evaluate_expression(expr, context)? {
                        return Ok(false);
                    }
                }
                Ok(true)
            }
            Expression::Or(exprs) => {
                for expr in exprs {
                    if self.evaluate_expression(expr, context)? {
                        return Ok(true);
                    }
                }
                Ok(false)
            }
            Expression::Not(expr) => {
                Ok(!self.evaluate_expression(expr, context)?)
            }
        }
    }

    /// Evaluate a single condition
    fn evaluate_condition(
        &self,
        condition: &Condition,
        context: &EvaluationContext,
    ) -> Result<bool> {
        let value = context.get_attribute(&condition.field)
            .ok_or_else(|| anyhow!("Attribute '{}' not found", condition.field))?;

        let result = match &condition.operator {
            Operator::Equals => value == &condition.value,
            Operator::NotEquals => value != &condition.value,
            Operator::GreaterThan => {
                self.compare_numeric(value, &condition.value, |a, b| a > b)?
            }
            Operator::LessThan => {
                self.compare_numeric(value, &condition.value, |a, b| a < b)?
            }
            Operator::GreaterThanOrEqual => {
                self.compare_numeric(value, &condition.value, |a, b| a >= b)?
            }
            Operator::LessThanOrEqual => {
                self.compare_numeric(value, &condition.value, |a, b| a <= b)?
            }
            Operator::Contains => {
                if let (Some(haystack), Some(needle)) = (value.as_str(), condition.value.as_str()) {
                    haystack.contains(needle)
                } else {
                    false
                }
            }
            Operator::NotContains => {
                if let (Some(haystack), Some(needle)) = (value.as_str(), condition.value.as_str()) {
                    !haystack.contains(needle)
                } else {
                    false
                }
            }
            Operator::Matches => {
                // Simplified regex matching
                if let (Some(text), Some(pattern)) = (value.as_str(), condition.value.as_str()) {
                    text.contains(pattern) // In production, use proper regex
                } else {
                    false
                }
            }
            Operator::In => {
                if let Some(array) = condition.value.as_array() {
                    array.contains(value)
                } else {
                    false
                }
            }
        };

        debug!(
            field = %condition.field,
            operator = ?condition.operator,
            result = result,
            "Condition evaluated"
        );

        Ok(result)
    }

    /// Compare numeric values
    fn compare_numeric<F>(
        &self,
        a: &serde_json::Value,
        b: &serde_json::Value,
        compare: F,
    ) -> Result<bool>
    where
        F: Fn(f64, f64) -> bool,
    {
        let a_num = a.as_f64()
            .ok_or_else(|| anyhow!("Cannot convert {:?} to number", a))?;
        let b_num = b.as_f64()
            .ok_or_else(|| anyhow!("Cannot convert {:?} to number", b))?;
        
        Ok(compare(a_num, b_num))
    }
}

/// Trust score calculator
pub struct TrustScoreCalculator {
    base_score: f64,
    decay_rate: f64,
}

impl TrustScoreCalculator {
    pub fn new() -> Self {
        Self {
            base_score: 0.5,
            decay_rate: 0.1,
        }
    }

    /// Calculate trust score based on various factors
    pub fn calculate_trust_score(
        &self,
        entity_id: &str,
        factors: &std::collections::HashMap<String, f64>,
    ) -> TrustScore {
        let mut score = self.base_score;
        let mut weighted_factors = std::collections::HashMap::new();

        // Weight different factors
        for (factor, value) in factors {
            let weight = match factor.as_str() {
                "authentication_success" => 0.3,
                "recent_violations" => -0.4,
                "time_since_last_activity" => -0.1,
                "reputation" => 0.3,
                "behavioral_anomaly" => -0.5,
                _ => 0.1,
            };

            let weighted_value = value * weight;
            score += weighted_value;
            weighted_factors.insert(factor.clone(), weighted_value);
        }

        // Clamp score between 0 and 1
        score = score.clamp(0.0, 1.0);

        TrustScore {
            entity_id: entity_id.to_string(),
            score,
            factors: weighted_factors,
            last_updated: chrono::Utc::now(),
            expires_at: Some(chrono::Utc::now() + chrono::Duration::hours(1)),
        }
    }

    /// Update trust score based on new event
    pub fn update_trust_score(
        &self,
        mut trust_score: TrustScore,
        event: &str,
        impact: f64,
    ) -> TrustScore {
        trust_score.score += impact;
        trust_score.score = trust_score.score.clamp(0.0, 1.0);
        trust_score.factors.insert(event.to_string(), impact);
        trust_score.last_updated = chrono::Utc::now();
        trust_score
    }
}

impl Default for TrustScoreCalculator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_simple_condition_evaluation() {
        let evaluator = PolicyEvaluator::new(ConflictResolution::FirstMatch);
        
        let condition = Condition {
            field: "cpu_usage".to_string(),
            operator: Operator::GreaterThan,
            value: json!(80.0),
        };

        let context = EvaluationContext::new("test-1".to_string())
            .with_attribute("cpu_usage".to_string(), json!(85.0));

        let result = evaluator.evaluate_condition(&condition, &context).unwrap();
        assert!(result);
    }

    #[test]
    fn test_trust_score_calculation() {
        let calculator = TrustScoreCalculator::new();
        
        let mut factors = std::collections::HashMap::new();
        factors.insert("authentication_success".to_string(), 1.0);
        factors.insert("recent_violations".to_string(), 0.0);
        
        let trust_score = calculator.calculate_trust_score("user-123", &factors);
        
        assert!(trust_score.score > 0.5);
        assert!(trust_score.score <= 1.0);
    }
}
