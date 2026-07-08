# DCM ↔ UDLM — the Data / Policy responsibility boundary

DCM and UDLM are two domains separated by one **responsibility boundary** — a service / contract seam.
Getting it right is what keeps the data model portable, auditable, and sovereign, and keeps DCM's logic
where it belongs. This is the DCM-side statement of the boundary defined in UDLM's
`design-principles/core-tenets.md`.

| Domain | Owner | Responsibility |
|---|---|---|
| **Data** | UDLM | Custody of data through its lifecycle: identity, the four states, versioning, relationships, provenance, audit records, sovereignty fields. *Hold, move, reference, version, audit.* |
| **Policy** | **DCM** | **Application of policy** — transformation, enrichment, derivation, decision, governance. *Compute, derive, evaluate, decide, enforce.* |

**UDLM defines the contracts (Data, Provider, and Policy); DCM is where Policy is *applied*.** UDLM
carries the data policy acts on and records the decisions policy makes; it never executes logic. DCM
never becomes the system of record for lifecycle state; it applies logic over UDLM data.

## What DCM owns (the verbs)
- **Assembly** — Intent → Requested: merge Layers (data) under Policy (logic), recording per-field
  provenance back into the UDLM record.
- **Policy evaluation** — Validation Policy, Transformation; the **Governance Matrix** and
  **sovereignty/accreditation/trust** decisions; placement.
- **Dependency-graph application** — validate the DAG (`RDG-001`), order forward execution, run
  compensation in reverse, schedule rehydration in dependency order.
- **Realization** — dispatch to Providers, collect Realized state, run Discovery → drift, resolve
  conflicts (field ownership / server-side apply).
- **Audit production** — write the synchronous, append-only, Merkle-chained log (`AUD-001/002`).
- **Adopted-standard runtime** — for externally-adopted standards (FOCUS, OpenCost, OSCAL, SCIM), the
  data carries identity + version pins; **DCM negotiates, translates, and enforces standard versions**
  and records the effective version as provenance. Full requirements: `adopted-standards-dcm.md`
  (`ADS-001…010`); the Data-side contract is UDLM `design-principles/adopted-standards.md` (tenet T5).
- **Enforcement** — reject changes to `immutable`/createOnly fields; reject sovereignty-boundary
  violations; reject non-conformant data at the seam.

## What DCM must NOT do (boundary violations)
- Become the durable system of record for lifecycle state — that is UDLM data.
- **Absorb an adopted standard's schema** into DCM persistence, or become the system of record for
  adopted data (cost, compliance, identity). That data conforms to its standard and is referenced via an
  Information Provider, lookup-only (`adopted-standards-dcm.md`, `ADS-007`).
- Push executable logic *into* the portable data model. UDLM carries **no embedded expression
  language**; all transformation/enrichment is DCM policy. This is what makes the contract layer
  **deterministic and reproducible** (the precondition for tamper-evident audit and sovereignty):
  determinism is structural in the data because the evaluator lives only in DCM.
- Let a runtime decision that legitimately depends on live state (e.g. placement by current capacity)
  silently alter the contract. Such decisions are **recorded as decisions in the audit log**, never
  written back as if they were the reproducible definition.

## Why the boundary holds the line on the four pillars
- **Audit:** data is immutable + version-pinned (`$id`); DCM produces the proofs. Reproducible forever.
- **Observability:** UDLM declares relationships + typed outputs; DCM reconciles observed vs declared.
- **Dependency graph:** UDLM carries typed edges; DCM constructs/validates/orders the DAG.
- **Sovereignty:** UDLM marks sovereignty fields `immutable` and bundles offline closures; DCM enforces
  the Governance Matrix. Because no expression rides in the data, nothing can route around the boundary.

> Test: a **noun** (record, contract, edge, marker, pin) is UDLM's. A **verb** (assemble, evaluate,
> decide, enforce, transform, resolve) is DCM's.

See UDLM `design-principles/core-tenets.md` (T1–T4) and `cross-cutting-requirements.md` for the
substrate side; the Resource Type Registry (`registry/`) is the concrete Data-domain contract DCM applies.
