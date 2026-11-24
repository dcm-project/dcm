# DCM — Composite Orchestration and the Catalog Cross-Walk

**Audience:** DCM control-plane implementers

> **What this is.** How the control plane *behaves* when it expands and dispatches a composite, and
> how its own catalog model lines up with UDLM's. Both moved here from
> `udlm/docs/spec/foundations/template-composition-model.md`, which defines the composite's DATA —
> what a constituent is, how the four states read, the registration contract. Computed, negotiated
> and executed behaviour is the control plane's (UDLM ADR-008), and the left column of the table
> below is entirely that: placement, dispatch sequencing, status computation, compensation.
>
> The data model stays in UDLM. This is what DCM does with it.

---

## 1. What DCM Does vs What the Registering Provider Does

| Concern | DCM | Registering Provider |
|---------|-----|----------------------|
| Catalog publication | Stores Composite Service registrations; publishes as catalog items | Provides registration: composition definition + constituent declarations |
| Placement of `external` constituents | Selects providers via placement | — |
| Policy evaluation (composite payload) | Runs all policies on assembled payload | — |
| Dependency graph construction | Built from `depends_on` declarations | — |
| Constituent dispatch sequencing | Derived from dependency graph | — |
| Constituent dispatch (`self`) | Sends standard constituent payload to provider | Receives constituent payload via standard Services API; returns standard realized state |
| Constituent dispatch (`external`) | Sends standard constituent payload to placed provider | — |
| Composite status determination | Computed from constituent outcomes + `required_for_delivery` classifications | — |
| Failure handling | Recovery Policy decides response | Provides standard decommission handling for `self` constituents |
| Compensation | Executes dependency-reverse decommission | Receives standard decommission calls for `self` constituents |
| Audit | Aggregates per-constituent audit records into composite audit trail | — |

### 1.1 The Composite Orchestration Scope Is Narrow

The registering provider's responsibility for a Composite Service is structurally identical to a standard Service Provider's responsibility for a single resource type. It receives constituent payloads one at a time (one per dispatched constituent it owns), it returns realized states one at a time, and it implements standard decommission handling. There is no "composite dispatch" API, no "constituent orchestration loop" inside the provider, and no provider-side aggregation.

Aggregation is DCM's responsibility. Sequencing is DCM's responsibility. Failure handling is DCM's responsibility.

---

## 2. Interop — the control plane's own catalog model

The DCM control-plane's merged catalog model (catalog-item-schema / declarative-api, dcm-project enhancements) expresses the same composition concepts in a name-referenced, inferred form. The mapping:

| UDLM catalog item | DCM control-plane catalog | Note |
|---|---|---|
| `component_id` | blueprint resource `name` | Their names are unique per item; ours pattern-locked and uuid-anchored at the item level |
| `depends_on` | `requires_resources` | Their single untyped "must-come-before" edge; ours is the same edge, typed |
| `bindings` (`from_component`/`output`/`to_field`) | CEL `${component.output}` wiring | Ours is the DECLARED/typed form; theirs the INFERRED form (edges implied by CEL references) |

Projection is lossless downward (data-model-core §4): a UDLM catalog item compiles onto their execution DAG without loss — `depends_on` becomes `requires_resources`, each binding becomes a `${from_component.output}` reference. The reverse is lossy (their model cannot express typed outputs' declared consumption, edge strength, or containment), which is why the typed form is the data model and their DAG is treated as a compiled artifact at the boundary.

---

**Source of truth for the data model:** `udlm/docs/spec/foundations/template-composition-model.md`
(constituent declaration, `provided_by`, the dependency graph, `required_for_delivery`, compensation
declaration, the four-state representation, composition visibility, rehydration, nesting depth, the
registration contract, and the `CMP-*` rules). Nothing here restates it — where the two disagree,
UDLM is authoritative.
