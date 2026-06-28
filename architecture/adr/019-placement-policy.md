# ADR-019: Placement Policy

**Status:** Proposed
**Date:** June 2026
**Docs:** ADR-002 (Three Abstractions), ADR-007 (Placement Engine), ADR-011 (Sovereignty); UDLM **ADR-001 (`Topology`)**, **ADR-002 (Capacity/Utilization)**, **ADR-004 (Provider capability declaration)**
**Tracking:** raised by dcm-project/dcm #64 (pkliczewski: "what about placement policy?")

## Context

The Placement Engine (ADR-007) tie-breaks on `affinity`/`cost`/`load`, but nothing **authors** placement constraints — there is no policy that lets a consumer/org express "spread across failure domains," "co-locate app+db," "keep in EU," or "prefer provider X." The data to resolve against now exists in UDLM (`Topology`, capacity/utilization, provider capability); this ADR adds the **policy** that consumes it.

## Decision

Introduce **Placement Policy** — the **8th typed Policy** (alongside Gating Policy, Validation, Transformation, Recovery, Orchestration-Flow, Governance-Matrix, Lifecycle).

- **Authors declarative placement constraints**: affinity / anti-affinity / co-locate / spread / prefer / avoid / pin, plus weights — keyed on abstract `Topology` **`kind`s** (`zone`/`host`/`power-domain`/…), never provider-native ids.
- **Declarative only** (no embedded expressions); the **Placement Engine evaluates** it. Output feeds the engine's scoring/tie-break stage.
- **Enforces the portability discipline** (UDLM ADR-001 §17): rejects intent that names provider-native topology ids — those belong to realized state.
- **Consumes**: UDLM `Topology` (the map), capacity/utilization (the load/headroom), and provider `topology_capability` (ADR-004) to filter/score candidates.

## Data · Policy · Provider (required lens — see ADR README)

- **Data (UDLM):** `Topology` (kinds + concrete domains), capacity/utilization overlay, each resource's locality reference — the facts placement reads. *(UDLM ADR-001/002.)*
- **Policy (DCM, this ADR):** the Placement Policy constraint grammar + the engine evaluation/scoring + portability enforcement. *(The decision/compute.)*
- **Provider:** declares `topology_capability` + `mobility` (ADR-004) and naturalizes abstract kinds to its native topology; populates the concrete `Topology`. *(What's possible + execution.)*

## Options considered
- **Provider-native placement constraints** — rejected: destroys portability.
- **Affinity via relationships only** — rejected: doesn't carry weights/spread/prefer or org-authored intent.
- **Placement Policy (8th typed policy) over abstract `Topology`** — **chosen**; fits the typed-policy model and the Data⇄Policy boundary.

## Consequences
- New typed policy; the taxonomy's typed-Policy set grows from 7 → 8.
- Cross-domain: governs placement of **any** resource type (the `Topology`/capability data it reads is cross-cutting).
- Sovereignty/residency becomes a placement constraint over jurisdiction-labeled domains (unifies with ADR-011).
- Companion: ADR-020 (migration & operational gating).
