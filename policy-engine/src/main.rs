use policy_engine::{api, engine::PolicyEngine, ConflictResolution};
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "policy_engine=info,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    // Create policy engine
    let engine = Arc::new(PolicyEngine::new(
        ConflictResolution::HighestPriority,
        0.7, // Trust threshold
    ));

    tracing::info!("Policy Engine initialized");

    // Start API server
    let host = std::env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8003);

    api::start_server(engine, &host, port).await?;

    Ok(())
}
