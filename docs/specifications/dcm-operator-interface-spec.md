# DCM Operator Interface Specification

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Operator Interface Specification



> ## 📋 Draft — Promoted from Work in Progress
>
> All questions resolved. Level 0–4 conformance levels defined. Cluster-scoped resource ownership clarified. CAPI integration specified.
>
> **This section is explicitly a work in progress and is less mature than the core DCM data model and architecture documentation.**
>
> The Kubernetes operator integration layer — including the Operator Interface Specification, Operator SDK API, and Kubernetes compatibility mappings — represents design intent that has not yet been validated against implementation. Specific interface contracts, API signatures, SDK method names, and CRD structures **will change** as implementation work begins.
>
> **Do not build against these specifications yet.** They are published to share design direction and invite feedback, not as stable contracts.
>
> Known gaps and open items for this section:
> - Operator Interface Specification: reconciliation hook signatures are provisional
> - Operator SDK API: Go module structure and dependency model not yet finalized
> - Kubernetes Compatibility Mappings: some concept mappings remain under discussion
> - SDK code examples are illustrative only — not yet tested against a real implementation
>
> Feedback and contributions welcome via [GitHub Issues](https://github.com/dcm-project/issues).



**Version:** 0.1.0-draft  
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Specification  
**Maintainers:** Red Hat FlightPath Team  
**GitHub:** https://github.com/dcm-project  
**Last Updated:** 2026-03

---

## Abstract

This specification defines the interface by which Kubernetes operators integrate with the DCM (Data Center Management) control plane as first-class Service Providers. An operator that conforms to this specification becomes a DCM Service Provider, enabling its managed resources to participate in DCM's unified lifecycle management, multi-tenancy, policy governance, cost analysis, drift detection, and service catalog.

DCM is designed as a superset of Kubernetes — extending Kubernetes' declarative, controller-based model upward to provide unified management across multiple clusters, infrastructure types, and organizational boundaries. This specification is the technical contract that enables that extension without requiring operators to abandon their existing Kubernetes-native design.

Operators conforming to this specification function as Service Providers within a single DCM instance. In federated deployments (Hub-Spoke or Peer topology), the operator registers with the appropriate Regional or local DCM instance — federation routing is handled by DCM, not by the operator.

---

## 1. Introduction

> **OIS Versioning:** Providers declare the OIS version they implement in capability registration (`ois_version`). DCM maintains dispatch compatibility with all supported OIS versions. See [API Versioning Strategy](../../architecture/control-plane/api-versioning.md) Section 7.


### 1.1 Motivation

Kubernetes operators are the most mature pattern for managing complex, stateful resources declaratively on Kubernetes. However, operators operate within a single cluster and lack the cross-cluster lifecycle management, multi-tenancy, cost attribution, sovereignty governance, and policy enforcement that enterprise organizations require at scale.

DCM provides these capabilities at the management plane level — above individual clusters. By conforming to this specification, an operator's managed resources become:

- **Multi-tenant** — DCM Tenant ownership and isolation applied automatically
- **Cost-attributed** — resource costs tracked and attributed across the full lifecycle
- **Policy-governed** — organizational policies applied at request time via DCM's Policy Engine
- **Cross-cluster** — the same resource type managed across multiple clusters through DCM
- **Self-service** — automatically available in the DCM Service Catalog for consumer request
- **Sovereignty-compliant** — placement and operational constraints enforced by DCM's GateKeeper policies
- **Audit-complete** — full provenance chain from intent through realization

### 1.2 Scope

This specification defines:
- The HTTP API an operator must expose to participate in DCM
- The data format for all API payloads (DCM Unified Data Model)
- The registration, health, capacity, status, and lifecycle event contracts
- The field mapping specification for translating between DCM format and CRD format
- Conformance levels and what each level unlocks in DCM

This specification does not define:
- How operators implement their internal reconciliation logic
- Which specific Kubernetes distributions operators must support
- The internal architecture of the DCM control plane
- Provider-specific business logic or domain knowledge

### 1.3 Relationship to the DCM Service Provider Contract

This specification is a Kubernetes-specific instantiation of the DCM Service Provider Contract. All general Service Provider Contract requirements apply. This specification adds Kubernetes-specific requirements and guidance. Where this specification and the general Service Provider Contract conflict, this specification takes precedence for Kubernetes operator implementations.

### 1.4 Terminology

- **Operator** — a Kubernetes controller that manages custom resources via a Custom Resource Definition (CRD)
- **DCM Control Plane** — the DCM management system that routes requests and manages lifecycle
- **Adapter** — a component that sits between DCM and an operator, implementing this specification on the operator's behalf (used when the operator cannot be modified directly)
- **Native implementation** — an operator that implements this specification directly, without an adapter
- **CR** — Custom Resource — an instance of a CRD managed by the operator
- **CRD** — Custom Resource Definition — the Kubernetes schema definition for a CR
- **Reconciliation loop** — the operator's control loop that drives actual state toward desired state

---

## 2. Conformance Levels

This specification defines three conformance levels. Higher levels unlock additional DCM capabilities. An operator may implement any level — DCM accepts operators at all levels, with capabilities gated by the declared conformance level.

**Design principle:** Level 1 must be achievable in a single day of work for an existing operator. Level 3 is the target for operators that want full DCM integration. The SDK (see Section 9) handles all protocol concerns — operator developers only implement business logic.

### 2.1 Level 1 — Basic

**What it requires:**
- Operator registration with DCM on startup
- Health check endpoint (`GET /health`)
- Basic status reporting to DCM when resource state changes

**What it unlocks:**
- Operator resources appear in the DCM Service Catalog
- Basic lifecycle state tracking (PROVISIONING, OPERATIONAL, FAILED, DECOMMISSIONED)
- Health monitoring via DCM Observability
- Basic cost tracking (resource exists/does not exist)

**Estimated implementation effort:** 1 day using the DCM Operator SDK

### 2.2 Level 2 — Standard

Level 2 conformance is required for providers that support auto-scaling, auto-healing, or provider-side maintenance operations. Level 2 includes all Level 1 requirements plus the Provider Update Notification API (Section 7a).


**What it requires:** All Level 1 requirements, plus:
- Capacity reporting to DCM (scheduled registration)
- Full lifecycle event reporting (DEGRADED, MAINTENANCE, UNSANCTIONED_CHANGE, etc.)
- Complete realized state payloads in DCM Unified Data Model format
- Field mapping declaration (CRD fields mapped to DCM Resource Type fields)

**What it unlocks:** All Level 1 capabilities, plus:
- Intelligent placement — DCM can route requests based on real capacity data
- Drift detection — DCM compares discovered state against realized state
- Full cost attribution — granular resource cost tracking throughout lifecycle
- Cross-cluster management — DCM can route the same resource type to multiple clusters
- Dependency graph participation — operator resources participate in DCM entity relationships

**Estimated implementation effort:** 2-3 days using the DCM Operator SDK

### 2.3 Level 3 — Full

**What it requires:** All Level 2 requirements, plus:
- Sovereignty capability declaration
- Field-level provenance in realized state payloads
- Override control metadata support
- Discovery endpoint (`POST /discover`) — operator can discover existing resources for brownfield ingestion
- Decommission confirmation callback

**What it unlocks:** All Level 2 capabilities, plus:
- Sovereignty enforcement — DCM can enforce placement and operational constraints per regulatory requirements
- Full audit chain — complete provenance from intent through realization
- Brownfield ingestion — existing resources can be imported into DCM lifecycle management
- Override control enforcement — policy-set field locks honored in operator requests

**Estimated implementation effort:** 3-5 days using the DCM Operator SDK

---

## 3. Registration API

### 3.1 Overview

Operators register with DCM on startup. Registration informs DCM of the operator's endpoint, the resource types it manages, its capabilities, and its conformance level. Registration is idempotent — re-registering with the same name updates the existing registration rather than creating a duplicate.

### 3.2 Registration Endpoint

**DCM endpoint:** `POST /api/v1/providers`

**Timing:** Called by the operator (or adapter) during startup, after the HTTP server is ready. Retried with exponential backoff on failure. Registration failure does not block operator startup — the operator functions normally for Kubernetes consumers even if DCM registration fails.

### 3.3 Registration Payload

```yaml
# Registration request payload
provider_registration:
  name: <unique provider name — natural key for idempotent re-registration>
  display_name: <human-readable name>
  conformance_level: <1|2|3>
  endpoint: <base URL of the operator's DCM API — e.g., https://operator.namespace.svc:8080>
  version: <operator version — Major.Minor.Revision>

  service_types:
    - service_type: <DCM Resource Type name — e.g., Storage.Database>
      service_type_uuid: <UUID of the DCM Resource Type from the registry>
      crd_reference:
        group: <CRD API group — e.g., postgresql.cnpg.io>
        version: <CRD version — e.g., v1>
        kind: <CRD kind — e.g., Cluster>
      operations_supported: [CREATE, READ, UPDATE, DELETE, DISCOVER]
      # DISCOVER only required for Level 3
      field_mapping_ref: <URL or inline field mapping declaration — see Section 7>

  kubernetes:
    cluster_id: <stable identifier for this Kubernetes cluster>
    cluster_endpoint: <Kubernetes API server endpoint>
    namespace_strategy: <per_tenant|shared|per_resource>
    # per_tenant: one namespace per DCM Tenant
    # shared: all DCM resources in one namespace, isolated by labels
    # per_resource: one namespace per resource instance

  metadata:
    region: <geographic region>
    zone: <availability zone>
    cluster_type: <ocp|vanilla|eks|gke|aks|other>
    cluster_version: <Kubernetes version>

  # Level 2+ required
  capacity:
    update_mode: <scheduled|on_demand|both>
    update_frequency_seconds: <integer — for scheduled mode>

  # Level 3 required
  sovereignty_capabilities:
    data_residency_regions: [<list of regions where data stays>]
    operational_sovereignty: <true|false>
    hard_tenancy_supported: <true|false>
    air_gapped_capable: <true|false>
    compliance_frameworks: [<list — e.g., PCI-DSS, SOC2, FedRAMP>]
```

### 3.4 Registration Response

```yaml
# Success response
provider_registration_response:
  provider_uuid: <DCM-assigned UUID — stable across re-registrations>
  name: <confirmed name>
  status: <registered|updated>
  conformance_level_accepted: <1|2|3>
  capabilities_enabled:
    - service_catalog
    - health_monitoring
    - cost_tracking
    # Level 2+
    - placement
    - drift_detection
    - cross_cluster_management
    # Level 3
    - sovereignty_enforcement
    - brownfield_ingestion
    - full_audit_chain
```

---

## 4. Health Check API

### 4.1 Overview

DCM polls the operator's health endpoint every 10 seconds (configurable). A healthy operator is eligible to receive new resource requests. An unhealthy operator is excluded from placement decisions.

### 4.2 Health Endpoint

**Endpoint:** `GET /health`  
**Authentication:** Unauthenticated (or internally secured — operator choice)  
**Expected response:** HTTP 200 OK for healthy or warn status; any non-200 for unhealthy (fail)

The health response body is **normative**. DCM uses the `status` field to determine provider health and trigger alerts. Providers that return a non-conforming or absent body are treated as `warn` until three consecutive failures, after which they are treated as `fail`.

```http
GET /health HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/health+json

{
  "status": "pass",              // REQUIRED: "pass" | "warn" | "fail"
  "version": "<semver>",         // REQUIRED: provider software version
  "dcm_registration_status": "registered",  // REQUIRED: "registered" | "unregistered" | "error"
  "uptime_seconds": 86423,       // RECOMMENDED: seconds since last restart
  "checks": {                    // RECOMMENDED: per-subsystem health
    "provider_backend": {
      "status": "pass",
      "observed_at": "<ISO 8601>"
    },
    "service_provider_connectivity": {
      "status": "pass",
      "observed_at": "<ISO 8601>"
    }
  },
  "details": {}                  // OPTIONAL: operator-specific additional detail
}
```

**Status semantics:**

| Status | HTTP code | Meaning | DCM behavior |
|--------|-----------|---------|--------------|
| `pass` | 200 | Fully operational | No action |
| `warn` | 200 | Operational but degraded | Fires `provider.degraded` event; alert platform admin |
| `fail` | any non-200 | Not operational | Fires `provider.unhealthy` event; triggers recovery policy |

The health endpoint format follows [RFC 8615 / IANA health+json](https://www.iana.org/assignments/media-types/application/health+json).

**DCM polling behavior:**
- Polling interval: declared in provider capability registration (`health_check_interval`, default PT30S)
- Consecutive `fail` threshold before `provider.unhealthy` event: 3 (profile-governed)
- Recovery: first `pass` after `fail` fires `provider.healthy` event

### 4.3 State Machine

- **Ready** — HTTP 200 received. Operator eligible for new requests.
- **NotReady** — Non-200 or timeout received 3 consecutive times (configurable threshold). Operator excluded from placement. Existing resources not affected.
- **Recovery** — Single HTTP 200 transitions NotReady back to Ready immediately.

---

## 5. Capacity Reporting API

*Required for Level 2 conformance.*

### 5.1 Overview

DCM maintains an internal capacity rating per operator, per service type, per location. Operators report capacity on a configurable schedule. DCM uses capacity data for intelligent placement decisions.

### 5.2 Capacity Registration

**DCM endpoint:** `POST /api/v1/providers/{provider_uuid}/capacity`

```yaml
capacity_report:
  provider_id: <uuid>
  report_timestamp: <ISO 8601>
  next_report_at: <ISO 8601>
  capacity_by_service_type:
    - service_type_uuid: <uuid>
      available_units: <integer>
      reserved_units: <integer>
      committed_units: <integer>
      unit_definition: <what one unit means — e.g., "1 database cluster">
      kubernetes_resources:
        available_cpu: <millicores>
        available_memory: <bytes>
        available_storage: <bytes>
        node_count: <integer>
```

### 5.3 Capacity Denial

When DCM dispatches a request the operator cannot fulfill, the operator **must** reject it with `INSUFFICIENT_RESOURCES`. DCM receives the denial and retries with an alternative provider.

```yaml
# Denial response to a resource creation request
denial_response:
  request_id: <uuid>
  denial_reason: INSUFFICIENT_RESOURCES
  denial_timestamp: <ISO 8601>
  service_type_uuid: <uuid>
  estimated_available_at: <ISO 8601 — optional>
  details: <human-readable explanation>
```

DCM updates its internal capacity rating for this operator immediately upon receiving a denial.

---

## 6. Resource Lifecycle API

### 6.1 Overview

DCM dispatches resource lifecycle operations to the operator via standard REST endpoints. The operator translates these into Kubernetes CR operations (Naturalization) and reports results back to DCM in DCM Unified Data Model format (Denaturalization).

### 6.2 Standard Endpoints

| Method | Endpoint | Description | Required Level |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/{service_type}` | Create a new resource | Level 1 |
| `GET` | `/api/v1/{service_type}` | List all resources | Level 1 |
| `GET` | `/api/v1/{service_type}/{resource_id}` | Get a specific resource | Level 1 |
| `PUT` | `/api/v1/{service_type}/{resource_id}` | Update a resource | Level 2 |
| `DELETE` | `/api/v1/{service_type}/{resource_id}` | Delete a resource | Level 1 |
| `POST` | `/api/v1/{service_type}/discover` | Discover existing resources | Level 3 |

### 6.3 Create Request

DCM sends the Requested State payload to the operator. The operator naturalizes it to a Kubernetes CR and submits it. The operator responds immediately with a PROVISIONING status — not waiting for reconciliation to complete.

```yaml
# Create request from DCM — Requested State payload in DCM format
create_request:
  request_id: <uuid — DCM request UUID for correlation>
  tenant_uuid: <uuid — DCM Tenant that owns this resource>
  # Both resource_type_uuid and resource_type_name are always present — DCM resolves from consumer input
  resource_type_uuid: <uuid>
  resource_type_name: Storage.Database
  spec:
    <DCM Unified Data Model fields for this resource type>
  relationships:
    <entity relationships declared at request time>
  metadata:
    override_control:
      <any field-level override constraints — Level 3>
```

```yaml
# Create response — immediate acknowledgment
create_response:
  resource_id: <operator-assigned ID — stable, used for subsequent operations>
  dcm_request_id: <echoed from request>
  lifecycle_state: PROVISIONING
  kubernetes_reference:
    namespace: <namespace where CR was created>
    name: <CR name>
    uid: <Kubernetes UID>
```

### 6.4 Realized State Payload

When the operator's reconciliation loop completes provisioning, it pushes the realized state to DCM. This is the critical Denaturalization step — translating Kubernetes-native status into DCM Unified Data Model format.

**DCM endpoint:** `PUT /api/v1/instances/{resource_id}/status`

```yaml
# Realized state payload — DCM Unified Data Model format
realized_state:
  resource_id: <operator resource ID>
  dcm_entity_uuid: <DCM entity UUID — provided by DCM in create request>
  lifecycle_state: <OPERATIONAL|FAILED|DEGRADED|DECOMMISSIONED>
  realized_timestamp: <ISO 8601>

  spec:
    <all fields of the realized resource in DCM format>
    <includes both what was requested and what the operator added>

  # Level 3 — provenance for each field
  field_provenance:
    <field_name>:
      source_type: provider
      source_uuid: <operator provider UUID>
      timestamp: <ISO 8601>

  kubernetes_reference:
    namespace: <namespace>
    name: <CR name>
    uid: <Kubernetes UID>
    resource_version: <Kubernetes resource version>

  relationships:
    <any relationships created during realization — e.g., storage entities>
```

### 6.5 Delete and Decommission

When DCM requests deletion, the operator deletes the CR and confirms decommission via the realized state endpoint with `lifecycle_state: DECOMMISSIONED`.

For **Level 3**, the operator must wait for DCM confirmation before deleting — this allows DCM to apply lifecycle policies (retain, detach) before the operator acts.

```yaml
# Decommission confirmation callback (Level 3)
# DCM calls this before the operator deletes
decommission_confirmation:
  resource_id: <uuid>
  lifecycle_policies_applied:
    - entity_uuid: <uuid of related entity>
      policy_applied: retain
      # storage was retained, not deleted with the parent
    - entity_uuid: <uuid of related entity>
      policy_applied: destroy
  proceed_with_deletion: <true|false>
```

---


---

## 7a. Provider Update Notification API

This section defines the Provider Update Notification endpoint — the formal mechanism by which Service Providers report authorized state changes to DCM. This is a **Level 2** conformance requirement for providers that support auto-scaling, auto-healing, or provider-side maintenance operations.

### 7a.1 Overview

The Provider Update Notification API enables providers to report authorized state changes so DCM can update its Realized State with a traceable Requested State record. This is distinct from drift — a provider submitting an update notification is asserting that the change was authorized (by a pre-existing policy or operational agreement). DCM evaluates the assertion and decides whether to accept or reject it.

**Key principle:** Providers never write directly to DCM's Realized State. They submit a notification; DCM processes it through its governance pipeline; DCM writes the Realized State if approved.

### 7a.2 Conformance Requirements

| Conformance Level | Requirement |
|------------------|-------------|
| Level 1 — Basic | Not required. Providers at Level 1 report all state changes as lifecycle events; DCM handles them as drift. |
| Level 2 — Standard | Required for providers that implement auto-scaling, auto-healing, or provider-side maintenance. |
| Level 3 — Full | Required. All authorized provider-side state changes must use this API. |

### 7a.3 Endpoint

```
POST /api/v1/provider/entities/{entity_uuid}/update-notification
Host: {dcm-instance}
Authorization: mTLS (provider certificate)
Content-Type: application/json
```

**Note:** This endpoint is on the DCM API Gateway, not on the provider. Providers call DCM; DCM does not poll providers for updates.

### 7a.4 Request Payload

```json
{
  "provider_uuid": "<uuid>",
  "notification_uuid": "<uuid>",
  "notification_type": "authorized_change | maintenance_change | auto_scale | auto_heal",
  "changed_fields": {
    "<field_name>": {
      "previous_value": "<value>",
      "new_value": "<value>",
      "change_reason": "<human-readable explanation>",
      "authorizing_policy_ref": "<uuid | null>"
    }
  },
  "effective_at": "<ISO 8601>",
  "provider_evidence_ref": "<provider-side reference>"
}
```

**`notification_uuid`** is an idempotency key. If DCM receives the same `notification_uuid` twice, it acknowledges the second request without reprocessing.

**`authorizing_policy_ref`** is the UUID of the DCM policy that pre-authorized this type of change. If null, DCM will evaluate whether a policy covers this change. If no policy covers it, the notification is rejected.

### 7a.5 Response Codes

| Response | Meaning |
|----------|---------|
| `202 Accepted` | Notification accepted. DCM is processing. Use `notification_status_url` to poll. |
| `200 OK` (with `status: approved`) | Notification accepted and Realized State updated. |
| `200 OK` (with `status: pending_approval`) | Notification queued pending consumer approval. Entity in PENDING_REVIEW. |
| `200 OK` (with `status: rejected`) | Notification rejected. Realized State not updated. Discrepancy is now drift. |
| `409 Conflict` | A notification for this entity is already being processed. Retry after the `retry_after` interval. |
| `422 Unprocessable` | Notification payload malformed or entity UUID not found in this provider's scope. |

```json
{
  "notification_uuid": "<uuid>",
  "status": "approved | pending_approval | rejected",
  "realized_state_uuid": "<uuid | null>",
  "rejection_reason": "<string | null>",
  "retry_after": "<ISO 8601 duration | null>",
  "notification_status_url": "/api/v1/provider/notifications/{notification_uuid}"
}
```

### 7a.6 Notification Status Polling

```
GET /api/v1/provider/notifications/{notification_uuid}

Response:
{
  "notification_uuid": "<uuid>",
  "status": "processing | approved | pending_approval | rejected",
  "entity_uuid": "<uuid>",
  "realized_state_uuid": "<uuid | null>",
  "consumer_approval_required": true | false,
  "consumer_notified_at": "<ISO 8601 | null>",
  "resolved_at": "<ISO 8601 | null>"
}
```

### 7a.7 Idempotency

Provider Update Notifications are idempotent by `notification_uuid`. If DCM crashes between receiving a notification and writing the Realized State, the provider can safely resend the same notification. DCM will not create duplicate Realized State records.

### 7a.8 Pre-Authorization Declarations

Providers may declare categories of updates they routinely make — enabling organizations to pre-authorize them in policy rather than reviewing each one:

```json
{
  "provider_uuid": "<uuid>",
  "update_capabilities": [
    {
      "notification_type": "auto_scale",
      "affected_fields": ["cpu_count", "memory_gb"],
      "max_change_magnitude": "2x",
      "typical_trigger": "Resource utilization threshold"
    },
    {
      "notification_type": "auto_heal",
      "affected_fields": ["storage_device_id", "network_interface_id"],
      "max_change_magnitude": "replacement",
      "typical_trigger": "Hardware failure"
    }
  ]
}
```

This declaration is part of provider registration (Section 3.3) and is surfaced in the Service Catalog to help consumers understand what provider-side changes they can expect.



---

## 7b. Cancellation API

This section defines the cancellation endpoint that Service Providers implement for Level 2+ conformance. Providers that declare `supports_cancellation: true` in their registration must implement this endpoint.

### 7b.1 Cancellation Endpoint

```
POST /cancel (on the provider, called by DCM)
Authorization: DCM mTLS certificate

Body:
{
  "cancellation_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "requested_state_uuid": "<uuid>",
  "reason": "consumer_requested | timeout | policy_triggered",
  "requested_at": "<ISO 8601>",
  "best_effort": true
}
```

### 7b.2 Response

| Code | Meaning |
|------|---------|
| `200 OK` (status: cancelled) | Cancellation clean; no resources provisioned |
| `200 OK` (status: partial_rollback) | Cancellation attempted; some resources may remain |
| `200 OK` (status: too_late) | Provider completed before cancellation arrived; late response forthcoming |
| `409 Conflict` | Already cancelled or already completed |

```json
{
  "cancellation_uuid": "<uuid>",
  "status": "cancelled | partial_rollback | too_late",
  "resources_remaining": [],
  "late_response_expected": false,
  "notes": "<string>"
}
```

### 7b.3 Late Response After Cancellation

If the provider returns `status: too_late`, it must still send the completed realization response via the standard realized-state callback. DCM's Late Response Pipeline handles this — the provider does not need to do anything different. The `LATE_RESPONSE_RECEIVED` Recovery Policy fires on the DCM side.

### 7b.4 Capability Declaration

```json
{
  "cancellation_capabilities": {
    "supports_cancellation": true,
    "cancellation_supported_during": ["DISPATCHED", "PROVISIONING"],
    "partial_rollback_possible": true,
    "cancellation_response_time_seconds": 30
  }
}
```


### 6.4 Interim Status Reporting

For long-running operations (provisioning complex resources, composite service constituents), providers may send interim progress updates to DCM without waiting for terminal status. This gives DCM — and therefore consumers — live visibility into multi-step operations.

**DCM endpoint for interim status:**

```
POST /api/v1/provider/entities/{entity_uuid}/status

Authorization: Bearer <provider-interaction-credential>
Content-Type: application/json

{
  "request_id": "<dcm-request-uuid>",
  "lifecycle_state": "PROVISIONING",   // current state — not yet terminal
  "progress": {
    "step_current": 3,
    "step_total": 7,
    "step_label": "Configuring network interfaces",
    "step_started_at": "<ISO 8601>",
    "estimated_completion": "<ISO 8601>"
  },
  "constituent_status": [              // for compound/composite service definition operations
    { "ref": "vm",      "status": "REALIZED",     "completed_at": "<ISO 8601>" },
    { "ref": "ip",      "status": "REALIZED",     "completed_at": "<ISO 8601>" },
    { "ref": "dns",     "status": "PROVISIONING", "started_at": "<ISO 8601>" },
    { "ref": "storage", "status": "PENDING",      "started_at": null }
  ],
  "notes": "<optional human-readable detail>"
}

Response 202 Accepted
```

DCM uses interim status to:
1. Update `current_step` and progress fields in the request status response
2. Publish `request.progress_updated` event (info urgency) to the Message Bus
3. Deliver live status updates to consumers via SSE stream (see Consumer API Section 4.3)

**Frequency:** Providers should not send interim status more frequently than once per 10 seconds. DCM rate-limits interim status calls per entity_uuid.

**Terminal status** is still reported via the existing create/update response callback — interim status supplements, not replaces it.

## 7. Field Mapping Specification

*Required for Level 2 conformance.*

### 7.1 Overview

The field mapping declaration tells DCM how to translate between DCM Unified Data Model fields and the operator's CRD fields. This mapping enables DCM to:
- Generate CRs from DCM Requested State payloads (Naturalization)
- Extract DCM Realized State from CR status (Denaturalization)
- Understand which DCM fields correspond to which CRD fields for drift detection

### 7.2 Field Mapping Declaration Format

```yaml
field_mapping:
  service_type: Storage.Database
  service_type_uuid: <uuid>
  crd_reference:
    group: postgresql.cnpg.io
    version: v1
    kind: Cluster

  # DCM Requested State → Kubernetes CR (Naturalization)
  dcm_to_cr:
    - dcm_path: resources.cpu
      cr_path: spec.instances[0].resources.requests.cpu
      transform: <none|integer_to_string|string_to_integer|custom>
      required: true

    - dcm_path: resources.memory
      cr_path: spec.instances[0].resources.requests.memory
      transform: gigabytes_to_kubernetes_memory
      required: true

    - dcm_path: engine
      cr_path: spec.imageName
      transform: engine_version_to_image
      # engine: postgresql, version: 15 → imageName: ghcr.io/cloudnative-pg/postgresql:15
      required: true

    - dcm_path: metadata.name
      cr_path: metadata.name
      required: true

    - dcm_path: tenant_uuid
      cr_path: metadata.labels.dcm-tenant-id
      required: true

    - dcm_path: dcm_entity_uuid
      cr_path: metadata.labels.dcm-entity-id
      required: true
      # All DCM-managed CRs must be labeled with their DCM entity UUID
      # This enables discovery and drift detection

  # Kubernetes CR status → DCM Realized State (Denaturalization)
  cr_status_to_dcm:
    - cr_path: status.phase
      dcm_path: lifecycle_state
      transform: cr_phase_to_dcm_state
      # Mapping defined in condition_mappings below

    - cr_path: status.readyInstances
      dcm_path: realized_data.ready_instances
      transform: none

    - cr_path: status.instancesStatus[0].ip
      dcm_path: realized_data.connection.host
      transform: none

    - cr_path: status.certificates.serverCASecret
      dcm_path: realized_data.tls.ca_secret_ref
      transform: none

  # Kubernetes conditions → DCM lifecycle states
  condition_mappings:
    - kubernetes_condition: "Ready=True"
      dcm_lifecycle_state: OPERATIONAL

    - kubernetes_condition: "Ready=False,Progressing=True"
      dcm_lifecycle_state: PROVISIONING

    - kubernetes_condition: "Ready=False,Progressing=False"
      dcm_lifecycle_state: FAILED

    - kubernetes_condition: "Degraded=True"
      dcm_lifecycle_state: DEGRADED

  # Kubernetes events → DCM lifecycle events
  lifecycle_event_mappings:
    - kubernetes_event: condition_change
      condition: "Ready=False"
      dcm_event: ENTITY_HEALTH_CHANGE
      severity: WARNING

    - kubernetes_event: condition_change
      condition: "Degraded=True"
      dcm_event: DEGRADATION
      severity: CRITICAL

    - kubernetes_event: spec_change_without_dcm_request
      dcm_event: UNSANCTIONED_CHANGE
      severity: WARNING
      # Detected when CR spec changes without a corresponding DCM request ID
      # Indicates drift — someone modified the CR directly in Kubernetes

  # Namespace strategy implementation
  namespace_strategy:
    type: per_tenant
    namespace_name_pattern: "dcm-{tenant_uuid_short}"
    # {tenant_uuid_short} = first 8 chars of tenant UUID
    labels_required:
      dcm-managed: "true"
      dcm-tenant-id: "{tenant_uuid}"
      dcm-entity-id: "{entity_uuid}"
```

### 7.3 Mandatory CR Labels

All CRs created by a DCM-conformant operator must carry these labels. These labels enable DCM's discovery and drift detection capabilities:

| Label | Value | Purpose |
|-------|-------|---------|
| `dcm-managed` | `"true"` | Identifies this CR as DCM-managed |
| `dcm-tenant-id` | DCM Tenant UUID | Tenant ownership |
| `dcm-entity-id` | DCM Entity UUID | Links CR to DCM entity record |
| `dcm-provider-id` | DCM Provider UUID | Which provider created this |
| `dcm-request-id` | DCM Request UUID | Which request created this |

Any CR change that does not have a corresponding DCM request ID in its update metadata is flagged as an UNSANCTIONED_CHANGE and reported to DCM.

---

## 8. Lifecycle Event API

*Required for Level 2 conformance.*

### 8.1 Overview

Operators must notify DCM of any event that affects the operational status of a managed resource. DCM acts as the Tenant advocate — it receives events, evaluates them through the Policy Engine, and determines the appropriate response.

### 8.2 Event Endpoint

**DCM endpoint:** `POST /api/v1/instances/{resource_id}/events`

### 8.3 Standard Event Types

| Event Type | Trigger | Severity | Required Level |
|------------|---------|----------|---------------|
| `ENTITY_HEALTH_CHANGE` | CR condition changes | INFO/WARNING | Level 2 |
| `DEGRADATION` | Resource is degraded but operational | WARNING | Level 2 |
| `MAINTENANCE_SCHEDULED` | Planned maintenance window | INFO | Level 2 |
| `MAINTENANCE_STARTED` | Maintenance has begun | INFO | Level 2 |
| `MAINTENANCE_COMPLETED` | Maintenance completed | INFO | Level 2 |
| `UNSANCTIONED_CHANGE` | CR modified without DCM request | WARNING | Level 2 |
| `CAPACITY_CHANGE` | Available capacity changed significantly | INFO | Level 2 |
| `DECOMMISSION_NOTICE` | Operator is shutting down | CRITICAL | Level 2 |
| `PROVIDER_DEGRADATION` | Operator itself is degraded | CRITICAL | Level 2 |

```yaml
# Event payload
lifecycle_event:
  event_uuid: <uuid>
  event_type: UNSANCTIONED_CHANGE
  provider_id: <uuid>
  resource_id: <operator resource ID>
  dcm_entity_uuid: <DCM entity UUID>
  event_timestamp: <ISO 8601>
  severity: WARNING
  requires_immediate_action: true

  details:
    changed_fields:
      - field_path: spec.instances[0].resources.requests.cpu
        previous_value: "2000m"
        current_value: "4000m"
        changed_by: <kubernetes user or service account>
        changed_at: <ISO 8601>

  kubernetes_reference:
    namespace: <namespace>
    name: <CR name>
    resource_version: <version at time of event>
```

---

## 9. DCM Operator SDK

### 9.1 Overview

The DCM Operator SDK is an open source Go library that handles all DCM protocol concerns for operator developers. Using the SDK, an operator developer only needs to:

1. Import the SDK
2. Configure field mappings (declarative YAML)
3. Add SDK hooks at key points in the reconciliation loop

The SDK handles registration, health check endpoint exposure, capacity reporting, status translation, lifecycle event emission, provenance generation, and label management.

### 9.2 SDK Initialization

```go
import dcmsdk "github.com/dcm-project/operator-sdk"

func main() {
    // Load field mapping configuration
    mappings, err := dcmsdk.LoadFieldMappings("dcm-mappings.yaml")

    // Initialize DCM SDK
    dcm, err := dcmsdk.New(dcmsdk.Config{
        ProviderName:      "cloudnativepg-provider",
        DisplayName:       "CloudNativePG Service Provider",
        ConformanceLevel:  dcmsdk.Level2,
        DCMEndpoint:       os.Getenv("DCM_ENDPOINT"),
        OperatorEndpoint:  os.Getenv("OPERATOR_ENDPOINT"),
        FieldMappings:     mappings,
        CapacityReporter:  &PostgresCapacityReporter{},
    })

    // Start HTTP server with DCM endpoints automatically registered
    dcm.StartServer(":8080")

    // Register with DCM on startup
    dcm.Register(context.Background())

    // Start operator manager
    mgr.Start(ctrl.SetupSignalHandler())
}
```

### 9.3 Reconciliation Loop Integration

```go
func (r *ClusterReconciler) Reconcile(
    ctx context.Context,
    req ctrl.Request,
) (ctrl.Result, error) {

    cluster := &cnpgv1.Cluster{}
    if err := r.Get(ctx, req.NamespacedName, cluster); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Check if this CR is DCM-managed
    if !r.DCM.IsManagedResource(cluster) {
        return ctrl.Result{}, nil
        // Not a DCM resource — normal operator behavior
    }

    // Detect unsanctioned changes
    if r.DCM.IsUnsanctionedChange(cluster) {
        r.DCM.ReportEvent(ctx, cluster, dcmsdk.UnsanctionedChange{
            ChangedFields: r.DCM.DetectChangedFields(cluster),
        })
    }

    // ... existing reconciliation logic ...

    // Report current state to DCM
    realizedState, err := r.DCM.TranslateStatus(cluster)
    if err != nil {
        return ctrl.Result{}, err
    }
    r.DCM.ReportStatus(ctx, cluster, realizedState)

    return ctrl.Result{}, nil
}
```

### 9.4 SDK Responsibilities

The SDK automatically handles:
- Self-registration on startup with retry and exponential backoff
- Health check HTTP endpoint (`GET /health`)
- Capacity reporting on configurable schedule
- CR label injection on creation (`dcm-managed`, `dcm-tenant-id`, etc.)
- Unsanctioned change detection (spec change without DCM request ID)
- Status translation using field mapping configuration
- Lifecycle event formatting and delivery to DCM
- Provenance metadata generation for realized state payloads (Level 3)

---

## 10. Kubernetes-to-DCM Concept Mappings

Understanding how Kubernetes concepts map to DCM concepts is essential for implementing this specification correctly.

| Kubernetes Concept | DCM Concept | Notes |
|-------------------|-------------|-------|
| Custom Resource Definition (CRD) | Resource Type Specification | CRD schema maps to DCM Resource Type fields |
| Custom Resource (CR) | Requested State → Realized State | CR is the naturalized form of the DCM payload |
| Operator reconciliation loop | Realization + Drift Detection | Reconciliation IS the realization process |
| CR status subresource | Realized State payload | Status must be denaturalized to DCM format |
| Kubernetes Namespace | DCM Tenant boundary | One namespace per Tenant (per_tenant strategy) |
| ownerReference | Entity Relationship | ownerReferences map to `contains`/`contained_by` relationships |
| Labels/Annotations | DCM Entity metadata | DCM-specific labels declared as mandatory |
| Finalizers | Lifecycle policy enforcement | Finalizers implement `retain` lifecycle policies |
| Kubernetes conditions | DCM lifecycle states | Mapped via condition_mappings declaration |
| Watch events | DCM lifecycle events | Kubernetes watch → DCM event translation |
| Kubernetes RBAC | DCM IDM/IAM + Policy Engine | Kubernetes RBAC is the runtime enforcement; DCM Policy Engine governs the request |
| Kubernetes cluster | DCM Resource Type: Platform.KubernetesCluster | The cluster itself is a DCM-managed resource |

---

## 11. Conformance Testing

### 11.1 Overview

The DCM project provides a conformance test suite that validates an operator's implementation against this specification. Operators that pass the conformance test suite at their declared level can claim DCM conformance.

### 11.2 Test Suite Structure

```
dcm-operator-conformance/
├── level1/
│   ├── registration_test.go
│   ├── health_check_test.go
│   └── basic_status_test.go
├── level2/
│   ├── capacity_test.go
│   ├── lifecycle_events_test.go
│   ├── realized_state_test.go
│   └── field_mapping_test.go
└── level3/
    ├── sovereignty_test.go
    ├── provenance_test.go
    ├── discovery_test.go
    └── decommission_confirmation_test.go
```

### 11.3 Running the Conformance Tests

```bash
# Run Level 1 conformance tests against a running operator
dcm-conformance test \
  --level 1 \
  --operator-endpoint https://my-operator:8080 \
  --dcm-endpoint https://dcm-control-plane:8080 \
  --service-type Storage.Database

# Run all levels
dcm-conformance test --level 3 --operator-endpoint ...
```

### 11.4 Conformance Certification

Operators that pass the conformance test suite may:
- Use the "DCM Compatible — Level N" badge in their documentation
- Be listed in the DCM Operator Registry
- Receive inclusion in the DCM default Service Catalog for participating organizations

---

## 12. Security Considerations

### 12.1 Authentication

DCM authenticates outbound requests to operators using the trust model established during registration. Operators must validate that incoming requests originate from the DCM control plane. The specific authentication mechanism is declared in the provider registration:

```yaml
trust_declaration:
  auth_method: <mtls|oauth2|api_key|hmac>
  auth_config: <method-specific configuration>
```

### 12.2 Namespace Isolation

When using the `per_tenant` namespace strategy, operators must enforce that resources in one namespace cannot access resources in another namespace. This is the physical enforcement of DCM's hard tenancy model at the Kubernetes level.

### 12.3 Unsanctioned Change Detection

Operators must monitor for changes to DCM-managed CRs that did not originate from a DCM request. Any such change is an UNSANCTIONED_CHANGE event and must be reported to DCM immediately. DCM's Policy Engine determines the appropriate response (REVERT, UPDATE_DEFINITION, ALERT, etc.).

---

## 13. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | Should the specification be submitted to CNCF as a sandbox project or proposed as a Kubernetes SIG? | Community adoption strategy | ✅ Resolved |
| 2 | Should conformance certification be self-certified (test suite passes) or require DCM project review? | Community trust | ✅ Resolved |
| 3 | How should the specification handle operators that manage cluster-scoped (non-namespaced) resources? | Namespace strategy | ✅ Resolved — Two models: (A) Cluster-as-a-Service: Tenant owns the entire cluster entity including all cluster-scoped resources within it; (B) Shared cluster: cluster-scoped governance resources belong to __platform__ Tenant. Cluster-as-a-Service is the primary model. |
| 4 | Should the SDK support non-Go operator frameworks (Java Operator SDK, Python kopf)? | Ecosystem breadth | ✅ Resolved |
| 5 | How does the specification interact with Kubernetes Cluster API — can CAPI clusters be DCM-managed resources? | Scope | ✅ Resolved |
| 6 | Should there be a Level 0 — a pure label-based passive mode requiring no operator changes? | Adoption friction | ✅ Resolved |

---

## Appendix A — Example Implementation Checklist

### Level 1 Checklist
- [ ] Operator registers with DCM on startup via `POST /api/v1/providers`
- [ ] Registration retried with exponential backoff on failure
- [ ] `GET /health` endpoint returns HTTP 200 when healthy
- [ ] `GET /health` returns non-200 when operator cannot fulfill requests
- [ ] Status reported to DCM when resource transitions to OPERATIONAL, FAILED, or DECOMMISSIONED
- [ ] All DCM-managed CRs labeled with mandatory DCM labels
- [ ] Create response returns PROVISIONING state immediately

### Level 2 Checklist
- [ ] All Level 1 items complete
- [ ] Capacity reported to DCM on configurable schedule
- [ ] Capacity denial returns `INSUFFICIENT_RESOURCES` with proper payload
- [ ] Full realized state payload in DCM Unified Data Model format
- [ ] Field mapping declaration complete and validated
- [ ] All standard lifecycle event types implemented
- [ ] Unsanctioned change detection active
- [ ] CR condition changes translated to DCM lifecycle events

### Level 3 Checklist
- [ ] All Level 2 items complete
- [ ] Sovereignty capabilities declared in registration
- [ ] Field-level provenance included in realized state payloads
- [ ] `POST /discover` endpoint implemented
- [ ] Decommission confirmation callback handled
- [ ] Override control metadata honored in CR creation

---

## Appendix B — Relationship to Other Specifications

- **DCM Data Model** — defines the Unified Data Model format used in all API payloads
- **DCM Service Provider Contract** — the general provider contract this specification extends
- **DCM Resource Type Registry** — where DCM Resource Types are registered; operators must reference registry UUIDs
- **AEP (API Enhancement Proposals)** — the DCM API follows AEP standards for REST API design
- **OpenAPI 3.1.0** — all API schemas are defined in OpenAPI 3.1.0

---

*This specification is maintained by the DCM Project. For questions, contributions, or conformance certification see [GitHub](https://github.com/dcm-project).*


## Resolution Notes

**Q1:** Submit the Operator Interface Specification as a CNCF specification project (not a Sandbox project requiring a working implementation). SIG App Delivery and SIG Cluster Lifecycle engagement happens before submission. See cncf-strategy.md for the full submission strategy.

**Q2:** Self-certified via automated test suite is the conformance gate — this is the low-friction path that enables broad adoption. An optional 'DCM Verified' badge is available via DCM project review for organizations wanting a higher-trust production claim. This mirrors Kubernetes conformance: automated test suite gates access; CNCF certification provides the badge.

**Q3:** Two distinct models apply, and it is important to not conflate them:

**Model A — Cluster as a catalog item (example Service Provider implementation):** A Kubernetes cluster can be offered as a catalog item that any authorized Tenant requests and owns — this is a natural use of DCM's Service Provider model, not a special architectural feature. From DCM's perspective, `Platform.KubernetesCluster` is simply a resource type whose Service Provider happens to provision Kubernetes clusters (e.g., via CAPI). The Tenant owns the resulting cluster entity, including all cluster-scoped resources within it, because the cluster is the resource boundary. This is an example of how DCM's architecture enables complex resources as services — DCM has no special knowledge of Kubernetes; it treats the cluster as any other resource entity.

**Model B — Shared cluster infrastructure (the exception):** When multiple Tenants share a single cluster (the multi-tenant cluster model), cluster-scoped resources that govern the shared infrastructure itself (admission webhook configurations, cluster-level network policies, CRD registrations) cannot be owned by any single Tenant — they belong to the `__platform__` system Tenant. These are resources that, if modified by a Tenant, would affect all other Tenants on the cluster. The distinction: resources *inside* a Tenant-owned cluster are always Tenant-owned; resources that *govern shared cluster infrastructure* belong to `__platform__`.

**The rule:** Cluster-scoped resources are owned by the Tenant that owns the cluster. If no single Tenant owns the cluster (shared infrastructure), cluster-scoped governance resources belong to `__platform__`. Operators managing cluster-scoped resources implement the standard base contract. The catalog item scope (`scope: cluster` vs `scope: namespaced`) determines which ownership model applies and what role is required to request it.

**Q4:** The Operator Interface Specification is a REST/HTTP API specification and is language-agnostic by definition. The Go SDK is the reference implementation. Operators in any language implement the specification directly via HTTP — no language-specific adapter is required. Community SDKs for Java and Python are encouraged as community projects under the DCM umbrella; the DCM project does not maintain them in v1.

**Q5:** CAPI clusters are `Platform.KubernetesCluster` resources in DCM. The CAPI operator registers as a Service Provider for this resource type. Once provisioned, a CAPI cluster can optionally register with DCM as a nested DCM deployment or as a Service Provider for workload resources (the composite service definition pattern). Sovereignty constraints are enforced at the CAPI provider selection level.

**Q6:** Level 0 exists as a label-based passive discovery mode. Organizations apply DCM labels to existing operator-managed resources. DCM discovers and tracks these resources (they appear in inventory, drift detection runs against them) but DCM does not dispatch to or control them. No operator code changes are required for Level 0. This is the brownfield ingestion model applied to operators — the lowest possible adoption friction.

