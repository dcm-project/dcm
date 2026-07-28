# DCM — Discussion Topics

> **Status Update (2026-03):** The DCM architecture has been substantially completed. All original 19 architecture review items, 10 session-added items, and 21 community questions have been resolved. The items below represent topics for ongoing community discussion and future evolution.
>
> **Current state:** 0 unresolved architectural questions · 331 capabilities across 39 domains · 58 data model documents · 12 specifications · 4 OpenAPI schemas · 6 JSON schemas · unified provider model (5 capability types) · 2 policy evaluation modes · 9 control plane services
>
> **Foundation:** Three abstractions (Data · Provider · Policy) · Unified Governance Matrix · Federated Contribution Model · Full OPA/Rego validation complete

## Open Community Discussion Topics

### 1. Kubernetes / CNCF Strategy (community decisions)
- CNCF submission scope: Operator Interface Spec as specification project first; DCM project after Level 2 reference implementation
- SIG App Delivery and SIG Cluster Lifecycle engagement before Sandbox submission
- Named adopters and TOC sponsor: project team action items
- Level 2 conformance scope now formally defined

### 2. Implementation Decisions (engineering decisions)
- KubeVirt reference implementation timeline → team estimates against defined Level 2 scope
- SDK language support beyond Go → community SDKs encouraged; Go SDK is reference implementation
- Non-Kubernetes container runtime support → implementation detail

### 3. Future Evolution Topics
- Normative data specifications (JSON Schema / OpenAPI) — the code-generation layer
- AI/ML Provider type — as DCM becomes AI-ready, a dedicated ML workload provider type
- Billing Provider type — deeper integration with enterprise billing and showback systems
- CMDB Provider type — dedicated contract for CMDB integration
- Multi-cloud federation model — extending DCM federation to public cloud providers
- GitOps PR UX improvements — better tooling for policy review workflow
- **UDLM as the universal observability export** *(added 2026-06-07)* — make
  UDLM-modeled data THE export surface for monitoring, alerting, logging, and
  audit consumption: telemetry entities + the event catalog exposed with
  discoverable schemas so *any* tool (metrics TSDB, log aggregator, SIEM,
  alerting pipeline) subscribes through one uniform, policy-scoped,
  retention-governed interface — no per-tool adapters. This is the UDLM goal
  ("one universal way to export data, consumable by any tool") applied to the
  observability domain; pairs OBS-002/OBS-003 with the UDLM event catalog and
  schema-sharing contracts. Validation use case:
  `dav/use-cases/observability/udlm-universal-telemetry-export.yaml`.
  DCM does not have to be the arbiter of the data — but it MAY be: where no
  platform exists or a canned solution is desired, a packaged
  **dcm-observability** component serves as the authoritative
  telemetry/monitoring platform (provider-contract §7 / PRV-007).
  First consumer and reference-implementation test bed: a homelab
  observability stack.
- **Brownfield inventory ingestion — adopt, don't recreate** *(added
  2026-06-07)* — migrating existing configuration-management estates (Ansible
  inventory) into DCM. Patterns established from live homelab migrations:
  (1) inventory groups → DCMGroups, host vars → entity attributes, with
  brownfield provenance; (2) **adopt-in-place is a hard requirement** — a
  Quay bucket migration to claim-based provisioning forced a data copy
  because the provisioner could not adopt the existing bucket; at estate
  scale that is prohibitive, so DCM ingestion must adopt resources where
  they stand; (3) embedded plaintext credentials (real finding: inventory
  carried jump-host/Pi/PiKVM passwords in cleartext) convert to vault-backed
  credential resources and get flagged for rotation; (4) coexistence —
  legacy-tool changes surface as drift, and ingestion stays reversible until
  cutover. Validation use case:
  `dav/use-cases/cross-domain/ansible-inventory-brownfield-ingestion.yaml`.


### 5. Kessel Integration (pre-implementation evaluation)
- Evaluation document written: `44-kessel-integration-evaluation.md`
- **Action required:** Discussion with Kessel development team to validate assumptions before any implementation work begins
- Key questions: API stability, sovereign/air-gapped deployment model, SpiceDB schema extensibility, resource type registry extensibility, HA/DR patterns
- **Do not implement until alignment confirmed** — document is for discussion only
- Two integration paths evaluated: Kessel Relations as Auth Provider (checks 1-2 of five-check model), Kessel Inventory as Discovered State data store
- 10 blocking items identified in doc 44 Section 10

### 4. Governance Questions
- Community governance model — how will the DCM project make decisions once public?
- Certified Profile Program — self-certified vs project-reviewed for compliance profiles
- Registry tier promotion — Tier 3 (Organization) to Tier 2 (Verified Community) pathway

---

*See [00-foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) for the three-abstraction model that resolved the major architectural questions.*


---

**Original discussion topics (archived):**

# DCM — Topics for Discussion and Modification

**Document Status:** 🔄 Active  
**Purpose:** A living document capturing topics that require further discussion, design decisions that need revisiting, and new capabilities to be incorporated into the DCM architecture and data model.  
**Process:** When a topic is resolved, move it to the appropriate architecture or data model document and mark it resolved here with a reference to where it was documented.

---

## How to Use This Document

- **Add** any topic that surfaces during design, review, or implementation that needs a decision or deeper discussion
- **Tag** each item with its area, priority, and status
- **Resolve** items by documenting the decision in the appropriate document and updating the status here
- **Never delete** resolved items — keep the full history for audit and traceability

---

## Status Key

| Status | Meaning |
|--------|---------|
| 🔴 Blocking | Must be resolved before dependent work can proceed |
| 🟡 Active | Under active discussion |
| 🟢 Resolved | Decision made — documented in referenced document |
| ⚪ Parked | Acknowledged but deferred — revisit later |

---

## Priority Key

| Priority | Meaning |
|----------|---------|
| P1 | Critical — affects foundational architecture |
| P2 | High — affects multiple components or documents |
| P3 | Medium — affects a specific component or document |
| P4 | Low — enhancement or refinement |

---

## Open Topics

---

### TOPIC-001 — Webhook Integration

**Area:** Control Plane, Provider Contract, Egress  
**Priority:** P2  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Notification Model (doc 23) supersedes standalone webhooks. Webhooks are one delivery channel within the notification model. Full event taxonomy in doc 33 (Event Catalog). See AI Prompt Sections 14, 25, 48.  
**Raised:** 2026-03  

#### Description

DCM needs a webhook integration model that allows external systems to be notified of DCM events and state changes in real time. Webhooks are a standard integration pattern that complements the existing API-first model and Message Bus — they enable a push-based notification model for consumers, providers, and external systems that cannot or do not poll DCM.

#### Use Cases

**Consumer Notifications**
- Notify a consumer's CI/CD pipeline when a resource request transitions to REALIZED state
- Notify an application team when their Resource/Service Entity enters DEGRADED state
- Notify a Tenant owner when an ownership transfer is initiated or completed
- Notify consumers when a dependency graph node fails during realization

**Provider Notifications**
- Notify a provider when a new request payload is dispatched to them
- Notify a provider when DCM initiates a discovery request
- Notify a provider when a decommission is requested for one of their entities

**External System Integration**
- Notify an external ITSM system (ServiceNow, Jira) when a request is created, updated, or completed
- Notify a monitoring system when Entity lifecycle state changes
- Notify a FinOps platform when new Resource/Service Entities are realized or decommissioned
- Notify a compliance system when compliance validation policies fire or sovereignty constraints are applied

**Operational Notifications**
- Notify SRE teams when provider capacity falls below threshold
- Notify security teams when unsanctioned changes are detected
- Notify auditors when specific policy types are triggered

#### Design Questions to Resolve

1. **Webhook registration model** — how do consumers, providers, and external systems register webhooks with DCM? Is registration via the Consumer API, Provider Registration, or a dedicated Webhook API?

2. **Event taxonomy** — what is the full list of events DCM can emit via webhook? Should this be an extensible registry similar to the Resource Type Registry?

3. **Payload format** — should webhook payloads use the DCM unified data model format, or a simplified event notification format? Should the full state payload be included or just a reference + event type?

4. **Authentication and security** — how does DCM authenticate outbound webhook calls? Options include: HMAC signatures, OAuth tokens, mTLS, API keys. How does the receiving system verify the webhook is genuinely from DCM?

5. **Retry and reliability** — what is DCM's obligation if a webhook delivery fails? Should DCM retry? How many times? With what backoff strategy? What happens if a webhook endpoint is consistently unavailable?

6. **Ordering guarantees** — are webhook events delivered in order? What happens if events arrive out of order at the receiving end?

7. **Filtering** — can webhook registrations declare filters — only receive events of specific types, for specific Resource Types, for specific Tenants, or for specific Resource Groups?

8. **Policy Engine integration** — should Validation Policy and other policy types be able to trigger webhook notifications as a policy action? This would make webhooks a first-class policy response alongside ALERT, REVERT, etc.

9. **Provider webhook obligations** — should providers be required to support webhook endpoints as part of their Provider Contract? Or is webhook support optional for providers?

10. **Tenant scoping** — should webhook registrations be scoped to a Tenant, meaning a webhook can only receive events for resources owned by the registering Tenant? Or should there be platform-level webhooks that span Tenants (for SRE/Audit personas)?

11. **Webhook versioning** — as DCM evolves, webhook payload schemas will change. How are webhook payload versions managed? Should webhook registrations declare which payload schema version they expect?

12. **Relationship to Message Bus** — DCM already has a Message Bus component. What is the distinction between webhook integration and Message Bus integration? Are webhooks the outbound consumer-facing layer on top of the Message Bus?

#### Initial Design Thoughts

Webhooks fit naturally as an **Egress capability** — they are outbound notifications from DCM to external systems, which is consistent with the existing Egress zone in the architecture (Messaging Protocol, Interoperability API).

The webhook registration model should likely be part of the **Consumer API** for consumer-facing webhooks and part of the **Provider Registration** for provider-facing webhooks.

Webhook events should be **typed and versioned** — consistent with DCM's universal versioning model. An event type like `entity.state.changed` should have a version, and webhook registrations should declare which version they support.

Webhook payloads should carry **provenance information** — the event payload should include enough context to trace back to the originating request, entity, and policy that caused the event. This is consistent with DCM's auditability requirements.

**Policy Engine integration** is particularly interesting — if the Policy Engine can fire webhooks as a response action, it enables real-time governance notifications without requiring consumers to poll DCM. This aligns with the DCM goal of getting actionable information to the right people as fast as possible.

#### References
- [Resource/Service Entities](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md) — provider lifecycle events
- [Service Dependencies](https://github.com/croadfeldt/udlm/blob/main/entities/service-dependencies.md) — dependency failure notifications
- Architecture: Egress zone, Message Bus, API Gateway

---

### TOPIC-002 — Intent Store and Intent Payload Structure

**Area:** Data Model  
**Priority:** P1  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Intent State fully specified in doc 02 (Four States), doc 04 (Examples), consumer-api-spec. Resource type referenced by FQN or UUID (both accepted). See AI Prompt Sections 4, 5, 80.  
**Raised:** 2026-03  

#### Description

The Intent State is captured when a consumer submits a request but the exact structure of the Intent payload has not been formally specified. The Intent payload is the consumer's raw declared desire — what they asked for before any processing, enrichment, or policy application. It needs a formal definition that is consistent with the four-state model and the layering model.

#### Questions to Resolve

1. What fields are required in an Intent payload vs optional?
2. How does the Intent payload reference a Resource Type — by UUID, by fully qualified name, or both?
3. How does the Intent payload declare its Tenant membership?
4. How does the Intent payload declare dependency requirements at the intent level?
5. How does the Intent payload declare group memberships?
6. How is the Intent payload versioned — does it carry a version or is it always a snapshot?

#### References
- [Context and Purpose](https://github.com/croadfeldt/udlm/blob/main/foundations/context-and-purpose.md) — four states
- [Layering and Versioning](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md) — Request Layer
- [Resource Grouping](https://github.com/croadfeldt/udlm/blob/main/entities/resource-grouping.md) — Tenant and group membership

---

### TOPIC-003 — Gating Policy vs Validation Policy Distinction

> **⚠️ Superseded (2026-06-30):** this topic's 2026-03 resolution predates the decision to **merge Gating Policy into Validation Policy**. There is no longer a separate "Gating Policy" type — "gating" is now the `enforcement_class: compliance` property of a Validation Policy. The historical text below is retained as a record of the pre-merge distinction; see `taxonomy/DCM-Taxonomy.md` and `AGENTS.md` for the current model.

**Area:** Policy Engine  
**Priority:** P2  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Gating Policy has enforcement_class (compliance=boolean deny, operational=risk score). Validation has output_class (structural=boolean fail, advisory=completeness score). Gating Policy can both block AND modify. See doc 29 (Scoring Model), AI Prompt Sections 17, 61.  
**Raised:** 2026-03  

#### Description

The distinction between Gating Policy and Validation policy categories needs better examples and a clearer formal definition. Both involve checking data against rules, but Gating Policy has override authority while Validation is pass/fail only. The boundary between them needs to be unambiguous.

#### Questions to Resolve

1. What is the precise trigger condition that makes a policy a Gating Policy vs a Validation policy?
2. Can a Gating policy both block AND modify in the same execution?
3. Are there cases where Validation and Gating Policy would produce different outcomes for the same rule?
4. Should Gating policies require explicit authorization (e.g., only CISO-owned policies can be Gating Policy)?

#### References
- [Layering and Versioning](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md) — Policy Layer section

---

### TOPIC-004 — Audit vs Observability Component Separation

**Area:** Control Plane  
**Priority:** P3  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Definitively separate (AUD-013). Opposite trade-offs: audit is 100% accuracy, append-only, 7+ year retention; observability is statistical sampling, downsampled, operational window. Cannot be combined. See doc 16, AI Prompt Section 37.3.  
**Raised:** 2026-03  

#### Description

The original architecture documents noted that Audit and Observability were separated for a reason that was later forgotten. This needs to be formally resolved — are they truly separate components with distinct responsibilities, or should they be merged?

#### Initial Thinking

**Audit** — focused on compliance evidence and transaction traceability. Reads provenance data intrinsic to data objects. Produces compliance reports, audit trails, and interrogation capability for Auditors, Security teams, and SRE personas. Historical record oriented.

**Observability** — focused on operational visibility — metrics, health, performance, real-time monitoring. Consumes provider lifecycle events, Entity state changes, and system health data. Operational present-state oriented.

These are likely genuinely separate concerns. Audit is about what happened and why. Observability is about what is happening now.

#### Questions to Resolve

1. Are Audit and Observability separate Atomic Components with separate APIs?
2. Do they share a data store or maintain separate stores?
3. How do provider lifecycle events flow to both components?

---

### TOPIC-005 — Message Bus Consumer Ingress Question

**Area:** Control Plane, Consumer Ingress  
**Priority:** P3  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Message Bus supports bidirectional integration. Inbound messages processed as authenticated API calls via registered webhook actor identity. Same Policy Engine evaluation as any API call. See doc 18, AI Prompt Section 25.  
**Raised:** 2026-03  

#### Description

The original architecture documents raised an unresolved question: should the Message Bus be offered as consumer ingress (inbound) in addition to egress (outbound)? The API-first principle suggests it should be egress only, but there are valid integration scenarios where external systems need to push data into DCM asynchronously.

#### Questions to Resolve

1. Should consumers be able to submit requests via the Message Bus, or only via the Consumer API?
2. If Message Bus ingress is supported, how are requests authenticated and authorized?
3. How does Message Bus ingress interact with the Intent State capture — is the message treated as an Intent payload?

---

### TOPIC-006 — Cache Architecture

**Area:** Data Model, Control Plane  
**Priority:** P2  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Hybrid push-pull model. Caches placed closest to consumption, subject to sovereignty. GitOps and Event Streams always authoritative; caches are derived projections. Sovereign DCM uses signed bundles only. See CACHE-001 through CACHE-004, AI Prompt Section 40.2-40.4.  
**Raised:** 2026-03  

#### Description

Several unresolved questions exist about where data caches live, how they are synchronized, and which cache is authoritative when caches diverge. This has implications for distributed DCM deployments and sovereignty scenarios.

#### Questions to Resolve

1. Where should data caches live? Hub DCM? Regional DCM? Sovereign DCM? All locations?
2. Should cache synchronization be push, pull, or both?
3. Which cache is authoritative when caches diverge?
4. What mechanism maintains consistency across distributed caches?
5. How do cache architecture decisions interact with sovereignty constraints — can cached data cross sovereignty boundaries?

---

### TOPIC-007 — Cross-Tenant Dependencies

**Area:** Data Model, Multi-Tenancy  
**Priority:** P2  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Relationship nature governs cross-tenant: constituent=never, operational=dual authorization, informational=unless deny_all. explicit_only is default stance. cross_tenant_authorization DCMGroup required. See doc 09, REL-010/011/012, XTA-001-005, AI Prompt Sections 11.13-11.14, 21.6.  
**Raised:** 2026-03  

#### Description

The dependency model currently assumes dependencies are resolved within a single Tenant. However, real-world deployments will have cross-tenant dependencies — a Payments Tenant application that depends on a shared DNS service owned by a Platform Tenant. The data model needs to formally address how cross-tenant dependencies are declared, resolved, and governed.

#### Questions to Resolve

1. How is a cross-tenant dependency declared — does it reference the Tenant UUID of the dependency owner?
2. What authorization is required for a cross-tenant dependency? Does the owning Tenant need to approve?
3. How does cost attribution work for cross-tenant service consumption?
4. How does drift detection work when a dependency is in another Tenant?
5. Can a compliance validation policy block cross-tenant dependencies?

---

### TOPIC-008 — Provider Trust Validation Mechanism

**Area:** Service Providers, Provider Contract  
**Priority:** P1  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Registration spec defines full approval pipeline (auto/reviewed/verified/authorized). Provider Callback Auth (doc 43, PCA-001-010) specifies two-layer mTLS + credential model. Trust levels: trusted/verified/untrusted. Accreditation model (doc 26) governs ongoing trust. See AI Prompt Sections 53.2, 76.  
**Raised:** 2026-03  

#### Description

The Provider Contract includes a Trust Contract — providers must be validated and certified to participate in the DCM ecosystem. The mechanism for establishing, maintaining, and revoking trust has not been designed.

#### Questions to Resolve

1. What is the certification process for a new provider?
2. What technical mechanism validates trust at request time?
3. How is trust revoked if a provider violates their contract?
4. Should trust be per-provider or per-catalog-item?
5. How does the trust chain interact with sovereignty requirements?

---

### TOPIC-009 — Physical Shared Infrastructure Tenancy

**Area:** Data Model, Tenancy  
**Priority:** P2  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** Three ownership patterns: Whole Allocation (indivisible, provider retains), Allocation (pool yields sub-resources), Shareable (one resource, multiple stakeholders). Physical infrastructure owned by __platform__ Tenant. See doc 04b, OWN-001 through OWN-008, AI Prompt Sections 8.3, 46.2.  
**Raised:** 2026-03  

#### Description

The current model assigns every Resource/Service Entity to exactly one DCM Tenant. This works cleanly for most cases but edge cases exist for truly shared physical infrastructure — a rack, a network switch, a power circuit — where the ownership model may be genuinely joint or ambiguous.

#### Questions to Resolve

1. Is jointly-owned physical infrastructure a valid DCM use case, or is it always owned by a Platform/Infrastructure Tenant?
2. If joint ownership is valid, how is it modeled without breaking the single-Tenant rule?
3. Does the Whole Allocation model cover all physical infrastructure scenarios?

---

### TOPIC-010 — Embedded Technology-Specific Data Bundles

**Area:** Data Model  
**Priority:** P3  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** native_passthrough field sanctioned for genuinely untranslatable provider-specific data. Always audit-logged (content if transparent, hash if opaque). Opaque passthrough blocked in fsi/sovereign by default. See DATA-001, AI Prompt Section 40.5.  
**Raised:** 2026-03  

#### Description

The original data model discussion raised the question of whether the data model should allow embedded target-technology-specific data bundles — for example, a Terraform HCL block or an Ansible vars file embedded directly in an entity definition. The authors noted "not convinced this is something we want."

#### Questions to Resolve

1. Should technology-specific data bundles be allowed in entity definitions?
2. If allowed, must they be in clear text and appropriate for Git storage?
3. How would embedded bundles interact with the portability model — they would clearly be portability-breaking?
4. Is there a better mechanism — such as a provider-specific extension field with an appropriate portability classification?

---

## Resolved Topics

---

### TOPIC-R001 — Field Override Control Mechanism

**Area:** Data Model, Policy Engine, Layering  
**Priority:** P1  
**Status:** 🟢 Resolved  
**Raised:** 2026-03  
**Resolved:** 2026-03  

#### Decision

Field override control is implemented as a **standard Policy Engine mechanism** using a graduated three-level model: Level 1 (no declaration — fully overridable), Level 2 (simple `override: allow|constrained|immutable`), Level 3 (full actor matrix with per-actor permissions, trusted grants, and expansion rules). The Policy Engine is the sole authority for setting override control. The Request Payload Processor enforces structural layer rules only.

#### Documented In
- [Data Layers and Assembly Process](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md) — Section 5a
- [Context and Purpose](https://github.com/croadfeldt/udlm/blob/main/foundations/context-and-purpose.md) — Section 4.4

---

### TOPIC-R002 — Storage/Networking Bundling vs Dependency Model (Q53)

**Area:** Data Model, Entity Relationships, Service Dependencies  
**Priority:** P1  
**Status:** 🟢 Resolved  
**Raised:** 2026-03  
**Resolved:** 2026-03  

#### Decision

The conflict between the enhancement documents (storage bundled in VM schema) and the data model (separate first-class entities) is resolved through a **universal Entity Relationship model**:

- Bundled consumer declarations are expanded by the Request Payload Processor into first-class Resource/Service Entities with their own UUIDs
- The relationship between parent and child entities is expressed using the universal relationship model — bidirectional, UUID-keyed, with lifecycle policies
- The same relationship model is used for ALL entity relationships — compute to storage, application to web server, resource to business unit — minimizing variance
- Lifecycle policies (destroy|retain|detach|notify on parent destroy/suspend/modify) replace the ephemeral/persistent classification
- Expansion rules live in the Resource Type Specification — portable and declarative
- The dependency graph concept is unified into the Entity Relationship Graph

#### Documented In
- [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) — complete relationship model
- [Information Providers](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers.md) — external data relationships
- [Service Dependencies](https://github.com/croadfeldt/udlm/blob/main/entities/service-dependencies.md) — updated to reference entity relationships

---

### TOPIC-R003 — Information Provider Model

**Area:** Data Model, Provider Contract  
**Priority:** P1  
**Status:** 🟢 Resolved  
**Raised:** 2026-03  
**Resolved:** 2026-03  

#### Decision

Information Providers are a first-class provider type in DCM. They follow the same registration, health check, trust, and contract model as Service Providers where applicable. Key decisions:

- Information types live in the same DCM registry as Resource Types — distinguished by category prefix (Business.*, Identity.*, Compliance.*, Operations.*)
- Standard vs extended data — DCM only relies on standard fields for operational decisions; organizations can extend with domain-specific fields
- Stable external key model — DCM UUID wraps external UUID; if external system changes its UUID, only the reference record changes
- Three-mode verification — scheduled (Mode 1), provider push (Mode 2, contractual obligation), on-demand (Mode 3, fallback)
- Internal business data follows the standard resource entity model when DCM owns it; external references use the Information Provider model

#### Documented In
- [Information Providers](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers.md)
- [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) — external relationship structure
- [Resource Type Hierarchy](https://github.com/croadfeldt/udlm/blob/main/entities/resource-type-hierarchy.md) — information type categories added

---

---

### TOPIC-011 — Enhancement Document Compatibility Findings

**Area:** Data Model, Provider Contract, Policy Engine, Catalog  
**Priority:** P1  
**Status:** 🟢 Resolved
**Resolved:** 2026-03
**Resolution:** All cross-cutting gaps resolved: field-level provenance (doc 00, Section 4.3), UUIDs (universal identity requirement), portability classification (doc 05), sovereignty declarations (doc A provider contract), tenancy (doc 15 universal groups), versioning (semver throughout), deprecation (five-status lifecycle). Enhancement docs superseded by current architecture.  
**Raised:** 2026-03  

#### Description

A compatibility review of six DCM enhancement documents against the data model identified areas of strong alignment and cross-cutting gaps that need resolution before the enhancements can be considered fully aligned with the data model.

#### Cross-Cutting Gaps (affect all or most enhancements)

1. **Field-Level Provenance** — absent in all enhancement documents. The Policy Engine spec mutates request payloads without recording provenance. The KubeVirt SP returns minimal status rather than full DCM-format realized payloads.

2. **UUIDs as Primary Identifiers** — most specs use `name` as the natural key rather than UUID as the primary key. The data model requires UUIDs as primary identifiers on all entities.

3. **Portability Classification** — absent from all provider and catalog specs. Every field must declare `universal|conditional|provider-specific|exclusive` classification.

4. **Sovereignty Declarations** — entirely absent from SP Registration and KubeVirt SP. Provider registration must include sovereignty capability declarations as a contractual obligation.

5. **Tenant Support** — explicitly deferred in V1 in the Policy Engine spec. The data model treats Tenant as mandatory and non-overridable. A clear migration path from V1 to Tenant support is needed.

6. **Universal Versioning** — catalog items use `apiVersion: v1alpha1` rather than Major.Minor.Revision. All definitions require universal versioning.

7. **Deprecation Model** — absent from all enhancement documents. All definitions require the `active → deprecated → retired` lifecycle.

#### Document-Specific Gaps

**SP Registration Flow:**
- Registration payload missing: sovereignty declarations, ownership model declaration, dependency declarations, capacity model mode declaration
- Uses `name` as natural key rather than UUID as primary key
- Capacity data (totalCpu, totalMemory) treated as static rather than dynamic — needs reconciliation with three-mode capacity model

**Service Type Definitions:**
- `providerHints` not formally marked as portability-breaking — silently bypasses portability enforcement
- Storage and networking bundled with compute — conflicts with the service dependency model which treats these as separate dependent services with their own lifecycle
- No UUIDs on field definitions, no provenance metadata, no versioning beyond v1alpha1

**Service Provider Health Check:**
- Covers liveness only — insufficient for full Provider Lifecycle Events contract
- Does not address DEGRADATION, MAINTENANCE, UNSANCTIONED_CHANGE, CAPACITY_CHANGE events
- Binary 200/non-200 model needs to coexist with structured event payload model

**Policy Engine:**
- `selected_provider` as a direct policy output conflicts with the data model's specificity narrowing model for provider selection
- No policy versioning or GitOps integration — data model requires policies maintained via GitOps
- No provenance recording on field mutations — data model requires provenance on every modification
- Constraint immutability model is compatible and can be mapped to `override_preference` field metadata

**Catalog Item Schema:**
- No UUIDs, no Tenant scoping, no portability classification, no deprecation model, no provenance
- `editable` field concept is valuable and not explicitly covered in data model — worth incorporating into the Resource Type Specification field definition
- `dependsOn` conditional field pattern maps to `conditional` portability classification but needs formal alignment

**KubeVirt Service Provider:**
- Realized payload returns minimal status rather than complete DCM-format payload — Denaturalization requirement not met
- No unsanctioned change detection — only VMI phase changes reported
- Registration gaps same as SP Registration Flow spec
- `namespace` in response payload is provider-native concept with no DCM equivalent

#### Questions to Resolve

1. Should the enhancement documents be updated to align with the data model, or should the data model be adjusted where the enhancements reveal practical implementation constraints?
2. For the storage/networking bundling vs. dependency model tension — is this a V1 simplification that gets resolved in V2, or does the data model need a "monolithic service" concept?
3. For `selected_provider` in the Policy Engine — should provider selection remain a policy output, or should it be moved to a dedicated placement component that consumes narrowed field sets from the Policy Engine?
4. What is the migration path from V1 (no Tenant support) to Tenant-mandatory?
5. Should the `editable` field concept from the Catalog Item Schema be formally incorporated into the Resource Type Specification?

#### References
- SP Registration: https://github.com/dcm-project/enhancements/blob/main/enhancements/sp-registration-flow/sp-registration-flow.md
- Service Types: https://github.com/dcm-project/enhancements/blob/main/enhancements/service-type-definitions/service-type-definitions.md
- Health Check: https://github.com/dcm-project/enhancements/blob/main/enhancements/service-provider-health-check/service-provider-health-check.md
- Policy Engine: https://github.com/dcm-project/enhancements/blob/main/enhancements/policy-engine/policy-engine.md
- Catalog Item: https://github.com/dcm-project/enhancements/blob/main/enhancements/catalog-item-schema/catalog-item-schema.md
- KubeVirt SP: https://github.com/dcm-project/enhancements/blob/main/enhancements/kubevirt-sp/kubevirt-sp.md

---

Copy the following template and fill in the fields:

```markdown
### TOPIC-NNN — Title

**Area:** <affected area>  
**Priority:** <P1|P2|P3|P4>  
**Status:** 🟡 Active  
**Raised:** <date>  

#### Description

<description of the topic>

#### Questions to Resolve

1. <question>

#### References
- <related documents>
```

---

*This document is maintained by the DCM Project team. Add topics freely — no topic is too small if it needs a decision.*

---

### 6. Universal Lightspeed Interface for Operations (future concept)

**Note captured for future exploration.**

A universal operations interface concept — working title "Lightspeed" — for DCM. Intent is a unified, high-velocity operational surface for all DCM actions regardless of the underlying provider, resource type, or lifecycle stage. Think of it as the operational equivalent of what the unified data model is to data: a single consistent interaction model for humans and automation alike across the full DCM estate.

**Initial thoughts to explore:**
- Single interface for any operation on any resource managed by DCM — no provider-specific tooling, no context switching
- "Lightspeed" implies minimal friction: operations that currently take multiple steps, approvals, and tool handoffs should be expressible and executable in a single interaction
- Applicable to both human operators (Web UI / CLI) and automation (agentic workflows, AIOps)
- Likely surfaces DCM's existing policy engine, lifecycle model, and unified data model as the execution layer — the interface is the innovation, not new backend capability
- Could be the primary surface for DCM's "AI Ready" design principle (README): agentic workflows operating over DCM's control plane via a natural-language-capable interface that still enforces all policy, sovereignty, and accreditation constraints

**Questions to answer when this gets scoped:**
- Is this a new GUI surface, a CLI, an AI agent interface, or all three?
- How does it relate to the existing Web UI spec and Flow GUI spec?
- What does "lightspeed" mean operationally — sub-second execution, zero-confirmation for pre-approved patterns, predictive pre-staging?
- How does it interact with the Authority Tier model — can it auto-route approval gates without interrupting the operator's flow?
- Is this the primary interface for the AIOps layer referenced in the README?

**Status:** Concept note — no design work started. Capture for roadmap planning.

### 7. Spectral AEP Linter + CI Workflow Adoption (PR #18 review)

**Source:** [PR #18](https://github.com/dcm-project/dcm/pull/18) by Fale — first draft of Interoperability API and Service Spec design guidelines.

**PR #18 disposition:** The interoperability API and object design RFC are superseded by the current architecture (4 canonical OpenAPI specs, 58 data model docs). Several conventions in PR #18 (camelCase fields, PascalCase enums, YAML content type, K8s apiVersion/kind/spec/status structure) contradict the team's established patterns (snake_case fields, UPPER_SNAKE_CASE enums, JSON, flat REST entities). PR should be closed with acknowledgment and pointer to current architecture.

**What to adopt:** The `.spectral.yaml` AEP linter config and the GitHub Actions CI workflow that validates OpenAPI specs against AEP rules. This enforces PRR-006 (AEP.DEV Linting) in CI.

**Blockers before adoption:**
- The team's greenfield specs use OpenAPI 3.1.0; the AEP Spectral ruleset was built for 3.0.x. Must test for false positives on 3.1 constructs before enabling CI enforcement.
- Determine scope: lint only greenfield specs in `src/api/v1alpha1/`, or also the canonical specs in `dcm/schemas/openapi/`?
- Decide if this goes in dcm-examples only, or also in the dcm architecture repo for the canonical specs.

**Status:** Future — pending OpenAPI 3.1 compatibility verification.

