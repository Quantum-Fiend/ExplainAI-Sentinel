# Security Policy

## Supported Versions

The following versions of **ExplainAI-Sentinel** are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes              |
| < 1.0   | ❌ No               |

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Instead, please report any security vulnerabilities by emailing **security@explainai-sentinel.io**.

When reporting, please include:
- A description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact.
- Any suggested fixes.

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Security Features of ExplainAI-Sentinel
- **mTLS**: Mutual TLS is required for all inter-service communication.
- **JWT**: All public-facing APIs require signed JSON Web Tokens.
- **Zero-Trust**: Continuous trust-scoring of service identities.
- **Privacy**: Differential privacy in federated learning models.
