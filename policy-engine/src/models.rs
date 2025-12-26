use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use chrono::{DateTime, Utc};

/// Policy priority levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Priority {
    Critical = 4,
    High = 3,
    Medium = 2,
    Low = 1,
}

/// Policy enforcement actions
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Action {
    Allow,
    Deny,
    Isolate,
    Throttle { rate: u32 },
    Redirect { target: String },
    Alert { severity: String },
    Log { level: String },
    Custom { action: String, params: HashMap<String, String> },
}

/// Condition operators
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Operator {
    Equals,
    NotEquals,
    GreaterThan,
    LessThan,
    GreaterThanOrEqual,
    LessThanOrEqual,
    Contains,
    NotContains,
    Matches,
    In,
}

/// Policy condition
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Condition {
    pub field: String,
    pub operator: Operator,
    pub value: serde_json::Value,
}

/// Logical expression for combining conditions
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Expression {
    Condition(Condition),
    And(Vec<Expression>),
    Or(Vec<Expression>),
    Not(Box<Expression>),
}

/// Policy rule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Policy {
    pub id: String,
    pub name: String,
    pub description: String,
    pub priority: Priority,
    pub enabled: bool,
    pub conditions: Expression,
    pub actions: Vec<Action>,
    pub metadata: HashMap<String, String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub version: u32,
}

/// Policy evaluation context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationContext {
    pub request_id: String,
    pub timestamp: DateTime<Utc>,
    pub attributes: HashMap<String, serde_json::Value>,
    pub metadata: HashMap<String, String>,
}

/// Policy evaluation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationResult {
    pub policy_id: String,
    pub matched: bool,
    pub actions: Vec<Action>,
    pub reason: String,
    pub confidence: f64,
    pub evaluation_time_ms: u64,
}

/// Policy conflict resolution strategy
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum ConflictResolution {
    FirstMatch,
    HighestPriority,
    MostSpecific,
    DenyOverrides,
    AllowOverrides,
}

/// Trust score for zero-trust enforcement
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrustScore {
    pub entity_id: String,
    pub score: f64,
    pub factors: HashMap<String, f64>,
    pub last_updated: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
}

/// Policy violation record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Violation {
    pub id: String,
    pub policy_id: String,
    pub context: EvaluationContext,
    pub action_taken: Action,
    pub timestamp: DateTime<Utc>,
    pub severity: String,
}

impl Policy {
    pub fn new(id: String, name: String, conditions: Expression, actions: Vec<Action>) -> Self {
        let now = Utc::now();
        Self {
            id,
            name,
            description: String::new(),
            priority: Priority::Medium,
            enabled: true,
            conditions,
            actions,
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
            version: 1,
        }
    }
}

impl EvaluationContext {
    pub fn new(request_id: String) -> Self {
        Self {
            request_id,
            timestamp: Utc::now(),
            attributes: HashMap::new(),
            metadata: HashMap::new(),
        }
    }

    pub fn with_attribute(mut self, key: String, value: serde_json::Value) -> Self {
        self.attributes.insert(key, value);
        self
    }

    pub fn get_attribute(&self, key: &str) -> Option<&serde_json::Value> {
        self.attributes.get(key)
    }
}

impl TrustScore {
    pub fn new(entity_id: String, score: f64) -> Self {
        Self {
            entity_id,
            score: score.clamp(0.0, 1.0),
            factors: HashMap::new(),
            last_updated: Utc::now(),
            expires_at: None,
        }
    }

    pub fn is_trusted(&self, threshold: f64) -> bool {
        self.score >= threshold
    }

    pub fn is_expired(&self) -> bool {
        self.expires_at.map_or(false, |exp| Utc::now() > exp)
    }
}
