---
Document Status: ✅ Complete
Document Type: Architecture Reference
---

# DCM Data Model — Control Plane Components

> **DCM-native control-plane runtime; no single UDLM contract counterpart.**
> The control-plane components are runtime implementations of the three UDLM
> abstractions (Data, Provider, Policy) — not a fourth abstraction and not a
> distinct UDLM contract. A peer DCM realization could decompose its control
> plane differently and still satisfy every UDLM contract.


**Document Status:** ✅ Complete
**Document Type:** Architecture Reference

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [udlm/foundations/foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: RUNTIME**
>
> Runtime implementations of the three abstractions — not a fourth abstraction


**Related Documents:** [Internal Component Authentication](internal-component-auth.md) | [Context and Purpose](https://github.com/croadfeldt/udlm/blob/main/foundations/context-and-purpose.md) | [Four States](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md) | [Resource/Service Entities](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md) | [Operational Models](https://github.com/croadfeldt/udlm/blob/main/lifecycle/operational-models.md) | [Policy Profiles](../governance-enforcement/policy-profiles.md)

---


The DCM Control Plane consists of **nine components** that implement the three foundational abstractions at runtime.

## 1. Purpose

> **Internal component authentication:** See [Internal Component Authentication](internal-component-auth.md) for the mTLS and interaction credential model governing all component-to-component calls within the DCM control plane.


This document formally defines the DCM control plane components that are referenced throughout the data model documents. Two components are defined here:

1. **The Request Orchestrator** — the event bus and coordinator of the request lifecycle pipeline
2. **The Cost Analysis Component** — the internal DCM component that provides cost signals for placement, catalog, and attribution

---

## 2. The Request Orchestrator

### 2.1 Role

The Request Orchestrator is the **event bus and pipeline coordinator** for all DCM request lifecycle operations. It does not perform any pipeline work itself — it listens for events, evaluates which components need to act on them, and routes work to the appropriate components.

The Request Orchestrator embodies DCM's **data-driven, policy-triggered orchestration model**: the pipeline is not a fixed procedural sequence. It is a cascade of event-condition-action responses, where policies define what happens when specific payload states are observed.

### 2.2 Data-Driven Orchestration Principle

**Policies ARE the orchestration.** The Request Orchestrator does not contain hardcoded pipeline logic. It publishes events to the Policy Engine; policies match on payload type and state; policy actions produce new payload states; those new states trigger further policy evaluations.

This means:
- Adding a new pipeline step = writing a new policy (no code change)
- Removing a step = deactivating a policy
- Changing when a step fires = changing a policy condition
- A static workflow (e.g., always require human approval for prod VMs) = a policy that always matches for those conditions
- A dynamic workflow (e.g., route to different approval processes based on cost) = a policy with conditional logic

Static and dynamic flows compose naturally — a static policy defines a guaranteed step; a dynamic policy defines a conditional step. Both are expressed as policies, evaluated by the same engine, producing deterministic outcomes.

**Determinism guarantee:** Dynamic execution remains deterministic because:
- The payload type vocabulary is a closed set
- Policy evaluation order within a domain level is deterministic (domain precedence)
- The payload mutation model is immutable (each policy produces a new payload version)
- The same input state always produces the same output state

### 2.3 The Payload Type Vocabulary

Every event in DCM carries a payload with a declared type. Policies pattern-match on these types. The payload type vocabulary is the foundational contract of the orchestration model.

```yaml
payload_types:
  # Request lifecycle
  request.initiated:          # consumer submitted a request
  request.intent_captured:    # Intent State written
  request.layers_assembled:   # layer assembly complete
  request.policies_evaluated: # all active policies evaluated
  request.placement_complete: # provider selected
  request.dispatched:         # sent to provider
  request.realized:           # provider confirmed realization
  request.failed:             # terminal failure
  request.cancelled:          # cancelled

  # Provider update
  provider_update.received:   # provider submitted update notification
  provider_update.evaluated:  # policy evaluation complete
  provider_update.accepted:   # accepted; Realized State updating
  provider_update.rejected:   # rejected; becomes drift

  # Drift and discovery
  discovery.cycle_complete:
  drift.detected:
  drift.resolved:

  # Recovery
  recovery.timeout_fired:
  recovery.late_response:
  recovery.compensation_triggered:

  # Governance
  policy.activated:
  layer.updated:
  profile.changed:
```

### 2.4 Event Routing Model

```
Event published: { type: "request.initiated", payload: {...}, entity_uuid: X }
  │
  ▼ Request Orchestrator receives event
  │   Routes to Policy Engine: "evaluate all policies matching request.initiated"
  │
  ▼ Policy Engine evaluates in domain precedence order
  │   Matching policies fire; payload mutations accumulated
  │   New payload state produced: { type: "request.layers_assembled", ... }
  │
  ▼ Request Orchestrator receives new event
  │   Routes to Policy Engine for next evaluation cycle
  │   (parallel if no data dependencies between active policies)
  │
  ▼ Continues until terminal state (request.realized or request.failed)
```

**Parallel execution:** Policies that have no data dependencies on each other evaluate concurrently. The Request Orchestrator tracks dependency declarations between policies and executes in parallel where safe.

### 2.5 Static Flow Support

Organizations that require guaranteed sequential flows express them as ordered policy sets:

```yaml
static_flow_policy_group:
  handle: "org/flows/prod-vm-approval-flow"
  concern_type: orchestration_flow
  ordered: true                # policies execute in declared sequence, not parallel
  policies:
    - step: 1
      handle: "org/policies/cost-check"
      condition: "request.initiated AND resource_type=Compute.VirtualMachine AND tenant.profile=prod"
      on_fail: halt
    - step: 2
      handle: "org/policies/manager-approval"
      condition: "request.cost_estimated > 500"
      on_fail: halt
    - step: 3
      handle: "org/policies/security-review"
      condition: "always"
      on_fail: halt
```

A static flow is a Policy Group with `concern_type: orchestration_flow` and `ordered: true`. The Request Orchestrator respects the declared order. Static flows integrate with dynamic policies — a dynamic policy can fire alongside the static flow steps.

### 2.5a Named Workflows vs Dynamic Policies — How They Compose

The Request Orchestrator does not distinguish between named workflows and dynamic policies — both arrive as events and are routed to the Policy Engine. The distinction is in *how they are declared*:

**Named Workflow Artifacts** (Orchestration Flow Policies with `ordered: true`) declare an explicit step sequence. An operator reading the workflow can see every step in order. Steps reference payload types from the closed vocabulary. Named workflows are the *explicit, visible skeleton* of a process.

**Dynamic Policies** (GateKeeper, Transformation, Recovery) fire when their match conditions are satisfied, regardless of workflow position. They are not declared in the workflow artifact. They are the *conditional behavior* that fills in the skeleton.

**Example — request lifecycle:**
```
Named workflow "system/workflows/request-lifecycle" declares:
  Step 1: request.initiated    → capture intent
  Step 2: request.intent_captured → run layer assembly
  Step 3: request.layers_assembled → run placement
  Step 4: request.placement_complete → dispatch

Dynamic policies also fire:
  GateKeeper "vm-size-limits" fires on request.layers_assembled
    if cpu_count > 32 → deny
  Transformation "inject-monitoring" fires on request.layers_assembled
    → adds monitoring_endpoint field
  Recovery "notify-on-timeout" fires on recovery.timeout_fired
    → NOTIFY_AND_WAIT action
```

The named workflow and the dynamic policies are independent artifacts. Adding a new GateKeeper does not modify the workflow. Modifying the workflow does not affect dynamic policies. They compose through the same Policy Engine evaluation on the same events.

### 2.6 Request Orchestrator Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Event routing | Receive all request lifecycle events; route to appropriate components |
| Pipeline coordination | Sequence component interactions per data dependencies |
| Timeout monitoring | Track dispatch_timeout and assembly_timeout; fire recovery triggers |
| Dependency resolution | For composite services, sequence component provisioning per dependency graph |
| Status tracking | Maintain current status of all in-flight requests; respond to status queries |
| Recovery coordination | On timeout/failure, invoke Recovery Policy evaluation |

---

## 3. The Cost Analysis Component

### 3.1 Role

The Cost Analysis Component is an **internal DCM control plane component** that provides cost signals to other components. It is not a billing system and not a provider type. It does not manage financial transactions, produce invoices, or serve as the authoritative financial record. It provides cost *signals* that DCM uses for placement decisions, pre-request estimation, and ongoing attribution.

The authoritative billing record lives in the organization's financial system. A billing system can register as an Information Provider to push authoritative cost data back into DCM for attribution records.

### 3.2 Three Cost Functions

**Function 1 — Pre-request cost estimation:**
Given a catalog item and assembled field values, compute the estimated lifecycle cost. Used by:
- Service Catalog describe endpoint (consumer sees cost before requesting)
- CI pipeline pre-validation (cost estimate in PR comment)
- Placement engine tie-breaker step 4 (cheapest eligible provider)

**Function 2 — Placement cost input:**
During Step 6 placement, provide current cost data per eligible provider for the requested resource type. If Cost Analysis data is unavailable, the placement engine falls back to static declared costs per REG-011.

**Function 3 — Ongoing cost attribution:**
For realized entities, track ongoing consumption and attribute costs to the owning Tenant. Consumed by OBS-005 (consumer cost view) and the resource describe endpoint (`estimated_cost_per_hour` field).

### 3.3 Cost Data Sources

The Cost Analysis Component ingests cost data from two sources, following the REG-011 hybrid model:

```yaml
cost_data_sources:
  static:
    source: provider_registration     # declared at provider registration time
    update_frequency: manual          # updated when rates change
    fields: [capex_per_unit, opex_per_unit_per_hour, currency]

  dynamic:
    source: external_cost_api         # external billing API or cloud pricing API
    registered_as: information_provider
    query_interval: PT1H
    fallback: static                  # use static if dynamic unavailable
    fallback_max_age: PT24H
```

### 3.4 Cost Estimation Model

```yaml
cost_estimation_request:
  catalog_item_uuid: <uuid>
  assembled_fields:
    cpu_count: 4
    memory_gb: 8
    storage_gb: 100
  tenant_uuid: <uuid>
  requested_duration: P30D           # optional; lifecycle estimate

cost_estimation_response:
  estimated_cost:
    per_hour: 0.32
    per_month: 230.40
    lifecycle_estimate: 691.20       # if requested_duration provided
    currency: USD
    confidence: high                 # high: current Cost Analysis data
                                     # medium: data > PT1H old
                                     # low: static fallback
    breakdown:
      - component: compute
        per_hour: 0.28
      - component: ip_allocation
        per_hour: 0.04
  cost_data_timestamp: <ISO 8601>
```

### 3.5 Cost Attribution for Realized Entities

```yaml
entity_cost_attribution:
  entity_uuid: <uuid>
  tenant_uuid: <uuid>
  billing_state: billable            # billable | non_billable | reduced_rate
  current_rate:
    per_hour: 0.32
    currency: USD
    rate_effective_since: <ISO 8601>
  monthly_accrual: 230.40
  cost_data_source: cost_analysis    # cost_analysis | static | unknown
```

### 3.6 Integration with Placement Engine

The placement engine queries Cost Analysis at step 4 of the tie-breaking hierarchy:

```
Step 4 — Cost Analysis (if available and determinable):
  Query Cost Analysis for each eligible provider
  Cost Analysis returns: estimated cost per unit per provider
  Placement engine prefers lowest cost among equally-ranked candidates
  If Cost Analysis unavailable: skip step 4; proceed to step 5
  # Cost Analysis unavailability never blocks placement
```

---

## 4. Related Policies

| Policy | Rule |
|--------|------|
| `CTL-001` | The Request Orchestrator is the single event bus for all request lifecycle events. No component communicates directly with another component outside of events published to the Request Orchestrator. |
| `CTL-002` | Policies ARE the orchestration. The Request Orchestrator does not contain hardcoded pipeline logic. Pipeline behavior is modified by adding, removing, or changing policies — not by changing the orchestrator. |
| `CTL-003` | Dynamic and static flows compose naturally. Static flows are Policy Groups with concern_type: orchestration_flow and ordered: true. Both types are evaluated by the same Policy Engine. |
| `CTL-004` | Cost Analysis is not a billing system. It provides cost signals for placement and attribution. The authoritative billing record lives in the organization's financial system, which may register as an Information Provider. |
| `CTL-005` | Cost Analysis unavailability never blocks placement. The placement engine falls back to static declared costs per REG-011 and skips the Cost Analysis tie-breaking step. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*

---

## 4. The Placement Engine

### 4.1 Role

The Placement Engine selects the specific Service Provider that will fulfill a resource request. It runs as step 6 of the Request Payload Processor assembly pipeline and is invoked by the Request Orchestrator after all policies have been evaluated and the assembled payload is ready for dispatch.

The Placement Engine does not make business decisions — those are made by policies (which inject constraints and preferences). The Placement Engine applies those constraints to find eligible providers, then deterministically resolves ties using a declared hierarchy.

### 4.2 Input and Output

**Input:**
- Assembled payload with full field-level provenance
- Sovereignty constraints (from compliance domain profile and any policy-injected constraints)
- Accreditation requirements (from Data/Capability Authorization Matrix)
- Preference scores or preferred provider UUIDs (if injected by Transformation policy)
- Tenant affinity declarations

**Output:**
- Selected provider UUID
- Placement reason (why this provider was selected)
- Sovereignty satisfaction record (which constraints were checked and passed)
- Reserve confirmation (provider confirmed it has capacity for this specific request)

This output is written to `placement.yaml` in the Requested Store directory.

### 4.3 Placement Algorithm — Six Steps

```
Step 1: Sovereignty Pre-Filter
  Eliminate any provider whose sovereignty_declaration does not satisfy
  the request's sovereignty constraints.
  → Providers that fail this step are never contacted.
  → If zero providers remain: RESERVE_QUERY_ALL_EXHAUSTED recovery trigger fires.

Step 2: Accreditation Filter
  Eliminate any provider that does not hold the required accreditations
  for the data classifications present in the assembled payload.
  → Checked against the active Data/Capability Authorization Matrix.
  → Providers with accreditation gaps are excluded.

Step 3: Capability Filter
  Eliminate any provider that does not declare support for the
  requested resource type and all required capabilities.
  → Based on provider registration catalog item declarations.

Step 4: Reserve Query
  Send a reserve query to each remaining candidate provider in parallel.
  → Providers have reserve_query_timeout to respond (profile-governed: PT5–30S).
  → Providers that do not respond within timeout: excluded from this placement cycle.
  → Providers that respond with INSUFFICIENT_CAPACITY: excluded; DCM updates
    internal capacity rating for that provider.
  → Providers that confirm capacity: advance to tie-breaking.

Step 5: Tie-Breaking (deterministic hierarchy)
  Applied when multiple providers confirmed capacity in Step 4:

  Priority 1: Policy preference
    A Transformation policy injected a preference_score or preferred_provider_uuid.
    Highest preference_score wins. preferred_provider_uuid is absolute — skips Steps 2-6.

  Priority 2: Provider declared priority
    Providers declare a numeric priority at registration (default: 50).
    Higher value = preferred when all else equal.

  Priority 3: Tenant affinity
    Tenant's Policy Group declares preferred providers for specific resource types.
    Affinity preference is a soft preference — does not override accreditation or sovereignty.

  Priority 4: Cost Analysis
    Cost Analysis component provides current cost per unit per candidate provider.
    Prefer lower total cost (CapEx + OpEx + licensing).
    Skip if: Cost Analysis unavailable, data stale > PT1H, or cost difference < 5%.

  Priority 5: Least loaded
    Prefer provider with lower current capacity utilization from reserve_query response.
    Skip if: utilization difference < 10%, or utilization data not returned.

  Priority 6: Consistent hash (final tiebreaker — always resolves)
    SHA-256(request_uuid + resource_type + sorted_candidate_uuids)
    Deterministic — same request always resolves to the same provider in a stable cluster.
    Never round-robin.

Step 6: Reserve Confirmation
  Notify the selected provider that its reservation is confirmed.
  Other providers that responded to the reserve query receive a reservation release.
  → Prevents capacity holds from accumulating across providers for the same request.
```

### 4.4 Reserve Query Protocol

```yaml
reserve_query:
  query_uuid: <uuid>               # idempotency key
  entity_uuid: <uuid>
  resource_type: Compute.VirtualMachine
  resource_type_spec_version: "2.1.0"
  requested_fields:
    cpu_count: 4
    memory_gb: 8
    storage_gb: 100
  sovereignty_requirements:
    data_residency: EU
  reservation_hold_ttl: PT5M      # provider holds capacity for this duration
                                   # released when: confirmed, rejected, or TTL expires
```

```yaml
reserve_query_response:
  query_uuid: <uuid>
  provider_uuid: <uuid>
  status: confirmed | insufficient_capacity | capability_not_supported
  capacity_held_until: <ISO 8601>   # if confirmed
  utilization_pct: 42               # current load; used for Step 5 tiebreaking
  cost_per_hour: 0.32               # if Cost Analysis integration enabled
  currency: USD
```

### 4.5 Placement Configuration

```yaml
placement_engine_config:
  reserve_query_timeout: PT10S       # profile-governed default
  parallel_reserve_queries: true     # always true; all candidates queried simultaneously
  max_candidates_per_placement: 10   # cap on parallel reserve queries
  cost_freshness_max: PT1H
  cost_difference_threshold: 0.05   # 5% — skip cost step if within this band
  utilization_difference_threshold: 0.10  # 10% — skip utilization step if within this band
  reservation_hold_ttl: PT5M
```

### 4.6 Placement Failure and Recovery

When placement cannot find an eligible provider:

| Failure Reason | Recovery Trigger |
|---------------|-----------------|
| All providers fail sovereignty filter | `RESERVE_QUERY_ALL_EXHAUSTED` |
| All providers fail accreditation filter | `RESERVE_QUERY_ALL_EXHAUSTED` |
| All providers respond INSUFFICIENT_CAPACITY | `RESERVE_QUERY_ALL_EXHAUSTED` |
| All reserve queries time out | `RESERVE_QUERY_ALL_EXHAUSTED` |

The `RESERVE_QUERY_ALL_EXHAUSTED` trigger fires the active Recovery Policy. Default action per profile: standard/prod → `NOTIFY_AND_WAIT`; dev → `RETRY` with exponential backoff.

### 4.7 Placement System Policies

| Policy | Rule |
|--------|------|
| `PLC-001` | Sovereignty pre-filter runs before any provider is contacted. Providers that fail sovereignty constraints never receive reserve queries. |
| `PLC-002` | Accreditation filter runs before reserve queries. Providers without required accreditations for the payload's data classifications are excluded. |
| `PLC-003` | Reserve queries are sent in parallel to all eligible candidates. Sequential querying is not permitted — it introduces latency and prevents fair capacity comparison. |
| `PLC-004` | The consistent hash tiebreaker is always the final tiebreaker. It ensures deterministic provider selection for identical inputs without round-robin non-determinism. |
| `PLC-005` | A confirmed reservation hold must be released when not used — either by confirmation dispatch or by explicit release on timeout. Capacity holds must not accumulate silently. |
| `PLC-006` | The Placement Engine never selects a provider based solely on network position or co-location. Every selection is based on declared constraints, policies, and the tie-breaking hierarchy. |

---

## 5. The Lifecycle Constraint Enforcer

### 5.1 Role

The Lifecycle Constraint Enforcer is a DCM control plane component that monitors all realized entities against their declared lifecycle constraints and fires expiry actions when constraints are reached. It is the authoritative enforcer of TTL, expiry date, and maximum execution time declarations.

Lifecycle constraint enforcement is a DCM concern — not a provider concern. The provider does not need to know about or implement any TTL logic.

### 5.2 What It Monitors

The Lifecycle Constraint Enforcer monitors three categories of constraint:

**Category 1 — Entity TTL:**
Duration-based: entity expires T duration after a reference point (realization, creation, last modification).

**Category 2 — Entity Expiry Date:**
Calendar-based: entity expires at an absolute timestamp.

**Category 3 — Process Resource Maximum Execution Time:**
Process Resources must declare `max_execution_time`. The Enforcer monitors all executing Process Resources and fires `on_max_exceeded` when the limit is reached.

### 5.3 Monitoring Loop

```
Lifecycle Constraint Enforcer runs continuously:

  Every cycle (interval: PT1M for standard/prod; PT5M for minimal/dev):

    Query Realized Store for entities with:
      lifecycle_state IN [OPERATIONAL, SUSPENDED, EXECUTING]
      AND lifecycle_constraints declared
      AND NOT already in terminal state

    For each entity:
      Compute time_remaining = constraint_expiry - now()

      If time_remaining <= warn_before_expiry:
        If warn_not_yet_sent:
          Emit: entity.ttl_warning notification
          Record: WARNING_EMITTED in entity provenance

      If time_remaining <= 0:
        Execute on_expiry action (see Section 5.4)
```

### 5.4 Expiry Action Execution

When a lifecycle constraint fires, the Enforcer executes the declared `on_expiry` action:

| Action | Behavior |
|--------|---------|
| `decommission` | Submit a decommission request through the standard pipeline — produces Requested State, dispatches to provider, full audit trail |
| `suspend` | Submit a suspend request through the standard pipeline |
| `notify` | Fire `entity.ttl_expired` notification to entity owner; no automated action |
| `review` | Entity enters PENDING_EXPIRY_ACTION state; Platform Admin and owner notified |
| `escalate` | Immediately escalate to Platform Admin; entity enters PENDING_EXPIRY_ACTION state |

**Grace period:** Expiry actions are not immediate. The Enforcer respects the declared `grace_period` (default PT1H) — the action fires `grace_period` after the constraint expires, giving human operators a window to intervene.

**Action failure:** If the expiry action fails to execute (provider unreachable, dependency conflict), the entity enters `PENDING_EXPIRY_ACTION` state (LTC-005). The Enforcer retries per the active Recovery Policy. Platform Admin is notified with urgency: high.

### 5.5 Expiry Audit Records

Every expiry-related event produces an audit record:

```yaml
audit_record:
  action: EXPIRY_WARNING | EXPIRY_ACTION_FIRED | EXPIRY_ACTION_FAILED |
          PENDING_EXPIRY_ACTION_ENTERED
  actor:
    type: system
    system_actor:
      component: lifecycle_constraint_enforcer
      trigger: ttl_reached | expires_at_reached | max_execution_time_reached
  entity_uuid: <uuid>
  details:
    constraint_type: ttl | expires_at | max_execution_time
    constraint_value: <declared value>
    action_taken: decommission | suspend | notify | review | escalate
    grace_period_remaining: <duration>
```

### 5.6 Process Resource Enforcement

Process Resources require `max_execution_time` (mandatory). The Enforcer monitors all EXECUTING Process Resources:

```
Process Resource enters EXECUTING state
  │
  ▼ Enforcer records: execution_started_at; computes execution_timeout_at
  │
  ▼ On every monitoring cycle:
  │   If now() >= execution_timeout_at:
  │     Emit: PROCESS_TIMEOUT event
  │     Entity state → FAILED
  │     Recovery Policy: COMPENSATION_FAILED trigger if resources were modified
  │     Notification: entity owner + Platform Admin (urgency: high)
```

### 5.7 Lifecycle Constraint Enforcer Policies

| Policy | Rule |
|--------|------|
| `LCE-001` | The Lifecycle Constraint Enforcer runs as a continuous monitor. It does not rely on provider callbacks or event triggers for expiry detection — it polls based on declared constraints. |
| `LCE-002` | Expiry actions are submitted through the standard DCM request pipeline. Decommission-on-expiry produces a Requested State record with `actor: system/lifecycle-constraint-enforcer`. |
| `LCE-003` | The Enforcer respects the declared grace_period before firing expiry actions. Grace period gives human operators a window to intervene before automated action. |
| `LCE-004` | Process Resource max_execution_time enforcement fires immediately on breach — no grace period. Hung processes are failed immediately to prevent resource leaks. |
| `LCE-005` | Expiry action failures enter PENDING_EXPIRY_ACTION state. The Enforcer retries per the active Recovery Policy. Indefinite retry without escalation is not permitted. |

---

## 6. The Search Index

### 6.1 Role

The Search Index is a **non-authoritative, queryable projection** of the GitOps stores (Intent Store and Requested Store). It enables millisecond-latency queries against stored entities without traversing Git history, while the GitOps stores remain the authoritative source of truth.

The Search Index is a PostgreSQL store contract. It has its own registration, health check, and sovereignty declaration. It is never the source of truth — if the Search Index and the GitOps store disagree, the GitOps store wins unconditionally.

### 6.2 What It Indexes

The Search Index maintains a projection of key fields from Intent State and Requested State records, enabling queries without retrieving full payloads from Git:

```yaml
search_index_record:
  entity_uuid: <uuid>
  entity_handle: <string>
  resource_type: Compute.VirtualMachine
  resource_type_category: Compute
  tenant_uuid: <uuid>
  lifecycle_state: OPERATIONAL
  drift_status: clean
  provider_uuid: <uuid>
  deployment_posture: prod
  compliance_domains: [hipaa]
  data_classifications: [restricted]      # highest classification in entity
  created_at: <ISO 8601>
  updated_at: <ISO 8601>
  cost_per_hour: 0.32
  currency: USD
  git_path: intent-store/tenant-uuid/Compute/VirtualMachine/entity-uuid/intent.yaml
  # git_path is the pointer back to the authoritative record
  tags: { environment: production, team: payments }
```

### 6.3 Required Query Operations

| Operation | Description |
|-----------|-------------|
| `find_by_uuid(entity_uuid)` | Return index record for a single entity |
| `find_by_tenant(tenant_uuid, filters)` | Return all entities for a Tenant with optional field filters |
| `find_by_resource_type(fqn, filters)` | Return all entities of a resource type |
| `find_by_provider(provider_uuid, filters)` | Return all entities hosted at a provider |
| `find_by_lifecycle_state(state, tenant_uuid)` | Return entities in a given lifecycle state |
| `find_by_drift_status(status, tenant_uuid)` | Return drifted or clean entities |
| `find_by_data_classification(classification)` | Return entities containing data of a given classification |
| `full_text_search(query, tenant_uuid)` | Full-text search across handle, display_name, tags |

All queries return the `git_path` — consumers fetch the full payload from Git if needed.

### 6.4 Consistency Model

The Search Index is **eventually consistent** with the GitOps stores. There is a defined maximum staleness:

```yaml
search_index_consistency:
  max_staleness: PT5M         # index must be within 5 minutes of GitOps store
  profile_overrides:
    prod: PT2M
    fsi: PT1M
    sovereign: PT1M
  on_staleness_exceeded:
    action: degrade_with_warning    # serve results with staleness warning
    alert: platform_admin           # alert on staleness exceeding 2× max
  rebuild_on_recovery: true         # full index rebuild from Git history on failure
  rebuild_max_duration: PT4H        # must complete within 4 hours for standard+
```

### 6.5 Unavailability Behavior

If the Search Index is unavailable:
- DCM degrades search operations gracefully: returns a `503 Service Degraded` response with a reference to the authoritative Git store
- Writes are not affected — GitOps stores are written directly; the index is updated asynchronously
- On recovery: the Search Index rebuilds from Git history
- No data is lost if the index is lost — it is always reconstructable from Git

### 6.6 Search Index Policies

| Policy | Rule |
|--------|------|
| `SIX-001` | The Search Index is non-authoritative. GitOps stores win on any disagreement. Consumers must be prepared to receive a git_path and fetch from the authoritative store. |
| `SIX-002` | The Search Index must be rebuildable from Git history at any time. Implementations that cannot perform a full index rebuild are non-conformant. |
| `SIX-003` | Search Index staleness beyond the profile-governed maximum triggers a platform admin alert. Staleness is surfaced in query responses — consumers are never served stale data silently. |
| `SIX-004` | Search Index unavailability degrades queries without impacting writes. Write operations proceed directly to the authoritative GitOps stores regardless of Search Index availability. |

---


---

## 7. The Drift Reconciliation Component

### 7.1 Role

The Drift Reconciliation Component compares the Discovered State of entities against their Realized State to detect, classify, and respond to drift. It is the consumer of Discovered Store data and the producer of drift records that feed into the Policy Engine for response evaluation.

Drift Reconciliation is purely a read-and-compare component — it never writes to the Realized Store. It reads Discovered State, reads Realized State, computes differences, classifies severity, and fires events into the Request Orchestrator. The Policy Engine and Recovery Policies determine what happens next.

### 7.2 Inputs and Outputs

**Inputs:**
- Discovered State snapshots (from Discovered Store, written by Discovery Scheduler)
- Realized State snapshots (from Realized Store)
- Resource Type Specifications (for field criticality declarations used in severity classification)
- Active governance profile (for magnitude thresholds used in severity classification)

**Outputs:**
- Drift records (written to Drift Record Store — a lightweight operational store)
- Drift events published to the Request Orchestrator: `drift.detected`, `drift.resolved`, `drift.severity_escalated`
- Unsanctioned change events: `unsanctioned_change.detected`

### 7.3 Comparison Algorithm

```
Discovery cycle completes → Discovered State snapshot written
  │
  ▼ Drift Reconciliation Component receives discovery.cycle_complete event
  │
  ▼ For each entity UUID in the discovery snapshot:
  │
  │   Load: latest Realized State snapshot for entity UUID
  │   Load: Discovered State snapshot (just written)
  │   Load: Resource Type Specification (field criticality per field)
  │
  ▼ Field-by-field comparison:
  │   For each field in Realized State:
  │     Does Discovered State contain this field?
  │     If yes: are the values equal?
  │     If no: field is absent — severity based on field criticality
  │   For each field in Discovered State not in Realized State:
  │     New field appeared — severity based on field criticality
  │
  ▼ Severity classification (per field):
  │   Field criticality (from Resource Type Spec) × Change magnitude (profile-governed)
  │   → severity matrix → minor | significant | critical
  │   Unsanctioned? → elevate one level
  │   Multiple drifted fields? → overall = highest individual severity
  │
  ▼ Unsanctioned check:
  │   Is there a Requested State record that explains this change?
  │   If yes: sanctioned change (may still be drift if realization didn't match)
  │   If no: unsanctioned_change.detected event fired (in addition to drift.detected)
  │
  ├── No drift detected:
  │     Update entity.last_discovered_at
  │     Update entity.drift_status = clean
  │     No drift record created
  │
  └── Drift detected:
        Create drift record
        Publish drift.detected to Request Orchestrator
        Policy Engine evaluates → response action
```

### 7.4 Drift Record Structure

```yaml
drift_record:
  uuid: <uuid>
  entity_uuid: <uuid>
  detected_at: <ISO 8601>
  discovery_snapshot_uuid: <uuid>        # the Discovered State snapshot that triggered this
  realized_state_uuid: <uuid>            # the Realized State snapshot compared against

  overall_severity: minor | significant | critical
  unsanctioned: true | false             # true if no corresponding Requested State record

  drifted_fields:
    - field_path: "fields.memory_gb"
      realized_value: 8
      discovered_value: 16
      field_criticality: medium           # from Resource Type Spec
      change_magnitude: significant       # 100% increase, threshold: standard 10-50%
      field_severity: significant
      elevated_for_unsanctioned: true     # elevated from significant → critical

  status: open | acknowledged | resolved | escalated
  resolution:
    resolved_at: <ISO 8601|null>
    resolution_type: reverted | updated_definition | accepted | escalated | null
    resolved_by_requested_state_uuid: <uuid|null>
```

### 7.5 Drift Resolution Tracking

Drift records are not resolved by the Drift Reconciliation Component — they are resolved by the Policy Engine's response actions. The Drift Reconciliation Component monitors for resolution:

```
REVERT action taken:
  New Requested State submitted → provider reverts → new Realized State written
  Next discovery cycle: Discovered State matches new Realized State
  Drift Reconciliation: no drift detected → drift_record.status = resolved
  drift.resolved event published

UPDATE_DEFINITION action taken:
  Consumer submits UPDATE_DEFINITION → new Realized State written with discovered values
  Next discovery cycle: Discovered State matches new Realized State
  Drift record.status = resolved with resolution_type: updated_definition

Entity decommissioned:
  Drift record.status = resolved with resolution_type: decommissioned
```

### 7.6 Governance Matrix Integration

Before classifying a discovered change as drift, the Drift Reconciliation Component evaluates the governance matrix to determine if the change is expected:

```
Field value in Discovered State differs from Realized State
  │
  ▼ Check: Is there a governance matrix rule that permits this provider
  │        to make this type of change to this field?
  │
  ├── Yes → This may be a Provider Update Notification that wasn't submitted
  │   DCM logs a warning: "Provider changed field without submitting update notification"
  │   Still treated as drift — provider should have submitted update notification
  │
  └── No → Standard drift detection; severity classification runs
```

### 7.7 Drift Reconciliation Policies

| Policy | Rule |
|--------|------|
| `DRC-001` | The Drift Reconciliation Component never writes to the Realized Store. It produces drift records and events only. |
| `DRC-002` | Drift detection runs after every discovery cycle. An entity with no corresponding Realized State record is an orphan candidate — not a drift event. |
| `DRC-003` | Unsanctioned changes are always elevated one severity level above the matrix classification. An unsanctioned significant drift is reported as critical. |
| `DRC-004` | Drift records are retained until the entity is decommissioned plus the configured audit retention period. They are not deleted on resolution — resolution is recorded within the record. |
| `DRC-005` | Drift detection produces events into the Request Orchestrator. The Policy Engine determines the response action. The Drift Reconciliation Component does not initiate remediation directly. |


## 8. Related Policies — Full Component Set

| Policy | Rule |
|--------|------|
| `CTL-001` | The Request Orchestrator is the single event bus for all request lifecycle events. No component communicates directly with another component outside of events published to the Request Orchestrator. |
| `CTL-002` | Policies ARE the orchestration. The Request Orchestrator does not contain hardcoded pipeline logic. |
| `CTL-003` | Dynamic and static flows compose naturally. Static flows are Policy Groups with concern_type: orchestration_flow and ordered: true. |
| `CTL-004` | Cost Analysis is not a billing system. It provides cost signals for placement and attribution. |
| `CTL-005` | Cost Analysis unavailability never blocks placement. |
| `PLC-001` through `PLC-006` | Placement Engine policies (see Section 4.7) |
| `LCE-001` through `LCE-005` | Lifecycle Constraint Enforcer policies (see Section 5.7) |
| `SIX-001` through `SIX-004` | Search Index policies (see Section 6.6) |
| `DRC-001` through `DRC-005` | Drift Reconciliation policies (see Section 7.7) |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
