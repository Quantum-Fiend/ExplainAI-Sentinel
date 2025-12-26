#[cfg(test)]
mod tests {
    use crate::models::{Policy, Condition, Action, EvaluationContext, TrustScore};
    use crate::evaluator::PolicyEvaluator;
    use std::collections::HashMap;

    #[test]
    fn test_policy_evaluation_allow() {
        let mut attributes = HashMap::new();
        attributes.insert("source_ip".to_string(), "10.0.0.5".to_string());
        attributes.insert("trust_level".to_string(), "0.9".to_string());

        let context = EvaluationContext {
            service_id: "service-a".to_string(),
            action: "READ".to_string(),
            resource: "resource-1".to_string(),
            attributes,
            trust_score: TrustScore {
                id: "service-a".to_string(),
                score: 0.9,
                factors: vec![],
                last_updated: 0,
            },
        };

        let policy = Policy {
            id: "p1".to_string(),
            name: "Allow High Trust".to_string(),
            conditions: vec![Condition {
                attribute: "trust_level".to_string(),
                operator: ">".to_string(),
                value: "0.8".to_string(),
            }],
            action: Action::Allow,
            priority: 10,
        };

        let evaluator = PolicyEvaluator::new("HighestPriority".to_string());
        let result = evaluator.evaluate(&context, &vec![policy]);
        
        assert_eq!(result.id, "p1");
        // Check if logic in evaluator.rs maps Correctly
    }
}
