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

**The 21 September-release use cases** (DAV set 29 — *FF Extended Target*) are documented as flows here, each
labeled by its canonical UC number (matching the [DCM Priorities 1-pager](https://docs.google.com/document/d/1gFEDUOlGDbaSxPdhFJhfxjl_iMRbkY9risTZVRhjt2I/edit)
and the Jira hand-off doc) and built on request-realization. Grouped by persona in
**[by-persona.md](by-persona.md)** — the usage-by-role view.

| UC | Flow | Summary |
|----|------|---------|
| 01 | [uc-01](uc-01-vm-as-udlm-resource.md) | VM as a first-class UDLM resource |
| 02 | [uc-02](uc-02-architecture-to-composite.md) | Architectural pattern to composite request |
| 03 | [uc-03](uc-03-vm-standard-provision.md) | Standard VM provision |
| 04 | [uc-04](uc-04-vm-intent-osac-placement.md) | Intent to VM placement on OSAC |
| 05 | [uc-05](uc-05-vm-status-provenance.md) | VM status provenance |
| 06 | [uc-06](uc-06-persistent-volume-provision.md) | Persistent volume provision and attach |
| 07 | [uc-07](uc-07-dependency-graph-data-model.md) | Dependency graph as first-class data |
| 08 | [uc-08](uc-08-cross-provider-dependency-ordering.md) | Cross-provider dependency ordering |
| 09 | [uc-09](uc-09-dependency-failure-surfaced.md) | Dependency failure surfaced |
| 10 | [uc-10](uc-10-full-rehydration-from-intent.md) | Full rehydration from intent |
| 11 | [uc-11](uc-11-provider-failure-recovery.md) | Provider-failure recovery |
| 12 | [uc-12](uc-12-resilience-posture-rehydration.md) | Resilience posture rehydration test |
| 13 | [uc-13](uc-13-vm-lifecycle-reconciliation.md) | VM lifecycle reconciliation |
| 14 | [uc-14](uc-14-drift-detection-remediation.md) | Drift detection and remediation |
| 15 | [uc-15](uc-15-merkle-tree-audit-verification.md) | Merkle-tree audit verification |
| 16 | [uc-16](uc-16-policy-override-approval.md) | Policy override approval workflow |
| 17 | [uc-17](uc-17-provider-registration-capability.md) | Provider registration and capability advertisement |
| 18 | [uc-18](uc-18-workload-portability.md) | Workload portability across providers |
| 19 | [uc-19](uc-19-policy-resolution-by-profile.md) | Policy resolution by profile |
| 20 | [uc-20](uc-20-profile-resolution-onboarding.md) | Profile resolution and tenant onboarding |
| 21 | [uc-21](uc-21-audit-chain-signed-proofs.md) | Cryptographically verifiable audit chain |

**Planned** (same shape): decommission & teardown ordering · drift detection → reconcile · rehydration
(faithful / provider-portable) · dependency brokering (fulfillment: provider).

---

## The shape a flow follows

1. **Thesis** — the outcome in one paragraph, with the pointer to the UDLM stage it performs.
2. **The actors** — the DCM components in play.
3. **The sequence** — a diagram, then a step-by-step walkthrough with a concrete worked example.
4. **What an implementer builds** — the authored content and declarations the flow depends on.
5. **Failure paths** — where and how each step fails, honestly.
6. **Pointers** — the governing contracts + the UDLM stage doc.
