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

### Writing standard — concise, clear, contextual, complete as minimally needed

The default for every ADR and document. Cold-reader-openable and *less is more* are one standard,
reconciled by **orienting, not re-teaching**: point to where foundational context lives, then stay
on the decision.

- **Background belongs in foundational documents, referenced — not inlined.** A definition or prior
  decision a reader needs lives in its home doc; this one links to it with a one-line gist and does
  not reproduce it. Open every document with an on-ramp — a **"Background — read first"** block
  (ADRs) or a *read-first* pointer (other docs): the foundational reading a third party needs, each
  cited once with what it settles, labeled so a reader who has the context skips it.
- **Complete as *minimally* needed.** Include exactly what moves the decision or task; cut the rest —
  including a point another section already made, and rhetorical flourish. Precision is never cut.
- **Know what the document *is* (Diátaxis).** Explanation (an ADR — *why*), reference (a
  schema/spec — *what*), how-to, or tutorial. Don't blend modes — an ADR *points to* the schema, it
  doesn't reproduce it; mode-blending is the main source of bloat.
- **References carry their gist** — never a bare number; one line on what it settled.
- Decision records are **immutable once Accepted** — superseded, not edited.

This mirrors the UDLM authoring standard (`CONTRIBUTING.md` DOC-001) so the two repos read the same.

## Licensing

By contributing to DCM you agree your contributions are licensed under Apache License 2.0, matching the
project license.
