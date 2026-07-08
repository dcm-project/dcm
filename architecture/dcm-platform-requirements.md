# DCM PLATFORM REQUIREMENTS DOCUMENT

**Data Center Management — Sovereign Cloud Framework**

*Requirements for the DCM control plane, data model, and provider ecosystem enabling enterprise organizations to manage infrastructure lifecycle with policy-as-code governance, tamper-evident audit, and multi-provider abstraction.*

**Date:** April 2026  
**Author:** Chris Roadfeldt, Principal Architect  
**Project:** Red Hat FlightPath — github.com/dcm-project

---

# Engagement Context

DCM addresses a fundamental gap in enterprise infrastructure management: on-premises data centers lack the unified control plane that public clouds provide as table stakes. Organizations operating large-scale, multi-platform infrastructure spend disproportionate engineering effort stitching together disparate automation tools, enforcing governance manually, and reconciling inventory that diverges silently between intended and actual state.

**Target Organizations**

- Enterprise data center operators running heterogeneous infrastructure (VM, container, network, storage) across multiple platforms
- Organizations with regulatory requirements (financial services, government, healthcare) requiring provable audit trails and data residency enforcement
- Platform engineering teams seeking to offer self-service infrastructure to development teams with built-in governance

**DCM's Value Proposition**

DCM is the management plane that sits above provisioning tools (Ansible, Terraform, Kubernetes operators) and governs what gets requested, approved, built, owned, and decommissioned. It provides: a unified data model and API across all infrastructure platforms; policy-as-code enforcement on every request before provisioning; full lifecycle management from request through decommission with tamper-evident audit; and a provider abstraction with capability discovery that makes any infrastructure platform consumable through the same interface.

**Delivery Context**

DCM is an open-source project under the Red Hat FlightPath initiative, licensed under Apache 2.0. The engineering team spans Red Hat and community contributors. The initial milestone is a summit demonstration showing end-to-end provisioning with policy enforcement and audit verification.

---

# Executive Summary

DCM requires a control plane that enables: declarative lifecycle management of infrastructure resources across heterogeneous providers; policy-as-code governance enforced on every request with configurable override mechanisms; a provider abstraction that makes any infrastructure platform — VM, container, network, storage — consumable through the same interface and data model; tamper-evident audit with mathematical provability (Merkle tree) at configurable granularity; sovereignty and data residency enforcement as first-class concepts, not afterthoughts; and a consumer experience that abstracts infrastructure complexity behind a service catalog.

The platform is designed as a management plane — it orchestrates lifecycle, enforces governance, and maintains state. It does not provision infrastructure directly. Provisioning is delegated to service providers (OpenStack, KubeVirt, ACM, Ansible, Terraform) that implement DCM's provider contract.

---

# Personas

## Consumer Developer

A developer or application owner who requests and manages infrastructure resources through the service catalog. Interacts with DCM via API, Web UI (RHDH), or Git PR. Does not need to understand which provider, datacenter, or network configuration fulfills their request — DCM handles that.

- **Key activities:** Browse service catalog, submit resource requests, track request status, handle policy blocks, manage running resources, view cost estimates, trigger decommission

## Platform Engineer

Defines the organizational infrastructure standards that DCM enforces. Authors resource type specifications, data layers (datacenter configs, environment defaults, tenant overrides), policies, and composite resource type specifications (three-tier applications, data pipelines).

- **Key activities:** Define resource types and catalog items, author data layers, write and test policies (shadow mode), create composite service definitions, manage the resource type registry

## Infrastructure Operator

Manages the physical and virtual infrastructure that DCM's providers abstract. Implements and operates service providers, manages provider health and capacity, handles accreditation and sovereignty declarations, and responds to drift remediation alerts.

- **Key activities:** Implement and register service providers, manage provider health and capacity reporting, handle naturalization/denaturalization, respond to discovery and drift events

## Policy and Compliance Owner

Defines and manages the governance rules that DCM enforces. Authors Gating policies (allow/deny), validation policies, sovereignty constraints, and override approval rules. Reviews audit trails and compliance reports.

- **Key activities:** Author and activate policies, configure policy profiles (minimal through sovereign), review override requests (dual-approval), verify audit integrity, manage compliance rescans

## Platform Administrator

Deploys and operates the DCM control plane itself. Manages the 9 control plane services, database, tenant configuration, auth provider setup, and platform health monitoring.

- **Key activities:** Deploy and upgrade DCM, onboard tenants, configure auth providers, manage profiles and deployment configuration, monitor platform health, rotate credentials

---

# Use Cases

The following use cases capture DCM's core requirements, organized by lifecycle phase and prioritized for the summit demonstration and subsequent delivery phases.

| **ID** | **Use Case** | **Priority** | **Personas** |
|--------|-------------|-------------|-------------|
| **UC-001** | Deploy DCM Control Plane | **P0** | Administrator |
| **UC-002** | Register Service Providers | **P0** | Operator, Administrator |
| **UC-003** | Populate Service Catalog | **P0** | Platform Engineer |
| **UC-004** | Configure Organizational Policies | **P0** | Policy Owner, Platform Engineer |
| **UC-005** | Configure Deployment Profiles | **P1** | Administrator |
| **UC-010** | Provision a Virtual Machine | **P0** | Consumer |
| **UC-011** | Provision a Three-Tier Application | **P0** | Consumer |
| **UC-012** | Handle a Policy-Blocked Request | **P0** | Consumer |
| **UC-013** | View Cost Before Committing | **P1** | Consumer |
| **UC-014** | Track Request Progress | **P0** | Consumer |
| **UC-020** | Update a Running Resource | **P0** | Consumer |
| **UC-021** | Scale Resource Capacity | **P1** | Consumer |
| **UC-022** | Detect and Remediate Drift | **P0** | Operator, Consumer |
| **UC-023** | Transfer Resource Ownership | **P2** | Consumer, Administrator |
| **UC-024** | Manage Subscription Lifecycle | **P2** | Consumer, Administrator |
| **UC-030** | Rebuild from Stored State (DR) | **P1** | Operator, Administrator |
| **UC-031** | Migrate Resources to New Provider | **P2** | Operator, Administrator |
| **UC-040** | Decommission a Resource | **P0** | Consumer |
| **UC-050** | Enforce Sovereignty and Data Residency | **P0** | Policy Owner |
| **UC-051** | Rescan Existing Resources Against New Policy | **P1** | Policy Owner |
| **UC-052** | Prove Pipeline Integrity to Auditor | **P0** | Policy Owner |
| **UC-053** | Prove Override Authorization | **P1** | Policy Owner |
| **UC-060** | Cross-Instance Placement (Federation) | **P2** | Administrator |
| **UC-070** | Monitor DCM Platform Health | **P1** | Administrator |
| **UC-071** | Onboard a New Tenant | **P0** | Administrator |
| **UC-072** | Validate Provider Accreditation | **P2** | Administrator, Policy Owner |
| **UC-080** | Scoped Interaction Credentials (Zero Trust) | **P1** | Administrator |
| **UC-081** | Session Management and Auth Failover | **P0** | Consumer, Administrator |
| **UC-090** | ITSM Integration (ServiceNow) | **P2** | Administrator, Operator |
| **UC-091** | Git-Based Request Ingress | **P1** | Consumer, Platform Engineer |
| **UC-100** | Deploy a Resource Pattern from Pattern Catalog | **P0** | Consumer, Platform Engineer |

---

## Day 0 — Platform Setup

### UC-001: Deploy DCM Control Plane

An administrator deploys the DCM control plane to an OpenShift cluster. PostgreSQL is the only required infrastructure dependency. The deployment includes 9 control plane services (API Gateway, Catalog Manager, Request Processor, Policy Engine, Placement Engine, Request Orchestrator, Audit Service, Discovery Service, Provider Manager), the PostgreSQL database with 18 tables and RLS tenant isolation, and initial configuration (system admin account, default profile, built-in auth provider). After deployment, the administrator verifies all services are healthy and the API gateway is reachable.

**Success criteria:** All 9 services healthy. API gateway responds to requests. Admin can authenticate and access the admin API. No external dependencies required beyond PostgreSQL.

### UC-002: Register Service Providers

An infrastructure operator registers a service provider (e.g., OpenStack Nova compute) with DCM. The registration includes: provider type (service, information, meta, auth, peer_dcm, or process), capability declaration (resource types supported, lifecycle operations), health endpoint URL, sovereignty zone declarations (which jurisdictions the provider operates in), accreditation declarations (compliance certifications), and callback authentication configuration. DCM validates the registration, probes the health endpoint, and activates the provider. The provider is now available for placement consideration.

**Success criteria:** Provider registered and active. Health check passes. Resource types appear in the registry. Provider is eligible for placement queries.

### UC-003: Populate Service Catalog

A platform engineer defines resource types and catalog items. A resource type specification (e.g., `Compute.VirtualMachine v1.0.0`) declares the vendor-neutral field schema (cpu_count, memory_gb, os_family), constraints (min/max values, allowed enums), type-level dependencies (every VM requires a Network.IPAddress), and lifecycle rules. A provider catalog item (e.g., "EU-WEST OpenStack VM — Standard") ties a resource type spec to a specific provider with pricing, SLAs, and availability. The platform engineer also creates data layers: datacenter layers (location, network ranges), environment layers (production vs dev defaults), tenant layers (team-specific overrides), and compliance layers (EU data residency requirements).

**Success criteria:** Consumers can browse the catalog filtered by RBAC. Resource type schemas are queryable. Dependency graphs are visible. Data layers resolve correctly during assembly.

### UC-004: Configure Organizational Policies

A policy and compliance owner authors the baseline policy set: a sovereignty Gating policy that blocks resources from deploying outside designated zones (hard enforcement); a sizing validation policy that enforces CPU and memory limits per tenant tier; a naming transformation policy that auto-generates standardized hostnames; a monitoring transformation policy that injects the organization's monitoring agent into every production resource; and a cost Gating policy that blocks requests exceeding budget thresholds. Each policy is first deployed in **shadow mode** — it evaluates against real traffic and logs results without blocking requests. After validation, the policy is promoted to active. Policies use the Gatekeeper ConstraintTemplate pattern: reusable Rego logic with parameterized instances.

**Success criteria:** Policies evaluate correctly in shadow mode. No false positives on legitimate requests. Activation enforces the policy on all matching requests. Audit records produced for every evaluation.

### UC-005: Configure Deployment Profiles

An administrator configures deployment profiles that govern operational behavior per environment:

| Profile | Audit Granularity | Override Timeout | Policy Minimums | Use |
|---------|-------------------|-----------------|----------------|-----|
| minimal | stage | 24h | none | Homelab, evaluation |
| dev | stage | 4h | naming, tagging | Development |
| standard | mutation | 8h | all core policies | Production |
| fsi | field | 48h | sovereignty + all core | Financial services |
| sovereign | field (synchronous) | 72h | all policies on all ops | Government, classified |

**Success criteria:** Profile assignment per tenant governs audit depth, override windows, and policy enforcement minimums. Profile changes take effect on next request.

---

## Day 1 — Consumer Operations

### UC-010: Provision a Virtual Machine

A consumer developer browses the service catalog, selects "Virtual Machine — Standard," and submits a request with 6 fields: cpu_count, memory_gb, storage_gb, os_family, environment, and name. The consumer does not specify a provider, datacenter, or network configuration.

**DCM processes the request through the full pipeline:**
1. **Intent captured** — Consumer's raw declaration stored with entity_uuid assigned
2. **Layer assembly** — 5 data layers merge organizational context (datacenter, environment, compliance, tenant, provider defaults) into the consumer's 6 fields, producing 10+ fields with full provenance
3. **Dependency resolution** — Resource type spec declares VM requires Network.IPAddress; DCM creates an IP sub-request automatically
4. **IP policy evaluation** — Sovereignty, subnet isolation, and pool selection policies evaluate against the IP sub-request; IPAM provider selected and IP allocated
5. **VM policy evaluation** — Gating Policy (sizing, sovereignty, approved OS images), Validation (field constraints), and Transformation (monitoring injection) policies evaluate
6. **Placement** — Sovereignty pre-filter eliminates non-compliant providers; remaining providers scored by capacity and confidence; best provider selected
7. **Dispatch** — Request Orchestrator sends the assembled payload (including the dependency-injected IP address) to the selected provider; the provider naturalizes DCM's unified payload into its native API
8. **Realization** — Provider provisions the VM, denaturalizes the result back to DCM's format, and callbacks with realized state
9. **Audit** — 17 Merkle tree leaves recorded across the VM entity and IP dependency

**Success criteria:** Consumer receives a running VM with the pre-allocated IP address. Full provenance chain traceable from every field value back to its origin. Audit trail is tamper-evident and verifiable. Consumer tracked progress through pipeline stages via status API.

### UC-011: Provision a Three-Tier Application

A consumer requests a "Web Application — Standard" catalog item. This is a composite service backed by a composite resource type specification that decomposes into four constituent resources: network port, database VM, application server VM, and load balancer.

The composite resource type spec declares the dependency graph and binding fields:
- Network port has no dependencies — provisioned first
- Database depends on network port — IP address injected from port
- Application server depends on database — connection string and credentials injected
- Load balancer depends on application server — backend pool configured from app server IPs

DCM processes each constituent through the full pipeline (policy evaluation, placement, dispatch) independently, respecting dependency order. Realized outputs from each constituent flow into dependent constituents via binding fields. If any required constituent fails, a compensation policy triggers reverse-order teardown of already-realized constituents.

**Success criteria:** Single catalog request produces 4 running, interconnected resources. Runtime values (IPs, connection strings) flow correctly between constituents. Each constituent is independently managed in DCM (its own entity_uuid, audit trail, drift detection). Decommission reverses dependency order.

### UC-012: Handle a Policy-Blocked Request

A consumer requests a VM with `environment: production` in a zone that violates their tenant's EU data residency policy. The request enters `POLICY_BLOCKED` state.

The consumer receives a structured response containing: the blocking policy name, type, and enforcement level; the specific field that violated (sovereignty_zone); compliant value suggestions (e.g., "zone must be one of: eu-west-1, eu-west-2"); and four resolution paths.

| Resolution | What happens |
|-----------|-------------|
| **Modify request** | Consumer changes the zone to eu-west-1 and resubmits. Request proceeds. |
| **Request override** | Consumer provides justification. For hard policies, dual-approval required (two approvers, different roles). |
| **Cancel** | Consumer abandons the request. Audit trail preserved. |
| **Escalate** | Request routed to the role responsible for the blocking policy domain (e.g., sovereignty admin for data residency violations, security admin for compliance blocks, cost admin for budget overruns). The responsible role reviews and may register an Exception Grant for future similar requests. Routing is configurable per policy domain and profile. |

**Success criteria:** Consumer receives actionable guidance, not just "denied." Override requests are auditable. Block timeout auto-cancels abandoned requests. Override frequency is tracked for policy review.

### UC-013: View Cost Before Committing

A consumer sees an estimated cost for their resource request before submitting. Cost data comes from provider catalog item metadata (declared at registration). The placement engine considers cost alongside sovereignty, tier, and capacity constraints — not as the sole factor.

**Success criteria:** Cost estimate displayed before submission. Cost attribution tracks to tenant and business unit.

### UC-014: Track Request Progress

After submitting a request, the consumer monitors progress through pipeline stages: SUBMITTED → ASSEMBLING → POLICY_EVALUATION → PLACEMENT → DISPATCHED → REALIZING → OPERATIONAL. For composite services, each constituent's status is tracked independently.

**Success criteria:** Real-time status updates via Server-Sent Events (SSE) or polling. Constituent-level tracking for composite service requests. Failed stages show clear error with remediation guidance.

---

## Day 2 — Ongoing Management

### UC-020: Update a Running Resource

A consumer modifies a running VM's memory from 8 GB to 16 GB. DCM creates a new request with operation_type `update`. Only lifecycle-relevant policies fire: the sizing validation policy re-evaluates (lifecycle_scope includes `update`, changed_field_filter includes `memory_gb`). The sovereignty policy does not re-evaluate (no zone change). Placement does not re-run (no provider change). The provider receives a delta payload and applies the change.

**Success criteria:** Only relevant policies fire. Unchanged fields are not re-evaluated. Audit records the specific mutation. Realized state updated to reflect new memory.

### UC-021: Scale Resource Capacity

A consumer scales application server replicas from 2 to 4. If the existing provider/zone has capacity, the scale occurs in place. If capacity is insufficient, placement re-evaluates to find a zone with capacity — subject to the same sovereignty and policy constraints as initial provisioning.

**Success criteria:** Scale-in-place when capacity exists. Automatic placement re-evaluation when it doesn't. Sovereignty constraints honored throughout.

### UC-022: Detect and Remediate Drift

The Discovery service polls providers on a configurable interval (default: 5 minutes). It compares discovered state to realized state. If a VM was manually modified outside DCM (e.g., memory changed from 8 GB to 16 GB via the hypervisor console), drift is detected. The configured drift policy determines the response: notify (alert the consumer and operator), auto-remediate (revert to realized state), or log (record the drift for manual review).

**Success criteria:** Drift detected within one polling interval. Notification sent to appropriate parties. Auto-remediation restores realized state when configured. Both VM entity and its IP dependency are independently discoverable.

### UC-030: Rebuild from Stored State (Disaster Recovery)

A datacenter failure renders an entire availability zone unavailable. The infrastructure operator initiates rehydration for all affected resources. DCM reads the original **Intent State** for each affected entity — the consumer's raw declaration, preserved immutably since submission.

Each entity re-enters the full pipeline as a new request with operation_type `rehydration`:

1. **Layer assembly re-runs** — layers may have changed since original provisioning (new compliance requirements, updated monitoring agents). The resource gets current organizational context, not stale data.
2. **All policies re-evaluate** — current sovereignty policies, sizing limits, and security requirements apply. A resource that was compliant when originally provisioned may now violate a newer policy. If so, it enters POLICY_BLOCKED and the operator must resolve before rehydration proceeds.
3. **Placement re-evaluates** — the original provider/zone is unavailable. The placement engine scores surviving providers, subject to the same sovereignty pre-filter. A resource originally in EU-WEST-Prod-1 may rehydrate to EU-WEST-Prod-2.
4. **Dependencies rehydrate in order** — for composite services (three-tier apps), DCM reads the dependency graph and rehydrates constituents in dependency order: database first, then backend (with new DB IP injected), then frontend (with new backend IP injected). Binding fields resolve against newly realized values, not cached originals.
5. **Entity UUID is preserved** — the resource keeps its original entity_uuid across rehydration. Audit trail links the original lifecycle to the rehydrated one.

**What does NOT happen:** The realized state from the lost zone is not replayed. The intent is re-processed from scratch with current layers, current policies, and current provider availability. This is a design choice — rehydration produces resources that comply with today's rules, not yesterday's.

**Success criteria:** All affected resources rebuilt on surviving infrastructure. Current policies enforced (not original-time policies). Dependencies resolve correctly with new runtime values. Entity UUIDs preserved. Complete audit trail links original and rehydrated lifecycles. Sovereignty constraints honored — resources cannot rehydrate into non-compliant zones.

### UC-040: Decommission a Resource

A consumer or TTL trigger initiates decommission. DCM checks for dependencies: if other resources depend on this one (e.g., a VM using an IP address), decommission is blocked with guidance. If no blockers, the request enters the pipeline with operation_type `decommission`. The provider tears down the resource. Credentials are revoked. The IP address is released back to its pool. Audit trail is preserved permanently.

**Success criteria:** Dependency checks prevent premature teardown. Provider confirms teardown. Dependent resources (IPs, credentials) are cleaned up. Audit trail survives decommission.

---

## Governance

### UC-050: Enforce Sovereignty and Data Residency

All resources handling restricted, PHI, or PCI data are placed exclusively in designated sovereignty zones. The sovereignty Gating policy fires on **every lifecycle operation** (initial provisioning, update, scale, rehydration, ownership transfer) — not just initial provisioning. A resource in EU-WEST stays in EU-WEST for its entire lifecycle.

Override requires dual-approval: two approvers from different roles, with written justification and compensating controls. Every override produces a Merkle audit leaf at field granularity.

**Success criteria:** No resource is ever realized in a non-compliant zone without an audited, dual-approved override. Sovereignty is enforced end-to-end, not just at creation.

### UC-052: Prove Pipeline Integrity to Auditor

An external auditor requests proof that a specific provisioning request was processed correctly. DCM returns:
- **Inclusion proof:** Mathematical proof that the specific audit record exists in the Merkle tree
- **Consistency proof:** Mathematical proof that the tree has only grown since the last signed tree head (no deletions)
- **Request chain:** The complete hash chain from intent through realization with Ed25519 signatures from each service
- **Signed tree head:** The current root hash signed by DCM's identity

The auditor can independently verify these proofs without trusting DCM.

**Success criteria:** Auditor verifies integrity using only DCM's public key and the proof data. No trust relationship with DCM required. Verification completes in seconds regardless of tree size.

---

## Platform Operations

### UC-071: Onboard a New Tenant

An administrator creates a new tenant with profile assignment (e.g., "standard" for a production team, "dev" for a sandbox). RLS isolation is enforced immediately — the new tenant cannot see other tenants' data. RBAC is configured: which roles exist, which actors belong to which roles. The catalog is filtered: the tenant sees only catalog items they're authorized to request. The administrator submits a test request to verify full pipeline isolation.

**Success criteria:** Tenant data is isolated by RLS from first query. RBAC filters the catalog correctly. Test request flows through the complete pipeline with no cross-tenant data leakage.

### UC-081: Session Management and Auth Failover

An actor authenticates via the configured auth provider (built-in, Keycloak, LDAP, OIDC). Session tokens are issued with configurable TTL. Concurrent session limits are enforced. If the primary auth provider fails, existing sessions remain valid (cached) and new authentication routes to the failover chain. Session revocation propagates immediately.

**Success criteria:** Authentication works through all configured providers. Failover is transparent. Session revocation takes effect immediately. Concurrent session limits enforced.

### UC-091: Git-Based Request Ingress

A developer submits an infrastructure request via Git Pull Request. The PR identity is resolved to the same DCM actor as API/UI login. The request enters the standard pipeline. Policy dry-run feedback is posted as PR comments. Approval via PR review maps to DCM approval. On merge, the request is dispatched.

**Success criteria:** Git PR identity resolves to DCM actor. Policy feedback appears as PR comments. Merge triggers dispatch. Full audit trail links PR to DCM request.

---

## Federation

### UC-060: Cross-Instance Placement (Federation)

An organization runs two DCM instances: DCM-EMEA (EU datacenters) and DCM-APAC (Asia-Pacific datacenters). A consumer on DCM-EMEA requests a resource that, due to latency requirements for an APAC-facing application, should be placed in an APAC zone. The consumer does not need to know which DCM instance will fulfill the request.

**How federation works:**

1. **Peer DCM registration** — DCM-APAC is registered as a `peer_dcm` provider on DCM-EMEA. The registration includes sovereignty declarations, federation eligibility scope (which resource types and operations are permitted), and an mTLS certificate for the federation tunnel.

2. **Request enters normal pipeline on DCM-EMEA** — Layer assembly, policy evaluation, and placement all run locally. The consumer's sovereignty policy allows APAC placement for this resource type.

3. **Placement considers remote providers** — The placement engine treats DCM-APAC's providers as candidates alongside local providers. Cross-DCM confidence scoring applies: `cross_dcm_confidence = source_confidence × (tunnel_trust_score / 100)`. Remote providers are scored lower by the trust factor, but may win if local providers lack capacity or sovereignty eligibility.

4. **DCM-EMEA dispatches to DCM-APAC via federation tunnel** — The request payload is sent over the mTLS tunnel. DCM-APAC receives it, runs its own local policy evaluation (local policies govern — remote policies cannot override), and dispatches to its selected provider.

5. **Dual audit** — Audit records are written in both DCM instances with a shared `correlation_id`. DCM-EMEA records the outbound federation dispatch. DCM-APAC records the local pipeline execution and realization. Either instance can produce a complete audit trail for its portion.

6. **Realized state flows back** — DCM-APAC's provider callback flows back through the federation tunnel to DCM-EMEA. The consumer on DCM-EMEA sees the resource as OPERATIONAL with the APAC provider's realized fields.

**Federation constraints:**
- Sovereignty is verified before tunnel establishment — a classified-zone provider cannot participate in federation
- Storage providers default to `federation_eligibility: none` — data sovereignty prohibits storage federation unless explicitly authorized
- Remote DCMs cannot decommission local resources through a tunnel — decommission is always local
- Certificate rotation uses a 30-day overlap period so peers can update trust stores without coordinated downtime

**Success criteria:** Consumer requests a resource on DCM-EMEA and receives it from DCM-APAC without knowing the routing. Audit trail in both instances with shared correlation_id. Sovereignty enforced at both ends. Federation tunnel is mTLS-only.

---

## Integration

### UC-090: ITSM Integration (ServiceNow Change Management)

An organization requires that all infrastructure provisioning creates change records in ServiceNow, updates are tracked through CMDB configuration items, and decommission retires the CI. DCM integrates with ServiceNow via a **process_provider** — a bidirectional integration that enriches DCM entities with ITSM metadata without making ServiceNow a required dependency.

**Design principle:** DCM replaces the infrastructure ticket as the provisioning mechanism. ITSM integration is additive — it enriches, it does not gate (unless explicitly configured to do so).

**Outbound flow (DCM → ServiceNow):**

1. **ITSM Policy evaluates** — An ITSM Action policy fires on DCM lifecycle events. It is a side-effect policy: it triggers ITSM actions but does not block the pipeline by default.

2. **On `request.dispatched`** — The ITSM integration creates a ServiceNow change request (CHG record) containing the request details, requesting actor, tenant, resource type, and placement decision. The CHG number is stored on the DCM entity as `business_data.itsm_references[].external_id`.

3. **On `entity.realized`** — The ITSM integration updates the change request to "Implemented" and creates or updates a CMDB Configuration Item (CI) with the realized resource's details (IP address, provider, datacenter, ownership).

4. **On `entity.updated`** — The ITSM integration updates the CMDB CI and creates a new change task linked to the parent CHG.

5. **On `entity.decommissioned`** — The ITSM integration closes the change request, retires the CMDB CI, and updates the CI's lifecycle status.

**Inbound flow (ServiceNow → DCM):**

6. **Change Advisory Board (CAB) approval** — For organizations that require CAB approval before provisioning, the ITSM Policy can be configured as `block_until_approved`. The DCM pipeline pauses after the change request is created in ServiceNow. When the CAB approves, ServiceNow calls DCM's approval API (`POST /api/v1/admin/approvals/{uuid}:vote`) with the decision. The pipeline resumes.

7. **ITSM-initiated requests** — A ServiceNow workflow can create a DCM request via the Admin API, enabling "request infrastructure from ServiceNow" patterns for organizations transitioning from ticket-based provisioning.

**Safety guardrail:** `block_until_created` (wait for CHG creation before proceeding) requires a `block_timeout` — the pipeline never permanently stalls waiting for an ITSM system. If the timeout fires, the pipeline proceeds with a warning and the ITSM record is created asynchronously when the system recovers.

**Supported ITSM systems:** ServiceNow, Jira Service Management, BMC Remedy/Helix, Freshservice, PagerDuty, Opsgenie, ManageEngine, Cherwell, TOPdesk, and a generic REST adapter for others.

**Success criteria:** Every provisioning request has a corresponding ServiceNow change record. CMDB CIs are created on realization and retired on decommission. CAB approval gates work when configured. ITSM system unavailability does not block DCM operations (non-blocking default with configurable blocking mode). Bidirectional links between DCM entity_uuid and ServiceNow CHG/CI numbers.

---

## Pattern Catalog

### UC-100: Deploy a Resource Pattern from the Pattern Catalog

A consumer browses the Pattern Catalog section of the service catalog and selects "Standard Web Application." The catalog shows the pattern's components (network segment, database, app servers, load balancer, DNS), the parameters the consumer needs to provide, the dependency graph, and estimated cost.

The consumer fills in 6 parameters (app_name, environment, db_engine, db_storage_gb, app_replicas, expose_public) and submits. DCM decomposes the pattern into 6 constituent resources, resolves the dependency graph, and processes each constituent through the full pipeline — layer assembly, policy evaluation, placement, dispatch — independently. Each constituent may be placed with a different provider: the database with a managed database provider, the VMs with a compute provider, the load balancer with a network provider.

**Dependency resolution and binding fields in action:**

1. Network Segment provisioned first (no dependencies) → produces subnet_cidr, security_group_id
2. Database provisioned next → receives network values via binding fields → produces ip_address, port, credentials_ref
3. App Servers provisioned next → receive DB connection string and network config via binding fields → produce ip_addresses, port
4. Load Balancer provisioned next → receives app server IPs as backend pool via binding fields → produces vip_address
5. DNS records provisioned last → receive LB address via binding fields → public DNS conditional on consumer parameter

The consumer monitors aggregate progress ("4 of 6 constituents realized") and can drill into individual constituent status. On completion, the consumer has a fully wired application environment.

**Policy interaction:** No new policy types are needed. Each constituent is a standard resource type, and existing policies match naturally — sovereignty policies check every constituent, sizing policies check VMs, storage policies check the database, naming policies check DNS records. A policy block on any constituent blocks the entire pattern until the consumer resolves it.

**Failure handling:** If any required constituent fails, the pattern's lifecycle policy determines the response: rollback all realized constituents (default), continue in degraded mode, or notify and hold for manual intervention.

**Pattern authoring:** Platform engineers create patterns as compound Resource Type Specifications in the Resource Type Registry. Patterns define constituents, dependencies, binding fields, exposed parameters, and lifecycle policies. Consumers see them as catalog items indistinguishable from atomic offerings — the decomposition is invisible.

**Success criteria:** Single request produces a complete, wired application environment. Runtime values flow correctly between constituents. Each constituent is independently managed (own entity_uuid, audit trail, drift detection, lifecycle). Decommission reverses dependency order. No new control plane services, policy types, or API endpoints required — patterns use existing DCM machinery.

### Pattern Catalog — Architectural Overlay

A deployment pattern is a reusable, provider-agnostic blueprint that defines a collection of resources, their dependencies, their runtime wiring, and their operational policies — together delivering a service that no single provider offers.

**Example patterns:**

| Pattern | Constituents | What it delivers |
|---------|-------------|-----------------|
| Standard Web Application | 2 app VMs, 1 DB, 1 LB, 1 network, 3 DNS | Production web app with HA, monitoring, DNS |
| Secure Data Pipeline | 1 Kafka cluster, 2 workers, 1 object store, 1 network policy, 1 key | Encrypted ingest pipeline with data residency |
| Developer Sandbox | 1 VM, 1 namespace, 1 ephemeral DB, 1 port forward | Disposable dev environment with TTL auto-cleanup |
| Regulated Database Service | 1 PostgreSQL (HA), 1 backup, 1 key, 1 audit sink, 2 DNS | Database meeting FSI data handling requirements |
| Edge Compute Node | 1 bare metal, 1 MicroShift, 1 VPN, 1 monitor agent, 1 cert | Self-contained edge node with central management |

**The key property:** No single provider owns the pattern. The database might come from one provider, the VMs from another, the load balancer from a third. The pattern defines *what* is needed and *how the pieces connect* — DCM figures out *who* provides each piece.

### How Patterns Layer on DCM

```
┌──────────────────────────────────────────────────────┐
│                  PATTERN CATALOG                      │
│  Curated library of reusable deployment blueprints    │
│  Authored by: Platform Engineers                      │
│  Consumed by: Consumer Developers                     │
│  Stored in: Resource Type Registry (composite types)   │
├──────────────────────────────────────────────────────┤
│                  SERVICE CATALOG                       │
│  Provider-specific offerings + pattern offerings       │
│  Populated by: Providers (atomic) + Patterns (composite)│
├──────────────────────────────────────────────────────┤
│                  DCM CONTROL PLANE                     │
│  Decompose → Policy → Placement → Dispatch → Audit    │
│  Each constituent → full pipeline independently        │
├──────────────────────────────────────────────────────┤
│                  SERVICE PROVIDERS                     │
│  VM · Network · Database · DNS · Storage · Container   │
│  Fulfill individual constituents of a pattern          │
└──────────────────────────────────────────────────────┘
```

**The Pattern Catalog is not a new architectural component.** It is a curated view of the Resource Type Registry filtered to composite resource types. DCM already has all the machinery — the composite service definition model, dependency graphs, binding fields, and constituent dispatch. The Pattern Catalog adds the curation and consumer experience layer.

### How a Pattern Maps to DCM Constructs

| Pattern concept | DCM construct | Where it lives |
|----------------|--------------|----------------|
| The pattern itself | Composite Resource Type Specification | Resource Type Registry |
| The constituents | Resource Type references with dependency declarations | `constituents[]` in the composite spec |
| How pieces connect | Binding fields — runtime values from one constituent injected into another | `binding_fields[]` on dependent constituents |
| What the consumer fills in | Parameterized fields exposed at the pattern level | `fields_from_parent[]` mapping pattern params to constituent fields |
| Who provides each piece | `provided_by: external` (DCM places) or `provided_by: self` (composite service definition handles) | Per-constituent declaration |
| What happens on failure | Lifecycle policy on the composite spec | `on_constituent_failure: rollback_all` or `continue_degraded` or `notify` |
| Operational policies | Standard DCM policies scoped to constituent resource types | Policy match on resource_type per constituent |

### Pattern Definition Example — Standard Web Application

```yaml
resource_type: ApplicationStack.WebApp
version: "1.0.0"
entity_type: composite_resource

# Consumer-facing parameters
parameters:
  app_name: { type: string, required: true }
  environment: { type: string, required: true, constraint: { layer_reference: "environment" } }
  db_engine: { type: string, default: postgresql, constraint: { enum: [postgresql, mysql] } }
  db_storage_gb: { type: integer, default: 50, constraint: { min: 10, max: 1000 } }
  app_replicas: { type: integer, default: 2, constraint: { min: 1, max: 10 } }
  expose_public: { type: boolean, default: false }

constituents:
  - name: network_segment
    resource_type: Network.Segment
    provided_by: external
    depends_on: []
    required_for_delivery: required
    fields_from_parent:
      - { source: "environment", target: "environment" }
      - { source: "app_name", target: "segment_name_prefix" }

  - name: database
    resource_type: Database.Managed
    provided_by: external
    depends_on: [network_segment]
    required_for_delivery: required
    binding_fields:
      - { source: "network_segment.subnet_cidr", target: "database.network_cidr" }
      - { source: "network_segment.security_group_id", target: "database.security_group_id" }
    fields_from_parent:
      - { source: "db_engine", target: "engine" }
      - { source: "db_storage_gb", target: "storage_gb" }

  - name: app_server
    resource_type: Compute.VirtualMachine
    provided_by: external
    depends_on: [database, network_segment]
    required_for_delivery: required
    binding_fields:
      - { source: "database.ip_address", target: "app_server.config.db_host" }
      - { source: "database.port", target: "app_server.config.db_port" }
      - { source: "database.credentials_ref", target: "app_server.config.db_credentials_ref" }
      - { source: "network_segment.subnet_cidr", target: "app_server.network_cidr" }
    fields_from_parent:
      - { source: "app_name", target: "hostname_prefix" }
      - { source: "app_replicas", target: "replicas" }

  - name: load_balancer
    resource_type: Network.LoadBalancer
    provided_by: external
    depends_on: [app_server]
    required_for_delivery: required
    binding_fields:
      - { source: "app_server.ip_addresses", target: "load_balancer.backend_pool" }
      - { source: "app_server.port", target: "load_balancer.backend_port" }
    fields_from_parent:
      - { source: "expose_public", target: "public_listener" }

  - name: dns_internal
    resource_type: DNS.Record
    provided_by: external
    depends_on: [load_balancer]
    required_for_delivery: partial
    binding_fields:
      - { source: "load_balancer.vip_address", target: "dns_internal.target_address" }
    fields_from_parent:
      - { source: "app_name", target: "hostname" }

  - name: dns_public
    resource_type: DNS.Record
    provided_by: external
    depends_on: [load_balancer]
    required_for_delivery: optional
    condition: "parent.expose_public == true"
    binding_fields:
      - { source: "load_balancer.public_vip_address", target: "dns_public.target_address" }
    fields_from_parent:
      - { source: "app_name", target: "hostname" }

lifecycle_policy:
  on_constituent_failure: rollback_all
  decommission_order: reverse_dependency
```

### What the Consumer Submits

```json
POST /api/v1/requests
{
  "catalog_item_uuid": "webapp-standard-uuid",
  "fields": {
    "app_name": "pet-clinic",
    "environment": "production",
    "db_engine": "postgresql",
    "db_storage_gb": 100,
    "app_replicas": 3,
    "expose_public": true
  }
}
```

Six fields. The consumer has no idea this produces 6 resources across 4 different providers.

### What DCM Executes

```
Round 1: Network Segment (no deps)
  → Placed with EU-WEST network provider
  → Realized: subnet_cidr=10.5.0.0/24, security_group_id=sg-abc123

Round 2: Database (binding: network values injected)
  → config.network_cidr = 10.5.0.0/24, security_group_id = sg-abc123
  → Placed with EU-WEST database provider
  → Realized: ip_address=10.5.0.50, port=5432, credentials_ref=vault:secret/pet-clinic-db

Round 3: App Server (binding: DB + network values injected)
  → config.db_host=10.5.0.50, db_port=5432, db_credentials_ref=vault:secret/pet-clinic-db
  → Placed with EU-WEST compute provider, 3 replicas
  → Realized: ip_addresses=[10.5.0.10, 10.5.0.11, 10.5.0.12], port=8080

Round 4: Load Balancer (binding: app server IPs injected)
  → config.backend_pool=[10.5.0.10, 10.5.0.11, 10.5.0.12], backend_port=8080
  → Placed with EU-WEST network provider
  → Realized: vip_address=10.5.0.100, public_vip_address=203.0.113.50

Round 5: DNS records (binding: LB addresses injected)
  → Internal: pet-clinic.internal → 10.5.0.100
  → Public: pet-clinic.example.com → 203.0.113.50 (expose_public=true)

All 6 constituents realized → composite status: OPERATIONAL
```

### Policy Interaction with Patterns

No new policy types are needed. Each constituent is a standard resource type, and existing policies match naturally:

| Policy | Fires on | What it does |
|--------|---------|-------------|
| Sovereignty Gating Policy | All 6 constituents | Ensures everything lands in EU-WEST |
| VM sizing limits | App Server | Validates replicas and VM size within tenant tier |
| DB storage limits | Database | Validates db_storage_gb within allowed range |
| Network naming | Network Segment, DNS | Enforces naming conventions |
| Monitoring injection | App Server, Database | Injects monitoring agent config |
| Backup policy injection | Database | Injects backup schedule based on environment |

### Who Authors Patterns vs Who Consumes Them

| Role | Responsibility |
|------|---------------|
| **Platform Engineer** | Authors pattern definitions as compound Resource Type Specs. Defines constituents, dependencies, binding fields, exposed parameters, lifecycle policies. Registers in Resource Type Registry. Creates service catalog items. |
| **Policy/Compliance Owner** | Writes policies that apply to pattern constituents. Does not need pattern-specific awareness — policies match on resource types, which patterns decompose into. May write pattern-level policies (e.g., "all ApplicationStack types require monitoring on every constituent"). |
| **Consumer Developer** | Browses catalog, selects a pattern, fills in parameters, submits. Sees aggregate status. Can drill into constituent detail. Does not need to understand the decomposition. |
| **Infrastructure Operator** | Provides the atomic services that patterns compose. Registers providers for Compute, Network, Database, DNS — not for the pattern itself. |

### Pattern Interaction with Other DCM Features

| Feature | How it works with patterns |
|---------|--------------------------|
| **Drift detection** | Each constituent independently discoverable. Drift attributed per-constituent. |
| **Decommission** | Reverse-dependency-order teardown. Individual constituents can also be removed independently. |
| **Rehydration** | All constituents rebuilt in dependency order with current policies. Binding fields resolve against newly realized values. |
| **Sovereignty** | Every constituent independently sovereignty-checked. A pattern cannot span zones unless every constituent passes. |
| **Cost estimation** | Pattern cost = sum of constituent costs from provider catalog items. |
| **Audit** | Each constituent has its own Merkle audit trail. Composite entity links all constituent entity_uuids. |
| **Override** | Block on any constituent blocks the pattern. Consumer resolves per-constituent. Escalation routes to the responsible policy domain owner. |
| **Federation** | Constituents can be placed across DCM instances. Database local, app servers federated — if sovereignty permits. |

### Pattern Lifecycle

Patterns follow the standard DCM artifact lifecycle: `developing → proposed → active → deprecated → retired`. Adding an optional constituent (e.g., a cache layer) is a minor version bump — existing deployments unaffected, new requests get the new constituent. Removing a required constituent is a major version bump.

---

# Architecture Principles

- **Management plane, not provisioning tool.** DCM orchestrates lifecycle and enforces governance. Provisioning is delegated to service providers that implement the provider contract.
- **Three abstractions.** Everything in DCM is Data, Provider, or Policy. No exceptions. If a new concept doesn't map to one of these three, the abstraction model needs revision.
- **Provider-agnostic.** Any infrastructure platform is consumable through the same interface via naturalization/denaturalization. Providers declare capabilities (realize_resources, serve_data, authenticate, federate, execute_workflows) rather than being assigned rigid types. Multi-capability providers register once. No lock-in to any platform.
- **Discoverable.** DCM advertises its capabilities via a machine-readable endpoint. External systems query what DCM offers and subscribe to data streams without reading documentation. Providers declare what they need from DCM at registration; DCM matches needs to capabilities automatically.
- **Policy-mandatory.** Every request is policy-evaluated. This is not optional. Governance is the value proposition, not a feature toggle.
- **Tamper-evident audit.** Every mutation is recorded in a Merkle tree with Ed25519 signatures. Auditors can verify integrity without trusting DCM.
- **Sovereignty first-class.** Data residency is enforced at request time on every lifecycle operation, not discovered after deployment.
- **Minimal infrastructure.** PostgreSQL is the only required dependency. Everything else (Kafka, Vault, Keycloak) is optional and follows the Internal/External delegation pattern.
- **Declarative and idempotent.** Consumers declare desired state. DCM converges toward it. Resubmitting the same request produces the same result.
- **API-first.** All capabilities are accessible via API. The Web UI (RHDH) is a consumer of the same API. AEP conventions (snake_case, JSON, flat REST).

---

# Success Outcomes

Each capability area maps to a measurable outcome:

| **Outcome** | **Enabling Use Cases** |
|-----------|----------------------|
| Developers provision infrastructure without knowing which platform fulfills it | UC-010, UC-011, UC-014 |
| Compound applications deploy as a single catalog request with dependency resolution | UC-011, UC-100 |
| Policy violations are caught at request time with actionable guidance | UC-004, UC-012 |
| Sovereignty and data residency enforced on every lifecycle operation | UC-050 |
| Audit integrity is mathematically provable to external auditors | UC-052, UC-053 |
| Drift between intended and actual state is detected and remediated | UC-022 |
| New infrastructure platforms are addable without changing DCM core | UC-002 |
| Bootstrap requires only PostgreSQL — no middleware stack | UC-001 |
| Override governance provides flexibility without undermining compliance | UC-012, UC-053 |
| Full lifecycle management from request through decommission | UC-010, UC-020, UC-040 |
| Disaster recovery rebuilds from stored intent with current policy evaluation | UC-030 |
| Multi-region placement without consumer awareness of DCM instance topology | UC-060 |
| ITSM records created automatically without gating provisioning by default | UC-090 |
| Self-service reduces platform engineering ticket volume | UC-010, UC-011, UC-014 |

---

# Priority Summary

| **Priority** | **Count** | **Use Cases** |
|------------|---------|-------------|
| **P0 (Must Have)** | 16 | UC-001 through UC-004, UC-010 through UC-012, UC-014, UC-020, UC-022, UC-040, UC-050, UC-052, UC-071, UC-081, UC-100 |
| **P1 (Should Have)** | 9 | UC-005, UC-013, UC-021, UC-030, UC-051, UC-053, UC-070, UC-080, UC-091 |
| **P2 (Future)** | 6 | UC-023, UC-024, UC-031, UC-060, UC-072, UC-090 |

---

# Open Design Questions

| **ID** | **Question** | **Status** |
|--------|-------------|-----------|
| **DQ-1** | Application definition language — How should consumers define multi-resource applications? YAML manifests, API composition, external DSL, or catalog-only? | Open — See [ADR-016](adr/016-application-definition-language.md) |
| **DQ-2** | RHDH integration depth — Is RHDH the sole frontend, or should DCM expose its own lightweight UI for environments without RHDH? | Open |
| **DQ-3** | Spectral AEP linter — Should OpenAPI specs be linted in CI? Requires 3.1 compatibility verification. | Open — See [DISCUSSION-TOPICS item 7](DISCUSSION-TOPICS.md) |
| **DQ-4** | Kessel integration — What, if any, integration with Project Kessel for authorization? | Discussion only — See doc 44 |

---

# Appendix: Key Terms

- **Naturalization:** Translation of DCM's unified payload into a provider's native API format.
- **Denaturalization:** Translation of a provider's native response back into DCM's unified format.
- **Evaluation Context:** The complete payload, provenance chain, constraint accumulator, and governance scope passed to the policy engine for each evaluation.
- **Binding Fields:** Declarations in composite service definitions that connect realized outputs of one resource (e.g., an IP address) to inputs of a dependent resource (e.g., a VM's network config).
- **Merkle Tree:** A binary hash tree where modifying any leaf changes the root hash. Enables inclusion proofs (a record exists) and consistency proofs (the tree has only grown). RFC 9162.
- **RLS (Row-Level Security):** PostgreSQL feature that automatically scopes every query to the actor's tenant — application code cannot leak cross-tenant data.
- **Sovereignty Zone:** A geopolitical or regulatory boundary declared by providers and enforced by policy. Resources placed in a zone are governed by that zone's data residency rules.
- **Shadow Mode:** A policy lifecycle stage where the policy evaluates against real traffic and logs results without blocking requests. Used for safe validation before activation.
- **RHDH (Red Hat Developer Hub):** Backstage-based developer portal used as DCM's primary Web UI frontend.
- **AEP (API Enhancement Proposals):** Open-source API design guidelines adopted by DCM for consistent API conventions.
