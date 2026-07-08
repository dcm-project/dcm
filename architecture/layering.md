---
Document Status: ✅ Stable — Architectural framing
Document Type: Architecture Foundation
Established: 2026-05-26
Maps to: UDLM substrate / DCM realization boundary
---

# Layering — UDLM substrate vs DCM realization

> **Implements contracts defined in UDLM**: this document names the boundary
> that the UDLM repo ([github.com/croadfeldt/udlm](https://github.com/croadfeldt/udlm))
> and this DCM repo collectively imply. The boundary rule is normative for
> both sides; the application of the rule (what lives where) is recorded in
> [`00-split-manifest.md`](00-split-manifest.md).

This document is the DCM-side perspective on the layering that justifies the
split between UDLM (substrate) and DCM (realization).

---

## The Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Higher-Order Universal Model           (deliberately deferred) │
│  ─────────────────────────────────                              │
│  A more abstract universal model that UDLM is a specialization  │
│  of. Could be derived later if a real second realization        │
│  creates the pressure. NOT formalized today.                    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│  UDLM — github.com/croadfeldt/udlm                              │
│  ────────────────────────────────                                │
│  The universal substrate. Owns the *what*:                      │
│    • entity types, fields, relationships                        │
│    • the four states (intent, requested, realized, discovered)  │
│    • allowed state transitions and lifecycle invariants         │
│    • provenance, lineage, identity                              │
│    • wire contracts (provider, policy, event payloads,          │
│      data store, schema-sharing protocol)                       │
│    • reference taxonomies (authority tier model, registry       │
│      governance model, layered-topology contract, ...)          │
│                                                                 │
│  UDLM owns wire-level compatibility. Any peer realization that  │
│  conforms produces data that any other conformant peer can      │
│  read, interpret, and exchange.                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (this repo realizes)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│  DCM — this repo                                                │
│  ────────────────                                                │
│  One operational platform built on UDLM. Owns the *how*:        │
│    • control-plane components and their boundaries              │
│    • the convergence engine (the intent → realized loop)        │
│    • policy evaluation at each transition                       │
│    • provider invocation, retry, dependency-graph orchestration │
│    • ingress / egress, APIs, service boundaries                 │
│    • drift detection, recovery utilities, expiration            │
│    • persistence (PostgreSQL mandated for this realization)     │
│    • specific 9-layer canonical location hierarchy              │
│    • mTLS + interaction credential as provider callback auth    │
│    • deployment topology, runtime concerns                      │
│                                                                 │
│  A different DCM-peer realization could consume the same UDLM   │
│  substrate and realize it differently while remaining wire-     │
│  compatible at the UDLM contract boundary.                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## The boundary rule

For each file or section, the test is:

> *"Could a peer of DCM, built independently, choose to do this differently
> and still be a valid realization of the same data?"*

- **Yes →** belongs in **DCM**. It's an operational/implementation choice.
- **No, it would break interop or invalidate the data →** belongs in **UDLM**.
  It's a substrate invariant.

| Concern | Layer | Why |
|---|---|---|
| State names (intent, requested, realized, discovered) | UDLM | Vocabulary every realization shares |
| Field shape at each state | UDLM | Same data, regardless of operationalization |
| Allowed transitions between states | UDLM | Invariant of the data, not a runtime choice |
| Provider response shape | UDLM | Wire contract |
| Policy input/output schemas | UDLM | Wire contract |
| Event payloads | UDLM | Wire contract that lets observers exist |
| Schema-sharing protocol | UDLM | Required for federation peers to exchange custom-type schemas |
| **The convergence loop that walks data through states** | **DCM** | Implementation choice — see [convergence-engine/overview.md](convergence-engine/overview.md) |
| **Provider invocation, retry, ordering** | **DCM** | Orchestration — see [convergence-engine/recovery-and-retry.md](convergence-engine/recovery-and-retry.md) |
| **PostgreSQL as the data store** | **DCM** | UDLM requires persistence; DCM mandates PostgreSQL specifically. See [persistence/postgres-mandate.md](persistence/postgres-mandate.md) |
| **mTLS + interaction credential for provider callback** | **DCM** | UDLM defines two-layer auth abstractly; DCM picks the specific mechanism. See [credentials-and-auth/provider-callback.md](credentials-and-auth/provider-callback.md) |
| **Specific 9-layer location hierarchy** | **DCM** | UDLM defines layered-topology contract; DCM picks Country → ... → Unit. See [topology/canonical-9-layer-hierarchy.md](topology/canonical-9-layer-hierarchy.md) |
| **Drift detection / recovery / expiration utilities** | **DCM** | Runtime concerns |
| **Control-plane components, service boundaries, APIs** | **DCM** | Deployment / runtime choices |

---

## Compatibility model (LOCKED)

**UDLM enforces wire-level compatibility at the data/event/contract boundary;
it does not enforce implementation portability.**

- Any system conformant to UDLM version X produces data that any other system
  conformant to the same major version can read, interpret, and exchange
  (versioning rules apply).
- Federation between peers is **literal interop**, not "architecturally similar
  systems requiring adapters."
- A peer realization's storage, internal APIs, control-plane components, and
  runtime mechanics are NOT constrained by UDLM — those are DCM-layer choices.

This is the K8s precedent: K8s API + CRDs are wire-compatible across
distributions; controllers are not portable. UDLM and DCM are in the same shape.

---

## Why the Higher-Order Model is deferred

A more abstract universal model likely exists above UDLM — a "manage-anything-
via-data-and-policy" pattern UDLM is a specialization of. It is intentionally
not formalized today:

- **Abstraction discipline.** UDLM is allowed to be specific enough to be
  realizable, even if that bakes in some assumptions a purer model wouldn't.
- **No pressure yet.** The higher-order model becomes worth formalizing when
  a real second realization (a non-DCM peer using UDLM) creates pressure to
  identify what is truly shared vs DCM-specific. Until then, drawing the line
  is guessing.
- **Cost asymmetry.** Premature abstraction costs more than lifting concepts
  up later when the line becomes obvious.

Treat the higher-order layer as **known to exist** and **named**, but **out of
scope for current documentation**. If a peer of DCM emerges, this is the layer
where the genuinely-shared bits will be lifted from UDLM.

---

## Implications for verification/assessment consumers

A verification consumer (an assessment realization or test harness — non-normative;
nothing here depends on a specific tool) tests use cases against the architecture.
Per this layering, that's two distinct questions:

1. **"Does UDLM support this use case?"** — does the substrate accommodate the
   entities, states, contracts, lifecycle the UC needs?
2. **"Does DCM operationalize it correctly?"** — does the convergence loop,
   provider orchestration, and runtime actually realize it?

Such a consumer's `spec_refs` use namespaced paths to disambiguate:
- `udlm/contracts/event-catalog.md` — substrate reference
- `dcm/architecture/convergence-engine/policy-evaluation.md` — realization reference

The two repos are independently fetchable; cross-repo references are resolved
during use-case evaluation.
