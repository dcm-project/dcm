# UC-15 · Provider-portable rebuild — the play

**Purpose:** how DCM rebuilds resources on an alternate provider after a failure, on top of
[request-realization](request-realization.md) — only the UC-specific mechanics.

> **Use Case:** `cross-domain/provider-portable-rebuild` · **Persona:** platform-engineer.

## What's different in the engine
- **Provider health is a trigger.** A failed health check or an explicit deregistration marks the provider
  unavailable and identifies the realized resources placed on it.
- **Placement re-runs with an exclusion.** The affected resources go back through the placement engine with
  the failed provider removed from the eligible pool. Validation policies re-evaluate against the alternate —
  a resource may only move somewhere policy still allows.
- **Naturalized references are re-derived.** The old provider's `provider_extensions` (namespace, native id,
  cluster) are dropped and re-enriched for the new provider through the ordinary enrichment step. The portable
  base of the resource is unchanged.
- **Re-realize, then confirm portability.** The dispatcher reserves and commits on the alternate provider, and
  the engine confirms the provider-neutral fields still match intent. The whole move is recorded.

## Sequence — only the UC-specific part
```mermaid
sequenceDiagram
    participant Reg as Provider registry
    participant Rebuild as Portable-rebuild controller
    participant Pol as Placement + policy engine
    participant Alt as Alternate provider
    participant St as Intent + realized stores
    participant Aud as Audit store

    Reg-->>Rebuild: provider unavailable (health / deregistration)
    Rebuild->>St: read intent for affected resources
    St-->>Rebuild: intent + realized
    Rebuild->>Pol: re-place with failed provider excluded
    Pol->>Pol: re-evaluate validation policies for alternate
    Pol-->>Rebuild: alternate eligible provider chosen
    Rebuild->>Rebuild: rewrite naturalized references for new provider
    Rebuild->>Alt: reserve then commit (re-realize from intent)
    Alt-->>Rebuild: built + new native id
    Rebuild->>St: update realized (provider-neutral fields match intent)
    Rebuild->>Aud: record portability event + re-resolution
```

## What an engineer adds
- The **health/deregistration signal** and the **controller** that gathers affected resources and drives
  re-placement with the failed provider excluded.
- The **reference-rewrite** step that clears and re-enriches provider-specific extensions for the new provider.
  Placement, enrichment, and the dispatcher are reused as-is.

## Pointers
- Stage: [udlm request-realization](https://github.com/croadfeldt/udlm/tree/main/docs/flows/request-realization.md). UC source: `cross-domain/provider-portable-rebuild`.
