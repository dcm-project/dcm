# ADR-027: Realizing the policy information firewall

**Status:** Proposed (croadfeldt upstream) — companion to UDLM **ADR-041** (policy as information firewall); downstream adoption pending eng alignment

**Date:** 2026-07-22

## Context

UDLM **ADR-041** settles that, in its **information-flow role**, policy **is an information firewall**: it mediates data crossing boundaries — **directionally** (egress *release* control + ingress *admission* control), on **structure** (the unresolved reference, L3/L4) or **value** (the resolved datum, L7), backed by a **resolver** and **reactive re-convergence**, dialing up to a **cross-domain guard** for high-assurance zones. ADR-041's UDLM-vs-DCM split assigns the **contract** (surfaces, directional structure, invariants, guard grammar) to UDLM and the **engine — every enforcement decision** to DCM.

This ADR records **where that engine half lives in DCM**. As with the scoped-Class realization (ADR-025), the finding is that it is *mostly already here*: DCM already has a policy engine, sovereignty/residency, a trust model, a naturalization boundary, and reference-resolution/change-impact. The firewall contract **organizes those into the flow role** and names a small amount of net-new work. It touches only policy's *flow* role; policy's assembly/constraint/fill role (ADR-006 as used by ADR-012/024/025) is unchanged.

## Decision

**1. The firewall's DCM responsibilities map onto existing engines.**

| Firewall responsibility (UDLM ADR-041) | DCM home |
|---|---|
| Evaluate policy at each crossing (the gates) | Policy engine (ADR-006) |
| **Egress** release-control — sovereignty, tenancy, classification-out | Sovereignty & residency (ADR-011) + multi-tenancy isolation (ADR-014) + policy engine (ADR-006) |
| **Ingress** admission — provenance / trust / classification-in | Trust model (ADR-022) + discovered ingestion (ADR-017) + naturalization (ADR-023) |
| **Resolver** — resolve projected / navigational data for value inspection (`PROJ-P1`) | Reference resolution (ADR-024) + data assembly (ADR-012) — the same resolver |
| **Structural** match on the unresolved reference/edge graph (L3/L4) | the change-impact graph (ADR-024) fed as a match source into the policy engine (ADR-006) |
| Audit each disposition (released / redacted / denied) | Audit & tamper-evidence (ADR-010) |

**2. Net-new DCM work (small):**
- **Structural-match evaluation** — the policy engine matches on the **unresolved** edge graph (target / relation / nature / **authority in the address**), not only on resolved values. Extends ADR-006 to read the ADR-024 graph as a match source. This is the L3/L4 surface; it needs no dereference and reuses the `impact_report` graph ("everything pointing to X").
- **Policy re-convergence** — capture **policy-input provenance** (each `policy → datum` dependency), then extend change-impact (ADR-024) to find affected **policies** (not only affected specs) and re-fire them. Push or pull is an engine choice; the requirement is the policy→data edges are recorded.
- **Policy cycle & non-determinism detection.** Policy application is a **re-entrant fixpoint** — evaluate → enrich/inject/mutate → re-validate, until stable (UDLM **ADR-041**) — which the engine MUST make **converge deterministically**:
  - **At execution** — the fixpoint loop is **bounded and cycle-detected**: oscillation (a state repeats) or divergence (no fixpoint within the bound) **halts with a policy-conflict diagnostic** naming the offending policies — never a silent non-deterministic result and never an unbounded loop. Backed by the Evaluation Context (shared constraint space, for confluence) and audit (ADR-010).
  - **At policy-injection (best-effort, static)** — when a policy enters the system, analyze the policy set's **mutation-dependency graph** (policy A's mutation triggers policy B's match) for cycles, and check **field-write confluence** (two policies writing one field order-dependently). **Reject or flag a cyclic / non-confluent set at admission** — catch it before a request hits it. Not fully decidable for data-conditioned mutations, so the execution guard is the backstop.
- **The cross-domain guard** — at a crossing, policy may **transform** (redact / mask / constraint-narrow / sanitize), not only permit/deny. **Egress is field-granular**: release a subset via the coordinate (a projection mask — release `dc-east.network.*`, redact `location.residency`, deny `power.*` in one crossing). Net-new sanitizing + partial-release behavior over ADR-006/011.
- **Crossing enumeration + directional gate placement** — instrument every governed crossing (assembly-into-spec, egress-to-peer/federation, provider-handoff, external-export) with the **egress + ingress pair**, each in its own policy domain. The provider edge (ADR-023) and the federation wire (ADR-025 §3) are two such crossings.
- **Profile-governed posture** — **boundary-mediation** (mediate crossings, not internal reads) by default; a high-assurance / `sovereign` profile dials up to **complete mediation** (the guard on every access). A profile-set posture over ADR-006 + ADR-014.

**3. Directional gates sit at DCM's existing crossings.** The egress gate is the *last* DCM decision before data leaves a domain (peer wire, provider handoff, export); the ingress gate is the *first* on receipt (naturalization-in, ingestion, a projected value admitted into a spec). Sovereignty/tenancy fire at egress (ADR-011/014); trust/provenance fire at ingress (ADR-022/017). **`PROJ-P6`** (ADR-041) — the ingress admission of a projected value — is the receiver-side gate DCM places at assembly-into-spec.

**4. The wire stays flat, and the guard runs before it.** DCM still exchanges the **resolved effective schema** with peers (ADR-025 §3). The federation **egress guard** applies *before* serialization — release / redact / deny field-by-field — so what crosses the wire is already the sanitized projection, never the pre-guard form. Consistent with the compatibility rule (ADR-021, UDLM ADR-008).

## Consequences
- **No new engine is required** — the firewall is realized by organizing existing engines (policy, sovereignty, tenancy, trust, naturalization, reference-resolution) into the flow role, plus the guard (its own follow-on) and structural-match/re-convergence extensions.
- The **change-impact graph (ADR-024) gains a second consumer**: structural policy matching and policy re-convergence, alongside spec blast-radius. One graph, three readers.
- **Policy-input provenance** is a new capture obligation (extends the provenance already kept for spec values).
- **Field-granular egress / partial-release** is the one genuinely net-new mechanism — a firewall rule with a projection mask on the §10 coordinate.
- **Deterministic convergence is a hard requirement, not best-effort** — it is what makes a realized request **reproducible and replayable** (audit; the dual-anchor / rehydration guarantees). Cycle/non-determinism detection (execution + injection) is how the engine enforces it.
- Ties **sovereignty & tenancy** to concrete **egress** gates and **trust / provenance / FSI** to concrete **ingress** gates — enforceable at named crossings rather than by prose. DCM must **not** force all data through the policy engine (UDLM ADR-041 Option A, rejected) — boundary-mediation is the default; the profile dials strictness.

## Data · Policy · Provider
- **Data** — the flows and their provenance (spec-value *and* policy-input provenance); DCM authors none of the contract.
- **Policy** — the firewall/guard itself: the enforcement decision at every crossing. This ADR *is* the Policy leg for the flow role.
- **Provider** — the provider edge is a governed crossing (ADR-023); realization honors the disposition (released / redacted / denied) the guard emits.
