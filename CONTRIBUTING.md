# Contributing to ExplainAI-Sentinel

First off, thank you for considering contributing to **ExplainAI-Sentinel**! It's people like you that make it such a great tool.

## 🌈 Our Polyglot Values
Because this project uses 9 programming languages, we have some special guidelines:
- **Consistency**: Maintain the established architectural patterns (Event-driven, REST, Microservices).
- **Quality**: Every language tier should follow its community's best practices (e.g., idiomatic Go, Rust, or Python).
- **Communication**: All components must use the unified JSON schemas for events and metrics.

## 🏗️ Development Setup
1.  **Clone the repo**: `git clone ...`
2.  **Ensure prerequisites**: See [SETUP.md](./SETUP.md).
3.  **Local Testing**: Use the root `Makefile` for orchestrating your changes.

## 🧪 Testing Standards
-   **Go**: `go test ./...`
-   **Python**: `pytest`
-   **Rust**: `cargo test`
-   **Java/Scala/Kotlin**: `mvn test`, `sbt test`, `./gradlew test`
-   **C**: Use the provided Makefile in `/logging`.

## 📝 Pull Request Process
1.  Create a branch from `develop`.
2.  Ensure CI passes (see GitHub Actions).
3.  Update the `CHANGELOG.md` with your changes.
4.  Tag a maintainer for review.

## 🛡️ Security
If you find a security vulnerability, please do **not** open an issue. Instead, email security@example.com.
