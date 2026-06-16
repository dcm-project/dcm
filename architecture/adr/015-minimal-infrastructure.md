# ADR-015: Why PostgreSQL Is the Only Required Dependency

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 11 (Data Store Contracts), Doc 17 (Deployment)

## Context

Infrastructure management platforms often require heavy middleware stacks: message brokers, secret managers, identity providers, search engines. This creates a bootstrap problem — you need significant infrastructure just to manage infrastructure. It also blocks adoption in resource-constrained environments (homelab, edge, evaluation).

## Decision

PostgreSQL is the only required dependency. DCM implements internal equivalents for every capability that optional services provide:

| Capability | Internal (default) | External (optional) |
|-----------|-------------------|-------------------|
| Events | PostgreSQL LISTEN/NOTIFY | Kafka |
| Secrets | Envelope-encrypted table | Vault |
| Auth | Built-in bcrypt + JWT | Keycloak/OIDC |
| Search | PostgreSQL full-text + GIN | OpenSearch |
| Notifications | PostgreSQL LISTEN/NOTIFY + webhooks | External notification service |

Every optional dependency follows the same pattern: internal by default, externally delegable by configuration. The same API surface is exposed regardless of which implementation is active.

## Consequences

- Bootstrap is `docker-compose up` with one PostgreSQL container
- Production deployments can delegate to Kafka, Vault, Keycloak when scale or policy requires it
- Internal implementations have performance ceilings (LISTEN/NOTIFY: ~1K events/sec vs Kafka: millions)
- Every new cross-cutting service must implement the internal path first
