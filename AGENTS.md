# AGENTS.md — DCM

> Cross-agent context file ([agents.md](https://agents.md) standard). `CLAUDE.md` is a symlink to this
> file so Claude Code reads the same source of truth. Keep this current as the architecture evolves.

## What this repo is

**DCM — Data Center Management.** A vendor-neutral architecture specification for an intent-driven
control plane that provisions, governs, and rehydrates data-center resources. **DCM is one realization
of UDLM** (the Unified Data-center Lifecycle Model, `github.com/croadfeldt/udlm`) — understand the UDLM
substrate first; DCM is the control-plane architecture built on it.

**This is a docs/architecture-only repo — there is no application code** (no Go/Python/TS, no build).
The deliverable is the specification: Markdown architecture docs, machine-readable contracts (OpenAPI /
JSON Schema / SQL), ADRs, and a taxonomy. **Apache-2.0.**

## Layout

```
architecture/      Core architecture. ADRs (adr/ + README index), DCM-Capabilities-Matrix.md, and subsystem folders
                   (control-plane/, convergence-engine/, ingestion/, credentials-and-auth/,
                   governance-enforcement/, runtime-features/, topology/, persistence/, integrations/).
                   Entry docs: overview.md, layering.md, operator-perspective.md, design-principles.md.
docs/              Prose specifications/ (consumer-api-spec, dcm-admin-api-spec), engineering/
                   (ENGINEERING-ALIGNMENT.md), holistic-vision.md.
schemas/           Machine-readable contracts: openapi/ (consumer/admin/provider-callback/operator),
                   jsonschema/ (events, providers, entities, policies, resource-type template),
                   sql/001-initial.sql (18 tables).
reference/         implementation-standards.md, implementation-specifications.md, operational-reference.md.
taxonomy/          DCM-Taxonomy.md (the controlled vocabulary).
examples/          orchestration-scenarios.md. (Full examples live in the external dcm-project/dcm-examples repo.)
dav/               The DCM validation corpus/schemas DAV runs against (see croadfeldt/dav).
README.md, project-overview.md, LICENSE
```

## Read first (entry points)

1. UDLM substrate — `github.com/croadfeldt/udlm` (DCM is one realization of it).
2. `architecture/overview.md` → `architecture/layering.md` (the UDLM/DCM boundary).
3. `architecture/convergence-engine/overview.md` — the intent→realized loop, the heart of DCM.
4. `architecture/operator-perspective.md`, `taxonomy/DCM-Taxonomy.md`.
5. `architecture/DCM-Capabilities-Matrix.md` — what DCM can do.
6. `architecture/adr/README.md` + ADRs 001–016 — the decision history (the "why").

## Operating rules

- **Commits:** `--no-gpg-sign`, author = the repo owner's public git identity (match `git log -1 --format='%an <%ae>'`), trailer
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Commit subjects use a lowercase
  `scope: short description` prefix (`sov:`, `use-cases:`, `docs:`, `observability:`, …) where scope =
  the doc area touched.
- **PRs are subject-scoped** — one logical doc area per PR (≤2–3k lines; split larger subjects on logical
  boundaries). **Lead with the "why"** and capture decisions as **ADRs** in `architecture/adr/` (next
  number, one decision each) — that is this repo's document-the-why mechanism.
- **Remotes:** GitHub `croadfeldt/dcm` (origin) + `dcm-project/dcm` (upstream — the canonical project
  home; promote scoped PRs upstream). Default branch `main`; use `gh`.
- **Counts come from source artifacts, never summary blocks.** Summary blocks in this repo (e.g. README
  "Key Facts", the old onboarding doc) disagree with each other and with the actual files. When you need a
  number, read the artifact:
  - capabilities → `architecture/DCM-Capabilities-Matrix.md` total (311 across 39 domains)
  - SQL tables → `schemas/sql/001-initial.sql` (18)
  - events → the §65 Event Catalog / UDLM event-catalog (82 across 26 domains)
  - API paths → `schemas/openapi/dcm-consumer-api.yaml` (75) / `dcm-admin-api.yaml` (admin spec)
  - providers → declared **capabilities** `(verb × domain)`, not fixed types (ADR-PROV-002); the legacy "provider types" are convenience labels for capability profiles — see `croadfeldt/udlm` capability-discovery.md
  - policy types → 7, with 2 evaluation modes (Internal via OPA / External via provider)

## Terminology decisions (locked 2026-06-30)

These decisions are settled. Apply them in all documentation and use case authoring.

### Provider hierarchy

**Provider** is the generic interface — any external component that provides capabilities to DCM.
**Service provider** is one typed provider within that hierarchy (not the top-level name).
Other provider types include: information, credential, auth, peer_dcm, process, etc.
Each provider registers with the generic provider interface and declares its capabilities.
Do NOT use "resource provider" — that rename was proposed but reversed.

> **Refined by ADR-PROV-002 (2026-07-11):** a provider is **not a type** — it declares **capabilities**
> `(verb × domain)` and occupies non-exclusive **capability categories**; the "typed provider" names above
> are convenience labels for capability profiles, and policy targets a capability/category, never a provider
> type. See `croadfeldt/udlm` `capability-discovery.md` + ADR-PROV-002/003/004 + ADR-RBAC-001.

### Validation policy (merged)

**Gating Policy has been merged into Validation Policy.** There is no longer a separate "Gating Policy"
type. Validation Policy now carries two orthogonal properties:
- `enforcement_class`: `compliance` (boolean deny — halts request) or `operational` (contributes risk score)
- `output_class`: `structural` (boolean pass/fail) or `advisory` (warnings without blocking)

A validation policy with `enforcement_class: compliance` is what was previously called a "gating policy."
Do NOT use "gatekeeper policy" (OPA Gatekeeper collision) or "gating policy" as a standalone type.

### Composite service / resource

**Composite service** is DCM's native concept for multi-component architectural patterns.
Do NOT use "likeC4" as a DCM-native concept — likeC4 is a customer-specific format (PNC).
A *process provider* can convert likeC4 → composite service, but DCM does not natively speak
any customer-specific format. UDLM is the core design language; customer format converters
live outside the core.

### Realized (not fulfilled)

The lifecycle state where a resource exists and is provider-confirmed is called **Realized**.
Do NOT use "fulfilled."

## Exploring the architecture

Read the specs directly — the **Layout** and **Read first** sections above route you, and each concern has
one authoritative doc. The former `architecture/ai/DCM-AI-PROMPT.md` (a 5,950-line full-architecture
snapshot) was **retired**: it duplicated the specs and drifted stale — it still taught the pre-ADR-PROV-002
typed-provider model, among other things. Load the specific spec docs you need into context; nothing an
agent needs is more than one hop away via the map above.
