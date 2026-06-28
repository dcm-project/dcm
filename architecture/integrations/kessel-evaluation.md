# DCM — Kessel Integration Evaluation

**Document Status:** 📋 Draft — For Discussion
**Document Type:** Integration Evaluation — Pre-Implementation
**Purpose:** This document evaluates the potential integration of DCM with the [Kessel project](https://github.com/project-kessel) for identity/access management and resource inventory. It is intended as a basis for discussion with the Kessel development team. **No architectural changes should be made to DCM based on this document until alignment with the Kessel team is confirmed.**

**Related Documents:** [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Universal Group Model](https://github.com/croadfeldt/udlm/blob/main/observability/universal-groups.md) | [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) | [Four States](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md) | [Accreditation and Zero Trust](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) | [Control Plane Components](../control-plane/components.md) | [Provider Callback Authentication](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-callback-auth.md)

**Related Projects:** [project-kessel](https://github.com/project-kessel) | [SpiceDB](https://github.com/authzed/spicedb) | [Google Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/)

---

## 1. Executive Summary

Kessel is a Red Hat project providing two capabilities: **Kessel Relations** (Relationship-Based Access Control built on SpiceDB, a Google Zanzibar implementation) and **Kessel Asset Inventory** (a hybrid cloud resource state tracking service with a common Protobuf/gRPC API).

DCM has architecturally similar needs in both areas. The evaluation concludes:

- **Kessel Relations** has strong alignment with DCM's access control requirements. The permission model maps cleanly, and the operational benefits — Zanzibar-style consistency, scalable graph traversal, shared source of truth across Red Hat products — are meaningful. Integration path exists via DCM's Auth Provider abstraction.

- **Kessel Inventory** has partial alignment with DCM's Discovered State store. The fit is real but narrower than it might appear: Kessel Inventory is a current-state snapshot system; DCM's inventory is a four-state lifecycle model with field-level provenance, drift detection, and append-only audit. Integration path exists via DCM's data store abstraction.

**Recommended next step:** Discussion with the Kessel development team to validate assumptions, confirm schema extensibility for DCM-specific resource types, and understand the Kessel Relations API stability and sovereign/air-gapped deployment model.

---

## 2. What Kessel Provides

### 2.1 Kessel Relations

Kessel Relations is an authorization service built on [SpiceDB](https://github.com/authzed/spicedb), which implements the [Google Zanzibar](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/) consistent global authorization model.

**Core model — Relationship-Based Access Control (ReBAC):**
- Resources and subjects are defined in a typed schema
- Relationships between subjects and resources are stored as tuples: `subject:X relation:Y object:Z`
- Permissions are computed by evaluating the relationship graph: "does user X have permission `submit_request` on tenant T?" traverses all paths from X to T through groups, roles, and other relationships
- Transitive relationships are handled natively: if user X is a member of group G, and group G has `admin` on tenant T, X inherits `admin` on T

**Zanzibar consistency model:**
- Snapshot reads: consistent reads at a point in time
- Zookie tokens: causality tokens that guarantee "read your own writes" without requiring full global linearizability — after writing a relationship tuple, the response includes a zookie; subsequent reads with that zookie are guaranteed to observe the write

**gRPC API surface (from the Kessel project):**
- `CheckPermission(subject, permission, resource)` → allow/deny
- `LookupResources(subject, permission, resource_type)` → list of resources subject has permission on
- `LookupSubjects(resource, permission, subject_type)` → list of subjects that have permission on resource
- `WriteRelationships(tuples)` → write relationship tuples
- `DeleteRelationships(filter)` → remove relationship tuples

### 2.2 Kessel Asset Inventory

Kessel Asset Inventory is a resource tracking service designed to provide a unified inventory view across hybrid cloud infrastructure — OpenShift clusters, RHEL systems, edge devices, and other Red Hat-managed resources.

**Core model:**
- Resources are described using a common Protobuf schema with a typed `ResourceType` and a `Spec` for type-specific fields
- Current state is tracked as an upsertable snapshot — last-write wins
- gRPC streaming API for push (providers send state updates) and pull (consumers query current state)
- Integration with Kessel Relations for auth-filtered inventory queries: "what resources of type X does subject Y have access to?"

**Intended use case:** Giving tools like ACM (Advanced Cluster Management), Insights, and the Hybrid Cloud Console a single query surface for "what exists across my estate?"

---

## 3. DCM's Current Model — What Needs to Be Understood

Before evaluating integration, it is important to characterize what DCM already has in both areas.

### 3.1 DCM's Authorization Model

DCM's current authorization model has five components working together:

**Auth Providers** (doc 19) — DCM delegates authentication to registered Auth Providers (LDAP, OIDC, FreeIPA, Active Directory, mTLS). Auth Providers are registered through the standard Provider contract. Multiple Auth Providers can be active simultaneously. Auth Providers return: authenticated actor identity, group memberships, roles.

**Universal Group Model** (doc 15) — DCM groups (`DCMGroup`) are typed by `group_class`. The classes relevant to authorization:
- `tenant_boundary` — the ownership and isolation boundary; every resource entity belongs to exactly one tenant
- `cross_tenant_authorization` — the formal mechanism for Tenant A to grant Tenant B access to a specific resource
- `policy_collection` — groups that activate policy sets
- DCMGroup membership is the basis for role resolution and policy application

**RBAC via role mapping** — Auth Providers map external groups to DCM roles (`consumer`, `platform_admin`, `sre`, etc.). The Policy Engine uses roles + group membership to evaluate access.

**Five-check boundary model** (doc 26) — Every interaction crosses five checks in sequence: identity verification → authorization → accreditation → data/capability matrix → sovereignty. Checks 1 and 2 are RBAC. Checks 3–5 are DCM-specific and involve accreditation records, data classification, and sovereignty zones.

**Cross-tenant authorization records** — When Tenant A grants Tenant B access to a resource, a `cross_tenant_authorization` DCMGroup is created. The Policy Engine checks for the existence of this record when evaluating cross-tenant requests.

**What DCM asks for in authorization decisions:**
1. Does actor X have role Y within tenant T?
2. What catalog items is actor X allowed to see? (RBAC-filtered list)
3. Can actor X perform operation O on resource R? (role + tenant ownership)
4. Does tenant T have a cross-tenant authorization to use resource R owned by tenant T2?
5. Is actor X a member of DCMGroup G with the required quorum? (approval gates, `authorized` tier)

### 3.2 DCM's Inventory Model

DCM's inventory is the **Four States model** (doc 02). This is meaningfully different from a general-purpose resource inventory.

**Intent State** — The consumer's declared desired state. Stored as a GitOps artifact (PR-based workflow). Immutable after creation. Not a snapshot — it is the authoritative record of what was requested and why.

**Requested State** — The assembled payload after layer enrichment, policy evaluation, and placement resolution. Write-once. Contains the full data model payload that was dispatched to the provider, including field-level provenance tracing every value back to its source.

**Realized State** — An append-only event stream of what the provider actually built. Every realization event is a new record — not an upsert. Contains field-level provenance from the provider. The relationship between a Realized State record and its corresponding Requested State record is explicit and mandatory.

**Discovered State** — An ephemeral snapshot of what the provider currently reports as existing, obtained through active discovery polling. Used by the Drift Reconciliation Component to compare against Realized State.

**What DCM asks for in inventory decisions:**
1. What is the current lifecycle state of entity UUID X? (Realized State read)
2. What resources does tenant T own? (indexed query over Realized State)
3. What entities have relationship R to entity X? (Entity Relationship Graph, doc 09)
4. What is the field-level provenance of field F on entity X? (Realized State metadata)
5. What entities are currently drifted? (Drift Record Store, DRC component output)
6. What did we discover vs what do we have as realized? (Drift comparison)
7. What happened to entity X over its full lifecycle? (Audit Store, time-indexed)

---

## 4. Integration Analysis

### 4.1 Kessel Relations — Authorization Backend

#### Mapping DCM's Permission Model to SpiceDB

DCM's five authorization questions map to SpiceDB as follows:

```
# Proposed SpiceDB schema for DCM
definition user {}

definition group {
  relation member:      user | group#member
  relation parent_group: group
  permission member     = member + parent_group->member
}

definition tenant {
  relation member:      user | group#member
  relation admin:       user | group#member
  relation platform_admin: user | group#member
  permission submit_request  = member + admin + platform_admin
  permission manage_resources = admin + platform_admin
  permission administer       = platform_admin
}

definition resource {
  relation owner_tenant:    tenant
  relation authorized_tenant: tenant    # cross-tenant authorization
  relation viewer:          user | group#member
  permission read   = owner_tenant->member + authorized_tenant->member + viewer
  permission modify = owner_tenant->admin
  permission decommission = owner_tenant->admin
}

definition dcm_group {
  relation member:    user | group#member
  relation quorum_threshold: integer  # NOTE: see Section 4.1.2
}
```

**Question 1** (does actor X have role Y in tenant T?) → `CheckPermission(user:X, permission:submit_request, tenant:T)`

**Question 2** (what catalog items can actor X see?) → `LookupResources(user:X, permission:read, resource_type:catalog_item)`

**Question 3** (can actor X do operation O on resource R?) → `CheckPermission(user:X, permission:modify, resource:R)`

**Question 4** (does tenant T have cross-tenant authorization on resource R?) → `CheckPermission(tenant:T#member, permission:read, resource:R)` — satisfied if `authorized_tenant` relationship exists

**Question 5** (approval gate quorum) — **Does not map cleanly to SpiceDB.** See Section 4.1.2.

#### 4.1.2 Approval Gate Quorum — The Gap

DCM's `authorized` tier approval requires N of M members of a declared DCMGroup to record decisions before an operation proceeds. SpiceDB is a membership and permission graph — it answers "does this subject have this permission?" but it does not count decisions or track quorum state across time.

**Resolution:** The approval gate workflow stays in DCM's Policy Engine regardless of Kessel integration. Kessel Relations handles who *can* approve (membership in the DCMGroup); DCM's Approval Store tracks who *has* approved and whether quorum is reached.

This is a clean boundary: Kessel answers the structural question ("is this actor authorized to vote?"); DCM answers the state question ("how many valid votes have been recorded?").

#### 4.1.3 DCM's Entity Relationship Graph is NOT an Authorization Graph

This is a critical distinction. DCM's entity relationships — `requires`, `constituent`, `shareable`, `allocated_from`, `peer` — are **operational relationships between infrastructure resources**, not access control relationships. They express: "VM X requires Storage Y", "Composite C has constituent VM X."

These must **not** be stored in Kessel Relations. They are:
- Semantically different from access control (lifecycle implications, not permissions)
- DCM-specific (not meaningful to any other system consuming Kessel)
- Owned by DCM's entity lifecycle model

DCM's Entity Relationship Graph (doc 09) remains entirely in DCM regardless of Kessel integration.

#### 4.1.4 Checks 3–5 of the Five-Check Boundary Model

DCM's five-check boundary model (identity → authorization → accreditation → data matrix → sovereignty) maps to Kessel Relations only for checks 1 and 2. Checks 3–5 are DCM-specific:

- **Accreditation** (check 3): Does the target provider hold the required accreditation for the data classification present? This involves DCM's Accreditation Registry and is not a subject/permission/resource question.
- **Data/Capability Matrix** (check 4): Is each field permitted to cross this boundary given its classification? This involves DCM's Governance Matrix policies.
- **Sovereignty** (check 5): Is the target endpoint within the sovereignty boundary? This involves DCM's Sovereignty Zone declarations.

None of checks 3–5 can be delegated to Kessel Relations. They remain in DCM's Policy Engine.

#### 4.1.5 Integration Path via Auth Provider Abstraction

DCM's Auth Provider abstraction (doc 19) is the natural integration point. Kessel Relations would register as a DCM Auth Provider or External Policy Evaluator:

```yaml
kessel_relations_auth_provider:
  provider_type: auth_provider
  auth_mode: kessel_rebac
  endpoint: https://kessel-relations.internal:9000
  schema_ref: <DCM SpiceDB schema version>
  
  # What this provider handles:
  handles:
    - check_permission       # CheckPermission calls
    - lookup_resources       # LookupResources calls
    - lookup_subjects        # LookupSubjects calls
  
  # What stays in DCM's Policy Engine:
  does_not_handle:
    - accreditation_checks
    - data_classification_matrix
    - sovereignty_checks
    - approval_gate_quorum
```

DCM's Policy Engine calls the Kessel Relations provider for authorization questions (checks 1 and 2) and evaluates checks 3–5 internally. The five-check sequence is preserved; only the implementation of checks 1–2 changes.

**Zookie handling:** DCM's API Gateway must thread zookie tokens through the request lifecycle: when a relationship is written (e.g., a new cross-tenant authorization is created), the resulting zookie is stored and used for subsequent permission checks in the same request context, guaranteeing consistency.

---

### 4.2 Kessel Inventory — Discovered State Store

#### 4.2.1 The Fit

Of DCM's four stores, **Discovered State** is the only one Kessel Inventory could plausibly replace. The reasons:

- Discovered State is the most ephemeral store — it is overwritten on each discovery cycle
- Discovered State does not require immutability or append-only semantics — it represents "what the provider reports right now"
- Discovered State is the "current state of infrastructure" — exactly what Kessel Inventory is designed to track
- Other Red Hat tools consuming Kessel Inventory would benefit from seeing the same discovered state that DCM uses for drift detection

The other three stores — Intent, Requested, and Realized — **cannot** be replaced by Kessel Inventory:
- Intent and Requested State require GitOps semantics (PR workflow, immutability, version history)
- Realized State requires append-only event stream semantics with field-level provenance and hash chain integrity
- None of DCM's lifecycle or audit requirements are in scope for Kessel Inventory

#### 4.2.2 The Schema Alignment Question

DCM's Discovered State uses the same unified data model format as Realized State — the DCM Resource Type Spec schema. Kessel Inventory uses a Protobuf-defined common resource schema.

For standard resource types (Compute, Network, Storage that map to well-known infrastructure concepts), the alignment is likely achievable. For DCM-specific resource types (Automation.AnsiblePlaybook, Platform.KubernetesCluster, custom org-defined types), schema extension or mapping is required.

**Open question for Kessel team:** How extensible is the Kessel Inventory resource type schema? Can DCM register custom resource types? Is there a type registry mechanism analogous to DCM's Resource Type Registry?

#### 4.2.3 Drift Detection Logic Stays in DCM

Kessel Inventory is a state store, not a drift detection system. Even if DCM uses Kessel Inventory as the Discovered State store, the Drift Reconciliation Component (doc 25, DRC domain) remains entirely in DCM:

- DRC queries Kessel Inventory for current discovered state
- DRC compares discovered state against DCM's Realized State
- DRC classifies differences by field criticality and change magnitude
- DRC produces Drift Records with SECURITY_DEGRADATION, BROKEN_REFERENCE, UNSANCTIONED_CHANGE classifications
- DRC writes Drift Records to DCM's Drift Record Store

Kessel Inventory's role is purely as the data source for the "what currently exists" side of the comparison. The intelligence stays in DCM.

#### 4.2.4 Integration Path via data store Abstraction

DCM's data store abstraction (doc 11) is the natural integration point. The Discovered Store would be implemented as a `storage_sub_type: snapshot_store` data store backed by Kessel Inventory:

```yaml
kessel_inventory_(prescribed infrastructure):
  provider_type: (prescribed infrastructure)
  storage_sub_type: snapshot_store
  backend: kessel_inventory
  endpoint: https://kessel-inventory.internal:9001
  
  # DCM uses this provider for:
  used_for: discovered_state
  
  # Write contract: provider calls POST /api/v1/instances/{id}/status
  # which DCM translates to Kessel Inventory upsert
  write_model: upsert_current_state
  
  # Read contract: DRC queries Kessel for discovered state
  read_model: streaming_query_by_type_and_tenant
```

This means the Kessel Inventory integration requires **no changes to DCM's data model** — only a new data store implementation. The Drift Reconciliation Component calls the same Discovered State Store interface; the underlying implementation happens to be Kessel Inventory.

---

## 5. Deployment and Sovereignty Considerations

### 5.1 Air-Gapped and Sovereign Deployments

DCM's `sovereign` profile requires air-gapped operation with no external dependencies. Any Kessel integration must support:

- Local/on-premises Kessel deployment (not cloud-hosted)
- Offline operation when Kessel is temporarily unavailable (cached authorization decisions for read-only operations)
- mTLS between DCM and Kessel instances

**Open question for Kessel team:** What is Kessel's deployment model for sovereign/air-gapped environments? Is there a supported on-premises deployment path? What is the operational footprint?

### 5.2 Multi-Instance Federation

DCM supports federation between multiple DCM instances (doc 22). A federated deployment may have multiple Kessel Relations instances (one per region or sovereignty zone) or a single shared instance.

**Open question for Kessel team:** How does Kessel Relations handle multi-region replication? Can SpiceDB schema and relationship data be replicated across sovereignty boundaries? What are the consistency guarantees in a federated topology?

### 5.3 Failure Mode Analysis

If Kessel Relations is unavailable, DCM cannot evaluate authorization checks 1–2 of the five-check model, which means DCM cannot process any requests. This is a critical dependency.

**Required mitigation strategies:**
- Read-through cache for CheckPermission results (short TTL, profile-governed)
- Circuit breaker: if Kessel is unavailable for >N consecutive checks, DCM enters a safe-deny mode (no new requests accepted) rather than a fail-open mode
- Kessel Relations HA deployment is a prerequisite, not optional

**Open question for Kessel team:** What HA and disaster recovery patterns are recommended for production Kessel Relations deployments?

---

## 6. Questions for the Kessel Team

The following questions should be addressed before any integration work begins:

### 6.1 Kessel Relations

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | What is the current API stability level of the Kessel Relations gRPC API? Are breaking changes expected? | DCM needs a stable contract to build against |
| 2 | Does Kessel Relations support on-premises / air-gapped deployment? What is the operational footprint? | Required for DCM's `sovereign` profile |
| 3 | How does the SpiceDB schema evolve? Is there a migration path when the DCM permission model changes? | Schema evolution is a production concern |
| 4 | Can Kessel Relations store relationships at the scale DCM requires? How many relationship tuples per tenant at what query latency? | DCM may have thousands of cross-tenant authorization records per deployment |
| 5 | How does Kessel handle the zookie (consistency token) lifecycle? Are zookies scoped to a namespace/tenant, or global? | Relevant to DCM's multi-tenant isolation model |
| 6 | Is Kessel Relations multi-tenant natively, or does DCM need to namespace its SpiceDB schema? | Critical for DCM's tenant isolation requirements |
| 7 | What is the intended integration pattern for other Red Hat products (ACM, Insights)? How would DCM's usage interoperate? | Kessel's value to DCM is partly the shared source of truth across RH products |
| 8 | Does Kessel Relations have a concept equivalent to DCM's "cross-tenant authorization"? How are trust grants between tenants modeled? | Core to DCM's resource sharing model |

### 6.2 Kessel Inventory

| # | Question | Why It Matters |
|---|----------|----------------|
| 9 | How extensible is Kessel Inventory's resource type schema? Can DCM register custom resource types? | DCM has domain-specific resource types not in Kessel's default schema |
| 10 | What is the write model? Last-write-wins upsert, or versioned? Does Kessel Inventory support the discovered state pattern (full overwrite on each discovery cycle)? | DCM's Discovered Store is a full-replacement snapshot per discovery cycle |
| 11 | How does Kessel Inventory integrate with Kessel Relations for auth-filtered queries? Is the integration already built, or planned? | Core to the value of using Kessel Inventory |
| 12 | What is the data retention model? Does Kessel Inventory keep history or only current state? | DCM needs "current state" only for Discovered State; history is in DCM's Audit Store |
| 13 | What is the API stability level for Kessel Inventory? | Same concern as #1 for Relations |
| 14 | Is there a reference implementation of a Kessel Inventory provider for a Kubernetes/OpenShift resource type? | DCM would follow this pattern for its Service Providers |

### 6.3 Joint Architecture Questions

| # | Question | Why It Matters |
|---|----------|----------------|
| 15 | Is the Kessel project open to DCM contributing Resource Type definitions and SpiceDB schema extensions to the upstream? | Reduces divergence risk; benefits broader community |
| 16 | How does Kessel handle sovereign data — data that must not cross jurisdictional boundaries? | Critical for DCM's sovereignty model |
| 17 | What is the recommended pattern for bootstrapping the Kessel-DCM trust relationship? (mTLS? OIDC? Service account?) | Required for DCM's zero-trust model |
| 18 | Does Kessel have a compatibility matrix for Red Hat platform versions (OpenShift, RHEL)? | DCM targets the same platforms |

---

## 7. Proposed Integration Architecture (Pending Kessel Alignment)

This section describes the target architecture **conditional on positive answers to the questions in Section 6**. It should not be implemented until validated with the Kessel team.

### 7.1 Kessel Relations as DCM Auth Provider

```
DCM Request Pipeline:
  │
  ▼ Auth Provider (Kessel Relations):
  │   Check 1: identity verification via mTLS certificate
  │   Check 2: CheckPermission(actor, operation, tenant/resource) via Kessel Relations gRPC
  │            ← returns allow/deny + zookie token
  │
  ▼ DCM Policy Engine (internal):
  │   Check 3: Accreditation check (DCM Accreditation Registry)
  │   Check 4: Data/Capability Matrix (DCM Governance Matrix)
  │   Check 5: Sovereignty check (DCM Sovereignty Zone registry)
  │
  ▼ All five checks pass → request proceeds to layer assembly
```

**Impact on DCM architecture:**
- Auth Provider registration: new `auth_mode: kessel_rebac` in doc 19
- Cross-tenant authorization DCMGroup: writes to both DCM Group Registry AND Kessel Relations tuple store
- RBAC evaluation: replaced by Kessel Relations CheckPermission call for checks 1–2
- Group membership sync: DCM Auth Providers (LDAP, OIDC) continue to manage authentication; group memberships are mirrored to Kessel Relations for use in permission evaluation

### 7.2 Kessel Inventory as DCM Discovered State Store

```
Discovery Cycle:
  │
  ▼ Discovery Scheduler triggers provider discovery
  │
  ▼ Service Provider returns RealizedStatePayload stream
  │   (current state in DCM Unified Data Model format)
  │
  ▼ Kessel Inventory data store:
  │   Translates DCM format → Kessel Inventory Protobuf schema
  │   Upserts to Kessel Inventory (replaces prior discovered state)
  │
  ▼ Drift Reconciliation Component (unchanged):
  │   Queries Kessel Inventory for discovered state
  │   Compares against DCM Realized State
  │   Produces Drift Records (classification, severity, field detail)
  │   Writes Drift Records to DCM Drift Record Store
```

**Impact on DCM architecture:**
- Discovered State Store: implement as data store backed by Kessel Inventory
- No changes to data model, drift detection logic, or Drift Reconciliation Component
- Resource type mapping: DCM Resource Type Specs → Kessel Inventory resource types (new tooling required)

---

## 8. What Does Not Change Regardless of Integration

The following DCM capabilities remain entirely in DCM regardless of how the Kessel integration develops:

| Capability | Why it stays in DCM |
|-----------|---------------------|
| Intent State Store (GitOps) | GitOps semantics, PR workflow, immutability — not in scope for Kessel |
| Requested State Store (write-once) | Assembled payload with full provenance — DCM-specific |
| Realized State Store (append-only event stream) | Hash-chained, tamper-evident, field-level provenance — DCM-specific |
| Approval gate quorum tracking | State-tracking across time — Kessel Relations answers membership, not quorum |
| Five-check boundary model (checks 3–5) | Accreditation, data classification, sovereignty — DCM-specific |
| Entity Relationship Graph | Operational relationships between resources — not access control |
| Field-level provenance | Source tracking per field — not in scope for Kessel |
| Drift detection logic and classification | DRC component — Kessel Inventory is a data source, not a drift engine |
| Audit trail (hash chain) | Tamper-evident audit — DCM-specific requirement |
| Resource lifecycle state machine | REQUESTED → OPERATIONAL → DECOMMISSIONED — DCM-specific |
| Policy Engine | Gating Policy, Transformation, Recovery, Orchestration Flow policies — DCM-specific |
| Authority Tier model | Approval routing — DCM-specific governance model |

---

## 9. System Policies (Proposed — Pending Validation)

These policies should be reviewed and confirmed after Kessel team alignment:

| Policy | Rule |
|--------|------|
| `KESSEL-001` | Kessel Relations, if registered as a DCM Auth Provider, handles authorization checks 1 and 2 of the five-check boundary model only. Checks 3–5 remain in DCM's Policy Engine and cannot be delegated. |
| `KESSEL-002` | DCM's entity relationship graph (operational relationships between infrastructure resources) must never be stored in Kessel Relations. Only access-control relationships (actor→group→tenant→resource permissions) are stored in Kessel Relations. |
| `KESSEL-003` | Kessel Inventory, if registered as a DCM data store for Discovered State, holds only ephemeral current-state snapshots. Intent, Requested, and Realized State stores remain in DCM-managed data stores. |
| `KESSEL-004` | If Kessel Relations is unavailable, DCM enters safe-deny mode: no new requests are accepted. Fail-open behavior is not permitted under any profile. |
| `KESSEL-005` | Zookie tokens from Kessel Relations CheckPermission responses must be threaded through the DCM request context to guarantee consistency across authorization checks within the same request. |
| `KESSEL-006` | Cross-tenant authorization DCMGroups that are backed by Kessel Relations must be written atomically: the DCM Group Registry record and the Kessel Relations tuple must both succeed or both fail. Partial writes are treated as failures. |
| `KESSEL-007` | DCM sovereign profile deployments require a locally-deployed Kessel instance. Cloud-hosted Kessel is not permitted for sovereign deployments. This requirement must be confirmed as feasible with the Kessel team. |

---

## 10. Open Items Before Integration Can Begin

| # | Item | Owner | Blocking? |
|---|------|-------|-----------|
| 1 | Kessel team review of Section 6 questions | Kessel team | Yes |
| 2 | Kessel Relations API stability confirmation | Kessel team | Yes |
| 3 | Sovereign/air-gapped deployment validation | Kessel team | Yes (for sovereign profile) |
| 4 | SpiceDB schema design review for DCM permission model | DCM + Kessel | Yes |
| 5 | Kessel Inventory resource type extensibility confirmation | Kessel team | Yes (for inventory integration) |
| 6 | HA/DR pattern review for production Kessel deployment | Kessel team | Yes |
| 7 | DCM Auth Provider interface extension for `kessel_rebac` mode | DCM team | No (can design in parallel) |
| 8 | DCM data store implementation for Kessel Inventory | DCM team | No (can design in parallel) |
| 9 | Zookie lifecycle management design in DCM request pipeline | DCM team | No (can design in parallel) |
| 10 | Resource type mapping: DCM Resource Type Specs → Kessel Inventory schema | DCM + Kessel | No (can design in parallel) |

---

*Document maintained by the DCM Project. For questions, contributions, or to schedule the Kessel alignment session see [GitHub](https://github.com/dcm-project).*
