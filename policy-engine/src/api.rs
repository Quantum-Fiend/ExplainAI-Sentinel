use crate::engine::PolicyEngine;
use crate::models::*;
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post, put, delete},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tracing::info;

/// API state
#[derive(Clone)]
pub struct ApiState {
    pub engine: Arc<PolicyEngine>,
}

/// API response wrapper
#[derive(Debug, Serialize)]
pub struct ApiResponse<T> {
    pub success: bool,
    pub message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
}

impl<T> ApiResponse<T> {
    pub fn success(message: impl Into<String>, data: T) -> Self {
        Self {
            success: true,
            message: message.into(),
            data: Some(data),
        }
    }

    pub fn error(message: impl Into<String>) -> ApiResponse<()> {
        ApiResponse {
            success: false,
            message: message.into(),
            data: None,
        }
    }
}

/// Query parameters for listing
#[derive(Debug, Deserialize)]
pub struct ListQuery {
    #[serde(default)]
    pub enabled: Option<bool>,
    #[serde(default = "default_limit")]
    pub limit: usize,
}

fn default_limit() -> usize {
    100
}

/// Create API router
pub fn create_router(engine: Arc<PolicyEngine>) -> Router {
    let state = ApiState { engine };

    Router::new()
        .route("/health", get(health_check))
        .route("/policies", get(list_policies).post(create_policy))
        .route("/policies/:id", get(get_policy).put(update_policy).delete(delete_policy))
        .route("/policies/:id/enable", put(enable_policy))
        .route("/policies/:id/disable", put(disable_policy))
        .route("/evaluate", post(evaluate_policies))
        .route("/trust/:entity_id", get(get_trust_score).put(update_trust_score))
        .route("/trust/:entity_id/adjust", post(adjust_trust_score))
        .route("/violations", get(list_violations))
        .route("/violations/policy/:policy_id", get(get_policy_violations))
        .route("/statistics", get(get_statistics))
        .layer(CorsLayer::permissive())
        .with_state(state)
}

/// Health check handler
async fn health_check() -> impl IntoResponse {
    Json(ApiResponse::success("Policy Engine is healthy", ()))
}

/// List policies
async fn list_policies(
    State(state): State<ApiState>,
    Query(query): Query<ListQuery>,
) -> impl IntoResponse {
    let mut policies = state.engine.list_policies();
    
    if let Some(enabled) = query.enabled {
        policies.retain(|p| p.enabled == enabled);
    }
    
    policies.truncate(query.limit);
    
    Json(ApiResponse::success(
        format!("Retrieved {} policies", policies.len()),
        policies,
    ))
}

/// Get policy by ID
async fn get_policy(
    State(state): State<ApiState>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.get_policy(&id)
        .map(|policy| Json(ApiResponse::success("Policy found", policy)))
        .ok_or(StatusCode::NOT_FOUND)
}

/// Create new policy
async fn create_policy(
    State(state): State<ApiState>,
    Json(policy): Json<Policy>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.add_policy(policy.clone())
        .map(|_| (StatusCode::CREATED, Json(ApiResponse::success("Policy created", policy))))
        .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)
}

/// Update policy
async fn update_policy(
    State(state): State<ApiState>,
    Path(id): Path<String>,
    Json(mut policy): Json<Policy>,
) -> Result<impl IntoResponse, StatusCode> {
    policy.id = id;
    
    state.engine.update_policy(policy.clone())
        .map(|_| Json(ApiResponse::success("Policy updated", policy)))
        .map_err(|_| StatusCode::NOT_FOUND)
}

/// Delete policy
async fn delete_policy(
    State(state): State<ApiState>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.remove_policy(&id)
        .map(|_| Json(ApiResponse::success("Policy deleted", ())))
        .map_err(|_| StatusCode::NOT_FOUND)
}

/// Enable policy
async fn enable_policy(
    State(state): State<ApiState>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.set_policy_enabled(&id, true)
        .map(|_| Json(ApiResponse::success("Policy enabled", ())))
        .map_err(|_| StatusCode::NOT_FOUND)
}

/// Disable policy
async fn disable_policy(
    State(state): State<ApiState>,
    Path(id): Path<String>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.set_policy_enabled(&id, false)
        .map(|_| Json(ApiResponse::success("Policy disabled", ())))
        .map_err(|_| StatusCode::NOT_FOUND)
}

/// Evaluate policies
async fn evaluate_policies(
    State(state): State<ApiState>,
    Json(context): Json<EvaluationContext>,
) -> impl IntoResponse {
    match state.engine.evaluate_and_resolve(&context) {
        Ok(result) => Json(ApiResponse::success("Evaluation completed", result)),
        Err(e) => Json(ApiResponse::error(format!("Evaluation failed: {}", e))),
    }
}

/// Get trust score
async fn get_trust_score(
    State(state): State<ApiState>,
    Path(entity_id): Path<String>,
) -> Result<impl IntoResponse, StatusCode> {
    state.engine.get_trust_score(&entity_id)
        .map(|score| Json(ApiResponse::success("Trust score found", score)))
        .ok_or(StatusCode::NOT_FOUND)
}

/// Update trust score request
#[derive(Debug, Deserialize)]
pub struct UpdateTrustScoreRequest {
    pub factors: std::collections::HashMap<String, f64>,
}

/// Update trust score
async fn update_trust_score(
    State(state): State<ApiState>,
    Path(entity_id): Path<String>,
    Json(req): Json<UpdateTrustScoreRequest>,
) -> impl IntoResponse {
    let score = state.engine.update_trust_score(&entity_id, &req.factors);
    Json(ApiResponse::success("Trust score updated", score))
}

/// Adjust trust score request
#[derive(Debug, Deserialize)]
pub struct AdjustTrustScoreRequest {
    pub event: String,
    pub impact: f64,
}

/// Adjust trust score
async fn adjust_trust_score(
    State(state): State<ApiState>,
    Path(entity_id): Path<String>,
    Json(req): Json<AdjustTrustScoreRequest>,
) -> impl IntoResponse {
    state.engine.adjust_trust_score(&entity_id, &req.event, req.impact);
    
    if let Some(score) = state.engine.get_trust_score(&entity_id) {
        Json(ApiResponse::success("Trust score adjusted", score))
    } else {
        Json(ApiResponse::error("Entity not found"))
    }
}

/// List violations
async fn list_violations(
    State(state): State<ApiState>,
    Query(query): Query<ListQuery>,
) -> impl IntoResponse {
    let violations = state.engine.get_violations(Some(query.limit));
    Json(ApiResponse::success(
        format!("Retrieved {} violations", violations.len()),
        violations,
    ))
}

/// Get violations for policy
async fn get_policy_violations(
    State(state): State<ApiState>,
    Path(policy_id): Path<String>,
) -> impl IntoResponse {
    let violations = state.engine.get_violations_for_policy(&policy_id);
    Json(ApiResponse::success(
        format!("Retrieved {} violations", violations.len()),
        violations,
    ))
}

/// Get statistics
async fn get_statistics(
    State(state): State<ApiState>,
) -> impl IntoResponse {
    let stats = state.engine.get_statistics();
    Json(ApiResponse::success("Statistics retrieved", stats))
}

/// Start API server
pub async fn start_server(engine: Arc<PolicyEngine>, host: &str, port: u16) -> anyhow::Result<()> {
    let app = create_router(engine);
    let addr = format!("{}:{}", host, port);
    
    info!("Policy Engine API server starting on {}", addr);
    
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}
