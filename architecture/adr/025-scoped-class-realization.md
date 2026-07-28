# ADR-025: Realizing the scoped-Class paradigm

**Status:** Accepted (croadfeldt upstream) — downstream adoption pending eng alignment
**Date:** 2026-07-21

## Context

UDLM **ADR-038** lands the *scoped resource-type Class* paradigm: resource types are layered **Base / Type / Provider Classes** composed of scoped `SharedDataElement`s, with a URL-native addressing coordinate, a dual-anchor reference model, and the *is-a* / *has-a* relationship axes. The third axis (**references-context**), field projection along edges, and `covers`/`skip` layer scoping were extracted to **UDLM ADR-054**. Their shared UDLM-vs-DCM split (the ADR-008 peer test) assigns the **model, grammar, classification, and data** to UDLM and the **engine — every *decision*** to DCM.

This ADR records **where that engine half lives in DCM**. The important finding: it is *mostly already here*. The paradigm is a cleaner data model over the realization engines DCM already has; only a few capabilities are net-new.

## Decision

**1. The paradigm's DCM responsibilities map onto existing engines.**

| Paradigm engine responsibility (UDLM ADR-038) | DCM home |
|---|---|
| Resolve the Class path (pick Type / Provider / instance from an eligible **set**) | Placement (ADR-007, ADR-019) — extended to Class-path resolution |
| Policy-fill type/provider-specific blanks (consumer-set ≻ policy-fill ≻ provider-default) | Policy engine (ADR-006) + override/exception governance (ADR-013) |
| Assemble layers (gather-by-`covers`, precedence, override, `narrow_only`), authorize `skip` | Data assembly / layering (ADR-012) + override governance (ADR-013) |
| Resolve references; compute blast radius (`impact_report`); enforce repoints | Reference resolution & change-impact (ADR-024) |
| Naturalize generic ↔ native (Provider Class realization) | Provider naturalization boundary (ADR-023) |
| Migration / rehydration on re-port | Migration & operational gating (ADR-020) |
| Ingest / promote vocabularies (`proposed → canonical`) | Brownfield greening / discovered ingestion (ADR-017) — extended per UDLM ADR-039 |
| Audit records; sovereignty gate at resolve | Audit & tamper-evidence (ADR-010); sovereignty & residency (ADR-011) |

**2. DCM is the domain for the non-canonical *definitions* — classes and layers — as a policy/profile feature.**

UDLM defines the Base/Type Class **spec** and the layer contract, ships the **canonical** Base/Type library, and **instructs DCM** what to do with instances of them (UDLM ADR-038, *Authorship & domain*). The definitions that fill those specs — provider- and org-authored — live and are governed here:

- **Provider Classes are provider-authored.** A `Compute.VM.OCPVirt` definition is a provider-created artifact. DCM registers it, validates it Liskov-conforms to its Type Class (the contribution gate), and exposes it for Class-path resolution and capability matching (extends ADR-023 + ADR-022).
- **Organizations may author their own Base, Type, and Provider classes — a policy/profile feature.** When the canonical library lacks a type, an org authors its own class (any layer) **under its own authority** (`acme.example/Compute.VM`), never shadowing canon; portability is authority-scoped, promotable to canon when proven. DCM accepts it through the **same** contribution path, **governed by org policy/profile** — who may author and promote (ADR-006/013 + ADR-022). UDLM defines the spec and instructs; **DCM implements the feature.**
- **Data-layer definitions are organization-level.** The layer *contract* (`covers`/`skip`/precedence/`narrow_only`) is UDLM; *which* layers exist and what they hold — an org compliance overlay, a Data-Center info bundle — are org implementation details DCM stores, **binds** to groups/tenants/requests, and assembles (ADR-012/013).
- **One contribution lifecycle over all of them.** Classes (any layer), data layers, and `SharedDataElement`/vocabularies run through **one** DCM pipeline — **register → validate against the UDLM spec for that kind → bind/resolve → promote (`proposed → canonical`)** — the same process, differing only in the **data spec** (Class spec, layer contract, element spec). This **subsumes vocab ingest (ADR-039) and Provider-Class registration into one engine**; policy/profile-driven, trust-gated (ADR-022).
- **DCM MAY ship examples or defaults** — a starter class, a default compliance layer — as conveniences, never as canon; an org overrides them. This is DCM content, not UDLM content.

**3. Net-new DCM work (small):**
- **The one contribution lifecycle** — register → validate-against-the-UDLM-spec-for-that-kind → bind/resolve → promote (`proposed → canonical`, incl. the ≥2-adopter promotion), applied uniformly to **classes (any layer), data layers, and `SharedDataElement`/vocabularies**; policy/profile-driven, trust-gated. **One engine, parameterized by data spec** — subsumes the former per-kind registration and vocab-ingest (extends ADR-017 + ADR-023 + ADR-006/013 + ADR-022).
- **Usage data for org-driven promotion — the engine informs; the organization decides and acts.** Promotion is an **organization action, not an engine one.** The engine may **provide usage / data-element data on request** — only with the responsible organization's **express consent and knowledge**, through the visibility governance of the information firewall (DCM ADR-027 / UDLM ADR-041) — and the org uses it to decide; the engine never proposes, reports unsolicited, or auto-promotes:
  - **Missing Base/Type classes.** On request, the engine can report which org-authored classes fill a canonical gap (a class the library lacks, held under the org's authority) — so the **org** may choose to pursue promote-to-canonical ("author for promotion"; UDLM ADR-038 *Naming depth*).
  - **Recurring Provider-Class elements.** On request, the engine can report how widely a `SharedDataElement` (by `(scope, name, schema)`) is carried across Provider classes (the ≥2-adopter usage signal) — so the **org** may choose to promote it upward to a Type/Base canonical element (UDLM ADR-038 §6 *gated upward contribution*).
  - **Consent, not surveillance.** Usage that spans providers, tenants, or organizations is **not** surfaced without the **express consent and knowledge of the responsible organization** — the same visibility governance as any cross-party data. The engine supplies data; the organization owns the decision and the action.
- **Class-path resolution** — Placement resolves a Base/Type Class request down to a concrete Provider Class + instance across the eligible *set*, by requirements + advertised capability + policy (extends ADR-007/019).
- **Requirements ↔ capability matching** — for requirements-based selection (storage, UDLM ADR-036) and portable-vocabulary membership (UDLM ADR-035).
- **The governed federation resolver** — resolving rooted addresses across peers/tenants/jurisdictions with the sovereignty gate at the wire (UDLM **ADR-040** stub; extends ADR-011 + ADR-024). Demand-driven, `peer` root first.

**4. The wire stays flat.** DCM exchanges the **resolved effective schema** (Base ⊕ Type ⊕ Provider, flattened) with peers, never the layered form — consistent with the compatibility rule (ADR-021, UDLM ADR-008).

## Consequences
- No new engine is required — the paradigm is realized by extending existing DCM engines, plus the federation resolver (its own follow-on, demand-driven).
- Addressing/query/filter are one mechanism (the coordinate predicate); DCM must not introduce a parallel selector/query construct (UDLM ADR-038 design criteria).
- Amends nothing structural in DCM; it *organizes* existing realization responsibilities under the paradigm and names the incremental work.

## Data · Policy · Provider
- **Data** — DCM consumes the UDLM Base/Type model, coordinate grammar, and layer contract; it authors none of *those*. But the **Provider-Class and data-layer definitions are DCM-domain** — provider- and org-authored, registered and governed here (Decision 2).
- **Policy** — placement, policy-fill, assembly, promotion, matching, skip/repoint gating, sovereignty.
- **Provider** — naturalization at the Provider-Class edge; capability advertisement.
