# Flows — the engine performing the model

**Purpose:** the layer of documentation **above specifications and contracts** — implementation-oriented
walkthroughs of how DCM runs one real outcome end-to-end. A specification says *what a component must
guarantee*; a **flow** shows *which components run, in what order, with what data*, so the system is
understood and buildable, not reverse-engineered out of the spec set.

---

## The stage and the actors

Every flow has two tellings:

- **UDLM sets the stage** — the model's telling defines the outcome in terms of abstractions, four-state
  transitions, and the **invariant each phase must uphold**, provider- and engine-neutral. It is the script
  and the rules. See [udlm `docs/flows/`](https://github.com/croadfeldt/udlm/tree/main/docs/flows).
- **DCM is the actors creating the play** — *this* tier tells the same flow as a concrete performance: the
  components, the sequence, the data at each step, the failure paths, and **what an engineer must build**.

Read the UDLM flow for *what must be true and why*; read the DCM flow for *how it is made true*. Each flow
here links its UDLM counterpart.

---

## Index

| Flow | What it performs | UDLM stage |
|---|---|---|
| [Request realization](request-realization.md) | An abstract, portable request becomes provider-ready — assembled, enriched, validated, then built | [udlm `docs/flows/request-realization.md`](https://github.com/croadfeldt/udlm/tree/main/docs/flows/request-realization.md) |

**[request-realization](request-realization.md) is the foundational flow** — it walks the whole model end
to end. Every other flow is intentionally **lighter and uses it as its base**: it assumes request-realization
and *references* the shared steps (assemble, place, enrich, reserve, converge) rather than re-explaining
them, so each use-case flow stays short and specific to what makes that case different. Read
request-realization first.

**Planned** (same shape): the 21 September-release use cases (each labeled by its Use Case number, grouped by
persona) · decommission & teardown ordering · drift detection → reconcile · rehydration (faithful /
provider-portable) · dependency brokering (fulfillment: provider).

---

## The shape a flow follows

1. **Thesis** — the outcome in one paragraph, with the pointer to the UDLM stage it performs.
2. **The actors** — the DCM components in play.
3. **The sequence** — a diagram, then a step-by-step walkthrough with a concrete worked example.
4. **What an implementer builds** — the authored content and declarations the flow depends on.
5. **Failure paths** — where and how each step fails, honestly.
6. **Pointers** — the governing contracts + the UDLM stage doc.
