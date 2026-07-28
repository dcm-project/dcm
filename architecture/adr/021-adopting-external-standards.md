# ADR-021: Adopting External Standards by Reference

**Status:** Accepted  
**Date:** June 2026  
**Docs:** `architecture/adopted-standards-dcm.md` (ADS-001…010), `architecture/data-policy-boundary.md`; UDLM `design-principles/core-tenets.md` (T5), `design-principles/adopted-standards.md`

## Context

DCM and UDLM repeatedly meet domains that a mature, vendor-neutral external standard **already models**:
cost/usage (**FOCUS** — FinOps Open Cost & Usage Specification), Kubernetes cost allocation
(**OpenCost**), compliance (**OSCAL**), identity (**SCIM**). The question recurs: do we model that data
*inside* DCM/UDLM, or reference the external standard?

Cost forced the decision. A first attempt modeled a cost type with a rate schema and outputs inside the
data substrate; it was retired. Modeling adjacent-domain data inside DCM/UDLM (a) duplicates an external
system's record and its lifecycle, (b) couples the substrate to one vendor's vocabulary — a cost type
expressed in Koku's metric names and `Infrastructure/Supplementary` taxonomy is serviceable by **one**
provider — and (c) means re-expressing (badly) a standard that already exists and that providers already
emit. That breaks the core requirement that contracts be **vendor-agnostic**.

## Decision

**Adopt external standards by reference; do not absorb them.** Decided by a test:

| Disposition | Meaning | When |
|---|---|---|
| **Absorb** | define the schema inside DCM/UDLM | only when **no** credible external standard exists **and** the data's lifecycle is genuinely the substrate's to custody |
| **Embed** | bake the fields into every entity | never |
| **Adopt** | reference the standard by conformance + binding | whenever a credible external standard already models the data |

Under Adopt, the **data** (UDLM) carries only: resource **identity** (the join key), a **version-pinned
conformance reference**, and the **binding**; never the standard's schema. **DCM** owns the verbs:
providers declare an `adopted_standard_support` matrix (which standard versions they emit/consume); DCM
**negotiates**, **translates**, and **enforces** versions, and records the **effective version** as
provenance (`adopted-standards-dcm.md`, ADS-001…010). Implementor-bounded parameters (e.g. cost rate
ranges, budgets) are enforced via policy-as-code, not hard-coded.

**Cost is the first case:** the cost data conforms to **FOCUS** (+ **OpenCost** for k8s allocation),
served via the Cost SP's Information-Provider query API — a `serve_data` + `realize_resources` provider
(ADR-005). The Koku backing is an *implementation detail of one provider*, never the contract.

## Alternatives Considered

1. **Absorb — define a cost type / schema in the registry** — rejected: duplicates FOCUS, breaks T1
   (the data model is a custodian, not the owner of every domain's data), and vendor-locks the contract
   to Koku's vocabulary.
2. **Embed cost fields on every entity** — rejected: a stronger T1 violation; cost is not intrinsic to
   every resource's lifecycle.
3. **Adopt FOCUS/OpenCost by reference, negotiate versions in DCM** — chosen: vendor-agnostic by
   construction, no duplication, tracks the standard's evolution without schema churn.

## Consequences

- Cost — and every future adopted domain — is **vendor-agnostic by construction**: any FOCUS-emitting
  provider satisfies the same binding; the backing implementation (Koku, Kubecost, a cloud export) is
  swappable.
- UDLM stays **thin** — identity, lifecycle, relationships, bindings — not a model of every adjacent
  domain. The architectural form of "don't reinvent the wheel."
- DCM gains a **version-negotiation/translation** responsibility (ADS-003/004) and a provider
  **support-matrix** at registration (ADS-001) — so providers detail which standard versions they
  support and implementors get the version they need.
- The external standard can **evolve without DCM schema changes** (FOCUS 1.x → next): DCM bumps a
  pointer, it does not migrate a copied schema.
- The litmus going forward: **if a new external-standard version would force a change to a DCM/UDLM
  schema, we absorbed it by mistake — it should have been adopted.**
- Adoption has **two tiers**, and the integration machinery is routed by kind: **value/codelist**
  standards (ISO 4217, ISO 8601, RFC 4122) are adopted as a referenced field constraint — *no* support
  matrix or version negotiation; **record/schema** standards (FOCUS, OpenCost, OSCAL, SCIM) get the full
  ADS-001…010 apparatus. The full routing table is in UDLM `design-principles/adopted-standards.md` §1a.
  This keeps ADS from being mis-applied to a codelist (e.g. Koku's ISO 4217 change vs its FOCUS export).
