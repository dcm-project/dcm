# Layering — Data Model vs DCM (vs the Higher-Order Model)

**Document Status:** ✅ Stable — Architectural framing
**Document Type:** Architecture Foundation — Read alongside `data-model/00-foundations.md`
**Established:** 2026-05-26 (working session)

> This document captures the conceptual layering that the existing
> `data-model/` and DCM platform documents collectively imply but do not state
> explicitly. The intent is to make the layering nameable so future docs can
> reason about which layer a concept belongs to.

---

## The Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  Higher-Order Universal Model           (deliberately deferred) │
│  ─────────────────────────────────                              │
│  A more abstract universal model that the Data Model below is   │
│  a specialization of. Could be derived from this work later if  │
│  a real second realization creates the pressure. NOT formalized │
│  today — kept "in the shadows" by design.                       │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (would specialize to)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│  Data Model                                                     │
│  ──────────                                                     │
│  The universal, normative representation that gives the control │
│  plane its universality. Owns the *what*:                       │
│    • entity types, fields, relationships                        │
│    • the four states (intent, requested, realized, discovered)  │
│    • allowed state transitions and lifecycle invariants         │
│    • provenance, lineage, identity                              │
│    • contracts that any realization must honor                  │
│      (provider contract, policy contract, event payloads)       │
│                                                                 │
│  Universal-enough-to-be-realized: specific enough that a        │
│  concrete operationalization can be built against it, abstract  │
│  enough that a peer of DCM could be built without redefining    │
│  the substrate.                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ (operationalizes / consumes)
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│  DCM                                                            │
│  ───                                                            │
│  One operational platform built on the Data Model. Owns the     │
│  *how*:                                                         │
│    • control-plane components and their boundaries              │
│    • the convergence engine (the intent → realized loop)        │
│    • policy evaluation at each transition                       │
│    • provider invocation, retry, dependency-graph orchestration │
│    • ingress / egress, APIs, service boundaries                 │
│    • drift detection, recovery utilities, expiration            │
│    • deployment topology, runtime concerns                      │
│                                                                 │
│  DCM is one use case of the Data Model. A different platform    │
│  could consume the same Data Model and realize it differently.  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Boundary Rules

| Concern | Layer | Why |
|---|---|---|
| State names (intent, requested, realized, discovered) | Data Model | Vocabulary every realization shares |
| Field shape at each state | Data Model | Same data, regardless of operationalization |
| Allowed transitions between states | Data Model | Invariant of the data, not a runtime choice |
| Provider response shape | Data Model | Interface — any realization implements against it |
| Policy input/output schemas | Data Model | Interface — any realization implements against it |
| Event payloads | Data Model | Interface that lets observers exist |
| **The convergence loop that walks data through states** | **DCM** | Implementation choice — could be done differently |
| **Provider invocation, retry, ordering** | **DCM** | Orchestration — DCM's mechanism |
| **Drift detection / recovery / expiration utilities** | **DCM** | Runtime concerns — operational additions on top |
| **Control-plane components, service boundaries, APIs** | **DCM** | Deployment / runtime choices |

### Quick test for which layer a new concept belongs to

Ask: *"Could a peer of DCM, built independently, choose to do this differently and still be a valid realization of the same data?"*

- **Yes →** belongs in **DCM**. It's an operational/implementation choice.
- **No, it would invalidate the data →** belongs in the **Data Model**. It's a substrate invariant.

---

## Why the Higher-Order Model Is Deferred

There likely exists a more abstract universal model above the Data Model — a "manage-anything-via-data-and-policy" pattern that the Data Model is a specialization of. **It is intentionally not formalized today.** Reasons:

- **Abstraction discipline.** A Data Model abstract enough to cover "any management system ever" stops being concrete enough to realize anything. The current Data Model is allowed to be specific enough to be realizable, even if that bakes in some assumptions a purer universal model wouldn't.
- **No pressure yet.** The higher-order model only becomes worth formalizing when a real second realization (a non-DCM platform using the same data model) creates pressure to identify which bits are truly shared vs DCM-specific. Until then, drawing the line is guessing.
- **Cost asymmetry.** Premature abstraction costs more than lifting concepts up later when the line becomes obvious. Concrete pressure is the right trigger.

Treat the higher-order layer as **known to exist** and **named** ("Higher-Order Universal Model"), but **out of scope for current documentation**. If a peer of DCM emerges, this is the layer where the genuinely-shared bits will be lifted.

---

## Implications for the Repo

- `architecture/data-model/` is the **Data Model** layer. The "DCM" in document titles there is mostly historical — the substance is Data Model.
- The DCM platform layer (control-plane components, deployment, APIs, runtime) is partially documented across `architecture/` (root level), `deployment/`, and `dcm-platform-requirements.md`.
- A future re-org could physically split these into two doc surfaces (or two repos: `data-model` + `dcm`) so the Data Model can be referenced independently. **Not done today** — keep the doc reorg as a follow-on once the boundary work above stabilizes.

## Implications for DAV (the verification framework)

DAV currently tests use cases against "the DCM architecture" as a single corpus. Per this layering, that's two distinct questions:

1. **"Does the Data Model support this use case?"** — does the substrate accommodate the entities, states, contracts, lifecycle the UC needs?
2. **"Does DCM operationalize it correctly?"** — does the convergence loop, provider orchestration, and runtime actually realize it?

Most existing UCs entangle both. A future evolution of DAV could:
- Split the spec corpus into Data Model docs vs DCM docs and tag UCs by which layer they're testing
- Add a `layer` dimension to UC metadata (`data_model` | `dcm` | `both`)
- Report verdicts per layer when applicable

Not actioned today; flagged so the structure is available when the docs split.
