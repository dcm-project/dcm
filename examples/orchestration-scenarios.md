---
Document Status: 📋 Draft — Initial Specification
Document Type: Examples — DCM Orchestration Scenarios
Established: 2026-05-26
Maps to: udlm/foundations/examples.md
---

# DCM Orchestration Scenarios

> **Builds on the canonical examples in UDLM**:
> [udlm/foundations/examples.md](https://github.com/croadfeldt/udlm/blob/main/foundations/examples.md).
> UDLM's examples illustrate the four-states lifecycle at contract level
> (intent → requested → realized → discovered). This document illustrates
> DCM-specific orchestration features: full dependency group orchestration,
> timeout enforcement and cancellation propagation, provider-side internal
> lifecycle reconciliation, retry mechanics, scoring-driven placement, and
> recovery policy actions.

---

## 1. Three-Tier Application — full dependency group orchestration

A consumer deploys a three-tier application (database, backend, frontend)
using a single dependency-group submission. This scenario shows DCM's
end-to-end orchestration: dependency parsing, sequential dispatch, field
injection, and failure handling.

### 1.1 Consumer submission

```json
POST /api/v1/request-groups
{
  "group_handle": "pet-clinic-deploy",
  "on_failure": "cancel_remaining",
  "timeout": "PT2H",
  "requests": [
    {
      "ref": "db",
      "catalog_item_uuid": "<postgres-uuid>",
      "fields": { "engine": "postgresql", "storage_gb": 50, "environment": "staging" }
    },
    {
      "ref": "backend",
      "catalog_item_uuid": "<vm-uuid>",
      "fields": { "app_name": "pet-clinic", "environment": "staging" },
      "depends_on": [
        { "ref": "db",
          "wait_for": "realized",
          "inject_fields": [
            { "from_field": "realized_fields.ip_address",      "to_field": "fields.config.db_host" },
            { "from_field": "realized_fields.port",            "to_field": "fields.config.db_port" },
            { "from_field": "realized_fields.credentials_ref", "to_field": "fields.config.db_credentials_ref" }
          ]
        }
      ]
    },
    {
      "ref": "frontend",
      "catalog_item_uuid": "<vm-uuid>",
      "fields": { "app_name": "pet-clinic", "replicas": 2, "environment": "staging" },
      "depends_on": [
        { "ref": "backend",
          "wait_for": "realized",
          "inject_fields": [
            { "from_field": "realized_fields.ip_address", "to_field": "fields.config.api_host" },
            { "from_field": "realized_fields.port",       "to_field": "fields.config.api_port" }
          ]
        }
      ]
    }
  ]
}
```

### 1.2 DCM orchestration

```
Request Orchestrator parses the dependency graph (DAG validation passes)
  ▼ All three requests get entity UUIDs immediately
  │   db:       ACKNOWLEDGED
  │   backend:  PENDING_DEPENDENCY (waiting on db: realized)
  │   frontend: PENDING_DEPENDENCY (waiting on backend: realized)
  ▼ Policy Engine evaluates the db request
  │   GateKeeper: staging environment authorized for tenant
  │   Validation: storage_gb within tier limits
  │   Transformation: monitoring agent injected
  ▼ Placement Engine selects PostgreSQL provider for db
  │   Score: 87; tie-breaker: cost analysis prefers eu-west-prod-2
  ▼ Dispatcher dispatches db with PT15M dcm_interaction credential
  ▼ Provider realizes PostgreSQL instance
  │   Callbacks: ip_address: 10.0.1.50, port: 5432, credentials_ref: vault:secret/pet-clinic-db
  ▼ db.realized event published
  ▼ Request Orchestrator unblocks backend
  │   Injects: config.db_host = 10.0.1.50
  │   Injects: config.db_port = 5432
  │   Injects: config.db_credentials_ref = vault:secret/pet-clinic-db
  ▼ backend enters standard assembly with injected fields
  ▼ Placement selects KubeVirt provider for backend
  ▼ Dispatcher dispatches backend; provider realizes
  │   Callbacks: ip_address: 10.0.2.30, port: 8080
  ▼ backend.realized event published
  ▼ Request Orchestrator unblocks frontend
  │   Injects: config.api_host = 10.0.2.30
  │   Injects: config.api_port = 8080
  ▼ frontend dispatched; provider realizes 2 VM replicas
  │   Callbacks: ip_addresses: [10.0.3.10, 10.0.3.11], port: 443
  ▼ All requests REALIZED
  ▼ request.group_completed event (urgency: medium)
  ▼ Consumer sees: pet-clinic group complete
```

### 1.3 What the consumer sees

```
pet-clinic-deploy (group) — completed
├── pet-clinic-db (Database.PostgreSQL) — OPERATIONAL
│   ip_address: 10.0.1.50, port: 5432
├── pet-clinic-backend (Compute.VirtualMachine) — OPERATIONAL
│   ip_address: 10.0.2.30, config.db_host: 10.0.1.50
└── pet-clinic-frontend (Compute.VirtualMachine × 2) — OPERATIONAL
    ip_addresses: [10.0.3.10, 10.0.3.11], config.api_host: 10.0.2.30
```

### 1.4 Failure variation: backend fails

If backend dispatch fails (provider returns error):

```
backend status → FAILED
  ▼ on_failure: cancel_remaining applies
  ▼ frontend (PENDING_DEPENDENCY) → CANCELLED with failure_reason: dependency_failed
  ▼ db (already REALIZED) is NOT auto-decommissioned (it's its own entity)
  ▼ Group status → failed
  ▼ Consumer notified: backend failed, frontend cancelled, db remains
```

The consumer may then decommission db manually if desired, or re-submit
backend separately to recover.

---

## 2. VM Provisioning — timeout enforcement and cancellation propagation

A standard VM request with dispatch_timeout enforcement. This scenario
illustrates DCM's timeout and recovery mechanics.

### 2.1 Setup

- Active profile: `prod`
- `dispatch_timeout`: PT30M
- Resource type: `Compute.VirtualMachine`
- Recovery profile: `recovery-notify-and-wait`

### 2.2 Sequence

```
Consumer submits VM request
  ▼ Standard nine-step assembly; placement selects eu-west-prod-1
  ▼ Dispatcher dispatches; entity → PROVISIONING; dispatch_timeout timer starts
  ▼ ... PT35M elapse without provider callback ...
  ▼ DISPATCH_TIMEOUT recovery trigger fires
  ▼ Recovery Policy evaluation:
  │   Profile recovery-notify-and-wait → NOTIFY_AND_WAIT with deadline: PT4H
  ▼ Entity transitions to TIMEOUT_PENDING
  ▼ Consumer notification fired with urgency: high
  │   "Provider eu-west-prod-1 did not respond within PT30M. Decide:
  │    DRIFT_RECONCILE, DISCARD_AND_REQUEUE, or DISCARD_NO_REQUEUE."
  ▼ ... consumer reviews and selects DISCARD_AND_REQUEUE within deadline ...
  ▼ DCM:
  │   1. Sends best-effort cancellation to provider
  │   2. Entity → FAILED (terminal for this cycle)
  │   3. New request cycle created from original Intent State
  │   4. Placement re-runs (eu-west-prod-1 may now be marked degraded)
  │   5. Selects eu-west-prod-2; dispatches
  ▼ eu-west-prod-2 realizes; entity → OPERATIONAL
  ▼ Orphan detection runs on eu-west-prod-1 to find any leaked resources
  │   from the original dispatch
  ▼ Orphan candidates surface to platform admin if found
```

The Recovery Policy gives operators control over how aggressive cleanup
should be. In `recovery-discard-and-requeue` profile, the same scenario
would auto-decide DISCARD_AND_REQUEUE without consumer interaction.

---

## 3. IP Allocation — provider-side internal lifecycle reconciliation

An IP allocation showing how DCM consumes provider-side internal lifecycle
states (without modeling them in DCM) and reconciles to DCM's lifecycle
vocabulary.

### 3.1 Setup

- Resource type: `Network.IPAddress`
- Provider: InfoBlox IPAM (declares both `realize_resources` and
  `serve_data` capabilities)
- Tenant: AppTeam

### 3.2 Sequence

```
Consumer submits IP allocation request for VM-A
  ▼ Placement selects InfoBlox; reserve_query confirms capacity in
    subnet 10.1.0.0/16
  ▼ Dispatcher dispatches: allocation_request for IPAddress in this subnet
  ▼ InfoBlox internal lifecycle:
  │   1. reserved   — internal hold during the allocation
  │   2. allocated  — IP carved out
  │   3. committed  — DCM dispatched with metadata
  ▼ Provider callback: PUT /api/v1/instances/{ip-resource-id}/status
  │   { lifecycle_state: REALIZED, fields: { address: 10.1.45.23,
  │     prefix_length: 32, address_family: IPv4, allocated_from_pool_uuid: ... } }
  ▼ DCM:
  │   - Validates mTLS + interaction credential
  │   - Verifies entity ownership binding (resource_id matches dispatch)
  │   - Writes Realized State; sets is_current = true
  │   - Emits entity.realized event
  ▼ Entity → OPERATIONAL with full DCM lifecycle visibility
  │   IP-entity ownership: AppTeam Tenant
  │   AllocationRecord relationship: allocated_from IPAddressPool (owned by NetworkOps)
```

### 3.3 InfoBlox internal lifecycle mapping

DCM does NOT model InfoBlox's `reserved → allocated → committed`. It
consumes the final state via the standard provider callback API. The
provider-internal phases are visible only through:

- The InfoBlox provider's audit trail (provider-side)
- DCM lifecycle events emitted by the provider via the lifecycle event API
  (optional)

DCM's Realized State is updated only when the provider declares the
allocation final and pushes the callback.

### 3.4 Reconciliation cycle

Twelve hours later, the Discovery Service runs against InfoBlox:

```
Discovery query: list all allocated IPs in subnet 10.1.0.0/16
  ▼ Discovery returns InfoBlox's current truth
  ▼ DCM compares to Realized State
  ▼ 10.1.45.23 still allocated to VM-A — no drift
  ▼ Discovery snapshot written; no drift event
```

If a discrepancy is found (e.g., InfoBlox reports the IP allocated to
different owner), DCM fires `drift.detected`. Recovery Policy evaluates;
default action: ESCALATE for IP-level drift in production profile.

---

## 4. Scoring-driven placement — high-value request with mixed signals

A consumer submits a request that scores into the `verified` tier; this
scenario shows scoring-driven approval routing and how multiple signals
compose.

### 4.1 Setup

- Active profile: `standard`
- Resource type: `Compute.VirtualMachine`
- Request: 64-vCPU VM, 256GB RAM, in production environment
- Scoring signals:
  - Signal 1 (size): high (64-vCPU is above typical)
  - Signal 2 (cost): medium (estimated $850/month)
  - Signal 3 (compliance): low (no PHI/PCI fields)
  - Signal 4 (consumer history): high (consumer has clean record)
  - Signal 5 (provider accreditation richness): high

### 4.2 Sequence

```
Consumer submits request
  ▼ Layer assembly + Policy Engine evaluation
  ▼ All GateKeeper policies pass (boolean gates: compliance, sovereignty)
  ▼ Scoring Model computes risk score
  │   Signal weights × signal values = 67
  ▼ Profile standard threshold lookup:
  │   - auto:       max_score 24
  │   - reviewed:   max_score 59
  │   - verified:   max_score 79 ← request scores into this band
  │   - authorized: max_score 100
  ▼ Required tier: verified
  ▼ Approval record created with required_tier_weight: 3
  ▼ Two qualified reviewers notified via Notification Service
  ▼ Reviewer A records APPROVE via Admin API
  │   pipeline_status: pending_verified (1 of 2 approvals)
  ▼ Reviewer B records APPROVE via ServiceNow (recorded_via: servicenow)
  │   pipeline_status: activating (2 of 2 approvals)
  ▼ Dispatcher resumes pipeline
  ▼ Placement Engine selects highest-scoring provider
  ▼ VM realized; entity → OPERATIONAL
```

The audit trail includes both reviewers' decisions with `recorded_via`
provenance ("dcm_admin_ui" for Reviewer A, "servicenow" for Reviewer B).

---

## 5. Retry-driven recovery — transient provider failure

A request dispatched during transient provider degradation; this scenario
shows the `recovery-aggressive-retry` posture in action.

### 5.1 Setup

- Active profile: `dev` with tenant override to `recovery-aggressive-retry`
- Resource type: `Compute.VirtualMachine`
- Provider: `compute-prod-1` (transiently overloaded)

### 5.2 Sequence

```
Consumer submits VM request
  ▼ Dispatcher dispatches; provider returns 503 (overloaded)
  ▼ ASSEMBLY_TIMEOUT recovery trigger fires
  │   (dispatch returned error before realization; treated as timeout
  │    in aggressive-retry posture for re-attempt)
  ▼ Recovery Policy: RETRY with exponential backoff
  │   max_attempts: 5
  │   initial_interval: PT15S
  │   max_interval: PT5M
  ▼ Retry 1: wait PT15S; dispatch again; 503
  ▼ Retry 2: wait PT30S; dispatch again; 503
  ▼ Retry 3: wait PT1M; dispatch again; 200 acknowledged
  ▼ Provider proceeds to realize; entity → OPERATIONAL after PT3M
  ▼ All retries audited with attempt_number and elapsed_time
```

If all 5 retries exhausted, `on_exhaustion: NOTIFY_AND_WAIT` with `PT2H`
deadline; consumer reviews and decides.

---

## 6. Brownfield ingestion — discovery to promotion

An existing VM in OpenStack not provisioned through DCM is brought under
DCM lifecycle management.

### 6.1 Setup

- Existing VM in OpenStack with `vm_id: vm-legacy-0001`
- DCM Discovery Service runs scheduled OpenStack discovery
- Ingestion Engine subscribes to discovery events

### 6.2 Sequence

```
Discovery Service runs scheduled OpenStack discovery
  ▼ Discovery finds vm-legacy-0001
  ▼ Match against existing Realized State: no match → brownfield candidate
  ▼ ingestion.candidate_identified event published
  ▼ Ingestion Engine creates ingestion record:
  │   ingestion_source: brownfield_discovery
  │   discovered_state_uuid: <uuid>
  │   tenant: __transitional__
  │   state: INGESTED
  ▼ Auto-assignment signal evaluation:
  │   Signal 1 (explicit_tenant_tag): no tag found
  │   Signal 2 (network_segment_mapping): VLAN-100 → maps to AppTeam Tenant
  │   Assignment: AppTeam Tenant; confidence: medium
  ▼ Tenant assigned; state → ENRICHING
  ▼ Information Provider enrichment:
  │   CMDB Information Provider queried; returns business unit "Payments",
  │   cost center "PAY-4421", product owner "Jane Smith"
  │   Confidence descriptor: authority_level: primary, corroboration: single_source
  ▼ Operator reviews; promotes via POST /api/v1/admin/ingest/{uuid}:promote
  ▼ state → PROMOTED
  ▼ Discovered State promoted to initial Realized State
  │   provenance.origin.source_type: brownfield_discovery
  ▼ Entity → OPERATIONAL; standard drift detection begins
```

From this point, future OpenStack discoveries compare against the Realized
State; any deviation fires `drift.detected`.

---

## 7. Cross-provider write-back

A consumer updates a VM's owner_business_unit field; DCM updates the CMDB
via write-back.

### 7.1 Setup

- VM entity owned by AppTeam Tenant
- CMDB Information Provider with `write_back: true`, supported_operations:
  [update], fields: [hostname, ip_address, owner_business_unit, lifecycle_state]
- Transformation policy: trigger CMDB write-back on `STATE_TRANSITION` or
  field update for `Compute.VirtualMachine`

### 7.2 Sequence

```
Consumer submits PATCH /api/v1/resources/{vm_uuid}/fields
  { "owner_business_unit": "Payments-Platform" }
  ▼ Standard nine-step assembly with new field value
  ▼ Transformation policy fires:
  │   trigger_write_back: provider: CMDB, operation: update,
  │   fields: [owner_business_unit]
  ▼ Placement: VM provider selected (state transition only; no new VM)
  ▼ Dispatcher updates VM at the VM provider
  ▼ Write-back executor runs:
  │   - Resolves CMDB write-back endpoint
  │   - Issues dcm_interaction credential scoped to CMDB + update operation
  │   - Sends payload: { entity_uuid, fields: { owner_business_unit: "Payments-Platform" } }
  │   - Records ENRICH audit record with source_type: information_provider_write_back
  ▼ CMDB updates; returns success
  ▼ Realized State updated with new field value
  ▼ Consumer receives confirmation
```

If write-back fails, the policy's retry configuration drives behavior;
failure does not roll back the entity update — write-back is a side effect,
not a precondition.
