# DCM Data Model — ITSM Integration

**Document Status:** 🔄 In Progress
**Document Type:** Architecture Reference — ITSM integration Type and ITSM Policy Type
**Related Documents:** [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md) | [Notification Model](../runtime-features/notifications.md) | [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md) | [Authority Tier Model](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) | [Consumer API Specification](../../docs/specifications/consumer-api-spec.md)

> **Design principle:** DCM is built to *replace* the infrastructure ticket as the primary provisioning mechanism. ITSM integration is additive — it enriches DCM entities with ITSM metadata, enables ITSM-initiated requests, and provides bidirectional lifecycle traceability for organizations that need it for compliance. **DCM never requires an ITSM system to function.**
>
> Two new additions to the DCM architecture:
> 1. **ITSM integration** — a new Provider type (12th) that speaks ITSM system APIs bidirectionally
> 2. **ITSM Policy** — a new Policy output type (8th) that triggers ITSM actions as a side-effect of DCM pipeline events

---

## 1. ITSM Integration

### 1.1 What ITSM Integration Is

ITSM integration connects DCM to an external IT Service Management system. It handles:

- **Outbound**: DCM lifecycle events → ITSM records (create change requests, update CMDB CIs, close incidents, link tickets to entities)
- **Inbound**: ITSM approvals and decisions → DCM (change approval recorded via approval vote API, request initiation from ITSM workflow)
- **Sync**: ITSM record references stored on DCM entities as business data (bidirectional link)

ITSM integration is **not** a separate provider type (it doesn't realize resources), **not** a notification service (though it may create notification-like records), and **not** a External Policy Evaluator (though ITSM approval status may inform DCM policies). It is its own type because it has a bidirectional contract, manages external record lifecycle, and requires specific capability declarations around ITSM system connectivity.

### 1.2 Data Flow

```
DCM lifecycle event fires (e.g. request.dispatched)
  │
  ▼ ITSM Policy evaluates (see Section 3)
  │   Determines: should an ITSM action fire? Which action?
  │
  ▼ ITSM integration receives action request
  │   Translates to target system's API format
  │   Calls ITSM system (ServiceNow, Jira, etc.)
  │
  ▼ ITSM system creates/updates record
  │   Returns record ID (CHG0012345, INC-4821, etc.)
  │
  ▼ ITSM integration stores reference on DCM entity
  │   entity.business_data.itsm_references[] updated
  │
  ▼ ITSM integration reports back to DCM
      itsm_reference_created event published
      External record ID in audit record

─────────────────────────────────────────────

ITSM system approves a change record
  │
  ▼ ITSM system calls DCM API (via webhook or polling)
  │   POST /api/v1/admin/approvals/{uuid}:vote
  │   { decision: "approve", recorded_via: "servicenow",
  │     external_reference: "CHG0012345" }
  │
  ▼ DCM records approval vote
  │   approval.decision_recorded event
  │
  ▼ Pipeline resumes if quorum/tier satisfied
```

### 1.3 Capability Declaration

```yaml
itsm_provider_capabilities:
  itsm_system: servicenow | jira_service_management | bmc_remedy | bmc_helix |
               freshservice | zendesk | pagerduty | opsgenie | manageengine |
               cherwell | topdesk | generic_rest
  
  # What this provider can do
  supported_actions:
    - create_change_request      # create a change record for DCM provisioning events
    - update_change_request      # update change record on state transitions
    - close_change_request       # close change record on realization/failure
    - create_incident            # create incident for failures, drift, security events
    - update_incident            # update incident on resolution
    - close_incident             # close incident on recovery
    - update_cmdb_ci             # update CMDB configuration item record
    - create_cmdb_ci             # create new CMDB CI for realized entities
    - retire_cmdb_ci             # retire CMDB CI on decommission
    - create_service_request     # create service request record
    - link_parent_record         # link DCM entity to existing ITSM record
    - inbound_approval           # accept approval decisions from ITSM system
    - inbound_request_initiation # allow ITSM workflows to submit DCM requests
  
  # System connectivity
  endpoint_url: <url>            # ITSM system API base URL
  api_version: <string>          # system-specific API version
  auth_credential_uuid: <uuid>   # references credential management service
  
  # Bidirectional webhook (for inbound)
  inbound_webhook:
    enabled: <bool>
    secret_credential_uuid: <uuid>   # HMAC secret for webhook verification
    
  # Field mappings (system-specific)
  field_mapping_ref: <git-path>  # path to field mapping YAML in Layer Store
  
  # CMDB CI type mapping
  cmdb_ci_type_map:
    - dcm_resource_type: Compute.VirtualMachine
      itsm_ci_type: cmdb_ci_server        # ServiceNow CI class
    - dcm_resource_type: Network.VLAN
      itsm_ci_type: cmdb_ci_network_gear
    - dcm_resource_type: Storage.Volume
      itsm_ci_type: cmdb_ci_storage_device
```

### 1.4 Required API Endpoints (ITSM integration implements)

```
POST {provider_base}/actions              # DCM submits action requests
GET  {provider_base}/actions/{action_id}  # DCM checks action status
GET  {provider_base}/records/{record_id}  # DCM retrieves record status
POST {provider_base}/inbound             # ITSM system sends inbound events
GET  /health                             # standard OIS health check
```

### 1.5 DCM Entity ITSM References

Realized entities gain an `itsm_references` block in business data:

```yaml
itsm_references:
  - system: servicenow
    provider_uuid: <itsm-provider-uuid>
    record_type: change_request
    record_id: "CHG0012345"
    record_url: "https://corp.service-now.com/nav_to.do?uri=change_request.do?sys_id=..."
    created_at: <ISO 8601>
    status: approved        # DCM's view of the record status
    last_synced_at: <ISO 8601>
    
  - system: jira_service_management
    provider_uuid: <itsm-provider-uuid>
    record_type: incident
    record_id: "INC-4821"
    record_url: "https://corp.atlassian.net/browse/INC-4821"
    created_at: <ISO 8601>
    status: open
    last_synced_at: <ISO 8601>
```

---

## 2. Supported ITSM Systems

### 2.1 ServiceNow

**API:** REST Table API (`/api/now/table/`), Business Rule webhooks, Flow Designer

```yaml
# ServiceNow ITSM integration registration
itsm_provider_registration:
  provider_handle: "servicenow-prod"
  itsm_system: servicenow
  endpoint_url: "https://corp.service-now.com"
  api_version: "v2"
  auth_credential_uuid: <uuid>    # api_key or oauth2 credential
  
  supported_actions:
    - create_change_request        # → change_request table
    - update_change_request
    - close_change_request
    - create_incident              # → incident table
    - update_cmdb_ci               # → cmdb_ci_server (or mapped class)
    - create_cmdb_ci
    - retire_cmdb_ci
    - inbound_approval             # Change Advisory Board approval → DCM vote
    
  # ServiceNow-specific field mapping
  change_request_template:
    assignment_group: "Infrastructure Automation"
    category: "Software"
    risk: "2"                      # Low
    impact: "3"                    # Low
    # DCM fields injected at runtime:
    short_description: "DCM: Provision {resource_type} '{entity_handle}'"
    description: "Requested by: {actor_handle}\nTenant: {tenant_handle}\nDCM Request: {request_uuid}"
    
  # CAB approval → DCM vote mapping
  inbound_approval:
    webhook_url: "https://dcm.corp/api/v1/admin/approvals/{approval_uuid}:vote"
    trigger_on: "change_request.state → 'Approved'"
    decision_field: "state"
    decision_map:
      "Approved": "approve"
      "Rejected": "reject"
      "Cancelled": "reject"
    external_reference_field: "number"    # → CHG0012345
    
  cmdb_ci_type_map:
    - dcm_resource_type: Compute.VirtualMachine
      itsm_ci_type: cmdb_ci_server
    - dcm_resource_type: Network.VLAN
      itsm_ci_type: cmdb_ci_netgear
    - dcm_resource_type: Storage.Volume
      itsm_ci_type: cmdb_ci_disk
    - dcm_resource_type: Kubernetes.Cluster
      itsm_ci_type: cmdb_ci_kubernetes_cluster
```

**Inbound: CAB approval flow**

```
ServiceNow Change Advisory Board approves CHG0012345
  │
  ▼ ServiceNow Business Rule fires on state change → "Approved"
  │   Calls DCM webhook: POST /api/v1/admin/approvals/{uuid}:vote
  │   Headers: X-ServiceNow-Signature: <hmac>
  │   Body: { decision: "approve", recorded_via: "servicenow",
  │           external_reference: "CHG0012345" }
  │
  ▼ DCM verifies HMAC signature against secret_credential_uuid
  │   Records approval vote
  │   Pipeline resumes if tier satisfied
```

### 2.2 Jira Service Management (Atlassian)

**API:** REST API v3, Atlassian Connect webhooks, Automation rules

```yaml
itsm_provider_registration:
  provider_handle: "jira-service-mgmt-prod"
  itsm_system: jira_service_management
  endpoint_url: "https://corp.atlassian.net"
  api_version: "3"
  auth_credential_uuid: <uuid>    # API token or OAuth2
  
  supported_actions:
    - create_change_request        # → Jira issue (Change type)
    - update_change_request
    - close_change_request
    - create_incident              # → Jira issue (Incident type)
    - create_service_request       # → Jira issue (Service Request type)
    - inbound_approval             # Jira Change approval → DCM vote
    
  change_request_template:
    project_key: "OPS"
    issue_type: "Change"
    summary: "DCM: {resource_type} '{entity_handle}'"
    description: |
      *Requested by:* {actor_handle}
      *Tenant:* {tenant_handle}
      *DCM Request UUID:* {request_uuid}
      *Catalog Item:* {catalog_item_handle}
    priority: "Medium"
    labels: ["dcm-automated", "{tenant_handle}"]
    
  inbound_approval:
    webhook_url: "https://dcm.corp/api/v1/admin/approvals/{approval_uuid}:vote"
    trigger_on: "issue.status → 'Approved'"
    decision_map:
      "Approved": "approve"
      "Declined": "reject"
    external_reference_field: "key"    # → OPS-4821
```

### 2.3 BMC Remedy / Helix ITSM

**API:** REST API (Remedy AR System REST), webhook callbacks

```yaml
itsm_provider_registration:
  provider_handle: "bmc-helix-prod"
  itsm_system: bmc_helix
  endpoint_url: "https://remedy.corp.example.com/api/arsys/v1"
  api_version: "v1"
  
  supported_actions:
    - create_change_request        # → CHG:Infrastructure Change
    - update_change_request
    - close_change_request
    - create_incident              # → HPD:Help Desk
    - update_cmdb_ci               # → AST:Config Item
    - inbound_approval
    
  change_request_template:
    form: "CHG:Infrastructure Change"
    Location_Company: "{tenant_handle}"
    Summary: "DCM: Provision {resource_type} '{entity_handle}'"
    Categorization_Tier_1: "Infrastructure"
    Categorization_Tier_2: "Provisioning"
    Change_Type: "Normal"
```

### 2.4 Freshservice

```yaml
itsm_provider_registration:
  provider_handle: "freshservice-prod"
  itsm_system: freshservice
  endpoint_url: "https://corp.freshservice.com/api/v2"
  
  supported_actions:
    - create_change_request
    - update_change_request
    - close_change_request
    - create_incident
    - create_service_request
    
  change_request_template:
    type: "Normal"
    risk: "Low"
    impact: "Low"
    subject: "DCM: {resource_type} '{entity_handle}'"
    description: "Tenant: {tenant_handle} | Actor: {actor_handle} | Request: {request_uuid}"
    group_id: <freshservice-group-id>
```

### 2.5 PagerDuty (Incident Management)

```yaml
itsm_provider_registration:
  provider_handle: "pagerduty-prod"
  itsm_system: pagerduty
  endpoint_url: "https://api.pagerduty.com"
  
  supported_actions:
    - create_incident              # for DCM failures, drift, security events
    - update_incident
    - close_incident
    
  # PagerDuty Events API v2
  incident_template:
    service_id: <pd-service-id>
    escalation_policy_id: <pd-policy-id>
    payload:
      summary: "DCM {event_type}: {entity_handle}"
      severity: "{{ drift_severity | map: critical→critical, significant→error, moderate→warning, minor→info }}"
      source: "dcm"
      custom_details:
        entity_uuid: "{entity_uuid}"
        tenant: "{tenant_handle}"
        dcm_event: "{event_type}"
```

### 2.6 Generic REST (Custom ITSM)

For ITSM systems not natively supported, the `generic_rest` type allows template-based HTTP calls:

```yaml
itsm_provider_registration:
  provider_handle: "custom-itsm-prod"
  itsm_system: generic_rest
  endpoint_url: "https://itsm.corp.example.com/api"
  
  action_templates:
    - action: create_change_request
      method: POST
      path: "/changes"
      headers:
        Content-Type: "application/json"
        X-API-Key: "{{ credential_value }}"
      body_template: |
        {
          "title": "DCM: {{ resource_type }} '{{ entity_handle }}'",
          "requested_by": "{{ actor_handle }}",
          "category": "Infrastructure",
          "external_id": "{{ request_uuid }}"
        }
      response_id_path: "$.id"    # JSONPath to extract record ID from response
      
    - action: inbound_approval
      inbound_field: "status"
      decision_map:
        "approved": "approve"
        "rejected": "reject"
```

---

## 3. ITSM Policy Type

### 3.1 What an ITSM Policy Is

An **ITSM Policy** is a new DCM Policy output type (8th, alongside GateKeeper, Validation, Transformation, Recovery, Orchestration Flow, Governance Matrix Rule, and Lifecycle Policy).

It fires as a **side-effect policy** — it does not block pipeline execution (it is not a GateKeeper) and does not transform the payload. It fires on a DCM event and triggers an ITSM action via a registered ITSM integration. The pipeline continues whether or not the ITSM action succeeds; ITSM failures are logged and alerted but do not block DCM operations.

**Key distinction:** An ITSM Policy is about *record-keeping and integration* with external governance systems. A GateKeeper Policy is about *allowing or blocking* operations. These are complementary, not competing.

### 3.2 Output Schema

```yaml
# ITSM Policy output schema
itsm_policy_output:
  type: itsm_action            # new output type identifier
  
  # Required
  itsm_provider_uuid: <uuid>   # which ITSM integration to call
  action: create_change_request | update_change_request | close_change_request |
          create_incident | update_incident | close_incident |
          update_cmdb_ci | create_cmdb_ci | retire_cmdb_ci |
          create_service_request | link_parent_record
          
  # Payload — fields to pass to ITSM integration
  # Supports template variables from the triggering event payload
  action_payload:
    <field>: <value or "{{ template_expression }}">
    
  # How to handle ITSM failure
  on_failure: log_and_continue | alert_and_continue | alert_only
  
  # Store the ITSM record reference on the DCM entity (optional)
  store_reference_on_entity: <bool>
  reference_label: <string>    # human-readable label for the reference
  
  # Require ITSM record creation before dispatch (optional — see note)
  block_until_created: <bool>  # default: false
  block_timeout: <ISO 8601 duration>  # max wait if block_until_created: true
```

> **`block_until_created`:** When `true`, the ITSM Policy behaves like a pre-dispatch gate — DCM waits for the ITSM record to be created before dispatching to the Service Provider. This is used when organizational policy requires a change record to exist before any provisioning begins. When `false` (default), the ITSM record is created in parallel with or after dispatch — suitable for notification-only use cases.

### 3.3 Example Policies

#### Policy 1: Create Change Request on Dispatch (ServiceNow)

```yaml
policy_handle: "create-change-on-dispatch"
policy_type: itsm_action
enforcement_level: soft
status: active

match:
  payload_type: request.dispatched
  conditions:
    - field: resource_type
      operator: in
      value: [Compute.VirtualMachine, Storage.Volume, Network.VLAN]

output:
  type: itsm_action
  itsm_provider_uuid: <servicenow-provider-uuid>
  action: create_change_request
  action_payload:
    short_description: "DCM: Provision {{ resource_type }} '{{ entity_handle }}'"
    description: |
      Automated provisioning via DCM.
      Request UUID: {{ request_uuid }}
      Actor: {{ actor_handle }}
      Tenant: {{ tenant_handle }}
      Catalog Item: {{ catalog_item_handle }}
    risk: "{{ risk_score | map: <25→'Low', <60→'Medium', else→'High' }}"
  store_reference_on_entity: true
  reference_label: "Change Request"
  on_failure: alert_and_continue
```

#### Policy 2: Block Dispatch Until Change Record Exists (Compliance Gate)

```yaml
policy_handle: "require-change-record-before-dispatch"
policy_type: itsm_action
enforcement_level: hard
status: active

match:
  payload_type: request.layers_assembled
  conditions:
    - field: tenant_handle
      operator: in
      value: [payments-team, pci-scope-team]

output:
  type: itsm_action
  itsm_provider_uuid: <servicenow-provider-uuid>
  action: create_change_request
  action_payload:
    short_description: "DCM: {{ resource_type }} provision — {{ tenant_handle }}"
    change_type: "Normal"
    assignment_group: "Change Advisory Board"
  store_reference_on_entity: true
  reference_label: "Change Request (PCI Scope)"
  block_until_created: true
  block_timeout: PT30M
  on_failure: alert_and_continue
```

#### Policy 3: Update CMDB on Realization

```yaml
policy_handle: "sync-cmdb-on-realization"
policy_type: itsm_action
status: active

match:
  payload_type: entity.realized
  conditions:
    - field: resource_type
      operator: in
      value: [Compute.VirtualMachine, Compute.BareMetalServer]

output:
  type: itsm_action
  itsm_provider_uuid: <servicenow-provider-uuid>
  action: create_cmdb_ci
  action_payload:
    name: "{{ entity_handle }}"
    ip_address: "{{ realized_fields.primary_ip }}"
    os: "{{ realized_fields.os_family }}"
    managed_by: "DCM"
    environment: "{{ tenant_handle }}"
    correlation_id: "{{ entity_uuid }}"
  store_reference_on_entity: true
  reference_label: "CMDB CI"
  on_failure: alert_and_continue
```

#### Policy 4: Create Incident on Drift (Jira)

```yaml
policy_handle: "create-incident-on-critical-drift"
policy_type: itsm_action
status: active

match:
  payload_type: drift.detected
  conditions:
    - field: drift_severity
      operator: in
      value: [significant, critical]

output:
  type: itsm_action
  itsm_provider_uuid: <jira-provider-uuid>
  action: create_incident
  action_payload:
    summary: "DCM Drift: {{ entity_handle }} — {{ drift_severity }}"
    description: |
      DCM has detected significant configuration drift.
      Entity: {{ entity_handle }} ({{ entity_uuid }})
      Severity: {{ drift_severity }}
      Drifted fields: {{ drifted_fields | count }} fields
      Detected at: {{ discovered_at }}
      View in DCM: https://dcm.corp/resources/{{ entity_uuid }}/drift
    priority: "{{ drift_severity | map: critical→'Highest', significant→'High' }}"
    labels: ["dcm-drift", "{{ resource_type | slugify }}"]
  store_reference_on_entity: true
  reference_label: "Drift Incident"
  on_failure: log_and_continue
```

#### Policy 5: Retire CMDB CI on Decommission

```yaml
policy_handle: "retire-cmdb-on-decommission"
policy_type: itsm_action
status: active

match:
  payload_type: entity.decommissioned

output:
  type: itsm_action
  itsm_provider_uuid: <servicenow-provider-uuid>
  action: retire_cmdb_ci
  action_payload:
    correlation_id: "{{ entity_uuid }}"    # find CI by DCM entity UUID
    install_status: "7"                    # ServiceNow: Retired
    retired_at: "{{ event_timestamp }}"
    decommission_reason: "DCM decommission — {{ actor_handle }}"
  on_failure: alert_and_continue
```

#### Policy 6: Close Change Record on Completion

```yaml
policy_handle: "close-change-on-completion"
policy_type: itsm_action
status: active

match:
  payload_type: request.realized
  conditions:
    - field: entity.itsm_references[?(@.record_type=='change_request')].record_id
      operator: exists

output:
  type: itsm_action
  itsm_provider_uuid: <servicenow-provider-uuid>
  action: close_change_request
  action_payload:
    state: "3"                              # ServiceNow: Closed
    close_code: "Successful"
    close_notes: "Provisioning completed successfully by DCM. Entity: {{ entity_uuid }}"
  on_failure: log_and_continue
```

---

## 4. ITSM integration System Policies

| Policy | Rule |
|--------|------|
| `ITSM-001` | ITSM integrations implement the base Provider contract (PRV-001) including registration, health check, sovereignty declaration, and zero trust authentication. ITSM system connectivity credentials must reference a registered credential management service — no plaintext credentials in provider registration. |
| `ITSM-002` | DCM does not require ITSM integration to function. ITSM Policies with `on_failure: alert_and_continue` (the default) never block DCM pipeline execution. Organizations must explicitly set `block_until_created: true` to gate pipeline on ITSM record creation. |
| `ITSM-003` | Inbound events from ITSM systems must be authenticated. ITSM integrations must verify HMAC signatures or OAuth tokens on all inbound webhooks before forwarding to DCM. Unauthenticated inbound events are rejected and logged. |
| `ITSM-004` | ITSM record references stored on DCM entities follow entity lifecycle — they are included in the Realized State record, preserved through updates, and retained in the decommissioned entity record for audit purposes. |
| `ITSM-005` | ITSM Policies that use `block_until_created: true` must declare a `block_timeout`. If the ITSM system does not confirm record creation within the timeout, the policy fires `on_failure` behavior and the block is released — the pipeline continues. A blocked pipeline is never permanently stalled by ITSM unavailability. |
| `ITSM-006` | Field mappings between DCM entities and ITSM CI types must be declared in the ITSM integration capability registration. Unmapped resource types are silently skipped for CMDB sync actions. |
| `ITSM-007` | Template expressions in ITSM Policy `action_payload` fields must resolve using values from the triggering event payload. Template expressions that reference unavailable fields produce a warning in the audit record and substitute an empty string. They do not block ITSM action execution. |

---

## 5. ITSM Policy System Policies

| Policy | Rule |
|--------|------|
| `ITSM-POL-001` | ITSM Policies follow the full Policy base contract (B-policy-contract.md): lifecycle (developing → proposed → active), shadow mode validation, audit obligation on every evaluation, domain precedence. |
| `ITSM-POL-002` | ITSM Policies are side-effect policies — they do not produce pipeline decisions (allow/deny/transform). They may not be used as GateKeeper substitutes except through the explicit `block_until_created: true` mechanism, which has its own timeout guarantee (ITSM-005). |
| `ITSM-POL-003` | ITSM Policy evaluation is recorded in the audit trail. The audit record includes: policy handle, matched event, ITSM provider UUID, action requested, ITSM record ID returned, and outcome (success/failure/timeout). |
| `ITSM-POL-004` | Multiple ITSM Policies may fire on the same event. All fire independently — one policy's failure does not prevent other ITSM Policies from executing. |

---

## 6. Additions to the Foundations Document

The foundations document provider type table gains a 12th row:

| Provider Type | Capability | Data direction |
|--------------|-----------|----------------|
| **ITSM integration** | Bidirectional integration with ITSM systems; creates/updates ITSM records from DCM events; routes ITSM approvals back to DCM | DCM → ITSM (outbound) / ITSM → DCM (inbound) |

The foundations document policy type table gains an 8th entry:

| Policy Type | Output | Pipeline role |
|------------|--------|---------------|
| **ITSM Action** | Triggers action in connected ITSM system; optionally stores record reference on entity; optionally gates pipeline on record creation | Side-effect (non-blocking by default) |

---

## 7. Event Catalog Additions

Two new events for the Event Catalog (doc 33):

| Event Type | Urgency | Trigger |
|-----------|---------|---------|
| `itsm.record_created` | info | ITSM integration successfully created a record in external system |
| `itsm.record_failed` | medium | ITSM integration failed to create/update record; `block_until_created` timeout reached |

These extend the existing event catalog with a new `itsm.*` domain prefix.

---

## 8. Standards Catalog Addition

ITSM integration standards and protocols used:

| Standard | Use in DCM ITSM |
|----------|----------------|
| ServiceNow REST Table API | Primary integration for ServiceNow create/update/query |
| Jira REST API v3 | Primary integration for Atlassian Jira Service Management |
| BMC AR REST API v1 | Primary integration for BMC Remedy/Helix |
| PagerDuty Events API v2 | Incident creation for alert-type ITSM integrations |
| ITIL v4 Change Management | Conceptual framework for DCM change record lifecycle mapping |
| JSON:API | Standard used by several ITSM REST APIs |
| HMAC-SHA256 | Inbound webhook signature verification for all ITSM systems |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
