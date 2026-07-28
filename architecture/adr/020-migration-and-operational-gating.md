# ADR-020: Migration & Operational Gating

**Status:** Proposed
**Date:** June 2026
**Docs:** ADR-002 (Three Abstractions), ADR-006 (Policy Engine), ADR-011 (Sovereignty), ADR-013 (Override & Exception Governance), ADR-019 (Placement Policy); UDLM **ADR-003 (Data mobility + process validation, T6)**, **ADR-004 (Provider capability declaration)**
**Tracking:** placement-data family — the control-plane side of UDLM data mobility + process validation

## Context

UDLM ADR-003 makes data mobility declarable (`data_mobility` requirements, `process_validation` lifecycle) and ADR-004 makes provider mobility/operational capability declarable. The control plane must **govern** when/whether a migration may run, **gate** on validation freshness, and **schedule** rehearsals — without inventing new policy machinery.

## Decision

Migration and operational gating **reuse the existing typed policies** (no new types beyond ADR-019); they are configurations of them:

- **Migration *permission*** → **Governance-Matrix** policy: every cross-boundary move is evaluated (sovereignty/jurisdiction — ADR-011); cross-jurisdiction migrations `DENY` / `ALLOW_WITH_CONDITIONS` / dual-approval (ADR-013).
- **Migration *sequence*** → **Orchestration-Flow** policy: the ordered cutover steps (provision target → replicate → verify → switch → drain) — provider executes each.
- **Capability match** → **Placement Policy** (ADR-019) extends to require a provider whose `mobility` (ADR-004) satisfies the resource's `data_mobility` (RTO/RPO/online).
- **Process-validation gating (T6)** → **Validation Policy** (`enforcement_class: compliance`): `gate_on_stale` ⇒ deny placing/depending-on a critical workload whose `mobility_validation` is `stale`/`failing`. Compliance-class (fail-safe).
- **Rehearsal scheduling** → an operational policy fires `simulated`/`rehearsal` runs on the `process_validation.cadence`; the provider runs them (`operational_capability.rehearsal_support`), evidence is recorded, freshness refreshed.

**A real incident executes the same validated path (T6)** — it validates the outcome; the gates above just ensure the path was proven first.

## Data · Policy · Provider (required lens)

- **Data (UDLM):** `data_mobility`, `process_validation`, `mobility_validation` evidence (ADR-003) — requirements + observed proof.
- **Policy (DCM, this ADR):** permission (Governance-Matrix), sequence (Orchestration-Flow), gating (compliance Validation), scheduling (operational) — when/whether/how-gated.
- **Provider:** declares `mobility` + `operational_capability` (ADR-004); **executes** the migration mechanism and the rehearsals (naturalization) — unmodeled "how."

## Options considered
- **A bespoke "migration policy" type** — rejected: migration permission/sequence/gating are already expressible as Governance-Matrix / Orchestration-Flow / Validation configurations; minimal-core.
- **Reuse existing typed policies + Placement Policy capability match** — **chosen.**

## Consequences
- No new policy *type* (beyond ADR-019); migration/operational gating are policy *configurations*.
- Cross-domain: applies to any resource carrying `data_mobility` (any stateful domain).
- Makes ADR-019's "change topology → rebuild" governed + proven: the rebuild is permission-checked, freshness-gated, and sequence-orchestrated.
- DAV connection: the `process_validation` findings/evidence are the same validation-backed records an assessment realization surfaces — one evidence model.
