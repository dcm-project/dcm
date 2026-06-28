## SECTION 0 — THE THREE FOUNDATIONAL ABSTRACTIONS (READ FIRST)

DCM is built on three foundational abstractions. Every concept maps to one or more of these three. There is no fourth.

### DATA — Everything That Exists
Any structured artifact with a type, UUID, lifecycle state, fields, data classification, and provenance. Entities, layers, policies, accreditations, audit records, groups, relationships, sovereignty zones, registration tokens — all Data.

**Universal Data properties:** UUID (stable across full lifecycle) · typed · lifecycle state · artifact metadata (handle, version, status, owned_by) · field-level provenance · data_classification per field · immutable if versioned

**Data lifecycle stages (four states):** Intent State (consumer declaration) → Requested State (assembled, policy-validated) → Realized State (provider-confirmed) → Discovered State (independently observed). These are the same entity at four lifecycle stages stored in different stores optimized for each access pattern.

**Data is assembled via layers** in deterministic precedence order. Every field carries provenance of its origin and all modifications.

### PROVIDER — Everything External
Any external component DCM calls or that calls DCM. All providers implement the **unified base contract** (registration, health, sovereignty, accreditation, governance matrix enforcement, zero trust) plus a **typed capability extension** that declares what operations they expose.

**Five provider types (all implement the same base contract):**
Service Provider (realize resources — including Credential.*, Notification.*, ITSM.* resource types) · Information Provider (serve authoritative external data) · Auth Provider (authenticate identities) · Peer DCM (federation — another DCM instance IS a typed provider) · Process Provider (execute workflows without producing resources)

**Adding a new provider type** = implement base contract + define capability extension. No core changes.

### POLICY — Everything That Decides
Any rule artifact that fires when Data matches conditions, produces a typed output, and is enforced at a declared level. Policies govern every transition, transformation, and constraint.

**Eight policy types (all implement the same base contract):**
Gating Policy (allow/deny) · Validation (pass/fail) · Transformation (field mutations) · Recovery (failure actions) · Orchestration Flow (pipeline ordering) · Governance Matrix Rule (boundary control) · Lifecycle Policy (relationship event actions) · ITSM Action (side-effect ITSM record creation)

**Policies ARE the orchestration.** Pipeline steps are policies firing on payload type events. Static flows = Orchestration Flow policies with `ordered: true`. Dynamic flows = conditional policies. Adding/removing pipeline steps = adding/removing policies.

**Adding a new policy type** = define a new output schema. Base contract inherited automatically.

### THE RUNTIME — Connecting the Three
```
Event (Data state change)
  → Policy Engine evaluates all matching Policies
  → Policies produce decisions / mutations / actions
  → Actions invoke Providers or produce new Data
  → New Data triggers new Events
  → Repeat
```

Control plane "components" are runtime specializations — not a fourth abstraction:
- Request Orchestrator = event bus (runtime)
- Policy Engine = policy evaluator (runtime)
- Placement Engine = Gating policy specialized for provider selection
- Cost Analysis = Information Provider (internal; data derivation)
- Lifecycle Constraint Enforcer = scheduled Recovery Policy trigger
- Discovery Scheduler = scheduled Provider invocation
- Notification Router = Transformation Policy + notification service invocation
- Drift Reconciliation = Data comparison producing Drift Record artifacts
- Search Index = PostgreSQL store contract (queryable projection)

### THE CORE ETHOS
Effective at the core mission · Easy to use · Easy to implement · Easy to extend and integrate

**Foundation documents:** 00-foundations.md (three abstractions) · A-provider-contract.md (unified provider base) · B-policy-contract.md (unified policy base)

---

# DCM Project — AI Model Prompt Script

**Purpose:** This script provides an AI model with the full context needed to participate effectively in DCM project work. It should be provided at the start of any AI-assisted session involving DCM architecture, documentation, code, or design work.

**Usage:** Paste this document into the AI model's context at the start of a session. Follow with the specific task or question.

**Maintainers:** Update this document whenever significant architectural decisions are made, new concepts are established, or open questions are resolved.

**Last Updated:** 2026-03  
**Status:** Architecture complete — 0 unresolved questions — Ready for implementation

**Note on section structure:** This prompt was built cumulatively across multiple design sessions. Sections 0–57 establish the architecture. Sections 58+ record subsequent additions and refinements. Capability counts, path counts, and domain counts in earlier sections reflect the state at the time that section was written. The authoritative current counts are: **331 capabilities across 39 domains · 59 data model docs · 12 specifications · 16 ADRs · 75 consumer API paths · 61 admin API paths · 109 event payloads across 23 domains · unified provider model (5 capability types) · 2 policy evaluation modes · 9 control plane services · 105 prompt sections.** When earlier sections conflict with later sections, the later section is authoritative. **Infrastructure (doc 51):** Unified provider model — providers declare capabilities: realize_resources, serve_data, authenticate, federate, execute_workflows. Multi-capability providers register once. Bidirectional capability discovery via GET /api/v1/capabilities. 2 policy evaluation modes: Internal (DCM evaluates via OPA) and External (external provider evaluates). Four data domains (Intent, Requested, Realized, Discovered) in a single PostgreSQL-compatible database. One required infrastructure: PostgreSQL-compatible DB. Authentication (local accounts + JWT), secrets (envelope encryption), and event routing (LISTEN/NOTIFY) are handled internally. OIDC IdP, Vault, Kafka, Redis, Git are optional deployment enhancements. 9 control plane services.

---

## SECTION 0b — DESIGN PRIORITY ORDER (applies to all decisions)

> **Full specification:** [00-design-priorities.md](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md) — includes decision framework, profile scaling table, and DPO-001–006 system policies.

**Priority 1 — Security (industry best practices):** Security properties are architecturally present in ALL profiles. What profiles control is enforcement strictness, threshold values, and automation level — not whether security applies. A `minimal` profile is "security with minimal operational overhead" — not "minimal security."

**Priority 2 — Ease of use:** The secure path must be the easy path. If the right path is also the hard path, teams will find other paths. Auto-approval for ordinary requests, policy authoring without Rego expertise, and profile defaults that eliminate configuration burden all serve this priority.

**Priority 3 — Extensibility/grouping:** Profile system, compliance domain overlays, policy groups, and registry governance enable adaptability through configuration, not code. New compliance requirements are policy additions. New deployment contexts are profile configurations.

**Priority 4 — Fit for purpose (always required):** DCM must manage data center infrastructure lifecycle end-to-end. Everything above serves this purpose. A system that cannot provision, track, and decommission a VM has failed.

**Implication for all design decisions:** When security and convenience conflict, security wins — but find a way to make the secure option easy. When extensibility and fit for purpose conflict, fit for purpose wins. When a profile tempts you to disable a security property rather than raise its threshold, the priority order says: keep the property, raise the threshold.

---

## SECTION 1 — PROJECT IDENTITY

You are assisting with the **DCM (Data Center Management)** project, an open-source strategic framework developed by the Red Hat FlightPath team developed by the Red Hat FlightPath Team.

**Key facts:**
- DCM is NOT a provisioning tool — it is a **governing framework**
- DCM is a **top-down orchestration and policy enforcement layer**
- DCM enables enterprises to achieve a "Private Cloud" / "Sovereign Cloud" experience with public cloud efficiencies on-premises
- DCM is **API-first, data-driven, and policy-governed**
- DCM is inspired by Kubernetes' declarative control plane model
- GitHub: https://github.com/dcm-project
- Website: https://dcm-project.github.io

**Authors:** Chris Roadfeldt (Principal Architect), Ryan Goodson (Senior Principal Architect), Adam Seeley (Global Director) — Red Hat FlightPath.

**Vision:** To make life better for all customers, internal teams, and future-looking entities.

**Mission:** Seamlessly manage the complete lifecycle of all data center infrastructure by providing a policy-governed, data-driven, and unified platform to enable and ensure sovereignty.

---

## SECTION 2 — THE PROBLEM DCM SOLVES

Organizations face these core challenges that DCM addresses:

1. **Fragmented Operations** — disparate tools, no unified management, functionality trapped in monoliths
2. **No Single Source of Truth** — multiple CMDBs diverge, no trustworthy representation of infrastructure state
3. **High Time-to-Market** — a single VM lifecycle may be managed by dozens of teams; firewall changes can take weeks
4. **The Private Cloud Gap** — "Private Cloud" ≠ "On-Premises Compute"; a true private cloud requires networking, storage, identity, catalog, FinOps, observability, auditing, and risk management
5. **Drift and State Discrepancy** — no reconciliation between discovered inventory and intended inventory
6. **Sovereignty Requirements** — organizations must enforce data residency, compliance, and operational control across their infrastructure

**The definitional clarification DCM makes:**
- Private Cloud ≠ On-Premises Compute
- Private Cloud > On-Premises IaaS
- Private Cloud = Hyperscale experience for on-premises infrastructure

---

## SECTION 3 — FOUNDATIONAL PRINCIPLES

These three constraints apply to ALL data, entities, and operations in DCM **universally and without exception:**

### 3.1 Declarative
Data describes **what something is or should be**, not how to achieve it. Every entity is a complete, self-describing statement of state. The procedures required to achieve that state are the concern of the Service Provider, not the data model.

### 3.2 Idempotent in Operation
Applying the same data to the same system multiple times must always produce the same result. No operation on DCM data should have different outcomes based on how many times it has been applied.

### 3.3 Immutable if Versioned
Once a version of any entity is published, it cannot be modified. Changes produce a new version. Previous versions remain intact and accessible forever.

---

## SECTION 4 — THE DCM DATA MODEL

**The data model is the most foundational element of DCM.** Everything in DCM acts on data in some way — reading, validating, triggering, enriching, gating, parsing, transforming, or comparing. The data model is the lingua franca — the API between all components.

### 4.1 Universal Identity Requirement
Every data object in DCM **must have a UUID**. This applies without exception to: resource definitions, catalog items, data layers, policies, policy sets, components, service providers, consumers, requests, and all other entities. UUIDs are used for provenance anchoring, dependency mapping, audit fidelity, and cross-state correlation.

### 4.2 The Four States
DCM tracks every resource through four distinct states. Together they provide complete visibility into what was wanted, what was asked for, what was built, and what actually exists.

| State | Description | Store | Created By |
|-------|-------------|-------|------------|
| **Intent** | What the consumer wants — raw declared desire before any processing | Intent Store | Consumer (Web UI / API) |
| **Requested** | Fully processed, policy-validated, enriched payload submitted to a provider | Request Store | Request Payload Processor |
| **Realized** | What was actually provisioned, returned by the provider in DCM unified format | Realized Store | Service Provider (via Denaturalization) |
| **Discovered** | What actually exists, as independently interrogated by a provider during discovery | Discovered Store | Service Provider (via Discovery) |

**Key operations across states:**
- **Drift Detection:** Discovered State vs. Realized State
- **Request Validation:** Requested State vs. Policy definitions
- **Intent Portability:** Intent State → re-process through current policies → new Requested State
- **Brownfield Ingestion:** Discovered State → enrichment → Realized State (lifecycle ownership)

**State lifecycle flow:**
```
Consumer Request → INTENT → (Policy Engine) → REQUESTED → (Service Provider) → REALIZED
                                                                                     ↕ compare
                                                              DISCOVERED ────────► Drift Detection
```

### 4.3 Field-Level Provenance and Data Lineage
This is a **structural requirement** of the data model — not a logging concern.

For any field, at any point in the pipeline, it must be possible to determine:
- What is the current value?
- Where did this value originate? (catalog item, layer, policy, consumer input, discovery)
- Has it been modified? If so — what changed it, which entity (by UUID), when, what was the previous value, and why?
- What is the complete chain of custody from origin to current value?

**Provenance is carried within the data object itself** — co-located with the data, not in an external log.

Every component that modifies data carries a **provenance obligation** — it must record its UUID, operation type, timestamp, and reason for every field it modifies. This is non-optional.

Conceptual provenance structure per field:
```yaml
field_name:
  value: <current value>
  metadata:
    override: <allow|constrained|immutable>
    basis_for_value: <human-readable — why this value was set>
    baseline_value: <original default before any override>
    locked_by_policy_uuid: <uuid — if constrained or immutable>
    locked_at_level: <global|tenant|user>
    constraint_schema: <JSON Schema — if constrained>
  provenance:
    origin:
      value: <original value>
      source_type: <catalog_item|base_layer|intermediate_layer|service_layer|policy|consumer|discovery|provider>
      source_uuid: <uuid>
      timestamp: <ISO 8601>
    modifications:
      - sequence: 1
        previous_value: <value before>
        modified_value: <value after>
        source_type: <policy|layer|component|provider>
        source_uuid: <uuid>
        operation_type: <enrichment|transformation|validation|gating|override|lock|grant>
        actor: <actor type that performed this>
        timestamp: <ISO 8601>
        reason: <human-readable>
```
The `metadata` block is set exclusively by the Policy Engine. `operation_type: lock` is used when a Gating Policy sets `override: immutable`. `operation_type: grant` is used when a trusted_grant is issued.

### 4.4 Universal Versioning
All entities, definitions, and data objects in DCM follow one versioning scheme: **Major.Minor.Revision**

| Component | Trigger |
|-----------|---------|
| **Major** | Breaking changes to the contract |
| **Minor** | Additive changes, backward compatible |
| **Revision** | Data/configuration changes, no contract impact |

This applies universally to: resource types, layers, policies, catalog items, provider registrations, registry entries, and all other definitions.

### 4.5 Universal Artifact Status Lifecycle
Every DCM artifact — layers, policies, resource types, catalog items, provider registrations — follows a five-status lifecycle:

| Status | Meaning | Applied? | Shadow? |
|--------|---------|---------|---------|
| `developing` | In development | No — dev mode only | No |
| `proposed` | Submitted for review/validation | No | Yes — policies shadow-execute against real traffic, output captured not applied |
| `active` | Live and governing | Yes | Yes — audit records |
| `deprecated` | Being phased out, replacement available | Yes — with warning | Yes |
| `retired` | End of life | No | No — terminal |

**Status transitions:** `developing → proposed → active → deprecated → retired`
Deprecated artifacts must include: replacement UUID, deprecation reason, migration guidance, sunset date.

**Previously:** The model had only `active → deprecated → retired`. The `developing` and `proposed` statuses were added to support the full artifact development workflow — especially the shadow execution validation model for policies.

### 4.6 Artifact Metadata Standard
Every DCM artifact carries a universal metadata block — applies to all artifacts without exception:
- `uuid` — immutable, DCM-assigned at creation
- `handle` — human-readable stable ID: `{domain}/{layer_type}/{name}` e.g. `platform/core/security-cpu-limits`
- `version` — Major.Minor.Revision
- `status` — five-status lifecycle (Section 4.5)
- `created_by` — audit record (who submitted): UUID optional + display_name required
- `owned_by` — accountability record (who is responsible, receives notifications): UUID optional + display_name required
- `created_via` — ingestion path: `pr | api | migration | system`
- `modifications` — append-only history of all changes with who/when/why

**Contact modes:** UUID+display_name when Identity Provider registered; display_name+email standalone/air-gapped. Both supported.

### 4.7 Provider Types
All five provider types follow the same base contract (registration, health check, trust, sovereignty, accreditation, governance matrix enforcement, zero trust, provenance emission). See Section 0 for the complete list. The four original categories and their data ownership model:

| Type | Purpose | DCM Owns Result? |
|------|---------|-----------------|
| **Service Provider** | Realizes resources — KubeVirt, VMware, AAP, Terraform | Yes |
| **Information Provider** | Serves authoritative external data DCM references but does not own | No — external system is authoritative |


The five provider types (service_provider, information_provider, auth_provider, peer_dcm, process_provider) all implement the same base contract. Capabilities that were formerly separate provider types (credentials, notifications, ITSM, message bus, storage, policy evaluation, registry) are now either internal to DCM or handled by service_providers with specialized resource types. See [A-provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) for the unified contract.

---

## SECTION 5 — THE FOUR STATES AND STORAGE MODEL

### 5.1 The Four States

Every DCM entity exists across four independently maintained state records:

| State | Question | Store Type | Characteristics |
|-------|----------|------------|----------------|
| **Intent State** | What did the consumer ask for? | GitOps | Immutable, branched, PR reviewed, CI/CD triggered |
| **Requested State** | What was approved and dispatched? | GitOps | Immutable, committed, CD triggered, full provenance |
| **Realized State** | What did the provider actually build? | Event Stream | Append-only, entity-keyed stream, high-frequency |
| **Discovered State** | What actually exists right now? | Event Stream (ephemeral) | Machine-generated, drift detection source |

### 5.2 Storage Architecture — Contract, Not Implementation

DCM defines store **contracts** — what capabilities, guarantees, and obligations each store must satisfy. Implementation technology is a deployment choice. PostgreSQL is the single required infrastructure.

```
GitOps Stores:        Intent, Requested, Layers, Policies
Event Stream Stores:  Realized, Discovered, Audit events
Search Index:         Queryable projection of GitOps stores (non-authoritative)
Audit Store:          Compliance-grade, immutable, long-retention
Observability Store:  Time-series metrics, traces, logs
```

### 5.3 The Entity UUID — Universal Key
The entity UUID is assigned at Intent State creation and links the entity across all four states and all stores. Given an entity UUID, DCM can reconstruct the complete lifecycle history from any store.

### 5.4 CI/CD Integration
GitOps stores are the natural CI/CD integration point:
- **CI pipeline** fires on branch/update: policy pre-validation (dry run), cost estimation, sovereignty check, auto-approve evaluation — results posted as PR comments
- **CD pipeline** fires on merge: layer assembly, full policy evaluation (binding), provider dispatch
- **Third rail — direct API ingress**: bypasses PR workflow, not governance. Same pipeline, no human review unless required by policy.

### 5.5 Rehydration — Three Sources, Six Modes

Rehydration uses a prior state record as the starting point for a new request. Governance always applies — rehydration is a new request, not a shortcut.

**Three sources:** Intent Store (full assembly runs), Requested Store (assembly skipped, governance runs), Realized Store (provider fields stripped, assembly skipped, governance runs)

**Two axes — six modes:**

| Mode | re_evaluate | policy_version | Use Case |
|------|-------------|----------------|----------|
| Faithful | false | current | Same provider, current governance |
| Provider-Portable | true | current | New provider, current governance |
| Historical Exact | false | pinned | Same provider, historical governance (audit evidence) |
| Historical Portable | true | pinned | New provider, historical governance |

**Placement flag on Requested/Realized rehydration:**
```yaml
placement:
  re_evaluate: false   # Honor original provider selection (default)
  # re_evaluate: true  # Strip provider, run placement policies fresh
governance:
  apply_all_policies: true  # Always true — never skippable
  policy_version: current   # current | pinned (pinned requires elevated auth)
```

**Named concept:** Provider-Portable Rehydration — rehydration with provider selection re-evaluated through current placement policies and current provider landscape.

**Partial Q54 resolution:** Policies set placement constraints. The placement component selects the specific provider within those constraints. Policies never name a specific provider — that would be portability-breaking.

### 5.6 Audit, Provenance, and Observability — Three Distinct Concerns

| Concern | What It Is | Audience | Retention |
|---------|-----------|----------|-----------|
| **Provenance** | Field-level data lineage embedded in every payload | System | Permanent — part of the data |
| **Audit** | Compliance-grade queryable record of all actions | Auditors, Compliance | Regulatory period (7+ years FSI) |
| **Observability** | Real-time metrics, traces, logs | SRE, Platform Engineers | Operational window (90 days) |

Audit is a **separate component** fed by provenance events emitted by all store contracts (contractual obligation). Surfaced through the DCM API Gateway — not a separate endpoint.

All DCM capabilities — catalog, requests, entities, policies, audit, observability — are surfaced through a **unified API Gateway hierarchy**.

---

## SECTION 6 — DATA LAYERS AND THE ASSEMBLY PROCESS

### 6.1 Layers vs Policies — The Clear Distinction

**Layers are data.** They carry static configuration, defaults, metadata, and context assembled into the request payload. A layer answers: "what values should these fields have?" Layers are passive — they declare values but do not execute logic. They come first in assembly (Steps 1-4).

**Policies are logic.** They evaluate the assembled payload and enforce rules, inject derived values, and make decisions. A policy answers: "given this data, is it valid? what should change? should this proceed?" Policies execute — they run code. They come after layers (Steps 5-9).

**The flow is strictly unidirectional:**
```
Steps 1-4: LAYERS assembled → merged payload produced (data)
Steps 5-9: POLICIES execute → payload evaluated and acted upon (logic)
```

**The decision rule:** Value that should appear in payload → Layer. Rule about whether payload is correct → Policy. Value derived by evaluating payload → Policy (Transformation type).

**What belongs in layers:** infrastructure defaults, organizational context, service configuration defaults, compliance metadata, business context labels.

**What belongs in policies:** validation rules, compliance enforcement, derived value injection, placement constraints, approval gates, security enforcement.

A policy that repeatedly injects the same static value into every request → that value belongs in a layer. A layer that contains conditional logic → that logic belongs in a policy.

### 6.2 Layer Domain Model (mirrors Policy domain)

| Domain | Authority | Can Override |
|--------|----------|-------------|
| `system` | DCM built-in — highest | Nothing above system |
| `platform` | Platform team | tenant, service, provider |
| `tenant` | Tenant Admin | service, provider within Tenant |
| `service` | Service Provider | provider |
| `provider` | Provider owner | Nothing above provider |
| `request` | Consumer — lowest | Nothing above request |

### 6.3 The Full Layer Structure

Every layer carries: artifact_metadata (standard), domain + priority (authority), concern_tags (discoverability), compatibility (resource_types, versions, profile_constraints), activation_condition (Q23 — conditional inclusion), fields with per-field override metadata (override: allow/constrained/immutable, basis_for_value), and usage context (description, applies_when, excludes_when, conflicts_with).

**activation_condition** — layer only included if condition evaluates true during Step 2. Conditions reference: request fields, tenant attributes, resource type fields, resolved core layer fields, ingress fields. Enables role-specific layers, GPU-only layers, PCI-scope-only layers.

### 6.4 Layer Groups

Layer Groups are `DCMGroup` with `group_class: layer_grouping` — cohesive collections of related layers. Same model as Policy Groups. Enables discovery ("show me all PCI compliance layers"), composition, and governance.

### 6.5 Consumer Layer Exclusion (Q21)

Consumers declare `layer_exclusions` with mandatory reason. Excluded layers removed in Step 2, produce no fields, cannot satisfy validation requirements. Gating policies may declare layers non-excludable (LAY-001).

### 6.6 Service Layer Versioning (Q22)

Service Layers independently versioned. Providers declare semver compatibility constraints (`^1.0.0`, `~1.2`). Cache entries carry version — invalidated when registered version changes (LAY-002).

### 6.7 Conditional Layer Inclusion (Q23)

`activation_condition` on layer evaluated in Step 2. False → layer excluded. Conditions reference request, tenant, resource type, core layer, and ingress fields. Recorded in assembly provenance (LAY-003).

### 6.8 Dependency Layer Chains (Q24)

Each service dependency has its own independent layer chain. Inherits parent's resolved placement fields (read-only). Does NOT inherit parent consumer declarations or type-specific layers. Layer exclusions declarable per-dependency (LAY-004).

### 6.9 The Nine-Step Assembly Process

Step 1 (Intent Capture) → Step 2 (Layer Resolution — with exclusions and activation_conditions) → Step 3 (Layer Merge — priority ordering, field-level provenance) → Step 4 (Request Layer Application) → Step 5 (Pre-Placement Policies: Transformation → Validation → Gating Policy) → Step 6 (Placement Engine Loop: reserve query + loop policy phase per candidate) → Step 7 (Post-Placement Policies) → Step 8 (Requested State Storage) → Step 9 (Provider Dispatch)

### 6.10 Layer System Policies
- `LAY-001` — Consumer layer exclusions with mandatory reason; Gating Policy can lock layers as non-excludable
- `LAY-002` — Service Layers independently versioned; semver compatibility on provider; cache invalidation on version change
- `LAY-003` — activation_condition on layers evaluated in Step 2; results recorded in provenance
- `LAY-004` — Each dependency has own layer chain; inherits parent resolved placement; no consumer declaration inheritance

## SECTION 7 — RESOURCE TYPE HIERARCHY AND SERVICE CATALOG

The Resource Type Hierarchy is how DCM achieves **resource portability** — expressing what a consumer needs independently of which specific provider delivers it.

### 7.1 The DCM Resource Type Registry
- DCM maintains an official registry of standard Resource Types
- Registry is **open** — community and implementors can propose new types
- All registry entries are **vendor-neutral by hard requirement**
- Exception: `exclusive` classification where one provider is the sole implementor
- Registry entries are versioned, immutable once published, and can be deprecated

### 7.2 Four Hierarchy Levels

**Level 1 — Resource Type Category** (broadest)
Organizational container. Examples: `Compute`, `Network`, `Storage`, `Platform`, `Security`, `Observability`, `Data`

**Level 2 — Resource Type** (abstract)
Defines a class of resource. Must be vendor-neutral. Examples: `Compute.VirtualMachine`, `Network.FirewallRule`

**Level 3 — Resource Type Specification** (standard contract)
The data contract for a Resource Type — all fields with types, constraints, and portability classifications.

**Level 4 — Provider Catalog Item** (concrete)
A specific provider's implementation of a Resource Type Specification.

### 7.3 Portability Classification
Every field in every Resource Type Specification carries a portability classification:

| Classification | Meaning | Portability |
|---|---|---|
| `universal` | All providers must support it | Fully portable |
| `conditional` | Some providers support it | Portable to supporting providers |
| `provider-specific` | One provider only | Portability-breaking — must be marked |
| `exclusive` | One provider for entire tech stack | Not applicable — declared |

**Hard requirements:**
- All `universal` fields MUST be supported by ALL implementing providers
- `provider-specific` fields MUST be marked portability-breaking
- Consumers MUST be warned when their request contains portability-breaking fields
- Portability warning enforcement is **organizational policy**: `block` | `warn` | `allow`

### 7.4 Inheritance
Resource Types support inheritance. Rules:
- Child inherits ALL parent fields — none can be removed or redefined
- Child may add new fields
- Child portability can only be equal to or more restrictive than parent
- Each level is independently versioned with parent UUID reference

### 7.5 Request Resolution — Specificity Narrowing
Provider selection is **never explicit**. It emerges from progressive specificity:
```
Resource Type declared        → matches all providers for that type
Universal fields specified    → still matches all providers
Conditional fields specified  → narrows to supporting providers
Provider-specific fields used → narrows to single provider (portability warning issued)
Placement/sovereignty applied → final provider selected by Policy Engine
```

---

## SECTION 8 — RESOURCE/SERVICE ENTITIES

### 8.1 Core Terminology

| Term | Definition |
|------|-----------|
| **Resource/Service Request** | What a consumer submits to DCM — the declared intent to consume a resource or service. The consumer side of the transaction. |
| **Resource/Service Entity** | The "thing" produced by a provider as a result of fulfilling a request — the allocation made real. The provider side of the transaction. |

### 8.2 DCM as Authoritative Owner — Always
DCM is ALWAYS the system of record for Resource/Service Entity data. DCM is ALWAYS authoritative for the resource definition. DCM ALWAYS owns the lifecycle. This applies regardless of the operational ownership model.

Providers are **custodians** of the underlying infrastructure — they are not the system of record.

### 8.3 Four Ownership Models

| Model | Description | Example |
|-------|-------------|---------|
| **Allocation** | Provider retains internal ownership. Consumer owns the Entity (the allocation). Provider has reclaim rights on decommission. | VM, Container, IP Address |
| **Cost Analysis Information Provider** | Specialized Information Provider supplying cost estimates, placement cost signals, cost actuals, and budget alerts; DCM provides input data; provider performs calculations |
| **Orchestration Flow Policy** | Named workflow artifact: Orchestration Flow Policy with `ordered: true`; declares explicit step sequence using payload type vocabulary; first-class Data artifact; versioned, GitOps-managed, profile-bound |
| **Request Orchestrator** | Runtime event bus; routes lifecycle events to Policy Engine; has no pipeline logic; both named workflows and dynamic policies are evaluated through it |
| **orchestration (DCM)** | Two-level composable model: Level 1 = named Orchestration Flow Policies (explicit sequence); Level 2 = dynamic policies (conditional, inline); both evaluated by Policy Engine; adding a step = adding to a workflow Policy; adding conditional behavior = writing a dynamic policy |
| **Provider Catalog Item** | What a specific Service Provider offers consumers: specific resource allocation or process with cost, availability, SLAs; linked to Resource Type Specification version |
| **cross_tenant_authorization** | DCMGroup with group_class: cross_tenant_authorization; grants one Tenant permission to reference/allocate/stake another Tenant's resources; revocation places active allocations in PENDING_REVIEW |
| **foundation Tenants** | Three system Tenants created at bootstrap: __platform__, __transitional__, __system__; cannot be decommissioned; declared in bootstrap manifest |
| **QUOTA_EXCEEDED** | Gating Policy rejection code when resource quota policy fires at Step 5 (pre-placement) |
| **Federated Contribution Model** | DCM defaults to federated data creation — all authorized actor types (platform admin, consumer/tenant, service provider, peer DCM) can contribute Data artifacts within their domain scope via the GitOps PR model; see doc 28 |
| **contributor** | Actor type that authored a Data artifact; recorded in artifact_metadata.contributed_by; determines review requirements; platform_admin / consumer / service_provider / peer_dcm |
| **contributed_by** | Artifact metadata block recording contributor_type, actor UUID, contribution_method, pr_url, reviewed_by; immutable once set |
| **DPO-001–006** | Design Priority system policies. DPO-001: security properties present in all profiles (not controlled by profiles). DPO-002: every security requirement needs an ease-of-use mechanism. DPO-005: minimal profile = "security with minimal overhead" not "minimal security". DPO-006: when security and ease conflict, redesign ease-of-use, not security. |
| **FCM-001–008** | Federated Contribution Model system policies; key: FCM-002 (domain scope violations = hard DENY), FCM-003 (GitOps PR for all), FCM-008 (contributor scope limits absolute) |
| **Unified Governance Matrix** | Single enforcement point for all cross-boundary decisions; four axes (subject/data/target/context); hard vs soft enforcement; field-level granularity (allowlist/blocklist/paths); profile-bound defaults; GMX-001–010 |
| **governance_matrix_rule** | Artifact declaring match conditions across four axes and a decision (ALLOW/DENY/ALLOW_WITH_CONDITIONS/STRIP_FIELD/REDACT/AUDIT_ONLY) with hard or soft enforcement |
| **sovereignty_zone** | Registered DCM artifact declaring geopolitical/regulatory boundary; rules reference zones by ID; inter-zone agreements declared explicitly |
| **STRIP_FIELD** | Governance matrix decision: remove named fields from payload and proceed; if stripped field is required → DENY_REQUEST |
| **REDACT** | Governance matrix decision: replace field value with `<REDACTED>`; field presence preserved; receiver knows field exists but not its value |
| **Provider Type Registry** | Three-tier registry of approved provider types; each entry declares permissions, default_approval_method, enabled_in_profiles, capability_schema_ref |
| **registration_token** | Pre-issued by platform admin; scoped to provider_type/handle_pattern/zone; single_use; grants_auto_approval flag; value presented once only |
| **approval_method** | Registration approval: auto | reviewed | verified | authorized; resolved as most_restrictive(provider_type_default, profile_min, token_effect) |
| **Drift Reconciliation Component** | Control plane component; compares Discovered vs Realized State; produces drift records and events; never writes to Realized Store; DRC-001–005 |
| **drift_record** | Artifact produced by Drift Reconciliation; field-by-field comparison result with severity classification; unsanctioned flag; status tracking through resolution |
| **Placement Engine** | Six-step algorithm: sovereignty filter → accreditation filter → capability filter → reserve query → tie-breaking (policy/priority/affinity/cost/load/hash) → confirm; PLC-001–006 |
| **reserve_query** | Parallel capacity queries to all eligible provider candidates; PT5M capacity hold; non-responders and insufficient-capacity providers excluded |
| **consistent hash** | Final placement tie-breaker: SHA-256(request_uuid+resource_type+sorted_candidates); deterministic; never round-robin |
| **Lifecycle Constraint Enforcer** | Monitors TTL/expiry/max_execution_time; fires expiry actions through standard pipeline; grace period before action; Process Resources: immediate FAILED on breach; LCE-001–005 |
| **Search Index** | Non-authoritative queryable projection of GitOps stores; indexes key fields; returns git_path for full payload; max staleness PT5M; always rebuildable; SIX-001–004 |
| **Admin API** | Platform admin REST interface: Tenant lifecycle, provider review, accreditation approval, discovery trigger, orphan resolution, recovery decisions, quota management, Search Index rebuild, bootstrap operations |
| **PENDING_EXPIRY_ACTION** | Entity state when expiry action fails to execute; Lifecycle Constraint Enforcer retries per Recovery Policy; Platform Admin notified urgency: high |
| **data_classification** | First-class field metadata: public/internal/confidential/restricted/phi/pci/sovereign/classified; phi/sovereign/classified are immutable once set |
| **Accreditation** | Formal versioned attestation that a component satisfies a compliance framework; issued by an Accreditor; carries validity period; lifecycle: developing→proposed→active→expired/revoked |
| **Accreditor** | Entity that issues accreditations: government body, regulatory body, QSA, certification body, or internal audit team |
| **Accreditation Gap** | Missing, expired, or revoked accreditation required for an active interaction; always high/critical severity; Recovery Policy governs response |
| **Data/Capability Authorization Matrix** | Policy Group artifact (concern_type: data_authorization_boundary) declaring what data fields and capabilities are permitted across interaction boundaries given data classification and accreditation level |
| **zero_trust_posture** | Sixth Policy Group concern type; four levels: none/boundary/full/hardware_attested; profile defaults: minimal=none, dev/standard=boundary, prod/fsi=full, sovereign=hardware_attested |
| **Five-check boundary model** | Identity → Authorization → Accreditation → Matrix → Sovereignty; all five checks at every DCM interaction boundary; all produce audit records |
| **Federation tunnel** | Mutually authenticated, encrypted, scoped DCM-to-DCM channel; zero trust model; establishes secure transport only, not implicit trust; per-message signing; scoped non-transferable credentials |
| **hard_constraint** | Data/Capability Matrix declaration that cannot be overridden by any policy; sovereign/classified data never crossing federation boundaries is a hard_constraint |
| **STRIP_FIELD** | Matrix enforcement action: remove non-permitted field from payload and proceed; if stripped field is required → escalates to DENY_REQUEST |
| **DENY_REQUEST** | Matrix enforcement action: block entire interaction; entity enters PENDING_REVIEW; notification dispatched |
| **Request Orchestrator** | DCM control plane event bus; routes lifecycle events to Policy Engine; coordinates pipeline via event-condition-action; does not contain hardcoded pipeline logic |
| **Cost Analysis Component** | Internal DCM control plane component; three functions: pre-request estimation, placement input, ongoing attribution; not a billing system; not a provider type |
| **Module** | DCM capability extension adding new functions; distinct from Profile (which configures behavior) |
| **orchestration_flow** | Policy Group concern_type for static sequential flows; ordered: true; both static and dynamic flows compose through the same Policy Engine |
| **payload_type** | Closed vocabulary of event types the Request Orchestrator publishes; policies pattern-match on payload type + state |
| **OPA integration** | Reference implementation for Mode 3 External Policy Evaluators; DCM payload as OPA input document; built-in Rego functions provided by DCM |
| **Flow GUI** | Visual policy composer and orchestration manager; execution graph view, policy canvas, shadow mode dashboard, flow simulation |
| **__platform__** | Immutable system Tenant owning DCM control plane resources; created at bootstrap before Policy Engine comes online |
| **__transitional__** | Immutable system Tenant holding brownfield entities during INGEST phase |
| **bootstrap manifest** | Signed manifest declaring initial system Tenants, bootstrap admin, and initial profile; hash-verified at every DCM startup |
| **cross_tenant_authorization** | DCMGroup with this group_class formally grants one Tenant access to another's resources; has lifecycle (duration, renewal, revocation); revocation places active allocations in PENDING_REVIEW |
| **drift_criticality** | Field-level property in Resource Type Spec (low/medium/high/critical); combined with change magnitude to produce drift severity |
| **Ingress API** | Infrastructure-layer entry point for all inbound DCM requests; sets ingress block; routes to Consumer/Provider/Admin API surfaces |
| **Provider Catalog Item** | Provider-specific instantiation of a Resource Type Specification; what consumers actually request; distinct from the Resource Type Specification itself |
| **Recovery Policy** | Formal DCM policy type mapping trigger conditions (DISPATCH_TIMEOUT, PARTIAL_REALIZATION, etc.) to response actions; same authoring model as Gating Policy/Validation/Transformation |
| **recovery_posture** | Fifth Policy Group concern_type governing failure and ambiguity response; binds a recovery profile group to the deployment |
| **DRIFT_RECONCILE** | Recovery action: schedule discovery; let drift detection resolve actual state |
| **DISCARD_AND_REQUEUE** | Recovery action: best-effort cleanup; new request cycle created immediately |
| **NOTIFY_AND_WAIT** | Recovery action: notify human; wait for explicit decision up to declared deadline |
| **TIMEOUT_PENDING** | Infrastructure Resource Entity state: dispatch timeout fired; recovery policy evaluating |
| **LATE_REALIZATION_PENDING** | Entity state: provider responded after timeout; NOTIFY_AND_WAIT recovery decision pending |
| **INDETERMINATE_REALIZATION** | Entity state: state ambiguous; drift detection resolving |
| **COMPENSATION_FAILED** | Entity state: composite service rollback itself failed; orphan detection active |
| **orphan_candidate** | Resource discovered at provider with no corresponding Realized State record; surfaced to platform admin for human resolution |
| **Discovery Scheduler** | DCM control plane component maintaining priority queue of discovery requests; dispatches to provider discovery endpoints |
| **recovery-automated-reconciliation** | Built-in recovery profile: trust drift detection; accept late responses; appropriate for dev/standard |
| **recovery-notify-and-wait** | Built-in recovery profile: notify human; never act automatically; appropriate for prod/fsi/sovereign |
| **notification service** | Ninth DCM provider type; translates unified notification envelope to delivery channel; handles delivery, retry, dead letter, and delivery confirmation callbacks |
| **Notification Router** | DCM control plane component that resolves notification audiences and routes envelopes to notification services |
| **audience resolution** | Deriving notification recipients by traversing the entity relationship graph from the changed entity at event time |
| **notification_uuid** | Idempotency key on notification envelopes; notification services use this to deduplicate on retry |
| **audience_role** | owner / stakeholder / approver / observer — why this actor is in the notification audience |
| **stakeholder_reason** | Notification envelope field explaining which relationship caused the actor to be in the stakeholder audience |
| **Tier 1 / Tier 2 / Tier 3 notifications** | Mandatory system (non-suppressable) / Tenant defaults / Actor subscriptions — three subscription tiers that compose |
| **NOT-001 through NOT-008** | Notification model system policies |
| **write-once snapshot store** | Realized Store implementation model: each record is a complete immutable entity state snapshot; no event replay; direct point-in-time lookup; supersession chain links snapshots |
| **corresponding_requested_state_uuid** | Mandatory non-nullable field on every Realized State snapshot; traces every Realized State change to an authorized request |
| **Provider Update Notification** | Formal API for providers to report authorized state changes; DCM evaluates via Policy Engine; approved → new Requested State + Realized State; rejected → drift event |
| **notification_uuid** | Idempotency key on Provider Update Notifications; safe to resend on provider crash |
| **pre-authorized update** | Category of provider update pre-approved by Gating policy; processed automatically without per-change human review |
| **Whole Allocation** | Entire resource allocated as indivisible unit. Provider retains ownership. Consumer has exclusive use. Not subdivided or shared. | Dedicated Bare Metal (provider-owned) |
| **Full Transfer** | Provider transfers complete ownership to consumer's DCM Tenant. Consumer controls full lifecycle including decommission. | Transferred Bare Metal, Licensed asset |
| **Hybrid Transfer** | Ownership can transfer multiple times. Current owner is always exactly one DCM Tenant. Every transfer is tracked and auditable. | Bare Metal reallocated between tenants |

Every Provider Catalog Item must declare which ownership model(s) it supports.

### 8.4 Resource/Service Entity Lifecycle
```
REQUESTED → PENDING → PROVISIONING → REALIZED → OPERATIONAL
                                                      │
                                          ┌───────────┼───────────┐
                                          ▼           ▼           ▼
                                      DEGRADED   MAINTENANCE  SUSPENDED
                                                      │
                                                DECOMMISSIONING → DECOMMISSIONED
```
`DECOMMISSIONED` is the only terminal state. Records are retained permanently and are immutable.

### 8.5 Process Resource Entities
A distinct entity class for ephemeral execution resources — automation jobs, playbooks, pipelines, workflows.
- Ephemeral lifecycle — exists for duration of execution
- Execution record retained permanently after terminal state
- Must belong to a DCM Tenant
- Must be in provenance chain of any Resource/Service Entity they affect
- Lifecycle: `REQUESTED → INITIATED → EXECUTING → COMPLETED | FAILED | CANCELLED`

### 8.6 Provider Capacity Model — Three Modes
- **Mode 1 — Dynamic Query**: DCM queries provider on-demand during request processing
- **Mode 2 — Provider Registration (preferred)**: Provider registers capacity on configurable schedule — default minimum twice daily
- **Mode 3 — Provider Denial (mandatory)**: Provider validates fulfillment capability before executing. Denies with `INSUFFICIENT_RESOURCES`. Triggers immediate DCM capacity rating update.

All three modes are always available. Mode 3 is mandatory for all providers.

### 8.7 Provider Lifecycle Events
Any provider event affecting Resource/Service Entity availability or operational characteristics MUST be reported to DCM immediately. This is a non-negotiable contractual obligation.

When DCM receives a provider event, the Policy Engine evaluates and determines response:
`ALERT | REVERT | UPDATE_DEFINITION | INVESTIGATE | DECOMMISSION | ESCALATE`

DCM acts as the **Tenant advocate** — protecting Tenant interests in all provider interactions.

---

## SECTION 9 — SERVICE DEPENDENCIES

### 9.1 Why Dependencies Must Be Declared in Advance
Dependencies must be declared in the data model — not discovered at runtime. This is required for:
- **Auditability** — complete dependency graph known before execution
- **Cost Analysis** — full resource footprint known before provisioning
- **Placement** — Policy Engine needs complete resource footprint for optimal placement
- **Idempotency** — same request always produces same dependency graph

### 9.2 Hybrid Dependency Declaration Model

**Type-Level Dependencies (Resource Type Specification)**
- Portable and provider-agnostic
- Apply to all Provider Catalog Items implementing that Resource Type
- Use Resource Type UUIDs — not provider-specific references
- Required for all implementations

**Provider-Specific Dependencies (Provider Catalog Item)**
- Provider-specific additions beyond type-level dependencies
- Must be marked `portability_breaking: true`
- Visible to Policy Engine and consumers as portability warnings

### 9.3 Dependency Types and Cardinality

| Type | Behavior |
|------|---------|
| `hard` | Must be realized before/alongside dependent. Failure fails dependent. |
| `soft` | Preferred but not blocking. Failure recorded but does not block. |
| `conditional` | Required only if specific request payload conditions are met. |

| Cardinality | Description |
|-------------|-------------|
| `one_to_one` | Exactly one dependency resource required |
| `one_to_many` | One or more dependency resources required |
| `one_to_optional` | Zero or one dependency resource |
| `one_to_range` | Specific numeric range required |

### 9.4 Dependency Graph
When a request is processed, a complete **Dependency Graph** is constructed — all resources that must be created including all transitive dependencies. Each resource appears exactly once. Circular references are invalid.

The graph is attached to the Requested State. Nodes updated to REALIZED as providers fulfill each dependency.

### 9.5 Dependency Payload Passing
When a dependency is realized, its Realized State payload is passed to the dependent provider. The dependent resource's Requested State payload is enriched with the dependency entity's UUID and relevant realized data. Recorded in field-level provenance with `source_type: dependency_payload`.

### 9.6 Failure Handling — Configurable per Request or Policy

| Mode | Behavior |
|------|---------|
| `fail_all` | Any hard dependency failure fails entire request. Partially realized nodes decommissioned. |
| `fail_dependent` | Failure fails only the dependent and its dependents. Independent branches continue. |
| `retry` | Failed dependencies retried with same or alternative provider. |
| `partial_complete` | Request marked partially complete. Failed nodes flagged for retry or manual intervention. |

### 9.7 Rehydration and Dependencies
Rehydration uses **Intent State** — not Realized State — to reconstruct the dependency graph. This ensures current policies and standards are applied. Resources can be rehydrated to a different provider as long as type-level dependencies are satisfiable.

---

## SECTION 10 — UNIVERSAL GROUP MODEL AND TENANCY

> The Universal Group Model (document 15-universal-groups.md) supersedes the separate Tenant and Resource Group models for new implementations. All existing constructs map 1:1 to `group_class` values. Existing UUIDs and API surfaces are preserved.

### 10.1 Universal Group Structure
Every grouping construct in DCM is a `DCMGroup` with:
- `group_class` — determines system behavior (see 10.2)
- `group_subclass` — advisory label, no system behavior
- `member_types_permitted` — what can be a member
- `exclusivity` — one or many groups of this class per member
- `enforcement_model` — advisory | enforced | mandatory (tenant_boundary: profile-governed)
- `lifecycle_policy` — on_group_destroy: **detach (default)** | notify | cascade | retain
- `former_group_membership` records retained permanently after detach
- `group_destruction_record` retained in Audit Store permanently
- Time-bounded membership: `valid_from / valid_until` on every membership

### 10.2 Group Classes

| group_class | Purpose | enforcement |
|-------------|---------|------------|
| `tenant_boundary` | Ownership/isolation boundary (replaces Tenant) | profile-governed |
| `resource_grouping` | Flexible entity tagging (replaces Resource Groups) | advisory |
| `policy_collection` | Policy cohesion unit (replaces Policy Group) | advisory |
| `policy_profile` | Deployment configuration (replaces Policy Profile) | enforced |
| `layer_grouping` | Related layers for a context | advisory |
| `composite` | Cross-type organizational unit | configurable |
| `federation` | Peer-group association (federated Tenants) | advisory |

### 10.3 DCM Tenant — tenant_boundary group_class
Every resource entity must belong to exactly one `tenant_boundary` group (GRP-001). Provides: ownership, isolation, cost attribution, policy scope, drift detection scope, rehydration scope, audit scope, sovereignty boundary.

**Structurally locked invariants** (cannot be overridden by any policy):
- One tenant_boundary group per resource — always
- Constituent relationships never cross tenant_boundary boundaries — at any nesting level

**Profile-governed enforcement:** `minimal` profile → advisory; `standard`/`prod`/`fsi`/`sovereign` → mandatory. A Gating policy fires when advisory tenancy detected in prod/fsi/sovereign deployment (GRP-011).

### 10.4 Nested Tenants
A `tenant_boundary` group can have `parent_group_uuid` pointing to another `tenant_boundary` group. The parent-child relationship is a governance and cost relationship — NOT ownership transfer.

**Parent can:** aggregate cost, apply governance overlay, query aggregate audit, declare child lifecycle policies  
**Parent cannot:** own child resources, cross child isolation boundaries, override more-restrictive child policies

**Governance inheritance — most restrictive wins (GRP-009):**
```
Most restrictive policy at ANY nesting level wins
  Child policies that are more restrictive than parent → child wins
  Parent policies cascade where child has no policy or is less restrictive
  Platform policies govern all tenant_boundary groups
```

### 10.5 Federated Tenants
A `federation` group contains peer `tenant_boundary` groups. Enables shared policy application, cross-federation visibility, and consolidated reporting. Does NOT grant governance authority — member Tenants remain independent (GRP-010).

### 10.6 Composite Groups
A `composite` group permits all member types — resource entities, policies, layers, and other groups. Enables "everything about Payments" as one organizational unit.

Policy targeting composite groups defaults to all member types. Declare `member_type_filter` to narrow. Policy linting warns if composite is targeted without filter (GRP-012).

### 10.7 GRP System Policies
GRP-001 through GRP-014. Key: GRP-001 (one tenant_boundary per resource), GRP-003 (no circular nesting), GRP-005 (detach is default on destroy), GRP-006 (resource in leaf Tenant always), GRP-009 (most restrictive wins in nesting), GRP-011 (advisory tenancy in prod triggers notification), GRP-013 (former_group_membership permanent), GRP-014 (destruction record permanent).

### 10.5 DCM System Policies for Grouping

| Policy | Rule |
|--------|------|
| `TEN-001` | Every Resource/Service Entity must belong to exactly one DCM Tenant |
| `TEN-002` | A Tenant must exist before resources can be created in it |
| `GRP-003` | Circular nesting in Resource Groups is invalid |
| `GRP-004` | Custom Resource Groups must implement the full Resource Group Interface |
| `GRP-005` | Exclusive membership groups must reject violating membership requests |

---

## SECTION 11 — ENTITY RELATIONSHIPS

### 11.1 Design Principle
**Single model. Minimum variance. Simple by default.** Every relationship in DCM — VM requires storage, application contains web server, resource references Business Unit — uses the same structure. No separate binding mechanism, no separate dependency graph, no separate business data association. One universal model.

### 11.2 Universal Relationship Structure
Every relationship is a first-class data object with its own UUID. Recorded **bidirectionally** — on both participating entities. The same `relationship_uuid` appears on both sides.

```yaml
relationship:
  relationship_uuid: <uuid — same on both sides>
  this_entity_uuid: <uuid>
  this_role: <role this entity plays>
  related_entity_uuid: <uuid of related entity or external reference>
  related_entity_type: <internal|external>
  related_entity_role: <role the related entity plays>
  information_provider_uuid: <uuid — if external>
  information_type: <e.g., Business.BusinessUnit — if external>
  relationship_type: <see types below>
  nature: <constituent|operational|informational>
  lifecycle_policy:
    on_related_destroy: <destroy|retain|detach|notify>
    on_related_suspend: <suspend|retain|detach|notify>
    on_related_modify: <cascade|ignore|notify>
  status: <active|suspended|terminated>
  provenance: <standard provenance>
```

### 11.3 Relationship Types (fixed vocabulary)

| Type | Inverse | Meaning |
|------|---------|---------|
| `requires` | `required_by` | Cannot function without the related entity |
| `depends_on` | `dependency_of` | Uses the related entity but can degrade without it |
| `contains` | `contained_by` | Logical container for the related entity |
| `references` | `referenced_by` | References without owning or requiring |
| `peer` | `peer` | Equal relationship |
| `manages` | `managed_by` | Has lifecycle management authority |

### 11.4 Relationship Nature

| Nature | Lifecycle Policy | Example |
|--------|-----------------|---------|
| `constituent` | Required | VM requires its boot disk |
| `operational` | Required | Web server depends on load balancer |
| `informational` | Not applicable | Resource references its Business Unit |

### 11.5 Lifecycle Policy Authority
```
Resource Type Specification default (lowest)
  → Provider Catalog Item default
    → Consumer declaration
      → DCM System Policy (non-overridable)
```

### 11.6 Relationship Roles
Standard roles: `compute`, `storage`, `networking`, `security`, `database`, `web`, `app`, `cache`, `queue`, `pipeline`, `identity`, `monitoring`, `business_unit`, `cost_center`, `product_owner`, `regulatory_scope`

Custom roles: extensible — organizations register domain-specific roles (e.g., `trading_engine`, `risk_calculator`). Semantic labels only — do not affect system behavior.

### 11.7 Where Relationships Are Declared
- **Resource Type Specification** — declares possible relationships (ceiling)
- **Catalog Item** — declares actual relationships for an offering (can only restrict)
- **Request time** — consumer declares instance relationships
- **External data** — same model for Business Unit, Cost Center, Person, etc.

### 11.8 Bundled Declaration Expansion
When consumer bundles storage/networking in a compute request:
1. **Processor** creates Resource/Service Entity stubs (PENDING) with UUIDs
2. **Processor** creates bidirectional Relationship records
3. **Processor** applies lifecycle policy hierarchy
4. **Policy Engine** validates binding type and lifecycle policy
5. **Service Provider** provisions natively, returns realized payloads in DCM format
6. **DCM** updates entities PENDING → REALIZED, activates relationships

### 11.9 The Entity Relationship Graph
All relationships form a traversable graph. Used for: rehydration (full graph traversal), cost rollup (accumulates across constituent relationships), drift detection (discovered vs realized graph comparison), decommission ordering (lifecycle policies at each edge), placement (pre-realization footprint), impact analysis (change propagation).

### 11.10 Supersedes Dependency Graph
The Entity Relationship model unifies the previously separate dependency graph concept. The dependency graph IS the relationship graph at pre-realization time — same structure, different lifecycle state.

### 11.11 Lifecycle Policy Conflict Resolution (Q57 resolved)
Lifecycle policy fields on relationships are **just fields**. They carry the same `override` metadata, the same provenance obligations, and resolve under the same Policy Engine authority hierarchy as any other DCM field. No special case — minimum variance.

**Priority schema governs conflicts within a tier.** Highest numeric priority runs first. First policy to set `override: immutable` on a lifecycle policy field locks it. `immutable_ceiling: absolute` applies for compliance mandates that must survive future policy changes.

**Ingestion conflict detection applies.** Two policies declaring conflicting lifecycle policies without priority differentiation → CONFLICT ERROR at ingestion.

**DCM System Policies:**
- `REL-008` — A `constituent` relationship lifecycle policy may not be set to `ignore` for `on_related_destroy`
- `REL-009` — Lifecycle policy conflicts between policies are resolved by the standard Policy Engine authority hierarchy — no special case

### 11.12 Relationship Type × Nature Matrix (valid combinations)

The two relationship dimensions form an explicit matrix. Invalid combinations are rejected by the Policy Engine at request time (REL-013).

| | `constituent` | `operational` | `informational` |
|---|---|---|---|
| **`requires`** | ✅ Core constituent | ✅ Hard operational dependency | ❌ Invalid |
| **`depends_on`** | ✅ Soft constituent | ✅ **Allocated resource cell** | ✅ Awareness |
| **`contains`** | ✅ Ownership container | ⚠️ Rare — justify explicitly | ❌ Invalid |
| **`references`** | ❌ Invalid | ❌ Invalid | ✅ **Business context cell** |
| **`peer`** | ❌ Invalid | ✅ Operational peers | ✅ Informational peers |
| **`manages`** | ✅ Component management | ✅ Operational management | ✅ Audit management |

- `operational` + `depends_on` = **allocated resource cell** — cross-tenant allocations live here
- `informational` + `references` = **business context cell** — Business Unit, Cost Center etc.

### 11.13 Cross-Tenant Relationships (Q59 resolved)

Relationship **nature** governs cross-tenant permissions:

| Nature | Cross-Tenant? | Rule |
|--------|--------------|------|
| `constituent` | ❌ Never | REL-010 |
| `operational` | ✅ With dual authorization | REL-011 |
| `informational` | ✅ Unless deny_all | REL-012 |

**Hard tenancy declaration** on Tenant entity:
```yaml
hard_tenancy:
  cross_tenant_relationships: operational_only
  # deny_all | operational_only | informational_only | allow_all
```

### 11.14 Allocated Resource Model (Q59 extension, Q61 partial)

An **Allocated Resource** is a pre-defined discrete slice of a parent resource made available by the owning Tenant for consuming Tenants to claim. It becomes a **first-class entity** in the consuming Tenant's scope with its own UUID, lifecycle, and governance.

**Relationship:** `depends_on` + `operational` + `cross_tenant: true` + `allocation_uuid`

**Parent pre-defines** `available_allocations` — consuming Tenant claims → DCM creates allocated entity + relationship → parent tracks in `active_allocations` with `notification_endpoint`.

**Lifecycle events** propagate from parent to all active allocations per each allocation's `parent_lifecycle_policy`:
`on_parent_destroy | on_parent_suspend | on_parent_maintenance | on_parent_degrade | on_parent_capacity_change`

**System policies:** REL-013 (invalid matrix combinations rejected), REL-014 (claim requires available allocation record)

### 11.15 Shared Resource Model — Same-Tenant (Q61 resolved)

A **Shared Resource** is an entity within a single Tenant that has active relationships from multiple parent entities. DCM maintains `active_relationship_count` — the number of active constituent/operational relationships. Informational relationships never count (REL-016).

**`sharing_model` on entity:**
```yaml
sharing_model:
  shareable: true
  sharing_scope: tenant
  active_relationship_count: 3   # DCM-maintained
  minimum_relationship_count: 0
  on_last_relationship_released: <destroy | retain | notify>
```

**`shareability` on Resource Type Specification:**
- `shareability.allowed: true` — instances can have multiple active relationships
- `shareability.allowed: false` (e.g., `Compute.BootDisk`) — second relationship rejected (REL-017)
- `max_active_relationships` — optional cap (e.g., license seat limits)

**Destruction deferral (REL-015):** Destructive lifecycle actions on shared resources are deferred until `active_relationship_count` reaches `minimum_relationship_count`. Deferred destruction is recorded in `deferred_destruction_record`.

### 11.16 Lifecycle Action Hierarchy — Save Overrides Destroy (REL-018)

When multiple relationships produce different lifecycle action recommendations on a shared resource, the most conservative action wins:

```
retain > notify > suspend > detach > cascade > destroy
```

`retain` always beats `destroy` — the save_overrides_destroy rule. Applies automatically per REL-018.

**Conflict detection (REL-019):** When recommendations differ, a `lifecycle_conflict_record` is created:
- Severity `info` — hierarchy resolved cleanly (e.g., retain beats destroy non-adjacent)
- Severity `warning` — adjacent levels or `notify` is the winning action — notifications sent
- Severity `critical` — immutable lifecycle lock overridden by REL-018 — platform admin notified

**Unified model:** Same-tenant sharing (`active_relationship_count`) and cross-tenant allocation (`active_allocations`) are the same reference-counting concept at different scopes. Both defer destructive actions until the last relationship/allocation is released.

---

## SECTION 12 — INFORMATION PROVIDERS

### 12.1 Purpose
Information Providers are a first-class DCM provider type that serves authoritative external data DCM needs to reference but does not own (HR systems, finance systems, CMDBs). DCM references but never caches or owns external data.

### 12.2 Provider Types — Data Ownership

DCM has five provider types (see Section 0 for the complete list). The data ownership question is most relevant to these four categories:

| Type | Purpose | DCM Owns Result? |
|------|---------|-----------------|
| **Service Provider** | Realizes resources — KubeVirt, VMware, AAP, etc. | Yes |
| **Information Provider** | Serves authoritative external data DCM references but does not own | No — external system is authoritative |


All five provider types follow the same base contract: registration, health check, trust, sovereignty, accreditation, governance matrix enforcement, zero trust, and provenance emission obligation.

### 12.3 Same Contract as Service Providers
Information Providers follow the same registration, health check, trust, and capacity model as Service Providers where applicable. Capacity = query capacity (requests/sec). Naturalization/Denaturalization = translating native format to DCM unified format.

### 12.4 Standard vs Extended Data
- **Standard data** — DCM-defined fields. Used for lookups, policy evaluation, operational decisions. Portable across all implementations.
- **Extended data** — organization-defined fields. Carried in payload for downstream consumers. DCM core does not rely on extended data for operational decisions.

### 12.5 Stable External Key Model
```yaml
external_entity_reference:
  uuid: <dcm-generated — stable internal anchor>
  external_uuid: <stable uuid from external system>
  information_provider_uuid: <uuid>
  information_type_name: Business.BusinessUnit
  lookup_method:
    primary_key: external_uuid
    fallback_keys:
      - field: code
        value: "BU-PAY"
  display_name: <non-authoritative — UI convenience only>
  verification:
    last_verified: <ISO 8601>
    verification_status: <verified|stale|unverifiable|deactivated>
```
DCM UUID wraps external UUID — if external system changes its UUID, only this record changes. All relationships remain valid.

### 12.6 Three-Mode Verification
- **Mode 1** — DCM-initiated scheduled verification (configurable frequency)
- **Mode 2** — Information Provider push (contractual obligation — same as SP lifecycle events)
- **Mode 3** — On-demand verification fallback when reference is stale

### 12.7 Information Types in the Registry
Same DCM registry as Resource Types — distinguished by category prefix:
- `Business.*` — BusinessUnit, CostCenter, ProductOwner
- `Identity.*` — Person, ServiceAccount, Group
- `Compliance.*` — RegulatoryScope, AuditFramework
- `Operations.*` — Runbook, SLA, SupportContract

---

## SECTION 13 — KUBERNETES SUPERSET STRATEGY

### 13.1 Position
DCM is a **superset of Kubernetes** — extending Kubernetes' declarative, controller-based model upward to provide unified management across multiple clusters, infrastructure types, and organizational boundaries. Kubernetes manages the execution plane. DCM manages the management plane.

### 13.2 What DCM Adds Beyond Kubernetes

| Capability | Kubernetes | DCM |
|------------|-----------|-----|
| Scope | Single cluster | Multi-cluster, multi-infrastructure |
| Tenancy | Namespace isolation | First-class Tenant ownership model |
| Policy | RBAC + admission webhooks | Full Policy Engine — Validation/Transformation/Gating Policy |
| Data lineage | Not provided | Field-level provenance on all data |
| Cost attribution | Not provided | Full lifecycle cost analysis |
| Drift detection | Controller reconciles | Four-state model — Intent/Requested/Realized/Discovered |
| Service catalog | Not provided | Self-service catalog with RBAC-governed presentation |
| Sovereignty | Not provided | Placement constraints, compliance evidence |
| Non-Kubernetes resources | Not provided | VMware, bare metal, OpenStack managed through same model |

### 13.3 Operator Integration — The Adapter Pattern
Kubernetes operators become DCM Service Providers through the DCM Operator Interface Specification. The pattern:
```
DCM Control Plane → Operator Adapter (Service Provider) → Kubernetes Operator → Cluster
```
The adapter handles Naturalization (DCM Requested State → Kubernetes CR) and Denaturalization (CR status → DCM Realized State).

### 13.4 Native Support Strategy
Goal: influence the Kubernetes operator ecosystem to adopt DCM as a superset. Three-phase approach:
1. **Generic Operator Adapter** — declarative field mappings, no operator changes needed
2. **DCM Operator SDK** — Go library, adds DCM support with minimal code changes, one day to Level 1
3. **Upstream contributions** — contribute DCM support directly to priority operators (KubeVirt, CloudNativePG, Strimzi, Cert-Manager)

### 13.5 Conformance Levels
- **Level 1** — Registration + health + basic status reporting. One day with SDK. Unlocks: catalog, health monitoring, basic cost tracking.
- **Level 2** — + Capacity + lifecycle events + full realized payloads + field mappings. 2-3 days. Unlocks: placement, drift detection, cross-cluster management.
- **Level 3** — + Sovereignty + provenance + discovery + decommission confirmation. 3-5 days. Unlocks: full audit chain, brownfield ingestion, sovereignty enforcement.

### 13.6 CNCF Strategy
Target CNCF Sandbox submission. FSI consortium (leading FSI consortium members) provides multi-organization adopter evidence. Key artifacts needed before submission: DCM Operator Interface Spec v1.0, SDK v0.1.0, KubeVirt Level 2 reference implementation, conformance test suite, governance model.

### 13.7 Key Kubernetes-to-DCM Concept Mappings
| Kubernetes | DCM |
|-----------|-----|
| CRD | Resource Type Specification |
| Custom Resource | Requested State → Realized State |
| Reconciliation loop | Realization + Drift Detection |
| Namespace | DCM Tenant boundary |
| ownerReference | Entity Relationship (contains/contained_by) |
| Finalizers | Lifecycle policy enforcement |
| Labels/Annotations | DCM entity metadata |
| Kubernetes conditions | DCM lifecycle states |

---

## SECTION 14 — WEBHOOK INTEGRATION

### 14.1 Purpose
Webhooks provide a **push-based notification model** for consumers, providers, and external systems that cannot or do not poll DCM. They complement the API-first model and Message Bus by enabling real-time outbound event notifications.

### 14.2 Architectural Position
Webhooks are an **Egress capability** — outbound notifications from DCM to external systems. They fit within the existing Egress zone alongside the Messaging Protocol and Interoperability API.

### 14.3 Core Use Cases

| Audience | Example Events |
|----------|---------------|
| **Consumer/CI-CD** | Resource request transitions to REALIZED; Entity enters DEGRADED state; dependency graph node fails |
| **Provider** | New request payload dispatched; discovery request initiated; decommission requested |
| **External Systems** | ITSM notification on request create/update/complete; FinOps platform on Entity realization/decommission |
| **Operational** | Provider capacity below threshold; unsanctioned change detected; Gating policy fired |
| **Compliance** | Sovereignty constraint applied; ownership transfer initiated/completed; audit-relevant policy triggered |

### 14.4 Key Design Principles (Established)
- Webhook events are **typed and versioned** — consistent with DCM universal versioning model
- Webhook payloads carry **provenance information** — sufficient context to trace back to the originating request, entity, and policy
- **Policy Engine integration** — the Policy Engine can fire webhooks as a response action (alongside ALERT, REVERT, UPDATE_DEFINITION, etc.)
- Webhook registrations are **scoped** — consumer-facing webhooks registered via Consumer API; provider-facing webhooks registered via Provider Registration
- Events should align with a **DCM Event Type Registry** — extensible, versioned, following the same registry model as Resource Types

### 14.5 Open Design Questions
See [DISCUSSION-TOPICS.md — TOPIC-001](../DISCUSSION-TOPICS.md) for the full list of design questions. Key unresolved items:
- Webhook registration model and API
- Full event taxonomy and registry structure
- Payload format — full state vs reference + event type
- Authentication model for outbound webhook calls
- Retry and reliability obligations
- Ordering guarantees
- Relationship to the Message Bus
- Whether provider webhook support is mandatory in the Provider Contract
- Tenant vs platform-level scoping

### 14.6 Status
**Under active discussion** — see DISCUSSION-TOPICS.md TOPIC-001. Do not make implementation assumptions until design questions are resolved.

---

## SECTION 15 — DCM ARCHITECTURE COMPONENTS

### 15.1 The Five Domains
DCM is organized into five horizontal domains from bottom to top:

| Domain | Persona | Content |
|--------|---------|---------|
| **Data Center Domain** | CIO | Physical infrastructure — Compute, GPU, RAM, Storage, Networking, HSM |
| **Resource Domain** | SRE | Declarative resources — VMs, containers, pods, clusters, external IPs |
| **Control Plane Domain** | CTO | Policy, Validate & Placement, Audit, Orchestration |
| **Application Domain** | Engineering | Data Center Pipeline, CI/CD |
| **Value Domain** | Line of Business | Software Build & Deploy, business outcomes |

### 15.2 Control Plane Components

| Component | Purpose |
|-----------|---------|
| **API Gateway** | Central clearing house — ingress for consumers, egress to providers |
| **Job Queue** | Manages asynchronous task execution |
| **Request Payload Processor** | Assembles, enriches, and merges data layers into complete request payload |
| **Policy Engine** | Validates, transforms, gates, and enriches data based on policy definitions |
| **IDM / IAM** | Authentication and identity — source of truth for personas and RBAC |
| **Service Catalog** | Presents available services/resources per RBAC policy |
| **Orchestration** | Coordinates multi-step workflows and manages request lifecycle |
| **Cost Analysis** | Tracks service costs throughout the full resource lifecycle |
| **Audit** | Records all operations — reads provenance intrinsic to data objects |
| **Observability** | Monitoring, logging, and metrics |
| **Resource Discovery** | Interrogates providers to discover existing resource state |
| **Message Bus** | Async communication between control plane and external systems |

### 15.3 Data Stores — PostgreSQL Store Contracts

All DCM stores use **PostgreSQL** as the single required infrastructure. DCM defines store contracts for each data domain. Four store contract types:

| Contract Type | Stores | Key Characteristics |
|--------------|--------|-------------------|
| **GitOps Store** | Intent, Requested, Layer, Policy | Branch/PR/merge semantics, immutable history, CI/CD hooks, Search Index companion |
| **Event Stream Store** | Realized, Discovered, Audit events | Append-only, entity-keyed streams, replayable, high-throughput |
| **Audit Store** | Compliance audit records | Compliance-grade, immutable, long-retention (7+ years FSI), hash-verified |
| **Observability Store** | Metrics, traces, logs | Time-series, short-to-medium retention, OpenTelemetry format |

**Search Index** — non-authoritative queryable projection of GitOps stores. Rebuilt from Git on demand. Git always wins on disagreement.

**DCM-internal caches** (Layer Cache, Policy Cache, Catalog Cache) — not data stores. Non-authoritative, cache-aside pattern, invalidated on writes.

### 15.4 Consumer Ingress
- **Web UI** — web interface for human consumers
- **Consumer API** — API interface for programmatic consumers and external systems

### 15.5 Egress
- **Messaging Protocol** — protocol translation to external systems
- **Interoperability API** — common API spec and data model for Service Provider communication

---

## SECTION 16 — SERVICE PROVIDERS

### 16.1 Core Principle
DCM is **not concerned with how a provider accomplishes its work** — only with:
- The data that crosses the boundary (conformant data in, conformant data out)
- The trust and contractual obligations the provider has declared and honored

### 16.2 Naturalization and Denaturalization
- **Naturalization** — provider transforms DCM unified data into its own tool-specific format for execution
- **Denaturalization** — provider transforms tool-specific results back into DCM unified format for return to the control plane

### 16.3 Provider Contract Dimensions
Providers must honor a multi-dimensional contract:

**Data Contract**
- Accept DCM unified data format
- Return complete DCM unified data format (not just status codes)
- Implement Naturalization and Denaturalization

**Sovereignty Contract**
- Explicitly declare which sovereignty dimensions they can satisfy
- Declaration is binding — if declared, it must be delivered
- Sovereignty dimensions: Data/Content, Operational, Security/Compliance, Placement/Mobility

**Capability Contract**
- Declare which Resource Types they implement
- Declare which lifecycle operations they support (CRUD + Discovery)
- Declare what they do NOT support

**Lifecycle Contract**
- Support all declared lifecycle states
- Participate in Discovery when requested
- Report Realized State completely and accurately
- Handle drift detection requests

**Query Contract**
- Support `reserve_query` — atomic: verify constraints + return metadata + place hold
- Support `capacity_query` (informational, no hold)
- Support `metadata_query` (informational, no hold)
- Declare which query types and metadata fields are supported in provider registration
- Complete missing metadata in realized payload or discovery loop
- `reserve_query` response must include `missing_metadata` for any requested fields not returned

**Trust Contract** *(validation mechanism — to be detailed)*
- Providers must be validated and certified to participate
- Trust is established at onboarding
- Chain of trust must be maintained

**Compliance/Audit Contract**
- Maintain audit trail of actions taken
- Make audit data available to DCM in DCM unified format
- Must not take actions outside of DCM-initiated requests (for managed resources)

**SLA/Operational Contract**
- Response time expectations
- Availability requirements
- Error handling and reporting standards
- Retry and idempotency guarantees

### 16.4 Provider Types
- **Atomic Providers** — manage a single fundamental resource type (VM, IP, VLAN, container)
- **Composite Services** — compose multiple constituent resource types into a single catalog item
- **Process Providers** — purely process-based workflow or automation
- **External Policy Evaluators** — supply policies; Mode 4 evaluates/enriches via black box query
- **event routing services** — bidirectional bridge to external message buses (Kafka, AMQP, NATS, etc.)
- **credential management services** — resolve secrets from external stores (Vault, AWS SM, Azure KV, CyberArk, etc.)
- **Auth Providers** — authenticate identities and resolve permissions (OIDC, LDAP, AD, FreeIPA, etc.)
- **Real-world providers** are typically combinations of the above

---

## SECTION 17 — THE POLICY ENGINE

### 17.1 Purpose
The Policy Engine is the **single authoritative logic gate for all business rules** in DCM. It enforces governance without embedding business logic into the control plane. It is the **sole authority for field override control** — no other component sets override metadata on fields.

### 17.2 Policy Categories

| Category | Description | Modifies Data? | Example |
|----------|-------------|----------------|---------|
| **Transformation** | Enriches or modifies the payload. Adds missing fields, applies standards. All changes recorded in provenance. May set `override: constrained`. | Yes | Inject PCI-compliant cryptography standard |
| **Validation** | Checks payload against rules. Pass/fail — no field modification. Failure rejects request. | No | VM class allowed in DMZ Zone A |
| **Gating Policy** | Highest authority. Overrides any field including consumer input. Sets `override: immutable`. Halts execution. | Yes — overrides everything | Block request violating sovereignty |

### 17.3 Policy Hierarchy
Three-tier execution — Global first, User last. Within each tier sorted by priority (higher value = higher authority):

```
Global  (Super Admin) — runs first, highest authority
Tenant  (Tenant Admin) — runs second
User    (End User)    — runs last, lowest authority
```

A Global policy cannot be overridden by Tenant or User. Field locks set by higher-authority policies cannot be unlocked by lower-authority policies.

### 17.4 Policy Implementation
- **Engine:** OPA (Open Policy Agent) with Rego policy language
- **Storage:** GitOps — all policies in Git, versioned, immutable once published
- **Execution:** Stored-policy model — OPA pre-loads policies; evaluation calls pre-loaded modules
- **Outputs:** `rejected` (bool), `patch` (field mutations), `constraints` (JSON Schema locks), provider placement constraints (NOT direct provider naming)

### 17.5 Policy Rules
- Policies operate only on policy definition, core data, and request payload data
- Outcomes must be **deterministic** — same input always produces same output for a given version
- All modifications recorded in field-level provenance with policy UUID, tier level, and reason
- Policies follow the five-status lifecycle: `developing → proposed → active → deprecated → retired`

### 17.6 Policy Scope
- **Core Policies** — all DCM actions regardless of provider
- **Service Policies** — specific to a Service Provider's services
- **Organizational Policies** — defined by the implementing organization
- **Domain Policies** — scoped to a specific domain or business unit

### 17.7 Proposed Policy — Shadow Execution
When a policy is in `proposed` status it runs in **shadow mode** against real request traffic:
- Executes alongside active policies on every relevant request
- Output captured in `proposed_evaluation_record` — what it would have done
- Output is **never applied** to the actual request
- Feeds the Validation Dashboard for reviewer analysis before activation
- Impact categories: `none | low | medium | high | critical`
- Activation requires approval after review period

### 17.8 Policy and Override Control
The Policy Engine exclusively sets `override_control` metadata. Three levels (see Section 6.10–6.11):
- Level 1 — no declaration → fully overridable (default)
- Level 2 — simple `override: allow|constrained|immutable`
- Level 3 — full `override_matrix` with per-actor permissions and trusted grants

### 17.9 Policy Placement Phase
Every policy declares when in the assembly process it executes:
- `pre` — before placement (default) — no provider context
- `loop` — inside the placement loop — has reserve query response data
- `post` — after placement confirmed — has full placement block
- `both` — pre and post

### 17.10 Policy Required Context
Policies declare what fields they need and what to do when fields are absent:
```yaml
required_context:
  - field: placement.provider_metadata.sovereignty_certifications
    if_absent: <gate | warn | skip>
    if_absent_reason: <human-readable>
```
If no policy declares `required_context` for an absent field → `implicit_approval` recorded in `policy_gap_record`. The system has no implicit opinion beyond what policies state.

---

## SECTION 18 — KEY USE CASES

### 18.1 Datacenter Rehydration (Repave)
Reconstruct ALL required components and configurations from code after catastrophic failure (ransomware, DR event, mandatory 90-day repave). Industry benchmark: leading FSI organization 60-day repave. DCM must beat this. Key metric: TTR (Time to Recovery).

### 18.2 Intelligent Placement
Automated placement of resources and workloads based on metadata, policies from CMDB/CISO/platform teams. Consumer declares criteria (location, SLA, security zones) — DCM determines optimal placement automatically.

### 18.3 Application as a Service
Meta Service Provider that consumes application code and provides its full execution lifecycle. Consumer defines metadata for required technologies or SLAs — provider handles the rest.

### 18.4 Regional Sovereignty
Enforce workload placement within specific regions or sovereignty constraints. CISO/CCO-driven policy ensuring data residency and jurisdictional compliance.

### 18.5 Data Enrichment
System enriches consumer requests with ancillary implementation details the consumer should not need to know. Consumer declares intent — DCM fills in the details.

### 18.6 Greening the Brownfield — Unified Ingestion Model
Bring existing unmanaged infrastructure under DCM lifecycle management using the unified ingestion model (see Section 20 and data model document 13-ingestion-model.md). The same three-step pattern applies to both brownfield ingestion and V1 migration:

```
1. INGEST   — bring the entity into DCM with whatever identity/metadata is available
2. ENRICH   — associate business data, ownership, Tenant assignment, relationships
3. PROMOTE  — transition from holding state to full DCM lifecycle ownership
```

**Brownfield flow:** Service Provider performs discovery → DCM identifies unmanaged Discovered State records → Entity stubs created (state: INGESTED, Tenant: `__transitional__`) → Business data and Tenant assigned → Promotion authorized → Discovered State promoted to Realized State → Drift detection active from this point.

**V1 Migration flow:** V1 resources inventoried → Auto-assignment attempted via signals (resource groups, business unit, request history) → Auto-assignable resources assigned in bulk → Manually assignable resources surfaced in admin queue → Orphaned resources assigned to `__transitional__` → Enrichment and promotion → Migration complete when `__transitional__` Tenant is empty.

**Key concepts:**
- `__transitional__` Tenant — system-managed holding area for unassigned ingested entities. Cannot be deleted or used for new provisioning. Governance policy enforces max residency and escalation.
- `ingestion_record` — provenance record on every ingested entity: source, confidence, assignment method, enrichment history, promotion timestamp
- Ingestion confidence: `high` (strong signal) | `medium` (inferred) | `low` (orphaned)
- Entities in `INGESTED` or `ENRICHING` state cannot be parents for allocated resource claims or hard dependencies for new requests

---

## SECTION 19 — DIGITAL SOVEREIGNTY

DCM addresses four dimensions of digital sovereignty:

| Dimension | DCM Enabler | Impact |
|-----------|-------------|--------|
| **Data and Content Sovereignty** | Data Model, Policy Engine, Validated Providers | Data residency and jurisdictional compliance |
| **Operational Sovereignty** | Policy Engine | Sovereign Execution Posture, Hard Tenancy enforcement |
| **Security and Compliance Sovereignty** | Audit, GRC | Evidence for strict regional mandates |
| **Mobility, Placement, Modernization** | Policy Engine, Providers, Data Model | Automated placement, provider mobility, brownfield ingestion |

**Sovereign Execution Posture** — the target end state where all operations are governed, auditable, and compliant with sovereignty requirements. This is the north star concept of DCM.

---

## SECTION 20 — INGESTION MODEL

The Ingestion Model is the **unified mechanism for bringing entities that exist outside DCM's lifecycle control into DCM governance**. It covers V1 Migration, Brownfield Discovery, and Manual Import — all follow the same pattern.

### 20.1 Three-Step Pattern
```
INGEST  → ENRICH  → PROMOTE  → OPERATIONAL
```

### 20.2 Ingestion Lifecycle States

| State | Tenant | New Requests? | Parent for Allocations? | New Relationships? |
|-------|--------|--------------|------------------------|-------------------|
| `INGESTED` | `__transitional__` or assigned | No | No | Informational only |
| `ENRICHING` | Assigned | No | No | Operational (read-only) |
| `PROMOTED` | Assigned | Yes | Yes | All types |

### 20.3 The `__transitional__` Tenant
System-managed holding Tenant for unassigned ingested entities:
- Cannot be deleted, renamed, or used for new resource provisioning
- Governance policy enforces `max_residency_days` and escalation action
- Hard tenancy: `operational_only` by default
- `created_via: system` — artifact metadata

### 20.4 Ingestion Record
Every ingested entity carries an `ingestion_record` in provenance:
- `ingestion_source` — `v1_migration | brownfield_discovery | manual_import`
- `assigned_tenant_uuid` — real Tenant or null if still in `__transitional__`
- `assignment_method` — `auto | manual | transitional`
- `assignment_signal` — human-readable description of what drove auto-assignment
- `ingestion_confidence` — `high | medium | low`
- `enrichment_status` — `pending | partial | complete`
- `enrichment_history` — append-only log of all enrichment actions
- `promoted_at` — when entity reached PROMOTED state

### 20.5 Auto-Assignment Signal Priority
DCM attempts auto-assignment in this order (configurable):
1. Explicit ownership metadata (high confidence)
2. Resource group membership (high confidence)
3. Request history (high confidence)
4. Network/location context (medium confidence)
5. Naming convention (medium confidence)
6. Provider context (medium confidence)
7. No signal → `__transitional__` (low confidence)

### 20.6 V1 Migration (Q55 resolved)
V1 resources have no `tenant_uuid`. V2 requires one (TEN-001). Migration uses the ingestion model:
- Pre-migration analysis pass classifies all V1 resources: `auto_assignable | manually_assignable | orphaned`
- Auto-assignable → bulk Tenant assignment + ingestion record
- Manually assignable → admin queue for human review and assignment
- Orphaned → `__transitional__` Tenant + governance timer
- Migration complete when `__transitional__` Tenant is empty

### 20.7 Brownfield Ingestion
Unmanaged discovered entities follow the same ingestion model:
- Service Provider discovery creates Discovered State records
- DCM identifies unmanaged Discovered State records (no matching Realized State)
- Entity stubs created (state: INGESTED, source: brownfield_discovery)
- Enriched → promoted → Discovered State becomes initial Realized State
- Drift detection active from promotion forward

### 20.8 DCM System Policies for Ingestion

| Policy | Rule |
|--------|------|
| `ING-001` | Every ingested entity must be assigned to one Tenant — real or `__transitional__` — before V2 eligibility |
| `ING-002` | Entities in `INGESTED` or `ENRICHING` state may not be parents for allocated resource claims |
| `ING-003` | `__transitional__` Tenant cannot be deleted, renamed, or used for new provisioning |
| `ING-004` | Every ingested entity must carry an `ingestion_record` in provenance |
| `ING-005` | Entities in `__transitional__` beyond `max_residency_days` must trigger configured escalation |
| `ING-006` | Brownfield entities may not be promoted without explicit actor authorization |
| `ING-007` | At brownfield promotion, Discovered State is promoted to Realized State — DCM assumes lifecycle ownership |

---

## SECTION 21 — POLICY ORGANIZATION: GROUPS, PROFILES, AND POLICY PROVIDERS

### 21.1 Three-Level Policy Organization
```
Policy Profile     — complete use-case configuration (composed of groups)
  │
Policy Groups      — single-concern policy collections (composed of policies)
  │
Policies           — individual Transformation / Validation / Gating Policy rules
  │  optionally sourced from
External Policy Evaluators   — external authoritative policy sources (fifth provider type)
```

### 21.2 Policy Groups
A **Policy Group** is a cohesive collection of policies addressing a single identifiable concern.

**Concern types:** `security | compliance | operational | recovery_posture | zero_trust_posture | data_authorization_boundary | orchestration_flow`

**Key fields:** `handle` (domain/group/name), `concern_type`, `concern_tags`, `extends` (inherits parent), `policies` (constituent policies), `activation_scope` (resource types, tenant tags, regions), `conflicts_with` (explicit conflict declarations), `source` (local or external_policy_evaluator)

**DCM built-in groups include:** core-minimal, dev-defaults, ephemeral-resources, audit-basic, audit-compliance, data-classification, cost-governance, sla-enforcement, hard-tenancy, explicit-cross-tenant, zero-trust, encryption-baseline, pci-dss, gdpr-eu, nist-800-53, iso-27001, fsi-audit, lifecycle-ttl-enforcement, air-gap, kubevirt, openstack, vmware

### 21.3 Policy Profiles
A **Policy Profile** is a complete DCM configuration for a specific use case composed of Policy Groups.

**Six DCM built-in profiles (least to most restrictive):**

| Profile | Handle | Tenancy | Enforcement | Cross-Tenant | Audit |
|---------|--------|---------|-------------|-------------|-------|
| `minimal` | `system/profile/minimal` | Optional — auto-created | Advisory only | allow_all | None |
| `dev` | `system/profile/dev` | Recommended | Warn only | operational_only | Basic 90-day |
| `standard` | `system/profile/standard` | Required | Blocking | explicit_only | Compliance-grade |
| `prod` | `system/profile/prod` | Required | Blocking + SLA | explicit_only | Compliance-grade |
| `fsi` | `system/profile/fsi` | Hard tenancy | Blocking | explicit_only | 7-year retention |
| `sovereign` | `system/profile/sovereign` | Hard tenancy | Blocking | deny_all | 10-year retention |

**Profile inheritance chain:** `system/profile/sovereign` extends `system/profile/fsi` extends `system/profile/prod` extends `system/profile/standard` extends `system/profile/dev` extends `system/profile/minimal`

**Profile activation levels (more specific wins):**
```yaml
installation_config:  default_profile: minimal
platform_config:      active_profile: prod; minimum_tenant_profile: dev
tenant_config:        active_profile: fsi  # must be >= minimum_tenant_profile
```

**Profile shadow validation:** proposed profiles run in shadow mode before activation — same as proposed policies.

### 21.4 External Policy Evaluator (Fifth Provider Type)
A **External Policy Evaluator** is a fifth DCM provider type — an external authoritative source supplying policies into DCM or evaluating/enriching data via external logic.

**Four delivery modes:**

| Mode | Name | `delivery.mode` value | Logic Lives In |
|------|------|----------------------|---------------|
| 1 | DCM Native Push/Pull | `push` / `pull` / `webhook` | DCM Policy Engine |
| 2 | OPA/Rego Bundle | `opa_bundle` | DCM Policy Engine (OPA) |
| 3 | External Schema (naturalization) | `external_schema` | DCM Policy Engine (post-translation) |
| 4 | Black Box Query-Enrichment | `black_box_query` | External provider — opaque to DCM |

**Modes 1-3** deliver policy rules. **Mode 4** is a query-response interface — DCM sends data, external system evaluates and/or enriches, returns structured result.

**Mode 4 can:**
- **Evaluate** — return pass/fail, score, or recommendation
- **Enrich** — inject additional fields into the payload (risk scores, compliance citations, cost predictions, org context, case references)
- **Both** — multi_factor result combining decision + enrichment

**Mode 4 governance requirements:**
- Data sovereignty check before ANY query is sent (BBQ-001, BBQ-003)
- Data minimization — only declared fields sent (BBQ-002)
- Full audit record per query-response cycle (BBQ-004) including `audit_token` for cross-system correlation
- Default failure behavior is `gate` — unknown is not safe (BBQ-005)
- Injected enrichment fields carry standard field-level provenance with `source_type: black_box_provider` + `audit_token` (BBQ-007)
- Override control applies to injected fields — Gating Policy can refuse enrichment (BBQ-008)
- Mode 4 enrichment providers require minimum `transformation` trust level (BBQ-009)

**Trust levels (all modes):**
- `trusted` → Gating Policy authority (dual approval elevation required)
- `verified` → Transformation/Validation only; Mode 4 enrichment minimum
- `untrusted` → advisory only

**`on_update` (Modes 1-3):** `proposed` (shadow validation) | `active` (immediate — trusted only)
**On provider failure:** policies deprecated with configurable sunset; Mode 4 → `on_unavailable` behavior fires

### 21.5 Lifecycle Time Constraints
First-class field on any resource entity. Follow standard data model precedence and override control.

**Two types:**
- `ttl` — ISO 8601 duration relative to reference_point (created_at | realization_timestamp | last_modified)
- `expires_at` — absolute ISO 8601 timestamp

When both declared, earliest wins (LTC-004). Gating Policy can lock as `override: immutable`.

**`on_expiry` actions:** `destroy | suspend | notify | review`

Expiry enforcement is a DCM control plane function — not a provider concern. Failed expiry action → `PENDING_EXPIRY_ACTION` state + escalation (LTC-005).

### 21.6 Cross-Tenancy Authorization — Explicit_Only Default
Default stance is now **`explicit_only`** — informational sharing is NOT open by default. Every cross-tenant relationship of any nature requires an explicit `cross_tenant_authorization` record.

**Authorization specifies who/what/when/where:**
```yaml
cross_tenant_authorization:
  authorized_consumer_tenant_uuid: <uuid>    # WHO
  permitted_fields: [field1, field2]         # WHAT — empty = all fields
  valid_from/valid_until: <ISO 8601>         # WHEN
  permitted_in_regions: [eu-west]            # WHERE
  authorization_level: <tenant_global | resource_specific | field_specific>
  # Hierarchy: field_specific > resource_specific > tenant_global (more specific wins)
```

All cross-tenant authorization decisions are policy-driven and DCM-enforced (XTA-004).

### 21.7 Rehydration Tenancy Controls
Tenancy controls, sovereignty directives, and cross-tenant authorizations **always use current policies during rehydration — cannot be pinned**.

**`policy_version: pinned`** governs resource configuration policies only. Tenancy/sovereignty always current.

When rehydration conflicts with current tenancy controls → entity enters **PENDING_REVIEW** state:
- Allocation not automatically released
- Notifications: entity owner, both Tenant admins, platform admin
- Resolution: re_authorize | release | escalate
- A policy may declare automatic resolution behavior (RHY-004)

### 21.8 System Policy Summary

**LTC:** LTC-001 through LTC-005 — lifecycle time constraint enforcement  
**XTA:** XTA-001 through XTA-005 — cross-tenancy authorization model  
**RHY:** RHY-001 through RHY-004 — rehydration tenancy controls  
**DEP:** DEP-001 through DEP-003 — cross-tenant dependency rules  
**BBQ:** BBQ-001 through BBQ-009 — Mode 4 black box query-enrichment governance

---

## SECTION 22 — UNIVERSAL GROUP MODEL

DCM collapses all grouping constructs into a single **DCMGroup** entity with `group_class` metadata. One mental model, one API, one registry. See `15-universal-groups.md` for the complete model.

### 22.1 Group Classes

| group_class | Replaces | member_types_permitted | exclusivity |
|-------------|---------|----------------------|------------|
| `tenant_boundary` | Tenant | resource_entity, group | one (structural lock) |
| `resource_grouping` | Resource Group | resource_entity | many |
| `policy_collection` | Policy Group | policy | many |
| `policy_profile` | Policy Profile | group | many |
| `layer_grouping` | Layer grouping | layer | many |
| `provider_grouping` | Provider collections | provider | many |
| `composite` | (new) | all types | many |
| `federation` | (new) | group (tenant_boundary) | many |

### 22.2 Structural Invariants (non-overridable)
- `GRP-INV-001` — resource_entity belongs to exactly one tenant_boundary group
- `GRP-INV-002` — constituent relationships cannot cross tenant_boundary boundaries
- `GRP-INV-003` — destroying parent tenant_boundary requires explicit resolution of all children first
- `GRP-INV-004` — resource in child tenant_boundary belongs to child — never parent
- `GRP-INV-005` — circular group membership invalid
- `GRP-INV-006` — group cannot be a member of itself

### 22.3 Composite Groups
`member_types_permitted: [resource_entity, policy, layer, group, provider]`. Policies targeting composite groups apply to all member types by default. Narrow with `member_type_filter`.

### 22.4 Nested Tenants
`tenant_boundary` group with `parent_group_uuid`. Parent has governance overlay and cost rollup — not ownership. Policy inheritance direction is profile-governed (opt_in for minimal/dev/fsi/sovereign; opt_out for standard/prod).

### 22.5 Federated Tenants
`federation` group containing `tenant_boundary` groups as peers. Members remain fully independent. Enables shared governance, consolidated reporting, scoped cross-member visibility.

### 22.6 API Backward Compatibility
`GET /tenants` → `GET /groups?group_class=tenant_boundary`. All existing UUIDs and API endpoints preserved.

---

## SECTION 23 — UNIVERSAL AUDIT MODEL

Every modification to every DCM artifact produces an audit record. No exceptions. See `16-universal-audit.md` for the complete model.

### 23.1 Four Required Fields
**Date/time** (ISO 8601 microseconds) | **Who** (composite actor chain) | **What** (subject entity) | **Action** (closed vocabulary)

### 23.2 Two-Stage Audit — Synchronous Commit + Async Enrichment

**Stage 1 (synchronous, < 1ms, in critical path):**
```yaml
commit_log_entry:
  entry_uuid: <uuid>
  sequence: <integer>           # monotonically increasing
  timestamp: <ISO 8601 microseconds>   # AUTHORITATIVE audit timestamp
  entity_uuid / entity_type / action / actor_uuid / tenant_uuid
  change_fingerprint: <SHA-256>
  status: pending_forward
```
Written using Raft consensus — confirmed when quorum (2/3 or 3/5) of Commit Log replicas acknowledge. Operation returns success after Stage 1. Stage 1 timestamp is the authoritative audit timestamp (AUD-013).

**Stage 2 (asynchronous, out of critical path):**
Audit Forward Service enriches minimal Commit Log entry → full audit_record → hash chain computed → written to Audit Store with retry. Full record visible seconds to minutes after Stage 1.

### 23.3 Composite Actor Chain — The "Who"
```yaml
actor:
  immediate:
    type: <human|system_component|policy|provider|scheduled_job|mode4_provider>
    uuid / display_name
  authorized_by:
    uuid / authorization_method: <direct_action|request_submission|policy_activation|system_policy|scheduled>
  request_uuid / policy_uuid / correlation_id
```

### 23.4 Action Vocabulary (closed — AUD-007)
`CREATE | MODIFY | STATE_TRANSITION | DELETE | ACTIVATE | DEACTIVATE | DEPRECATE | RETIRE | MEMBER_ADD | MEMBER_REMOVE | RELATIONSHIP_CREATE | RELATIONSHIP_RELEASE | AUTHORIZE | REVOKE | EVALUATE | ENRICH | LOCK | HOLD_PLACE | HOLD_CONFIRM | HOLD_RELEASE | DRIFT_DETECT | DRIFT_RESOLVE | INGEST | PROMOTE | EXPIRE | REHYDRATE | QUERY | DISCOVER | LOGIN | LOGOUT | CONFIG_CHANGE`

### 23.5 Retention — Reference-Based
- `retention_status: live` — any referenced entity non-retired → retain unconditionally
- `retention_status: all_retired` → apply governing policy
- Post-lifecycle defaults: dev=P90D, standard=P3Y, prod/fsi=P7Y (DEFAULT), sovereign=P10Y

### 23.6 Tamper-Evidence — Hash Chain
`record_hash` (SHA-256 of record) + `previous_record_hash` (preceding record for this entity) + `chain_sequence`. Chain breaks detectable and trigger security alerts (AUD-010).

### 23.7 Recoverability
- DCM crash after Stage 1 → Audit Forward Service replays `pending_forward` entries on restart (AUD-011)
- Audit Store unavailable → Commit Log accumulates; Audit Forward Service retries when recovered
- Commit Log quorum unavailable → operation aborted — no silent change

### 23.8 System Policies
- `AUD-001` — Every modification produces Commit Log entry synchronously; Commit Log write failure aborts operation
- `AUD-002` — Audit records append-only and immutable while retention obligations apply
- `AUD-003` — Audit records survive at least as long as any referenced entity is live
- `AUD-004` — Post-lifecycle retention governed by policy; default P7Y
- `AUD-005` — Actor field must identify immediate actor + authorized_by chain
- `AUD-006` — record_hash + previous_record_hash hash chain required
- `AUD-007` — Action field must use closed vocabulary
- `AUD-008` — Audit Store must support queries by entity_uuid, actor_uuid, action, timestamp range, tenant_uuid, request_uuid, retention_status
- `AUD-009` — Audit Forward Service delivers with exponential backoff retry; cleared only after Audit Store confirmation AND retention window
- `AUD-010` — Hash chain verification first-class; chain breaks trigger immediate security alerts
- `AUD-011` — On restart, Audit Forward Service replays all pending_forward entries before accepting new operations
- `AUD-012` — Commit Log uses Raft consensus with quorum writes
- `AUD-013` — Stage 1 Commit Log timestamp is authoritative audit timestamp

---

## SECTION 24 — DEPLOYMENT AND REDUNDANCY

Every DCM component and store is designed for redundancy by default. Everything containerized. Profile-governed. Self-hosting. See `17-deployment-redundancy.md` for the complete model.

### 24.1 Core Principles
- **Redundant by default** — every component and store has a redundancy model
- **Everything containerized** — all components run as Kubernetes pods; no bare-metal DCM
- **Profile-governed** — replica counts and quorum set by active Profile; not per-component
- **Stateless control plane** — all state in external stores; any pod can fail and be replaced
- **Self-hosting** — DCM's own deployment is a DCM resource; DCM manages itself

### 24.2 Redundancy Matrix by Profile

| Profile | CP Replicas | Store Replicas | Write Quorum | Zone Spread | Geo-Replication |
|---------|------------|---------------|-------------|------------|----------------|
| `minimal` | 1 | 1 | No | No | No |
| `dev` | 1 | 1 | No | No | No |
| `standard` | 3 | 3 | 2/3 | Preferred | No |
| `prod` | 3 | 3 | 2/3 | Required | Yes |
| `fsi` | 5 | 5 | 3/5 | Required | Yes |
| `sovereign` | 5 | 5 | 3/5 | Required | Within boundary |

### 24.3 Store Redundancy Model

| Store | Implementation | Write Quorum | Notes |
|-------|---------------|-------------|-------|
| Commit Log | etcd (Raft) | 2/3 | Stage 1 audit; < 1ms write |
| GitOps Store | Gitea/equivalent | 2/3 | Intent, Requested, Layers, Policies |
| Event Stream | Kafka/equivalent | 2/3 | Realized, Discovered, Audit events |
| Audit Store | Elasticsearch/equivalent | 2/3 | Indexed, queryable, compliance-grade |
| Search Index | Elasticsearch/equivalent | 1 | Non-authoritative — rebuildable from Git |

### 24.4 Pod Security Model (all components)
`run_as_non_root: true` | `run_as_user: 65534` | `read_only_root_filesystem: true` | `allow_privilege_escalation: false` | `capabilities.drop: [ALL]` | mTLS for all inter-component communication (RED-009)

### 24.5 Self-Hosting
DCM's own deployment is declared as a `dcm_deployment` DCM resource in Git. DCM runs drift detection on its own components. Bootstrap sequence: bootstrap installer → reads `dcm_deployment` from Git → provisions to target redundant state → hands off.

### 24.6 The Repave Scenario
DCM lost entirely → bootstrap installer on new cluster → reads `dcm_deployment` from Git → provisions itself → rehydrates customer workloads in dependency order → drift detection validates. Recovery bounded by infrastructure provisioning speed — not backup restoration.

### 24.7 System Policies
- `RED-001` — All DCM components run as containers in Kubernetes pods
- `RED-002` — All control plane components stateless
- `RED-003` — Profiles above `minimal`: replicas >= 3 with anti-affinity
- `RED-004` — Profiles above `minimal`: quorum writes with write_quorum >= 2
- `RED-005` — Commit Log uses Raft consensus with quorum writes
- `RED-006` — DCM deployment declared as DCM resource in Git
- `RED-007` — DCM runs drift detection on its own components
- `RED-008` — Rolling updates must not reduce replicas below min_available
- `RED-009` — All component communication uses mTLS
- `RED-010` — Bootstrap manifest is the only DCM config outside DCM's management scope

---

## SECTION 25 — WEBHOOKS, MESSAGING, AND EXTERNAL INTEGRATION

### 25.1 The Three Integration Mechanisms
- **Outbound Webhooks** — DCM pushes event notifications to external HTTP endpoints
- **Inbound Webhooks** — External systems push requests, queries, and events to DCM
- **event routing service** — Persistent bidirectional event streaming with external message buses

All three are authenticated, authorized, and audited identically to any other DCM API call. No privileged back-channel.

### 25.2 Universal Ingress/Egress Actor Model

Every request carries an immutable `ingress` block set by the DCM ingress layer:
```yaml
ingress:
  surface: <web_ui|consumer_api|webhook_inbound|message_bus_inbound|
            provider_callback|policy_engine|scheduler|rehydration|
            ingestion|dcm_internal|operator_cli>
  protocol: <https|amqp|kafka|grpc|websocket>
  authenticated_via: <hmac_sha256|mtls|bearer_token|oidc|ldap|...>
  actor:
    uuid / type / display_name / identity_source
    auth_provider_uuid / auth_provider_type
    roles / tenant_scope / groups / permissions
    authorized_by: {method, authorizing_entity_uuid, expiry}
    session_uuid / mfa_verified
    external_identity: {provider, subject, claims}
  webhook_registration_uuid / service_provider_uuid / parent_request_uuid
  source_ip  # audit only — never used for authorization
```
The ingress block is immutable — policies may read but never modify it. Carried verbatim into audit records. Policies can act on any ingress field (surface, actor.roles, auth_provider_type, mfa_verified, etc.).

Egress calls carry DCM's authenticated identity via the `egress` block: component, authenticated_via, credential_ref, originating_request_uuid.

### 25.3 Outbound Webhooks
Optional and policy-governed. Profile sets defaults — fsi/sovereign may require via Policy Group.

Key properties:
- **Schema adapters** — consumer pins to a schema version; DCM transforms forever; 90-day deprecation notice
- **Managed secret rotation** — automatic with transition window; consumer notified via signed event
- **Endpoint health** — suspend-not-delete on failure; full config retained for reactivation
- **Versioned registrations** — standard DCM artifact lifecycle; Git-managed
- **Sovereignty-aware** — delivery blocked if endpoint jurisdiction incompatible with Tenant sovereignty

Delivery: at-least-once; per-entity ordering guaranteed; cross-entity ordering not guaranteed; `event_uuid` is idempotency key.

### 25.4 Inbound Webhooks
DCM exposes typed authenticated endpoints:
- `POST /webhooks/inbound/request` — submit service request
- `POST /webhooks/inbound/query` — query entity state/catalog
- `POST /webhooks/inbound/event` — push provider state change / CI/CD signal
- `POST /webhooks/inbound/ingestion` — push brownfield ingestion data
- `POST /webhooks/inbound/data` — push enrichment or information data

Callers must be registered as **webhook actors** with role, tenant_scope, permitted_operations, and rate_limit. Full Policy Engine evaluation — same as any other API call. Returns 202 Accepted + request_uuid for async operations.

### 25.5 event routing service (Sixth Provider Type)
Persistent bidirectional event streaming. Supports: kafka, amqp, nats, mqtt, azure_service_bus, aws_eventbridge, gcp_pubsub, rabbitmq, custom.

Inbound messages processed as authenticated API calls via registered webhook actor identity. Same Policy Engine evaluation as inbound webhooks.

Architecture: internal Message Bus → Message Bus Bridge Service ↔ external message bus.

### 25.6 Webhook System Policies
WHK-001 through WHK-014 — see doc 18. Key: ING-008 (ingress block immutable), ING-009 (full actor context required), ING-010 (egress authenticated), ING-011 (no anonymous access), ING-012 (webhook/message bus always authenticated).

---

## SECTION 26 — AUTHENTICATION, AUTHORIZATION, AND AUTH PROVIDERS

### 26.1 Auth Provider — The Eighth Provider Type
An **Auth Provider** answers two questions: (1) is this identity who they claim to be? and (2) what are they permitted to do? Every authentication mode is an Auth Provider implementation.

**Authentication is always required — no anonymous access in any profile.** The difference between profiles is how much effort setup requires.

### 26.2 Built-In Auth Provider (zero configuration)
Always registered, cannot be deregistered. Supports:
- **Static API key** — generated at bootstrap, shown once, 30 seconds to start
- **Local users** — `dcm user create --username admin --role platform_admin`
- **GitHub/GitLab OAuth** — opt-in, requires client_id + secret

### 26.3 Auth Modes by Profile

| Profile | Auth Modes | Setup Effort |
|---------|-----------|-------------|
| `minimal` | Static API key, Local user/password | 30 seconds – 2 min |
| `dev` | + GitHub/GitLab OAuth, FreeIPA/AD direct bind | 5–15 minutes |
| `standard` | + OIDC via broker, AD/FreeIPA direct | 30–60 minutes |
| `prod` | + OIDC direct, MFA configurable | 1–2 hours |
| `fsi` | + mTLS required, MFA required | 4–8 hours |
| `sovereign` | + Air-gapped OIDC/mTLS | 1–2 days |

No anonymous access in any profile. No static API key in standard+. mTLS required in fsi/sovereign.

### 26.4 LDAP / FreeIPA / Active Directory
FreeIPA: direct LDAP bind with optional Kerberos SSO and HBAC enforcement. Ideal for Red Hat / Linux-first environments.

Active Directory: LDAP bind with `LDAP_MATCHING_RULE_IN_CHAIN` (OID 1.2.840.113556.1.4.1941) for nested group resolution. `sAMAccountName` or UPN for user lookup. Automatic DC failover.

Both support: group_role_map (external groups → DCM roles), tenant_mapping (external groups → DCM Tenants), group_sync (interval-based re-sync), multiple domain controllers for failover.

### 26.5 Multiple Auth Providers and Routing
Multiple providers registered simultaneously. Ingress layer routes based on authentication signal (mtls_client_cert → mtls provider; bearer_token → OIDC or API key provider; basic_auth → LDAP; hmac_signature → webhook provider; none → reject).

Auth providers can be chained: authentication (LDAP bind) → enrichment (LDAP groups) → augmentation (OIDC userinfo for rich claims like department, cost_center).

### 26.6 credential management service (Seventh Provider Type)
Cross-cutting dependency for all secret resolution. Supports: hashicorp_vault, aws_secrets_manager, azure_key_vault, gcp_secret_manager, kubernetes_secrets, cyberark, delinea, external_api, dcm_internal.

All provider registrations, webhook configurations, and Auth Provider connections reference credentials via:
```yaml
secret_ref:
  service_provider_uuid: <uuid>
  secret_path: "dcm/path/to/secret"
  version: latest
```
Credentials never stored in Git. Never appear in audit record values (only secret_path logged). Cached in memory with configurable TTL.

### 26.7 Auth Provider Health
On unhealthy: existing sessions remain valid until TTL expiry; new auth attempts route to fallback_provider_uuid or are rejected. On_unhealthy options: alert, fallback_to_next, block_new_sessions.

### 26.8 System Policies
AUTH-001 through AUTH-010 — see doc 19. Key: AUTH-008 (no anonymous access in any profile), AUTH-009 (webhook/message bus always authenticated), AUTH-007 (credentials always via credential management service).

---

## SECTION 27 — REGISTRY GOVERNANCE

### 27.1 The Three-Tier Registry

| Tier | Name | Maintained By | Contains |
|------|------|--------------|---------|
| 1 | DCM Core | DCM Project team | Universal types (Compute.VirtualMachine, Network.VLAN, etc.) |
| 2 | Verified Community | Named community maintainers | Technology-specific types (OpenStack.HeatStack, KubeVirt.VirtualMachine) |
| 3 | Organization | Deploying organization | Organization-specific/proprietary types |

### 27.2 The Federated Registry Model
Not centralized, not fully distributed — federated:
```
DCM Project Registry (origin) → Organization Registry (local mirror) → Air-gapped Registry (offline copy)
```
Every DCM deployment has exactly one active **Resource Type Registry** (sub-type of Information Provider). Air-gapped deployments use signed bundles verified against the organization's public key — no external connectivity required.

### 27.3 PR-Based Proposal Workflow (Q9)
Resource Type proposals are Pull Requests against the registry repository. Automated gates before review: schema validation, FQN conflict check, dependency resolution, breaking change detection, test case coverage. Shadow validation in `proposed` status is mandatory before `active` promotion.

**Review periods by change type:** Revision=3 days, Minor/Tier2=7 days, Tier1=14 days, Breaking=21 days, Deprecation=30 days, Emergency=waived (7-day shadow minimum).

### 27.4 Deprecation Lifecycle — Default Policies (Q11)
Deprecation lifecycle is governed by **default DCM system policies** (REG-DP-001 through REG-DP-007), overridable via standard policy priority. FSI/sovereign profiles lock sunset periods as immutable.

| Policy | Default | Overridable? |
|--------|---------|-------------|
| `REG-DP-001` | 30-day notification before deprecation | Yes |
| `REG-DP-002` | Sunset: Tier 1=P12M, Tier 2=P6M | Yes (locked in fsi/sovereign) |
| `REG-DP-003` | Migration window: P90D after retirement | Yes |
| `REG-DP-004` | Successor type required in deprecation notice | Yes |
| `REG-DP-005` | Retired types reject new requests | **No — structural** |
| `REG-DP-006` | Existing realizations → DEPRECATED_RUNTIME | Yes |
| `REG-DP-007` | Emergency migration floor: P30D | **No — floor** |

DEPRECATED_RUNTIME: eligible for modify/decommission; not eligible for rehydration using deprecated type; drift detection continues.

### 27.5 Version Resolution Policy (Q12)
Strictly enforced — no silent resolution to different version. DCM never auto-upgrades across major versions.

`version_policy` options: `exact` | `compatible` (^major) | `latest_minor` (~minor) | `latest`

Profile defaults: minimal=latest, dev/standard/prod=compatible, fsi/sovereign=exact.

### 27.6 Provider Tie-Breaking Hierarchy (Q13)
When multiple providers satisfy all placement criteria equally:
1. **Policy preference** — Transformation policy injected preference_score or preferred_provider_uuid
2. **Provider priority** — numeric field on registration (default: 50; higher = preferred)
3. **Tenant affinity** — Policy Group declares preferred providers for resource types
4. **Cost analysis** — if Cost Analysis has current data AND cost is determinable and comparable (skip if not)
5. **Least loaded** — capacity utilization from reserve_query (skip if data unavailable)
6. **Consistent hash** — SHA-256(request_uuid + resource_type + sorted_candidate_uuids); deterministic, never round-robin

Cost ranks above operational load because it is a business decision. 5% threshold — candidates within 5% cost are treated as equal.

### 27.7 Resource Type Registry — Policy Governed (Q14)
The Resource Type Registry is fully policy-governed. Policies act on registry sync, activation, bundle import, and version upgrades. Profile-appropriate registry policy groups activated by default:

| Group | Profile | Behavior |
|-------|---------|---------|
| `system/group/registry-minimal` | minimal | Advisory; pull everything; warn only |
| `system/group/registry-dev` | dev | Warn on unverified sources; Tier 1+2 |
| `system/group/registry-standard` | standard | Block unverified; sovereignty filter |
| `system/group/registry-prod` | prod | Vendor allowlist; audit all syncs; major version manual approval |
| `system/group/registry-fsi` | fsi | Exact pinning; immutable sunset; dual-approval syncs |
| `system/group/registry-sovereign` | sovereign | Signed bundles only; offline; no external connectivity |

### 27.8 System Policies
REG-001 through REG-007 and REG-DP-001 through REG-DP-007 — see doc 20.

---

## SECTION 28 — STORAGE ARCHITECTURE

### 28.1 Git Repository Structure (Q79)
Handle-based directory structure. Four repos: Intent, Requested, Layers, Policies. Minimal/dev may use monorepo; standard+ use separate repos. `main` is authoritative. Tenant isolation under `{tenant-uuid}` directories. DCM service account handles all Git reads/writes — no direct Tenant Git access.

```
dcm-intent/tenants/{tenant-uuid}/requests/{request-uuid}/intent.yaml
dcm-requested/tenants/{tenant-uuid}/requests/{request-uuid}/requested-payload.yaml
dcm-layers/{domain}/{type}/{name}/v{Major}.{Minor}.{Revision}.yaml
dcm-policies/{domain}/{type}/{name}/v{Major}.{Minor}.{Revision}.yaml
```

### 28.2 Multi-Region Replication (Q80)
Declared capability on store configuration. Active Profile determines minimum requirements:
- minimal/dev: 1 replica, no multi-region
- standard: 3 replicas, strong/bounded consistency
- prod/fsi/sovereign: 3-5 replicas, strong consistency, geo-replicated
- sovereign: multi-region required but within sovereignty boundary only

(STO-001)

### 28.3 Data Store Failure Handling (Q81)
Per store type — policy-governed:
- **Commit Log:** quorum unavailable → abort operation (no silent changes)
- **GitOps Stores:** unavailable → queue writes locally (max size + max age); explicit reject on exhaustion
- **Event Stream:** producer queues locally; consumer resumes from last offset on recovery
- **Audit Store:** two-stage model — accumulates in Commit Log; operations not blocked
- **Search Index:** non-authoritative; degrades gracefully; full rebuild on recovery

(STO-002)

### 28.4 Search Index — Separate Sub-Type (Q82)
Separate PostgreSQL store contract — distinct from GitOps stores. Non-authoritative, rebuildable from authoritative stores. Consistency lag declared (e.g., PT5M). API queries may specify `freshness: authoritative` to bypass index. (STO-003)

### 28.5 Audit Store — Specialized Sub-Type (Q83)
Specialized PostgreSQL store contract — NOT the same as Event Stream. Properties: append-only with immutability enforcement, hash chain integrity, reference-based retention tracking, compliance-grade multi-dimensional queries. Event Stream is the delivery channel; Audit Store is the compliance destination. (STO-004)

---

## SECTION 29 — PROVIDER SOVEREIGNTY DECLARATIONS

### 29.1 Obligation
Every provider registration (Service, Information, Message Bus, Policy, Auth Provider) MUST include a `sovereignty_declaration` block. Contractual obligation — not optional metadata.

### 29.2 What Sovereignty Declaration Covers
- **operating_jurisdictions** — countries and legal jurisdictions where provider physically operates
- **legal_frameworks** — applicable frameworks (GDPR, HIPAA, FedRAMP, ITAR, etc.)
- **data_residency_guarantee** — data never leaves declared jurisdictions (true/false)
- **data_transit_jurisdictions** — jurisdictions data transits through during operations
- **external_dependencies** — external connectivity requirements, air_gap_capable flag, external services with data sharing details
- **sub_processors** — third-party sub-processors with jurisdiction and data handled
- **government_access_risk** — which governments can legally compel access
- **certifications** — current certifications with validity periods (ISO-27001, SOC2, PCI-DSS, FedRAMP)
- **audit_rights** — customer audit rights and notice periods
- **change_notification** — mandatory notification events and SLA (e.g., PT24H)

### 29.3 Change Notification and DCM Response
Provider MUST notify DCM when any sovereignty data changes. DCM treats sovereignty changes as discovered drift → Policy Engine re-evaluation:
- **No violations:** update record, emit webhook event, notify Tenants (informational)
- **Violations found:** for each affected resource, policy declares action:
  - `notify_only` — inform Tenant; no automatic action
  - `pause` — suspend resource; Tenant must act
  - `migrate` — Provider-Portable Rehydration to compliant provider (sequential)
  - `emergency_migrate` — parallel provisioning before decommission

Sovereignty violation record created in Audit Store. Notifications: Tenant owner, platform admin, data_protection_officer.

### 29.4 Auto-Migration
Policy declares `migrate` or `emergency_migrate` → DCM uses Provider-Portable Rehydration. Non-compliant provider excluded from placement candidate set. Full audit trail linking violation record to migration request. (SOV-001 through SOV-005)

---

## SECTION 30 — GIT PR INGRESS

### 30.1 Concept
DCM supports `git_pr_merge` and `git_pr_open` as ingress surfaces. Teams submit standard DCM resource definition YAML as Pull Requests. DCM's Git Request Watcher monitors designated repositories.

### 30.2 Git Actor Identity Resolution
**DCM trusts the Git server's authentication assertion — not user-declared Git configuration.** Git `user.email` self-declaration is ignored — spoofing vector.

Resolution methods (all go through registered Auth Provider):
- `oidc_subject_lookup` — Git server OAuth subject → OIDC Auth Provider → DCM actor
- `ldap_username_lookup` — Git server username → LDAP/AD Auth Provider → DCM actor
- `ssh_key_fingerprint` — key fingerprint → DCM SSH key registry → DCM actor
- `webhook_service_account` — CI/CD service account → registered webhook actor

**The resolved actor has IDENTICAL roles, groups, and tenant scope to the same user logging in via web UI.** Git PR ingress does not grant different permissions than any other surface. Same Auth Provider, same group mappings, same tenant scope enforcement.

**Unresolvable identity → explicit PR rejection comment** with actionable guidance. Never silently ignored.

### 30.3 PR Lifecycle
1. PR opened → DCM resolves author → Auth Provider → shadow policy evaluation posted as PR comments
2. Human review + Git branch protection approvals
3. PR merged → actor re-verified at merge time (not assumed from PR open) → full nine-step assembly → realization result posted as PR comment
4. Realized state committed to `realized/` directory (optional)

### 30.4 The git_context in ingress block
```yaml
ingress:
  surface: git_pr_merge
  actor: <fully resolved DCM actor — same as web UI login>
  git_context:
    repository / pr_number / pr_url / merge_commit
    pr_author / pr_reviewers / pr_approved_by
    # pr_approved_by: DCM resolves reviewer Git identities via same Auth Provider
```

### 30.5 Policy Use Cases
- Require specific approvers in pr_approved_by before processing
- Require MFA for Git PR merges in prod Tenants
- Restrict resource types submittable via Git PR
- Require actor to be in authorized Tenant group
- Post shadow evaluation results as PR comments

### 30.6 System Policies
GIT-001 through GIT-008 — see doc 18. AUTH-011 — Git identity resolution uses registered Auth Provider; same role/group/tenant scope as any other ingress.

---

## SECTION 31 — ENTITY AND DEPENDENCY GAPS

### 31.1 Ownership Transfers (Q25)
Ownership transfers are **unlimited by default**. Each transfer is immutably recorded with a monotonically incrementing `transfer_number` and mandatory reason field. Policy may declare a maximum per resource type via Gating Policy. ENT-001.

### 31.2 Bare Metal Indivisibility (Q26)
`Compute.BareMetal` declares `allocation_model: whole_unit` and `shareability.allowed: false` (structural lock). Placement holds are exclusive — no concurrent holds on the same server. Provider must report full physical identity (serial_number, hardware_profile) in realized payload and notify DCM of any sharing attempt. ENT-002.

### 31.3 Capacity Confidence Actions (Q27)
Confidence ratings trigger policy-governed automatic actions:
- `HIGH` → proceed (all profiles)
- `MEDIUM` → proceed_with_warning (minimal/dev) or refresh_before_placement (prod/fsi/sovereign)
- `LOW` → proceed_with_warning (minimal), refresh_before_placement (dev/standard), reject (prod/fsi/sovereign)

LOW confidence triggers a Mode 1 Information Provider query before finalizing placement in standard+ profiles. Policy Group overrides per resource type. ENT-003.

### 31.4 Process Resource Execution Time (Q28)
`max_execution_time` is **mandatory** on Process Resource entities. Enforced by the Lifecycle Constraint Enforcer as a standard TTL. Profile governs default `on_max_exceeded`:
- minimal/dev: `notify`
- standard/prod: `escalate`
- fsi/sovereign: `terminate`

ENT-004.

### 31.5 SUSPENDED State Billing (Q29)
`billing_state` is a first-class field on all entities: `billable | non_billable | reduced_rate`. Policy injects `billing_state` and `billing_metadata` (rate_multiplier, billable_components) during state transitions. Cost Analysis component consumes the field — DCM carries the billing signal, policy decides the billing model. ENT-005.

### 31.6 Dependency Graph Versioning (Q30)
Dependency graphs versioned as part of their parent catalog item — not independently. New required dependency or removed dependency = **major (breaking) version bump**. New optional dependency = minor bump. Constraint change = revision bump. Dependency graph version captured in assembly provenance. ENT-006.

### 31.7 Dependency Graph Storage (Q31)
Not a separate entity. Three levels:
- Declared graph: embedded in Resource Type Specification (GitOps)
- Resolved graph: embedded in `placement.yaml` in Requested State
- Realized graph: Realized State events per dependency

ENT-007.

### 31.8 Dependency Graph Depth (Q33)
Profile-governed maximum: minimal=20, dev=15, standard/prod=10, fsi/sovereign=7. Requests exceeding max depth rejected with clear error. Circular dependency detection always enforced regardless of depth configuration. ENT-008.

### 31.9 Composite Service Composition Visibility (Q34)
A Composite Service registration declares `composition_visibility`:
- `opaque` — consumer sees only top-level service; sub-resources not in DCM; drift on realized payload only
- `transparent` — all sub-resources registered as DCM entities; full drift detection
- `selective` — provider declares which sub-resources are DCM-visible

ENT-009.

### 31.10 System Policies
ENT-001 through ENT-009 — see docs 06 and 07.

---

## SECTION 32 — INFORMATION PROVIDER CONFIDENCE SCORING AND AUTHORITY

### 32.1 Confidence Scoring — 0 to 100
Every Information Provider field value carries a confidence score (0-100). DCM computes scores — providers do not self-declare. Score bands for policy use: very_high (81-100), high (61-80), medium (41-60), low (21-40), very_low (0-20).

**Formula:**
```
confidence_score = min(100, base_score × freshness_multiplier × corroboration_multiplier × authority_multiplier)
```

| Factor | Values |
|--------|--------|
| Base score | primary_authoritative=90, secondary=70, discovered=60, advisory=50, self_reported=40, inferred=30 |
| Freshness | <1h=1.00, <1d=0.95, <7d=0.85, <30d=0.70, >30d=0.50 |
| Corroboration | 1 source=1.00, 2 agree=1.10, 3+ agree=1.15, disagree=0.60 |
| Authority | primary=1.00, secondary=0.85, advisory=0.70 |

### 32.2 Authority as Layer Data
Authority scope and priority for Information Providers are declared in **platform or system domain layers** — not just policies. This is static organizational knowledge ("our CMDB is authoritative for business unit data"). Layer-defined authority establishes the default; policies act on confidence scores at runtime.

### 32.3 Ingestion-Time Conflict Detection
Conflict detection at ingestion time (7-step flow): schema validation → authority scope check → confidence score computation → conflict detection → resolution policy → entity record update → INGEST audit record.

**Resolution strategies:** `higher_authority_wins` | `higher_confidence_wins` | `higher_priority_wins` | `escalate` | `merge` (array fields only)

Authority scope conflicts detected at **registration time** — two providers claiming primary authority for the same field cannot both go active without explicit resolution.

### 32.4 Write-Back (Q63)
Optional declared capability. Policy triggers write-back — never automatic. Produces ENRICH audit records. Credentials via credential management service. (INF-002)

### 32.5 Extended Schema Versioning (Q64)
Semver semantics: field removal/type change = major (breaking); new optional field = minor; constraint change = revision. Migration plan required for major bumps. (INF-003)

### 32.6 Well-Known Provider Registry (Q65)
Three-tier registry (Core/Community/Organization) — same governance model as Resource Type Registry. Separate registries, shared infrastructure. (INF-004)

### 32.7 Air-Gapped Verification (Q66)
Three modes: pre-verified signed bundle, internal mTLS (for internal providers), periodic online re-verification with cached tokens. Profile governs cache expiry behavior. (INF-005)

### 32.8 System Policies
INF-001 through INF-008 — see docs 10 and 21.

---

## SECTION 33 — DCM FEDERATION AND CROSS-INSTANCE COORDINATION

### 33.1 Three Relationship Types
- **Peer DCM** — same organizational level; share resources/information
- **Parent-Child DCM** — hierarchical; parent has governance overlay; does not own child resources
- **Hub DCM** — specialized parent as resource allocation clearinghouse

All use the Universal Group Model: federation group (peers) or tenant_boundary nesting (parent-child).

### 33.2 Provider Federation Eligibility
Every provider registration declares `federation_eligibility`:
- `mode: none` — cannot participate in any federation (sovereign/classified providers)
- `mode: selective` — only with explicitly declared partners
- `mode: open` — any trusted DCM peer (sovereignty checks always apply)

**Layer-defined defaults** in `platform` domain layer. Individual registrations may be **more restrictive** — never more permissive without Gating Policy approval.

**Federation scope declares:** permitted resource types + operations, data sharing permissions, max concurrent allocations. Remote DCMs CANNOT decommission local resources through a tunnel.

**Storage providers default to `mode: none`** — data sovereignty prohibits storage federation unless explicitly authorized.

### 33.3 The DCM Provider — Ninth Provider Type
Wraps another DCM instance's API. Always mTLS (non-configurable). Sovereignty checks mandatory before tunnel establishment. Local DCM policies govern ALL resources from any tunnel.

**Non-negotiable primary concerns on all tunnels:**
- Sovereignty: verified before establishment; data classification checked per egress
- Authentication: always mTLS — no API key or bearer token
- Authorization: local policies govern; remote policies cannot override
- Audit: records in BOTH DCM instances; shared correlation_id
- Observability: cross-DCM allocation visible in both instances

### 33.4 Cross-DCM Confidence Scoring
```
cross_dcm_confidence = source_resource_confidence × (tunnel_trust_score / 100)
```
Federation trust score (0-100): factors include identity verification, sovereignty compatibility, certifications currency, audit trail integrity, uptime, compliance.

### 33.5 DCM Export/Import
Signed export package: tenants, layers, policies, provider registrations (not credentials), entity intent/requested states, groups, audit records with hash chain. Never export credentials.

Import trust score (0-100): source verification + sovereignty compatibility + data completeness + schema compatibility + audit trail integrity. Low score → reject or escalate.

### 33.6 System Policies
DCM-001 through DCM-008 — see doc 22.

---

## SECTION 34 — OPERATIONAL AND PERFORMANCE GAPS

### 34.1 Field-Level Provenance Models (Q7, Q8)

**Three configurable models — organization chooses; profile provides default:**

**Model A — Full Inline**
All provenance stored on entity record. Simplest queries, highest storage cost, no tooling required.
- ✅ Auditors read one record — regulatory clarity
- ✅ No dependency on layer chain store
- ❌ Very high storage volume at scale
- ❌ Write amplification

**Model B — Deduplicated (Content-Addressed) ← RECOMMENDED**
Layer chain is the deduplication key. Classical content-addressed dedup (like Git objects, Docker layers). Only delta fields store unique provenance. 95-99% storage reduction for standardized deployments. Lossless because layer chains are immutable.
- ✅ Dramatic storage reduction
- ✅ Full audit reconstruction always possible
- ✅ Write performance highest (layer-matching fields free)
- ❌ Chain traversal tooling required for queries
- ❌ Layer chain must be retained while any entity references it

**Model C — Tiered Archive**
Hot (full detail) → warm (change events) → cold (hash anchors). Degrades gracefully.
- ✅ Balances cost and access speed
- ✅ Compliant for long retention
- ❌ Cross-tier queries for long time ranges
- ❌ Cold tier requires full records from warm/hot for reconstruction

**Model B+C — Combined**
Maximum efficiency: content-addressed dedup + tiered archival of chains and deltas.

**Profile defaults:**

| Profile | Provenance Group | Rationale |
|---------|----------------|-----------|
| minimal, dev | `system/group/provenance-full-inline` | Simplicity; scale not a concern |
| standard, prod | `system/group/provenance-deduplicated` | Scale matters; tooling justified |
| fsi, sovereign | `system/group/provenance-full-inline` | Regulatory clarity; self-contained |

Organizations override by swapping the active provenance Policy Group.

**Audit completeness guarantee (OPS-002):** Regardless of model, full provenance is always reconstructable from entity record + layer chain store + Audit Store combined.

### 34.2 Background Conflict Validation (Q85)
Event-triggered (primary) on layer ingestion/update — async, non-blocking. Scheduled weekly sweep as safety net. Both triggers produce same conflict record format and audit trail. (OPS-003)

### 34.3 Policy Minimum Review Periods (Q86)
Change-type minimum periods: Gating Policy=14d, Validation=7d, Transformation=3d. Profile multipliers: minimal=0×, dev=0.5×, standard=1×, prod=1.5×, fsi/sovereign=2×. DCM enforces — not bypassable except emergency activation with dual-approval audit. (OPS-004)

### 34.4 Shadow Evaluation Store (Q87)
Dedicated **Validation Store** (not Audit Store). Queryable and modifiable. Links to Audit Store EVALUATE events via audit_record_uuid. Default retention P90D after policy promotion/retirement. (OPS-005)

### 34.5 Artifact Status Extensions (Q88)
Five standard statuses (developing/proposed/active/deprecated/retired) are invariant — no custom additions. Organizations use status_metadata for workflow state (purely informational, no system behavior). Policy gates status transitions based on status_metadata field values. (OPS-006)

### 34.6 System Policies
OPS-001 through OPS-006 — see docs 03 and 06.

---

## SECTION 35 — PROFILE COMPOSITION — POSTURE AND COMPLIANCE DOMAINS

### 35.1 The Two-Dimensional Profile Model

**Profiles compose two orthogonal dimensions:**

```
Complete Profile = Deployment Posture Group + Compliance Domain Group(s)
```

**Dimension 1 — Deployment Posture** (vertical axis): How DCM infrastructure behaves — redundancy, enforcement strictness, audit retention, tenancy model.

| Posture Group | Key Behaviors |
|--------------|--------------|
| `system/group/posture-minimal` | Advisory; single instance; no redundancy |
| `system/group/posture-dev` | Warn-not-block; basic logging |
| `system/group/posture-standard` | Full enforcement; 3-replica; explicit cross-tenant |
| `system/group/posture-prod` | Full enforcement + SLA; geo-replicated |
| `system/group/posture-hardened` | 5-replica; 7-year audit; dual approval |
| `system/group/posture-sovereign` | Air-gap; deny_all; 10-year audit; signed bundles |

**Dimension 2 — Compliance Domain** (horizontal): Which regulatory frameworks govern data and resources.

| Compliance Group | Domain |
|----------------|--------|
| `system/group/compliance-fsi` | Financial Services — Basel III, SOX, Dodd-Frank |
| `system/group/compliance-pci-dss` | Payment Card Industry — PCI-DSS v4 |
| `system/group/compliance-hipaa` | Healthcare — HIPAA/HITECH PHI |
| `system/group/compliance-fedramp-moderate` | US Federal Moderate — NIST 800-53 Moderate |
| `system/group/compliance-fedramp-high` | US Federal High — NIST 800-53 High |
| `system/group/compliance-dod-il2` through `il6` | DoD Impact Levels |
| `system/group/compliance-government` | Government/public sector |
| `system/group/compliance-gdpr` | EU GDPR data protection |
| `system/group/compliance-iso27001` | ISO 27001 information security |
| `system/group/compliance-nist-800-53` | NIST 800-53 security framework |
| `system/group/compliance-soc2` | SOC 2 service organization controls |
| `system/group/compliance-nerc-cip` | Critical infrastructure energy/utilities |
| `system/group/compliance-sovereign` | Sovereign/classified — air-gap, HSM, signed bundles |

### 35.2 Built-In Profile Compositions

The six core profiles are posture+compliance compositions:

```
minimal = posture-minimal
dev = posture-dev
standard = posture-standard
prod = posture-prod
fsi = posture-hardened + compliance-fsi + compliance-pci-dss + compliance-iso27001
sovereign = posture-sovereign + compliance-sovereign
```

**Extended built-in profiles:**

| Profile | Extends | Compliance Groups Added |
|---------|---------|------------------------|
| `system/profile/hipaa-prod` | prod | compliance-hipaa, compliance-iso27001 |
| `system/profile/hipaa-sovereign` | sovereign | compliance-hipaa |
| `system/profile/fedramp-moderate` | prod | compliance-fedramp-moderate, compliance-nist-800-53 |
| `system/profile/fedramp-high` | sovereign | compliance-fedramp-high, compliance-nist-800-53 |
| `system/profile/government` | prod | compliance-government, compliance-nist-800-53 |
| `system/profile/dod-il4` | sovereign | compliance-dod-il4, compliance-fedramp-high, compliance-nist-800-53 |
| `system/profile/dod-il5` | dod-il4 | compliance-dod-il5 |
| `system/profile/dod-il6` | dod-il5 | compliance-dod-il6, compliance-sovereign |

### 35.3 HIPAA Compliance Group Key Controls
- PHI field classification enforcement (phi: true tag required)
- PHI access control (phi_authorized role required)
- Audit retention: P6Y minimum
- AES-256 at rest, TLS 1.3 in transit for PHI
- Breach notification workflow via sovereignty_violation_record
- BAA tracking: providers declare baa_in_place in sovereignty_declaration
- Minimum Necessary standard on Mode 4 data_request_spec

### 35.4 Government/DoD Key Controls
- Data classification mandatory on all resources
- Cross-boundary controls for classification levels
- Audit retention: P10Y minimum
- DoD IL4+: CUI handling markers; foreign sub-processor exclusion
- DoD IL5+: sovereign posture within US boundary
- DoD IL6: classified + HSM required for key management

### 35.5 Tenant-Level Compliance Overlay
**One DCM deployment, multiple compliance postures per Tenant:**
```yaml
tenant_config:
  active_profile: system/profile/prod     # posture from platform
  compliance_groups:
    - system/group/compliance-hipaa        # this Tenant handles PHI
    - system/group/compliance-pci-dss      # this Tenant processes payments
```
Clinical Tenants (HIPAA) + Billing Tenants (HIPAA + PCI-DSS) + Admin Tenants (standard) — all on same DCM platform.

### 35.6 System Policies
- `PROF-001` — Profiles compose posture + compliance domain groups
- `PROF-002` — Compliance groups apply at platform or Tenant level; additive not replacing
- `PROF-003` — DCM ships built-in compliance groups for all major domains
- `PROF-004` — implementation_posture groups (provenance model etc.) are independent of compliance domain

---

## SECTION 36 — GROUPING AND RELATIONSHIP GAPS

### 36.1 Group Subclass Registry (Q35)
No separate registry needed. `group_class` is the closed system-behavior set. `group_subclass` is open and advisory — freely declared, never validated. DCM ships a community subclass catalog as a non-authoritative reference (same infrastructure as well-known provider registry). GRP-011.

### 36.2 Group Sovereignty Interaction (Q36)
Class-specific sovereignty rules:
- `tenant_boundary` — NEVER cross-sovereignty (structural, not configurable)
- `resource_grouping` — permitted by default; policy may restrict for classified resources
- `policy_collection` / `layer_grouping` — always permitted (governance artifacts, no data)
- `composite` — governed by most restrictive member type
- `federation` — permitted with DCM federation rules (DCM-003)

GRP-012.

### 36.3 Tenant Decommission Lifecycle (Q37)
Mandatory four-phase staged decommission:
1. **Pre-decommission validation** (blocking): resource state, cross-tenant relationships, compliance holds, rehydration leases, child groups resolved first
2. **Resource decommission**: cascade (default) / retain (ORPHANED state) / notify (PENDING_DECOMMISSION)
3. **Group membership cleanup**: remove from all memberships; empty federation groups → EMPTY state
4. **Audit record archival**: all records enter post-lifecycle retention — NEVER destroyed

Child tenant_boundary groups must be resolved BEFORE parent decommission (GRP-INV-003). GRP-013.

### 36.4 Time-Bounded Group Membership (Q38)
Already in Universal Group Model via `valid_from` / `valid_until` on every membership. Lifecycle Constraint Enforcer handles expiry. `on_expiry` actions: `remove` / `notify` (default) / `suspend_member`. `warn_before_expiry: P7D` standard. Expiry produces `MEMBER_REMOVE` audit record with `reason: membership_ttl_expired`. GRP-014.

### 36.5 Group Policy Inheritance (Q39)
Class-specific defaults, all profile-governed:
- `tenant_boundary`: `opt_out` (standard/prod) — parent cascades unless child excludes; `opt_in` (minimal/dev/fsi/sovereign)
- `federation`: always `opt_in` — peer consent required, not configurable
- `composite`: `opt_out` by default, configurable
- `resource_grouping` / `policy_collection`: not applicable

GRP-015.

### 36.6 Relationship Role Validation (Q58)
Advisory by default. Resource Type Spec may declare `permitted_relationship_roles` with `role_validation: advisory | enforced`. Advisory → assembly warning for unknown roles. Enforced → unknown roles rejected at request time. DCM ships community role catalog as non-authoritative reference. REL-020.

### 36.7 Relationship Graph Depth (Q60)
Profile-governed max: minimal=25, dev=20, standard/prod=15, fsi/sovereign=10. Circular detection always enforced. Depth = graph traversal distance between any two entities (NOT count of relationships on one entity). REL-021.

### 36.8 System Policies
GRP-011 through GRP-015 — see doc 15. REL-020, REL-021 — see doc 09.

---

## SECTION 37 — AUDIT AND OBSERVABILITY GAPS

### 37.1 Information Provider Trust Score Validation (Q15)

Dual-trigger model — same pattern as conflict validation:

**Event-triggered (primary):** push fails schema validation → degraded; push conflicts with primary authority → degraded; health check fails → degraded; sovereignty declaration change → re-evaluated; registration update → re-verification triggered.

**Scheduled (safety net):** daily health check; weekly full re-verification (identity, sovereignty, certifications, schema). fsi/sovereign: daily full re-verification.

**Trust score → source_trust mapping:**
- Score ≥ 80: `verified` → confidence multiplier 1.00
- Score 60-79: `degraded` → confidence multiplier 0.75
- Score < 60: `suspended` → no new pushes accepted; score = 0

(INF-009)

### 37.2 Confidence Scoring — The Hybrid Descriptor Model (Q15 extended)

**Three-tier model:**
- **Confidence Descriptor** (primary — stored): `authority_level` + `corroboration` + `source_trust` + `last_updated_at`
- **Derived Score** (0-100, computed on demand): mathematical composition for placement and conflict resolution
- **Derived Band** (very_high/high/medium/low/very_low, computed on demand): what humans and policies use

**Who sets each field:**
- `authority_level`: set at registration from authority declaration layer (static per field per provider)
- `corroboration`: computed at ingestion (confirmed/single_source/contested based on multi-provider comparison)
- `source_trust`: maintained by trust scoring system (event-triggered + scheduled)
- `last_updated_at`: set at each push event

**Score formula:** `min(100, base(authority_level) × freshness_mult × corroboration_mult × trust_mult)`

**Freshness is computed at query time** from `now - last_updated_at` — never stored (avoids staleness). Score and band computed at query time for the same reason.

**Audit reconstruction:** authority_level (from registration) + corroboration (from ingestion event) + source_trust (from trust audit) + last_updated_at (from push event) → score and band fully reconstructable from stored facts.

**Configurable derivation:** base scores, freshness thresholds, and band thresholds configurable via Policy Group — stored as versioned policy artifacts.

### 37.3 Audit vs Observability — Definitively Separate (Q16)

| | Audit | Observability |
|--|-------|--------------|
| Purpose | WHAT HAPPENED + WHO authorized | SYSTEM HEALTH + PERFORMANCE |
| Consumers | Auditors, compliance, legal | SREs, operators, dashboards |
| Write rate | Low (per action) | Very high (per second) |
| Retention | P7Y+ | Days to months |
| Mutability | Never — append-only | Downsampling acceptable |
| Accuracy | 100% required | Statistical sampling OK |
| Failure | Missing = compliance violation | Missing = operational inconvenience |

They cannot be combined without violating one contract or the other. Observability may reference audit record UUIDs for correlation. AUD-013.

### 37.4 Curated Observability Event Stream (Q17)

DCM publishes a curated event stream via Message Bus — NOT raw metrics. Policy governs what is published, subscriber roles, and redaction. Published by default: component.health_changed, resource.state_transition, capacity.threshold_crossed, drift.detected, security.gating_triggered, provider.confidence_changed. NOT published by default: metrics.raw (explicit policy opt-in required).

Observability events on Message Bus do NOT replace audit records. OBS-001.

### 37.5 System Policies
- `INF-009` — dual-trigger trust score; degraded/suspended states; policy governs thresholds
- `AUD-013` — audit and observability definitively separate; different contracts/consumers
- `OBS-001` — curated observability event stream via Message Bus; policy-filtered; raw metrics opt-in only

---

## SECTION 38 — OVERRIDE CONTROL AND ENHANCEMENT GAPS

### 38.1 The Complete Field Lifecycle Contract

Three questions together define the full field governance model across a resource's lifecycle:

```
ASSEMBLY TIME (Q50 — override_preference):
  Which layers can set this field?
  immutable → only this layer and higher-domain layers
  constrained → any layer within declared bounds
  allow → any layer

CATALOG PRESENTATION (Q52 — constraint_visibility):
  What does the consumer see about this field's constraints?
  full → constraint + bounds + reason + suggestions
  summary → bounds only
  hidden → enforced silently

POST-REALIZATION (Q56 — editability):
  Can the consumer change this field after provisioning?
  editable: false → requires reprovisioning
  editable: true → targeted delta update permitted (within edit_constraints)
```

### 38.2 Override Preference Enforcement (Q50)

`override: allow | constrained | immutable` on layer fields is enforced by the Request Payload Processor during assembly **Step 3 (Layer Merge)**. No separate Gating policy needed.

**Authority rule:** `immutable` prevents overrides from lower-authority domains only. A platform domain `immutable` field blocks tenant/service/provider/request — but system domain can still override. Higher authority always wins.

**Gating Policy escalation:** A Gating policy may additionally lock an `allow` or `constrained` field at runtime — for compliance mandates the layer author didn't anticipate.

**Enforcement:** If a lower-priority layer or consumer sets an `immutable` field → assembly halts with clear error identifying the conflicting layer and locking layer.

LAY-005.

### 38.3 Constraint Schema Visibility (Q52)

Constrained fields expose their constraint schema to consumers in the Service Catalog UI and Consumer API at a policy-governed disclosure level.

**Disclosure levels:** `full` (constraint + bounds + reason + suggestions), `summary` (bounds only), `hidden` (silently enforced)

**Profile defaults:** minimal/dev/standard → full; prod/fsi → summary; sovereign → hidden

**API:** `GET /api/v1/catalog/items/{id}/schema` returns field schemas at the declared visibility level for the authenticated consumer's Tenant profile.

Policy may override per field or resource type.

LAY-006.

### 38.4 Post-Realization Field Editability (Q56)

**Editability is orthogonal to override_preference:**
- `override` governs assembly time (which layers can set the field during request construction)
- `editable` governs post-realization (can the consumer update the field on a running resource)

**Declared on Resource Type Specification:**
```yaml
fields:
  cpu_count:    editable: true; edit_constraints: {range: 1-32}; requires_restart: true
  hostname:     editable: false; non_editable_reason: "Requires reprovisioning"
  dns_servers:  editable: true; requires_restart: false
  region:       editable: false; non_editable_reason: "Region immutable post-realization"
```

**Update request flow:** validate editable → validate edit_constraints → evaluate edit_policy → produce delta Requested State → dispatch delta to provider → update Realized State

**Critical:** Updates are targeted deltas — **layers do NOT re-run**. Only changed fields validated and dispatched. Layer chain NOT re-assembled for updates.

Editable fields and edit_constraints visible in Service Catalog at same constraint_visibility level as constraint schemas.

ENT-010.

### 38.5 System Policies
- `LAY-005` — override: allow/constrained/immutable enforced at Step 3; immutable = lower-authority only; Gating Policy may additionally lock
- `LAY-006` — constraint schema visible at full/summary/hidden level; profile-governed; API endpoint
- `ENT-010` — editability first-class on Resource Type Spec; independent of override_preference; updates = targeted deltas; layers do not re-run

---

## SECTION 39 — FOUR STATES OPERATIONAL GAPS

### 39.1 Entity UUID Preservation on Rehydration (Q75)

Entity UUIDs are **preserved on rehydration** — UUID is the stable logical identity across all provider migrations, sovereignty changes, and lifecycle events. All external references (CMDB, cost attribution, audit trails, relationships, dependencies) use UUID. Generating a new UUID would silently break all references.

What changes: the **provider-side identifier** (actual VM ID, container name, resource handle). Recorded in `rehydration_history`:
```yaml
entity:
  uuid: <original-uuid>    # PRESERVED
  rehydration_history:
    - rehydration_uuid: <uuid>
      from_realized_entity_id: "vm-12345"   # no longer valid
      to_realized_entity_id: "vm-67890"     # new provider ID
      trigger / from_provider / to_provider / rehydrated_by
      intent_state_ref / previous_requested_state_ref / new_requested_state_ref
```

**Rehydration is transactional** — failure preserves pre-rehydration state completely; no UUID change, no partial state. RHY-005.

### 39.2 Pinned Authentication Level for Rehydration (Q76)

Entities may declare `rehydration_constraints.min_auth_level` — a minimum floor the rehydrating actor must meet. Prevents privilege escalation through the rehydration mechanism.

Auth levels (ascending): `api_key → ldap_password → oidc → oidc_mfa → hardware_token → hardware_token_mfa`

**Profile enforcement:** minimal/dev = not enforced; standard = advisory warn; prod = enforced reject; fsi = enforced + dual approval on mismatch; sovereign = dual approval always.

**Automated rehydration** (DCM service account for provider migration): requires `allow_delegated_rehydration: true` OR platform admin manual authorization → full audit trail preserving accountability. RHY-006.

### 39.3 Concurrent Rehydration Handling (Q77)

**Exclusive rehydration lease per entity** — only one rehydration active at a time.

```yaml
rehydration_lease:
  entity_uuid / lease_uuid / acquired_by / acquired_at
  lease_ttl: PT2H    # expires if rehydration hangs
  trigger / status: active|completed|failed|expired
```

**Concurrent request:**
- Active lease + higher priority incoming → escalate to platform admin; queue
- Active lease + same/lower priority → reject with retry guidance; REHYDRATION_BLOCKED audit

**Priority (1=highest):** security/compliance emergency → manual platform admin → automated sovereignty migration → provider decommission → manual consumer request

**TTL expiry:** marks rehydration `failed`; releases lease; triggers drift detection for partial completion assessment. RHY-007.

### 39.4 Discovered State Retention (Q78)

Ephemeral operational data — NOT the source of truth (Realized State is). Three modes:

| Mode | Behavior |
|------|---------|
| `rolling_window` | Keep last N days; useful for trending |
| `event_driven` | Retain until drift_resolved; ensures investigation has snapshot |
| `hybrid` (recommended) | min_retention + retain_until_drift_resolved + max_retention ceiling |

**Profile defaults:**
- minimal: rolling P3D
- dev: rolling P7D
- standard/prod: hybrid P24-48H min / P30D max
- fsi/sovereign: hybrid P7D min / P90D max

**Audit relationship:** Discovered State records are NOT in the Audit Store (too high-volume, too ephemeral). Drift events triggered by Discovered State ARE in the Audit Store with discovery snapshot UUID reference. After snapshot expires: audit record preserved; snapshot no longer available. RHY-008.

### 39.5 Complete Rehydration Policy Set
RHY-001 through RHY-008 — see doc 02.

---

## SECTION 40 — ARCHITECTURE GAPS: CACHE MODEL, INGESTION, DEPLOYMENT

### 40.1 DCM Deployment Topology — Hub/Regional/Sovereign

The Ship/Shore/Enclave terminology from defense IT contexts has been replaced throughout with universally understood terms aligned to DCM's federation model:

| Former Term | Replacement | Meaning |
|-------------|-------------|---------|
| Shore | **Cost Analysis Information Provider** | Specialized Information Provider supplying cost estimates, placement cost signals, cost actuals, and budget alerts; DCM provides input data; provider performs calculations |
| **Orchestration Flow Policy** | Named workflow artifact: Orchestration Flow Policy with `ordered: true`; declares explicit step sequence using payload type vocabulary; first-class Data artifact; versioned, GitOps-managed, profile-bound |
| **Request Orchestrator** | Runtime event bus; routes lifecycle events to Policy Engine; has no pipeline logic; both named workflows and dynamic policies are evaluated through it |
| **orchestration (DCM)** | Two-level composable model: Level 1 = named Orchestration Flow Policies (explicit sequence); Level 2 = dynamic policies (conditional, inline); both evaluated by Policy Engine; adding a step = adding to a workflow Policy; adding conditional behavior = writing a dynamic policy |
| **Provider Catalog Item** | What a specific Service Provider offers consumers: specific resource allocation or process with cost, availability, SLAs; linked to Resource Type Specification version |
| **cross_tenant_authorization** | DCMGroup with group_class: cross_tenant_authorization; grants one Tenant permission to reference/allocate/stake another Tenant's resources; revocation places active allocations in PENDING_REVIEW |
| **foundation Tenants** | Three system Tenants created at bootstrap: __platform__, __transitional__, __system__; cannot be decommissioned; declared in bootstrap manifest |
| **QUOTA_EXCEEDED** | Gating Policy rejection code when resource quota policy fires at Step 5 (pre-placement) |
| **Federated Contribution Model** | DCM defaults to federated data creation — all authorized actor types (platform admin, consumer/tenant, service provider, peer DCM) can contribute Data artifacts within their domain scope via the GitOps PR model; see doc 28 |
| **contributor** | Actor type that authored a Data artifact; recorded in artifact_metadata.contributed_by; determines review requirements; platform_admin / consumer / service_provider / peer_dcm |
| **contributed_by** | Artifact metadata block recording contributor_type, actor UUID, contribution_method, pr_url, reviewed_by; immutable once set |
| **DPO-001–006** | Design Priority system policies. DPO-001: security properties present in all profiles (not controlled by profiles). DPO-002: every security requirement needs an ease-of-use mechanism. DPO-005: minimal profile = "security with minimal overhead" not "minimal security". DPO-006: when security and ease conflict, redesign ease-of-use, not security. |
| **FCM-001–008** | Federated Contribution Model system policies; key: FCM-002 (domain scope violations = hard DENY), FCM-003 (GitOps PR for all), FCM-008 (contributor scope limits absolute) |
| **Unified Governance Matrix** | Single enforcement point for all cross-boundary decisions; four axes (subject/data/target/context); hard vs soft enforcement; field-level granularity (allowlist/blocklist/paths); profile-bound defaults; GMX-001–010 |
| **governance_matrix_rule** | Artifact declaring match conditions across four axes and a decision (ALLOW/DENY/ALLOW_WITH_CONDITIONS/STRIP_FIELD/REDACT/AUDIT_ONLY) with hard or soft enforcement |
| **sovereignty_zone** | Registered DCM artifact declaring geopolitical/regulatory boundary; rules reference zones by ID; inter-zone agreements declared explicitly |
| **STRIP_FIELD** | Governance matrix decision: remove named fields from payload and proceed; if stripped field is required → DENY_REQUEST |
| **REDACT** | Governance matrix decision: replace field value with `<REDACTED>`; field presence preserved; receiver knows field exists but not its value |
| **Provider Type Registry** | Three-tier registry of approved provider types; each entry declares permissions, default_approval_method, enabled_in_profiles, capability_schema_ref |
| **registration_token** | Pre-issued by platform admin; scoped to provider_type/handle_pattern/zone; single_use; grants_auto_approval flag; value presented once only |
| **approval_method** | Registration approval: auto | reviewed | verified | authorized; resolved as most_restrictive(provider_type_default, profile_min, token_effect) |
| **Drift Reconciliation Component** | Control plane component; compares Discovered vs Realized State; produces drift records and events; never writes to Realized Store; DRC-001–005 |
| **drift_record** | Artifact produced by Drift Reconciliation; field-by-field comparison result with severity classification; unsanctioned flag; status tracking through resolution |
| **Placement Engine** | Six-step algorithm: sovereignty filter → accreditation filter → capability filter → reserve query → tie-breaking (policy/priority/affinity/cost/load/hash) → confirm; PLC-001–006 |
| **reserve_query** | Parallel capacity queries to all eligible provider candidates; PT5M capacity hold; non-responders and insufficient-capacity providers excluded |
| **consistent hash** | Final placement tie-breaker: SHA-256(request_uuid+resource_type+sorted_candidates); deterministic; never round-robin |
| **Lifecycle Constraint Enforcer** | Monitors TTL/expiry/max_execution_time; fires expiry actions through standard pipeline; grace period before action; Process Resources: immediate FAILED on breach; LCE-001–005 |
| **Search Index** | Non-authoritative queryable projection of GitOps stores; indexes key fields; returns git_path for full payload; max staleness PT5M; always rebuildable; SIX-001–004 |
| **Admin API** | Platform admin REST interface: Tenant lifecycle, provider review, accreditation approval, discovery trigger, orphan resolution, recovery decisions, quota management, Search Index rebuild, bootstrap operations |
| **PENDING_EXPIRY_ACTION** | Entity state when expiry action fails to execute; Lifecycle Constraint Enforcer retries per Recovery Policy; Platform Admin notified urgency: high |
| **data_classification** | First-class field metadata: public/internal/confidential/restricted/phi/pci/sovereign/classified; phi/sovereign/classified are immutable once set |
| **Accreditation** | Formal versioned attestation that a component satisfies a compliance framework; issued by an Accreditor; carries validity period; lifecycle: developing→proposed→active→expired/revoked |
| **Accreditor** | Entity that issues accreditations: government body, regulatory body, QSA, certification body, or internal audit team |
| **Accreditation Gap** | Missing, expired, or revoked accreditation required for an active interaction; always high/critical severity; Recovery Policy governs response |
| **Data/Capability Authorization Matrix** | Policy Group artifact (concern_type: data_authorization_boundary) declaring what data fields and capabilities are permitted across interaction boundaries given data classification and accreditation level |
| **zero_trust_posture** | Sixth Policy Group concern type; four levels: none/boundary/full/hardware_attested; profile defaults: minimal=none, dev/standard=boundary, prod/fsi=full, sovereign=hardware_attested |
| **Five-check boundary model** | Identity → Authorization → Accreditation → Matrix → Sovereignty; all five checks at every DCM interaction boundary; all produce audit records |
| **Federation tunnel** | Mutually authenticated, encrypted, scoped DCM-to-DCM channel; zero trust model; establishes secure transport only, not implicit trust; per-message signing; scoped non-transferable credentials |
| **hard_constraint** | Data/Capability Matrix declaration that cannot be overridden by any policy; sovereign/classified data never crossing federation boundaries is a hard_constraint |
| **STRIP_FIELD** | Matrix enforcement action: remove non-permitted field from payload and proceed; if stripped field is required → escalates to DENY_REQUEST |
| **DENY_REQUEST** | Matrix enforcement action: block entire interaction; entity enters PENDING_REVIEW; notification dispatched |
| **Request Orchestrator** | DCM control plane event bus; routes lifecycle events to Policy Engine; coordinates pipeline via event-condition-action; does not contain hardcoded pipeline logic |
| **Cost Analysis Component** | Internal DCM control plane component; three functions: pre-request estimation, placement input, ongoing attribution; not a billing system; not a provider type |
| **Module** | DCM capability extension adding new functions; distinct from Profile (which configures behavior) |
| **orchestration_flow** | Policy Group concern_type for static sequential flows; ordered: true; both static and dynamic flows compose through the same Policy Engine |
| **payload_type** | Closed vocabulary of event types the Request Orchestrator publishes; policies pattern-match on payload type + state |
| **OPA integration** | Reference implementation for Mode 3 External Policy Evaluators; DCM payload as OPA input document; built-in Rego functions provided by DCM |
| **Flow GUI** | Visual policy composer and orchestration manager; execution graph view, policy canvas, shadow mode dashboard, flow simulation |
| **__platform__** | Immutable system Tenant owning DCM control plane resources; created at bootstrap before Policy Engine comes online |
| **__transitional__** | Immutable system Tenant holding brownfield entities during INGEST phase |
| **bootstrap manifest** | Signed manifest declaring initial system Tenants, bootstrap admin, and initial profile; hash-verified at every DCM startup |
| **cross_tenant_authorization** | DCMGroup with this group_class formally grants one Tenant access to another's resources; has lifecycle (duration, renewal, revocation); revocation places active allocations in PENDING_REVIEW |
| **drift_criticality** | Field-level property in Resource Type Spec (low/medium/high/critical); combined with change magnitude to produce drift severity |
| **Ingress API** | Infrastructure-layer entry point for all inbound DCM requests; sets ingress block; routes to Consumer/Provider/Admin API surfaces |
| **Provider Catalog Item** | Provider-specific instantiation of a Resource Type Specification; what consumers actually request; distinct from the Resource Type Specification itself |
| **Recovery Policy** | Formal DCM policy type mapping trigger conditions (DISPATCH_TIMEOUT, PARTIAL_REALIZATION, etc.) to response actions; same authoring model as Gating Policy/Validation/Transformation |
| **recovery_posture** | Fifth Policy Group concern_type governing failure and ambiguity response; binds a recovery profile group to the deployment |
| **DRIFT_RECONCILE** | Recovery action: schedule discovery; let drift detection resolve actual state |
| **DISCARD_AND_REQUEUE** | Recovery action: best-effort cleanup; new request cycle created immediately |
| **NOTIFY_AND_WAIT** | Recovery action: notify human; wait for explicit decision up to declared deadline |
| **TIMEOUT_PENDING** | Infrastructure Resource Entity state: dispatch timeout fired; recovery policy evaluating |
| **LATE_REALIZATION_PENDING** | Entity state: provider responded after timeout; NOTIFY_AND_WAIT recovery decision pending |
| **INDETERMINATE_REALIZATION** | Entity state: state ambiguous; drift detection resolving |
| **COMPENSATION_FAILED** | Entity state: composite service rollback itself failed; orphan detection active |
| **orphan_candidate** | Resource discovered at provider with no corresponding Realized State record; surfaced to platform admin for human resolution |
| **Discovery Scheduler** | DCM control plane component maintaining priority queue of discovery requests; dispatches to provider discovery endpoints |
| **recovery-automated-reconciliation** | Built-in recovery profile: trust drift detection; accept late responses; appropriate for dev/standard |
| **recovery-notify-and-wait** | Built-in recovery profile: notify human; never act automatically; appropriate for prod/fsi/sovereign |
| **notification service** | Ninth DCM provider type; translates unified notification envelope to delivery channel; handles delivery, retry, dead letter, and delivery confirmation callbacks |
| **Notification Router** | DCM control plane component that resolves notification audiences and routes envelopes to notification services |
| **audience resolution** | Deriving notification recipients by traversing the entity relationship graph from the changed entity at event time |
| **notification_uuid** | Idempotency key on notification envelopes; notification services use this to deduplicate on retry |
| **audience_role** | owner / stakeholder / approver / observer — why this actor is in the notification audience |
| **stakeholder_reason** | Notification envelope field explaining which relationship caused the actor to be in the stakeholder audience |
| **Tier 1 / Tier 2 / Tier 3 notifications** | Mandatory system (non-suppressable) / Tenant defaults / Actor subscriptions — three subscription tiers that compose |
| **NOT-001 through NOT-008** | Notification model system policies |
| **write-once snapshot store** | Realized Store implementation model: each record is a complete immutable entity state snapshot; no event replay; direct point-in-time lookup; supersession chain links snapshots |
| **corresponding_requested_state_uuid** | Mandatory non-nullable field on every Realized State snapshot; traces every Realized State change to an authorized request |
| **Provider Update Notification** | Formal API for providers to report authorized state changes; DCM evaluates via Policy Engine; approved → new Requested State + Realized State; rejected → drift event |
| **notification_uuid** | Idempotency key on Provider Update Notifications; safe to resend on provider crash |
| **pre-authorized update** | Category of provider update pre-approved by Gating policy; processed automatically without per-change human review |
| **Whole Allocation** | Ownership pattern: consumer owns the entire resource entity outright in their Tenant; no pool involved |
| **Allocation** | Ownership pattern: pool yields independently-owned sub-resources; consumer owns their allocation; AllocationRecord relationship links to pool |
| **Shareable** | Ownership pattern: one resource, multiple stakeholders; consumers hold stakes (relationships) only; no consumer owns any portion |
| **AllocationRecord** | Cross-tenant relationship from an allocation entity back to its source pool entity |
| **stake_strength** | Relationship property on shareable resource attachments: required (blocks decommission) / preferred / optional |
| **PENDING_REVIEW** | Formal Infrastructure Resource Entity lifecycle state for conflicts requiring human resolution (sovereignty, cross-tenant auth revocation, ownership transfer conflicts) |
| **Consumer API** | DCM REST API for consumers: catalog browsing, request submission, resource management, audit trail access |
| **Consumer Request Status** | Lifecycle: ACKNOWLEDGED → ASSEMBLING → AWAITING_APPROVAL → APPROVED → DISPATCHED → PROVISIONING → COMPLETED/FAILED/CANCELLED |
| **01-entity-types.md** | Entity type taxonomy: Infrastructure Resource, Composite Resource, Process Resource; sub-types and invariants |
| **04-examples.md** | Worked examples: VM end-to-end, IP allocation, VLAN sharing, brownfield ingestion, drift remediation; Git repo structure |
| **04b-ownership-sharing-allocation.md** | Authoritative ownership model: whole allocation, allocation, shareable; policies OWN-001 through OWN-008 |
| **federation routing** | Hub DCM applies placement engine logic at the DCM instance level; Regional DCMs are DCM Provider instances; sovereignty is a hard pre-filter; same tie-breaking hierarchy as provider selection |
| **independent_with_overlap** | Certificate rotation model: old cert valid P30D after new cert issued; allows peers to update trust stores without coordinated downtime |
| **alert_and_hold** | Federated drift detection response when peer DCM is unavailable: do not assume drift; hold state; escalate to platform admin after PT24H |
| **AUDIT_STORE_UNAVAILABLE** | Gap record inserted in Audit Store hash chain after recovery from Audit Store failure; timestamps the exact outage window; makes gap explicit and auditable |
| **confidence aggregation** | Per-entity endpoint computing overall confidence band (= lowest field band); identifies contested and stale fields; computed on demand never stored |
| **explicit_no_filter** | Composite group declaration suppressing the no member_type filter linting warning; confirms broad targeting is intentional |
| **certified profile** | DCM profile carrying formal third-party certification metadata (HIPAA assessor, FedRAMP JAB, PCI QSA); promoted to Tier 1; applies to artifact not deployment |
| **POLICY_PROVIDER_ELEVATED** | Audit action recorded when a External Policy Evaluator's mode level is elevated; always produced regardless of profile |
| **tier_certifications** | Certification metadata on Resource Type Specs or profiles from recognized certifying bodies; filter criterion, not structural tier boundary |
| **tier_3_to_tier_2_promotion** | PR-based pathway for organizations to promote internal Tier 3 Resource Types to Verified Community (Tier 2); requires production deployment, OSS license, named maintainer, migration path |
| **independent operation mode** | Resource Type Registry state when upstream registry is permanently unavailable; existing types continue; new community type adoption requires governance decision |
| **SCIM 2.0** | System for Cross-domain Identity Management; optional Auth Provider capability for automated actor provisioning from enterprise IdPs; provisions actors and group memberships; roles not SCIM-provisioned |
| **step-up MFA** | Additional MFA challenge at sensitive operations within an already-authenticated session; declared per operation by policy; step-up token TTL PT10M |
| **actor.type** | Audit record field: human / service_account / system; enables filtering between human-initiated and automated lifecycle operations in queries and dashboards |
| **system_actor** | Audit record block on system-initiated records: identifies DCM component, trigger event, and authorizing policy UUID |
| **Merkle root proof** | Federation-level audit integrity mechanism: Hub DCM computes Merkle root of all Regional DCM chain tips daily; any chain break detectable against stored root |
| **per-instance hash chain** | Each DCM instance (Hub/Regional/Sovereign) maintains its own independent hash chain; not merged cross-instance; cross-referenced via correlation_id |
| **AUTH-012 through AUTH-015** | Auth Provider gap policies: SCIM provisioning, failover handling, two-tier MFA, pluggable user store |
| **AUD-014 through AUD-017** | Universal Audit gap policies: hash chain verification modes, Commit Log capacity, system-initiated records, distributed hash chains |
| **Hub DCM** | Central/global instance; governance origin; authoritative registry |
| Ship | **Regional DCM** | Distributed regional instance; manages resources in its region |
| Enclave | **Sovereign DCM** | Air-gapped/compliance-isolated; signed bundle updates only |

These map directly onto the DCM federation model (DCM-001 through DCM-008, doc 22).

### 40.2 Cache Placement (Q1)
Caches placed closest to consumption point, subject to sovereignty constraints:
- **Layer + Catalog caches**: Regional DCM (closest to assembly); Hub DCM is authoritative origin
- **Information Provider caches**: co-located with source; never cross sovereignty boundary
- **Search Index**: Hub DCM primary; Regional DCM optional mirror; Sovereign DCM local index
- **Sovereign DCM caches**: always local static; populated from signed bundles; no live sync

CACHE-001.

### 40.3 Cache Synchronization (Q2)
**Hybrid push-pull model:** Pull on profile-governed schedule (minimal=P4H through fsi/sovereign=P5M); push invalidation via Message Bus for time-sensitive events (layer_updated, policy_activated, sovereignty_change). Pull failure → serve cached. Push failure → queue+retry within PT1H. Sovereign DCM: signed bundle import only. CACHE-002.

### 40.4 Cache Authoritativeness (Q3)
GitOps stores and Event Streams always authoritative. Caches are derived projections — never authoritative. Cache divergence → rebuild from nearest authoritative store → CACHE_DIVERGENCE_DETECTED Audit event. Regional DCMs send cache state hash in heartbeats to Hub DCM; mismatch → forced refresh. CACHE-003, CACHE-004.

### 40.5 Native Passthrough (Q5)
Core data model does not embed technology-specific data. `native_passthrough` field sanctioned for genuinely untranslatable provider-specific data. Always audit-logged (content if transparent; hash if opaque). Opaque passthrough blocked in fsi/sovereign profiles by default. DATA-001.

### 40.6 Physical State Representation (Q6)
Intent/Requested → YAML in Git. Realized → Event Stream → Realized Store. Discovered → Discovered Store (ephemeral). Resolved by STO-001 through STO-005.

### 40.7 Ingestion Model Gaps

**Signal priority configurable (Q1):** Platform domain layer declares priority order. explicit_tenant_tag always first; default_tenant always last; middle signals reorderable. ING-012.

**Bulk promotion (Q2):** Supported with profile-governed limits (minimal=unlimited → sovereign=25 per batch). Preview required. PT24H rollback. BULK_PROMOTE audit record. ING-013.

**Max ingestion sources per entity (Q3):** Profile-governed (5 standard/prod; 3 fsi/sovereign). Warn or reject on exceed. ING-014.

**Ingestion → Service Catalog (Q4):** Ingested entities promotable to catalog items. Bidirectional drift detection between entity and catalog item. ING-015.

### 40.8 Deployment Redundancy Gaps

**Bootstrap manifest verification (Q1):** GitOps stored + hash-verified at every startup. Tampering prevents startup. Operator-signed. RED-011.

**Sovereign Kubernetes upgrades (Q2):** Pre-staged images via signed bundles. DCM maintenance mode during upgrade. Startup verification before resuming queued requests. RED-012.

**Non-Kubernetes runtimes (Q3):** Kubernetes required for production. Podman/Docker Compose for dev/community only. DCM Operator is Kubernetes-native. RED-013.

**Minimum hardware specs (Q4):** Declared as DCM Resource definitions per profile; enforced by placement engine. minimal=2cpu/4Gi/20Gi/1 replica → fsi/sovereign=32cpu/64Gi/500Gi/5 replicas. RED-014.

**DCM self-hosted drift detection (Q5):** DCM is a DCM-managed resource — same drift detection. Bootstrap hash provides independent Operator verification. Audit hash chain breaks externally detectable. RED-015.

---

## SECTION 41 — SECURITY, AUTH, AND AUDIT REFINEMENTS

### 41.1 SCIM 2.0 User Provisioning (Auth Q1)

SCIM 2.0 is an optional Auth Provider capability for enterprise deployments. Automates actor lifecycle from enterprise IdPs (Okta, Azure AD, Ping, JumpCloud).

**What SCIM manages:** DCM actor records (create/update/deactivate), DCM group memberships from IdP groups.

**What SCIM does NOT manage:** Roles — they require explicit DCM policy authorization. This prevents privilege escalation through the SCIM channel.

**Deprovisioning:** `suspend` by default (reversible; sessions terminated; leases released; in-flight requests complete first). AUTH-012.

### 41.2 Auth Provider Failover — In-Flight Requests (Auth Q2)

**In-flight requests (already authenticated):** Continue to completion — session token carries resolved roles/groups/tenant scope; Auth Provider not needed for assembly.

**New requests, provider down:** Follow declared failover chain. Sessions valid for declared TTL (PT8H default) regardless of provider availability.

**Session expiry during outage:** Requires re-auth via available failover provider. All providers unavailable → reject new authentication with clear error.

Failover chain: primary LDAP → OIDC backup → local users (last resort). AUTH-013.

### 41.3 Two-Tier MFA — Per-Session and Step-Up (Auth Q3)

**Per-session MFA:** Validated at login; captured in `ingress.actor.mfa_verified`.

**Step-up MFA:** Additional challenge at sensitive operations even within a valid MFA session. Policy declares which operations require step-up:
- platform_policy_activate, provider_decommission, tenant_decommission
- sovereignty_zone_change, auth_provider_update, manual_rehydration (if entity requires hardware_token_mfa)

Step-up token TTL: PT10M. Profile defaults: minimal/dev = no MFA; standard = recommended; prod = per-session required + destructive ops step-up; fsi = per-session + all policy changes; sovereign = hardware token + all admin ops. AUTH-014.

### 41.4 Built-In Auth Provider Storage Backend (Auth Q4)

Pluggable storage backend following the data store model. SQLite (minimal/dev) → PostgreSQL (standard+). FSI/sovereign require encryption at rest. Local store should contain bootstrap users, service accounts, API keys only — not enterprise users. AUTH-015.

### 41.5 Hash Chain Verification Modes (Audit Q1)

Three independent levels:
- **Continuous write:** Hash computed on every write — this IS chain construction; always active
- **Scheduled sweep:** Background verification: standard=weekly, prod=daily, fsi/sovereign=every 6 hours
- **On-demand:** Operator-triggered for any time range (max P365D per run)

Failure: security alert + integrity incident; new writes continue (halting writes is itself a security risk). AUD-014.

### 41.6 Commit Log Capacity and Overflow (Audit Q2)

Configurable max capacity (default 10Gi) with declared overflow policy:
- `alert_and_continue` (minimal/dev/standard/prod) — availability priority
- `reject_new_ops` (fsi/sovereign) — audit completeness priority; operating unaudited is a compliance violation

Backpressure: alert at 75%, urgent at 90%. P7D max age triggers escalation regardless of capacity. AUD-015.

### 41.7 System-Initiated Audit Records (Audit Q3)

`actor.type` field on all audit records: `human | service_account | system`

System records include `system_actor` block: component + trigger + authorizing_policy_uuid. Full audit records — appear in all queries and compliance reports. Enables dashboard filtering: "show only human-initiated changes" vs "show only automated lifecycle operations". AUD-016.

### 41.8 Distributed Hash Chain Integrity (Audit Q4)

Per-instance hash chains — each DCM instance (Hub, Regional, Sovereign) has its own independent chain. Federation-level integrity via daily Merkle root proof at Hub DCM. Cross-instance queries: parallel chains with cross-references via `correlation_id` — not merged. Per-instance verification always local; federation verification requires Hub DCM connectivity. AUD-017.

---

## SECTION 42 — POLICY AND REGISTRY REFINEMENTS

### 42.1 Community Profile and Group Submissions (Policy Q1)

Organizations submit custom profiles and policy groups to the DCM community registry via same PR-based workflow as Resource Types — Tier 2. Requirements: documented use case, at least one production deployment reference, test results, named maintainer. Same lifecycle as Resource Types (shadow validation before active, deprecation, sunset). PROF-005.

### 42.2 Certified Profile Program (Policy Q2)

Certified profiles carry third-party certification metadata (HIPAA assessor, FedRAMP JAB, PCI QSA). Certified profiles promoted to Tier 1 (DCM Core). Certification applies to the profile artifact only — not to any specific deployment. Community-contributed Tier 2 profiles that obtain certification can be promoted to Tier 1. PROF-006.

### 42.3 External Policy Evaluator Trust Elevation Approval (Policy Q3)

Trust elevation (increasing mode level) requires formal approval workflow. Profile-governed approver requirements:
- standard: 1 platform_admin
- prod: platform_admin + security_owner (min 2)
- fsi: platform_admin + security_owner + compliance_officer (dual approval)
- sovereign: 3 approvers + change control ticket

P7D shadow period after elevation before outputs become binding. POLICY_PROVIDER_ELEVATED audit record. PROF-007.

### 42.4 Dev Profile Resource TTL Configurability (Policy Q4)

Default TTL declared in system domain layer; overridable at platform domain level. Per-resource-type overrides supported (VMs: P7D, Storage: P14D, DNS: P3D). on_expiry action configurable: notify (consumers can extend) vs destroy. PROF-008.

### 42.5 Air-Gapped External Policy Evaluator Delivery (Policy Q5)

Signed bundle model — same as registry bundles. Mode 3 bundles include OPA Rego files. Mode 4 in sovereign profiles: endpoint must be within sovereignty boundary — external AI service calls blocked by BBQ-001 sovereignty check. PROF-009.

### 42.6 No Fourth Registry Tier (Registry Q1)

Certification metadata within existing tier structure — no structural fourth tier. filter: tier_certifications provides equivalent discovery. REG-008.

### 42.7 Tier 3 to Tier 2 Promotion (Registry Q2)

PR-based promotion pathway with additional requirements: production deployment + OSS-compatible license + named community maintainer + documented migration path from Tier 3 handle. Current Tier 3 users notified. REG-009.

### 42.8 Upstream Registry Permanently Unavailable (Registry Q3)

Organization Registry mirror is self-sufficient — upstream loss is a governance decision, not an operational crisis. Three options: designate community mirror as new upstream / fork the registry / continue as independent installation. Existing operations never interrupted. REG-010.

### 42.9 Provider Cost Metadata Source (Registry Q4)

Static declaration or dynamic Cost Analysis sourcing; hybrid recommended (Cost Analysis preferred, static fallback, fallback_max_age: PT24H). Placement engine cost analysis step uses freshest available source — no changes to tie-breaking model. REG-011.

---

## SECTION 43 — FEDERATION, OBSERVABILITY, AND FINAL REFINEMENTS

### 43.1 DCM-to-DCM Certificate Rotation (Federation Q1)

Independent rotation per instance with P30D overlap period. Peers notified via Message Bus 60 days before expiry. Automatic renewal triggers 90 days before expiry. Overlap allows peers to update trust stores without coordinated downtime. DCM-009.

### 43.2 Federation Routing — Full Placement Engine at DCM Level (Federation Q2 — Extended)

**Hub DCM federation routing follows the same placement engine logic as provider selection.** Regional DCMs are treated as DCM Provider instances.

**Sovereignty is a hard pre-filter — not a tie-breaker:**
- Filter eligible Regional DCMs by sovereignty compatibility before the placement loop
- No eligible Regional DCMs after filter → reject with clear error

**Tie-breaking hierarchy at the DCM instance level (same as provider selection):**
1. Policy preference (policy declares preferred Regional DCM)
2. Federation priority (numeric priority on DCM Provider registration)
3. Tenant affinity (Tenant's resources prefer a specific Regional DCM)
4. Sovereignty match quality (exact over partial match)
5. Geographic affinity (closest regional to consumer)
6. Least loaded (capacity utilization)
7. Consistent hash (deterministic tiebreaker)

**Sub-regional routing:** Regional DCM acts as Hub for its children — same logic recursive within federation depth limit. Load balancing is step 6 (least loaded) — not a primary strategy.

DCM-010.

### 43.3 Federated Drift Detection Ownership (Federation Q3)

Provider-side DCM discovers; consumer-side DCM compares against its Requested State. Discovered State events published via federation Message Bus with correlation_id + consumer_dcm_uuid tag. Peer DCM unavailable = alert-and-hold (not assumed drift); max hold PT24H then escalate. DCM-011.

### 43.4 Cross-DCM Audit Correlation (Federation Q4)

No full synchronization. correlation_id reference model — each DCM keeps its own authoritative audit trail. On-demand pull for compliance investigations requires platform admin auth + sovereignty check + peer DCM authorization. DCM-012.

### 43.5 Maximum Federation Depth (Federation Q5)

Profile-governed: minimal/dev=5, standard/prod=3, fsi/sovereign=2. Measured as hops from deepest instance to Hub DCM. Depth 3 covers Hub → Regional → Sub-Regional → Edge. DCM-013.

### 43.6 Audit Provenance Scattered Resolutions

- **Q1 (Audit Store architecture):** Already resolved as STO-004 — specialized PostgreSQL store contract; see doc 11.
- **Q2 (Air-gapped replication):** Live sync for Regional DCMs; signed bundle export for Sovereign DCMs; sovereignty check required; hash chain preserved; AUD-018.
- **Q3 (Default dashboard):** Grafana bundled for minimal/dev/standard; enterprise integration recommended for prod; required for fsi; local-only for sovereign; OBS-002.
- **Q4 (Failing Data Store):** Two-stage model handles it — Commit Log (etcd) independent of data stores; AUDIT_STORE_UNAVAILABLE gap record on recovery; hash chain makes gap explicit; AUD-019.

### 43.7 Universal Groups — Composite Linting (Q1)

Linting warning (not error) when composite group policy targeting has no member_type filter. Operator may suppress with explicit_no_filter: true. GRP-016.

### 43.8 Information Provider — Confidence Aggregation (Q2) and Override Notifications (Q3)

**Confidence aggregation API:** GET /api/v1/entities/{uuid}/confidence — overall band = lowest field band (conservative); computed on demand; identifies contested and stale fields. INF-010.

**Override notifications:** Provider opt-in via conflict_notification in registration; webhook or Message Bus; overriding value may be redacted by policy for confidentiality. INF-011.

---

## SECTION 44 — FOUNDATIONAL CAPABILITIES MATRIX

### 44.1 Overview

DCM has 95 foundational capabilities across 15 domains. Each capability has a unique ID (domain prefix + sequence number), three perspectives (Consumer, Producer, Platform/Admin), and declared dependencies. This matrix drives Jira ticket creation and implementation planning.

### 44.2 Minimum Viable Capability Set (21 capabilities for end-to-end demo)

IAM-001 → IAM-002 → IAM-003 → IAM-007 → CAT-001 → REQ-001 → REQ-002 → REQ-003 → REQ-004 → REQ-005 → REQ-006 → REQ-007 → PRV-001 → PRV-002 → PRV-003 → PRV-004 → PRV-005 → LCM-001 → DRF-001 → DRF-002 → AUD-001

### 44.3 Domain Summary

| Prefix | Domain | Count |
|--------|--------|-------|
| IAM | Identity and Access Management | 7 |
| CAT | Service Catalog | 7 |
| REQ | Request Lifecycle Management | 10 |
| PRV | Provider Contract and Realization | 9 |
| LCM | Resource Lifecycle Management | 7 |
| DRF | Drift Detection and Remediation | 5 |
| POL | Policy Management | 7 |
| LAY | Data Layer Management | 5 |
| INF | Information and Data Integration | 6 |
| ING | Ingestion and Brownfield Management | 4 |
| AUD | Audit and Compliance | 5 |
| OBS | Observability and Operations | 5 |
| STO | Storage and State Management | 6 |
| FED | DCM Federation and Multi-Instance | 5 |
| GOV | Platform Governance and Administration | 7 |
| **Total** | | **95** |

### 44.4 Perspectives

- **Consumer** — what the end user / application team experiences or can do
- **Producer** — what the Service Provider or platform component must implement
- **Platform/Admin** — what the platform engineer or SRE must configure or operate

Empty perspective = that capability does not have a direct touchpoint for that role.

### 44.5 Key Dependency Chain

```
IAM-001 (Auth) → IAM-003 (RBAC) → CAT-001 (Catalog) → REQ-001 (Submit)
  → REQ-003 (Layers) → REQ-004 (Policy) → REQ-005 (Placement) → REQ-007 (Dispatch)
    → PRV-001 (Provider Reg) → PRV-003 (Realization) → PRV-005 (Realized State)
      → LCM-001 (State Transitions) → DRF-001 (Discovery) → DRF-002 (Drift)
```

### 44.6 Resources
- Interactive map: DCM-Capabilities-Map.html
- CSV for Jira import: DCM-Capabilities-Matrix.csv
- Markdown reference: DCM-Capabilities-Matrix.md
- Taxonomy: DCM-Taxonomy.md

---

## SECTION 45 — DCM TAXONOMY

The DCM Taxonomy is the authoritative vocabulary for all DCM work — code, documentation, Jira tickets, design discussions. Four parts:

### 45.1 Core Vocabulary (key terms)
- **Service Provider** — provisions/configures/manages infrastructure; implements naturalization, realization, denaturalization, capacity reporting, sovereignty maintenance. *NOT "producer."*
- **Hub DCM** — central/global instance; authoritative registry origin. *NOT "Shore."*
- **Regional DCM** — distributed regional instance; treated as DCM Provider by Hub placement engine. *NOT "Ship."*
- **Sovereign DCM** — air-gapped/compliance-isolated; signed bundle updates only. *NOT "Enclave."*
- **Layer** — passive data (what values should fields have); distinct from Policy (executable logic)
- **Policy** — executable rule evaluating assembled payload; distinct from Layer
- **Confidence Descriptor** — primary data model for Information Provider confidence: authority_level + corroboration + source_trust + last_updated_at (stored); score + band derived at query time
- **Rehydration** — replaying Intent State to new provider; UUID always preserved
- **Targeted Delta** — post-realization field update; does not re-run layer assembly chain
- **Fulfillment** — complete process from consumer submission to Service Provider realization
- **Reserve Query** — placement engine asking providers "can you fulfill this right now?"

### 45.2 Anti-Vocabulary (terms to avoid)
| Avoid | Use Instead |
|-------|-------------|
| Producer | **Service Provider** |
| Shore / Ship / Enclave | **Hub DCM** / **Regional DCM** / **Sovereign DCM** |
| Realize / Realization | **Provision** / **Install** / **Fulfill** |
| Widgets | Specific resource type name |
| Data Center | **Region** / **Zone** |
| User (generic) | **Developer**, **Application Owner**, **Platform Engineer** |
| Service (unqualified) | **Catalog Item** / **Resource Type** / **Service Provider** |
| Manage (unqualified) | **Provision** / **Configure** / **Monitor** / **Decommission** |

### 45.3 Roles and Personas
Developer/Application Owner (consumer), Platform Engineer (platform ops), Policy Owner (governance), Platform Admin (highest-privilege ops), SRE (operational health), Tenant Admin (tenant management), Service Provider Team (provider integration).

### 45.4 Capability Domain Prefixes
IAM, CAT, REQ, PRV, LCM, DRF, POL, LAY, INF, ING, AUD, OBS, STO, FED, GOV — see Section 44.

---

## SECTION 46 — GROUP 1: MISSING DOCUMENTS

### 46.1 01-entity-types.md — Entity Types Taxonomy

Three primary entity types in DCM:

**Infrastructure Resource Entity** — persistent, full lifecycle (REQUESTED → PENDING → PROVISIONING → REALIZED → OPERATIONAL → SUSPENDED → DECOMMISSIONED). Owned by exactly one Tenant. Drift detection active. TTL management. `PENDING_REVIEW` is a valid state for sovereignty/tenancy conflicts during rehydration — not an error state; requires human resolution.

**Composite Resource Entity** — produced by a Composite Service request that aggregates multiple Infrastructure Resource Entities. Owns its UUID; constituents own theirs. `lifecycle_state` reflects aggregate health — OPERATIONAL only when all required constituents OPERATIONAL. Two-level drift detection (composite + constituent). Staged decommission (composite first, then constituents in reverse dependency order). `composition_visibility: opaque|transparent|selective`.

**Process Resource Entity** — ephemeral execution (automation jobs, playbooks, pipelines). Short lifecycle (REQUESTED → INITIATED → EXECUTING → terminal). No SUSPENDED state. No PENDING_REVIEW. `max_execution_time` mandatory — no default. Must record `affected_entity_uuids` if any infrastructure modifications made.

Entity sub-types: Shared Resource Entity (`ownership_model: shareable`), Allocatable Pool Resource (pool entity), Allocation entity (`ownership_model: allocation`).

Entity identity invariants: UUID never changes (including rehydration); single Tenant ownership always; provider entity ID is separate from DCM UUID; audit records preserved per retention policy.

### 46.2 04b-ownership-sharing-allocation.md — Ownership, Sharing, and Allocation

**The three ownership patterns — use these terms precisely:**

**Whole Allocation** — consumer receives entire resource entity; owns it outright in their Tenant; no pool involved; full lifecycle control; decommission is straightforward.

**Allocation** — pool resource (owned by platform Tenant) yields new independently-owned sub-resources. Consumer owns their allocation outright. AllocationRecord relationship links allocation → pool. Decommissioning the allocation releases it back to the pool. Pool entity unaffected. Example: IPAddressPool → IPAddress entities.

**Shareable** — single resource owned by one Tenant; multiple consumers hold stakes (relationships) but own nothing. No new entity created per consumer. Decommission deferred while required stakes active. Consumer holds an `attached_to` or `depends_on` relationship with declared `stake_strength: required|preferred|optional`. Example: VLAN shared by multiple VMs.

**Critical distinction:** Shareable = one resource, multiple stake-holders. Allocation = one pool, multiple independently-owned sub-resources. Never confuse these.

Hybrid case: an allocation from a shareable pool. Consumer owns their /28 subnet (allocation). The parent /16 is shareable (NetworkOps owns it, multiple /28s have stakes in it).

OWN-001 through OWN-008 policies govern these patterns.

### 46.3 04-examples.md — Worked Examples and Git Repository Structure

**Git repository structure (resolves Q54 deferred item):**
- Intent Store: `intent-store/{tenant-uuid}/{resource-type-category}/{resource-type}/{entity-uuid}/intent.yaml`
- Requested Store: `requested-store/{tenant-uuid}/{resource-type-category}/{resource-type}/{entity-uuid}/` with: `requested.yaml`, `assembly-provenance.yaml`, `placement.yaml`, `dependencies.yaml`
- Provider selection is in `placement.yaml` — not encoded in directory structure (Q54 resolved)

**Five worked examples:**
1. VM provision end-to-end (layer assembly, policy evaluation, placement, all four states)
2. IP Address allocation (pool → consumer-owned allocation entity, AllocationRecord relationship)
3. VLAN attachment (shareable ownership — stake relationship, decommission deferral)
4. Brownfield ingestion (INGEST → ENRICH → PROMOTE with CMDB Information Provider)
5. Drift detection and remediation (unsanctioned memory change, severity, ESCALATE, UPDATE_DEFINITION resolution)

### 46.4 consumer-api-spec.md — Consumer API Specification

Consumer API base URL: `/api/v1/`. Three ingress surfaces: REST API (this spec), Web UI, Git PR.

**Authentication:** Bearer token from `/api/v1/auth/token`. Tenant context via `X-DCM-Tenant` header — always required when actor has multiple Tenants. Step-up MFA via `X-DCM-StepUp-Token` for sensitive operations.

**Service Catalog:** `GET /api/v1/catalog` (list, filtered by RBAC), `GET /api/v1/catalog/{uuid}` (describe with full schema, constraints, cost estimate), `GET /api/v1/catalog/search`.

**Request submission:** `POST /api/v1/requests` → 202 with entity_uuid and status_url. Consumer request status lifecycle: ACKNOWLEDGED → ASSEMBLING → AWAITING_APPROVAL → APPROVED → DISPATCHED → PROVISIONING → COMPLETED|FAILED|CANCELLED. `DELETE /api/v1/requests/{uuid}` for cancellation (only before PROVISIONING).

**Resource management:** `GET /api/v1/resources` (list), `GET /api/v1/resources/{uuid}` (describe with confidence scores, drift status, editable flags), `PATCH /api/v1/resources/{uuid}` (targeted delta for editable fields), `POST /suspend`, `DELETE` (decommission with deferred response if stakes active), `POST /rehydrate`.

**Audit:** `GET /api/v1/resources/{uuid}/audit` with chain_integrity field, `GET /api/v1/audit/correlation/{id}` for cross-state timeline.

Three conformance levels: Level 1 (read-only), Level 2 (standard), Level 3 (full including rehydration and audit).

### 46.5 Context-and-Purpose Fix

Section 5 subsections were incorrectly numbered 3.1/3.2/3.3 — corrected to 5.1/5.2/5.3. Q6 garbled row in open questions table — corrected.

### 46.6 Q54 Resolution

Git repository structure is independent of provider selection. Provider selection is stored in `placement.yaml` within the entity's directory. The deferred note in the four states doc has been updated to reference the worked examples document for the complete layout.

---

## SECTION 47 — STORE ARCHITECTURE: INTENT, REQUESTED, REALIZED, DISCOVERED

### 47.1 The Four Stores — Corrected Model

| Store | Type | Implementation | Why |
|-------|------|---------------|-----|
| Intent | GitOps (required) | GitHub/GitLab/Gitea | PR workflow is first-class feature, not implementation detail |
| Requested | Write-once store (PostgreSQL) | GitOps (reference); PostgreSQL (production scale) | Machine-generated; no PR benefit; Git degrades at scale |
| Realized | Write-once Snapshot Store | PostgreSQL; CockroachDB | Snapshot-based (not event stream); request-traceable only |
| Discovered | Ephemeral Snapshot Stream | Kafka; EventStoreDB | High-frequency; never a rehydration source; ephemeral |

**Intent Store must be GitOps** — the PR workflow, branch-per-request, and human review are architectural features.

**Requested Store should NOT be GitOps at production scale** — Git throughput degrades under high-frequency machine writes; PR mechanics add latency with no benefit for machine-generated content. Write-once document store with hash-chain integrity satisfies the contract.

**Realized Store is NOT an event stream** — it is a write-once snapshot store. Each record is a complete entity state, not a field-level event. This makes rehydration a direct lookup (not a replay) and makes point-in-time queries trivial.

**Discovered Store remains an event stream** — high-frequency, machine-generated, ephemeral; never a rehydration source.

### 47.2 The Fundamental Realized Store Constraint

> **Realized State only changes when an authorized request produces a corresponding Requested State record. No exceptions.**

Three write sources — all require `corresponding_requested_state_uuid` (non-nullable):
1. `initial_realization` — provider confirms first provisioning
2. `consumer_update` — consumer targeted delta approved and confirmed
3. `provider_update` — DCM approves a Provider Update Notification

**What does NOT write to Realized Store:**
- Drift detection (reads only)
- Discovery cycles (writes to Discovered Store only)
- Unsanctioned provider changes (become drift events)
- Direct admin writes (bypassing the request pipeline is forbidden)

**Drift is always unsanctioned** — there are no "legitimate drift events." Every authorized change goes through a request and produces a Requested State record. If Discovered State differs from Realized State without a corresponding Requested State record, it is drift.

### 47.3 Provider Update Notification

Formal mechanism for providers to report authorized state changes (auto-scaling, auto-healing, maintenance). Not drift — the provider is asserting the change was authorized.

**DCM processing pipeline:**
```
Provider submits POST /api/v1/provider/entities/{uuid}/update-notification
  → Authentication (provider mTLS)
  → Policy Engine evaluates (pre-authorized? requires consumer approval?)
  → APPROVED: create provider_update Requested State → write Realized State snapshot
  → REQUIRES_APPROVAL: entity enters PENDING_REVIEW; consumer notified
  → REJECTED: Realized State unchanged; discrepancy becomes drift
```

**Pre-authorization:** Providers declare update capabilities at registration. Organizations pre-authorize categories of updates via Gating policy (e.g., auto-scale within 2× bounds). Pre-authorized updates are processed automatically.

**Consumer approval API:** `GET /api/v1/resources/{uuid}/provider-notifications` and `POST /approve` or `/reject`. On approval → new Requested State + Realized State. On rejection → drift event.

**Idempotency:** `notification_uuid` is the idempotency key. Safe to resend on provider crash.

**Level 2 conformance requirement** in the Operator Interface Specification for providers implementing auto-scaling, auto-healing, or provider-side maintenance.

### 47.4 Realized State Snapshot Structure

```yaml
realized_state_snapshot:
  realized_state_uuid: <uuid>
  entity_uuid: <uuid>
  realized_at: <ISO 8601>
  source_type: initial_realization | consumer_update | provider_update
  corresponding_requested_state_uuid: <uuid>   # mandatory, not nullable
  supersedes_realized_state_uuid: <uuid|null>
  superseded_by_realized_state_uuid: <uuid|null>
  fields: { # complete entity state }
```

### 47.5 Rehydration from Realized State

Rehydration picks a specific snapshot — direct lookup by `realized_state_uuid` or by timestamp. Not a replay. Not a projection. A complete entity state that was explicitly authorized through DCM's governance pipeline. The supersession chain enables historical rehydration ("rehydrate as of March 15").

### 47.6 New Policies

- `STO-007`: Realized Store is write-once snapshot; every write requires non-nullable `corresponding_requested_state_uuid`; enforcement at store API level
- `STO-008`: Intent Store requires GitOps; Requested Store requires write-once semantics (GitOps reference impl; write-once document stores supported at scale)
- `RSE-010`: Realized State only changes via authorized request; drift detection never writes to Realized Store
- `RSE-011`: Provider Update Notifications evaluated by Policy Engine before any Realized State change
- `RSE-012`: Categories of provider updates may be pre-authorized via Gating policy
- `RSE-013`: Provider updates requiring consumer approval place entity in PENDING_REVIEW

---

## SECTION 48 — NOTIFICATION MODEL

### 48.1 Core Principle: Relationship Graph Determines Audience

The audience for every notification is derived from the **entity relationship graph at event time** — not from a manually maintained subscriber list. When VLAN-100 is decommissioned, every VM attached to it gets notified automatically through their relationship edges. No subscription management required.

### 48.2 notification service — Ninth Provider Type

| # | Type |
|---|------|
| 1-8 | (existing providers) |
| **9** | **notification service** — translates DCM unified envelope to delivery channel (Slack, PagerDuty, email, ServiceNow, webhook, SMS); handles delivery, retry, dead letter; reports delivery status back to DCM |

notification services register with DCM declaring supported channels, sovereignty, and delivery guarantees. Organizations configure which channel to use per subscription.

### 48.3 Three Subscription Tiers

**Tier 1 — Mandatory system notifications (non-suppressable):** Security events, sovereignty violations, audit chain breaks. Always delivered to Security Team + Platform Admin. Cannot be filtered.

**Tier 2 — Tenant defaults:** Tenant admin configures baseline for all resources in Tenant — which event categories fire, which channels, urgency routing.

**Tier 3 — Actor subscriptions:** Individual actors subscribe to specific events on specific resources or resource types.

Tiers compose: Tier 1 always fires; Tier 2 applies to all Tenant resources; Tier 3 adds specifics. Actor subscriptions can add channels but cannot suppress Tier 1.

### 48.4 Audience Resolution Algorithm (6 steps)

1. Direct owner of changed entity (role: owner)
2. Traverse relationship graph — for each relationship: check event relevance, check min stake_strength, resolve related entity's owner (role: stakeholder)
3. Approval requirements — add approvers (role: approver)
4. Mandatory system audiences (Security Team, Platform Admin for security events)
5. Actor subscription overrides (can add; cannot remove mandatory)
6. Deduplicate; same actor via multiple paths → one notification with all roles listed

### 48.5 Event Taxonomy (closed vocabulary — 7 categories)

1. **Request lifecycle:** acknowledged, requires_approval, approved, dispatched, completed, failed, cancelled, gating_rejected
2. **Resource lifecycle:** realized, state_changed, ttl_warning, ttl_expired, suspended, resumed, decommissioning, decommissioned, decommission_deferred, ownership_transferred, pending_review
3. **Drift and discovery:** drift.detected, drift.severity_escalated, drift.resolved, drift.escalated, unsanctioned_change.detected
4. **Provider update:** submitted, requires_approval, approved, rejected, auto_approved
5. **Dependency and relationship:** dependency.state_changed, stakeholder.resource_decommissioning, allocation.pool_capacity_low, cross_tenant_auth.revoked
6. **Governance:** policy.activated, external_policy_evaluator.trust_elevated, profile.changed, catalog_item.deprecated
7. **Security/system (mandatory):** audit.chain_integrity_alert, sovereignty.violation, federation.tunnel_degraded, security.unsanctioned_provider_write

### 48.6 Notification Envelope (unified — all channels)

Key fields: notification_uuid (idempotency), correlation_id (links to audit record), event_type, urgency (critical/high/medium/low), entity info, audience role + stakeholder_reason (WHY this actor is in audience), context (previous/new state, changed_fields), action (type/url/deadline for approvals), deep links.

### 48.7 Provider Update + Notifications Integration

`provider_update.requires_approval` fires → consumer receives notification with `action.type: approve`, `action.deadline` (default PT24H). Approved → `provider_update.approved` + `entity.state_changed` to stakeholders. Rejected → `provider_update.rejected` + drift event.

### 48.8 Webhooks Are Now a Notification Channel

Outbound webhooks (doc 18) are superseded by the Notification Model. Webhooks are one channel type within a notification service. Existing webhook registrations are auto-converted to actor-level subscriptions with a webhook-type notification service — no migration needed.

### 48.9 Delivery Pipeline

Event → Audit record → Notification Router resolves audience → Subscription resolution → Envelope generation per actor → Route to notification service(s) → Provider delivers → Delivery confirmation → NOTIFICATION_DISPATCHED audit record.

### 48.10 Policies

NOT-001 through NOT-008. Key: audience derived from relationship graph (NOT-001); mandatory notifications never suppressable (NOT-002); cross-tenant notifications sovereignty-checked (NOT-003); every dispatch is audited (NOT-004); notification service must be registered for external delivery (NOT-007); event taxonomy is closed vocabulary (NOT-008).

REL-022 through REL-024: traversal depth declared in Resource Type Spec; default depth 1; sovereignty respected; same actor via multiple paths → one notification with all roles.

---

## SECTION 49 — GROUP 2: OPERATIONAL MODELS

### 49.1 Three Timeout Scopes

All three independently configurable and audited:
- **Assembly timeout** — max time for Request Payload Processor nine-step assembly (standard: PT3M; prod: PT2M)
- **Dispatch timeout** — max time waiting for provider realization after dispatch (standard/prod: PT30M-PT1H; resource-type overrides for legitimately long types)
- **Reserve-query timeout** — max time for a single provider to respond to reserve query (prod: PT5S); on timeout: skip that candidate, continue placement loop

### 49.2 Cancellation — Three Scenarios

1. **Before dispatch:** Clean cancel; no provider interaction; entity → CANCELLED
2. **After dispatch, provider not started:** DCM sends cancellation; provider confirms; entity → CANCELLED
3. **During PROVISIONING:** Provider capability-dependent:
   - Supports cancellation: send cancel; provider attempts rollback; outcome → Recovery Policy
   - No cancellation support: CANCEL_PENDING; wait for completion; LATE_RESPONSE_RECEIVED fires

Cancellation is always best-effort — never guaranteed. Provider declares `supports_cancellation` and `partial_rollback_possible` at registration.

### 49.3 Discovery Scheduling — Three Trigger Types

1. **Scheduled (cron):** Each Resource Type Spec declares discovery interval; profile overrides; profile_min=PT4H minimal, PT5M fsi/sovereign
2. **Event-triggered:** After entity.realized (PT30S delay), drift.resolved (PT60S), provider.degraded (immediate), TIMEOUT_PENDING (PT5M orphan detection), COMPENSATION_FAILED (immediate)
3. **On-demand:** `POST /api/v1/admin/discovery/trigger` by platform admin; also used by CI/CD pre-validation and brownfield ingestion

Discovery Scheduler component maintains priority queue (Critical → High → Standard → Background). Queue depth bounded per profile.

### 49.4 Recovery Policy Model — The Unified Framework

Recovery Policies are a formal DCM policy type (alongside Gating Policy, Validation, Transformation). Same authoring, GitOps store, shadow mode, activation workflow, and audit trail.

**Trigger vocabulary (closed):** ASSEMBLY_TIMEOUT, DISPATCH_TIMEOUT, RESERVE_QUERY_ALL_EXHAUSTED, LATE_RESPONSE_RECEIVED, CANCELLATION_SENT, CANCELLATION_CONFIRMED, CANCELLATION_FAILED, PARTIAL_REALIZATION, COMPENSATION_IN_PROGRESS, COMPENSATION_FAILED

**Action vocabulary (closed):** DRIFT_RECONCILE, DISCARD_AND_REQUEUE, DISCARD_NO_REQUEUE, ACCEPT_LATE_REALIZATION, COMPENSATE_AND_FAIL, NOTIFY_AND_WAIT (with deadline + on_deadline_exceeded), ESCALATE, RETRY (with backoff + max_attempts + on_exhaustion)

### 49.5 Four Built-in Recovery Profile Groups

| Group | Posture | Profile Default |
|-------|---------|----------------|
| `recovery-automated-reconciliation` | Trust drift detection to converge | minimal/dev/standard |
| `recovery-discard-and-requeue` | Clean up and restart on ambiguity | (opt-in) |
| `recovery-notify-and-wait` | Notify human; never act automatically | prod/fsi/sovereign |
| `recovery-aggressive-retry` | Retry everything before giving up | (opt-in) |

Binding hierarchy: resource-type override > Tenant override > profile default > system default (automated-reconciliation).

`recovery_posture` is a Policy Group concern_type (alongside security, compliance, operational, zero_trust_posture, data_authorization_boundary, orchestration_flow).

### 49.6 Late Response Pipeline

Provider responds after DCM timeout:
1. Late Response Handler activates (entity in TIMEOUT_PENDING state)
2. Cancel the pending cancellation if not yet sent
3. Write realized payload to Realized Store
4. Entity → LATE_REALIZATION_PENDING (if NOTIFY_AND_WAIT) or action per policy (if DRIFT_RECONCILE or DISCARD_AND_REQUEUE)

NOTIFY_AND_WAIT consumer interface: `GET /api/v1/resources/{uuid}/recovery-decisions` and `POST` with chosen action. Platform admin can resolve any entity's pending decision via Admin API.

### 49.7 Composite Service Compensation

Declared per component in service definition:
- `required_for_delivery: atomic` — failure triggers full compensation rollback
- `required_for_delivery: partial` — failure → DEGRADED (not FAILED); no compensation triggered
- `compensation_on_failure: decommission_immediately | release_allocation | skip | notify`
- `compensation_order: <integer>` — reverse order = first-decommissioned; lowest compensation_order runs last in reverse

Partial delivery policy: `min_required_components` declares minimum for DEGRADED delivery; `auto_retry_optional_components` retries failed optional components.

### 49.8 Five New Lifecycle States

| State | Entry | Recovery Trigger |
|-------|-------|-----------------|
| TIMEOUT_PENDING | Dispatch timeout fired | DISPATCH_TIMEOUT |
| LATE_REALIZATION_PENDING | Late response received + NOTIFY_AND_WAIT | LATE_RESPONSE_RECEIVED |
| INDETERMINATE_REALIZATION | DRIFT_RECONCILE action taken | — |
| COMPENSATION_IN_PROGRESS | Compound rollback underway | — |
| COMPENSATION_FAILED | Rollback itself failed | COMPENSATION_FAILED |

### 49.9 Orphan Detection Pipeline

Triggers: timeout with cancellation sent, cancellation failed, compensation failed, DISCARD_NO_REQUEUE. Queries provider for resources matching Requested State characteristics in the provisioning time window, excluding known Realized State UUIDs. Creates ORPHAN_CANDIDATE records; notifies platform admin (urgency: high); human resolves (manual decommission, adopt into DCM, or mark false positive).

### 49.10 Policies

OPS-010 through OPS-019. Key: cancellation always best-effort (OPS-011); recovery policies are formal DCM policy type (OPS-014); four built-in recovery profiles (OPS-015); binding hierarchy resource-type > Tenant > profile (OPS-016); compensation in reverse dependency order (OPS-017); orphan detection on any uncertain cleanup (OPS-018); NOTIFY_AND_WAIT deadline always has on_deadline_exceeded action (OPS-019).

---

## SECTION 50 — GROUPS 3, 4, AND 5: FINAL ARCHITECTURE GAPS

### 50.1 Cost Analysis — Information Provider Model (Group 3)

Cost Analysis is an **Information Provider** — not a built-in DCM component. DCM does not calculate costs; it provides input data and consumes cost signals. Integration target: Red Hat Cost Management or any external cost management platform.

**DCM provides to Cost Analysis:** entity lifecycle events (realized/suspended/decommissioned with billing_state), provider catalog item declared costs, provider capacity utilization, request payload previews for pre-request estimates.

**Cost Analysis provides to DCM:** pre-request cost estimates (pulled by service catalog and CI pipeline), placement cost signals (pulled during placement Step 4), cost actuals (pushed after billing period), budget alerts (pushed when thresholds approached).

**Fallback chain:** Cost Analysis provider → static declared cost (provider registration) → resource type default estimate → no estimate. Staleness thresholds govern fallback (PT24H standard; PT1H sovereign).

CMP-001, CMP-002.

### 50.2 Orchestration — Reconciled Model (Replaces Conflicting Earlier Statements)

DCM orchestration operates at two levels that compose through the same Policy Engine and event bus:

**Level 1 — Named Workflow Artifacts (explicit, visible, auditable):**
An Orchestration Flow Policy with `concern_type: orchestration_flow` and `ordered: true` is a named workflow. It declares steps in explicit sequence using the closed payload type vocabulary as step identifiers. Named workflows are first-class Data artifacts — versioned, GitOps-managed, profile-bound, same lifecycle as all other artifacts. The request lifecycle pipeline is a built-in system Orchestration Flow Policy that cannot be deactivated but can be extended. Workflows are triggered: by events on the Request Orchestrator, by schedule (via Discovery Scheduler pattern), manually via Admin API, or by output of another policy.

**Level 2 — Dynamic Policies (conditional, inline):**
Gating Policy, Transformation, Recovery, Governance Matrix, and Lifecycle Policies fire when their match conditions are satisfied — within or alongside workflow steps. They are not declared in workflow artifacts; they evaluate whenever payload state matches their conditions.

**How they compose:** A named workflow step fires when its declared payload type event occurs. Dynamic policies also fire on the same event if their conditions match. Both are evaluated by the same Policy Engine. Both are triggered by events on the Request Orchestrator event bus. The workflow provides the explicit sequence skeleton; dynamic policies provide conditional behavior within it.

**The "Orchestrator" term** in earlier sections refers to the combination of: Request Orchestrator (event bus) + Orchestration Flow Policy evaluation (named workflows) + Policy Engine (dynamic policy evaluation). There is no separate "Orchestrator" component — the Request Orchestrator is the event bus, and workflows are Policies.

**Adding an explicit pipeline step** = add a step to an Orchestration Flow Policy artifact.
**Adding conditional behavior** = write a Gating Policy, Transformation, or Recovery policy.
**Both are Data artifacts evaluated by the Policy Engine.**

### 50.3 Ingress API vs Consumer API (Group 5 fix)

The **Ingress API** is the network infrastructure layer (API Gateway) — TLS termination, auth validation, rate limiting, ingress block population, routing. It routes to three logical API surfaces on distinct path prefixes:
- `/api/v1/` → **Consumer API** (catalog, requests, resource management, audit)
- `/api/v1/provider/` → **Provider API** (callbacks, update notifications, cancellation)
- `/api/v1/admin/` → **Admin API** (discovery triggers, orphan review, tenant management)

The Ingress API is not a separate service — it is the API Gateway component. CMP-007.

### 50.4 Consumer Rate Limiting and Quota Model (Group 5 fix)

**Request rate quotas** — enforced at Ingress API level per actor; returns 429 with Retry-After. Configured in platform-domain layer.

**Resource quotas** — enforced by Gating policies at Step 5 (pre-placement). No hardcoded mechanism — quotas are declared policies. Quota exceeded → QUOTA_EXCEEDED Gating Policy rejection. Quota increase requests submitted via `Process.QuotaIncreaseRequest` catalog item → Orchestrator routes to platform admin for approval → Gating policy updated.

CMP-006.

### 50.5 Drift Severity — Three-Tier Classification (Group 4 fix)

**Tier 1 — Field criticality** (declared in Resource Type Spec): `drift_criticality: minor|significant|critical` per field.

**Tier 2 — Magnitude thresholds** (system layer, overridable at platform/tenant): >50% change on significant field upgrades to critical; 10+ changed items upgrades minor to significant.

**Tier 3 — Provider and consumer injection:** Providers suggest severity in update notifications (raise only). Consumers override sensitivity on specific entities (raise or lower — entity owner controls their resource's sensitivity).

**Resolution:** highest severity from all three tiers wins.

### 50.6 Cross-Tenant Authorization Lifecycle (Group 4 fix)

`cross_tenant_authorization` is a DCMGroup with `group_class: cross_tenant_authorization`. Created by: granting Tenant admin (standard), Platform Admin (emergency), or pre-authorization policy (automated). Has declared duration or perpetual. On revocation: all active allocations/stakes under that authorization enter PENDING_REVIEW; notifications to both Tenant admins and affected resource owners; PT72H default resolution deadline; on_deadline_exceeded recovery policy fires. CTX-001 through CTX-004.

### 50.7 Bootstrap Tenant Creation Sequence (Group 4 fix)

Three foundation Tenants created during bootstrap (declared in bootstrap manifest, cannot be decommissioned):
- `__platform__` — owns DCM's own control plane resources
- `__transitional__` — holds brownfield entities during ingestion
- `__system__` — owns system-level artifacts

Bootstrap sequence: verify manifest → initialize storage → create foundation Tenants → create initial Platform Admin actor → activate system layers/policies/recovery profiles → register built-in providers → ready. RED-016.

### 50.8 Catalog Item vs Resource Type Clarification (Group 5 fix)

**Resource Type** — classification category; vendor-neutral; declares field schema expectations; groups catalog items for portability.

**Resource Type Specification** — versioned formal definition in registry; providers implement against this.

**Provider Catalog Item** — what a specific provider offers to consumers: specific options, cost, availability, SLAs, linked to a Resource Type Specification version. Can be a resource allocation OR a process (automation job, playbook, pipeline). *Consumers request by Resource Type; DCM resolves to a catalog item.*

Anti-vocabulary: never say "catalog item" when you mean "resource type specification." Never say "resource type" when you mean a specific offering.

### 50.9 BBQ-001 and Federation Routing Reconciliation (Group 5 fix)

These operate at different scopes — complementary not conflicting:
- **DCM-010 sovereignty pre-filter (Hub level):** Which Regional DCMs are eligible for this request?
- **BBQ-001 check (Regional DCM level):** Is this Mode 4 External Policy Evaluator endpoint within my sovereignty boundary?

Hub selects Regional DCM using DCM-010. Regional DCM applies BBQ-001 for its own Mode 4 queries. Hub sovereignty pre-filter does NOT bypass Regional DCM's BBQ-001 check.

---

## SECTION 51 — ACCREDITATION, DATA AUTHORIZATION MATRIX, AND ZERO TRUST

### 51.1 Three Interconnected Models

Three models compose to govern trust and data handling across all DCM boundaries:
1. **Accreditation** — is this component certified to handle this data type?
2. **Data/Capability Authorization Matrix** — given certification, what data/capabilities are permitted across this boundary?
3. **Zero Trust** — is this specific call, right now, from who it claims to be, permitted to do what it's attempting?

All three checks run at every interaction boundary. All five boundary checks (identity → authorization → accreditation → matrix → sovereignty) produce audit records regardless of outcome.

### 51.2 Data Classification — First-Class Field Metadata

Eight classification levels: `public | internal | confidential | restricted | phi | pci | sovereign | classified`

Carried as `data_classification` on every field in every DCM payload. Declared in: Resource Type Specification (default per field), Data Layer (domain-wide override), explicit field instance (highest precedence). `phi`, `sovereign`, `classified` are **immutable once set** — no layer or policy may downgrade them (ACC-003). Default for unclassified fields: `internal`.

### 51.3 Accreditation Model

First-class versioned artifacts. Seven types (ascending trust): `self_declared`, `first_party`, `third_party`, `qsa_assessment`, `baa`, `regulatory_certification`, `sovereign_authorization`. Lifecycle: developing → proposed → active → deprecated → retired. Renewal warning P90D before expiry. On expiry/revocation: **Accreditation Gap** record created; Recovery Policy evaluates response; affected entities potentially blocked.

Accreditations cover: `data_classifications`, `capabilities`, `geographic_scope`. DCM deployments themselves carry accreditations (enabling federated trust verification). Providers declare accreditations via `POST /api/v1/provider/accreditations` → proposed → platform admin activates.

### 51.4 Data/Capability Authorization Matrix

Policy Group artifact with `concern_type: data_authorization_boundary`. Activated as part of compliance domain group (HIPAA domain → HIPAA boundary matrix). Three sections:

**Outbound data permissions:** `data_classification × required_accreditation_type → ALLOW | STRIP_FIELD | DENY_REQUEST | WARN_AND_ALLOW`. PHI requires BAA — no BAA → DENY_REQUEST. Restricted requires third_party — no third_party → STRIP_FIELD.

**Capability permissions:** STORE_AT_REST on PHI requires BAA. REPLICATE_CROSS_REGION on PHI requires BAA + replication target also has BAA. EXPORT_TO_EXTERNAL_SYSTEM on PHI/restricted/sovereign requires regulatory_cert.

**Inbound data permissions:** What provider may return; which partition stores it; consumer visibility requirements.

**Federation boundary matrix:** `sovereign` and `classified` data = `hard_constraint: true` → NEVER crosses any federation boundary regardless of accreditation. This cannot be overridden by any policy.

**Enforcement pipeline:** Classification inventory → Accreditation resolution → Matrix evaluation per field → ALLOW/STRIP/DENY/WARN → Audit record.

### 51.5 Zero Trust Interaction Model

**Network position grants zero trust.** Five checks at every boundary:
1. Identity verification (mTLS mutual; certificate pinning; hardware attestation for sovereign)
2. Authorization verification (explicit permission; scoped credential; not revoked)
3. Accreditation check (target holds required cert; current; in-scope)
4. Data/Capability Matrix check (fields and capabilities permitted)
5. Sovereignty check (BBQ-001; endpoint within boundary)

All five produce audit records on pass AND fail.

**Credentials:** Scoped (minimum necessary operation), short-lived (PT15M for fsi/sovereign; PT30M prod; PT1H standard), non-transferable. Bound to specific entity + provider + operation type.

### 51.6 Zero Trust Posture — Sixth Policy Group Concern Type

Four levels: `none` (minimal) → `boundary` (dev/standard; external boundaries only) → `full` (prod/fsi; everywhere including internal) → `hardware_attested` (sovereign; TPM/HSM required).

Profile defaults: minimal=none, dev/standard=boundary, prod/fsi=full, sovereign=hardware_attested.

### 51.7 Federation Tunnel Zero Trust

Federation tunnels = secure transport, not implicit trust. Structure: mTLS with certificate pinning + per-message signing (ed25519) + replay protection (nonce + PT5M window). Federation credentials scoped to specific operation + specific tunnel + specific resource types. Non-transferable.

Hub-spoke: Hub presents its own credential to Regional DCMs. Regional DCM credentials are never relayed. Each DCM instance verifies the Hub's accreditation before accepting federation messages.

Data boundary: sovereign/classified NEVER crosses federation tunnel (hard_constraint). fsi: max classification = restricted within same jurisdiction. sovereign: internal only, same instance.

### 51.8 Policies

ZT-001 through ZT-005 (zero trust) + ACC-001 through ACC-006 (accreditation). Key:
- ZT-001: network position = zero trust
- ZT-003: sovereign/classified never crosses any boundary (hard constraint)
- ZT-004: federation tunnel = secure transport, not trust
- ACC-003: phi/sovereign/classified classification is immutable
- ACC-004: matrix enforced at every outbound boundary before dispatch
- ACC-006: zero_trust_posture is the sixth Policy Group concern type

---

## SECTION 52 — PERSONAS

| Persona | Primary Concern |
|---------|----------------|
| **Consumer** | Self-service access to resources and services |
| **Service Provider** | Exposing services through DCM catalog |
| **Auditor** | End-to-end transaction review and validation |
| **Policy Creator** | Defining and maintaining governance policies |
| **SRE** | Stability, uptime, drift reconciliation, brownfield management |
| **CTO** | Accelerate innovation, reduce risk, enable sovereignty |
| **CIO/MD** | Lifecycle management, agility, IT investment maximization |
| **CISO/CCO** | Sovereignty enforcement, compliance, risk reduction |
| **Application Owner** | Focus on application code, not infrastructure specifics |
| **Line of Business** | Business outcomes — new products, revenue, compliance |

---

## SECTION 53 — GOVERNANCE MATRIX, REGISTRATION, AND DRIFT RECONCILIATION

### 53.1 Unified Governance Matrix (doc 27)

The **single enforcement point** for all cross-boundary data and capability decisions in DCM. Supersedes the Data/Capability Authorization Matrix in doc 26 Section 4. Evaluates every interaction using four axes:

**Axis 1 — Subject (who):** actor | service_provider | information_provider | auth_provider | peer_dcm | process_provider | system. With identity (specific UUID or trust_posture or accreditation_level) and tenant scope.

**Axis 2 — Data (what):** classification (exact/in/minimum/maximum), resource_type, field_paths (allowlist/blocklist/any with dot-notation paths including wildcards `fields.phi_*`), capability (read/write/store/replicate/export/notify/execute/discover/query/federate).

**Axis 3 — Target (where):** type, specific provider/peer UUID, sovereignty_zone (match/not_in), jurisdiction (includes/excludes/intersects country codes), trust_posture (minimum), accreditation_held (includes/not_includes).

**Axis 4 — Context (under what conditions):** profile (posture/compliance_domains), zero_trust_posture (minimum level), tls_mutual, hardware_attestation, federated, cross_jurisdiction, cross_tenant.

**Decisions:** ALLOW | DENY | ALLOW_WITH_CONDITIONS | STRIP_FIELD | REDACT | AUDIT_ONLY

**Hard vs soft enforcement:** Hard rules cannot be relaxed by any downstream rule — ever. GMX-004: sovereign/classified data DENY to all external targets is always hard regardless of profile. Soft rules can be tightened by more-specific domain rules.

**Field-level granularity:** allowlist mode (only named fields cross boundary), blocklist mode (named fields stripped/redacted), passthrough. STRIP_FIELD removes field; REDACT replaces value with `<REDACTED>`; if stripped field is required → escalates to DENY_REQUEST (GMX-010).

**Profile-bound defaults:** minimal (pass public/internal; hard DENY sovereign/classified), dev (add confidential with TLS), standard (restricted requires third_party accreditation; PHI denied by default), prod (verified peers only for confidential+; notification fields stripped for restricted), fsi (cross-jurisdiction hard DENY for regulated data; PHI requires BAA+verified+full-ZT), sovereign (no sensitive data in federation; hardware attestation required for all federation).

**Compliance domain rules:** Automatically added when domain active. HIPAA: minimum_necessary principle; PHI audit all interactions; no export without regulatory cert. GDPR: EU residency hard rule; personal identifier fields stripped outside EU zones.

**Sovereignty zones:** Registered artifacts declaring jurisdictions, regulatory frameworks, inter-zone agreements, and required provider accreditation. Rules reference zones by ID, not raw country codes.

**Evaluation algorithm:** Hard DENY first → any hard DENY = terminal DENY. Soft constraints by domain precedence (entity > resource_type > tenant > platform > system); DENY > STRIP_FIELD > ALLOW. Conditions evaluated for ALLOW_WITH_CONDITIONS. Field permissions applied. Audit record always written. GMX-001 through GMX-010.

### 53.2 Registration Specification (dcm-registration-spec.md)

**Provider Type Registry:** Three-tier (Core/Community/Organization). Each entry declares permissions, default_approval_method, default_trust_level, enabled_in_profiles, capability_schema_ref. Five provider types: service_provider (reviewed), information_provider (reviewed), auth_provider (verified), peer_dcm (verified), process_provider (reviewed).

**Registration token model:** Pre-issued by platform admin (POST /api/v1/admin/registration-tokens). Scoped to provider_type, handle_pattern, sovereignty_zone. single_use. grants_auto_approval flag. Token value presented once — never retrievable. Max trust level bounded by token scope.

**Approval method resolution:** most_restrictive(provider_type_default, profile_min_method, token_grants_auto). Profile can only tighten. Token can relax to auto ONLY if profile.allow_token_auto_approval=true. Committee approval cannot be relaxed by token.

**Profile defaults:** minimal/dev → reviewed, token auto-approval enabled. standard → reviewed, token auto-approval enabled (max trust: standard). prod → reviewed; high-trust types require verified; no token auto-approval. fsi → verified everything; minimum_accreditation: third_party. sovereign → authorized everything; minimum_accreditation: regulatory_certification; hardware_attestation required.

**Registration pipeline:** SUBMITTED → VALIDATING (8 automated checks: provider type enabled, governance matrix pre-check, registration token, certificate, sovereignty declaration, capability consistency, health endpoint, accreditation) → PENDING_APPROVAL → ACTIVE. Approval methods: auto (immediate), reviewed (one admin), verified (two independent admins), authorized (DCMGroup quorum).

**Per-type capability schemas:** service_provider (resource types, capacity model, cancellation support, discovery, naturalization format, cost metadata), information_provider (data domains, authority level, query capacity, confidence model), auth_provider (auth modes, MFA methods, RBAC model, token lifetime), peer_dcm (federation scope, trust level, mTLS certificate), process_provider (workflow types, execution engine, callback pattern).

**Federated trust postures:** verified (manually approved; full scope), vouched (Hub-introduced; bounded scope), provisional (crypto-verified; catalog_query only if profile permits). Approval: dev auto-promotes provisional; standard reviewed for verified; prod/fsi verified; sovereign authorized+hardware-attestation. Profile federation_policy block declares all parameters.

**Ongoing lifecycle:** health monitoring (polling; degraded → reduced routing; failure_threshold → UNAVAILABLE; 2×threshold → drift triggered), certificate rotation (P90D default; P14D warning; P7D transition window), capability amendments (simplified flow), graceful deregistration (entity migration plan required), forced deregistration (verified/authorized; entities → INDETERMINATE_REALIZATION; Recovery Policy fires).

### 53.3 Drift Reconciliation Component (doc 25 Section 7)

Control plane component that compares Discovered State vs Realized State. Read-only — never writes to Realized Store. Produces drift records and events into Request Orchestrator.

**Algorithm:** discovery.cycle_complete event → field-by-field comparison per entity → field criticality (from Resource Type Spec) × change magnitude (profile-governed thresholds) → severity matrix (minor/significant/critical) → unsanctioned check (no corresponding Requested State? → elevate one level; fire unsanctioned_change.detected) → drift_record created → drift.detected event → Policy Engine evaluates response.

**Drift record:** entity_uuid, discovery_snapshot_uuid, realized_state_uuid, overall_severity, unsanctioned flag, drifted_fields (field_path, realized_value, discovered_value, field_criticality, change_magnitude, field_severity, elevated_for_unsanctioned), status (open/acknowledged/resolved/escalated).

**Resolution tracking:** Drift record status updated when REVERT (next discovery shows clean) or UPDATE_DEFINITION (new Realized State written) or ACCEPT or entity DECOMMISSIONED. drift.resolved event published.

**Governance matrix integration:** Checks if a governance matrix rule permits the provider to make this type of change. If yes: warning (provider should have submitted update notification). Still treated as drift — provider must use the Provider Update Notification API.

DRC-001 through DRC-005. Nine control plane components now fully defined in doc 25.

---



## SECTION 54 — FEDERATED CONTRIBUTION MODEL (doc 28)

### Core Principle
DCM defaults to a federated model for data creation, import, usage, and lifecycle. Every authorized actor type can contribute Data artifacts within their permitted domain scope. The same GitOps PR flow and lifecycle (developing → proposed → active → deprecated → retired) applies to all contributors. Profile-bound auto-approval governs what requires human review.

### Four Contributor Types
1. **Platform Admin** — all artifact types, all domains, no restrictions
2. **Consumer/Tenant** — tenant-domain policies, resource groups, notification subscriptions, webhook registrations, cross-tenant authorization records, request layers
3. **Service Provider** — resource type specs (types they offer), provider catalog items, service layers, provider-domain policies
4. **Peer DCM** — registry entries, policy templates, service layers (via federation channels, scoped by trust posture)

### Contributor Permission Boundaries (hard DENY — Governance Matrix enforced)
- Consumers cannot contribute system or platform domain policies
- Providers cannot contribute specs for resource types they don't offer
- Provisional peers: registry entries only (no policies; authorized approval)
- Vouched peers: registry entries + service layers only (reviewed always)
- Verified peers: registry entries + policy templates + service layers (reviewed standard+; auto dev)

### Universal Contribution Pipeline
Submit → Governance Matrix evaluates contributor permissions → proposed status (shadow mode for policies) → review flow (auto / reviewed / verified / authorized per profile + artifact type + contributor) → active → lifecycle by contributor (deprecate/retire) → platform admin override at any time

### Contribution Artifact Types by Contributor
- Consumer: tenant policies (all 7 types), resource groups, notification subs, webhooks, cross-tenant auth records, request layers
- Provider: Resource Type Specs (their types), catalog items, service layers, provider-domain Gating Policy/Validation policies
- Peer DCM: registry entries, policy templates (verified peers), service layers (verified/vouched)

### Contribution Store Directory Structure
`dcm-policy-store/system/` (platform admin) · `platform/` (platform admin) · `tenant/<handle>/` (consumer) · `provider/<handle>/` (provider) · `federated/<peer-dcm-uuid>/` (peer DCM)
`dcm-registry/core/` (DCM project) · `community/<contributor>/` (community) · `organization/<provider>/` (org)

Every artifact includes `contributed_by` block: contributor_type, actor/tenant/provider/peer_dcm UUID, contribution_method (api/flow_gui/git_pr/federation_push), pr_url, reviewed_by. Immutable once set.

### Profile-Governed Auto-Approval
- minimal/dev: most contributions auto-approved; shadow optional
- standard: consumer/provider policies → reviewed; shadow default on, P7D review period
- prod: governance matrix rules → verified; provider specs → reviewed; shadow P14D
- fsi: all consumer/provider contributions → verified; shadow P30D; must review all divergence cases
- sovereign: all → authorized; shadow P30D; orphaned artifacts auto-retire

### Consumer API Contribution Endpoints (Section 9)
`POST /api/v1/contribute/policy` (generates PR, activates shadow mode) · `POST /api/v1/contribute/resource-group` (activates immediately) · `GET /api/v1/contribute` (list contributions) · `DELETE /api/v1/contribute/{uuid}` (withdraw, closes PR)

### Organization Sub-Tiers (Registry)
Three-tier model extended to all artifact types: `organization/platform` (platform admin authored), `organization/provider` (provider authored, scoped to their types), `organization/tenant` (consumer authored, scoped to their Tenant). Lower sub-tier = lower inherent trust = may require additional review.

### FCM-001 through FCM-008 System Policies
FCM-001: contributor recorded in contributed_by; immutable. FCM-002: domain scope violations = hard DENY. FCM-003: all contributions via GitOps PR (except auto-approve). FCM-004: policies enter shadow mode by default. FCM-005: platform admin override always available; audited. FCM-006: orphaned artifacts don't auto-deactivate (except sovereign). FCM-007: federation contribution scoped by trust posture. FCM-008: contributor scope limits absolute.

---

## SECTION 55 — TERMINOLOGY GLOSSARY

| Term | Definition |
|------|-----------|
| **DCM** | Data Center Management — the framework itself |
| **Sovereign Execution Posture** | Target state where all operations are governed, auditable, and sovereignty-compliant |
| **Hard Tenancy** | Strict isolation between tenants at the infrastructure level |
| **UDM** | Unified Data Model — the centralized data schema and single source of truth |
| **Naturalization** | Converting UDM format to provider-specific format for execution |
| **Denaturalization** | Converting provider-specific results back to UDM format |
| **Greening the Brownfield** | Bringing existing unmanaged resources under DCM lifecycle management |
| **Intent Portability** | Replaying an Intent State through current policies to produce a new Requested State |
| **Resource Type** | Abstract, vendor-neutral definition of a class of resource |
| **Provider Catalog Item** | Concrete provider implementation of a Resource Type Specification |
| **Portability-Breaking** | A field or operation that ties a request to a specific provider |
| **CMDB** | Configuration Management Database — DCM aims to replace the fragmented multi-CMDB problem |
| **GRC** | Governance, Risk, and Compliance |
| **TTR** | Time to Recovery — key metric for rehydration use case |
| **MTTD** | Mean Time to Deploy or Detect |
| **MTTR** | Mean Time to Recovery/Repair |
| **FSI** | Financial Services Institution |
| **IaC** | Infrastructure as Code |
| **GitOps** | Managing infrastructure definitions through Git workflows |
| **CRUD** | Create, Read, Update, Delete — full lifecycle operations |
| **IPU** | In-Place Upgrade |
| **EOL** | End of Life |
| **Field-Level Provenance** | Structural mechanism carrying data lineage within each data object |
| **Data Lineage** | Complete chain of custody of any field value from origin through all modifications |
| **Base Layer** | Foundation entity for a resource — every layer chain starts here |
| **Core Layer** | Type-agnostic data layer carrying organizational and infrastructure context |
| **Service Layer** | Type-scoped data layer carrying service-specific configuration — must declare Resource Type scope |
| **Request Layer** | Consumer's declared intent — becomes Intent State on submission |
| **Layer Chain** | Ordered sequence of layers merged to produce an assembled payload |
| **Assembly Process** | Seven-step process by which the Request Payload Processor builds a Requested State payload |
| **Gating Policy** | Highest-authority policy that can override any field including consumer input |
| **Transformation Policy** | Policy that enriches or modifies payload fields — all changes recorded in provenance |
| **Validation Policy** | Policy that checks payload against rules — pass/fail, no field modification |
| **Resource/Service Request** | What a consumer submits to DCM — declared intent to consume a resource or service |
| **Resource/Service Entity** | The "thing" produced by a provider fulfilling a request — the allocation made real |
| **DCM Tenant** | Mandatory first-class ownership boundary for all Resource/Service Entities |
| **Allocation Model** | Provider retains infrastructure ownership; consumer owns the Entity allocation |
| **Whole Allocation Model** | Entire resource allocated as indivisible unit; provider retains ownership |
| **Full Transfer Model** | Provider transfers complete ownership of underlying resource to consumer Tenant |
| **Hybrid Transfer Model** | Ownership can transfer multiple times; always exactly one owning Tenant |
| **Process Resource Entity** | Ephemeral execution resource — playbook, pipeline, workflow. Permanent execution record. |
| **Dependency Graph** | Complete map of all resources required to fulfill a request including transitive dependencies |
| **Type-Level Dependency** | Portable, provider-agnostic dependency declared at Resource Type Specification level |
| **Provider-Specific Dependency** | Additional dependency declared at Provider Catalog Item level — must be marked portability-breaking |
| **Resource Group** | Flexible composable grouping entity — functions like a structured tag |
| **Custom Resource Group** | Implementor-defined grouping entity with full parity to DCM Default Resource Group |
| **Tenant Advocate** | DCM's role in protecting Tenant interests in all provider interactions |
| **DCM System Policy** | Non-overridable policy built into DCM — cannot be disabled or overridden by organizational policy |
| **Webhook** | Push-based outbound notification from DCM to an external system triggered by a DCM event |
| **Commit Log** | Stage 1 audit store — minimal record, Raft consensus quorum write, sub-millisecond; Audit Forward Service reads from it to produce full audit records |
| **Audit Forward Service** | DCM component that enriches Commit Log entries into full audit_record structures and delivers them to the Audit Store asynchronously with retry |
| **Self-Hosting** | DCM's own deployment is a DCM resource; DCM manages itself through the same model used for customer infrastructure |
| **dcm_deployment** | The DCM resource declaring DCM's own deployment — profile, replica counts, store implementations, redundancy configuration |
| **Bootstrap manifest** | The minimal configuration outside DCM's management scope used to bootstrap DCM before it can manage itself |
| **Redundancy by Default** | DCM architectural principle: every component and store has a redundancy model; `minimal` profile sets replicas: 1; all others set replicas >= 3 |
| **Quorum Write** | Write confirmed durable only when a majority of replicas acknowledge it; used by Commit Log and all durable stores in standard+ profiles |
| **Raft** | Consensus protocol used by Commit Log (etcd) for quorum writes; guarantees durability even if minority of replicas fail |
| **DCMGroup** | Universal group entity — all grouping constructs in DCM expressed as DCMGroup with group_class |
| **group_class** | Determines system behavior of a DCMGroup — closed built-in set: tenant_boundary, resource_grouping, policy_collection, policy_profile, layer_grouping, composite, federation |
| **Cost Analysis Information Provider** | Specialized Information Provider supplying cost estimates, placement cost signals, cost actuals, and budget alerts; DCM provides input data; provider performs calculations |
| **Orchestration Flow Policy** | Named workflow artifact: Orchestration Flow Policy with `ordered: true`; declares explicit step sequence using payload type vocabulary; first-class Data artifact; versioned, GitOps-managed, profile-bound |
| **Request Orchestrator** | Runtime event bus; routes lifecycle events to Policy Engine; has no pipeline logic; both named workflows and dynamic policies are evaluated through it |
| **orchestration (DCM)** | Two-level composable model: Level 1 = named Orchestration Flow Policies (explicit sequence); Level 2 = dynamic policies (conditional, inline); both evaluated by Policy Engine; adding a step = adding to a workflow Policy; adding conditional behavior = writing a dynamic policy |
| **Provider Catalog Item** | What a specific Service Provider offers consumers: specific resource allocation or process with cost, availability, SLAs; linked to Resource Type Specification version |
| **cross_tenant_authorization** | DCMGroup with group_class: cross_tenant_authorization; grants one Tenant permission to reference/allocate/stake another Tenant's resources; revocation places active allocations in PENDING_REVIEW |
| **foundation Tenants** | Three system Tenants created at bootstrap: __platform__, __transitional__, __system__; cannot be decommissioned; declared in bootstrap manifest |
| **QUOTA_EXCEEDED** | Gating Policy rejection code when resource quota policy fires at Step 5 (pre-placement) |
| **Federated Contribution Model** | DCM defaults to federated data creation — all authorized actor types (platform admin, consumer/tenant, service provider, peer DCM) can contribute Data artifacts within their domain scope via the GitOps PR model; see doc 28 |
| **contributor** | Actor type that authored a Data artifact; recorded in artifact_metadata.contributed_by; determines review requirements; platform_admin / consumer / service_provider / peer_dcm |
| **contributed_by** | Artifact metadata block recording contributor_type, actor UUID, contribution_method, pr_url, reviewed_by; immutable once set |
| **DPO-001–006** | Design Priority system policies. DPO-001: security properties present in all profiles (not controlled by profiles). DPO-002: every security requirement needs an ease-of-use mechanism. DPO-005: minimal profile = "security with minimal overhead" not "minimal security". DPO-006: when security and ease conflict, redesign ease-of-use, not security. |
| **FCM-001–008** | Federated Contribution Model system policies; key: FCM-002 (domain scope violations = hard DENY), FCM-003 (GitOps PR for all), FCM-008 (contributor scope limits absolute) |
| **Unified Governance Matrix** | Single enforcement point for all cross-boundary decisions; four axes (subject/data/target/context); hard vs soft enforcement; field-level granularity (allowlist/blocklist/paths); profile-bound defaults; GMX-001–010 |
| **governance_matrix_rule** | Artifact declaring match conditions across four axes and a decision (ALLOW/DENY/ALLOW_WITH_CONDITIONS/STRIP_FIELD/REDACT/AUDIT_ONLY) with hard or soft enforcement |
| **sovereignty_zone** | Registered DCM artifact declaring geopolitical/regulatory boundary; rules reference zones by ID; inter-zone agreements declared explicitly |
| **STRIP_FIELD** | Governance matrix decision: remove named fields from payload and proceed; if stripped field is required → DENY_REQUEST |
| **REDACT** | Governance matrix decision: replace field value with `<REDACTED>`; field presence preserved; receiver knows field exists but not its value |
| **Provider Type Registry** | Three-tier registry of approved provider types; each entry declares permissions, default_approval_method, enabled_in_profiles, capability_schema_ref |
| **registration_token** | Pre-issued by platform admin; scoped to provider_type/handle_pattern/zone; single_use; grants_auto_approval flag; value presented once only |
| **approval_method** | Registration approval: auto | reviewed | verified | authorized; resolved as most_restrictive(provider_type_default, profile_min, token_effect) |
| **Drift Reconciliation Component** | Control plane component; compares Discovered vs Realized State; produces drift records and events; never writes to Realized Store; DRC-001–005 |
| **drift_record** | Artifact produced by Drift Reconciliation; field-by-field comparison result with severity classification; unsanctioned flag; status tracking through resolution |
| **Placement Engine** | Six-step algorithm: sovereignty filter → accreditation filter → capability filter → reserve query → tie-breaking (policy/priority/affinity/cost/load/hash) → confirm; PLC-001–006 |
| **reserve_query** | Parallel capacity queries to all eligible provider candidates; PT5M capacity hold; non-responders and insufficient-capacity providers excluded |
| **consistent hash** | Final placement tie-breaker: SHA-256(request_uuid+resource_type+sorted_candidates); deterministic; never round-robin |
| **Lifecycle Constraint Enforcer** | Monitors TTL/expiry/max_execution_time; fires expiry actions through standard pipeline; grace period before action; Process Resources: immediate FAILED on breach; LCE-001–005 |
| **Search Index** | Non-authoritative queryable projection of GitOps stores; indexes key fields; returns git_path for full payload; max staleness PT5M; always rebuildable; SIX-001–004 |
| **Admin API** | Platform admin REST interface: Tenant lifecycle, provider review, accreditation approval, discovery trigger, orphan resolution, recovery decisions, quota management, Search Index rebuild, bootstrap operations |
| **PENDING_EXPIRY_ACTION** | Entity state when expiry action fails to execute; Lifecycle Constraint Enforcer retries per Recovery Policy; Platform Admin notified urgency: high |
| **data_classification** | First-class field metadata: public/internal/confidential/restricted/phi/pci/sovereign/classified; phi/sovereign/classified are immutable once set |
| **Accreditation** | Formal versioned attestation that a component satisfies a compliance framework; issued by an Accreditor; carries validity period; lifecycle: developing→proposed→active→expired/revoked |
| **Accreditor** | Entity that issues accreditations: government body, regulatory body, QSA, certification body, or internal audit team |
| **Accreditation Gap** | Missing, expired, or revoked accreditation required for an active interaction; always high/critical severity; Recovery Policy governs response |
| **Data/Capability Authorization Matrix** | Policy Group artifact (concern_type: data_authorization_boundary) declaring what data fields and capabilities are permitted across interaction boundaries given data classification and accreditation level |
| **zero_trust_posture** | Sixth Policy Group concern type; four levels: none/boundary/full/hardware_attested; profile defaults: minimal=none, dev/standard=boundary, prod/fsi=full, sovereign=hardware_attested |
| **Five-check boundary model** | Identity → Authorization → Accreditation → Matrix → Sovereignty; all five checks at every DCM interaction boundary; all produce audit records |
| **Federation tunnel** | Mutually authenticated, encrypted, scoped DCM-to-DCM channel; zero trust model; establishes secure transport only, not implicit trust; per-message signing; scoped non-transferable credentials |
| **hard_constraint** | Data/Capability Matrix declaration that cannot be overridden by any policy; sovereign/classified data never crossing federation boundaries is a hard_constraint |
| **STRIP_FIELD** | Matrix enforcement action: remove non-permitted field from payload and proceed; if stripped field is required → escalates to DENY_REQUEST |
| **DENY_REQUEST** | Matrix enforcement action: block entire interaction; entity enters PENDING_REVIEW; notification dispatched |
| **Request Orchestrator** | DCM control plane event bus; routes lifecycle events to Policy Engine; coordinates pipeline via event-condition-action; does not contain hardcoded pipeline logic |
| **Cost Analysis Component** | Internal DCM control plane component; three functions: pre-request estimation, placement input, ongoing attribution; not a billing system; not a provider type |
| **Module** | DCM capability extension adding new functions; distinct from Profile (which configures behavior) |
| **orchestration_flow** | Policy Group concern_type for static sequential flows; ordered: true; both static and dynamic flows compose through the same Policy Engine |
| **payload_type** | Closed vocabulary of event types the Request Orchestrator publishes; policies pattern-match on payload type + state |
| **OPA integration** | Reference implementation for Mode 3 External Policy Evaluators; DCM payload as OPA input document; built-in Rego functions provided by DCM |
| **Flow GUI** | Visual policy composer and orchestration manager; execution graph view, policy canvas, shadow mode dashboard, flow simulation |
| **__platform__** | Immutable system Tenant owning DCM control plane resources; created at bootstrap before Policy Engine comes online |
| **__transitional__** | Immutable system Tenant holding brownfield entities during INGEST phase |
| **bootstrap manifest** | Signed manifest declaring initial system Tenants, bootstrap admin, and initial profile; hash-verified at every DCM startup |
| **cross_tenant_authorization** | DCMGroup with this group_class formally grants one Tenant access to another's resources; has lifecycle (duration, renewal, revocation); revocation places active allocations in PENDING_REVIEW |
| **drift_criticality** | Field-level property in Resource Type Spec (low/medium/high/critical); combined with change magnitude to produce drift severity |
| **Ingress API** | Infrastructure-layer entry point for all inbound DCM requests; sets ingress block; routes to Consumer/Provider/Admin API surfaces |
| **Provider Catalog Item** | Provider-specific instantiation of a Resource Type Specification; what consumers actually request; distinct from the Resource Type Specification itself |
| **Recovery Policy** | Formal DCM policy type mapping trigger conditions (DISPATCH_TIMEOUT, PARTIAL_REALIZATION, etc.) to response actions; same authoring model as Gating Policy/Validation/Transformation |
| **recovery_posture** | Fifth Policy Group concern_type governing failure and ambiguity response; binds a recovery profile group to the deployment |
| **DRIFT_RECONCILE** | Recovery action: schedule discovery; let drift detection resolve actual state |
| **DISCARD_AND_REQUEUE** | Recovery action: best-effort cleanup; new request cycle created immediately |
| **NOTIFY_AND_WAIT** | Recovery action: notify human; wait for explicit decision up to declared deadline |
| **TIMEOUT_PENDING** | Infrastructure Resource Entity state: dispatch timeout fired; recovery policy evaluating |
| **LATE_REALIZATION_PENDING** | Entity state: provider responded after timeout; NOTIFY_AND_WAIT recovery decision pending |
| **INDETERMINATE_REALIZATION** | Entity state: state ambiguous; drift detection resolving |
| **COMPENSATION_FAILED** | Entity state: composite service rollback itself failed; orphan detection active |
| **orphan_candidate** | Resource discovered at provider with no corresponding Realized State record; surfaced to platform admin for human resolution |
| **Discovery Scheduler** | DCM control plane component maintaining priority queue of discovery requests; dispatches to provider discovery endpoints |
| **recovery-automated-reconciliation** | Built-in recovery profile: trust drift detection; accept late responses; appropriate for dev/standard |
| **recovery-notify-and-wait** | Built-in recovery profile: notify human; never act automatically; appropriate for prod/fsi/sovereign |
| **notification service** | Ninth DCM provider type; translates unified notification envelope to delivery channel; handles delivery, retry, dead letter, and delivery confirmation callbacks |
| **Notification Router** | DCM control plane component that resolves notification audiences and routes envelopes to notification services |
| **audience resolution** | Deriving notification recipients by traversing the entity relationship graph from the changed entity at event time |
| **notification_uuid** | Idempotency key on notification envelopes; notification services use this to deduplicate on retry |
| **audience_role** | owner / stakeholder / approver / observer — why this actor is in the notification audience |
| **stakeholder_reason** | Notification envelope field explaining which relationship caused the actor to be in the stakeholder audience |
| **Tier 1 / Tier 2 / Tier 3 notifications** | Mandatory system (non-suppressable) / Tenant defaults / Actor subscriptions — three subscription tiers that compose |
| **NOT-001 through NOT-008** | Notification model system policies |
| **write-once snapshot store** | Realized Store implementation model: each record is a complete immutable entity state snapshot; no event replay; direct point-in-time lookup; supersession chain links snapshots |
| **corresponding_requested_state_uuid** | Mandatory non-nullable field on every Realized State snapshot; traces every Realized State change to an authorized request |
| **Provider Update Notification** | Formal API for providers to report authorized state changes; DCM evaluates via Policy Engine; approved → new Requested State + Realized State; rejected → drift event |
| **notification_uuid** | Idempotency key on Provider Update Notifications; safe to resend on provider crash |
| **pre-authorized update** | Category of provider update pre-approved by Gating policy; processed automatically without per-change human review |
| **Whole Allocation** | Ownership pattern: consumer owns the entire resource entity outright in their Tenant; no pool involved |
| **Allocation** | Ownership pattern: pool yields independently-owned sub-resources; consumer owns their allocation; AllocationRecord relationship links to pool |
| **Shareable** | Ownership pattern: one resource, multiple stakeholders; consumers hold stakes (relationships) only; no consumer owns any portion |
| **AllocationRecord** | Cross-tenant relationship from an allocation entity back to its source pool entity |
| **stake_strength** | Relationship property on shareable resource attachments: required (blocks decommission) / preferred / optional |
| **PENDING_REVIEW** | Formal Infrastructure Resource Entity lifecycle state for conflicts requiring human resolution (sovereignty, cross-tenant auth revocation, ownership transfer conflicts) |
| **Consumer API** | DCM REST API for consumers: catalog browsing, request submission, resource management, audit trail access |
| **Consumer Request Status** | Lifecycle: ACKNOWLEDGED → ASSEMBLING → AWAITING_APPROVAL → APPROVED → DISPATCHED → PROVISIONING → COMPLETED/FAILED/CANCELLED |
| **01-entity-types.md** | Entity type taxonomy: Infrastructure Resource, Composite Resource, Process Resource; sub-types and invariants |
| **04-examples.md** | Worked examples: VM end-to-end, IP allocation, VLAN sharing, brownfield ingestion, drift remediation; Git repo structure |
| **04b-ownership-sharing-allocation.md** | Authoritative ownership model: whole allocation, allocation, shareable; policies OWN-001 through OWN-008 |
| **federation routing** | Hub DCM applies placement engine logic at the DCM instance level; Regional DCMs are DCM Provider instances; sovereignty is a hard pre-filter; same tie-breaking hierarchy as provider selection |
| **independent_with_overlap** | Certificate rotation model: old cert valid P30D after new cert issued; allows peers to update trust stores without coordinated downtime |
| **alert_and_hold** | Federated drift detection response when peer DCM is unavailable: do not assume drift; hold state; escalate to platform admin after PT24H |
| **AUDIT_STORE_UNAVAILABLE** | Gap record inserted in Audit Store hash chain after recovery from Audit Store failure; timestamps the exact outage window; makes gap explicit and auditable |
| **confidence aggregation** | Per-entity endpoint computing overall confidence band (= lowest field band); identifies contested and stale fields; computed on demand never stored |
| **explicit_no_filter** | Composite group declaration suppressing the no member_type filter linting warning; confirms broad targeting is intentional |
| **certified profile** | DCM profile carrying formal third-party certification metadata (HIPAA assessor, FedRAMP JAB, PCI QSA); promoted to Tier 1; applies to artifact not deployment |
| **POLICY_PROVIDER_ELEVATED** | Audit action recorded when a External Policy Evaluator's mode level is elevated; always produced regardless of profile |
| **tier_certifications** | Certification metadata on Resource Type Specs or profiles from recognized certifying bodies; filter criterion, not structural tier boundary |
| **tier_3_to_tier_2_promotion** | PR-based pathway for organizations to promote internal Tier 3 Resource Types to Verified Community (Tier 2); requires production deployment, OSS license, named maintainer, migration path |
| **independent operation mode** | Resource Type Registry state when upstream registry is permanently unavailable; existing types continue; new community type adoption requires governance decision |
| **SCIM 2.0** | System for Cross-domain Identity Management; optional Auth Provider capability for automated actor provisioning from enterprise IdPs; provisions actors and group memberships; roles not SCIM-provisioned |
| **step-up MFA** | Additional MFA challenge at sensitive operations within an already-authenticated session; declared per operation by policy; step-up token TTL PT10M |
| **actor.type** | Audit record field: human / service_account / system; enables filtering between human-initiated and automated lifecycle operations in queries and dashboards |
| **system_actor** | Audit record block on system-initiated records: identifies DCM component, trigger event, and authorizing policy UUID |
| **Merkle root proof** | Federation-level audit integrity mechanism: Hub DCM computes Merkle root of all Regional DCM chain tips daily; any chain break detectable against stored root |
| **per-instance hash chain** | Each DCM instance (Hub/Regional/Sovereign) maintains its own independent hash chain; not merged cross-instance; cross-referenced via correlation_id |
| **AUTH-012 through AUTH-015** | Auth Provider gap policies: SCIM provisioning, failover handling, two-tier MFA, pluggable user store |
| **AUD-014 through AUD-017** | Universal Audit gap policies: hash chain verification modes, Commit Log capacity, system-initiated records, distributed hash chains |
| **Hub DCM** | Central/global DCM instance; authoritative registry origin; governance authority; replaces "Shore" terminology |
| **Regional DCM** | Distributed regional DCM instance; manages resources in its region; caches from Hub DCM; replaces "Ship" terminology |
| **Sovereign DCM** | Air-gapped or compliance-isolated DCM instance; local static caches from signed bundles; replaces "Enclave" terminology |
| **native_passthrough** | Sanctioned field for provider-specific data that cannot be expressed in the unified model; always audit-logged; opaque mode blocked in fsi/sovereign |
| **BULK_PROMOTE** | Audit action for bulk entity promotion; single audit record with full member list; requires preview + approval in prod+ profiles |
| **CACHE policies** | CACHE-001 through CACHE-004 — cache placement, sync, authoritativeness, consistency |
| **DATA-001** | Policy: core data model does not embed technology-specific data; native_passthrough sanctioned with governance |
| **RED-011 through RED-015** | Deployment redundancy gap policies: bootstrap verification, K8s upgrades, runtime support, hardware specs, self-hosted drift |
| **ING-012 through ING-015** | Ingestion gap policies: signal priority configurable, bulk promotion, max sources, catalog promotion |
| **rehydration_history** | Immutable record on entity of all rehydration events: trigger, from/to provider, from/to provider-side IDs, actor, state refs |
| **rehydration_lease** | Exclusive time-bounded lock per entity during rehydration; prevents concurrent rehydrations; TTL prevents orphans |
| **min_auth_level** | Entity rehydration constraint declaring minimum actor authentication level required; profile governs enforcement |
| **allow_delegated_rehydration** | Entity flag permitting DCM service accounts to rehydrate automatically; requires platform admin authorization audit trail |
| **REHYDRATION_BLOCKED** | Audit event recorded when a concurrent rehydration attempt is rejected due to active lease |
| **hybrid retention mode** | Discovered State retention: minimum window + retain until drift resolved + hard maximum ceiling |
| **rolling_window retention** | Discovered State retention: keep last N days regardless of drift status |
| **override: allow/constrained/immutable** | Layer field metadata declaring override intent; enforced by Request Payload Processor at Step 3; immutable prevents lower-authority overrides only; Gating Policy may additionally lock |
| **constraint_visibility** | Policy-governed disclosure level for constrained fields: full (constraint+bounds+reason+suggestions), summary (bounds only), hidden (silently enforced) |
| **editable** | Resource Type Spec field declaration: can this field be modified post-realization via a targeted delta update (true) or only via reprovisioning (false) |
| **edit_constraints** | Bounds declared on editable fields: range, list, enum; validated at update time; same constraint types as assembly-time constraints |
| **requires_restart** | Editable field flag indicating whether a provider restart action is needed to apply the update |
| **targeted delta** | Update mechanism for editable fields: applies only changed fields to Realized State; does NOT re-run the layer assembly chain |
| **non_editable_reason** | Human-readable explanation on non-editable fields explaining why reprovisioning is required to change them |
| **confidence_descriptor** | Primary confidence data model: authority_level (from registration), corroboration (from ingestion), source_trust (from trust system), last_updated_at (from push) — stored fields |
| **freshness** | Derived confidence field computed at query time from (now - last_updated_at) vs thresholds: high (<1h), medium (<1d), low (<7d), stale (>7d) |
| **corroboration** | Confidence descriptor field: confirmed (2+ sources agree), single_source, contested (sources disagree) |
| **source_trust** | Confidence descriptor field maintained by trust scoring system: verified (score ≥80), degraded (60-79), suspended (<60) |
| **OBS-001** | Policy: DCM publishes curated Observability Event Stream via Message Bus; policy-filtered; raw metrics opt-in; does not replace audit records |
| **AUD-013** | Policy: Audit and Observability are definitively separate components — opposite trade-offs; cannot be combined |
| **group_subclass** | Advisory label on a DCMGroup — no system behavior; used for organization-specific semantics (e.g., cost_center, business_unit) |
| **composite group** | DCMGroup with group_class: composite — permits cross-type membership (resources, policies, layers, groups) |
| **federation group** | DCMGroup with group_class: federation — peer association of tenant_boundary groups; enables shared policies and consolidated reporting |
| **nested Tenant** | A tenant_boundary group with parent_group_uuid pointing to another tenant_boundary group |
| **federated Tenant** | A tenant_boundary group that is a member of a federation group |
| **former_group_membership** | Permanent provenance record retained by a member after group destruction or membership expiry |
| **group_destruction_record** | Permanent Audit Store record of a destroyed group including its full member list at destruction time |
| **member_type_filter** | Policy targeting declaration narrowing scope within a composite group to specific member types |
| **most_restrictive_wins** | Governance inheritance principle for nested Tenants — most restrictive policy at any level in the hierarchy applies |
| **Nested Tenant** | tenant_boundary group with parent_group_uuid — child maintains isolation; parent has governance overlay and cost rollup |
| **GRP-INV** | Universal group structural invariants — non-overridable regardless of enforcement_model or Profile |
| **Universal Audit Record** | Uniform audit record produced by every DCM component for every change — date/time, who, what, action |
| **Composite Actor Chain** | The who in an audit record — immediate actor + authorized_by human chain + originating request/policy |
| **Action Vocabulary** | Closed set of audit record action values — free text rejected at write time (AUD-007) |
| **Reference-Based Retention** | Audit records retained while any referenced entity is live — not fixed time schedule |
| **Write-Ahead Log (WAL)** | Local audit delivery buffer — change + audit record written atomically; Audit Store delivery async with retry; WAL cleared after Audit Store confirms |
| **Hash Chain** | Per-entity tamper-evident chain: record_hash + previous_record_hash; chain breaks detectable and trigger security alerts |
| **Mode 4 External Policy Evaluator** | Black box query-enrichment policy provider — DCM sends query, external system evaluates and/or enriches, returns structured result; logic is opaque to DCM |
| **Black Box Query-Enrichment** | Mode 4 operation where an external system simultaneously evaluates request data and injects enrichment fields into the payload |
| **audit_token** | Provider-issued reference in Mode 4 responses enabling cross-system audit correlation between DCM audit trail and provider's internal logs |
| **data_request_spec** | Mode 4 registration declaration of which fields the provider is authorized to receive, with classification ceiling per field |
| **Policy Naturalization** | Translation of external policy schemas (OSCAL, XCCDF, CIS JSON) into DCM policy format — Mode 3 External Policy Evaluator mechanism |
| **Policy Group** | Cohesive versioned collection of policies addressing a single identifiable concern — the unit of policy reuse |
| **Policy Profile** | Complete DCM configuration for a specific use case — composed of Policy Groups |
| **External Policy Evaluator** | Fifth DCM provider type — external authoritative source supplying policies into DCM |
| **concern_type** | Policy Group classification: technology, compliance, sovereignty, business, operational, security |
| **minimal profile** | Least restrictive built-in profile — advisory enforcement, auto-tenant, home lab / evaluation |
| **sovereign profile** | Most restrictive built-in profile — hard tenancy, deny_all cross-tenant, maximum sovereignty |
| **Lifecycle Constraint Enforcer** | DCM control plane component monitoring realized entities against time constraints |
| **cross_tenant_authorization** | Explicit authorization record for cross-tenant relationship — specifies who, what, when, where |
| **explicit_only** | Default cross-tenant hard tenancy setting — ALL cross-tenant requires explicit authorization |
| **PENDING_REVIEW** | Entity state during paused rehydration tenancy conflict — awaiting resolution |
| **Policy Gap Record** | Audit record for fields absent from reserve query with no applicable policy — records implicit_approval |
| **Shared Resource** | An entity within a single Tenant with active relationships from multiple parent entities; governed by sharing_model and reference counting |
| **sharing_model** | Entity-level declaration of shareability, active_relationship_count, and on_last_relationship_released behavior |
| **active_relationship_count** | DCM-maintained count of active constituent/operational relationships on a shared resource |
| **save_overrides_destroy** | The lifecycle action hierarchy rule: retain > notify > suspend > detach > cascade > destroy; most conservative action always wins |
| **lifecycle_conflict_record** | Audit record created when multiple lifecycle action recommendations differ; carries severity, resolved action, and resolution rule |
| **deferred_destruction_record** | Audit record created when a destructive lifecycle action is deferred because active_relationship_count is above minimum |
| **Ingestion Model** | Unified DCM mechanism for bringing entities outside lifecycle control into DCM governance — covers V1 migration, brownfield discovery, and manual import |
| **Ingestion Record** | Provenance record on every ingested entity — source, confidence, assignment method, enrichment history, promotion timestamp |
| **`__transitional__` Tenant** | System-managed holding Tenant for unassigned ingested entities — cannot be deleted, renamed, or used for new provisioning |
| **Ingestion Confidence** | `high | medium | low` — quality signal for auto-assignment; reflects how reliable the Tenant assignment is |
| **Brownfield** | Existing infrastructure not yet under DCM lifecycle management — brought in via brownfield ingestion |
| **V1 Migration** | Migration of pre-Tenant DCM V1 entities to V2 using the ingestion model |
| **INGESTED state** | First ingestion lifecycle state — entity in DCM, minimal metadata, Tenant may be __transitional__ |
| **ENRICHING state** | Second ingestion lifecycle state — Tenant assigned, metadata and relationships being completed |
| **PROMOTED state** | Final ingestion lifecycle state — all requirements met, DCM assumes full lifecycle ownership |
| **DCM Event Type** | A versioned, typed event that DCM can emit — follows universal versioning model |
| **Event Type Registry** | DCM-maintained registry of standard event types — extensible like the Resource Type Registry |
| **Webhook Registration** | Declaration by a consumer, provider, or external system of which DCM events they want to receive and where |
| **Discussion Topics** | Living document (DISCUSSION-TOPICS.md) capturing unresolved design decisions and topics requiring further discussion |
| **Override Preference** | Level 2 simple override declaration — single `override: allow|constrained|immutable` on a field |
| **Override Matrix** | Level 3 per-actor permission matrix for fields requiring nuanced governance |
| **Field Override Control** | Graduated mechanism (Levels 1-3) governing who can change what field, under what conditions |
| **Structural Layer Rules** | Non-configurable rules enforced by the Request Payload Processor — layer immutability, precedence order, chain integrity |
| **Business Override Rules** | Configurable override control rules enforced by the Policy Engine via override metadata |
| **Trusted Grant** | Explicit expansion of override permissions issued by a higher-authority actor to a specific entity UUID |
| **Actor Registry** | Extensible registry of override actors — built-in (policy.global, consumer_request, sre_override, etc.) plus custom actors |
| **Basis for Value** | Field metadata documenting why a particular value was set |
| **Baseline Value** | Field metadata recording the original default value before any override was applied |
| **Entity Relationship** | Universal bidirectional relationship between any two entities — internal or external |
| **Entity Relationship Graph** | Complete traversable graph of all entity relationships in DCM |
| **Relationship UUID** | UUID identifying a specific relationship — same on both sides of the bidirectional record |
| **Relationship Type** | Fixed vocabulary describing the nature of a relationship (requires, depends_on, contains, references, peer, manages) |
| **Relationship Role** | Semantic label describing the function a related entity serves (compute, storage, networking, business_unit, etc.) |
| **Relationship Nature** | Structural character of a relationship — constituent, operational, or informational |
| **Lifecycle Policy** | Declares what happens to an entity when its related entity changes state |
| **Bundled Declaration Expansion** | Processor mechanism expanding bundled fields (e.g., storage in VM request) into first-class entities and relationships |
| **Information Provider** | DCM provider type serving authoritative external data DCM references but does not own |
| **External Entity Reference** | Stable pointer record DCM uses to reference data in an external system |
| **Standard Data** | DCM-defined fields on an information type — used for lookups and operational decisions |
| **Extended Data** | Organization-defined fields added to an information type — carried in payload but not used for DCM core operations |
| **Information Type** | Registry entry for a category of external data (Business.BusinessUnit, Identity.Person, etc.) |
| **Stable External Key** | The external system's UUID used as the primary lookup anchor for an external entity reference |
| **Trust But Verify** | DCM's approach to external references — trusts external data is correct, verifies references remain valid |
| **DCM Operator Interface Specification** | The formal technical contract defining how Kubernetes operators integrate with DCM as Service Providers |
| **DCM Operator SDK** | Go library implementing the Operator Interface Specification — enables Level 1 conformance in one day |
| **Conformance Level** | The level of DCM integration an operator implements — Level 1 (basic), Level 2 (standard), Level 3 (full) |
| **Naturalization (Kubernetes)** | Translating DCM Requested State into a Kubernetes CR |
| **Denaturalization (Kubernetes)** | Translating Kubernetes CR status back into DCM Realized State format |
| **Unsanctioned Change** | A change to a DCM-managed CR that did not originate from a DCM request — detected via missing DCM request annotation |
| **Operator Adapter** | A component implementing the DCM Service Provider API on behalf of an operator that cannot be modified directly |
| **CNCF Sandbox** | The initial CNCF maturity level — target for initial DCM project submission |
| **Conformance Test Suite** | The test suite that validates an operator's implementation against the DCM Operator Interface Specification |
| **Intent State** | The immutable record of a consumer's original declaration — captured before any assembly or policy evaluation |
| **Requested State** | The fully assembled, policy-processed, provider-ready payload — the authoritative record of what DCM instructed a provider to build |
| **Realized State** | The provider-confirmed record of what was actually built — append-only event stream keyed by entity UUID |
| **Discovered State** | What DCM observes actually existing through active discovery — ground truth for drift detection |
| **Data Store Contract** | The interface specification through which DCM defines persistence requirements — implemented by PostgreSQL |
| **GitOps Store** | PostgreSQL store contract for Intent and Requested State — branch, PR, merge, CI/CD hook semantics |
| **Event Stream Store** | PostgreSQL store contract for Realized and Discovered State — append-only, entity-keyed, replayable |
| **Search Index** | Queryable projection of GitOps stores — explicitly non-authoritative, rebuilt from Git on demand |
| **Provider-Portable Rehydration** | Rehydration with provider selection re-evaluated through current placement policies |
| **Faithful Rehydration** | Rehydration honoring the original provider selection from the source record |
| **Pinned Policy Version** | Rehydration using policies as of a specific historical timestamp — requires elevated authorization |
| **Audit Component** | Separate DCM component aggregating provenance events from all stores — compliance-grade, long-retention |
| **Observability Store** | Time-series metrics, traces, and logs — operational, not compliance-grade |
| **Third Rail** | Direct API ingress path — bypasses PR workflow, never bypasses governance |
| **Layer Domain** | Organizational and architectural home of a layer — system, platform, tenant, service, provider |
| **Layer Handle** | Human-readable stable identifier for a layer — format: domain/layer_type/name |
| **Priority Schema** | Hierarchical dotted-notation priority system for deterministic layer conflict resolution |
| **Priority Value** | Numeric dotted-notation priority — higher value wins; no ceiling, infinitely insertable in both directions |
| **Immutable Ceiling** | `immutable_ceiling: absolute` — explicit declaration that a field lock cannot be overridden by any future higher-priority policy; the nuclear option for true non-negotiables |
| **Priority Label** | Semantic context for a priority value — human-readable, does not affect ordering |
| **Reference Priority Taxonomy** | DCM's advisory priority category ranges — not enforced, organizations adopt/adapt/ignore |
| **Artifact Metadata** | Universal metadata block on every DCM artifact — identity, ownership, creation, modification history, contact |
| **created_by** | Artifact metadata field — the audit record of who physically submitted the artifact |
| **owned_by** | Artifact metadata field — the accountability record of who is responsible and receives notifications |
| **created_via** | Artifact metadata field — ingestion path: pr, api, migration, system |
| **Proposed Shadow Execution** | Policy artifact in proposed status executing against real traffic — output captured, never applied |
| **Proposed Evaluation Record** | Shadow output record for a proposed policy — what it would have done on a real request |
| **Validation Dashboard** | Review interface showing aggregate shadow output for proposed policies before activation |

---

## SECTION 56 — COMMUNITY QUESTIONS RESOLVED

All 21 previously open community/implementation questions are now resolved. Key decisions:

### Kubernetes Compatibility (5 resolved)
- **Namespace → Tenant mapping:** brownfield ingestion model handles pre-existing namespaces; each namespace maps to one DCM Tenant; resources without ownership go to `__transitional__` Tenant
- **Cluster boundary:** DCM manages across multiple clusters; `Platform.KubernetesCluster` is a resource type DCM provisions, not DCM's own boundary; Tenant is the boundary
- **Admission webhooks vs Policy Engine:** complementary layers — admission webhooks enforce cluster-native policy, DCM Policy Engine enforces DCM request policy; defense in depth, not duplication
- **Kubernetes Information Provider:** separately deployed Information Provider following the unified base contract; no built-in providers in DCM
- **Managed K8s (EKS/GKE/AKS):** managed clusters register as Service Providers of `Platform.ManagedKubernetesCluster`; DCM manages workloads within, not the control plane

### CNCF Strategy (5 resolved)
- **Submission scope:** Operator Interface Specification as a CNCF specification project first; DCM project submission follows after Level 2 reference implementation
- **Named adopters:** minimum 2 named evaluators + 1 FSI design partner before submission; project team action item
- **TOC sponsor:** target App Delivery TAG and Runtime TAG; SIG engagement surfaces sponsors; project team action item
- **SIG engagement timing:** BEFORE Sandbox submission; SIG App Delivery and SIG Cluster Lifecycle; Cluster API overlap must be addressed pre-submission
- **Level 2 timeline:** scope is now formally defined (dispatch/cancel/discover + realized state + governance matrix + health check); team estimates timeline against defined scope

### Operator Interface Specification (6 resolved)
- **CNCF submission:** specification project (not sandbox project requiring implementation); SIG engagement first
- **Conformance certification:** self-certified via automated test suite (low friction gate) + optional DCM Verified badge via project review
- **Cluster-scoped resources — two models:** (A) **Cluster as a catalog item (example):** When a Service Provider offers Kubernetes clusters as a resource type, a Tenant that owns a provisioned cluster entity owns all cluster-scoped resources within it — the cluster entity is the ownership boundary; (B) **Shared cluster infrastructure:** cluster-scoped resources governing shared multi-tenant cluster infrastructure belong to `__platform__` Tenant. Note: Cluster-as-a-Service is an example Service Provider implementation, not a DCM architectural feature — DCM treats the cluster as any other resource entity
- **Non-Go frameworks:** spec is language-agnostic; Go SDK is reference implementation; community Java/Python SDKs encouraged; not maintained by DCM project in v1
- **Cluster API as an example Service Provider:** A CAPI-based operator can register as a Service Provider for a `Platform.KubernetesCluster` resource type — this is an example of what DCM's Provider model enables, not a special architectural feature. DCM has no built-in knowledge of Kubernetes; a CAPI Service Provider is structurally identical to any other Service Provider. Once provisioned, the cluster entity can optionally register as a nested Service Provider for workload resources (the Composite Service pattern — composing compute + network + storage + DNS + credentials)
- **Level 0:** exists — label-based passive discovery, no operator code changes; DCM discovers and tracks but does not control; lowest adoption friction

### Operator SDK (5 resolved)
- **Language-agnostic adapter:** not needed — spec is language-agnostic; Go SDK is reference only
- **DCM unavailability:** local durable queue (SQLite); replay on reconnect; DEGRADED mode on overflow with QUEUE_OVERFLOW audit + alert; never drop silently
- **Dynamic field resolution:** Information Provider reference in field mapping; DCM resolves during layer assembly; keeps logic in Policy Engine with full provenance
- **Testing framework:** mock DCM test harness ships as first-class SDK component; configurable failure/delay injection; required for Level 2 conformance
- **Prometheus metrics:** mandatory; 6 standard metrics (registration_status, event_delivery_total, event_delivery_duration, queue_depth, dispatch_duration, discovery_cycle_duration); required for Level 2 conformance

**Zero remaining unresolved architectural questions.** Remaining open items are project team action items (named adopters, TOC sponsor, KubeVirt timeline).

---

## SECTION 57 — PREVIOUSLY OPEN QUESTIONS (NOW CLOSED)

These items are explicitly unresolved. Do not make assumptions about them — flag them and ask for guidance.

| # | Question | Area |
|---|----------|------|
| 1 | Where should data caches live? (Hub DCM, Regional DCM, Sovereign DCM, all?) | Data Model |
| 2 | Should cache synchronization be push, pull, or both? | Data Model |
| 3 | Which cache is authoritative when caches diverge? | Data Model |
| 4 | What mechanism maintains consistency across distributed caches? | Data Model |
| 5 | Should the data model allow embedded target-technology-specific data bundles? | Data Model |
| 6 | How are the four states represented physically? | Data Model |
| 7 | Performance impact of field-level provenance at scale — optimization strategies? | Data Model |
| 8 | Should provenance metadata be inline or in a linked provenance document? | Data Model |
| 9 | What is the governance model for proposing new Resource Types to the registry? | Catalog |
| 10 | Should the registry support a formal review/approval workflow? | Catalog |
| 11 | What is the minimum sunset period for deprecated definitions? | Catalog |
| 12 | Should version constraints in requests be strictly enforced or advisory? | Catalog |
| 13 | How are conflicts resolved when multiple providers satisfy all narrowing criteria equally? | Catalog |
| 14 | Should the registry be distributed or centralized? Sovereignty implications? | Catalog |
| 15 | Trust validation mechanism for provider certification | Providers |
| 16 | Audit vs. Observability — are these truly separate components? | Control Plane |
| 17 | Message Bus — should it be exposed as consumer ingress or egress only? | Control Plane |
| 18 | Gating Policy vs. Validation policy distinction — needs better examples | Policy Engine |
| 19 | How are conflicting Service Layers at the same precedence level resolved? | Data Layers | ✅ Resolved — priority schema + ingestion conflict detection |
| 20 | Should Core Layers be ordered within their precedence level? | Data Layers | ✅ Resolved — priority schema provides deterministic ordering |
| 21 | Can a consumer explicitly exclude a layer from their request? | Data Layers |
| 22 | How are Service Layers registered and versioned relative to their Service Provider registration version? | Data Layers |
| 23 | Should assembly support conditional layer inclusion — a layer only applied if a specific field value is present? | Data Layers |
| 24 | How does the layer chain interact with service dependencies — does each dependent service get its own chain? | Data Layers |
| 25 | For Hybrid Transfer — what is the maximum number of ownership transfers allowed? | Entities |
| 26 | For Whole Allocation of bare metal — how is indivisibility enforced at the provider level? | Entities |
| 27 | Should capacity confidence ratings trigger automatic actions (e.g., LOW triggers Mode 1 query)? | Entities |
| 28 | For Process Resources — should there be a maximum execution time before DCM escalates? | Entities |
| 29 | How does SUSPENDED state interact with cost analysis — is a suspended Entity still billable? | Entities |
| 30 | How are dependency graphs versioned relative to catalog item versions? | Dependencies |
| 31 | Should the dependency graph be stored as a separate entity or embedded in the request payload? | Dependencies |
| 32 | How are cross-tenant dependencies handled? | Dependencies | ✅ Resolved — governed by REL-010/011/012; DEP-001/002/003 for dependency graph specifics; explicit_only default; cross_tenant_authorization required |
| 33 | Should there be a maximum dependency graph depth? | Dependencies |
| 34 | How does the dependency graph interact with the Composite Service model? | Dependencies |
| 35 | Should DCM maintain a registry of well-known custom group types? | Grouping |
| 36 | How does group membership interact with sovereignty — can a group span sovereignty boundaries? | Grouping |
| 37 | When a Tenant is decommissioned, what happens to its resources and group memberships? | Grouping |
| 38 | Should Resource Groups support time-bounded membership? | Grouping |
| 39 | How are group-level policies inherited by nested child groups — opt-in or opt-out? | Grouping |
| 40 | Webhook registration model — Consumer API, Provider Registration, or dedicated Webhook API? | Webhooks |
| 41 | Full DCM event taxonomy and whether it should be a versioned registry | Webhooks |
| 42 | Webhook payload format — full state payload vs reference + event type | Webhooks |
| 43 | Webhook authentication model for outbound calls | Webhooks |
| 44 | Webhook retry and reliability obligations | Webhooks |
| 45 | Webhook ordering guarantees | Webhooks |
| 46 | Relationship between webhooks and the Message Bus | Webhooks |
| 47 | Should provider webhook support be mandatory in the Provider Contract? | Webhooks |
| 48 | Tenant vs platform-level webhook scoping | Webhooks |
| 49 | Should webhook registrations declare which payload schema version they expect? | Webhooks |
| 50 | Should override_preference be declarable in layer definitions as a hint to the Policy Engine? | Override Control |
| 51 | When immutable is set by a Global policy, can a higher-priority Global policy still override it? | Override Control | ✅ Resolved — execution order makes default immutable effectively absolute; immutable_ceiling: absolute provides explicit forward-looking protection |
| 52 | Should constraint_schema on a constrained field be visible to consumers in the Service Catalog UI? | Override Control |
| 53 | Enhancement gaps: storage/networking bundling vs. dependency model — V1 simplification or new concept needed? | Enhancements |
| 54 | Enhancement gaps: selected_provider as policy output vs. placement component concern | Enhancements | ✅ Resolved — Placement Engine is a distinct named component; nine-step assembly; reserve query; placement loop with policy phases; policy_gap_record for implicit approval; post-placement policy pass |
| 55 | Enhancement gaps: migration path from V1 (no Tenant) to Tenant-mandatory | Enhancements | ✅ Resolved — unified ingestion model; __transitional__ Tenant; three-step ingest/enrich/promote; ING-001 through ING-007; also covers brownfield ingestion |
| 56 | Enhancement gaps: should editable field concept from Catalog Item Schema be incorporated into Resource Type Spec? | Enhancements |
| 57 | How are relationship conflicts resolved — two policies declare different lifecycle policies for the same relationship? | Entity Relationships | ✅ Resolved — standard Policy Engine authority hierarchy; lifecycle policy fields are just fields; no special case; REL-008 and REL-009 |
| 58 | Should relationship roles be validated against the role registry at request time, or is validation advisory? | Entity Relationships |
| 59 | How does the relationship graph interact with multi-tenant scenarios — can a relationship cross Tenant boundaries? | Entity Relationships | ✅ Resolved — nature governs; constituent never; operational with dual auth; informational unless deny_all; REL-010/011/012; allocated resource model |
| 60 | Should there be a maximum relationship graph depth? | Entity Relationships |
| 61 | How are shared entities represented — an entity required by multiple parents? | Entity Relationships | ✅ Resolved — sharing_model with active_relationship_count; save_overrides_destroy hierarchy; lifecycle_conflict_record; REL-015 through REL-019 |
| 62 | How are conflicting Information Provider push events handled — two providers claim authority for the same record? | Information Providers |
| 63 | Should Information Providers support write-back — DCM updating external records via the provider? | Information Providers |
| 64 | How is the extended schema versioned when a provider adds or removes extended fields? | Information Providers |
| 65 | Should DCM maintain a registry of well-known Information Providers to simplify onboarding? | Information Providers |
| 66 | How does Information Provider verification interact with air-gapped environments? | Information Providers |
| 67 | Should CNCF submission be for DCM as a whole or for the Operator Interface Specification as a standalone standard? | CNCF Strategy |
| 68 | Which FSI consortium members will be named as public adopters in the CNCF submission? | CNCF Strategy |
| 69 | How does the Namespace-to-Tenant mapping work for clusters with pre-existing namespaces? | Kubernetes Compatibility |
| 70 | How does DCM interact with Kubernetes admission webhooks — duplicate or complement Policy Engine? | Kubernetes Compatibility |
| 71 | Should the Kubernetes Information Provider be a built-in DCM component or separately deployed? | Kubernetes Compatibility |
| 72 | How does DCM interact with managed Kubernetes services (EKS, GKE, AKS) where cluster management is outside user control? | Kubernetes Compatibility |
| 73 | Should the SDK support non-Go operator frameworks via a language-agnostic REST adapter? | SDK Design |
| 74 | How should the SDK handle DCM endpoint unavailability — queue events locally or drop? | SDK Reliability |
| 75 | Should the entity UUID be preserved or regenerated on rehydration? | Four States |
| 76 | For pinned policy version rehydration — what is the minimum authorization level? | Four States |
| 77 | How are concurrent rehydration requests for the same entity handled? | Four States |
| 78 | Should the Discovered Store retain full history or only a configurable window? | Four States |
| 79 | Git repository structure for Intent and Requested stores — deferred pending Q54 | Storage |
| 80 | Should data stores support multi-region replication as a declared capability? | Storage |
| 81 | How are store failures handled — failover, queuing, or rejection? | Storage |
| 82 | Should the Search Index be a separate store contract or bundled with the primary store? | Storage |
| 83 | Should the Audit Store be a specialized store contract or a general event stream? | Audit |
| 84 | Should DCM provide a default observability dashboard or only the telemetry? | Observability |
| 85 | Should the background conflict validation job run on schedule or be event-triggered? | Data Layers |
| 86 | What is the minimum validation review period for a proposed policy before activation? | Policy Engine |
| 87 | Should the proposed shadow evaluation record be stored in the Audit Store or a separate validation store? | Storage |
| 88 | Should organizations be able to define their own artifact status extensions beyond the five standard statuses? | Artifact Metadata |

---

## SECTION 58 — EXAMPLES AND USE CASES (dcm-examples.md)

### Orchestration Examples (8 scenarios)

**1.1 Basic request lifecycle** — submit → layers_assembled (Gating Policy + Transformation fire) → placement (6-step) → dispatch → realized. Shows named workflow + dynamic policies composing on same events.

**1.2 Human approval gate** — Gating Policy with `requires_approval: true` flag inserts AWAITING_APPROVAL step without modifying named workflow. Manager approves via API → pipeline resumes.

**1.3 Policy-gated hard block** — Gating Policy denies unsupported OS. Consumer receives clear error with policy_uuid and suggestion. No requires_approval flag → terminal FAILED.

**1.4 Composite Service** — VM + IP + DNS + LoadBalancer delivered as one catalog item. Dependency-ordered execution (parallel where no deps). DNS fails (partial delivery) → DEGRADED state. Recovery: NOTIFY_AND_WAIT. Consumer chooses: accept degraded or trigger DNS retry.

**1.5 Drift detection + remediation** — Discovery finds memory_gb changed (unsanctioned). Drift: significant + unsanctioned → critical. Policy: ESCALATE. Consumer submits REVERT → new request cycle → next discovery clean.

**1.6 Dispatch timeout + late response** — Provider silent for PT30M → TIMEOUT_PENDING → Recovery: NOTIFY_AND_WAIT (prod profile). Provider responds at T+45M → LATE_RESPONSE_RECEIVED. Consumer chooses DISCARD_AND_REQUEUE.

**1.7 Federation-routed request** — Local providers at capacity. Placement queries Hub DCM (Peer DCM provider). Hub routes to Regional DCM B. Governance Matrix checked at each hop. Realized State flows back chain. entity_uuid preserved.

**1.8 Brownfield ingestion** — Discovery finds unmanaged VM. Orchestration Flow Policy: discover → INGEST → ENRICH (CMDB query) → await operator → PROMOTE to tenant. Drift detection activated post-promotion.

### Provider Examples (4 scenarios)

**2.1 Service Provider dispatch cycle** — Full payload showing DCM unified format → naturalize to OpenStack Nova → execute → denaturalize back. Shows provenance on injected fields (monitoring_endpoint from policy).

**2.2 Information Provider enrichment** — CMDB query during layer assembly. Response with confidence descriptor. Fields injected with source_type: information_provider and source_uuid.

**2.3 External Policy Evaluator Mode 3 (OPA sidecar)** — Exact OPA HTTP API call format, input document structure, response parsing.

**2.4 notification service delivery** — VLAN decommission event. Audience: owner (NetworkOps) + 2 stakeholders (required stakes) + 1 observer (optional stake). Per-actor envelopes with stakeholder_reason field. Slack message format.

### Consumer API Examples (2 scenarios)

**3.1 Complete request lifecycle** — catalog browse → describe (see constraints) → submit → poll status sequence → get realized resource with confidence scores.

**3.2 Provider update approval** — Provider submits auto-scale notification → REQUIRES_CONSUMER_APPROVAL → consumer reviews pending notifications → approve → new Realized State.

### Admin API Examples (2 scenarios)

**4.1 Provider registration review** — List pending registrations (with validation results) → approve with review notes.

**4.2 Orphan resolution** — List orphan candidates → investigate → adopt_into_dcm → entity promoted to full lifecycle.

### Registration Flow Example (1 scenario)

**5.1 Complete provider onboarding** — Admin issues registration token → provider submits registration payload (mTLS + token) → 8 automated validation checks shown → PENDING_APPROVAL → admin reviews → ACTIVE. Full capability declaration structure for Service Provider.

---

## SECTION 59 — CAPABILITIES MATRIX (167 capabilities, 26 domains)

The DCM Capabilities Matrix contains 167 capabilities across 26 domains. Each capability row specifies what consumers, service providers, and platform admins can do, along with dependencies.

**Current domain count: 26**
IAM, CAT, REQ, PRV, LCM, DRF, POL, LAY, INF, ING, AUD, OBS, STO, FED, GOV, ACC, ZTS, GMX, DRC, FCM, SMX, MPX, CPX, DPO, ATM, EVT, VER (26 domain prefixes; see taxonomy for full names)

**Recent additions (docs 29–34):**
- SMX (Scoring Model, doc 29): risk scoring, approval routing, signal weights, governance matrix
- CMP (Composite Service, doc 30): composite service definition, constituent dispatch via dependency graph
- CPX (credential management service, doc 31): credential lifecycle, rotation, revocation, profile-governed security
- ATM (Authority Tier, doc 32): dynamic ordered tier list, custom tiers, degradation gate, impact detection
- EVT (Event Catalog, doc 33): 82 event types, base envelope, payload schemas, EVT-001–007
- VER (API Versioning, doc 34): breaking change definition, deprecation lifecycle, version discovery

**SMX-008 hard constraint:** auto_approve_below ≤ 50 in ALL profiles
**ATM-002 hard constraint:** auto tier max_score ≤ 50 in ALL profiles
**CPX-001 absolute:** credential values NEVER in DCM stores in ANY profile
**EVT-007:** audit.* critical events are non-suppressable


## SECTION 60 — DOCUMENTATION STRUCTURE

DCM documentation follows a hierarchical structure:

```
dcm-docs/ (internal working docs)
├── README.md
├── DCM-AI-PROMPT.md                       # This file
├── DISCUSSION-TOPICS.md
├── data-model/                            # → website: /docs/architecture/data-model/
│   ├── 00-context-and-purpose.md          ✅
│   ├── 02-four-states.md                  ✅
│   ├── 03-layering-and-versioning.md      ✅
│   ├── 05-resource-type-hierarchy.md      ✅
│   ├── 06-resource-service-entities.md    ✅
│   ├── 07-service-dependencies.md         ✅
│   ├── 08-resource-grouping.md            ✅
│   ├── 09-entity-relationships.md         ✅
│   ├── 10-information-providers.md        ✅
│   ├── 11-storage-providers.md            ✅
│   └── 12-audit-provenance-observability.md ✅
└── specifications/                        # → website: /docs/architecture/specifications/
    ├── dcm-operator-interface-spec.md     ✅
    ├── 11-kubernetes-compatibility.md     ✅
    ├── dcm-operator-sdk-api.md            ✅
    └── cncf-strategy.md                  ✅

Website structure (Hugo / Hextra):
content/
├── _index.md                              # Homepage — 4 bottom cards
└── docs/
    ├── _index.md                          # Docs index
    ├── architecture/
    │   ├── _index.md                      # Architecture section — 3 cards
    │   ├── overview.md                    # High Level Design ✅
    │   ├── data-model/
    │   │   ├── _index.md                  # Data Model section — 11 cards
    │   │   └── (11 data model docs)       ✅
    │   └── specifications/
    │       ├── _index.md                  # Specifications section — 4 cards
    │       └── (4 specification docs)     ✅
    └── enhancements/
        ├── _index.md
        └── (existing enhancement stubs — unchanged)
```

---

## SECTION 61 — SCORING MODEL (doc 29)

### Governing Principle
Questions of fact use boolean gates. Questions of degree use scoring. Secondary test: "Can a regulator accept 'the score was below threshold' as a complete explanation?" If not — boolean.

### Gating Policy enforcement_class (required field)
- `compliance` — boolean deny gate. Default and fail-safe if omitted. Used for: regulatory requirements (PHI→BAA, sovereign data), security hard requirements, anything where score-around creates legal liability.
- `operational` — contributes `risk_score_contribution` (weight 1–100) to request risk score. Used for: cost ceilings, size limits, quota pressure, off-hours context, business rule preferences.

### Validation output_class (required field)
- `structural` — boolean pass/fail. Default and fail-safe. Missing required fields, type errors, broken references.
- `advisory` — completeness score contribution + warning list. Never blocks. Recommended fields absent, unusual values, low confidence.

### The Five Scoring Signals (aggregate → request_risk_score 0–100)
1. **Operational Gating Policy score** (weight: 0.45 standard) — sum of risk_score_contribution from all fired operational Gating Policies, capped at 100
2. **Completeness score** (weight: 0.15) — sum of advisory Validation contributions
3. **Actor risk history score** (weight: 0.20) — decay-weighted (λ=0.1, half-life 7 days) history of actor's previous request outcomes; events: validation_failure(5), gating_deny(10), compliance_deny(20), policy_override(8), drift_caused(15), forced_decommission(12)
4. **Quota pressure score** (weight: 0.10) — zero below 75% utilization; max(0, (util - 0.75) / 0.25) × 100 above
5. **Provider accreditation richness** (weight: 0.10, inverse) — weighted portfolio sum; higher richness = lower provider risk contribution

### Profile-Governed Thresholds → Approval Routing
auto_approve (<threshold) | reviewed | verified | authorized (>threshold)
Default per profile: minimal(<45), dev(<40), standard(<25), prod(<15), fsi(<10), sovereign(<5)
SMX-008 applies to ALL profiles including minimal — auto_approve_below may never exceed 50
**SMX-008: auto_approve_below may never exceed 50 in any profile, including minimal.** minimal achieves higher effective auto-approval through lower signal weights, not higher thresholds.
Signal weights must sum to 1.00 (validated at profile activation).

### Profile Enforcement Class Overrides
Profiles can promote operational→compliance or demote compliance→operational (non-regulatory only).
SMX-003: policies with `regulatory_mandate: true` cannot be demoted. Set by platform admins. Audited.
Threshold and override changes take effect immediately. Score Records are immutable — no retroactive changes.

### Pipeline Sequence (doc 29, Section 8)
1. Evaluate all policies
2. Compliance Gating Policy fires → HALT (boolean deny, no score)
3. Structural Validation fails → HALT (boolean fail, no score)
4. Governance Matrix DENY → HALT (always boolean, never scored — SMX-004)
5. Collect operational Gating Policy contributions → Signal 1
6. Collect advisory Validation contributions → Signal 2
7. Fetch actor risk history → Signal 3
8. Calculate quota pressure → Signal 4
9. Calculate provider accreditation richness → Signal 5
10. Aggregate with profile weights → request_risk_score
11. Apply profile thresholds → routing_decision
12. Write Score Record to Audit Store (SMX-010: required for every scored request)
13. Route: auto_approve | queue_for_review | queue_dual | queue_committee

### What Is NEVER Scored
Governance Matrix (SMX-004) · authentication · authorization · five-check boundary enforcement · lifecycle state transitions · unsanctioned change flag · TTL expiry · request status states

### Score Exposure
Consumer: risk_score, routing_decision, score_drivers (top 3, human-readable), advisory_warnings
Platform admin: full Score Record — all signal breakdowns, weights, actor risk history detail
Actor risk history never exposed to other consumers (privacy — SMX-007)

### Score Record (immutable, Audit Store)
score_record_uuid, request_uuid, entity_uuid, request_risk_score, routing_decision, routing_threshold_applied, profile_uuid, signal_breakdown (per signal: score, weight, weighted_contribution, fired_policies)

### New API Endpoints
Consumer: risk_score + advisory_warnings on POST /api/v1/requests response and GET status
Admin: GET/PATCH /api/v1/admin/profiles/{name}/scoring · POST overrides · GET/POST /actors/{uuid}/risk-history · GET /scoring/audit
Flow GUI: GET /flow/api/v1/graph/scoring-overlay · POST /flow/api/v1/simulate/score · Threshold slider in Profile Management view · Score breakdown panel in Simulation

### SMX-001–010 System Policies
SMX-001: Gating Policy must declare enforcement_class (compliance default). SMX-002: Validation must declare output_class (structural default). SMX-003: regulatory_mandate:true = no profile demotion. SMX-004: Governance Matrix always boolean. SMX-005: signal weights must sum to 1.00. SMX-006: Score Records immutable. SMX-007: actor risk history not exposed to other consumers. SMX-008: auto_approve_below ≤ 50. SMX-009: scoring_weight 1–100; aggregate capped at 100 before weighting. SMX-010: Score Record required for every scored request.

### Capabilities
SMX-001 through SMX-008 in Capabilities Matrix Domain 21. Total: 167 capabilities, 26 domains.

---

## SECTION 62 — COMPOSITE SERVICE COMPOSITION MODEL (doc 30)

### What a Composite Service Is

A Composite Service is a **catalog-level registration** that declares a composite payload — multiple constituent resource types, with declared dependencies and delivery requirements — fulfillable as a single request. There is no separate "meta provider" type. A Service Provider that registers a Composite Service simply declares the composition definition and fulfills the constituents flagged `provided_by: self`; everything else is DCM's standard machinery. The 5 provider types are: service_provider, information_provider, auth_provider, peer_dcm, process_provider.

### Key Principle
The Composite Service registration declares the dependency graph. DCM executes it. Parallelism emerges from the graph — constituents with no unresolved dependencies dispatch concurrently. The registering provider does not manage sequencing, external placement, failure handling, or compensation.

### provided_by (critical field on each constituent)
- `self` — registering provider handles this constituent via standard Services API (naturalize/execute/denaturalize — same as any Service Provider)
- `external` — DCM places with best available provider via Placement Engine (all sovereignty/accreditation/trust checks apply)
- `<provider_uuid>` — DCM dispatches to specific named provider

### depends_on → Execution Order
Each constituent declares `depends_on: [component_id, ...]`. DCM reads this graph and dispatches in order — no dependencies first, then those whose dependencies are OPERATIONAL. Parallelism within a round emerges from the graph. The registering provider does NOT manage this.

### required_for_delivery
- `required` — failure triggers Recovery Policy; unrealized constituents cancelled
- `partial` — failure noted; composite continues; composite status may be DEGRADED
- `optional` — failure noted; execution continues unaffected

### Division of Responsibility (authoritative — see doc 30 Section 4)
**DCM:** catalog, layer assembly, policy/scoring, external placement (Placement Engine), dependency-ordered dispatch, failure handling (Recovery Policy), compensation (dependency-reverse decommission), composite Realized State assembly, drift detection, audit, lifecycle.
**Registering provider:** declares Composite Service composition; executes `self` constituents as standard Service Provider; implements standard decommission for `self` constituents.

### Composite Entity Four States
- **Intent:** Composite request stored as-is; no constituent expansion
- **Requested:** DCM expands using Composite Service definition; Placement Engine resolves `external` providers; constituent blocks have component_id, provided_by, depends_on, required_for_delivery
- **Realized:** DCM assembles from all constituent realized payloads; composite_status; synthesized composite_fields
- **Discovered:** Per-constituent providers (transparent) or aggregated via the registering provider's standard discovery surface (opaque/selective)

### Composite Status — determined by DCM
- `OPERATIONAL` — all required constituents OPERATIONAL
- `DEGRADED` — required OPERATIONAL; partial(s) failed; accepted if profile permits
- `FAILED` — required constituent(s) failed → Recovery Policy → compensation in dependency-reverse order

### Composition Visibility
- `opaque` — top-level entity only; aggregated discovery via the registering provider's standard discovery surface
- `transparent` — all constituents as DCM entities; UUIDs = deterministic(parent_uuid + component_id); per-constituent drift detection
- `selective` — declared sub-set as DCM entities

### Rehydration
Primary use case for dependency graph declaration. DCM sequences rehydration from `depends_on` graph in same order as provisioning. `external` constituents re-placed by Placement Engine. `self` constituents return to the same registering provider.

### Scoring
Operational Gating Policies fire on the composite payload (not per-constituent). Signal 5 (accreditation richness) = lowest richness score among required-constituent providers.

### Nested Composite Services
Max depth 3 enforced by DCM at placement. A Composite Service used as a constituent of another Composite Service has no awareness it is a constituent — receives and responds with standard payloads.

### CMP-001–CMP-008 System Policies
CMP-001: self constituents use standard Services API. CMP-002: DCM derives ordering from depends_on. CMP-003: parallelism from graph, not the registering provider. CMP-004: composite status determined by DCM. CMP-005: Recovery Policy governs failure/compensation. CMP-006: external placement by Placement Engine only. CMP-007: transparent UUIDs are deterministic. CMP-008: max nesting depth 3 enforced at placement.

### Capabilities: CMP-001–CMP-007 (Domain 22 — 141 total across 23 domains)

## SECTION 63 — CREDENTIAL PROVIDER MODEL (doc 31)

### Two Credential Categories
1. **DCM Interaction Credentials** — short-lived (PT15M–PT1H profile-governed), scoped to specific operation+entity+provider. Issued before every provider dispatch. Implements ZTS-002. Never stored beyond use.
2. **Consumer-Facing Resource Credentials** — SSH keys, API keys, kubeconfigs, service account tokens, database passwords, x509 certificates. Issued as part of resource realization; delivered via Consumer API.

### CPX-001 (most important): Values NEVER in DCM stores
Credential values are never written to GitOps stores, Realized State Store, or Audit Store. DCM stores only metadata (UUID, type, scope, expiry, status). Values held by credential management service; retrieved via authenticated `value_retrieval_endpoint`.

### Credential Record Fields
credential_uuid, credential_type, status (active/rotating/revoked/expired), issued_at, valid_until, issued_to (actor/entity/component/provider UUID), scope (operations[], resource_types[], tenant_uuid), non_transferable:true, bound_to_ip (fsi/sovereign), value_retrieval_endpoint, value_retrieval_auth, rotation_of (parent UUID if rotation), service_provider_uuid, entity_uuid

### Issuance Flows
- **Resource credential:** after VM/resource realized → DCM sub-request to credential management service → metadata stored in Realized State → consumer retrieves value via authenticated endpoint
- **Interaction credential:** before each provider dispatch → credential management service issues scoped cred → included in dispatch → expires PT15M regardless; new cred issued for each interaction
- **Bootstrap:** special mechanism before credential management service is registered; see doc 17

### Rotation Protocol
Trigger types: pre_expiry (default), scheduled, security_event, actor_request, provider_initiated. Standard flow: issue new cred → transition window (both valid) → revoke old at window end → notify consumer. Window: P1D consumer creds; PT5M dcm_interaction; P7D x509. Emergency rotation (security_event): NO transition window — old revoked immediately; fastest-channel delivery of new.

### Revocation Model
Revocation Triggers: actor_deprovisioned, entity_decommissioned, security_event, provider_deregistered, actor_request, ttl_expired. Propagation: credential record → status:revoked → publish credential.revoked to Message Bus → all components refresh revocation cache within SLA (PT5M standard; PT1M fsi/sovereign) → credential management service invalidates stored value within SLA.

### Use-Time Validation (CPX-002 enforcement)
Providers must validate at use time (not just receipt): check revocation cache, verify valid_until, verify operation within scope, verify IP binding. Reject with 403 if any check fails. Cache refresh: ≤ PT1M standard; ≤ PT30S fsi/sovereign.

### CPX-006: Actor Deprovisioning
Triggers immediate revocation of ALL credentials issued to actor. Revocation events published to Message Bus BEFORE deprovisioning acknowledged.
CPX-007: Entity decommissioning triggers revocation of all entity-scoped credentials before decommission confirmed. Decommission that cannot revoke enters COMPENSATION_IN_PROGRESS.

### Consumer API Endpoints
GET /api/v1/resources/{entity_uuid}/credentials — list credential metadata
GET /api/v1/credentials/{uuid}/value — retrieve value (step_up_mfa if required); every retrieval audited with retrieval_uuid
POST /api/v1/credentials/{uuid}/rotate — request rotation; returns old/new UUIDs + transition_window_ends

### credential management service API Contract
POST {issue_endpoint} · POST {rotate_endpoint} · DELETE {revoke_endpoint}/{uuid} · POST {validate_endpoint} (use-time check) · GET {list_endpoint}?entity_uuid=

### Profile-Governed Credential Configuration (doc 31 Section 12)
credential_profile block controls: permitted_credential_types (homelab: api_key/x509/ssh; sovereign: hsm_backed_key only) · max_lifetime per credential type per profile · scheduled_rotation_required (ALL profiles: true; minimal/dev allow manual trigger and P365D/P180D max intervals) · min_transition_window (minimal: PT0S; standard+: P1D) · value_retrieval_auth_required (minimal: bearer_token; prod: step_up_mfa; sovereign: mtls) · audit_every_retrieval (minimal: false; standard+: true) · idle_detection_threshold (minimal: P30D; dev: P14D; standard: P7D; prod: P3D; fsi: P1D; sovereign: PT12H — NEVER null) · ip_binding_required (minimal-prod: false; fsi/sovereign: true) · fips_140_level_required (minimal: 0; fsi: Level 2; sovereign: Level 3) · approved_algorithms (minimal: forbidden_algorithms list [MD5,SHA-1,DES,3DES,RSA<2048]; standard: Ed25519/ECDSA-P-384; fsi: FIPS-only; sovereign: HSM-generated only) · revocation_check_frequency (minimal: PT5M; fsi: PT30S; sovereign: PT15S) · revocation_sla (minimal: PT10M; sovereign: PT30S)

### Compliance Domain Overlays (additive, never relaxing)
hipaa: audit_every_retrieval:true, idle_detection:P7D, max rotation api_key:P90D
pci_dss: max_rotation_interval:P90D (mandatory — req 8.3.9), min_password_complexity:12+4-classes
fedramp_moderate: fips_level:1 · fedramp_high: fips_level:2, ip_binding:true · dod_il4: fips:2, ip_binding:true

### AAL Mapping (NIST 800-63B)
minimal/dev=AAL1 · standard=AAL2 (MFA for sensitive types) · prod=AAL2 (MFA all) · fsi=AAL2+ (hardware MFA, FIPS L2) · sovereign=AAL3 (hardware-bound, FIPS L3, tamper evidence)

### New Fields on Credential Record
algorithm (Ed25519/ECDSA-P-384/RSA-4096/HS256/etc.) · key_usage [authentication|signing|encryption] · retrieved_count_threshold (hours; idle alert threshold)

### CPX-001–CPX-012 System Policies
CPX-001: values never in DCM stores. CPX-002: every provider interaction must present scoped credential. CPX-003: revocation propagation within declared SLA. CPX-004: emergency rotation has no transition window. CPX-005: every value retrieval audited. CPX-006: actor deprovisioning revokes all actor credentials. CPX-007: entity decommission blocks on credential revocation. CPX-008: fsi/sovereign credentials must be IP-bound or hardware-attested.

### Capabilities: CPX-001–CPX-007 (Domain 23 — 148 total across 23 domains)

---

## SECTION 64 — AUTHORITY TIER MODEL (doc 32 — 32-authority-tier-model.md)

> **Full specification:** [32-authority-tier-model.md](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) — ordered tier list, custom tier contribution, dynamic threshold format, impact detection pipeline, ATM-001–ATM-012.

### Core Model
Authority tiers are a **named, ordered list**. Names are stable references; numeric weight is derived from list position at evaluation time — never hardcoded. Organizations can insert custom tiers between existing ones without breaking any existing name references.

### Default Tier List (ordered)
```
auto → reviewed → verified → authorized
```
Position determines weight: auto=1, reviewed=2, verified=3, authorized=4.
If org inserts `compliance_reviewed` after `verified`: auto=1, reviewed=2, verified=3, compliance_reviewed=4, authorized=5.
All existing references to `authorized` still resolve correctly.

### decision_gravity (stable severity vocabulary)
- `none` → auto (automated; no human judgment)
- `routine` → reviewed (standard authority; one qualified reviewer)
- `elevated` → verified (elevated authority; separation of duties; two distinct reviewers)
- `critical` → authorized (highest authority weight; DCMGroup + quorum required)

decision_gravity is stable and position-independent. Custom tiers must declare consistent gravity.

### Dynamic Threshold Format
Profile thresholds are a named-tier list, NOT fixed column keys:
```yaml
approval_routing:
  - { tier: auto,       max_score: 24 }   # ATM-002: never exceed 50
  - { tier: reviewed,   max_score: 59 }
  - { tier: verified,   max_score: 79 }
  - { tier: authorized, max_score: 100 }
```
Custom tiers insert into this list. Existing tier names and ranges shift only for the affected range.

### Custom Tiers
Contributed via standard contribution pipeline; require `verified` tier approval (ATM-004). Must declare decision_gravity consistent with position (ATM-003). Cannot alter dcm_gate semantics of existing DCM system tiers (ATM-005).

### Authorized Tier (dcmgroup_required: true)
Requires a declared DCMGroup and quorum threshold. Organization defines: group composition (CTO, CISO, board, single delegate — any structure), how members deliberate, what external tools they use. DCM enforces that N members of the declared DCMGroup recorded decisions via Admin API. Organization provides everything else.

### Tier Registry Change Impact Detection (doc 32 Section 7)
When tier registry changes, DCM computes a **tier_impact_diff** — a structured comparison of proposed vs current ordered list — before activation:
- **SECURITY_DEGRADATION**: tier's gravity or position decreased → blocks activation until reviewed and accepted (ATM-009)
- **BROKEN_REFERENCE**: tier name removed but still referenced → blocks activation until resolved (ATM-010)
- **PROFILE_GAP**: new tier inserted but profile threshold list not updated → warning, does not block (ATM-012)
- **SECURITY_UPGRADE / STALE_WEIGHT**: informational, does not block

Degradation review gate: each SECURITY_DEGRADATION must be accepted via `POST /api/v1/admin/tier-registry/{change_uuid}/accept-degradation` by a `verified` or `authorized` tier reviewer before activation.

Impact report (ATM-011) stored in Audit Store for every registry change, at proposal and at activation.

Admin API: POST /api/v1/admin/tier-registry/changes (propose) · GET .../impact (report) · POST .../accept-degradation · POST .../activate

### ATM-001–ATM-012 System Policies
ATM-001: tiers identified by name; weight derived from position. ATM-002: auto tier max_score ≤ 50. ATM-003: custom gravity consistent with position. ATM-004: custom tiers require verified-tier approval. ATM-005: custom tiers cannot change existing tier dcm_gate semantics. ATM-006: dcmgroup_required tiers must have DCMGroup declared before use. ATM-007: four gravity values are DCM vocabulary (org cannot add gravity values). ATM-008: approval records store weight at creation time for point-in-time audit.

### Federation Tier Resolution
Peer DCM instances may have different custom tier lists. Resolution strategy: `gravity_match` — match by decision_gravity, not tier name. Unknown peer tiers escalate to their declared gravity level.

---

## SECTION 65 — EVENT CATALOG (doc 33 — 33-event-catalog.md)

> **Full specification:** [33-event-catalog.md](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md) — authoritative source for all 82 DCM event types, payload schemas, urgency levels, EVT-001–EVT-007 system policies.

### Base Envelope (all events share this)
event_uuid (idempotency key — EVT-002: consumers must treat duplicates as already-processed) · event_type · event_schema_version · timestamp (from Commit Log — authoritative) · dcm_version · dcm_instance_uuid · subject (entity_uuid, entity_type, entity_handle, tenant_uuid, actor_uuid) · urgency (critical/high/medium/low/info) · payload (event-specific) · links (self, audit_record)

### Event Domains (82 total across 26 domains)
request.* (14): submitted → intent_captured → layers_assembled → policies_evaluated → requires_approval → approved → placement_complete → dispatched → compound_assembled → dependencies_resolved → realized/failed/gating_rejected/cancelled
entity.* (13): realized, state_changed, modified, ttl_warning, ttl_expired, suspended, resumed, decommissioning, decommissioned, decommission_deferred, ownership_transferred, pending_review, expired
drift.* (4): detected, severity_escalated, resolved, escalated
provider.* (5): registered, deregistered, healthy, unhealthy, degraded
provider_update.* (5): submitted, requires_approval, approved, rejected, auto_approved
rehydration.* (5): started, paused, interrupted, completed, blocked
policy.* (4): activated, deactivated, evaluated, shadow_result
credential.* (4): rotating, revoked, idle, expired
approval.* (4): decision_recorded, quorum_reached, window_expiring, expired
tier_registry.* (4): proposed, impact_assessed, degradation_detected, activated
audit.* (3): chain_integrity_alert, chain_break, forward_failed
dependency.* (2): state_changed + stakeholder.resource_decommissioning
allocation.* (2): pool_capacity_low, released
ingestion.* (3): transitional_created, enriched, promotion_approved
governance.* (3): catalog_item_deprecated, profile_changed, policy_trust_elevated
security.*/sovereignty.*/federation.*/auth.*: unsanctioned_provider_write, sovereignty.violation, sovereignty.migration_required, federation.tunnel_degraded, auth.provider_failover

### Urgency Levels
critical (push + page if configured) · high (push) · medium (standard) · low (standard) · info (batch/webhook only)
critical + audit.* events: NON-SUPPRESSABLE — EVT-005 and EVT-007

### Schema Versioning
event_schema_version increments ONLY on breaking changes (removing fields, changing types/semantics). Adding optional fields is NOT breaking. EVT-004.

### Non-Standard Events
Providers/extensions may publish non-standard events using reverse-DNS prefix (e.g. com.acme.custom_event). EVT-006.

### EVT-001–EVT-007 System Policies
EVT-001: all events must include base envelope. EVT-002: event_uuid is idempotency key. EVT-003: timestamp from Commit Log. EVT-004: schema version increments on breaking changes only. EVT-005: critical urgency → push delivery. EVT-006: non-standard events use reverse-DNS prefix. EVT-007: audit.* critical events are non-suppressable.

---

## SECTION 66 — API VERSIONING STRATEGY (doc 34 — 34-api-versioning-strategy.md)

> **Full specification:** [34-api-versioning-strategy.md](../control-plane/api-versioning.md) — breaking change definition, deprecation lifecycle, version discovery, sunset behavior, VER-001–VER-009.

### Versioning Model
URL path versioning: `/api/v1/`, `/api/v2/`, etc. Version is per-API surface (Consumer, Admin, Provider/OIS, Flow GUI) — NOT per-endpoint. All endpoints in a surface share the same major version. Non-breaking changes do not change the URL.

### Breaking Change Definition (VER-002)
**Breaking:** removing fields/endpoints, changing field types, changing URL structure, tightening validation, changing HTTP status semantics, removing enum values, changing HTTP method.
**NOT breaking:** adding optional fields, adding endpoints, expanding enums, relaxing validation, adding error codes, performance changes. When in doubt → treat as breaking.

### Deprecation Lifecycle
Profile-governed support windows:
- minimal: 90 days notice, 180 days deprecated support
- standard: 180 days / 365 days
- prod: 365 days / 730 days (2 years)
- fsi: 18 months / 3 years
- sovereign: 2 years / 4 years

Deprecated versions: fully functional until sunset. Bugs fixed; features not backported. `Deprecation`, `Sunset`, `Link` headers on every response (RFC 8594/RFC 9745). VER-003.

### Version Discovery
`GET /.well-known/dcm-api-versions` — lists all API surfaces, current/supported/deprecated versions, base URLs, changelog URLs.
Per-version changelog: `GET /api/v{N}/changelog`
Machine-readable migration guide (required by VER-008): `GET /api/v{N}/migration-guide`

### Sunset Behavior
After sunset: `410 Gone` with successor_version, migration_guide_url, sunset_date.
Three events: `governance.api_version_deprecated`, `governance.api_version_sunset_warning` (30 days before), `governance.api_version_sunset`.

### Version Negotiation
URL path is authoritative. Optional `DCM-API-Version: v1` header for explicit pinning (returns 406 if sunsetted).
`/api/latest/` alias exists but NOT for production — pin to specific version.

### Preview Endpoints
`/api/v{N}/preview/` — no stability commitment; may change without major version increment; not for production automation.

### OIS (Provider API) Versioning
Providers declare `ois_version` in capability registration. DCM maintains dispatch compatibility with all supported OIS versions during deprecation window. VER-009.

### VER-001–VER-009 System Policies
VER-001: URL path versioning only. VER-002: breaking change definition. VER-003: deprecation headers required. VER-004: deprecated versions fully functional until sunset. VER-005: support windows profile-governed. VER-006: latest alias not for production. VER-007: preview endpoints not stable. VER-008: migration guide required per new major version. VER-009: OIS dispatch compatibility during deprecation window.

---

## SECTION 67 — SESSION TOKEN REVOCATION (doc 35 — 35-session-revocation.md)

> **Full specification:** [35-session-revocation.md](../control-plane/session-revocation.md) — session lifecycle, revocation triggers, revocation registry, token introspection, AUTH-016–AUTH-022.

### Session Record
session_uuid · actor_uuid · auth_provider_uuid · auth_method · mfa_verified · created_at · expires_at · status (active/refreshing/revoked/expired) · revocation_reason · revoked_at · revoked_by

### Session Store
Fast-queryable operational store (not GitOps-backed). Redis/Postgres (standard+) or in-memory (minimal/dev). Profile-governed TTLs: minimal PT8H → sovereign PT15M. Concurrent session limits: unlimited(minimal) → 1(sovereign).

### Revocation Triggers
actor_logout (single session, self) · actor_logout_all (all sessions, self) · actor_deprovisioned (all sessions — parallel with CPX-006) · actor_suspended · security_event (emergency, no grace period) · concurrent_limit_exceeded (oldest session evicted) · auth_provider_deregistered · credential_compromised · admin_forced_logout

### Session Revocation Registry
Fast-queryable store of revoked-but-not-yet-expired session UUIDs. ALL components that accept bearer tokens MUST check this on every request. Cache age: PT5M(minimal) → no cache(sovereign). AUTH-018.

### Actor Deprovisioning (AUTH-016)
Session revocation and credential revocation (CPX-006) are PARALLEL operations. Deprovisioning not acknowledged until BOTH complete. Neither blocks the other.

### Emergency Revocation (AUTH-019)
security_event trigger: immediate, no grace period. auth.security_session_revoked event: urgency critical, non-suppressable. SLA: PT30S(standard) → PT5S(sovereign).

### Token Introspection
POST /api/v1/auth/introspect (RFC 7662). Returns {active: true/false, session_uuid, actor_uuid, expires_at, mfa_verified, roles}. Requires introspection scope. AUTH-020.

### Consumer API Session Endpoints
DELETE /api/v1/auth/session (logout single) · DELETE /api/v1/auth/sessions (logout all) · GET /api/v1/auth/sessions (list active) · DELETE /api/v1/auth/sessions/{uuid} (revoke specific)
Admin: POST /api/v1/admin/actors/{uuid}/revoke-sessions (force revoke, requires reason)

### AUTH-016–AUTH-022 System Policies
AUTH-016: deprovisioning fires session + credential revocation in parallel. AUTH-017: revocation SLA PT5M(minimal) → PT5S(sovereign). AUTH-018: all components check revocation registry. AUTH-019: emergency revocation = critical urgency, non-suppressable. AUTH-020: introspection endpoint requires introspection scope. AUTH-021: oldest session evicted at concurrent limit. AUTH-022: refresh tokens invalidated when parent session revoked.

---

## SECTION 68 — INTERNAL COMPONENT AUTHENTICATION (doc 36 — 36-internal-component-auth.md)

> **Full specification:** [36-internal-component-auth.md](../control-plane/internal-component-auth.md) — component identity, Internal CA, bootstrap tokens, communication graph, ICOM-001–ICOM-009.

### Two-Layer Enforcement
Mesh layer (Istio/mTLS): prevents impersonation at transport. Application layer (DCM): enforces what each component is permitted to do. BOTH required. Network position grants zero trust — internal calls receive same boundary checks as external.

### Component Identity
Each component has: component_uuid · component_type · mTLS certificate (from Internal CA) · service_account_uuid · allowed_operations · allowed_targets list.

### Component Types
api_gateway · policy_engine · placement_engine · request_orchestrator · scoring_engine · drift_reconciler · lifecycle_enforcer · notification_router · audit_store · session_store · message_bus · service_provider_proxy

### Communication Graph (enforced, not advisory)
Consumer/Admin → API Gateway → Request Orchestrator → Policy Engine / Placement Engine / Scoring Engine
All components → Session Store (revocation check) + credential management service Proxy (interaction creds)
ICOM-004: components may ONLY call declared allowed_targets. Unauthorized source → 403 + ICOM_UNAUTHORIZED_SOURCE audit (urgency: high). ICOM-003.

### Every Internal Call Requires
1. mTLS certificate from Internal CA (transport identity)
2. ZTS-002 scoped interaction credential (operation authorization) — scoped to specific operation + target component, valid PT5M max
3. Correlation ID

### Internal CA
Per-deployment CA. Certificates: ECDSA-P-384, P90D lifetime, auto-renew P14D before expiry. CRL + OCSP endpoints. Internal CA root cert installed in ALL component trust stores at deploy time. ICOM-006, ICOM-009.

### Bootstrap Protocol (ICOM-007)
New component has no cert yet. Platform admin generates one-time bootstrap token (PT1H max). Component uses bootstrap token → gets first cert from Internal CA → token invalidated immediately. Kubernetes: token injected as Secret, deleted by component after cert acquisition. Unused tokens auto-expire at PT1H.

### Certificate Compromise (ICOM-008)
Compromised cert → added to Internal CA CRL immediately → all components refresh CRL within profile SLA (PT15S sovereign, PT1M standard) → ICOM_CERT_COMPROMISED audit (urgency: critical) → platform admin notified → new cert issued.

### ICOM-001–ICOM-009 System Policies
ICOM-001: mTLS required ALL internal calls, no exceptions. ICOM-002: interaction credential required IN ADDITION to mTLS. ICOM-003: unauthorized source → 403 + high-urgency audit. ICOM-004: components only call declared allowed_targets. ICOM-005: all internal calls audited. ICOM-006: component certs max P90D, Internal CA only. ICOM-007: bootstrap tokens one-time-use PT1H max. ICOM-008: compromised certs → CRL immediately. ICOM-009: Internal CA root in all trust stores; no external CA certs for internal comms.

---

## SECTION 69 — SCHEDULED AND DEFERRED REQUESTS (doc 37 — 37-scheduled-requests.md)

> **Full specification:** [37-scheduled-requests.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/scheduled-requests.md) — scheduling model, dual policy evaluation, maintenance windows, Request Scheduler component, SCH-001–SCH-006.

### Scheduling Model
schedule.dispatch: immediate (default) | at (specific time with not_before/not_after) | window (maintenance window reference) | recurring (cron expression). Added as optional field on POST /api/v1/requests — no new submission endpoint.

### SCHEDULED Status
Request enters SCHEDULED status in Intent State after passing declaration-time Gating Policy. Visible in GET /api/v1/requests?status=SCHEDULED. Cancellable via DELETE /api/v1/requests/{uuid} before dispatch. request.scheduled event (info urgency).

### Dual Policy Evaluation (SCH-001)
Gating Policy runs at declaration time (fail fast) AND at dispatch time (validate against current state). Dispatch-time rejection → FAILED with schedule_policy_rejection (SCH-003). Data, quotas, policies may all change between declaration and dispatch.

### Deadline Enforcement (SCH-005)
not_after: if passed without dispatch → FAILED with schedule_deadline_missed. No retry. request.failed event (medium urgency).

### Maintenance Windows
Reusable named recurrence artifacts. Platform admin creates; consumers reference by window_uuid in schedule. Admin: POST /api/v1/admin/maintenance-windows. Consumer: GET /api/v1/maintenance-windows.

### New Events (added to doc 33)
request.scheduled · request.schedule_cancelled · request.schedule_deadline_missed (17 total in request.* domain)

---

## SECTION 70 — REQUEST DEPENDENCY GRAPH (doc 38 — 38-request-dependency-graph.md)

> **Full specification:** [38-request-dependency-graph.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/request-dependency-graph.md) — consumer-declared cross-request ordering, field injection, PENDING_DEPENDENCY status, RDG-001–RDG-006.

### What This Is
Consumer-declared ordering of INDEPENDENT requests. Distinct from: type-level deps (doc 07, resolved automatically) and Composite Service composition (doc 30, platform team defines). Use when no Composite Service exists for the composite deployment.

### Request Dependency Group
POST /api/v1/request-groups — submit multiple requests with depends_on declarations using local refs. Response includes group_uuid and per-request entity_uuids. GET /api/v1/request-groups/{uuid} for group status. DELETE to cancel.

### PENDING_DEPENDENCY Status
Dependent request waits in PENDING_DEPENDENCY until dependency reaches wait_for: acknowledged|approved|dispatched|realized (default: realized). Quota counted at group submission, not at dispatch. RDG-004.

### Field Injection
inject_fields: pass realized output fields from dependency (e.g. IP address) into dependent request's fields automatically at dispatch time. Subject to Transformation policies. RDG-003.

### Failure Handling
on_failure: cancel_remaining (dependents → CANCELLED with dependency_failed) | continue (only directly-dependent requests fail). Group timeout: all non-terminal → FAILED with group_timeout. RDG-005.

### Constraints (RDG-001, RDG-002, RDG-006)
Circular deps rejected at submission (422) — must be a DAG. Max 50 requests per group. Request may belong to at most ONE group (409 on second add).

### New Events (added to doc 33)
request.pending_dependency · request.dependency_met · request.group_completed · request.group_failed

---

## SECTION 71 — DCM SELF-HEALTH ENDPOINTS (doc 39 — 39-dcm-self-health.md)

> **Full specification:** [39-dcm-self-health.md](../control-plane/self-health.md) — liveness, readiness, component health, Prometheus metrics, HLT-001–HLT-006.

### Three Endpoints
GET /livez (liveness — PT5S max, no external calls, unauthenticated, Kubernetes restarts on fail) ·
GET /readyz (readiness — checks Session Store + Audit Store + Policy Engine + Message Bus + Auth Provider, unauthenticated, Kubernetes removes from LB on fail) ·
GET /api/v1/admin/health (per-component detail, admin auth required)

### Liveness (/livez)
{status: pass|fail}. Fail if: deadlocked, Internal CA unreachable. Responds within PT5S. No DB reads, no external calls. HLT-002.

### Readiness (/readyz)
{status: pass|warn|fail, checks: {session_store, audit_store, policy_engine, message_bus, auth_provider}}. Fail if ANY core dependency unreachable. Warn if optional component degraded. Used for startup probe (failureThreshold 30 × 10s = 300s startup allowance). HLT-003, HLT-006.

### Component Health (/api/v1/admin/health)
Full per-component status: api_gateway, request_orchestrator, policy_engine, placement_engine, scoring_engine, request_scheduler, drift_reconciler, lifecycle_enforcer, discovery_scheduler, notification_router, session_store, audit_store, message_bus, internal_ca. Plus providers{registered/healthy/degraded/unhealthy} and auth_providers summary.

### Prometheus Metrics (/metrics)
dcm_requests_total · dcm_request_duration_seconds · dcm_requests_pending_dependency_total · dcm_policy_evaluations_total · dcm_sessions_active_total · dcm_session_revocations_total · dcm_drift_open_records_total · dcm_providers_healthy_total · dcm_internal_ca_certificates_active. HLT-005.

### Kubernetes Manifest
livenessProbe: /livez PT5S timeout, 10s period, 3 failures.
readinessProbe: /readyz PT10S timeout, 5s period, 6 failures.
startupProbe: /readyz PT10S timeout, 10s period, 30 failures (allows 300s startup).

---

## SECTION 72 — STANDARDS AND COMPLIANCE CATALOG (doc 40 — 40-standards-catalog.md)

> **Full specification:** [40-standards-catalog.md](https://github.com/croadfeldt/udlm/blob/main/reference/standards-catalog.md) — authoritative source for all RFCs, protocols, cryptographic standards, CNCF projects, and compliance frameworks used in DCM.

### Internet Standards (IETF RFCs) — Normative
Auth/AuthZ: RFC 7519 (JWT) · RFC 7517 (JWK) · RFC 7662 (Token Introspection) · RFC 6749 (OAuth 2.0) · RFC 4511 (LDAP) · RFC 7643/7644 (SCIM 2.0)
Transport: RFC 8446 (TLS 1.3, preferred) · RFC 5246 (TLS 1.2, minimum) · RFC 5280 (X.509/CRL) · RFC 6960 (OCSP)
Certificate enrollment: RFC 7030 (EST, preferred) · RFC 8555 (ACME) · RFC 8894 (SCEP, optional) · RFC 4210 (CMP, optional)
API lifecycle: RFC 8594 (Sunset header, VER-003) · RFC 9745 (Deprecation header, VER-003)
Health/discovery: RFC 8615 (Well-Known URIs, /livez /readyz /.well-known/dcm-api-versions)
Data: ISO 8601 (all timestamps and durations) · RFC 8259 (JSON, all API bodies)

### Cryptographic Standards
Permitted algorithms: ECDSA P-384 (Internal CA, all profiles), AES-256-GCM, SHA-256 minimum, SHA-384/512 for fsi+
RSA permitted only ≥ 2048 bits
TLS: 1.3 preferred, 1.2 minimum — TLS 1.0/1.1 strictly prohibited in ALL profiles
FIPS 140-2 Level 1+ (standard/prod), Level 2+ (fsi/fedramp), Level 3 (sovereign/dod_il4)
FORBIDDEN (all profiles, no exceptions): MD5, SHA-1, DES, 3DES, RC4, RSA < 2048

### Authentication Assurance Levels (NIST SP 800-63B)
minimal/dev: AAL1 (single factor OK) · standard/prod: AAL2 (MFA required) · fsi: AAL2+ (phishing-resistant) · sovereign: AAL3 (hardware authenticator)

### Compliance Frameworks and DCM Profile/Overlay Mapping
HIPAA → fsi profile + hipaa overlay · PCI DSS → pci_dss overlay (P90D max rotation, 12-month audit) · FedRAMP Moderate/High → fedramp_moderate/fedramp_high overlays (NIST 800-53) · DoD IL4 → dod_il4 overlay (FIPS 140-2 Level 2, hardware attestation) · GDPR → sovereignty constraints + data classification · ISO 27001 → all profiles (risk-based approach) · SOC 2 → standard+ (Type II audit trail) · NIST SP 800-53 → FedRAMP profiles

### CNCF Ecosystem (Graduated Projects)
Kubernetes (deployment, CRD operator, resource model) · OPA/Open Policy Agent (policy engine backend, Rego) · Prometheus (metrics, /metrics endpoint) · OpenTelemetry (tracing, correlation IDs) · Istio (internal mTLS service mesh) · Argo CD / Flux (GitOps delivery) · SPIFFE (workload identity concept — inspiration for ICOM component identity model)

### Operational Standards (Normative)
W3C SSE / Server-Sent Events (GET /api/v1/requests/{uuid}/stream — live status without polling) · OpenAPI 3.1 (REST API spec format — consumer, admin, OIS specs) · Unix cron / POSIX (recurring schedule expressions in doc 37) · IANA health+json (RFC 8615 — /livez /readyz health response format) · GitOps / OpenGitOps v1.0 (all DCM artifacts in Git; PR-based contribution)

### External CA credential management services (Optional)
HashiCorp Vault PKI (native API + EST/ACME; recommended enterprise PKI for fsi/sovereign; operates as subordinate CA) · Venafi TLS Protect (ACME/EST/REST) · EJBCA (ACME/CMP/SCEP) — all implemented as x509_certificate credential management services per doc 31; NOT Auth Providers

### Policy Family → Standards Mapping (doc 40 Section 9)
AUTH → RFC 6749/7519/7662/OIDC/SCIM · CPX → FIPS 140/RFC 5280/8555/7030/8894/4210 · ICOM → RFC 8446/5280/SPIFFE/FIPS 140 · VER → RFC 8594/9745 · SES → RFC 7662/7009 · HLT → RFC 8615/Kubernetes probes · ZTS → NIST SP 800-207/800-63B · SCH/RDG → industry scheduling/DAG patterns · SMX/ATM → organizational risk governance

---

## SECTION 73 — OPERATIONAL REFERENCE (doc 41 — 41-operational-reference.md)

> **Full specification:** [41-operational-reference.md](../../reference/operational-reference.md) — GitOps store partitioning, store migration playbook, disaster recovery scenarios, OPS-001–007.

### GitOps Store Partitioning (Section 1)
Three strategies: tenant-shard (hash(tenant_uuid) % N shards — recommended), per-tenant (one repo per tenant — MSP/strict isolation), time-based archiving (active vs cold archive repos). Triggers: >50k entities, clone time >PT30S, >500 tenants, repo >10GB. Layer Store partitioned by resource domain (Compute.*, Network.*, etc.). Shallow clones for read-only consumers; read mirrors for audit/drift.

### Store Migration Playbook (Section 2)
5-phase pattern: Prepare → Backfill → Validate → Cutover → Decommission (after burn-in). Dual-write mode during migration. Audit chain must be unbroken across cutover (OPS-002). Source stays read-only for burn-in period — DO NOT decommission early (OPS-003). Profile-governed burn-in: P7D(minimal) → P90D(fsi/sovereign). Rollback available during burn-in by re-pointing to source. Common paths: SQLite→PostgreSQL (evaluation→standard), PostgreSQL→CockroachDB (HA requirement), GitOps repo restructuring (monorepo→shards via git filter-repo).

### Disaster Recovery Scenarios (Section 3)
5 scenarios with RTO/RPO per profile:
- S1 Component failure: pod restart; RTO PT1M(sovereign)–PT15M(minimal); RPO 0 (stateless)
- S2 Store failure: failover/restore; RTO PT5M(fsi)–PT2H(minimal); RPO 0(GitOps)–PT15M(Audit)
- S3 Full control plane loss: redeploy + store reconnect; RTO PT5M(fsi)–PT30M(minimal); RPO 0
- S4 Partial region loss: federation reroutes; sovereignty-scoped may block until region recovers
- S5 Repave (complete loss, Git intact): bootstrap from Git, restore operational stores from backup, rehydrate managed resources; RTO PT2H(fsi)–PT24H(minimal)

Post-recovery validation checklist (Section 3.6): /livez pass, /readyz pass, audit chain verify, store validate, drift scan, cert status, write post-incident audit record. OPS-005.

### OPS-001–007 System Policies
OPS-001: partitioning declared in deployment manifest. OPS-002: audit chain continuity across migration. OPS-003: source read-only during burn-in; do not decommission early. OPS-004: RTO must be met per profile. OPS-005: post-recovery checklist written to audit store. OPS-006: Audit Store minimum P365D retention all profiles. OPS-007: Git remotes must have push access from 2+ geographically separated locations.

---

## SECTION 74 — WEB INTERFACE SPECIFICATIONS (3 specs)

> **Consumer GUI:** [dcm-consumer-gui-spec.md](../../docs/specifications/dcm-consumer-gui-spec.md) — Consumer Portal wrapping all 16 Consumer API sections, bounded by tenancy
> **Admin GUI:** [dcm-admin-gui-spec.md](../../docs/specifications/dcm-admin-gui-spec.md) — Admin Panel wrapping all Admin API sections, role-gated
> **Provider GUI:** [dcm-provider-gui-spec.md](../../docs/specifications/dcm-provider-gui-spec.md) — Provider management shell + 11 type-specific extension sets

### Unified Shell Architecture (GUI-010)
ONE application, THREE role-gated surfaces: Consumer Portal (all actors) + Admin Panel (platform_admin/sre/auditor/security/policy_owner/finops) + Provider Management (provider_owner role). One login, one session token — navigation adapts to highest privilege level. Flow GUI (policy authoring) is linked/embeddable within Admin Panel.

### Consumer Portal (dcm-consumer-gui-spec.md — 20 sections)
Tenancy: X-DCM-Tenant header; ContextSelector in masthead (hidden for single-tenant actors).
Navigation (PatternFly grouped left nav): Service Catalog | MY WORK (Requests, Resources, Dependency Groups) | Approvals [badge] | GOVERNANCE (Cost & Quota, Audit Trail, Contributions) | SETTINGS (Notifications, Sessions). **Hide, not disable** — unavailable items hidden entirely.
Key capability — Live Status (GUI-002): SSE stream (GET /api/v1/requests/{uuid}/stream); events: status_change, progress_updated, approval_required, approval_recorded, heartbeat; constituent_status array for Composite Service requests; fallback to polling.
Key capability — Request form: rendered from catalog item schema; live cost estimate; scheduling section (at/window/recurring); dependency group linking with field injection declaration.
Key capability — ITSM Bridge (GUI-014, section 8): ITSM references (ServiceNow/Jira change records, CMDB CIs) displayed on entity Overview tab; ITSM notification service translates DCM events → ITSM records; ITSM systems call Admin API to record approval votes (DCM records decision, ITSM runs CAB process); CMDB sync is one-way DCM→CMDB via notification service subscription.
Key capability — Consumer Audit Trail (section 11): own resource audit trail with Correlation ID trace through full pipeline; filterable by operation/type/date; export CSV.
Key capability — Drift Report (section 6.3): cross-resource drift view with severity sorting; Revert All Critical bulk action; export drift report.
Security: MFA step-up inline (no page leave); strict CSP (connect-src self + DCM API origin only; no inline scripts).

### Admin Panel (dcm-admin-gui-spec.md)
Platform health dashboard: component health grid, provider health summary, pending approvals count — all from GET /api/v1/admin/health.
Tier registry editor: drag-and-drop reorder; impact report shows SECURITY_DEGRADATION(red)/BROKEN_REFERENCE(orange)/PROFILE_GAP(yellow)/SECURITY_UPGRADE(green); activate blocked until all blocking items resolved.
Scoring editor: visual slider with hard-stop — auto_approve_below slider maximum is 50 (SMX-008/ATM-002); signal weights must sum to 100%.
Flow GUI accessible via link or embedded iframe for policy_owner/sre roles.

### Provider Management (dcm-provider-gui-spec.md)
Common shell for ALL 5 provider types: overview, config, health history, audit trail, notifications.
Provider ownership: declared at registration (owner_team_uuid); provider_owner role scoped per provider UUID.
Service Provider extensions: capacity management (manual override for emergencies), managed entities with drift indicators, naturalization mapping viewer, test naturalization tool, interim status config.
credential management service extensions: inventory (metadata only — NEVER values), rotation management, revocation registry search, external CA config (protocol, chain, CRL/OCSP status), algorithm compliance view (forbidden algorithms must be zero).
Auth Provider extensions: connection status with failover chain, SCIM sync status, session statistics by auth method.

### Security Model (all GUI surfaces)
Navigation: hide not disable. Roles from session token; re-checked on token refresh. Tenancy: X-DCM-Tenant enforced UI + API (defense in depth). Step-up MFA: inline prompt without page navigation; cached PT10M. CSP: connect-src self + DCM API; no inline scripts; no eval().

### RHDH Integration (dcm-rhdh-integration-spec.md)
PRIMARY deployment model. 6 plugin packages as Dynamic Plugins (no RHDH rebuild): @dcm/backstage-plugin (frontend) · @dcm/backstage-plugin-backend (proxy + SSE relay + auth) · @dcm/backstage-plugin-catalog-backend (entity provider: DCMService + DCMResource) · @dcm/backstage-plugin-scaffolder-backend (dcm:request:submit, dcm:request:wait with live log, dcm:request:group, dcm:catalog:refresh) · @dcm/backstage-permission-policy (DCM roles → Backstage permissions) · @dcm/backstage-plugin-auth-backend (RHDH as DCM OIDC provider).
Auth: RHDH/Keycloak → OIDC token exchange → DCM session token (cached in RHDH backend by backstage user ref). Tenancy: RHDH Group context → X-DCM-Tenant header (via dcm-tenant-{uuid} group naming convention).
Entity model: DCMService kind (catalog items, namespace=dcm-catalog) auto-generated from DCM API every PT5M. DCMResource kind (realized resources, namespace=dcm-tenant-uuid) auto-synced from Realized State. Both search-indexed in RHDH.
Scaffolder = request form: each DCM catalog item generates one Backstage Software Template from its JSON Schema. Template wizard → dcm:request:submit → dcm:request:wait (live log: step N/M, constituent status) → dcm:catalog:refresh → entity appears in catalog. NO separate request form UI needed.
PatternFly nav: NavGroup(MY WORK > Requests/Resources/Groups) · NavItem with NotificationBadge (Approvals [count]) · NavGroup(GOVERNANCE > Cost&Quota/Contributions) · NavGroup(SETTINGS > Notifications/Sessions). Tenant via RHDH ContextSelector in masthead.
Pre-built RHDH value: RHSSO/Keycloak auth (no auth code) · RBAC plugin (no-code role management) · TechDocs (DCM docs in-portal) · ArgoCD plugin (layer store visibility) · AAP plugin (Ansible provider job status) · OCM plugin (cluster management alongside DCM).
Migration: Standalone SPA → RHDH via Dynamic Plugin loading only; no data migration, no API changes; 5-phase migration ending in standalone SPA decommission.

---

## SECTION 75 — ITSM INTEGRATION (doc 42 — 42-itsm-integration.md)

> **Full specification:** [42-itsm-integration.md](../integrations/itsm.md) — 12th provider type, 8th policy type, 6 example policies, ITSM-001–007, ITSM-POL-001–004.

### Design Principle
DCM replaces the infrastructure ticket as the provisioning mechanism. ITSM integration is ADDITIVE — never required for DCM to function. Non-blocking by default. Organizations opt into blocking gates explicitly.

### ITSM Integration (via process_provider)
Bidirectional: outbound (DCM events → ITSM records) + inbound (ITSM approvals → DCM votes). Implements full base Provider contract (PRV-001). Supported systems: ServiceNow, Jira Service Management, BMC Remedy/Helix, Freshservice, PagerDuty, Opsgenie, ManageEngine, Cherwell, TOPdesk, generic_rest.
Key capabilities: create/update/close change_request, create/update/close incident, create/update/retire cmdb_ci, create service_request, inbound_approval, inbound_request_initiation.
Credentials: auth via credential management service (ITSM-001). Inbound webhooks: HMAC-SHA256 verified (ITSM-003).

### ITSM Action Policy (8th policy type)
Side-effect policy — fires on DCM events, triggers ITSM action, does NOT block pipeline by default.
Output schema: itsm_provider_uuid, action, action_payload (template expressions: {{ field }}), store_reference_on_entity, block_until_created, block_timeout, on_failure.
ITSM-005: block_until_created REQUIRES block_timeout — pipeline never permanently stalled.
ITSM-POL-002: NOT a Gating Policy substitute except via explicit block_until_created mechanism.
ITSM-POL-004: Multiple ITSM Policies on same event fire INDEPENDENTLY.

### 6 Policy Examples
1. create_change_request on request.dispatched (ServiceNow) — log and continue
2. block_until_created for PCI-scope tenants (compliance gate with PT30M timeout)
3. create_cmdb_ci on entity.realized — with IP address from realized_fields
4. create_incident on drift.detected (significant/critical severity, Jira)
5. retire_cmdb_ci on entity.decommissioned
6. close_change_request on request.realized

### ITSM Entity References
itsm_references[] on entity business data: system, record_type, record_id, record_url, status, last_synced_at. Preserved through entity lifecycle. In audit records.

### recorded_via Field
Already on approval vote API: dcm_admin_ui | servicenow | jira | slack_bot | api_direct | other. ITSM integration populates this on inbound approvals.

### Event Catalog Additions
itsm.record_created, itsm.record_updated, itsm.record_failed — new itsm.* domain (21st domain; 85 total events).

### ITSM-001–007 + ITSM-POL-001–004
ITSM-001: base Provider contract applies. ITSM-002: non-blocking by default. ITSM-003: inbound webhook HMAC auth. ITSM-004: references persist through lifecycle. ITSM-005: block_until_created mandatory timeout. ITSM-006: unmapped resource types silently skipped for CMDB sync. ITSM-007: missing template fields → warning + empty string (no block).

---

## SECTION 76 — PROVIDER CALLBACK AUTHENTICATION (doc 43 — 43-provider-callback-auth.md)

**Purpose:** Specifies how Service Providers authenticate inbound calls to the DCM control plane (the Provider Callback API). Resolves the gap between the outbound credential model (DCM → Provider) and the inbound model (Provider → DCM).

**Two-layer model:**
- **Layer 1 — mTLS:** Provider presents its registered certificate on every TLS connection. DCM validates the chain against the registered CA and the stored certificate fingerprint for that provider_uuid. Proves transport-level identity.
- **Layer 2 — Provider Callback Credential:** A `dcm_interaction` credential issued by the credential management service at provider activation time. Scoped to `provider_uuid` + `allowed_operations`. Short-lived (PT15M fsi/sovereign; PT1H standard). Presented as `Authorization: Bearer` on every callback call. Proves operation-level authorization.
- Both layers are required. mTLS alone does not prove authorization. The credential alone cannot establish the connection.

**Entity-level authorization (per call, independent of credential):**
- `realized_state_push`: DCM verifies `credential.provider_uuid` matches the `provider_uuid` in the Requested State record for that `resource_id`. Prevents a provider from pushing state for entities it was not dispatched to.
- `update_notification`: DCM verifies the calling provider is the current Realized State provider for the entity AND the `notification_type` was declared in the provider's registration.
- `lifecycle_event`: DCM verifies the calling provider is the provider on record for the resource.

**Credential lifecycle:**
- Issued at provider activation; delivered via the activation response (retrieved via credential management service)
- Rotated automatically by DCM before expiry (DCM initiates rotation; provider must implement refresh)
- Transition window (50% of credential lifetime) during which both old and new credentials are accepted
- Revoked immediately on: provider deregistration, 5+ scope violations in PT1H, admin explicit revocation, certificate expiry without rotation

**Registration special case:**
- Initial registration (`POST /api/v1/providers`) uses a registration token (single-use, admin-issued) not the callback credential — no callback credential exists until activation
- Re-registration (same name, updating version/capabilities) uses the active callback credential
- Re-registration that changes sovereignty declaration requires a new registration token and triggers a new approval pipeline

**System policies:** PCA-001 through PCA-010. Key: PCA-003 (entity-level ownership check is independent of credential), PCA-004 (5 scope violations → auto-suspend), PCA-010 (all inbound calls produce audit records including rejected ones — no silent failures).


## SECTION 77 — AEP API ALIGNMENT

DCM's four OpenAPI specifications follow AEP (API Enhancement Proposals — aep.dev) conventions in three specific areas:

**1. Custom methods (AEP-136):** Actions on resources use colon syntax. `POST /resources/{id}:suspend` not `POST /resources/{id}/suspend`. Applies to all state-transition and action operations in Consumer and Admin APIs (30 path conversions total: :suspend, :resume, :rehydrate, :rotate, :extend-ttl, :transfer, :bulk-decommission, :acknowledge, :revert, :approve, :reject, :reinstate, :trigger, :rebuild, :activate, :vote, :revoke-sessions, :accept-degradation, :rotate-credential, :read-all, and others).

**2. Long-Running Operations (AEP-151):** Async operations that produce a trackable result return an `Operation` resource (not `202 Accepted` with no body). The `Operation` has: `name` (stable poll URL), `done` (boolean), `metadata` (stage/progress/resource_uuid), `response` (present when done=true, success), `error` (present when done=true, failure). 14 consumer-facing operations return Operation: submitRequest, createRequestGroup, updateResource, decommissionResource, suspendResource, resumeResource, rehydrateResource, initiateOwnershipTransfer, bulkDecommission, revertDrift, rotateCredential, contributePolicy, contributeResourceGroup (consumer API) + decommissionTenant (admin API). Fire-and-forget operations (capacity reports, interim status, lifecycle events, discovery triggers) retain `202 Accepted` — no Operation body.

**3. Pagination (AEP-158):** `page_size` and `page_token` query parameters (not `limit`/`cursor`). Responses include `next_page_token`.

**Deliberately NOT aligned:** Resource names (DCM retains bare UUIDs — immutability across ownership transfers is more important than AEP naming), timestamp field names (`created_at` not `create_time` — would require data model change with no functional benefit).

**Operator API note:** The operator-facing Services API (dcm-operator-api.yaml) uses the callback pattern — operators are NOT consumer-facing LRO callers. `updateResource` in the operator spec uses `202 Accepted` (async with callback) + `200 OK` (sync with RealizedStatePayload), not an Operation resource.

## SECTION 78 — KESSEL INTEGRATION EVALUATION (doc 44 — 44-kessel-integration-evaluation.md)

**Status:** Pre-implementation evaluation. Discussion with Kessel team required before any implementation. No DCM architecture changes should be made based on this document until alignment is confirmed.

**What Kessel is:**
- **Kessel Relations:** Authorization service built on SpiceDB (Google Zanzibar / ReBAC). `CheckPermission(subject, permission, resource)` traverses relationship graph. Zookie consistency tokens for "read your own writes" guarantee.
- **Kessel Asset Inventory:** Hybrid cloud resource state tracking (current-state snapshot store, gRPC streaming API). Integrates with Kessel Relations for auth-filtered inventory queries.

**Integration Option A — Kessel Relations as DCM Auth Provider:**
- Handles checks 1 and 2 of DCM's five-check boundary model (identity + authorization). Checks 3-5 (accreditation, data matrix, sovereignty) remain in DCM's Policy Engine — cannot be delegated.
- DCM's entity relationship graph (operational: requires/constituent/shareable) must NOT go in Kessel Relations — only access-control relationships.
- Approval gate quorum stays in DCM (Kessel answers "is actor authorized to vote?"; DCM tracks "how many have voted").
- Integration path: new `auth_mode: kessel_rebac` Auth Provider registration.
- Zookie tokens must be threaded through DCM request context for consistency.

**Integration Option B — Kessel Inventory as Discovered State Store:**
- Discovered State only (most ephemeral store, current-state snapshot). Intent, Requested, Realized stores remain in DCM — not replaceable by Kessel Inventory.
- Drift detection logic stays in DCM's DRC component regardless — Kessel Inventory is a data source, not a drift engine.
- Field-level provenance, lifecycle state machine, audit chain — all stay in DCM.
- Integration path: snapshot store backed by Kessel Inventory. No data model changes.

**Pros (Relations):** SpiceDB production-grade, Zanzibar consistency, scalable graph traversal, shared source of truth across Red Hat products, single CheckPermission call replaces multi-step group-lookup + policy-evaluation.

**Pros (Inventory):** Feeds same discovered state to ACM/Insights/HCC, reduces DCM's operational burden for ephemeral store, gRPC streaming fits provider push pattern.

**Cons (Relations):** Hard runtime dependency (unavailability = safe-deny mode), schema coupling requires coordinated evolution, quorum model doesn't fit, entity relationship graph stays in DCM anyway.

**Cons (Inventory):** Four-state model mismatch (Kessel is upsert/current-state only), no field-level provenance, no drift detection, schema extensibility for DCM-specific types unconfirmed, project maturity risk.

**18 questions for Kessel team documented in Section 6. 10 blocking items in Section 10.**

**KESSEL-001 through KESSEL-007** are the proposed system policies — not active until Kessel alignment is complete.
## SECTION 79 — CONSISTENCY REVIEW (doc 45 — 45-consistency-review.md)

Full consistency review completed 2026-03. Key findings and fixes:

**Fixed:** AEP colon paths applied to admin-api-spec.md (13 paths) and consumer-api-spec.md (4 remaining); stale entity_type values corrected (`allocated_resource`→`infrastructure_resource`, `resource_entity`→`infrastructure_resource`); stale scoring threshold keys replaced with named-tier format comments; `provider_id`→`provider_uuid` in DCM API endpoint paths; Operation (LRO) polling section added to consumer spec.

**Canonical rules:** entity_type has exactly three values (infrastructure_resource, composite_resource, process_resource). Custom method paths use colon syntax in ALL docs. `provider_uuid` in DCM APIs; `resource_id` (operator-assigned) in callback APIs — these are intentionally distinct. Lifecycle state UPPERCASE in YAML, lowercase in prose — by design.

**Three implementation decisions still needed:** (1) resource_type field: accept FQN string or require UUID at dispatch? (2) Operation polling: same endpoint as request status or separate? (3) API Gateway must map resource_id → entity_uuid at callback boundary.


## SECTION 80 — IMPLEMENTATION DECISIONS RESOLVED (doc updates 2026-03)

Three open implementation decisions have been resolved:

**DECISION 1 — resource_type field: accept both FQN and UUID**
- Consumers may supply resource_type as either FQN string (`Compute.VirtualMachine`) or Registry UUID
- DCM resolves either form to the canonical (resource_type_uuid, resource_type_name) pair at request assembly time in the Request Payload Processor
- FQN recommended for consumer use (stable across deployments; returned by service catalog)
- UUID accepted for programmatic use where UUID was obtained from catalog API
- Unresolvable references rejected at validation time: 422 + code RESOURCE_TYPE_NOT_FOUND
- Dispatch payloads (CreateRequest/UpdateRequest) to operators ALWAYS carry both: resource_type_uuid + resource_type_name
- Added to: dcm-common.json (resource_type_ref oneOf type), CatalogItem schema (oneOf in consumer YAML), doc 05, consumer spec, operator spec

**DECISION 2 — operation.name → /api/v1/operations/{uuid} (separate AEP endpoint)**
- operation_uuid == request_uuid — the same UUID serves both endpoints
- GET /api/v1/operations/{uuid} → Operation schema (AEP-standard: done, metadata, response/error)
- GET /api/v1/requests/{uuid}/status → RequestStatus schema (DCM-native: pipeline_stage, full history)
- Both endpoints reflect the same underlying operation state
- Operation.metadata includes request_uuid field so AEP clients can navigate to the rich view if needed
- POST /api/v1/requests returns Operation with name = /api/v1/operations/{request_uuid}
- Added to: consumer YAML (new GET /api/v1/operations/{operation_uuid} path, 61 paths total), Operation schema (request_uuid in metadata, dual-endpoint description), consumer spec (Operations polling section with dual-endpoint table)

**DECISION 3 — resource_id → entity_uuid mapping (RESOLVED by existing data model)**
- Not an open decision — already solved by the schema
- DCM sends dcm_entity_uuid in every CreateRequest dispatch; operator echoes it in every response and callback
- DCM uses entity_uuid for all routing; resource_id is operator's own correlation handle stored opaquely
- API Gateway validates dcm_entity_uuid in each callback matches the entity under the calling provider's credential
- Documented explicitly in operator interface spec


## SECTION 81 — SPEC COMPLETION: K8S + OPERATOR SDK (2026-03)

**11-kubernetes-compatibility.md** — Completed:
- Document status header and related docs cross-references added
- Section 2 intro: explains the superset relationship explicitly
- Section 4 summary table: 7 DCM capabilities vs Kubernetes gaps, side-by-side
- Comment lines cleaned from section 3a (code comment artifacts removed)
- AEP alignment note added
- All 5 open questions were already resolved; Resolution Notes complete
- Status: ✅ Complete

**dcm-operator-sdk-api.md** — Completed:
- Document status header, related docs, AEP alignment note added
- New Section 11: Callback Credential Management — automatic rotation, entity_uuid vs resource_id contract, DCM validation rule
- resource_type_name field annotated: "FQN — always present alongside resource_type_uuid"
- All 5 open questions were already resolved; Q10 header annotated
- Status: ✅ Complete

**All 14 specifications now have:** AEP alignment notes, document status headers, no stale slash-verb paths, consistent field naming.


## SECTION 82 — PDF VALIDATION + THREE NEW ADDITIONS (2026-03)

**PDF (Miro board) was validated against current architecture.** Core finding: PDF = original design intent; current docs = evolved, more detailed implementation. Structurally aligned. Three gaps identified and filled:

**GAP 1 — Static Replace use case (dcm-examples.md sections 1.9 + 1.10):**
- Static Replace = re-provision using existing Requested State verbatim, no layer enrichment, no policy re-evaluation. Deterministic rebuild.
- Distinct from Rehydration (mode: intent) which replays original Intent State through current policies and layers.
- `POST /api/v1/resources/{uuid}:rehydrate` with `mode: static` (same endpoint, different mode).
- Precondition: application data on separate partition (VM OS/config is what gets rebuilt).
- Orchestration Flow Policy specified (4-step: validate → decommission → dispatch original requested state → restore operational).
- In-Place Upgrade (Leapp/IPU) also documented as Section 1.10 — upgrades OS in-place, preserves entity UUID, creates new Realized State delta record.

**GAP 2 — Workload Analysis (new doc 46-workload-analysis.md):**
- New capability: actively classifies discovered resources by operational characteristics.
- Answers: "what is this resource?", "is it migratable?", "what lifecycle model applies?"
- WorkloadProfile = process_resource_entity of type Analysis.WorkloadProfile.
- Fires automatically as part of brownfield ingestion pipeline (DRC → WLA → Ingestion).
- MTA (Migration Toolkit for Applications) is the reference Information Provider implementation.
- 6 system policies WLA-001 through WLA-006.
- API: GET /api/v1/resources/{uuid}/workload-profile, POST /api/v1/resources/{uuid}/workload-profile:analyze
- Added to Capabilities Matrix as Domain 36 (6 capabilities: WLA-001 to WLA-006).

**GAP 3 — Per-provider monitoring contract (registration spec + self-health doc):**
- 7 Provider Readiness Gates (GATE-SP-01 through GATE-SP-07) added to registration spec Section 7.2.
- Gates 1-3 required for all profiles; Gates 4-7 required for standard+.
- GATE-SP-01: OpenAPI spec declared and reachable.
- GATE-SP-02: Healthy API at activation.
- GATE-SP-03: State Management callback implemented.
- GATE-SP-04: Tenant Metadata endpoint (usage by tenant, quota consumed).
- GATE-SP-05: Prometheus metrics (4 required families: dispatches_total, dispatch_duration_seconds, realizations_total, health_status).
- GATE-SP-06: AEP.DEV linting passes (no errors in provider OpenAPI spec).
- GATE-SP-07: Multi-tenant dispatch (accepts tenant_uuid).
- Self-health doc (39-dcm-self-health.md) Section 7: Per-Provider Metrics Contract added.
- Added to Capabilities Matrix as PRR-001 through PRR-007 in Provider Contract domain.
- Matrix now: 37 domains / 287 capabilities.

**PDF naming differences documented (not errors — terminology evolution):**
Widget → Resource/Entity; Requested/Realized/Discovered Widget Store → State Stores;
Widget Discovery → Discovery Scheduler; Interoperability API → Operator Interface;
Provisioned Store → Realized State Store; Job Queue → Message Bus; Rules Engine → Policy Engine.


## SECTION 83 — ACCREDITATION MONITOR (doc 47 — 47-accreditation-monitor.md)

**Purpose:** Continuously verifies registered accreditations against authoritative external sources. Answers: "Is this accreditation still valid according to the issuing authority — not just the expiry date we were told?"

**Four verification tiers (by automation depth):**
- **Tier 1 — External Registry API (full automation):** FedRAMP (marketplace.fedramp.gov/api), CMMC 2.0 (cyberab.org/catalog), StateRAMP, ISO 27001 (iaf.nu CertSearch). Queries by external_registry_id; detects status changes including mid-cycle revocations.
- **Tier 2 — Document Currency (partial automation):** SOC 2, PCI DSS AoC. Fetches document from certificate_ref/audit_report_ref, extracts date via PDF metadata or header parsing, validates against max_age threshold (default P365D).
- **Tier 3 — Contract Webhook (event-driven):** HIPAA BAA, DoD IL. Inbound webhook from DocuSign/Ironclad/etc fires when BAA is signed, amended, or terminated. DCM processes: signed→active, amended→pending_review, terminated→revoked.
- **Tier 4 — Expiry-Only (no external check):** Self-declared, internal, HIPAA BAA without contract system. Monitors declared valid_until only.

**Key flows:**
- Tier 1 poll detects Revoked status → immediate accreditation revocation → Accreditation Gap triggered (no admin confirmation required for revocations)
- Tier 1 poll detects status change to non-revoked (e.g., Authorized → In Process) → status: pending_review → admin confirms
- Registry unreachable → increment failure_count; no status change; fires verification_stale at threshold
- stale_after exceeded → stale_action: warn/suspend/escalate (profile-governed: warn for dev/standard, suspend for prod, escalate for fsi/sovereign)

**Accreditation record additions (doc 26 Section 3.3):** `verification` block with tier, registry_api/document_check/contract_webhook sub-blocks, stale_after, stale_action, verification_failure_count. `status` gains `pending_review` state. `gap_type` gains `verification_stale`.

**Scoring Model addition (doc 29 Signal 5):** `verification_multipliers` — accreditation weight discounted based on verification currency: external_registry verified today = 1.0, expiry_only = 0.7, stale = 0.4, failed threshold = 0.1.

**New events (doc 33 Section 20):** accreditation.verified, accreditation.status_changed, accreditation.registry_mismatch, accreditation.verification_stale, accreditation.document_expired, accreditation.contract_event, accreditation.expiry_approaching.

**8 system policies: ACM-001 through ACM-008.** Key: ACM-002 (status change → pending_review except Revoked which is immediate), ACM-003 (registry unreachable does NOT revoke), ACM-004 (fsi/sovereign must use tier ≥ document_currency), ACM-007 (all verifications produce audit records — no silent checks).

**Air-gapped mode:** Tiers fall back to expiry_only for unreachable registries. Retries after air_gapped_retry_interval (default P30D). Manual update of last_verified_at permitted with required justification.

**Matrix:** Domain 37, ACM-001 through ACM-007. Total: 37 domains / 287 capabilities.


## SECTION 84 — COMPREHENSIVE USE CASE EXAMPLES (dcm-use-case-examples.md)

New specification: `specifications/dcm-use-case-examples.md` — 1,853 lines, 5 sections.

**Shared context:** All examples use consistent fictitious actors (alice@corp, bob@corp, svc-pipeline@corp), tenants (payments-bu, web-platform-bu, platform-team), and providers (vmware-prod, netbox-prod, vault-prod, freeipa-prod, ceph-prod, rabbitmq-prod, servicenow-prod, webapp-meta) for cross-example coherence.

**Section 1 — Data Model Examples (12 examples):**
- 1.1 Four States: VM intent → layer assembly → requested state → realized state → discovered state → decommission
- 1.2 Layer Assembly: 6-layer compose (base/DC/zone/BU/service/request) with full provenance
- 1.3 Governance Matrix: PHI request denied — four-axis evaluation, HIPAA BAA missing on provider
- 1.4 Scoring Model: 5-signal risk score (0-100), placement tie-breaking by accreditation richness + verification multiplier
- 1.5 Authority Tier: 200-VM bulk request → CRITICAL tier → 3-step approval chain
- 1.6 Entity Relationships: VM+IP+FirewallRule composite, decommission impact analysis
- 1.7 Universal Groups: tenant boundary, resource group, cross-tenant read authorization
- 1.8 Scheduled Requests: maintenance window + deferred OS patch via CI/CD
- 1.9 Request Dependency Graph: DB→App→LB 3-node chain with field injection between nodes
- 1.10 Workload Analysis: legacy VM discovered → classified (batch_processor, confidence:medium) → MTA score → ingested
- 1.11 Accreditation Monitor: FedRAMP daily verify + mid-cycle revocation → immediate gap trigger
- 1.12 Session Revocation: stolen laptop → all sessions revoked → in-flight request aborted safely

**Section 2 — Provider Interaction Examples (6 new examples, 2.5–2.10):**
- 2.5 Auth Provider (FreeIPA): registration, LDAP auth flow, group mapping → DCM roles
- 2.6 Data Store: write-once snapshot registration, Realized State write
- 2.7 event routing service (RabbitMQ): topic exchange, routing key pattern, multi-subscriber routing
- 2.8 credential management service (Vault): AppRole registration, ephemeral bind-password fetch, dynamic DB creds, consumer SSH key retrieval with audit
- 2.9 Composite Service: WebApp (VM+IP+FW+DNS) decomposition, parallel + sequential constituent ordering, field injection
- 2.10 ITSM integration (ServiceNow): incident creation on provider health change, field mapping, resolve on recovery

**Section 3 — Registration Flow Examples (3 examples):**
- 3.1 Information Provider (NetBox): token issuance, mTLS registration, 6-check validation, approval, assembly enrichment
- 3.2 Auth Provider (Azure AD OIDC): secondary auth source for contractors, precedence ordering, TTL-scoped role mapping
- 3.3 Composite Service: constituent validation, circular dependency check, activation

**Section 4 — OPA Policy Integration (2 examples):**
- 4.1 Shadow mode: 30-day shadow evaluation, divergence reporting, admin review dashboard, promotion to active
- 4.2 Bundle delivery: sidecar registration, 5-minute pull cycle, hot reload, evaluation call with input/output

**Section 5 — GUI Examples (3 examples):**
- 5.1 Consumer Portal: login → catalog → cost estimate → submit → progress polling → credential delivery
- 5.2 Admin GUI Policy Flow: node-by-node pipeline visualization with shadow indicators and red blocking paths
- 5.3 Admin GUI Drift Dashboard: severity summary, critical drift detail, revert/accept/investigate actions


## SECTION 85 — EXAMPLES EXPANSION (dcm-examples.md)

dcm-examples.md expanded from 1,058 lines to 2,189 lines. Now covers all 10 provider types, all 3 remaining policy types, and 8 new lifecycle/model flows. Full section inventory:

**Section 6 — Provider Type Examples (NEW):**
- 6.1 Data Store — state store write/read cycle (provenance emission, replica confirmation)
- 6.2 Auth Provider — OIDC cutover from GitHub OAuth (shadow evaluation, zero-downtime cutover)
- 6.3 credential management service — SSH key issuance post-VM-realization, 90-day TTL, auto-rotation at P45D
- 6.4 Composite Service — three-tier WebApp stack (VM→VM→LB→DNS with field injection between tiers)
- 6.5 ITSM integration — ServiceNow Change Request lifecycle (create→approve→implement→close)
- 6.6 event routing service — Kafka event bridge (entity lifecycle events, dead letter handling)

**Section 7 — Policy Type Examples (NEW):**
- 7.1 Transformation Policy — OS image auto-injection (immutable field, provenance annotation)
- 7.2 Placement Policy — PHI VM with HIPAA BAA requirement (require/prefer/exclude model, audit trail)
- 7.3 Shadow Execution — cost-cap policy rollout (parallel evaluation, divergence report, safe activation)

**Section 8 — Lifecycle and Model Examples (NEW):**
- 8.1 Scheduled Request — deferred provisioning via maintenance window (deadline handling, cancellation)
- 8.2 Request Dependency Graph — three-tier app with realized field injection across tiers
- 8.3 Authority Tier Routing — sovereign decommission requiring sequential platform_admin + CISO approval
- 8.4 Rehydration (intent mode) — DR failover to new datacenter (contrast with Static Replace)
- 8.5 Session Revocation — emergency security incident response (revoke-all, in-flight handling)
- 8.6 Workload Analysis — brownfield VM classification via MTA (port scan, process list, classification pipeline)
- 8.7 Scoring Model — placement tie-breaking with 5 signals (accreditation verification multiplier effect)
- 8.8 Accreditation Monitor — FedRAMP status change detection (mid-cycle downgrade, pending_review flow)

**Previously covered (Sections 1-5, unchanged):**
Service Provider (dispatch cycle), Information Provider (assembly enrichment), External Policy Evaluator (OPA sidecar),
notification service (audience graph), Consumer API lifecycle, Admin API flows, Registration onboarding,
Brownfield ingestion, Static Replace, In-Place Upgrade.

All 10 provider types: ✅ covered. All 7 policy output schemas: ✅ covered. All major model flows: ✅ covered.


## SECTION 86 — LOCATION TOPOLOGY LAYER MODEL (doc 48)

**New doc:** 48-location-topology-layers.md — specifies where resources can be allocated, how location data flows into requests as Core Layers, and how consumers select locations.

**Core concept:** Location is not a string field. It is a resolved chain of versioned Core Layers — one per level of the topology hierarchy. When a consumer selects "DC1 — Frankfurt Alpha", DCM assembles Country → Region → Zone → Site → Data Center layers into the request payload, injecting all structured location data at each level.

**Standard hierarchy (9 levels, configurable names, standard types):**
- Level 1 Country (CTY) — jurisdiction, regulatory frameworks, ISO codes
- Level 2 Region (RGN) — interconnects, latency profile, failover region
- Level 3 Zone/AZ (AZ) — isolation boundary, HA peers, RPO/RTO
- Level 4 Site/Campus (SITE) — physical address, security tier, facilities contacts
- Level 5 Data Center (DC) — tier classification, power/cooling, PUE, certifications
- Level 6 Hall/Pod (HALL) — optional; network segment, cooling type
- Level 7 Cage/Enclosure (CAGE) — optional; tenant isolation, access control
- Level 8 Rack (RACK) — rack units, power circuits, ToR switch
- Level 9 Unit/Slot (UNIT) — optional; typically provider-managed

**Authority model:** Each level has a designated owning authority (Data Center Operations, Network Operations, Facilities, Platform Governance). Changes require GitOps PRs approved by the owning authority. Upper levels (Country, Region, Zone) require platform_admin approval; lower levels (Hall, Cage, Rack) can be operator-approved.

**Custom types:** Custom levels insertable anywhere using decimal level values (e.g., Fleet=3.5, Ship=4.5 in a Navy deployment). Navy example included in doc.

**Priority bands:** Location layers occupy dedicated bands in the Core Layer priority space: Country=100.xx, Region=200.xx, Zone=300.xx, Site=400.xx, DC=500.xx, Hall=600.xx, Cage=700.xx, Rack=800.xx. Ensures specific always overrides general.

**Consumer API (NEW):**
- GET /api/v1/locations — list available location nodes (entitlement-filtered, filterable by resource_type, catalog_item, level, classification)
- GET /api/v1/locations/{uuid} — full detail including hierarchy, sovereignty, compliance, capacity
- ServiceRequest now accepts location_uuid or location_handle
- Consumer selects at any level; Placement Engine refines to specific DC at dispatch

**Admin API (NEW):**
- GET/POST /api/v1/admin/location-types — manage location type registry
- GET /api/v1/admin/locations — all location nodes (no entitlement filter)
- PATCH /api/v1/admin/locations/{uuid} — update mutable fields (e.g., rack_units_available)

**OpenAPI updates:** Consumer API now 63 paths; Admin API now 44 paths. LocationList, LocationSummary, LocationDetail schemas added to consumer API.

**Placement Engine integration:** Location layers feed LOC-005 sovereignty enforcement (max_data_classification per DC), Step 1 sovereignty pre-filter, Step 3 capability filter, and Placement Policy expressions (input.payload.location.jurisdiction, etc.).

**9 system policies: LOC-001 through LOC-009.**

**Matrix:** 38 domains / 294 capabilities.


## SECTION 87 — REFERENCE DATA LAYERS + LAYER-REFERENCED FIELD CONSTRAINTS

**Core clarification applied:** Layer data is the source of allowed values for resource type fields. This is not new architecture — it is the `layer_reference` constraint type made explicit throughout the documentation.

**Pattern:** A field in a Resource Type Specification can declare `constraint.type: layer_reference` with a `layer_type` name. At catalog item render time, DCM resolves the active instances of that layer type into the `allowed_values` list. The consumer selects from that list; DCM injects the full layer data into the assembled payload.

**Standard reference data layer types:**
- `location.data_center` — where resources can be placed (hierarchy: Country→Region→Zone→Site→DC→Hall→Cage→Rack)
- `os_image` — approved OS images (Platform Security team)
- `vm_size` — approved VM size profiles (Platform Team)
- `network_zone` — available network zones (Network Operations)
- `environment` — deployment environments (Platform Governance)
- `storage_class` — storage tiers (Storage Operations)
- `gpu_profile` — GPU configurations (Platform Team)

**Governance model:** Reference Data Layer instances have IDENTICAL lifecycle, controls, security, and governance as Resource Types — `developing → proposed → active → deprecated → retired`, GitOps workflow, versioned, owned by declared authority, immutable once active. Adding a new approved OS image = adding a new `os_image` layer. No Resource Type Specification change needed.

**Changes made this session:**

doc 03 (layering): New Section 3.7 — Reference Data Layers. Defines the pattern, governance model, and YAML format for `os_image` and `vm_size` reference data layers. Updated Core Layers cross-ref.

doc 05 (resource types): New Section 2.1b — Layer-Referenced Field Constraints. Explains why `layer_reference` is preferred over static enums. Complete table of standard layer types with owning authorities. Shows what the catalog item field constraint looks like when resolved (full `allowed_values` with structured data). Adds `layer_reference` and `layer_reference_list` to the field constraint type vocabulary, including `filter`, `display_field`, `value_field` sub-fields.

consumer-api-spec.md Section 3.2: Catalog item field schema now shows four field examples:
  - `cpu_count` — static `enum` constraint (unchanged)
  - `os_image` — `layer_reference` to `os_image` type (resolved `allowed_values` with image metadata)
  - `location` — `layer_reference` to `location.data_center` type (resolved with DC name, zone, certifications, capacity_status)
  - `size` — `layer_reference` to `vm_size` type (resolved with CPU/RAM defaults)
  Section 3.3 submit request shows layer UUIDs in the fields object with comments explaining DCM's resolution.

doc 48 (location): New Section 0 — Pattern Context. Explicitly frames location as one application of the Reference Data Layer pattern. Section 8 (Consumer Selection Model) updated: location selection is via the catalog item field constraint, not a separate /locations endpoint. Shows how filter clause on the layer_reference constraint controls which DCs appear per catalog item.

API changes: Removed standalone /api/v1/locations and /api/v1/locations/{uuid} consumer endpoints (wrong model — location is a field constraint, not a separate API). Admin API keeps /api/v1/admin/location-types and /api/v1/admin/locations (correct — admin manages the Reference Data Layer registry). Consumer API back to 61 paths.


## SECTION 88 — RESOURCE TYPE AUTHORITY + UNIFIED LAYER MODEL CLARIFICATION

**Core clarification:** All of DCM's data — Resource Type Specifications, Reference Data Layers, Service Layers, provider extension layers — is built on the same layer model with the same lifecycle, governance, ownership, and security model. This was architecturally correct but not explicitly stated.

**What was already in the architecture (confirmed, no changes needed):**
- Three-tier registry (DCM Core / Verified Community / Organization) — doc 20
- Provider as Resource Type Publisher (doc 28 section 6.1)
- Resource Type Specification vs Catalog Item distinction (doc 05 section 2.1a)
- Portability classification (universal/conditional/provider-specific/exclusive) — doc 05 section 4
- Provider-specific extension fields must be marked portability-breaking — doc 05 section 4
- Layer domain model (system/platform/tenant/service/provider) — doc 03 section 4.1
- Service Layers contributed by providers — doc 28 section 6.3
- GitOps workflow for resource type proposals — doc 20 section 3.1

**What was added (4 targeted additions):**

**1. Resource Type Authority — Stewardship Model (doc 05 new Section 2.1c):**
Every Resource Type Specification has a declared Resource Type Authority — the team responsible for defining, maintaining, evolving, and deprecating it. Same `owned_by` governance model as all other DCM artifacts. Required approver for all future version PRs. Standard authority assignments by category: Compute→Platform Team, Network→Network Ops, Storage→Storage Ops, Security→CISO, etc. Three tiers: DCM maintainers (Tier 1), named community maintainers (Tier 2), org domain teams (Tier 3).

**2. Three-Way Field Constraint Model (doc 05 new Section 3a):**
Resource Type Authorities choose per field:
- Option 1 — layer_reference: valid values are active instances of a named layer type (location, OS images, network zones). Portable. Value governance delegated to the layer type's authority.
- Option 2 — provider-declared constraint: ad-hoc enum/range in the Resource Type Spec or Catalog Item. CPU counts, memory ranges, protocol versions. Portable if values are vendor-neutral.
- Option 3 — no constraint: free-form or provider judgment. Names, descriptions, provider-internal IDs.
Decision guide table included. Key point: VM size is Option 2 or 3 by default — not layer-referenced unless the org explicitly wants a governed size catalog. This is an organizational decision, not an architectural mandate.

**3. Provider Extension Layers (doc 05 Section 6.2 extended):**
Providers can contribute extension layers (domain: provider) alongside their catalog item declaration — `provider_extension_layer_handles` field. These inject provider-specific fields during payload assembly only when that catalog item is selected. Cannot override platform/tenant layers. Same portability_breaking: true semantics as inline extensions. Resource Type Authority may adopt popular extensions as conditional fields in a future spec version.

**4. Unified Layer Model Statement (doc 03 Section 3.7 + Section 4.1):**
Explicit statement that Resource Type Specifications ARE data layer artifacts. Same lifecycle, same governance, same GitOps workflow, same authority model, same domain access control. The Resource Type Registry is a specialized layer store. All DCM data — type definitions, reference data, service configuration, provider extensions — lives in this one unified model.

**Authority vs Publisher clarification (doc 28 Section 6.1):** Resource Type Authority defines the spec; Service Provider publishes the catalog item implementing it. Often the same team. May be different: platform team defines Compute.VirtualMachine; Nutanix, VMware, and bare metal teams independently register catalog items implementing it.


## SECTION 89 — SECTION 9 EXAMPLES: RESOURCE TYPE + LAYER LIFECYCLE (dcm-examples.md)

dcm-examples.md expanded from 2,189 to 3,381 lines. Section 9 added — 8 subsections showing
the complete lifecycle of VM and WebApp resources from layer definition through rehydration.

**9.1 Layer Definitions:** Full YAML for all foundational layers — OS image (Platform Security Team),
location/DC (Data Center Operations), network zone (Network Operations), zone and country ancestor layers.
Each with complete artifact_metadata, owned_by, domain, data blocks.

**9.2 Resource Type Specifications:** Complete `Compute.VirtualMachine` v2.1.0 spec showing:
- Universal fields: cpu_count/memory_gb/storage_gb (range constraints — intrinsic), os_image/location/
  network_zone/environment (layer_reference — governed lists)
- Conditional fields: high_availability, gpu_profile (layer_reference)
- Extension point declaration for provider hypervisor config
- Application.WebApp v1.0.0 spec: app_name/tier_level (static enum — intrinsic),
  environment/location (layer_reference), web_replica_count/db_engine (range/enum).

**9.3 Provider Catalog Items:** Two providers implementing Compute.VirtualMachine:
- Nutanix EU-WEST: portable (portability_class: portable), narrows CPU/RAM enums,
  contributes Service Layer with AHV hypervisor defaults, backup policy, monitoring agent.
- VMware EU-WEST: non-portable (portability_class: provider-specific), contributes
  Provider Extension Layer with vsphere_resource_pool/datastore_cluster/vmware_tools_version.

**9.4-9.5 VM Request and Processing Pipeline:** Full 8-step trace from consumer submission through
intent capture → layer reference resolution → layer assembly (showing each contributing layer and field
provenance) → policy evaluation (Gating Policy, Validation, Transformation each shown) → placement →
requested state write (with provenance on every field) → dispatch → realized state.

**9.6 WebApp as a Service Request:** Composite Service composition: DB first, then 3 web VMs with
db_host injected from DB realization, then LoadBalancer with backend_pool injected from VM IPs.
Tier 1 Gating policies enforcing HA, minimum replicas, LTM requirement. Environment layer
injecting production defaults (backup, TTL=null, approval tier, log retention).

**9.7 VM Rehydration (DR failover DC1→DC2):** Shows location override in placement_constraints,
fresh layer resolution against DC2 layer chain (different cluster_uuid in Nutanix Service Layer),
certification gap warning (SOC 2 not at AMS-DC2), hostname preserved / FQDN updated, entity_uuid
preserved across DC move. Static Replace vs Rehydration contrast explained in pipeline steps.

**9.8 WebApp Rehydration (standards refresh — no incident):** Rolling replacement pattern for Tier 1.
Shows: retired OS image → auto-upgrade Transformation policy substitutes RHEL 9.5; environment layer
v1.2 injects new log_retention_days=365 and vulnerability scanning; new Tier 1 Gating Policy bumps
replica count 3→4; DB unchanged (no OS dependency). Full audit record showing every field change,
its source layer/policy, and version.


## SECTION 90 — DOCUMENTATION CLEANUP PASS (2026-03)

No prior implementations exist — DCM is at v1. All migration/backward-compat/update language
removed from documentation. Every doc is the authoritative first-version spec.

**Removed entirely:**
- All 38 Active Development Notice blockquotes across every data model and specification doc
- `## 7. V1 Migration` section from doc 13 — V1 concept has no basis in first implementation; `v1_migration` ingestion_source type renamed `legacy_import`; `v1_identifier` → `legacy_identifier`
- `## 7. Migration from Current Constructs` section from doc 15 (universal groups)
- `## 9. Migration Path — Standalone SPA → RHDH` from RHDH spec — replaced with clean "Deployment Options" section (standalone_spa vs rhdh are configuration choices, not migration paths)

**Reframed (concept kept, backward-looking framing removed):**
- doc 06 section 7a.6: "Updated table (supersedes 7.2)" → "Provider Lifecycle Events"
- doc 07: "dependency graph superseded by entity relationships" → scope cross-reference
- doc 08: "superseded by Universal Group Model" → "Related: see Universal Group Model"
- doc 09: "This document supersedes dependency graph concept" → plain cross-reference
- doc 13: "V1 migration and brownfield ingestion are the same" → "same ingestion model for all sources"
- doc 18: "outbound webhook superseded by Notification Model" → "one delivery channel within Notification Model"
- doc 23: "This model supersedes standalone webhooks" → "outbound webhooks are one delivery channel"
- doc 26: "Section 4 superseded by Governance Matrix" → scope statement
- doc 27: "This document supersedes Section 4 of doc 26" → cross-reference
- doc 11 (k8s): "Migration Path — Kubernetes-Native to DCM-Managed" → "Incremental Adoption"
- doc 34: "Client Migration Path" → "Version Upgrade Path"; "backward compat" → "version-compatible"; "deprecation window" → "until version is sunset"
- doc 15: "preserve backward compatibility with existing API consumers" → "for convenience"
- OIS spec: "during the deprecation window" → "until the OIS version is sunset"

**Verification:** 12 stale patterns — all clean after cleanup pass.

---

## SECTION 91 — SYNC AUDIT AND FULL RESYNC (2026-03)

Full Hugo content sync performed. State before sync:
- 5 data model docs missing from Hugo entirely (43-provider-callback-auth, 44-kessel-evaluation, 45-consistency-review, 46-workload-analysis, 47-accreditation-monitor)
- 44 of 53 data model docs stale (primarily -5 line delta from Active Development Notice removal)
- 7 specs stale (dcm-examples, dcm-registration-spec, dcm-operator-interface-spec, dcm-rhdh-integration-spec, 11-kubernetes-compatibility, consumer-api-spec, dcm-operator-sdk-api)
- Capabilities Matrix and DISCUSSION-TOPICS stale
- AI prompt had one stale matrix reference: "36 domains / 281 capabilities" (from Provider Readiness Gates session before Accreditation Monitor domain was added)

**After sync:** All 53 data model docs × 2 Hugo locations: in sync. All 14 specs: in sync. All top-level docs: in sync. AI prompt matrix refs updated to 37/287.

---

## SECTION 92 — ARCHITECTURE GAPS ANALYSIS (2026-03)

Systematic scan of all docs, schemas, and capabilities matrix. Summary:

**Tier 1 — Spec gaps (documented capability, API endpoints missing):**
- Federation Admin API (doc 22 architecture complete; no OpenAPI paths for tunnel management, peer listing, trust posture)
- Scheduled/Deferred Requests maintenance-windows endpoints (doc 37 specifies them; not in admin YAML)
- Workload Analysis endpoints (doc 46 specifies GET /workload-profile and :analyze; not in consumer YAML)
- Accreditation Monitor contract-event and :configure-webhook endpoints (doc 47; not in admin YAML)

**Tier 2 — Implementation gaps (no specification exists):**
- Cost Analysis component internal model (376 refs; no spec for how it calculates)
- Cross-region data replication model (multi-region assumed; consistency + sovereignty enforcement at replication layer unspecified)
- Secret zero / initial credential bootstrap (day-0 sequence has no spec; chicken-and-egg problem every deployer hits)
- Multi-tenancy at storage layer (row-level security, tenant-scoped encryption — not specified)
- Rate limiting implementation (policy references it; enforcement mechanics unspecified)
- Audit log hash chain implementation (tamper evidence concept documented; implementation not specified)

**Tier 3 — Security posture gaps:**
- No threat model document (attack surfaces, adversary profiles, STRIDE analysis)
- No supply chain security spec (SBOM, provider package signing, operator container provenance)
- No secrets scanning spec for GitOps stores

**Tier 4 — Experience gaps:**
- New tenant onboarding flow not specified
- Pre-request cost estimation UX not specified end-to-end
- Provider sandbox/test mode not specified
- Capacity forecasting model not specified
- SLA/SLO tracking not specified

**Two ownership ambiguities:**
- Who issues operation_uuid — API Gateway or Request Orchestrator?
- Who owns the Credential Revocation Registry?

---

## SECTION 93 — LIGHTSPEED INTERFACE CONCEPT + DISCUSSION TOPICS (2026-03)

**DISCUSSION-TOPICS.md updated:** Item 6 added — "Universal Lightspeed Interface for Operations."

Concept: a universal, high-velocity operational surface for all DCM actions regardless of provider, resource type, or lifecycle stage. Operations that currently require multiple tool hops, context switching, and approval interruptions should be expressible and executable in a single interaction.

**Key design questions captured for future roadmap:**
- New GUI surface, CLI, AI agent interface, or all three?
- How does it relate to existing Web UI spec and Flow GUI spec?
- What does "lightspeed" mean operationally — sub-second execution, zero-confirmation for pre-approved patterns, predictive pre-staging?
- How does it interact with Authority Tier model — can it auto-route approval gates without interrupting operator flow?
- Is this the primary interface for the AIOps layer referenced in the README?

**Status:** Concept only — no design work started. Future roadmap item.


## SECTION 94 — ALL ARCHITECTURE GAPS ADDRESSED (2026-03)

All gaps from Section 92 gap analysis resolved.

**Tier 1 — API Endpoint Gaps (all closed):**
- Federation Admin API: 6 new admin YAML paths including GET/POST /api/v1/admin/federation/peers, :set-trust-posture, :suspend, /routed-requests, GET/PATCH /api/v1/admin/federation/config. Schemas: FederationPeer, FederationPeerRegistration, FederationConfig.
- Scheduled Requests: 3 new admin paths for maintenance windows: GET/POST /maintenance-windows, GET/PATCH/DELETE /maintenance-windows/{uuid}, GET /maintenance-windows/{uuid}/scheduled-requests. Schemas: MaintenanceWindow, MaintenanceWindowCreate, MaintenanceWindowPatch.
- Workload Analysis: 2 new consumer paths — GET /resources/{uuid}/workload-profile, POST /resources/{uuid}/workload-profile:analyze. WorkloadProfile schema added.
- Accreditation Monitor: 3 new admin paths — :verify, :configure-webhook, /contract-event.
- Final counts: consumer 63 paths / 33 schemas; admin 57 paths / 27 schemas.

**Tier 2 — Implementation Gaps (doc 49 — 49-implementation-specifications.md, 728 lines):**
- Rate Limiting (sec 2): Token bucket at API Gateway. Per-actor bucket, profile-governed parameters (60/min minimal to 600/min prod), PT120S TTL on state. 5 policies RLM-001 through RLM-005.
- Audit Hash Chain (sec 3): SHA-256 with canonical concatenation (0x1F separator). GENESIS anchor for chain start. Continuous per-write verification + periodic sweep (PT1H sovereign, PT12H prod). Chain resealing endpoint: POST /api/v1/admin/audit/entities/{uuid}:reseal-chain.
- Multi-Tenancy at Storage Layer (sec 4): GitOps=directory namespace, EventStream=per-tenant stream, Snapshot=PostgreSQL RLS + AES-256-GCM per-tenant key, Search=index namespace. Cryptographic tenant deletion via key revocation. 4 policies STI-001 through STI-004.
- Cross-Region Replication (sec 5): Per-store replication model. Sovereignty-aware routing enforced at replication layer. Lag monitoring with degraded/unavailable state transitions. Last-write-wins + vector clocks for conflict resolution.
- Secret Zero Bootstrap (sec 6): Bootstrap manifest with internal CA + pre-shared component credentials replaced by mTLS within PT5M of CA startup. credential management service takes CA key ownership on registration. Air-gapped options: embedded vault / operator passphrase / HSM. 4 policies BOOT-001 through BOOT-004.

**Ownership Ambiguities (sec 7) — Both resolved:**
- operation_uuid: issued by API Gateway at ingress (operation_uuid == request_uuid). API Gateway writes initial Operation; Request Orchestrator updates via shared fast store.
- Credential Revocation Registry: owned by credential management service. Key: credential_uuid to revocation metadata. TTL: max(credential_ttl, P90D). Session Revocation Registry is separate — owned by Auth component.

**Tier 3 — Security Posture (sec 8):**
- Threat model: 5 boundaries (Consumer Ingress, Provider Interface, Admin, Internal Component, Storage). Highest-risk: credential management service compromise and Internal CA compromise — mitigated by air-gapped credential management service and HSM-backed CA for sovereign profiles.
- Supply chain: provider OpenAPI spec signing (mTLS private key; rejected at GATE-SP-01 if unsigned), container image provenance via Sigstore/Cosign, GitOps secrets scanning, SBOM mandatory for fsi/sovereign. 5 policies SEC-001 through SEC-005.

**Tier 4 — Experience Gaps (sec 9):**
- New Tenant Onboarding (sec 9.1): full sequence — entity, groups, quota, admin actor, Git namespace, audit stream, member invitations, onboarding_complete event.
- Pre-Request Cost Estimation UX (sec 9.2): catalog display then POST /cost/estimate with fields then dry_run: true for placement preview then actual submit.
- Provider Sandbox/Test Mode (sec 9.3): sandbox_mode: true in registration, excluded from production placement, explicit targeting via _test_context, graduation path to production.
- SLA/SLO Tracking (sec 9.4): SLO declared in Resource Type Specification (time_to_operational, uptime, drift_detection_latency), continuous measurement from audit records, breach events, consumer status endpoint, admin aggregate report endpoint.


## SECTION 95 — CONTINUED: MATRIX + SPEC CLEANUP (2026-03)

**Capabilities Matrix updated:** 38 domains / 299 capabilities (was 294).
New capabilities added from doc 49 implementation specifications:
- OBS-006: SLA/SLO Declaration (Resource Type Spec + consumer status endpoint + admin report)
- OBS-007: SLO Breach Detection and Notification
- STO-007: Cross-Region Sovereignty-Aware Replication (routing enforced at replication layer)
- STO-008: Tenant-Scoped Storage Isolation (RLS + per-tenant stream + index namespace)
- STO-009: Tenant-Scoped Encryption for fsi/sovereign (AES-256-GCM, credential management service managed)
- ZTS-007: Provider OpenAPI Spec Signing (SEC-001, mandatory at GATE-SP-01)
- ZTS-008: GitOps Secrets Scanning (SEC-002, SECRETS_DETECTED rejection)
- ZTS-009: SBOM Declaration (SEC-003, mandatory fsi/sovereign)
- PRV-010: Provider Sandbox/Test Mode
- GOV-008: Tenant Onboarding Workflow

**Admin API:** Added `GET /api/v1/admin/workload-analysis` — aggregate workload profile view across all tenants with archetype/confidence/resource_type filtering and archetype_distribution histogram. Admin API now: 57 paths / 27 schemas.

**All 15 specification docs now have Document Status headers.** 7 specs updated: cncf-strategy, consumer-api-spec, dcm-admin-api-spec, dcm-flow-gui-spec, dcm-opa-integration-spec, dcm-operator-interface-spec, dcm-registration-spec.

**Open markers: 0.** No TODO/FIXME, no Active Dev Notices, no superseded-by language, no V1 Migration references anywhere in the corpus.

**Current state:** 55 data model docs / 15 specifications / 4 OpenAPI schemas / 38 domains / 299 capabilities / 97 prompt sections.


## SECTION 96 — PROJECT OVERVIEW DOCUMENT (project-overview.md)

New canonical document added: `project-overview.md` (located at dcm-docs root and Hugo /docs/project-overview).

**Purpose:** Single authoritative description of DCM for any audience — engineers, business stakeholders, executives, or community members encountering the project for the first time. Referenced from README and Hugo navigation as the first document to read.

**Content:**
- What DCM Is: governing control plane above provisioning tools; not a deployment tool; the management plane that connects existing automation
- Architecture in one sentence + event loop diagram
- The Problem DCM Solves: 5 specific problems (fragmented ops, long TTM, private cloud gap, unreliable data, compliance overhead)
- What DCM Does: three abstractions in full — Data (4 states), Policy (7 types with table), Provider (11 types with table)
- What this enables: self-service consumer experience; standards enforced structurally
- Who Benefits: Consumers, Platform Engineers, Security/Compliance, SRE, Auditors, FinOps — each with specific value statement
- Where DCM Operates: deployment topology table (single-region/federated/hub-regional/sovereign), data sovereignty model, target environments with compliance frameworks listed
- Key Facts table: accurate current counts (55 docs, 15 specs, 299 caps/38 domains, 63 consumer paths, 61 admin paths)
- 9 Core Design Principles

**README.md updated:** Accurate counts, new project-overview link as first doc in foundation table, all doc ranges updated (55 data model docs, 15 specs), AI prompt described as 98 sections.

**Hugo updated:**
- Root _index.md: replaced thin 'About DCM' with full What/Who/Three Abstractions/Benefits layout; Active Dev Notice removed
- docs/_index.md: replaced Active Dev Notice with navigation cards including project-overview link
- architecture/overview.md: Active Development Notice removed
- /docs/project-overview.md: new Hugo page from project-overview.md


## SECTION 97 — HOW + ETHOS SECTIONS ADDED

**project-overview.md expanded** from 164 to 327 lines. Two new sections added:

**## How DCM Works** (5 subsections):
- The Event Loop: policy-driven event loop diagram showing event → Policy Engine → typed outputs → Providers/Data → new events
- The Request Lifecycle: 5-step numbered sequence from intent declaration through layer assembly, policy evaluation, dispatch, and ongoing lifecycle
- How Policy Replaces Hard-Coded Logic: why every business rule is a Policy artifact and what that means operationally
- How Providers Integrate: base contract + capability extension model; organizations wrap existing automation, not replace it
- How Data Sovereignty Is Enforced: structural property evaluated at every boundary; Governance Matrix always boolean; no scoring override

**## Ethos** (5 subsections):
- Security Is the Baseline, Not a Feature: minimal profile = security with minimal overhead, not minimal security; secure path must also be easy path
- The Governed Path Must Also Be the Easy Path: self-service is the delivery mechanism for governance; if governed path is harder, teams route around it
- Compliance Is Constructed, Not Audited: audit evidence and provenance are structural products of operations, not reconstructed post-hoc
- The Architecture Should Be Easy to Implement and Extend: three-abstraction test; no core changes for new capabilities that fit Data/Provider/Policy
- No Silent Behavior: every operation produces an observable artifact; every state transition audited; every decision has typed output

**README.md updated** with condensed How + Ethos sections: event loop summary, request lifecycle in one paragraph, four design priority ethos statements, links to full sections in project-overview.md.


## SECTION 98 — SUMMIT 2026 ROADMAP ALIGNMENT (2026-03)

Source: DCM Technical Roadmap Summit 2026 presentation (Red Hat FlightPath Team).

**Origin story from roadmap:**
- Initial inspiration: US Navy warships disconnected for months, needing consistent updates in short windows
- Summit 2025: Market gap identified for private cloud framework 'from Idea to Infrastructure'
- June 2025: Banking consortium workshop identified three needs: automated workload placement, automated DC rehydration, standards-based APIs
- Summit 2026: First public showcase of DCM Control Plane

**Three Summit demo use cases:**
1. Datacenter Rehydration — show rehydration meta process (CIO persona: restore after ransomware/90-day redeploy cycle)
2. Intelligent Placement — show business logic via policies (CTO persona: metadata-driven infrastructure placement)
3. Application as a Service — show Meta Service Provider (App Owner persona: full execution lifecycle from code)

**Three post-Summit use cases:**
1. Greening the Brownfield — discover unmanaged resources via Service Providers or CMDB import; lifecycle ownership transfer
2. New Data Center Deployment — bootstrap new DC; automated workload migration from legacy DC
3. Application Modernization — MTA integration; platform migration + code enhancement recommendations

**MVP Roadmap phases:**
- March 1: API gateway + Catalog API + policy in pipeline + data stores + initial rules (control plane core only)
- April 1: Service Catalog Web UI + Service Providers (VM, OCP Cluster, Web App, X2Ansible, Networking, Firewall) + Rehydration trigger + Placement + Consumer API + SP integration specs
- May 1: On-prem deploy + external message bus + observability + 3rd party module integration + long-term storage + IDM integration

**Demo pipeline (slide 17) maps exactly to DCM architecture:**
- App Request = Consumer POST /api/v1/requests
- Requested Store = Intent State (GitOps)
- Customize Region layer = Transformation Policy (Core Layer injection)
- Tier Region Policy (OPA Rego) = Gating Policy/Validation Policy (Mode 3 OPA)
- App Declaration = Requested State (assembled payload)
- Declared Store = Requested State Store
- Egress = Service Provider dispatch via Operator Interface
- VM Service Provider Mock API = mock Service Provider for demo

**Architecture coverage: FULL.** All three demos and all three MVP phases are architecturally specified.

**Outstanding implementation decisions (ordered by urgency):**
- Q6 (blocking): resource_uuid vs entity_uuid in Operation.metadata — must decide before code
- Q7 (blocking): expires_at (26 refs) vs valid_until (canonical) — fix before session model implementation
- Q1 (pre-March): Technology stack — recommended: NATS JetStream / custom Go API gateway / OPA sidecar / Gitea / PostgreSQL+Alembic
- Q8 (pre-March): Intelligent Placement is best March 1 demo candidate (pipeline-only, mock SP)
- Q2 (pre-April): Mock providers confirmed by slides (VM Service Provider Mock API explicit)
- Q3 (pre-April): ACM — treat as Information Provider (feeds cluster inventory), not Service Provider
- Q4 (pre-April): X2Ansible — needs resource type spec for AAP job template/workflow as DCM resource
- Q5 (pre-April): Firewall — handle as FirewallRule constituent of a Networking Composite Service
- Q9 (pre-April): RHDH vs Consumer GUI — RHDH is likely Summit target (Red Hat branding on slides)
- Q10 (pre-April): 'Data Center Pipeline' = RHDH scaffolding sitting above DCM Consumer API; consistent with RHDH integration spec


## SECTION 99 — IMPLEMENTATION DECISIONS + EXAMPLE #1 (2026-03)

**Field name decisions (final):**
- resource_uuid: KEEP (AEP standard) — Operation.metadata already correct; entity_uuid is correct everywhere else in the model
- expires_at: KEEP (valid_until replaced) — 77 refs across 20 files + 1 OpenAPI schema replaced; valid_until is now gone from corpus

**Technology stack (Red Hat sanctioned open source):**
- Event bus: AMQ Streams (Apache Kafka on OpenShift) — Kafka CR via AMQ Streams operator
- API Gateway: Custom Go service — thin, controllable for demo; Service Mesh handles mTLS
- Policy engine: OPA (Open Policy Agent) — Mode 3 sidecar + standalone Deployment for complex policies
- Git server: GitLab CE (self-hosted) — Intent Store, Requested Store, Policy Store
- Database: PostgreSQL — CrunchyData PGO operator
- Service Mesh / mTLS: OpenShift Service Mesh (Istio/Envoy) — STRICT PeerAuthentication across all namespaces
- Secret Management: HashiCorp Vault + External Secrets Operator
- Auth / IDM: Keycloak (Red Hat SSO) — OIDC; DCM Auth Provider implementation
- Observability: OpenTelemetry + Prometheus + Grafana (OpenShift Monitoring stack)
- Front End: RHDH (Red Hat Developer Hub / Backstage) + DCM plugin
- Deployment automation: Ansible Automation Platform
- Certificate management: cert-manager

**Provider decisions:**
- Real providers (not mocks) — exercises architecture portability
- VM as a Service: DCM → AAP → KVM/libvirt or OpenStack Nova
- Network Port: DCM → Netbox (IPAM) or OpenStack Neutron
- OCP Cluster: DCM → ACM Shim (Go service) → ACM API → ClusterDeployment (Hive)
- ACM also as Information Provider: feeds cluster inventory/capacity into placement engine
- Web App: Composite Service composing VM + Network Port + OCP Cluster (optional)
- X2Ansible: deferred. Firewall: deferred.

**New document: implementations/example-1-summit/IMPLEMENTATION.md** (1029 lines)
Contents:
- Purpose and scope (3 Summit demos + portability validation goal)
- Technology stack table (all Red Hat sanctioned choices)
- Architecture overview ASCII diagram (3 namespaces: dcm-system, dcm-providers, dcm-infra)
- Provider specs: VM, Network Port, OCP Cluster (ACM Shim), Web App Composite Service
- All 3 demo use case flows: Intelligent Placement, DC Rehydration, App as a Service
- Namespace + Pod design (API Gateway with OPA sidecar, Orchestrator, Policy Engine, Provider pods)
- Full OpenShift file structure (ansible/ + openshift/ + config/ directories)
- Key Kubernetes resources: Kafka topics, Istio mTLS PeerAuthentication, ExternalSecret CRs
- Configuration files: dev profile YAML, Tier Region Policy Rego (matches slide 17 exactly), VM catalog item YAML
- Ansible playbooks: site.yml master, group_vars, Kafka role task, provider registration task
- Portability notes: what changes vs what doesn't when providers are replaced
- Demo seed data: tenants, users, resource types, catalog items, Core Layers, sample policies

**Namespaces:** dcm-system (control plane), dcm-providers (all providers), dcm-infra (supporting infra)
**Deployment:** Ansible site.yml → prerequisites → infra → dcm-control-plane → dcm-providers → dcm-demo-data

## SECTION 100 — EXAMPLE IMPLEMENTATION #1 — SUMMIT DEMO (2026-03)

New artifact: `implementations/example-01-summit-demo/` — 57 files / 5,683 lines.
Labeled as Example Implementation #1. Isolated from core architecture docs.
Purpose: validate DCM architecture/data model and demonstrate portability.
Providers built here may be replaced — this is an exercise in the Provider contract.

**Implementation decisions applied:**
- `resource_uuid` in Operation.metadata (AEP convention — kept as-is, already correct)
- `expires_at` for token/session expiry (already canonical in schemas — 0 occurrences of valid_until)
- Technology: AMQ Streams (Kafka), GitLab CE, PostgreSQL (CrunchyData PGO), OPA sidecar, Keycloak, Vault, OpenShift Service Mesh, RHDH
- All Red Hat sanctioned OSS where possible

**Directory structure:**
- `openshift/` — 27 YAML manifests: namespace, RBAC, all control plane deployments, all provider deployments, storage, auth, vault, service mesh, RHDH, monitoring
- `ansible/` — 12 files: site.yml master playbook + inventory + 10 roles (operators, storage, auth, vault, service-mesh, control-plane, providers, rhdh, seed-data)
- `config/` — 13 files: PostgreSQL schema (RLS + hash chain tables), OPA policies (Rego), Keycloak realm, DCM profile/layers/catalog-items
- `docs/` — 5 files: README, ARCHITECTURE mapping, deployment guide, demo script, provider dev guide

**Control plane (8 Go services, each a separate container/Deployment):**
dcm-api-gateway, dcm-request-orchestrator, dcm-policy-engine, dcm-placement-engine, dcm-request-processor, dcm-audit, dcm-catalog, dcm-discovery

**Storage stack:** PostgreSQL (Snapshot Store + Operations + Audit), GitLab CE (GitOps Store), AMQ Streams/Kafka (Event Stream), OpenSearch (Search Index)

**Service Providers (5):**
- dcm-provider-vm: wraps AAP/Ansible for VM provisioning (OIS Level 2)
- dcm-provider-ocp-cluster: wraps RHOCP/CAPI (OIS Level 2)
- dcm-provider-network: wraps AAP for network ports/VLANs (OIS Level 2)
- dcm-provider-acm-shim: shim wrapping ACM API as standard DCM provider; ClusterRole grants ACM ManagedCluster/Placement/ManifestWork access
- dcm-provider-webapp: Service Provider that registers a Composite Service composing VM + Network + OCP Cluster (OIS Level 1; sequential with rollback)

**OPA Rego policies (Summit demo):**
- tier-region.rego: Gating Policy (compliance) — enforces zone ⊆ tier allowed zones. Matches slide 17 demo exactly.
- vm-sizing.rego: Validation (structural) — CPU/RAM/storage bounds by environment
- placement-weights.rego: Transformation — 5-signal scoring (capacity 35%, affinity 10%, cost 20%, perf 20%, risk 15%)

**Security posture:**
- STRICT mTLS via OpenShift Service Mesh across all components (Boundary 4)
- Per-component ServiceAccounts with minimum RBAC
- Vault: per-provider policies (vm provider can only read dcm/data/providers/vm/*)
- PostgreSQL RLS: dcm_app role cannot query across tenant boundaries
- Keycloak PKCE for RHDH consumer authentication
- Audit records: append-only enforced by SQL trigger + REVOKE UPDATE/DELETE

**Demo script covers 3 use cases:**
1. Intelligent Placement (March 1): tier-region.rego enforces zone policy; pipeline visible in RHDH
2. Datacenter Rehydration (April 1): simulate DC loss; :rehydrate endpoint replays Intent through current policies
3. Application as a Service (April 1): single request → webapp Composite Service is dispatched by DCM as Network + VM + OCP Cluster in dependency order

**Deploy single command:** `cd ansible && ansible-playbook site.yml -i inventory/hosts.yml`
**BOOT-002:** Bootstrap admin password CHANGE_ME_BOOT002 must be rotated on first login.


## SECTION 101 — FULL SYNC COMPLETE (2026-03)

Complete documentation sync performed. All artifacts now in sync.

**Current corpus state:**
- Data model: 55 documents (00-foundations through 49-implementation-specifications + A-provider-contract + B-policy-contract)
- Specifications: 15 documents (all with Document Status headers)
- OpenAPI schemas: consumer 63 paths/33 schemas, admin 57 paths/27 schemas, operator 5 paths/12 schemas, callback 7 paths/11 schemas
- Capabilities Matrix: 38 domains / 299 capabilities (verified: summary count matches row count)
- AI Prompt: 103 sections, 0 duplicates
- Open markers (TODO/FIXME/Active Dev Notice/superseded-by/V1 Migration): 0
- Example Implementation #1: 57 files / 5,683 lines

**Hugo website state (fully synced):**
- /docs/data-model: 55 files
- /docs/architecture/data-model: 109 files (55 source + 54 duplicates from earlier build — source is /docs/data-model)
- /docs/architecture/specifications: 24 files (15 specs + 4 OpenAPI YAMLs + indexes)
- /docs/implementations/example-01-summit-demo: 5 pages (README, architecture mapping, deployment guide, demo script, provider dev guide)
- Active Development Notices: removed from all files (3 remaining instances cleared in this sync)
- Navigation: root _index, docs _index, architecture _index, implementations _index all updated with current content

**README.md (135 lines):** accurate counts, implementation section added, AI prompt section count updated to 103.

**project-overview.md (328 lines):** accurate counts, reference implementation entry added to Key Facts table.

**DISCUSSION-TOPICS.md:** 6 items including Lightspeed Interface concept (item 6) and Kessel evaluation (item 4).

**Implementation status:** Example #1 fully specified. Architecture fully ready for implementation. Remaining pre-coding decisions: event bus tech, API gateway tech, policy engine runtime, Git server — all documented in prompt section 99 (Summit Roadmap Alignment). All field names resolved (resource_uuid per AEP, expires_at for token expiry).


## SECTION 102 — WORKING INSTRUCTIONS FOR AI MODELS

When working on this project, apply these instructions in addition to the numbered guidance in SECTION 60 (Documentation Structure):

172. **DCM defaults to federated data creation** — platform admins are not the only contributors; consumers author tenant-domain policies; providers publish resource type specs and service layers; peer DCMs contribute registry entries; all via GitOps PR with profile-governed review
173. **Contributor domain scope is hard DENY at submission** — consumers cannot contribute system/platform policies regardless of declared domain; providers cannot contribute specs for types they don't offer; enforced by Governance Matrix at contribution time (FCM-002)
174. **All contributed policies enter shadow mode by default** — proposed status with shadow evaluation before activation; shadow_review_period is profile-governed (P7D standard → P30D fsi/sovereign); platform admin reviews divergence cases before promoting
175. **Orphaned artifacts do not auto-deactivate** — when contributor's access is revoked, their active artifacts remain active until platform admin assigns new owner or explicitly retires; exception: sovereign profile auto-retires orphaned artifacts (FCM-006)
176. **Gating Policy enforcement_class is required and fail-safe** — if omitted, treated as compliance (boolean deny). Operational-class Gating Policies never halt the request; they contribute a weighted risk_score_contribution to the aggregate. The aggregate risk score determines approval routing, not individual policy outcomes.
177. **Validation output_class is required and fail-safe** — if omitted, treated as structural (boolean halt). Advisory-class Validations never halt requests; they accumulate completeness score and warning list surfaced to the consumer.
178. **Governance Matrix is always boolean — never scored** — SMX-004 is absolute. Scoring cannot be used to route around data sovereignty or regulatory boundaries. The Governance Matrix evaluates before the scoring pipeline runs.
179. **Profile thresholds determine routing, not individual policies** — the approval routing decision (auto/review/dual/authorized) emerges from the aggregate risk score crossing profile-configured thresholds, not from individual policy flags. Changing governance sensitivity = adjusting thresholds in the profile.
180. **SMX-008 is a hard system constraint** — auto_approve_below may never exceed 50 in any profile. Platform admins cannot override this. Profiles submitted with auto_approve_below > 50 fail validation.
181. **A Composite Service is a composition definition fulfilled by a registering Service Provider** — not an orchestrator. The registering provider declares the dependency graph so DCM can place, sequence, and govern constituents. For `self` constituents it executes as any Service Provider does. DCM handles all orchestration, placement, failure, and compensation.
182. **Composite Entity has ONE entity UUID** that links Intent, Requested, Realized, and Discovered states; the UUID is assigned at Intent creation and is stable throughout the lifecycle including rehydration
183. **DEGRADED is a valid terminal state** — not an error; a DEGRADED entity enters standard OPERATIONAL lifecycle; profile governs whether degraded delivery is accepted; Recovery Policy governs failure/compensation decisions
184. **Parallelism emerges from the dependency graph** — constituents with no unresolved dependencies dispatch concurrently within DCM's pipeline; the registering provider does not manage this
186. **Credential values are NEVER stored in DCM** (CPX-001) — only metadata is stored; values are held by the credential management service; retrieved via authenticated endpoint; this applies to ALL credential types including dcm_interaction credentials
187. **Every provider dispatch requires a scoped interaction credential** (CPX-002) — issued before dispatch, scoped to the specific operation+entity+provider, expires PT15M; provider must validate at use time not just receipt; check revocation cache on each use
189. **Security properties are present in ALL profiles — minimal profile is "security with minimal operational overhead" not "minimal security"** — rotation required in all profiles (minimal: P365D max, manual OK); idle detection on in all profiles (minimal: P30D); algorithm baseline in all profiles (minimal: forbidden list); CPX-001 (values never in DCM stores) is absolute — homelab (minimal) uses bearer_token retrieval, no scheduled rotation, no FIPS; sovereign uses mtls+hardware attestation, FIPS Level 3, PT15S revocation cache; same API contract, same data model, same CPX-001 (values never in DCM stores)
196. **API versioning is per-surface not per-endpoint** (VER-001) — Consumer, Admin, Provider/OIS, Flow GUI each have their own major version; all endpoints within a surface share the version; when in doubt whether a change is breaking, it is (VER-002); prod support window is 2 years deprecated after 1 year notice; sovereign is 4 years deprecated after 2 years notice; deprecated versions return Deprecation + Sunset headers (RFC 8594/RFC 9745)
197. **Consumer API has 16 sequential sections (reorganized)** — sections were renumbered 1–16 in logical order: Auth(2), Catalog(3), Requests(4), Resources(5), Drift(6), Groups(7), Approvals(8), Cost(9), Notifications(10), Search(11), Audit(12), Errors(13), Contributions(14), Credentials(15), Conformance(16); old 5b/5c/6b/7b numbering is gone
198. **Admin API base URL is /api/v1/admin/ (version-first)** — NOT /admin/api/v1/; all 40 admin endpoints use /api/v1/admin/; this is the authoritative form used everywhere in the specs and data model docs
199. **Consumer API has idempotency (1.5), rate limiting (1.6), request IDs (1.7), and standard envelope (1.8)** — POST requests support Idempotency-Key header (PT24H retention); rate limits are profile-governed (60/min minimal → 600/min sovereign) with Retry-After on 429; all list responses use {"items":[...],"total":N,"next_cursor":"..."} envelope; X-DCM-Request-ID and X-DCM-Correlation-ID on all responses
200. **OIS health check response is normative (not optional)** — providers MUST return {status: pass|warn|fail, version, dcm_registration_status}; missing/malformed body = warn; 3 consecutive non-200 = provider.unhealthy event; response format follows RFC 8615 / IANA health+json
201. **Doc 35 (35-session-revocation.md) is complete** — session lifecycle: intent→requested→realized store model; AUTH-016 (deprovisioning revokes sessions AND credentials in parallel); AUTH-017 (revocation SLA: PT5M minimal → PT5S sovereign); AUTH-018 (ALL components check revocation registry on every bearer token request — no exceptions); AUTH-019 (emergency revocation = critical urgency, non-suppressable); AUTH-020 (introspection endpoint authenticated); AUTH-021 (oldest session revoked on concurrent limit breach); AUTH-022 (refresh tokens invalidated on parent session revocation); session endpoints: DELETE /api/v1/auth/session, DELETE /api/v1/auth/sessions, GET /api/v1/auth/sessions, DELETE /api/v1/auth/sessions/{uuid}; admin: POST /api/v1/admin/actors/{uuid}/revoke-sessions
202. **Doc 36 (36-internal-component-auth.md) is complete** — ICOM-001 (all internal calls mTLS); ICOM-002 (scoped interaction credential required IN ADDITION to mTLS on every call); ICOM-003 (unauthorized source → 403 + audit); ICOM-004 (components may only call declared allowed_targets); ICOM-005 (all internal calls audited); ICOM-006 (P90D max cert validity); ICOM-007 (bootstrap tokens one-time-use, PT1H max); ICOM-008 (compromised cert → CRL immediately); ICOM-009 (Internal CA root in all trust stores at deploy); component communication graph is declared and enforced — not implicit; every call: mTLS cert (transport identity) + ZTS-002 interaction credential (operation authorization)
203. **Session revocation and internal component auth complete the zero trust model** — external boundary: provider↔DCM uses mTLS + scoped credentials (CPX-001–CPX-012); internal boundary: component↔component uses Internal CA mTLS + ZTS-002 interaction credentials (ICOM-001–ICOM-009); actor sessions: Auth Provider issues tokens; Session Revocation Registry checked on every request (AUTH-018); credentials: credential management service manages values that never touch DCM stores (CPX-001); together these four surfaces cover the complete trust boundary

201. **35-session-revocation.md (AUTH-016–AUTH-022)** — session revocation and credential revocation are PARALLEL on actor deprovisioning (not sequential); revocation registry must be checked on EVERY request by ALL components; sovereign profile: no revocation registry cache; emergency revocation (security_event) is critical urgency + non-suppressable; refresh tokens are invalidated when parent session is revoked (AUTH-022)
202. **36-internal-component-auth.md (ICOM-001–ICOM-009)** — network position grants ZERO trust for internal calls — same five-check boundary model as external; every internal call requires BOTH mTLS cert AND ZTS-002 interaction credential; bootstrap tokens are one-time-use PT1H max; unauthorized source component → 403 + high-urgency audit; component certs from Internal CA only, max P90D, never external CA
203. **SES and ICOM domains added to capabilities matrix** — matrix is now 177 capabilities across 28 domains; SES-001–SES-005 (session lifecycle, deprovisioning, emergency revocation, introspection, concurrent enforcement); ICOM-001–ICOM-005 (mTLS, bootstrap, call authorization, interaction credentials, cert revocation)
204. **Domain prefix totals now 28** — IAM CAT REQ PRV LCM DRF POL LAY INF ING AUD OBS STO FED GOV ACC ZTS GMX DRC FCM SMX MPX CPX DPO ATM EVT VER SES ICOM; README and taxonomy both updated to 177/28
205. **Doc 37 (Scheduled Requests): dual policy evaluation** — Gating Policy runs at declaration AND at dispatch; dispatch-time rejection = FAILED not retried; schedule field is optional addition to existing POST /api/v1/requests body; SCHEDULED status is cancellable; not_after deadline miss = terminal FAILED (SCH-005)
206. **Doc 38 (Request Dependency Graph): distinct from type-level and Composite Service deps** — consumer-declared ad-hoc ordering for independent requests; POST /api/v1/request-groups; PENDING_DEPENDENCY status counts against quota at submission not dispatch; max 50 requests per group; circular deps → 422 at submission; field injection passes realized outputs into dependent request fields automatically
207. **Doc 39 (DCM Self-Health): three endpoints, different purposes** — /livez (liveness, PT5S max, no external calls, Kubernetes restarts pod on fail) vs /readyz (readiness, checks 5 core dependencies, Kubernetes removes from LB) vs /api/v1/admin/health (per-component detail, admin auth required, Prometheus metrics at /metrics); all follow RFC 8615 / IANA health+json
208. **Capabilities matrix now 189 across 31 domains** — SES(5) ICOM(5) SCH(4) RDG(4) HLT(4) added; domain prefixes: IAM CAT REQ PRV LCM DRF POL LAY INF ING AUD OBS STO FED GOV ACC ZTS GMX DRC FCM SMX MPX CPX DPO ATM EVT VER SES ICOM SCH RDG HLT (31 total)
209. **40-standards-catalog.md is the authoritative source for all DCM standards** — forbidden algorithms (MD5, SHA-1, DES, 3DES, RC4, RSA<2048) are prohibited in ALL profiles with no exceptions; TLS 1.0/1.1 prohibited in ALL profiles; ECDSA P-384 is the mandated algorithm for Internal CA certs; AAL mapping: minimal/dev=AAL1, standard/prod=AAL2, fsi=AAL2+, sovereign=AAL3; doc 40 Section 8 maps every standard to the docs that use it
209. **External CAs belong in the credential management service (NOT Auth Provider)** — Auth Provider authenticates identity; credential management service manages credential lifecycle; External CAs (Vault PKI, Venafi, EJBCA, AWS ACM PCA) are x509_certificate credential management services using ACME(RFC 8555)/EST(RFC 7030)/SCEP/CMP protocols; ICOM-009 updated — trust anchor is any registered CA root, not just built-in Internal CA; doc 36 profile table: cert lifetime P180D(minimal) → P14D(sovereign); sovereign requires HSM-backed certs if hardware_attested posture
210. **Live updates: SSE stream + OIS interim status** — GET /api/v1/requests/{uuid}/stream (text/event-stream, closes on terminal status) for browser/CLI without polling; events: status_change, progress_updated, approval_required, approval_recorded, heartbeat(30s); OIS providers POST /api/v1/provider/entities/{uuid}/status for interim progress with step_current/step_total/constituent_status; request.progress_updated event added to doc 33; rate-limited: max 1 interim status per 10s per entity
211. **Profile coverage added to docs 36-39** — doc36 cert lifetime table(P180D minimal→P14D sovereign), algorithm min table; doc37 max scheduling horizon(P365D minimal→P7D sovereign), concurrent scheduled limit, maintenance window approval tier; doc38 max group size(100 minimal→5 sovereign), group timeout max, field injection validation strictness, nesting depth; doc39 metrics scraping restrictions(sovereign internal only), /api/v1/admin/health MFA requirements(fsi/sovereign)
212. **40-standards-catalog.md is the authoritative standards reference** — 19 RFCs, 3 cryptographic standards tables (permitted algorithms, forbidden algorithms, FIPS levels), 6 compliance frameworks, 7 CNCF ecosystem projects, W3C SSE, OpenAPI 3.1, SPIFFE (informative), HashiCorp Vault PKI / Venafi / EJBCA as External CA credential management service backends (NOT Auth Providers); Section 9 maps all 17 policy families to their standards basis; usage map tracks which standards appear in which documents
213. **41-operational-reference.md covers the three operational gaps** — GitOps partitioning (3 strategies; tenant-shard recommended; trigger thresholds table), store migration (5-phase dual-write playbook; never decommission source before burn-in; audit chain continuity required OPS-002), DR (5 scenarios; post-recovery validation checklist mandatory OPS-005; Audit Store minimum P365D retention all profiles OPS-006); RTO: PT1M sovereign component → PT24H minimal repave
214. **Three GUI specs define the unified DCM web application** — one application with role-gated surfaces: Consumer Portal (all actors — catalog, SSE live status with constituent tracking, resources, approvals, cost, sessions), Admin Panel (platform roles — health dashboard, tier registry drag-drop editor with hard-stops, scoring slider max 50), Provider Management (provider_owner role — 5 provider types with common shell + type-specific tabs; Credential management shows metadata never values; algorithm compliance must show zero forbidden algorithm violations)
215. **Doc 42 adds 12th provider type (ITSM integration) and 8th policy type (ITSM Action Policy)** — ITSM is ADDITIVE (DCM never requires it); ITSM Action Policy is side-effect only (non-blocking default); block_until_created requires block_timeout (never permanently stalls pipeline, ITSM-005); recorded_via field already existed on approval vote — ITSM inbound approvals use it; 6 policy examples covering ServiceNow + Jira for provisioning, CMDB sync, incident on drift, decommission; itsm.* event domain adds 3 events (85 total, 21 domains)
215. **Consumer GUI ITSM bridge (GUI-011, section 8 of dcm-consumer-gui-spec.md)** — ITSM is a CONSUMER of DCM events, not a source of truth; DCM is the system of record; CMDB sync is one-way DCM→CMDB via notification service subscription to entity.* events; ITSM approval votes call POST /api/v1/admin/approvals/{uuid}/vote — the CAB process happens in ITSM, DCM just records the outcome; ITSM references stored as business data fields on entities; Audit Trail (section 11) is consumer-scoped own-resource view; cross-tenant audit is Admin Panel only
215. **RHDH/Backstage is the PRIMARY consumer GUI deployment model** — 6 Dynamic Plugin packages (no RHDH rebuild); Scaffolder IS the request form (auto-generated templates from catalog item JSON Schema); DCMService + DCMResource entity kinds sync to RHDH catalog every PT5M; tenancy via RHDH Group context → X-DCM-Tenant; OIDC token exchange for auth delegation; PatternFly NavGroup/NavItem/NotificationBadge for sidebar; Approvals shows live pending count badge; all compliance enforced by DCM control plane — RHDH is a client
195. **33-event-catalog.md is the SINGLE authoritative source for all DCM event types** — 82 events across 26 domains; all events share the base envelope (event_uuid, event_type, event_schema_version, timestamp from Commit Log, urgency, payload, links); consumers implement idempotency using event_uuid; critical urgency events are non-suppressable; non-standard events use reverse-DNS prefix; event_schema_version only increments on breaking changes
194. **Tier registry changes are gated by impact detection** — any change that creates a SECURITY_DEGRADATION (tier gravity or position decreased) blocks activation until each degradation is explicitly accepted by a verified-tier or above reviewer via Admin API; BROKEN_REFERENCE also blocks; PROFILE_GAP is a warning that does not block; all changes produce an impact report in the Audit Store (ATM-009–012)
193. **Authority tiers are named positions in an ordered list — not fixed enum values** — tier weight derived from list position at evaluation time; organizations insert custom tiers between existing ones without breaking existing name references; 'authorized' tier always means 'highest current gravity' regardless of what's been inserted before it; ATM-001: never hardcode tier weights
192. **DCM provides the approval gate and audit trail — the review process is the organization's responsibility** — for authorized tier: DCM tracks quorum of a DCMGroup; the authorized deliberation and vote collection happen outside DCM; external systems (ServiceNow, Jira, Slack bots) can call Admin API to record votes; DCM does NOT build authorized management; for reviewed and verified: same principle — DCM holds the pipeline until the API receives the required decisions
191. **The priority order is a decision framework, not a suggestion** — when security and ease of use conflict, security wins AND you must design an easy mechanism for the secure path; "it's too complex" is a reason to improve the ease-of-use design, not to reduce security; "minimal profile" means minimal overhead, never minimal security (DPO-005, DPO-006)
190. **key_usage is declared at issuance and validated at use** (CPX-009) — a credential issued for authentication cannot be used for signing; credential management service must validate this at the validate endpoint; prevents algorithm confusion attacks
188. **Actor deprovisioning and entity decommissioning trigger immediate credential revocation** (CPX-006, CPX-007) — deprovisioning publishes revocation events before the deprovisioning is acknowledged; decommission is blocked until all entity-scoped credentials are revoked
185. **provided_by: external constituents are placed by DCM's Placement Engine** — all governance controls (sovereignty, accreditation, trust) apply; the Composite Service definition has no influence over external constituent provider selection

---

## Session: Architecture Consistency and Policy Model (April 2026)

**Summary:** Infrastructure consolidated to 1 required dependency (PostgreSQL). Auth, secrets, and events handled internally by default with optional external delegation. Policy evaluation model expanded with Evaluation Context, Constraint Type Registry, and Policy Templates. Full consistency pass across all 58 data model docs and 15 specifications.

216. **One required infrastructure: PostgreSQL** — Authentication (local accounts + argon2id + DCM-issued JWT), secrets (envelope encryption with AES-256-GCM + KEK from environment), and event routing (LISTEN/NOTIFY) are all handled internally. External systems (OIDC IdP, Vault, Kafka, Redis, Git, service mesh) are optional deployment enhancements registered through the standard provider contract.

217. **Internal/External pattern applied three times** — Policy evaluation (Internal: OPA evaluates; External: external provider evaluates). Secrets management (Internal: PostgreSQL secrets table + envelope encryption; External: Vault-compatible API). Authentication (Internal: actors table + argon2id + JWT; External: auth_provider — OIDC, SAML, LDAP). Same pattern, consistent across all three domains.

218. **Data-driven policy matching** (doc B §2) — A policy fires when the data says it should fire. Any field from three sources (request payload, evaluation context, entity metadata) can be a match trigger. No pre-assignment of policies to resource types. Specificity ranges from universal (no conditions) to fully scoped (VMs in DMZ in zone A for application UUID XXXXX).

219. **Evaluation Context with multi-pass convergence** (doc B §7) — Transient constraint space scoped to one request evaluation. Three phases per pass: collect constraints, resolve conflicts, apply and validate. Hard/soft constraint binding. Auto-resolution via declared `on_conflict` strategies. Maximum 3 passes (configurable). Unresolvable hard-hard conflicts escalate to human. Per-pass audit captures complete context snapshots.

220. **Constraint Type Registry** (doc B §8) — Shared vocabulary for the Evaluation Context. Each constraint type has a canonical name, OpenAPI v3 schema, emittable_by/consumable_by declarations. 10 built-in types (zone_restriction, distribution_requirement, cost_ceiling, network_restriction, resource_limits, compliance_requirement, sovereignty_boundary, approval_requirement, scheduling_constraint, provider_restriction). Organizations register custom types. Validation at policy activation catches vocabulary mismatches at authoring time.

221. **Policy Templates** (doc B §9) — Gatekeeper ConstraintTemplate pattern adapted for DCM. Templates define reusable Rego logic with parameter schemas and declared emitted/consumed constraint types. Policy artifacts are instances binding parameters and match conditions. DCM auto-generates `data.dcm.constraint_types` Rego library from the Constraint Type Registry — constructor functions enforce schemas at compile time.

222. **Doc 11 rewritten** as "Data Store Contracts" (791→154 lines) — Enforcement rules for the four PostgreSQL data domains (append-only, RLS, hash chain, REVOKE grants). No storage provider abstraction.

223. **Doc 31 rewritten** as "Credential Management" (979→154 lines) — Internal secrets via PostgreSQL envelope encryption (default). External via Vault-compatible API (optional). Consumer-facing credentials handled by service_provider with Credential.* resource types.

224. **Doc A §7 rewritten** as 5 provider types (556→387 lines) — Removed Storage, Policy, Credential, Notification, Message Bus, Registry, ITSM as separate types. Added Process Provider (ephemeral workflow execution). Service Provider description updated to cover Credential.*/Notification.*/ITSM.* resource types.

225. **Doc 14 §4 rewritten** — "External Policy Evaluators" (4 modes) → "Policy Evaluation Modes" (Internal/External). BBQ-001–009 governance preserved for External mode. Mode numbering removed.

226. **Doc 02 §4 rewritten** — "data store Model" (old terminology) → "Data Domain Model" with PostgreSQL table enforcement. Git as optional ingress adapter, not a state store.

227. **Capabilities matrix updated** — 309→331 capabilities. Added: POL-008 (Constraint Type Registry), POL-009 (Evaluation Context), POL-010 (Policy Templates), POL-011 (DCM Constraint Types Library), POL-012 (Data-Driven Matching), STO-010 (Internal Secrets), STO-011 (Pipeline Event Routing), STO-012 (Internal Authentication). Domain 13 (Storage) rewritten for PostgreSQL. Domain 23 renamed to Credential Management.

228. **Bulk consistency pass** — Zero old provider type references remain outside AI prompt historical sections. Zero old store model references. Zero old policy mode references (Mode 3/4) in policy contexts (information provider retrieval modes correctly retained). All "3 required infrastructure" / "Vault required" / "Keycloak required" references updated.

229. **Unified audit and payload integrity via Merkle tree** (doc 16 §8) — RFC 9162 (Certificate Transparency v2.0) pattern. Each audit record is a Merkle leaf with input/output payload hashes, service signature, and tree position. Inclusion proofs (O(log n)), consistency proofs, and request chain verification unify audit trail integrity and payload chain of custody into one mechanism. Satisfies NIST 800-53 AU-9(3), AU-10(2/3/5), SI-7; FIPS 186-5 (Ed25519); FedRAMP High AU-10.

230. **Configurable audit granularity** (doc 16 §8.1) — Three levels: `stage` (~6 leaves/request — one per pipeline stage), `mutation` (~15-30 leaves — one per layer merge, policy evaluation, constraint resolution), `field` (mutation + per-field old/new value hashes). Profile defaults: minimal/dev → stage, standard/prod → mutation, fsi/sovereign → field (minimum, cannot downgrade). Inter-stage verification: synchronous (fsi/sovereign required), asynchronous, or disabled (homelab).

231. **Lifecycle-scoped policy evaluation** (doc B §2.2–2.3) — 10 lifecycle operation types: initial_provisioning, update, scale, rehydration, decommission, ownership_transfer, subscription_renewal, drift_remediation, provider_migration, compliance_rescan. Each policy declares `lifecycle_scope` specifying which operations trigger it. `changed_field_filter` enables policies to fire only when specific fields change on update/scale operations (e.g., placement policies skip memory-only changes, sovereignty fires on zone/provider changes). Profile-governed minimums: fsi/sovereign require sovereignty and Gating policies on ALL lifecycle operations — cannot be scoped down.

232. **Policy Override Model** (doc B §18) — Five override mechanisms organized by severity: Override Policy (planned exceptions, full lifecycle, cannot target hard policies), Exception Grant (pre-authorized time-bounded waiver with compensating controls, dual-approval for hard), Manual Override (immediate single-request authorization, dual-approval for hard), Dual-Approval Escalation (required modifier for hard policy overrides — two individuals from different roles), Compensating Control Substitution (satisfy policy intent through different mechanisms without actually overriding). Every override produces a Merkle tree audit leaf. Profile-governed: fsi/sovereign require dual-approval on ALL overrides.

233. **Test Framework Specification** (doc 52) — Automated self-reflecting test framework for data model and architecture validation. Generate→Execute→Verify→Analyze→Enhance loop. Machine-readable architecture summary (YAML) covering all fundamentals: 4 data domains, 5 provider types, 10 lifecycle operations, 8 policy types, 5 override mechanisms, 3 audit granularity levels. 56 named invariants across 7 categories: MATCH (7), EVAL (8), OVRD (9), LSCOPE (4), DATA (3), MRKL (6), RLS (3), PROV (7). Edge case categories: policy interaction (7 scenarios), provider (5), data integrity (5), lifecycle (5). Framework outputs enhancement proposals when gaps are discovered.

234. **Override Approval Flow** (doc B §18.8) — When a policy blocks a request and no automatic resolution exists (no active override policy, exception grant, or compensating control), the request enters PENDING_OVERRIDE status. DCM publishes `override.required` event. Notification routing delivers to eligible approvers via internal (LISTEN/NOTIFY → Consumer Portal) and external (webhook to ServiceNow/Jira/Slack) channels. Approver(s) act via Admin API (`POST /api/v1/admin/overrides/{request_uuid}/approve`). For dual-approval: first approval recorded, second notification sent, pipeline held until both arrive or timeout. On approval: pipeline resumes from blocked stage with override injected into Evaluation Context. On timeout: request fails with OVERRIDE_TIMEOUT. Timeout is profile-governed (minimal/dev: PT24H, standard/prod: PT4H, fsi/sovereign: PT1H). `override_requests` table (18th SQL table) stores the complete approval record.

235. **Override events and API** — 5 new events (override.required, override.first_approval, override.approved, override.rejected, override.expired) bring total to 109 event payloads across 23 domains. 4 new Admin API endpoints (list/get/approve/reject) bring admin paths to 61.

236. **Policy Block Resolution** (doc B §18.8) — When a policy blocks a request and no automatic resolution exists, DCM does NOT silently enter an override queue. The request enters POLICY_BLOCKED status and the consumer is notified with actionable guidance: what blocked the request, why, compliant values to fix it, and four resolution options (modify request to be compliant, request override, cancel request, escalate to platform admin). Resolution guidance includes per-field suggestions derived from the blocking policy's constraint output. Consumer acts via `POST /api/v1/requests/{id}:resolve`. Only the "request override" option triggers the override approval flow (§18.9). This is the consumer-facing experience — §18.9 is the admin-facing approval mechanism.

237. **Override approval is one resolution option, not the default** — The pipeline flow is: POLICY_EVALUATION → POLICY_BLOCKED (consumer notified with options) → consumer chooses action → if modify: re-enters pipeline from assembly → if request_override: PENDING_OVERRIDE → approval flow → if cancel: CANCELLED → if escalate: platform admin notified. Two separate timeouts: block timeout (how long before auto-cancel) and override timeout (how long approvers have). Both profile-governed.

## SECTION 103 — APRIL 2026 SESSION: ADRs, WALKTHROUGH, PATTERN CATALOG, REQUIREMENTS (2026-04)

### 103.1 Architecture Decision Records (Rewritten)

16 ADRs in `architecture/adr/`, rewritten to answer "why does this exist?" not "how did we implement it?":

| ADR | Title | One-Line |
|-----|-------|---------|
| 001 | Why DCM Exists | Unified management plane for on-prem — governance layer above provisioning tools |
| 002 | Three Foundational Abstractions | Everything is Data, Provider, or Policy |
| 003 | Four Lifecycle States | Intent → Requested → Realized → Discovered, immutable, linked by entity_uuid |
| 004 | Service Catalog & Consumer UX | Four-level hierarchy; consumers declare what, not how |
| 005 | Provider Abstraction | 6 types with naturalization/denaturalization; any platform, same interface |
| 006 | Policy Engine | Policy-as-code on every request; 8 types; multi-pass convergence |
| 007 | Placement Engine | Multi-stage scoring: sovereignty pre-filter → capability → capacity → policy |
| 008 | Dependency Resolution | Type-level deps → automatic sub-requests; binding fields inject runtime values |
| 009 | API Gateway & Control Plane | Single entry point; 9 services; deterministic pipeline |
| 010 | Audit & Tamper Evidence | Merkle tree (RFC 9162); configurable granularity; provable integrity |
| 011 | Sovereignty & Data Residency | First-class enforcement on every lifecycle op; dual-approval for overrides |
| 012 | Data Assembly & Layering | Organizational data merges with consumer requests; field-level provenance |
| 013 | Override & Exception Governance | 5 mechanisms from planned exceptions to dual-approval |
| 014 | Multi-Tenancy & Isolation | PostgreSQL RLS at database layer |
| 015 | Minimal Infrastructure | PostgreSQL only required dep; Internal/External delegation for everything else |
| 016 | Application Definition Language | **OPEN** — How should consumers define multi-resource apps? 4 options under evaluation |

ADR-016 is the key open design question raised by the engineering team (Ondra/machacekondra). Options: API-only, YAML manifests, external DSL (Bicep/CEL), API composition. Comparison to Radius and KRO included. Decision pending team discussion.

### 103.2 End-to-End Walkthrough

`architecture/WALKTHROUGH.md` — 581 lines, 11 stages tracing a VM provision including IP dependency resolution:

1. Consumer submits intent (6 fields)
2. Layer assembly (5 layers merge → 10+ fields with provenance)
3. Policy evaluation (Gating Policy, Validation, Transformation — 4 policies)
4. Dependency resolution (VM requires Network.IPAddress → sub-request created)
5. IP policy evaluation (sovereignty, subnet isolation, pool selection — 4 policies)
6. IP realization (InfoBlox IPAM allocates 10.1.45.23)
7. Dependency injection + VM placement (IP injected, providers scored)
8. VM dispatch (naturalization to OpenStack Nova with pre-allocated IP)
9. VM callback (denaturalization, realized state)
10. Discovery (both VM and IP independently polled, drift comparison)
11. Audit trail (17 Merkle leaves across 2 entities)

### 103.3 Deployment Pattern Catalog

Patterns are composite Resource Type Specifications — reusable, provider-agnostic blueprints that define collections of resources with dependencies and binding fields. The Pattern Catalog is NOT a new architectural component — it is a curated view of the Resource Type Registry filtered to composite types. All existing DCM machinery (Composite Services, dependency graphs, binding fields, placement) executes patterns.

Example patterns: Standard Web Application (6 constituents), Secure Data Pipeline, Developer Sandbox, Regulated Database Service, Edge Compute Node.

Pattern interaction with DCM features: each constituent independently policy-evaluated, independently placed, independently discoverable for drift, independently auditable. Decommission reverses dependency order. Rehydration rebuilds in dependency order with current policies.

### 103.4 Platform Requirements Document

`dcm-platform-requirements.md` — 700 lines following enterprise requirements template:
- 5 personas (Consumer, Platform Engineer, Operator, Policy Owner, Administrator)
- 31 use cases in summary table, 23 with detailed descriptions
- Organized by lifecycle: Day 0 (5 UCs), Day 1 (5 UCs), Day 2 (4 UCs), Governance (2 UCs), Platform Ops (3 UCs), Federation (1 UC), Integration (1 UC), Pattern Catalog (1 UC + full overlay)
- Architecture principles, success outcomes, priority summary (16 P0, 9 P1, 6 P2)
- 4 open design questions documented

### 103.5 PR Reviews

**PR #50 (selrahal — Nova OpenAPI spec):** Architecture covers via Naturalization/Denaturalization. Nova spec belongs in dcm-examples. OpenStack Nova provider added with registration YAML, deployment manifest, and Go service.

**PR #18 (Fale — Interoperability API + object design RFC):** Superseded by current architecture. Conventions conflict with team's established patterns (camelCase vs snake_case, YAML vs JSON, K8s structure vs flat REST, OpenAPI 3.0.4 vs 3.1.0). Spectral AEP linter worth adopting after 3.1 compatibility testing. Added as DISCUSSION-TOPICS item 7.

### 103.6 Escalation Routing Fix

Doc B §18.8 updated: policy block escalation routes to the responsible policy domain owner (sovereignty admin, security admin, cost admin) — not generic "platform admin." Routing configurable per policy domain and profile. Fixed in doc B, walkthrough, HTML presentation, and requirements document.

### 103.7 Documentation Review Strategy

Engineering team feedback incorporated. Key decisions:
- ADRs rewritten outward-facing per Ondra's feedback ("why does this exist, not how we implemented it")
- NotebookLM recommended over raw AI prompt for reproducible onboarding (Piotr's point)
- Domain-split PRs with reviewer assignments (Gabriel's point)
- Use cases drive architecture and priorities (Piotr and Ygal's point)
- Reading guide (proposal 1), session changelogs (proposal 7) still needed

### 103.8 Meta Provider Removal → Composite Service

**Decision:** `meta_provider` was removed as a provider type (6 → 5 types). Composite payload delivery is now a catalog-level concept registered by ordinary Service Providers as **Composite Services**, with the Control Plane handling all orchestration (placement, sequencing, failure handling, compensation). Individual constituents are fulfilled by standard **Service Providers**.

**What changed:**
- Provider type count: 6 → 5 (service_provider, information_provider, auth_provider, peer_dcm, process_provider)
- Doc 30 retitled: "Meta Provider Composability Model" → "Composite Service Composition Model"
- `provided_by: self` → `provided_by: self` (the registering provider) or `provided_by: <provider_uuid>` (a named service provider) or `provided_by: external` (DCM places via Placement Engine)
- Pattern Catalog uses composite Resource Type specifications, not a meta provider type
- SQL CHECK constraint updated (meta_provider removed from provider_type enum)
- System policy IDs renamed: MPX-001..MPX-008 → CMP-001..CMP-008 (semantics preserved)
- All ADRs, walkthrough, requirements, pattern overlay, examples repo updated
- AI prompt fully migrated to Composite Service vocabulary

**What didn't change:**
- The composite Resource Type Specification YAML format — identical
- Consumer experience — still requests a catalog item, gets a composed application
- Dependency graphs, binding fields, compensation — all still work identically
- Platform engineer authoring — still defines composite specs the same way

### 103.9 Authoritative Counts Update

| Metric | Value |
|--------|-------|
| Data model docs | 58 |
| Specifications | 15 |
| ADRs | 16 (+ README) |
| OpenAPI schemas | 4 |
| Capabilities | 331 across 39 domains |
| SQL tables | 18 |
| Consumer API paths | 74 |
| Admin API paths | 61 |
| Event payloads | 109 across 23 domains |
| Provider types | 5 |
| Policy evaluation modes | 2 |
| Control plane services | 9 |
| Required infrastructure | 1 (PostgreSQL) |
| Test invariants | 60 |
| Use cases (Jira) | 30 epics, 249 stories |
| Use cases (requirements doc) | 31 total, 23 detailed |
| Prompt sections | 104 |


## SECTION 104 — CAPABILITY DISCOVERY, UNIFIED PROVIDER MODEL, AND K8S FUTURE FEATURE (2026-04)

### 104.1 Unified Provider Model (replaces typed providers)

Provider types (service_provider, information_provider, auth_provider, peer_dcm, process_provider) are replaced by a **single provider type with capability declarations**. All providers share the base contract (registration, health, sovereignty, accreditation, zero trust, audit). What varies is the capabilities:

| Capability | What it means | Replaces |
|-----------|--------------|----------|
| `realize_resources` | Provision/update/decommission infrastructure | service_provider |
| `serve_data` | Respond to queries with authoritative data | information_provider |
| `authenticate` | Authenticate identities, return tokens/roles | auth_provider |
| `federate` | Another DCM instance — mTLS, dual audit | peer_dcm |
| `execute_workflows` | Run ephemeral workflows, no persistent entities | process_provider |

**Key change:** A provider can declare multiple capabilities. An IPAM system registers once with `capabilities: [serve_data, realize_resources]`. Old type names become convenience labels derived from capability profiles.

### 104.2 Capability Discovery

**DCM side:** `GET /api/v1/capabilities` — machine-readable advertisement of what DCM offers. External systems query by domain (cost, audit, lifecycle) and get matching capabilities with subscription endpoints. No docs required — the API is self-describing.

**Provider side:** At registration, providers declare `needs_from_dcm` alongside capabilities. DCM matches needs to its capabilities and returns subscription endpoints. Provider explicitly activates subscriptions (never auto-subscribed).

**Integration flow:** External system queries capabilities → discovers matching data streams → subscribes via webhook → data flows automatically. Replaces the manual "read docs, find events, wire webhook" pattern.

New doc: **53-capability-discovery.md** — full specification.

### 104.3 Kubernetes Operator Compatibility → Future Feature

Moved to `docs/future-features/`:
- kubernetes-compatibility.md
- dcm-operator-interface-spec.md
- dcm-operator-sdk-api.md

These describe design intent not yet validated against implementation. DCM's current architecture manages infrastructure through the provider contract. Kubernetes-specific operator integration (CRD mappings, operator SDK, K8s API compatibility layer) is future work that builds on the provider model.

Specifications count: 15 → 12 (3 moved to future-features).

### 104.4 Authoritative Counts Update

| Metric | Value |
|--------|-------|
| Data model docs | 59 (added doc 53) |
| Specifications | 12 (3 K8s specs moved to future-features) |
| ADRs | 16 (+ README) |
| OpenAPI schemas | 4 |
| Capabilities | 331 across 39 domains |
| SQL tables | 18 |
| Consumer API paths | 74 (+1 for /capabilities) |
| Admin API paths | 61 |
| Event payloads | 109 across 23 domains |
| Provider model | Unified — capability-based (5 capability types, multi-capability providers) |
| Policy evaluation modes | 2 (Internal, External) |
| Control plane services | 9 |
| Required infrastructure | 1 (PostgreSQL) |
| Prompt sections | 105 |

