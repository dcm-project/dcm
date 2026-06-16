# ADR-002: Three Foundational Abstractions — Data, Provider, Policy

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 00 (Foundations)

## Context

A management plane for infrastructure must handle many concerns: data storage, external integrations, governance rules, audit trails, placement decisions, dependency resolution, lifecycle events, and more. Without a unifying model, the architecture becomes a collection of ad-hoc services with unclear boundaries.

## Decision

Every component of DCM maps to exactly one of three foundational abstractions:

**DATA** — Everything stored and versioned. The unified data model, entity lifecycle states, field-level provenance, data layers, and audit records. Data flows through a deterministic pipeline: Intent → Requested → Realized → Discovered.

**PROVIDER** — Everything external. Any system DCM interacts with through a defined contract. Providers receive data from DCM, act on it, and return data to DCM. Six provider types cover all external interactions: service, information, meta, auth, peer_dcm, and process.

**POLICY** — Everything that decides. Rules that fire when data matches conditions and produce typed outputs: allow/deny, validation, field mutations, recovery actions, orchestration directives. Policies govern every transition and transformation in DCM.

The interaction model: Data changes trigger Policy evaluation. Policy decisions may mutate Data or select Providers. Providers produce new Data. The cycle repeats.

## Consequences

- Any new capability must map to one of these three abstractions — if it doesn't fit, the abstraction model needs revision, not a fourth pillar
- Documentation, APIs, and code are organized around these three concepts
- Team members only need deep knowledge of 1-2 abstractions for their area of work
