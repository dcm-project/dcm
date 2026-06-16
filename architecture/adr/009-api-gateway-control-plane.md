# ADR-009: Why an API Gateway and What the Control Plane Services Do

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 25 (Control Plane Services), OpenAPI Specs

## Context

DCM has multiple consumers (developers, platform engineers, admins, providers, external systems) that interact via different APIs with different authorization scopes. Internally, DCM has multiple services that process requests through a pipeline. These services need a single entry point that handles authentication, routing, rate limiting, and API versioning.

## Decision

The **API Gateway** is the single entry point for all external traffic. It handles:
- Authentication (JWT validation, API key verification)
- Route multiplexing (consumer API, admin API, provider callback API)
- Rate limiting and throttling per tenant
- TLS termination
- API versioning (v1, v1alpha1)

Behind the gateway, **9 control plane services** process requests through the pipeline:

| Service | What it does |
|---------|-------------|
| API Gateway | Routes external traffic to internal services |
| Catalog Manager | Serves the service catalog and resource type registry |
| Request Processor | Assembles layers, resolves dependencies, builds requested state |
| Policy Engine | Evaluates all matching policies against the request payload |
| Placement Engine | Scores and selects providers for fulfillment |
| Request Orchestrator | Dispatches to providers, manages async callbacks, handles retries |
| Audit Service | Records tamper-evident audit trail with Merkle tree |
| Discovery Service | Polls providers for current state, detects drift |
| Provider Manager | Manages provider registration, health monitoring, sovereignty declarations |

## Consequences

- All external traffic goes through one endpoint — simplifies network policy and TLS
- Services communicate internally via direct calls or PostgreSQL LISTEN/NOTIFY
- Each service has its own health endpoint and can be scaled independently
- The pipeline is deterministic: assembly → policy → placement → dispatch → callback
