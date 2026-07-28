# ADR-024: Reference Resolution & Change-Impact Cascade

**Status:** Proposed
**Date:** July 2026
**Docs:** UDLM ADR-012 (Data References — the data side); [ADR-012](012-data-assembly-layering.md) (Data Assembly & Layering); [ADR-006](006-policy-engine.md) (Policy Engine); [ADR-011](011-sovereignty-data-residency.md)

## Context

UDLM lets a field reference shared, governed data by object reference — `{ref_uuid, ref_name, ref_version, reference_data_type}` pointing at an immutable Reference Data Layer version — instead of inlining a copy (UDLM ADR-012). Referenced entities are immutable: a change mints a new version (new uuid), and lineage is a single explicit `supersedes` DAG. That is the **Data**. Two things are left for DCM (**Policy**): *when* references are resolved into a request payload, and *what to do* when referenced data a live payload was built against is later superseded — the change-impact question ("a library embedded in a container image is bumped; what is affected?").

The trap is auto-cascade: quietly re-minting dependents when referenced data changes. That rewrites authored intent (someone pinned a version deliberately), assumes forward-compatibility that may not hold, and fans a single base change into an unreviewable blast radius. So impact and action must be separated.

## Decision

**1. DCM resolves references at assembly time.** During payload assembly (ADR-012), the assembly engine dereferences each `ref_uuid` to its immutable Reference Data Layer version and injects that version's structured data into the payload, recording the reference (uuid + version) as the field's provenance. Because the target is immutable, resolution is deterministic and reproducible. A **retired** target is refused at resolution; a merely superseded one resolves normally (the pin is honored — immutability).

**2. Change-impact is consumed, not computed.** UDLM derives the impact map from the `supersedes` DAG + the reverse reference graph, cascading transitively (deployment → image → library). DCM **consumes** that map; it does not maintain a parallel lineage. Impact is advisory data — surfacing it changes nothing.

**3. Acting on impact is a governed cascade policy — never automatic.** Whether and how to move a dependent off a superseded version is an 8th-family Policy decision (ADR-006), profile-governed along a spectrum:
- **notify** — surface the impact map to the referrer's owner (default; the only floor for sovereign/fsi).
- **propose** — open a new-version PR/change for the owner to review and approve (GitOps).
- **auto-adopt** — mint the dependent's new version automatically. Permitted **only** under an explicitly permissive profile (e.g. dev), **never** sovereign/fsi, and never across a major-version bump of the referenced data.

The referrer's **owner** decides; the referenced data's change never rewrites a dependent's intent by itself. Cascade runs as an ordinary policy evaluation (auditable per ADR-010), and any adopted change is a normal new immutable version — not an in-place edit.

## Data · Policy · Provider (required lens)

- **Data (UDLM)** — the reference shape, the immutable Reference Data Layer versions, the `supersedes` lineage DAG, and the derived transitive impact map (UDLM ADR-012). DCM adds no lineage data of its own.
- **Policy (DCM)** — resolves references into the assembled payload with provenance; consumes the impact map; runs the profile-governed cascade policy (notify → propose → auto-adopt); refuses retired targets and gates deprecated ones per profile.
- **Provider** — n/a for lineage: a provider receives the **naturalized payload with references already resolved and injected** (ADR-023), never raw references, and never resolves or cascades. Its declared capability set is unaffected.

## Options considered

- **(A) Auto-cascade in the substrate** — UDLM auto-bumps dependents when referenced data changes. Rejected: rewrites authored intent, crosses the UDLM/DCM boundary (data mutating on a policy trigger), and creates unbounded blast radius.
- **(B) No cascade support — manual only** — ignore the impact map. Rejected: drift becomes invisible; the map is cheap, and "who is pinned to a superseded base?" is exactly the security/compliance question operators must answer.
- **(C) [chosen] DCM resolves references + consumes UDLM's transitive impact map + a profile-governed cascade policy (notify → propose → auto-adopt)** — impact is advisory data, action is a governed decision.

## Consequences

- **+** Impact ("who is behind on a superseded base") is answerable across the whole graph, transitively, without mutating anything — the input to security/compliance action.
- **+** Intent is never silently rewritten: moving a dependent forward is always an owner-approved (or profile-permitted) new immutable version, auditable like any other.
- **+** The floor is safe — sovereign/fsi only ever *notify*; auto-adoption is opt-in and profile-scoped.
- **−** Owners must act on notifications; the platform will surface pinned-to-superseded references but not fix them for regulated tenants. That is the intended trade (no silent auto-upgrade of governed intent).
- Pairs with ADR-012 (assembly/provenance) and ADR-023 (references resolved before the provider boundary).
