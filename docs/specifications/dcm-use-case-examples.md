# DCM — Use Case Examples

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Use Case Reference
**Related Documents:** [Examples and Use Cases](dcm-examples.md) | [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Four States](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md) | [Layering and Versioning](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md) | [Governance Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md) | [Scoring Model](../../architecture/convergence-engine/scoring.md)

> This document contains worked examples for every DCM provider type, data model, and specification
> area not covered in [dcm-examples.md](dcm-examples.md). Examples use consistent fictitious actors,
> tenants, and providers throughout for cross-reference coherence.

---

## Shared Context

All examples reference these fictitious entities:

```
Tenants:
  payments-bu         UUID: ten-pay-001   Business unit: card payment processing
  web-platform-bu     UUID: ten-web-001   Business unit: customer-facing web
  platform-team       UUID: ten-plt-001   Platform engineering (admin)

Actors:
  alice@corp.example  UUID: act-alice-001  Developer, payments-bu
  bob@corp.example    UUID: act-bob-001    Platform engineer, platform-team
  svc-pipeline@corp   UUID: act-svc-001    CI/CD service account

Providers:
  vmware-prod         UUID: pvd-vm-001     Service Provider — Compute.VirtualMachine
  netbox-prod         UUID: pvd-net-001    Information Provider — Network.IPAddress
  vault-prod          UUID: pvd-vlt-001    credential management service
  freeipa-prod        UUID: pvd-ipa-001    Auth Provider — FreeIPA/LDAP
  ceph-prod           UUID: pvd-cph-001    data store — Realized State snapshots
  rabbitmq-prod       UUID: pvd-rmq-001    event routing service
  servicenow-prod     UUID: pvd-sn-001     ITSM integration — ServiceNow
  webapp-meta         UUID: pvd-wam-001    composite service definition — ApplicationStack.WebApp

Data Centers / Zones:
  dc-west-1 / zone-a    Primary production zone
  dc-east-1 / zone-b    DR zone
```

---

# Section 1 — Data Model Examples

## 1.1 The Four States — VM Lifecycle from Request to Decommission

This example traces a single `Compute.VirtualMachine` entity through all four states, from the consumer's original intent through decommission.

**Step 1: Consumer submits a request — Intent State created**

```
POST /api/v1/requests
Authorization: Bearer <alice-session-token>

{
  "catalog_item_uuid": "cat-vm-standard",
  "fields": {
    "vm_name": "payments-api-03",
    "cpu_cores": 8,
    "ram_gb": 32,
    "os": "RHEL 9",
    "zone": "dc-west-1/zone-a",
    "purpose": "payments API service node"
  }
}
```

DCM immediately writes the Intent State record — immutable from this moment forward:

```yaml
intent_state_record:
  intent_uuid: int-pay-api-03
  entity_uuid: ent-vm-pay-03      # assigned on first request
  tenant_uuid: ten-pay-001
  actor_uuid:  act-alice-001
  recorded_at: 2026-03-31T09:00:00Z

  # Verbatim consumer input — never altered by policy
  raw_intent:
    catalog_item_uuid: cat-vm-standard
    fields:
      vm_name: payments-api-03
      cpu_cores: 8
      ram_gb: 32
      os: RHEL 9
      zone: dc-west-1/zone-a
      purpose: payments API service node
```

**Step 2: Layer assembly and policy evaluation — Requested State built**

DCM's Request Payload Processor assembles layers in precedence order:

```yaml
# Layer 1 — Base (org-wide standards)
dcm:
  network:
    dns_suffix: .internal.corp.example
  security:
    selinux: enforcing
    firewall: enabled

# Layer 2 — Data Center (dc-west-1)
location:
  datacenter: dc-west-1
  rack_prefix: rack-w1
  power_domain: ups-west-primary

# Layer 3 — Payments BU Service Layer
compliance:
  pci_dss: true
  network_segment: payments-dmz
  encryption_at_rest: required
  log_retention_days: 365

# Layer 4 — Request Layer (consumer-supplied fields)
vm:
  name: payments-api-03
  cpu_cores: 8
  ram_gb: 32
  os_image: rhel-9-latest-approved   # enriched from "RHEL 9" by Transformation policy
  zone: dc-west-1/zone-a
```

Gating policy fires: `payments-dmz` placement requires PCI DSS accreditation on the provider → `pvd-vm-001` has active PCI DSS accreditation → PASS.

Transformation policy fires: `cpu_cores: 8` in payments zone → sets `cpu_pinning: true` per PCI DSS performance isolation requirement.

Requested State written (the fully assembled, policy-approved dispatch payload):

```yaml
requested_state_record:
  requested_state_uuid: req-pay-api-03
  entity_uuid: ent-vm-pay-03
  intent_uuid: int-pay-api-03
  tenant_uuid: ten-pay-001
  provider_uuid: pvd-vm-001        # placement resolved
  assembled_at: 2026-03-31T09:00:05Z

  payload:
    vm_name: payments-api-03
    cpu_cores: 8
    cpu_pinning: true              # injected by Transformation policy
    ram_gb: 32
    os_image: rhel-9-latest-approved
    network_segment: payments-dmz
    encryption_at_rest: true
    log_retention_days: 365
    zone: dc-west-1/zone-a
    selinux: enforcing
```

**Step 3: Provider realizes the request — Realized State written**

Provider confirms provisioning and returns:

```yaml
realized_state_snapshot:
  realized_state_uuid: rlz-pay-api-03-v1
  entity_uuid: ent-vm-pay-03
  source_requested_state_uuid: req-pay-api-03
  realized_at: 2026-03-31T09:02:47Z
  lifecycle_state: OPERATIONAL

  # Provider-supplied realization details (added to assembled payload)
  provider_data:
    resource_id: vm-4821                  # provider's internal ID
    hypervisor_host: esxi-w1-rack3-b04
    mac_address: 00:50:56:ab:cd:ef
    assigned_ip: 10.42.18.55
    boot_time: 2026-03-31T09:02:31Z
    bios_uuid: 4201abcd-0000-0000-0000-000000000001
```

**Step 4: Discovery confirms state — Discovered State updated**

Discovery Scheduler polls `pvd-vm-001` 24 hours later:

```yaml
discovered_state_record:
  entity_uuid: ent-vm-pay-03
  discovered_at: 2026-04-01T09:05:00Z
  provider_uuid: pvd-vm-001
  resource_id: vm-4821

  discovered_fields:
    cpu_cores: 8
    ram_gb: 32
    os_image: rhel-9-latest-approved
    cpu_pinning: true
    power_state: running
    uptime_hours: 24.1
    disk_usage_pct: 12

# Drift check: all discovered fields match Realized State → no drift
# drift_record: null
```

**Step 5: Decommission**

```
DELETE /api/v1/resources/ent-vm-pay-03

# Entity enters DECOMMISSIONING → provider deletes VM → DECOMMISSIONED
# Intent, Requested, and Realized State records are retained for audit
# Discovered State cleared
```

---

## 1.2 Layer Assembly — Full Walkthrough

A request for a web server in the payments zone demonstrates how six layers compose into a single dispatch payload.

**Layers in precedence order (lowest → highest):**

```yaml
# Layer 0: Base entity (org-wide defaults)
---
handle: layers/base/compute/vm-standard
version: "3.1.0"
type: base_entity
data:
  selinux: enforcing
  firewall: enabled
  ntp_server: ntp.internal.corp.example
  dns_suffix: .internal.corp.example
  monitoring_agent: node_exporter
  log_collector: filebeat
  log_destination: logs.corp.example:5044
```

```yaml
# Layer 1: Data Center — dc-west-1
---
handle: layers/dc/west-1
version: "2.0.0"
parent: layers/base/compute/vm-standard@3.1.0
type: layer_entity
data:
  location:
    datacenter: dc-west-1
    region: us-west
    rack_prefix: rack-w1
    power_domain: ups-west-primary
  network:
    gateway: 10.42.0.1
    dns: [10.42.0.53, 10.42.0.54]
```

```yaml
# Layer 2: Zone — dc-west-1/zone-a (DMZ)
---
handle: layers/zone/west-1-zone-a-dmz
version: "1.5.0"
parent: layers/dc/west-1@2.0.0
type: layer_entity
data:
  network:
    segment: dmz-payments
    vlan: 142
    firewall_policy: payments-dmz-policy
  compliance:
    pci_dss: true
    log_retention_days: 365
```

```yaml
# Layer 3: Payments BU service layer
---
handle: layers/service/payments-bu/compute
version: "1.2.0"
parent: layers/zone/west-1-zone-a-dmz@1.5.0
type: layer_entity
data:
  security:
    cpu_pinning: true            # PCI isolation
    encryption_at_rest: required
  backup:
    enabled: true
    frequency: daily
    retention: 30d
```

```yaml
# Layer 4: Web server service layer
---
handle: layers/service/web-platform/nginx-config
version: "2.0.0"
parent: layers/service/payments-bu/compute@1.2.0
type: layer_entity
data:
  software:
    packages: [nginx, certbot]
    nginx_config_ref: git://configs/nginx/standard.conf@v3
  ports_open: [80, 443]
```

```yaml
# Layer 5: Request layer (consumer-supplied)
---
type: request_layer
data:
  vm_name: payments-web-07
  cpu_cores: 4
  ram_gb: 16
  os_image: rhel-9-latest-approved
  zone: dc-west-1/zone-a
```

**Assembled payload (higher layers win on conflict):**

```yaml
# Assembled dispatch payload sent to pvd-vm-001
assembled_payload:
  vm_name: payments-web-07         # from request layer
  cpu_cores: 4                     # from request layer
  ram_gb: 16                       # from request layer
  os_image: rhel-9-latest-approved # from request layer
  selinux: enforcing               # from base (not overridden)
  firewall: enabled                # from base (not overridden)
  ntp_server: ntp.internal.corp.example
  dns_suffix: .internal.corp.example
  monitoring_agent: node_exporter  # from base
  log_collector: filebeat          # from base
  log_destination: logs.corp.example:5044
  location:
    datacenter: dc-west-1          # from dc layer
    region: us-west
    rack_prefix: rack-w1
  network:
    segment: dmz-payments          # from zone layer (overrides dc layer)
    vlan: 142
    gateway: 10.42.0.1
    dns: [10.42.0.53, 10.42.0.54]
    firewall_policy: payments-dmz-policy
  compliance:
    pci_dss: true                  # from zone layer
    log_retention_days: 365
  security:
    cpu_pinning: true              # from payments BU layer
    encryption_at_rest: required
  backup:
    enabled: true
    frequency: daily
    retention: 30d
  software:
    packages: [nginx, certbot]     # from web layer
    nginx_config_ref: git://configs/nginx/standard.conf@v3
  ports_open: [80, 443]

provenance:
  # Every field carries its source layer and the actor who set it
  - field: cpu_pinning
    value: true
    source: layers/service/payments-bu/compute@1.2.0
    set_by: bob@corp.example
    reason: PCI DSS compute isolation requirement
  - field: log_retention_days
    value: 365
    source: layers/zone/west-1-zone-a-dmz@1.5.0
    set_by: compliance-team@corp.example
    reason: PCI DSS requirement 10.5
```

---

## 1.3 Governance Matrix — PHI Data Request Evaluation

A developer in the `web-platform-bu` tenant requests a VM to host a new microservice that will process Protected Health Information (PHI). DCM evaluates the four-axis governance matrix.

**The request:**

```yaml
subject: actor act-alice-001         # Axis 1: WHO
  tenant: ten-web-001
  mfa_verified: true
  session_risk_score: 0.12           # low — recent login, known device

data: payload.data_classifications   # Axis 2: WHAT
  contains: [phi]                    # request fields marked phi by policy

target: pvd-vm-001                   # Axis 3: WHERE
  sovereignty_zone: us-commercial
  accreditations: [iso_27001, soc2_type2]   # no hipaa_baa

context:                             # Axis 4: UNDER WHAT CONDITIONS
  profile: prod
  time: 2026-03-31T14:00:00Z         # business hours
  request_risk_score: 68             # elevated — PHI + no BAA
```

**Axis 1 (Subject):** Actor is authenticated, MFA verified, session risk low → PASS

**Axis 2 (Data):** Payload contains PHI classification → triggers HIPAA rules

**Axis 3 (Target):** `pvd-vm-001` is checked for HIPAA BAA accreditation → **no BAA registered** → FAIL

**Axis 4 (Context):** `prod` profile requires accreditation completeness for PHI → DENY

**Governance Matrix decision:**

```yaml
governance_decision:
  outcome: DENY
  rule_matched: "PHI data requires HIPAA BAA on target provider"
  axis_failing: target
  detail:
    provider_uuid: pvd-vm-001
    missing_accreditation: hipaa_baa
    required_for: phi classification in payload
  remediation:
    option_1: "Submit BAA for pvd-vm-001 and await activation"
    option_2: "Route to a provider with active HIPAA BAA accreditation"
    option_3: "Remove PHI from this service's data scope"

# Request is blocked before dispatch — no Requested State written
# Consumer receives:
{
  "error": {
    "code": "GOVERNANCE_DENIED",
    "message": "PHI data cannot be placed on pvd-vm-001 — HIPAA BAA not present",
    "remediation": "Contact your platform admin to add a BAA for this provider"
  }
}
```

---

## 1.4 Scoring Model — Risk Score and Placement Decision

Three providers are candidates for a Tier 1 VM request. DCM calculates a risk score and routes to the approval tier.

**Signals for this request:**

```yaml
# Signal 1: Operational Gating Policy Score
# No Gating policies fired → score: 0 (lowest risk)
signal_1: 0

# Signal 2: Policy Completeness Score
# All policies evaluated; no shadow-only policies for this resource type → score: 0
signal_2: 0

# Signal 3: Actor Risk History Score
# alice@corp.example — no failed requests, no policy violations in 90 days → score: 5
signal_3: 5

# Signal 4: Tenant Quota Pressure Score
# payments-bu is at 62% of VM quota → moderate pressure → score: 18
signal_4: 18

# Signal 5: Provider Accreditation Richness (for placement tie-breaking)
# pvd-vm-001: iso_27001(20) + soc2_type2(20) + pci_dss(25) = 65 → external verified P1D → ×1.0
# pvd-vm-002: iso_27001(20) + soc2_type2(20) = 40 → external verified P7D → ×0.9 = 36
# pvd-vm-003: soc2_type2(20) = 20 → stale verification → ×0.4 = 8

aggregate_risk_score:
  formula: "(signal_1 × 0.35) + (signal_2 × 0.25) + (signal_3 × 0.20) + (signal_4 × 0.15) + (signal_5_inverse × 0.05)"
  value: 21
  # 21 → STANDARD tier (threshold: 0-39 = STANDARD, 40-69 = ELEVATED, 70+ = CRITICAL)
```

**Authority Tier routing:**

```yaml
# Risk score 21 → STANDARD tier → no additional approval required
# Placement: pvd-vm-001 wins (highest accreditation richness score: 65)

placement_decision:
  provider_uuid: pvd-vm-001
  approval_tier: STANDARD
  auto_approved: true
  rationale: "Risk score 21 < 40 threshold; pvd-vm-001 highest accreditation richness"
```

**Contrast — the same request from a high-risk actor:**

```yaml
# If signal_3 (actor risk) = 45 (recent policy violations):
aggregate_risk_score: 52   # → ELEVATED tier

placement_decision:
  provider_uuid: pvd-vm-001
  approval_tier: ELEVATED
  auto_approved: false
  requires_approval_from:
    - role: tenant_admin            # payments-bu tenant admin
  approval_deadline: PT4H
```

---

## 1.5 Authority Tier Model — Multi-Tier Approval Routing

A developer requests 200 VMs simultaneously (bulk deployment for a load test). Risk score crosses the CRITICAL threshold and requires multi-tier sign-off.

```yaml
# Bulk request: 200 × Compute.VirtualMachine for load-test-bu tenant
# Signal 4 (quota pressure): 200 VMs = 95% of quota → score: 38
# Signal 3 (actor history): svc-pipeline@corp — automated, clean history → 0
# Aggregate risk score: 58 → ELEVATED

# But: 200 instances triggers an additional policy:
#   "bulk_request_over_100 → escalate to CRITICAL tier"
# Gating Policy fires and elevates: score_override: CRITICAL

authority_tier_routing:
  risk_score_raw: 58
  score_override: CRITICAL       # Gating Policy escalation
  tier_applied: CRITICAL
  approval_chain:
    - step: 1
      approver_role: tenant_admin
      tenant_uuid: ten-web-001
      deadline: PT2H
      status: pending

    - step: 2
      approver_role: platform_admin
      deadline: PT4H             # starts after step 1 approved
      status: waiting

    - step: 3
      approver_role: ciso_delegate
      deadline: PT8H             # starts after step 2 approved
      status: waiting

  # If any step times out → request enters APPROVAL_EXPIRED state
  # Policy: NOTIFY_AND_WAIT → Compliance Team paged
```

**Tenant admin approves (step 1):**

```
POST /api/v1/approvals/apv-bulk-load-001
Authorization: Bearer <tenant-admin-token>

{
  "decision": "approve",
  "rationale": "Authorized load test — signed off by VP Engineering"
}

# → step 2 notification fires to platform admin
```

---

## 1.6 Entity Relationships — Composite Web Service

A `Compute.VirtualMachine`, `Network.IPAddress`, and `Security.FirewallRule` are related as a composite web service entity.

```yaml
# Three entities with explicit relationships
entities:
  - entity_uuid: ent-vm-pay-03       # the VM
    resource_type: Compute.VirtualMachine
    tenant_uuid: ten-pay-001

  - entity_uuid: ent-ip-pay-03       # the IP assigned to the VM
    resource_type: Network.IPAddress
    tenant_uuid: ten-pay-001

  - entity_uuid: ent-fw-pay-03       # the firewall rule permitting traffic
    resource_type: Security.FirewallRule
    tenant_uuid: ten-pay-001

relationships:
  - relationship_uuid: rel-001
    from_entity: ent-vm-pay-03
    to_entity: ent-ip-pay-03
    relationship_type: assigned_to
    cardinality: one_to_one
    required_for_delivery: true      # VM cannot be OPERATIONAL without an IP

  - relationship_uuid: rel-002
    from_entity: ent-vm-pay-03
    to_entity: ent-fw-pay-03
    relationship_type: protected_by
    cardinality: one_to_many
    required_for_delivery: false     # VM can be OPERATIONAL; rule is operational hygiene
```

**Impact of decommissioning the VM:**

```yaml
# Consumer: DELETE /api/v1/resources/ent-vm-pay-03
# DCM evaluates relationship graph before dispatch:

decommission_impact_analysis:
  entity: ent-vm-pay-03
  dependents:
    - entity_uuid: ent-ip-pay-03
      relationship: assigned_to
      impact: IP address released → available for reassignment
      action: decommission_with_parent

    - entity_uuid: ent-fw-pay-03
      relationship: protected_by
      impact: Firewall rule becomes orphaned — no host to protect
      action: notify_admin           # rule not auto-deleted; may apply to other VMs

  consumer_presented:
    "Decommissioning this VM will release IP ent-ip-pay-03. Firewall rule
     ent-fw-pay-03 will become orphaned and require manual review."
```

---

## 1.7 Universal Groups — Tenant, Resource Group, and Cross-Tenant Sharing

**Setup: payments-bu tenant with a resource group and a shared database**

```yaml
# Tenant (group_class: tenant_boundary)
dcm_group:
  uuid: ten-pay-001
  group_class: tenant_boundary
  handle: tenants/payments-bu
  display_name: Payments Business Unit
  members:
    - { type: actor, uuid: act-alice-001, role: member }
    - { type: actor, uuid: act-pay-admin, role: tenant_admin }

# Resource group within the tenant (group_class: resource_group)
dcm_group:
  uuid: rg-pay-api-servers
  group_class: resource_group
  handle: tenants/payments-bu/groups/api-servers
  parent_tenant_uuid: ten-pay-001
  display_name: Payments API Servers
  members:
    - { type: entity, uuid: ent-vm-pay-01, role: member }
    - { type: entity, uuid: ent-vm-pay-02, role: member }
    - { type: entity, uuid: ent-vm-pay-03, role: member }
```

**Cross-tenant sharing: payments-bu shares a read-only DB with web-platform-bu**

```yaml
# Authorization record (cross-tenant read access)
cross_tenant_authorization:
  uuid: xta-db-share-001
  grantor_tenant: ten-pay-001
  grantee_tenant: ten-web-001
  scope:
    entity_uuids: [ent-db-pay-analytics]
    permissions: [read]             # not write or decommission
  expires_at: 2026-12-31T23:59:59Z
  approved_by: act-pay-admin
  governance_matrix_check: ALLOW    # PHI not in this DB; cross-tenant read permitted

# web-platform-bu can now query:
GET /api/v1/resources/ent-db-pay-analytics
# → 200 OK (authorized via cross-tenant grant)

DELETE /api/v1/resources/ent-db-pay-analytics
# → 403 Forbidden (write not in grant scope)
```

---

## 1.8 Scheduled Requests and Maintenance Windows

**Scenario: OS patch deployment during an approved maintenance window**

**Step 1: Platform admin defines maintenance window**

```
POST /api/v1/admin/maintenance-windows

{
  "display_name": "Q2 OS Patching — West Zone",
  "starts_at": "2026-04-06T02:00:00Z",
  "ends_at":   "2026-04-06T06:00:00Z",
  "scope": {
    "tenant_uuids": ["ten-pay-001", "ten-web-001"],
    "resource_types": ["Compute.VirtualMachine"]
  },
  "change_freeze": false
}

Response: { "window_uuid": "mw-q2-patch-001" }
```

**Step 2: CI/CD pipeline submits a deferred patching request**

```
POST /api/v1/requests

{
  "catalog_item_uuid": "cat-os-patch-rhel9",
  "fields": {
    "target_entity_uuid": "ent-vm-pay-03",
    "patch_baseline": "rhel9-2026-q2",
    "pre_patch_snapshot": true
  },
  "scheduled_at": "2026-04-06T02:15:00Z",
  "maintenance_window_uuid": "mw-q2-patch-001"
}

Response:
{
  "name": "/api/v1/operations/req-patch-pay-03",
  "done": false,
  "metadata": {
    "stage": "SCHEDULED",
    "scheduled_at": "2026-04-06T02:15:00Z",
    "resource_uuid": "ent-vm-pay-03"
  }
}
```

**Step 3: At 02:15Z — window opens, request executes**

```yaml
# Orchestrator fires at scheduled_at
# Entity: OPERATIONAL → UPDATING
# Process.OSPatch entity created, linked to VM entity
# Provider receives:

dispatch_payload:
  entity_uuid: ent-vm-pay-03
  operation: patch
  patch_baseline: rhel9-2026-q2
  pre_patch_snapshot: true
  maintenance_window_uuid: mw-q2-patch-001

# Provider: takes snapshot, applies patches, reboots, validates
# Callback received: OPERATIONAL
# New Realized State written with updated os_patch_level
# Process.OSPatch entity: DECOMMISSIONED (process complete)
```

---

## 1.9 Request Dependency Graph — Multi-Resource Compound Provisioning

A CI/CD pipeline provisions three resources with strict ordering: DB first, then app server, then load balancer (which needs both IPs).

**Step 1: Submit the dependency group**

```
POST /api/v1/request-groups

{
  "display_name": "payments-api-stack-v2 rollout",
  "requests": [
    {
      "client_id": "db",
      "catalog_item_uuid": "cat-postgresql-ha",
      "fields": { "db_name": "payments_v2", "storage_gb": 500 }
    },
    {
      "client_id": "app",
      "catalog_item_uuid": "cat-vm-standard",
      "fields": { "vm_name": "payments-api-04", "cpu_cores": 8 },
      "depends_on": ["db"],
      "wait_for": "OPERATIONAL",
      "inject_from_dependency": {
        "db": { "db_host": "$.realized.assigned_ip" }
      }
    },
    {
      "client_id": "lb",
      "catalog_item_uuid": "cat-haproxy-config",
      "fields": { "pool_name": "payments-api-pool" },
      "depends_on": ["app"],
      "wait_for": "OPERATIONAL",
      "inject_from_dependency": {
        "app": { "backend_ips": "$.realized.assigned_ip" }
      }
    }
  ]
}

Response: { "group_uuid": "grp-pay-stack-v2" }
```

**Step 2: Execution sequence**

```
T+0s    DB request dispatched → pvd-pg-001
T+90s   DB realized → assigned_ip: 10.42.18.100
        DB field injection into app request:  db_host: 10.42.18.100
T+90s   App request dispatched → pvd-vm-001 (with db_host injected)
T+150s  App realized → assigned_ip: 10.42.18.55
        App field injection into lb request: backend_ips: [10.42.18.55]
T+150s  LB request dispatched → pvd-lb-001 (with backend_ips injected)
T+165s  LB realized → all three OPERATIONAL
        Group status: COMPLETE
```

**Query group status at any point:**

```
GET /api/v1/request-groups/grp-pay-stack-v2

{
  "group_uuid": "grp-pay-stack-v2",
  "status": "IN_PROGRESS",
  "requests": [
    { "client_id": "db",  "status": "OPERATIONAL", "entity_uuid": "ent-db-pay-v2" },
    { "client_id": "app", "status": "PROVISIONING", "entity_uuid": "ent-vm-pay-04" },
    { "client_id": "lb",  "status": "PENDING_DEPENDENCY", "entity_uuid": null }
  ]
}
```

---

## 1.10 Workload Analysis — Discovered VM Classified and Ingested

A VM exists in the data center that was never provisioned through DCM. Discovery finds it; Workload Analysis classifies it; ingestion brings it under lifecycle management.

**Step 1: Discovery Scheduler finds unknown VM**

```yaml
discovered_state_record:
  entity_uuid: null                  # no DCM UUID yet — new entity
  provider_uuid: pvd-vm-001
  provider_entity_id: vm-9917        # provider's internal ID
  discovered_at: 2026-03-31T08:00:00Z

  discovered_fields:
    ip_address: 10.42.22.77
    hostname: legacy-payments-batch
    os: RHEL 7.9
    cpu_cores: 4
    ram_gb: 8
    running_processes: [java, cron, rsync]
    open_ports: [8080, 22]
    disk_gb: 200

# DCM assigns a provisional entity_uuid and writes INGESTED state
entity_uuid: ent-disc-9917
lifecycle_state: INGESTED
tenant_uuid: __transitional__
```

**Step 2: Workload Analysis fires automatically**

```yaml
# Analysis.WorkloadProfile entity created
workload_profile_entity:
  entity_uuid: ent-wla-9917
  resource_type: Analysis.WorkloadProfile
  subject_entity_uuid: ent-disc-9917
  lifecycle_state: OPERATIONAL

  classification:
    resource_type_match:
      primary: Compute.VirtualMachine
      confidence: high

    workload_archetype:
      type: batch_processor
      confidence: medium
      signals:
        - "cron present: scheduled job execution"
        - "java process: JVM-based batch framework"
        - "rsync present: data sync pattern"
        - "port 8080: likely management API, not customer-facing"
        - "RHEL 7.9: end-of-life — upgrade candidate"

    migration_readiness:
      containerization_score: 4      # low — stateful batch job, not container-friendly
      blockers:
        - "Stateful data in /data — requires persistent volume mapping"
        - "RHEL 7.9 runtime — requires migration to RHEL 9 base image first"
      suggested_target: Compute.VirtualMachine    # stay as VM, upgrade OS

    lifecycle_recommendation:
      dcm_lifecycle_model: standard
      rehydration_eligible: true
      notes: "Application on /opt, data on /data — static replace eligible after OS upgrade"
```

**Step 3: Platform admin enriches and promotes**

```
PATCH /api/v1/resources/ent-disc-9917
{
  "tenant_uuid": "ten-pay-001",
  "display_name": "Payments Batch Processor (Legacy)",
  "cost_center": "CC-PAY-OPS",
  "owner": { "actor_uuid": "act-pay-admin" }
}

# Auto-assignment policy fires: batch_processor archetype → assign to 'batch-workloads' resource group
# Entity promoted: INGESTED → ENRICHING → PROMOTED → OPERATIONAL
# Entity now under full DCM lifecycle management
```

---

## 1.11 Accreditation Monitor — FedRAMP Verification and Mid-Cycle Revocation

**Setup: Provider with FedRAMP High accreditation**

```yaml
accreditation:
  artifact_metadata:
    uuid: acc-fr-high-001
    handle: accreditations/providers/pvd-vm-fed-001/fedramp-high
    version: "1.0.0"
    status: active

  subject_uuid: pvd-vm-fed-001
  framework: fedramp_high
  accreditation_type: regulatory_certification
  accreditor:
    name: FedRAMP PMO
    type: government

  issued_at: 2025-06-01T00:00:00Z
  expires_at: 2026-06-01T00:00:00Z
  renewal_warning_before: P90D

  external_registry_id: FR2025-0088    # FedRAMP Marketplace ID

  verification:
    tier: external_registry
    registry_api:
      provider: fedramp
      lookup_key: FR2025-0088
      poll_interval: P1D
      last_checked_at: 2026-03-30T09:00:00Z
      last_result: confirmed_active
    stale_after: P3D
    stale_action: escalate           # sovereign profile — escalate not warn
```

**Day 1: Normal verification cycle**

```yaml
# Accreditation Monitor polls marketplace.fedramp.gov
# GET /api/products?id=FR2025-0088
# Response: { "status": "Authorized", "impact_level": "High" }

# Monitor fires:
event:
  type: accreditation.verified
  urgency: low
  payload:
    accreditation_uuid: acc-fr-high-001
    framework: fedramp_high
    registry: fedramp_marketplace
    checked_at: 2026-03-31T09:00:00Z

# DCM updates: last_verified_at, last_result: confirmed_active
# Scoring Model Signal 5: weight 40 × multiplier 1.0 = 40 (full weight)
```

**Day 47: FedRAMP PMO revokes the authorization mid-cycle**

```yaml
# Monitor polls: GET /api/products?id=FR2025-0088
# Response: { "status": "Revoked", "revocation_date": "2026-05-17" }

# status = Revoked → immediate revocation (no admin confirmation required — ACM-002)
event:
  type: accreditation.status_changed
  urgency: critical
  payload:
    accreditation_uuid: acc-fr-high-001
    from_status: authorized
    to_status: revoked
    external_source: fedramp_marketplace
    action_taken: immediate_revocation

# DCM immediately:
# 1. Sets accreditation status → revoked
# 2. Fires Accreditation Gap for pvd-vm-fed-001
# 3. All active requests targeting pvd-vm-fed-001 with sovereign/fedramp data → SUSPENDED
# 4. Platform Admin + Compliance Team paged (urgency: critical, non-suppressable)
# 5. Recovery Policy: NOTIFY_AND_WAIT (sovereign profile default)

accreditation_gap_record:
  provider_uuid: pvd-vm-fed-001
  required_framework: fedramp_high
  gap_type: revoked
  severity: critical
  affected_entity_uuids: [ent-vm-fed-01, ent-vm-fed-02, ent-vm-fed-07]
  policy_response: NOTIFY_AND_WAIT
```

---

## 1.12 Session Revocation — Security Event Response

A developer's laptop is reported stolen at 14:30. The security team needs to immediately terminate all active DCM sessions for that actor.

**Step 1: Security team triggers emergency revocation**

```
POST /api/v1/admin/actors/act-alice-001/sessions:revoke-all
Authorization: Bearer <security-admin-token>

{
  "revocation_reason": "SECURITY_EVENT",
  "detail": "Laptop reported stolen — device UUID: dev-alice-macbook-001",
  "audit_reference": "INC-2026-0847"
}
```

**Step 2: DCM processes emergency revocation**

```yaml
# All active sessions for act-alice-001 identified: [sess-alice-001, sess-alice-002]
# Session tokens added to Revocation Registry immediately
# (Zero-latency: registry checked on every API call inbound)

revocation_registry_entries:
  - token_jti: jwt-alice-sess-001
    revoked_at: 2026-03-31T14:30:07Z
    reason: SECURITY_EVENT
    actor_uuid: act-alice-001

  - token_jti: jwt-alice-sess-002
    revoked_at: 2026-03-31T14:30:07Z
    reason: SECURITY_EVENT
    actor_uuid: act-alice-001

event:
  type: security.session_revoked
  urgency: critical
  payload:
    actor_uuid: act-alice-001
    sessions_revoked: 2
    reason: SECURITY_EVENT
    incident_ref: INC-2026-0847
```

**Step 3: In-flight request intercepted**

```yaml
# Alice had just submitted a request at 14:30:05 — 2 seconds before revocation
# Request was in POLICY_EVALUATION stage
# Orchestrator checks Revocation Registry before dispatch:

check_result: token jwt-alice-sess-001 in revocation registry
action: ABORT_REQUEST
request_status: CANCELLED
reason: "Actor session revoked during request processing"
# Resource NOT provisioned — safe state
```

**Step 4: Next login attempt fails cleanly**

```
GET /api/v1/resources
Authorization: Bearer jwt-alice-sess-001

→ 401 Unauthorized
{
  "error": "TOKEN_REVOKED",
  "message": "Session has been administratively revoked. Contact your platform admin."
}
```

---

# Section 2 — Provider Interaction Examples

## 2.5 Auth Provider — FreeIPA Integration

**Registration:**

```yaml
auth_provider_registration:
  artifact_metadata:
    uuid: pvd-ipa-001
    handle: providers/auth/corporate-freeipa
    version: "1.0.0"
    status: active
    owned_by: { display_name: Platform Team }

  name: Corporate FreeIPA
  description: Primary enterprise directory — FreeIPA with Kerberos

  capabilities:
    authentication: true
    mfa: false                       # Kerberos SSO, MFA handled by RHSSO layer
    group_membership: true
    role_mapping: true

  protocol: ldap
  endpoint: ldaps://ipa.corp.example:636
  bind_credential_uuid: crd-ipa-bind-001   # stored in credential management service

  group_mapping:
    # FreeIPA groups → DCM roles
    - ipa_group: dcm-platform-admins
      dcm_role: platform_admin
    - ipa_group: dcm-tenant-payments
      dcm_role: tenant_member
      tenant_uuid: ten-pay-001
    - ipa_group: dcm-tenant-web
      dcm_role: tenant_member
      tenant_uuid: ten-web-001

  health_check:
    endpoint: /health
    method: ldap_bind_check
```

**Authentication flow:**

```
1. alice@corp.example submits credentials to DCM Consumer API
2. DCM forwards to pvd-ipa-001: LDAP bind as alice@corp.example
3. FreeIPA validates credentials → success
4. DCM queries: memberOf → [dcm-tenant-payments, dcm-team-api-devs]
5. Group mapping applied → alice gets: tenant_member(ten-pay-001)
6. DCM issues session token (JWT) with actor_uuid + group claims
7. Session written to Session Store
```

---

## 2.6 data store — Ceph Realized State Snapshots

**Registration:**

```yaml
(prescribed infrastructure)_registration:
  uuid: pvd-cph-001
  name: ceph-prod
  display_name: Ceph — Realized State realized data domain
  store_type: write_once_snapshot
  version: "1.0.0"
  endpoint: https://ceph-rgw.corp.example:7480

  capabilities:
    write: true
    read: true
    delete: false            # write_once_snapshot — immutable
    content_addressed: true  # SHA-256 keyed
    encryption_at_rest: true
    replication_factor: 3

  bucket: dcm-realized-state
  auth_credential_uuid: crd-ceph-s3-001
```

**DCM writes a Realized State snapshot:**

```yaml
# After provider confirms VM provisioning:
# DCM stores the full realized_state_record as a content-addressed object

storage_write_request:
  store_type: write_once_snapshot
  key: realized-state/ent-vm-pay-03/rlz-pay-api-03-v1
  content_hash: sha256:a1b2c3d4...
  payload: <full realized_state_record YAML>

# Ceph stores it; returns: { "stored": true, "etag": "sha256:a1b2c3d4..." }
# DCM records: realized_state_uuid → storage key mapping
```

---

## 2.7 event routing service — RabbitMQ Event Routing

**Registration:**

```yaml
(optional infrastructure)_registration:
  uuid: pvd-rmq-001
  name: rabbitmq-prod
  display_name: RabbitMQ — DCM Event Bus
  version: "1.0.0"
  endpoint: amqps://rabbitmq.corp.example:5671
  auth_credential_uuid: crd-rmq-001

  capabilities:
    publish: true
    subscribe: true
    durable_queues: true
    dead_letter: true

  exchange_config:
    name: dcm.events
    type: topic
    durable: true

  routing_key_pattern: "{domain}.{event_type}.{urgency}"
  # Examples:
  #   request.completed.low
  #   provider.health_changed.high
  #   accreditation.status_changed.critical
```

**Event flows through the bus:**

```yaml
# 1. DCM publishes event (internal → bus)
publish:
  exchange: dcm.events
  routing_key: accreditation.status_changed.critical
  payload:
    event_type: accreditation.status_changed
    urgency: critical
    accreditation_uuid: acc-fr-high-001
    from_status: authorized
    to_status: revoked

# 2. notification service subscribes and routes to appropriate channels
subscribe:
  queue: dcm.notifications.critical
  binding: "#.critical"            # all critical urgency events
  handler: service_provider    # notification service consumes and routes

# 3. ITSM integration subscribes to provider events
subscribe:
  queue: dcm.itsm.provider-events
  binding: "provider.#"            # all provider domain events
  handler: itsm_provider            # creates ServiceNow incident
```

---

## 2.8 credential management service — Vault Secret Fetch at Dispatch Time

**Registration:**

```yaml
service_provider_registration:
  uuid: pvd-vlt-001
  name: vault-prod
  display_name: HashiCorp Vault — credential management service
  version: "1.0.0"
  endpoint: https://vault.corp.example:8200

  capabilities:
    fetch_secret: true
    rotate_credential: true
    dynamic_secret: true           # Vault dynamic credentials
    ttl_management: true

  auth_method: approle
  approle_role_id: dcm-control-plane
  approle_secret_uuid: crd-vault-approle-001   # bootstrap credential

  secret_engines:
    - path: secret/dcm/            # KV v2 for static credentials
    - path: database/              # dynamic DB credentials
    - path: pki/                   # certificate issuance
```

**Fetch flow at dispatch time:**

```yaml
# Request Payload Processor needs the FreeIPA bind password for the auth provider:

credential_fetch_request:
  credential_uuid: crd-ipa-bind-001
  requesting_component: request_payload_processor
  purpose: auth_provider_bind

# DCM calls credential management service:
# GET vault.corp.example:8200/v1/secret/data/dcm/providers/auth/freeipa-bind
# Vault authenticates DCM via AppRole, returns:
# { "data": { "password": "s3cr3t-b1nd-p4ss" } }

# Credential returned to Payload Processor — never written to any store
# Used ephemerally for the LDAP bind → discarded after use

# For dynamic DB credentials (short-lived):
dynamic_credential_fetch:
  credential_uuid: crd-db-dynamic-001
  vault_path: database/creds/payments-db-role
  ttl: PT1H                        # expires after 1 hour
  # Vault creates a temp DB user, returns: { "username": "v-dcm-pay-1a2b", "password": "..." }
```

**Consumer retrieves a resource credential:**

```
GET /api/v1/resources/ent-vm-pay-03/credentials

Response:
[
  {
    "credential_uuid": "crd-vm-pay-03-ssh",
    "type": "ssh_key",
    "display_name": "SSH Access Key",
    "fetch_url": "/api/v1/credentials/crd-vm-pay-03-ssh/value"
  }
]

GET /api/v1/credentials/crd-vm-pay-03-ssh/value
Authorization: Bearer <alice-session-token>

Response:
{
  "type": "ssh_key",
  "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...",
  "username": "cloud-user",
  "expires_at": "2026-04-30T00:00:00Z"
}
# Audit record written: act-alice-001 fetched crd-vm-pay-03-ssh at 2026-03-31T10:00:00Z
```

---

## 2.9 composite service definition — Compound WebApp Provisioning

`webapp-meta` is a composite service definition that composes a VM + IP + Firewall Rule + DNS Record into a single `ApplicationStack.WebApp` catalog item. The consumer requests one thing; DCM provisions four.

**Compound service definition (registered by composite service definition):**

```yaml
composite service_registration:
  uuid: pvd-wam-001
  name: webapp-meta
  display_name: Web Application Stack (composite service definition)

  resource_types_composed:
    - fqn: ApplicationStack.WebApp
      version: "2.0.0"
      constituents:
        - component_id: vm
          resource_type: Compute.VirtualMachine
          provided_by: external       # DCM places with appropriate compute provider
          required_for_delivery: required

        - component_id: ip
          resource_type: Network.IPAddress
          provided_by: external
          required_for_delivery: required
          depends_on: []              # IP can provision in parallel with VM

        - component_id: fw
          resource_type: Security.FirewallRule
          provided_by: external
          required_for_delivery: optional
          depends_on: [vm, ip]        # needs both IPs before rule can be written
          inject_from:
            vm: { source_ip: "$.realized.assigned_ip" }
            ip: { dest_ip: "$.realized.ip_address" }

        - component_id: dns
          resource_type: Network.DNSRecord
          provided_by: external
          required_for_delivery: optional
          depends_on: [ip]
          inject_from:
            ip: { a_record_value: "$.realized.ip_address" }
```

**Consumer request (one item, four resources provisioned):**

```
POST /api/v1/requests
{
  "catalog_item_uuid": "cat-webapp-standard",
  "fields": {
    "app_name": "payments-portal",
    "cpu_cores": 4,
    "ram_gb": 16,
    "dns_hostname": "payments.corp.example",
    "firewall_source": "0.0.0.0/0",
    "firewall_dest_port": 443
  }
}

# Composite entity created: ent-app-portal-001 (ApplicationStack.WebApp)
# DCM decomposes into 4 constituent requests:
#   ent-vm-portal  → pvd-vm-001    (PROVISIONING)
#   ent-ip-portal  → pvd-net-001   (PROVISIONING, parallel)
#   ent-fw-portal  → pvd-fw-001    (PENDING_DEPENDENCY on vm + ip)
#   ent-dns-portal → pvd-dns-001   (PENDING_DEPENDENCY on ip)

# Composite entity is OPERATIONAL when all required_for_delivery constituents are OPERATIONAL
# Status visible as one entity to the consumer
```

---

## 2.10 ITSM integration — ServiceNow Incident on Provider Health Change

**Setup:** `servicenow-prod` is registered and configured to create incidents on provider health events.

```yaml
itsm_provider_registration:
  provider_handle: servicenow-prod
  itsm_system: servicenow
  endpoint_url: https://corp.service-now.com
  api_version: v2
  auth_credential_uuid: crd-sn-api-001

  supported_actions:
    - create_incident
    - update_incident
    - resolve_incident
    - create_change_request

  field_mappings:
    # DCM event fields → ServiceNow fields
    incident:
      short_description: "$.event.payload.detail"
      urgency:
        critical: 1     # ServiceNow urgency: 1=High
        high: 2
        medium: 3
        low: 4
      assignment_group: "DCM Platform Operations"
      category: "Infrastructure"
      subcategory: "Cloud Management"
      cmdb_ci: "$.event.payload.provider_uuid"
```

**Event fires: provider goes unhealthy**

```yaml
# pvd-vm-001 health check fails 3 consecutive times
event:
  type: provider.health_changed
  urgency: high
  payload:
    provider_uuid: pvd-vm-001
    from_state: healthy
    to_state: unhealthy
    failure_count: 3
    detail: "Health endpoint unreachable: connection timeout"

# ITSM integration receives via Message Bus
# Creates ServiceNow incident:

servicenow_api_call:
  method: POST
  path: /api/now/table/incident
  body:
    short_description: "DCM Provider Unhealthy: pvd-vm-001 — connection timeout"
    urgency: 2                        # high → ServiceNow urgency 2
    assignment_group: DCM Platform Operations
    category: Infrastructure
    subcategory: Cloud Management
    cmdb_ci: pvd-vm-001
    description: |
      DCM Provider pvd-vm-001 (VMware Prod) has failed 3 consecutive health checks.
      Last error: connection timeout
      Affected resource types: Compute.VirtualMachine
      Routing: capacity reduced, new requests redirected to pvd-vm-002

# ServiceNow responds: { "sys_id": "INC0087432" }
# DCM stores: provider pvd-vm-001 → itsm_reference: INC0087432

# When provider recovers:
servicenow_api_call:
  method: PATCH
  path: /api/now/table/incident/INC0087432
  body:
    state: 6                          # ServiceNow: resolved
    close_notes: "DCM Provider pvd-vm-001 returned to healthy state"
    resolved_at: 2026-03-31T16:45:00Z
```

---

# Section 3 — Registration Flow Examples

## 3.1 Information Provider Onboarding — NetBox as Network IP Provider

```yaml
# Step 1: Platform admin issues registration token
POST /api/v1/admin/registration-tokens
{
  "provider_type": "information_provider",
  "handle_pattern": "providers/information/network/*",
  "valid_for": "PT24H"
}
Response: { "token": "reg-tok-netbox-001", "expires_at": "2026-04-01T09:00:00Z" }

# Step 2: NetBox provider submits registration
POST /api/v1/admin/providers/register
Authorization: Bearer reg-tok-netbox-001
X-Client-Cert: <mTLS cert — corp CA signed>

{
  "provider_type": "information_provider",
  "name": "NetBox — Network IP Registry",
  "handle": "providers/information/network/netbox-prod",
  "version": "1.0.0",
  "endpoint": "https://netbox.corp.example",
  "implements": [
    {
      "information_type_name": "Network.IPAddress",
      "information_type_version": "1.2.0",
      "lookup_methods_supported": ["primary_key", "cidr_query"],
      "extended_fields_supported": true,
      "extended_schema": {
        "vrf_id": { "type": "integer" },
        "site_slug": { "type": "string" },
        "role": { "type": "string", "enum": ["loopback", "anycast", "secondary"] }
      }
    }
  ],
  "sovereignty_declaration": {
    "data_residency": ["US"],
    "crosses_jurisdiction": false
  }
}

# Step 3: Validation (6 checks for information_provider)
# V1: information_provider enabled in prod profile ✓
# V2: Governance Matrix pre-check: ALLOW ✓
# V3: Token valid and matches handle pattern ✓
# V4: mTLS certificate valid, corp CA chain ✓
# V5: Sovereignty declaration complete ✓
# V6: Health endpoint reachable ✓

# Step 4: Platform admin approves
POST /api/v1/admin/registrations/reg-netbox-001/approve
{ "rationale": "NetBox is our authoritative IP registry" }

# Step 5: ACTIVE — NetBox now enriches assembly payloads
# When a request for any resource in dc-west-1 is assembled:
#   DCM queries NetBox: "give me next available IP in 10.42.18.0/24"
#   NetBox returns: { "ip": "10.42.18.56", "vrf_id": 4, "site_slug": "dc-west-1" }
#   IP injected into assembled payload
```

---

## 3.2 Auth Provider Onboarding — Adding a Secondary OIDC Provider

```yaml
# Scenario: Adding Azure AD as a secondary auth source for contractors
POST /api/v1/admin/providers/register
Authorization: Bearer reg-tok-oidc-001
X-Client-Cert: <mTLS cert>

{
  "provider_type": "auth_provider",
  "name": "Azure AD — Contractor Identity",
  "handle": "providers/auth/azure-ad-contractors",
  "version": "1.0.0",

  "capabilities": {
    "authentication": true,
    "mfa": true,
    "group_membership": true,
    "role_mapping": true
  },

  "protocol": "oidc",
  "oidc_config": {
    "issuer": "https://login.microsoftonline.com/{tenant-id}/v2.0",
    "client_id": "dcm-azure-ad-client",
    "client_secret_uuid": "crd-azure-oidc-secret",
    "scopes": ["openid", "profile", "email", "groups"],
    "group_claim": "groups"
  },

  "group_mapping": [
    {
      "oidc_group_id": "aad-grp-dcm-contractors",
      "dcm_role": "tenant_member",
      "tenant_uuid": "ten-web-001",
      "scope_restriction": {
        "allowed_resource_types": ["Compute.VirtualMachine"],
        "max_ttl": "P7D"             # contractor VMs expire after 7 days
      }
    }
  ],

  "precedence": 2                    # lower than FreeIPA (precedence 1)
                                     # FreeIPA checked first; Azure AD is fallback
}
```

---

## 3.3 composite service definition Onboarding

```yaml
POST /api/v1/admin/providers/register
Authorization: Bearer reg-tok-meta-001

{
  "provider_type": "composite service",
  "name": "Web Application Stack",
  "handle": "providers/meta/webapp-stack",
  "version": "2.0.0",

  "resource_types_composed": [
    {
      "fqn": "ApplicationStack.WebApp",
      "version": "2.0.0",
      "catalog_item_template_uuid": "cat-tmpl-webapp-001",
      "constituents": [
        {
          "component_id": "vm",
          "resource_type": "Compute.VirtualMachine",
          "provided_by": "external",
          "required_for_delivery": "required"
        },
        {
          "component_id": "ip",
          "resource_type": "Network.IPAddress",
          "provided_by": "external",
          "required_for_delivery": "required",
          "depends_on": []
        },
        {
          "component_id": "fw",
          "resource_type": "Security.FirewallRule",
          "provided_by": "external",
          "required_for_delivery": "optional",
          "depends_on": ["vm", "ip"]
        }
      ]
    }
  ],

  "decomposition_policy_handle": "system/meta/webapp-decompose-v2"
}

# Validation:
# V1: composite service enabled in profile ✓
# V2: All constituent resource_types registered in Registry ✓
# V3: No circular dependencies in constituent graph ✓
# V4: Decomposition policy handle resolvable ✓

# Once ACTIVE: "ApplicationStack.WebApp" appears in service catalog
# Consumers request one item; DCM provisions all constituents automatically
```

---

# Section 4 — OPA Policy Integration Examples

## 4.1 OPA Policy Bundle Delivery and Shadow Mode

**Scenario: New PCI DSS policy deployed in shadow mode before enforcement**

```yaml
# Policy author submits new policy artifact
POST /api/v1/admin/policies/submit

{
  "handle": "compliance/pci/card-data-network-isolation",
  "version": "1.0.0",
  "type": "gating",
  "enforcement_class": "hard_stop",
  "status": "proposed",           # starts in shadow mode
  "opa_bundle_ref": "git://policies/compliance/pci/card-data-isolation@v1.0.0",
  "applies_to": {
    "resource_types": ["Compute.VirtualMachine", "Network.VLAN"]
  },
  "description": "Card data VMs must be on isolated network segments — not shared with non-PCI workloads"
}
```

**Shadow mode evaluation (next 30 days):**

```yaml
# Policy evaluates against every matching request but does NOT block
# Results logged as shadow_divergence events

shadow_divergence_event:
  policy_handle: compliance/pci/card-data-network-isolation@1.0.0
  request_uuid: req-vm-web-07
  tenant_uuid: ten-web-001
  actor_uuid: act-alice-001
  shadow_result: WOULD_BLOCK
  reason: "VM requested on shared VLAN 100 — card data isolation requires dedicated VLAN ≥200"
  # Real decision: ALLOW (shadow mode — not enforced yet)

# Platform admin reviews shadow dashboard after 2 weeks:
GET /api/v1/admin/policies/compliance/pci/card-data-network-isolation/shadow-report

{
  "evaluation_period": "2026-03-01 to 2026-03-15",
  "total_evaluations": 847,
  "would_block_count": 12,
  "would_block_pct": 1.4,
  "top_blocking_reasons": [
    { "reason": "VLAN < 200", "count": 9 },
    { "reason": "mixed tenant segment", "count": 3 }
  ],
  "recommendation": "Safe to activate — 12 impacted requests in 2 weeks, all addressable"
}

# Admin activates:
PATCH /api/v1/admin/policies/compliance/pci/card-data-network-isolation
{ "status": "active" }
# Policy now enforced — all future matching requests checked for real
```

---

## 4.2 OPA Bundle Delivery to External Policy Evaluator

```yaml
# OPA sidecar (External Policy Evaluator) registered:
external_policy_evaluation_registration:
  uuid: pvd-opa-001
  name: opa-compliance-sidecar
  mode: sidecar                    # co-deployed with DCM control plane
  bundle_sources:
    - handle: compliance/pci/*
      git_ref: git://policies/pci@main
      pull_interval: PT5M          # pull fresh bundle every 5 minutes
    - handle: compliance/hipaa/*
      git_ref: git://policies/hipaa@main
      pull_interval: PT5M

# Bundle pull cycle:
# 1. OPA sidecar polls git repo every 5 minutes
# 2. New bundle detected (policy updated by compliance team via GitOps PR)
# 3. OPA loads new bundle — hot reload, no downtime
# 4. DCM notified: external_policy_evaluation.bundle_updated event

# Policy evaluation call (from Request Orchestrator to OPA sidecar):
POST /v1/data/dcm/policies/evaluate
{
  "input": {
    "request": {
      "resource_type": "Compute.VirtualMachine",
      "tenant_uuid": "ten-pay-001",
      "payload": { "network_segment": "dmz-payments", "vlan": 142 }
    },
    "actor": { "uuid": "act-alice-001", "roles": ["tenant_member"] },
    "provider": { "uuid": "pvd-vm-001", "accreditations": ["pci_dss", "iso_27001"] }
  }
}

Response:
{
  "result": {
    "allow": true,
    "policies_evaluated": 14,
    "transformations": [
      { "field": "cpu_pinning", "value": true, "reason": "PCI isolation" }
    ],
    "gatings_fired": 0
  }
}
```

---

# Section 5 — Admin and Consumer GUI Examples

## 5.1 Consumer Portal — New Resource Request Flow

```
Step 1: Consumer logs in
  → Redirected to FreeIPA SSO via OIDC
  → Returns with session token (alice, payments-bu, tenant_member)

Step 2: Service Catalog presented
  → DCM filters by: alice's roles + payments-bu tenant + prod profile
  → Shows: [Compute.VirtualMachine, Network.IPAddress, ApplicationStack.WebApp, ...]
  → Cost estimate shown per catalog item (from Cost Analysis component)

Step 3: Alice selects "Compute.VirtualMachine — Standard"
  → Form generated from catalog item field_schema
  → Pre-fill hints from previous requests (last used zone, OS)

Step 4: Pre-request cost estimate
  POST /api/v1/cost/estimate
  { "catalog_item_uuid": "cat-vm-standard", "fields": { "cpu_cores": 8, "ram_gb": 32 } }
  → { "monthly_estimate": "$142.40", "one_time": "$0", "currency": "USD" }

Step 5: Alice submits request
  → Operation returned: { "name": "/api/v1/operations/req-pay-api-03", "done": false }
  → Portal polls operation.name every 2 seconds
  → Progress bar: INITIATED → POLICY_EVALUATION → DISPATCHED → PROVISIONING → OPERATIONAL

Step 6: Resource is OPERATIONAL
  → Portal shows: IP address, SSH key download link, hostname
  → Toast notification: "payments-api-03 is ready"
```

---

## 5.2 Admin GUI — Policy Flow Visualization

The Flow GUI shows the policy evaluation pipeline for a given request as an interactive diagram.

```
Admin selects: Request req-pay-api-03
Flow GUI renders:

[ Consumer Input ]
       │
       ▼
[ Layer Assembly ]
  ├── Base Layer (3.1.0) ✓
  ├── DC West-1 Layer (2.0.0) ✓
  ├── DMZ Zone Layer (1.5.0) ✓
  ├── Payments BU Layer (1.2.0) ✓
  └── Request Layer ✓
       │
       ▼
[ Policy Evaluation — 14 policies ]
  ├── Gating Policy: pci-network-isolation ✓ PASS
  ├── Gating Policy: phi-provider-accreditation ✓ PASS (no PHI in request)
  ├── Validation: vm-size-limits ✓ PASS
  ├── Transformation: pci-cpu-pinning → cpu_pinning: true APPLIED
  └── Transformation: approved-os-image → rhel-9-latest-approved APPLIED
       │
       ▼
[ Placement Engine ]
  ├── Candidates: [pvd-vm-001 (score:65), pvd-vm-002 (score:36)]
  └── Selected: pvd-vm-001 (highest accreditation richness)
       │
       ▼
[ Dispatch → pvd-vm-001 ]
  └── Status: OPERATIONAL ✓

# Clicking any node shows full input/output payload for that step
# Shadow mode indicator (S) shown on any policy evaluated in shadow
# Red path shown for any Gating Policy that fired and blocked
```

---

## 5.3 Admin GUI — Drift Dashboard

```
Admin opens Drift Dashboard:

Summary:
  Open drift records: 7
  ├── Critical: 1  (security config drift — out-of-hours change)
  ├── High: 3      (resource sizing drift — manual changes)
  └── Medium: 3    (metadata drift — tags removed)

Critical drift: ent-vm-pay-03
  Discovered: selinux: permissive
  Realized:   selinux: enforcing
  Changed at: 2026-03-30T03:15:00Z (2:00 AM — suspicious)
  Provider:   pvd-vm-001
  Policy response: NOTIFY_AND_WAIT → Compliance Team paged

Admin actions available:
  [Revert to Realized State]  → dispatches remediation to pvd-vm-001
  [Accept Discovered State]   → updates Realized State record (requires reason)
  [Investigate]               → opens audit trail for this entity since last drift-clean
```

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
