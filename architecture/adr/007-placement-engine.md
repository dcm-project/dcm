# ADR-007: How DCM Decides Where Things Run

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 50 (Placement), Doc 14 (Profiles)

## Context

When a consumer requests a VM, they don't specify which provider or datacenter. Multiple providers may be capable of fulfilling the request. DCM must select the best provider based on sovereignty requirements, capacity, compliance, cost, and organizational policy.

## Decision

The Placement Engine selects providers through a multi-stage scoring process:

1. **Sovereignty pre-filter** — Eliminate providers that don't satisfy data residency requirements (e.g., EU-WEST resources can only go to EU-WEST providers). This is a hard gate, not a score.

2. **Capability filter** — Eliminate providers that don't support the requested resource type or lack required capabilities.

3. **Reserve query** — Query remaining providers for capacity availability and get confidence scores.

4. **Policy-driven scoring** — Apply placement policies that score providers on criteria like cost, performance tier, organizational preference, and existing affinity (e.g., co-locate with related resources).

5. **Selection** — Highest-scoring provider wins. Ties broken by configurable rules.

For composite services (composite resource type specifications), placement runs per-constituent — the database may land on a different provider than the app server, each scored independently but subject to the same sovereignty constraints.

## Consequences

- Consumers never choose providers — placement is always policy-driven
- Adding new providers to a zone automatically makes them candidates for placement
- Placement decisions are audited with full scoring rationale
- Provider health affects placement — unhealthy providers are excluded
