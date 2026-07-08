# ADR-014: How Tenants Are Separated

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Data Store Contracts (UDLM), Universal Groups (UDLM)

## Context

DCM serves multiple teams (tenants) within an organization. Each tenant's data, resources, policies, and audit trails must be isolated. A developer on Team A must not see Team B's resources, and Team A's policies must not affect Team B's requests (unless they're system-level policies that apply to everyone).

## Decision

**Row-Level Security (RLS)** in PostgreSQL enforces tenant isolation at the database layer. Every query is automatically scoped to the actor's tenant — application code cannot accidentally leak cross-tenant data.

Tenants are **DCMGroups** with type `tenant_boundary`. Groups can be nested (organization → department → team) and support the universal group model for flexible organizational mapping.

**Policy domain precedence** respects tenancy: system > platform > tenant > resource_type > entity. A system-level sizing policy applies to all tenants. A tenant-level naming convention applies only to that tenant.

**Per-tenant key binding + crypto-shredding.** A Tenant's data-at-rest key material is bound to it by reference — `dcm-group.key_bindings` → a `Credential.EncryptionKey` (envelope DEK/KEK) issued by a credential-capability provider. That makes the key **addressable**, so the realization can keep it in-boundary (sovereign profile), rotate it, and **crypto-shred** it on decommission: destroying the tenant's KEK renders its data-at-rest unrecoverable (GDPR Art. 17 erasure) while the immutable audit ledger survives (UDLM GRP-013). UDLM carries the binding (data); the realization owns the key lifecycle and the KMS/HSM integration. This is the architecture primitive, not the implementation.

## Consequences

- Tenant isolation is enforced by the database, not application logic — defense in depth
- Cross-tenant operations (ownership transfer, shared resources) require explicit policy authorization
- RLS adds a small query overhead (~2-5%) — acceptable for the security guarantee
- 18 SQL tables all include tenant_uuid columns with RLS policies
- Tenant offboarding erases data-at-rest by **crypto-shredding the per-tenant key** (`key_bindings`), not by mutating the audit ledger — right-to-erasure without breaking tamper-evidence
