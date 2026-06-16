# Architecture Decision Records

Short, reviewable summaries of the major architectural decisions in DCM. Each ADR answers **"Why does this exist and what does it do?"** — not implementation details.

**Reading order:** ADRs 001-003 establish the foundations. Read those first, then jump to whichever ADRs are relevant to your area.

| ADR | Decision | One-Line Summary |
|-----|----------|-----------------|
| [001](001-why-dcm-exists.md) | Why DCM Exists | Unified management plane for on-prem infrastructure — the governance layer above provisioning tools |
| [002](002-three-abstractions.md) | Three Foundational Abstractions | Everything in DCM is Data, Provider, or Policy — no exceptions |
| [003](003-four-lifecycle-states.md) | Four Lifecycle States | Intent → Requested → Realized → Discovered — immutable states linked by entity_uuid |
| [004](004-service-catalog-consumer-experience.md) | Service Catalog & Consumer UX | Four-level hierarchy from resource types to catalog items; consumers declare what, not how |
| [005](005-provider-abstraction.md) | Provider Abstraction | Unified provider model with capability declarations; bidirectional discovery; any platform, same interface |
| [006](006-policy-engine.md) | Policy Engine | Policy-as-code on every request; 8 policy types from gatekeeping to orchestration flow |
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
