# Policy Engine

High-performance, memory-safe policy enforcement engine built with Rust.

## Features

- **Policy DSL**: Flexible policy definition with conditions and actions
- **Constraint Solving**: Advanced policy evaluation with multiple operators
- **Zero-Trust Enforcement**: Real-time trust scoring for entities
- **Conflict Resolution**: Multiple strategies (FirstMatch, HighestPriority, DenyOverrides, etc.)
- **Violation Tracking**: Automatic recording and querying of policy violations
- **REST API**: Complete API for policy management and evaluation
- **High Performance**: Memory-safe, concurrent operations with DashMap
- **Metrics**: Built-in Prometheus metrics support

## Architecture

```
policy-engine/
├── src/
│   ├── models.rs      # Data models (Policy, Action, Condition, TrustScore)
│   ├── evaluator.rs   # Policy evaluation logic
│   ├── engine.rs      # Main policy engine
│   ├── api.rs         # REST API handlers
│   ├── lib.rs         # Library exports
│   └── main.rs        # Server entry point
└── Cargo.toml         # Dependencies
```

## Installation

### Prerequisites

- Rust 1.70+
- Cargo

### Build

```bash
cargo build --release
```

### Run

```bash
cargo run --release
```

The API will be available at `http://localhost:8003`

## API Documentation

### Policy Management

#### Create Policy

```bash
curl -X POST http://localhost:8003/policies \
  -H "Content-Type: application/json" \
  -d '{
    "id": "policy-1",
    "name": "High CPU Alert",
    "description": "Alert on high CPU usage",
    "priority": "High",
    "enabled": true,
    "conditions": {
      "Condition": {
        "field": "cpu_usage",
        "operator": "GreaterThan",
        "value": 80.0
      }
    },
    "actions": [
      {
        "Alert": {
          "severity": "high"
        }
      }
    ],
    "metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "version": 1
  }'
```

#### List Policies

```bash
curl http://localhost:8003/policies?enabled=true&limit=10
```

#### Get Policy

```bash
curl http://localhost:8003/policies/policy-1
```

#### Update Policy

```bash
curl -X PUT http://localhost:8003/policies/policy-1 \
  -H "Content-Type: application/json" \
  -d '{...}'
```

#### Delete Policy

```bash
curl -X DELETE http://localhost:8003/policies/policy-1
```

#### Enable/Disable Policy

```bash
curl -X PUT http://localhost:8003/policies/policy-1/enable
curl -X PUT http://localhost:8003/policies/policy-1/disable
```

### Policy Evaluation

#### Evaluate Policies

```bash
curl -X POST http://localhost:8003/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req-123",
    "timestamp": "2024-01-01T00:00:00Z",
    "attributes": {
      "cpu_usage": 85.0,
      "user": "admin",
      "service": "auth-service"
    },
    "metadata": {}
  }'
```

Response:
```json
{
  "success": true,
  "message": "Evaluation completed",
  "data": {
    "policy_id": "policy-1",
    "matched": true,
    "actions": [
      {
        "Alert": {
          "severity": "high"
        }
      }
    ],
    "reason": "Policy 'High CPU Alert' conditions satisfied",
    "confidence": 1.0,
    "evaluation_time_ms": 2
  }
}
```

### Trust Scoring

#### Get Trust Score

```bash
curl http://localhost:8003/trust/user-123
```

#### Update Trust Score

```bash
curl -X PUT http://localhost:8003/trust/user-123 \
  -H "Content-Type: application/json" \
  -d '{
    "factors": {
      "authentication_success": 1.0,
      "recent_violations": 0.0,
      "reputation": 0.8
    }
  }'
```

#### Adjust Trust Score

```bash
curl -X POST http://localhost:8003/trust/user-123/adjust \
  -H "Content-Type: application/json" \
  -d '{
    "event": "failed_login",
    "impact": -0.2
  }'
```

### Violations

#### List Violations

```bash
curl http://localhost:8003/violations?limit=50
```

#### Get Policy Violations

```bash
curl http://localhost:8003/violations/policy/policy-1
```

### Statistics

#### Get Engine Statistics

```bash
curl http://localhost:8003/statistics
```

Response:
```json
{
  "success": true,
  "message": "Statistics retrieved",
  "data": {
    "total_policies": 10,
    "enabled_policies": 8,
    "total_violations": 25,
    "total_entities": 100,
    "trusted_entities": 85,
    "trust_threshold": 0.7
  }
}
```

## Policy DSL

### Conditions

Supported operators:
- `Equals`, `NotEquals`
- `GreaterThan`, `LessThan`, `GreaterThanOrEqual`, `LessThanOrEqual`
- `Contains`, `NotContains`
- `Matches` (pattern matching)
- `In` (array membership)

### Logical Expressions

Combine conditions with:
- `And`: All conditions must be true
- `Or`: At least one condition must be true
- `Not`: Negates the expression

Example:
```json
{
  "And": [
    {
      "Condition": {
        "field": "cpu_usage",
        "operator": "GreaterThan",
        "value": 80.0
      }
    },
    {
      "Condition": {
        "field": "user",
        "operator": "NotEquals",
        "value": "admin"
      }
    }
  ]
}
```

### Actions

Available actions:
- `Allow`: Permit the request
- `Deny`: Block the request
- `Isolate`: Quarantine the entity
- `Throttle { rate }`: Rate limit
- `Redirect { target }`: Redirect to another service
- `Alert { severity }`: Generate alert
- `Log { level }`: Log the event
- `Custom { action, params }`: Custom action

## Conflict Resolution

When multiple policies match, conflicts are resolved using:

- **FirstMatch**: Use the first matching policy
- **HighestPriority**: Use the policy with highest priority
- **MostSpecific**: Use the policy with most conditions
- **DenyOverrides**: Deny actions take precedence
- **AllowOverrides**: Allow actions take precedence

## Trust Scoring

Trust scores are calculated based on weighted factors:

| Factor | Weight |
|--------|--------|
| authentication_success | +0.3 |
| recent_violations | -0.4 |
| time_since_last_activity | -0.1 |
| reputation | +0.3 |
| behavioral_anomaly | -0.5 |

Trust scores range from 0.0 (untrusted) to 1.0 (fully trusted).

## Usage Example

```rust
use policy_engine::{PolicyEngine, Policy, Expression, Condition, Operator, Action, Priority, ConflictResolution, EvaluationContext};
use serde_json::json;

#[tokio::main]
async fn main() {
    // Create engine
    let engine = PolicyEngine::new(ConflictResolution::HighestPriority, 0.7);
    
    // Define policy
    let policy = Policy {
        id: "policy-1".to_string(),
        name: "High CPU Alert".to_string(),
        description: "Alert on high CPU".to_string(),
        priority: Priority::High,
        enabled: true,
        conditions: Expression::Condition(Condition {
            field: "cpu_usage".to_string(),
            operator: Operator::GreaterThan,
            value: json!(80.0),
        }),
        actions: vec![Action::Alert { severity: "high".to_string() }],
        metadata: Default::default(),
        created_at: chrono::Utc::now(),
        updated_at: chrono::Utc::now(),
        version: 1,
    };
    
    // Add policy
    engine.add_policy(policy).unwrap();
    
    // Create evaluation context
    let context = EvaluationContext::new("req-123".to_string())
        .with_attribute("cpu_usage".to_string(), json!(85.0));
    
    // Evaluate
    let result = engine.evaluate_and_resolve(&context).unwrap();
    
    if let Some(result) = result {
        println!("Policy matched: {}", result.policy_id);
        println!("Actions: {:?}", result.actions);
    }
}
```

## Performance

- **Evaluation Latency**: <1ms for simple policies
- **Throughput**: 100K+ evaluations/second
- **Memory**: Efficient concurrent data structures (DashMap)
- **Thread-Safe**: Lock-free operations where possible

## Configuration

Set environment variables:

```bash
export HOST=0.0.0.0
export PORT=8003
export RUST_LOG=policy_engine=info
```

## Testing

```bash
cargo test
```

## Benchmarks

```bash
cargo bench
```

## License

MIT License
