# Architecture Decision Records

Short, reviewable summaries of the major architectural decisions in DCM. Each ADR answers **"Why does this exist and what does it do?"** — not implementation details.

**Required lens (every ADR / DecisionRecord).** Each decision MUST state its **Data · Policy · Provider** aspects — the three foundational abstractions (ADR-002). *Data* = what's modeled/held (UDLM); *Policy* = what's decided/computed/governed (DCM); *Provider* = what's declared as possible and what executes the mechanism. A decision that can't name all three (or explicitly say "n/a, because…") isn't fully scoped. This is foundational across UDLM and DCM (and any consumer).

**Reading order:** ADRs 001-003 establish the foundations. Read those first, then jump to whichever ADRs are relevant to your area.

> **ADRs and the UDLM `DecisionRecord`.** These ADRs are the human-authored, prose form of "why the architecture
> is the way it is." UDLM defines that same WHY as a first-class, machine-trackable record type — the
> **`DecisionRecord`** in the Knowledge entity-type family (`udlm/entities/knowledge-family.md` §4.5) — anchored to
> the capability/decision it justifies, paired with [Audit & Tamper Evidence](010-audit-tamper-evidence.md) and
> field-level provenance ([ADR-012](012-data-assembly-layering.md)). A `DecisionRecord` is the substrate-level,
> **validation-backed** counterpart of an ADR (it reaches `CANONICAL` only with passing use-case validation); the
> authoring/validation loop is realized by a conformant assessment realization (non-normative; nothing here depends on a specific tool). Adopt-by-reference per
> [ADR-021](021-adopting-external-standards.md): DCM records its decisions *as* UDLM DecisionRecords rather than a
> parallel form.

**DecisionRecord scope & validation.** A `DecisionRecord` is **scoped** (Data·Policy·Provider): **architecture-scoped** records are these ADRs; **policy-scoped** and **provider-scoped** records capture the *why* of a policy or a provider/capability adoption. A record reaches `CANONICAL` via **scope-appropriate validation** — *architecture:* use-case / conformance validation; *policy:* Policy-Engine validation + **Shadow Mode** (a `proposed` policy evaluated against real traffic, never applied); *provider:* attestation verification + conformance. This is **distinct from runtime decisions** (a policy firing, a provider selection), which are captured as **Audit + provenance** ([ADR-010](010-audit-tamper-evidence.md)), **not** DecisionRecords — a DecisionRecord is the deliberate *why* (authoring time, any scope); audit is *what happened* (runtime). The validation runner is therefore not one component but the scope's existing mechanism (conformance / Shadow Mode / attestation verification) — DCM-owned, no external dependency.

| ADR | Decision | One-Line Summary |
|-----|----------|-----------------|
| [001](001-why-dcm-exists.md) | Why DCM Exists | Unified management plane for on-prem infrastructure — the governance layer above provisioning tools |
| [002](002-three-abstractions.md) | Three Foundational Abstractions | Everything in DCM is Data, Provider, or Policy — no exceptions |
| [003](003-four-lifecycle-states.md) | Four Lifecycle States | Intent → Requested → Realized → Discovered — immutable states linked by entity_uuid |
| [004](004-service-catalog-consumer-experience.md) | Service Catalog & Consumer UX | Four-level hierarchy from resource types to catalog items; consumers declare what, not how |
| [005](005-provider-abstraction.md) | Provider Abstraction | Unified provider model with capability declarations; bidirectional discovery; any platform, same interface |
| [006](006-policy-engine.md) | Policy Engine | Policy-as-code on every request; 8 policy types from gating to orchestration flow |
| [007](007-placement-engine.md) | Placement Engine | Multi-stage scoring: sovereignty pre-filter → capability → capacity → policy scoring |
| [008](008-dependency-resolution.md) | Dependency Resolution | Type-level dependencies trigger automatic sub-requests; binding fields inject runtime values |
| [009](009-api-gateway-control-plane.md) | API Gateway & Control Plane | Single entry point routing to 9 internal services; deterministic pipeline |
| [010](010-audit-tamper-evidence.md) | Audit & Tamper Evidence | Merkle tree (RFC 9162) with configurable granularity; mathematically provable integrity |
| [011](011-sovereignty-data-residency.md) | Sovereignty & Data Residency | First-class enforcement on every lifecycle operation; dual-approval for overrides |
| [012](012-data-assembly-layering.md) | Data Assembly & Layering | Organizational data merges with consumer requests; field-level provenance on everything |
| [013](013-override-exception-governance.md) | Override & Exception Governance | 5 mechanisms from planned exceptions to dual-approval; governance with flexibility |
| [014](014-multi-tenancy-isolation.md) | Multi-Tenancy & Isolation | PostgreSQL RLS enforces tenant isolation at the database layer |
| [015](015-minimal-infrastructure.md) | Minimal Infrastructure | PostgreSQL is the only required dependency; everything else is optional |
| [016](016-application-definition-language.md) | Application Definition Language | **OPEN** — How should consumers define multi-resource applications? Options under evaluation |
| [017](017-brownfield-greening-discovered-ingestion.md) | Brownfield Greening / Discovered Ingestion | Bring existing resources into the four states — two discovery avenues (provider / 3rd-party), Discovered store holds unclaimed, reverse placement → claim → Realized, optional Intent backport; correlation IDs dedup the same resource across sources |
| [018](018-wire-serialization-event-conventions.md) | Wire Serialization & Event Conventions | snake_case payloads end-to-end (AEP-conformant; Go json tags, Python Pydantic native — no alias generator); CloudEvents envelope; event topics use lowercase dot-notation for broker wildcard routing — the runtime side of UDLM's data-model casing |
| [019](019-placement-policy.md) | Placement Policy | The 8th typed policy — declarative affinity/anti-affinity/spread/co-locate/pin over abstract `Topology` kinds; engine evaluates; enforces portability. Consumes UDLM ADR-001/002/004 |
| [020](020-migration-and-operational-gating.md) | Migration & Operational Gating | Migration permission (Governance-Matrix) + sequence (Orchestration-Flow) + freshness gating (compliance Validation) + rehearsal scheduling — reuses existing policy types; control-plane side of UDLM ADR-003/004 |
| [021](021-adopting-external-standards.md) | Adopting External Standards | Adopt (reference) standards like FOCUS/OpenCost/OSCAL/SCIM — don't absorb; providers declare version support, DCM negotiates |
| [022](022-trust-model.md) | DCM Trust Model (incl. Credential API Selection) | Uphold·participate·expose a full trust model across 5 planes (PKI/mTLS, OAuth/OIDC, credential issuance, attestation, federation); DCM is a trust **broker**, not a credential authority; credentials brokered like placement (declare→select→attest, value direct CPX-001); security/trust/fit > portability; market-graded by profile; self-attested |
| [023](023-provider-naturalization-boundary.md) | Provider Naturalization Boundary | Generic intent + data in, mechanism hidden, generic denaturalized results out; naturalized/native forms are never Data; the provider owns naturalize/denaturalize (UDLM ADR-008) |
| [024](024-reference-resolution-and-change-impact.md) | Reference Resolution & Change-Impact Cascade | DCM resolves data references into the payload at assembly; consumes UDLM's transitive impact map; the cascade action (bump dependents) is a profile-governed policy (notify → propose → auto-adopt), never automatic — the policy counterpart to UDLM ADR-012 |
