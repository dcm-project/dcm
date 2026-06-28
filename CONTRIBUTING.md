# Contributing to DCM

DCM — the Data Center Management control plane — is open-source under Apache License 2.0. Contributions
to the control plane, the provider ecosystem, and the architecture docs are welcome. The architecture is
captured in `architecture/`; the major decisions are recorded as ADRs in `architecture/adr/`.

## Subject-scoped pull requests (default)

The default unit of contribution is **one subject per PR** — a single, complete logical change, titled
by its subject (e.g. "Enable cost provider", "Adopt FOCUS 1.4 for cost", "Add EgressFirewall to the
namespace"). Keep PRs to roughly ≤2–3k lines; if a subject is larger, split it along logical boundaries
into a sequence of independently reviewable, subject-scoped PRs rather than forcing one oversized change.
Prefer logical boundaries over size-driven cuts, and never bundle unrelated subjects. Lead every PR
description with a short **Why** (the rationale), linking the ADR or requirement when one exists.

## Document the why

Every non-trivial change records its rationale, not just its diff:
- **Architectural decisions** get an ADR in `architecture/adr/` (next available number; follow the
  existing shape — Context, Decision, Alternatives Considered, Consequences). One decision per ADR;
  don't bundle.
- **Requirement changes** update the relevant requirement set (`dcm-platform-requirements.md` and the
  ID series — `ADS-`, `AUD-`, `RDG-`, …).
- A reviewer should be able to reconstruct *why* a change exists from the repo, not just *what* changed.

## Licensing

By contributing to DCM you agree your contributions are licensed under Apache License 2.0, matching the
project license.
