# DCM End-to-End Walkthrough — VM Provision

**Purpose:** Trace a single request through the entire DCM pipeline with real data structures at every stage. This is the single document to read if you want to understand how DCM works in practice.

**Time to read:** ~20 minutes  
**Prerequisites:** None — this document is self-contained.

---

## The Scenario

A developer on the AppTeam tenant requests a standard Linux VM for a payments API server. The request must comply with EU data residency requirements. The VM requires an IP address — DCM automatically resolves this dependency by requesting an IP from the appropriate IPAM provider, governed by core sovereignty policies and service-specific subnet policies. We follow this request from the consumer's API call through to a running VM and its first discovery cycle.

---

## Stage 1: Consumer Submits Intent

The developer calls the Consumer API:

```
POST /api/v1/requests
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "catalog_item_uuid": "compute-vm-standard-uuid",
  "fields": {
    "cpu_count": 4,
    "memory_gb": 8,
    "storage_gb": 100,
    "os_family": "rhel",
    "environment": "production",
    "name": "payments-api-server-01"
  }
}
```

**What the consumer declares:** What they need. Not where it runs, not which provider, not which datacenter. Just the desired outcome.

**What DCM creates — Intent State:**

```yaml
entity_uuid: f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0
resource_type: Compute.VirtualMachine
tenant_uuid: a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6   # AppTeam
submitted_by: b2c3d4e5-actor-uuid
submitted_at: 2026-03-15T09:00:00Z

fields:
  cpu_count: 4
  memory_gb: 8
  storage_gb: 100
  os_family: rhel
  environment: production
  name: "payments-api-server-01"
```

**What happens immediately:**
- Authorization check: actor has `request:compute:vm` permission in AppTeam tenant
- Sovereignty check: AppTeam's tenant has `data_residency: EU-WEST` — this will constrain placement later
- The `entity_uuid` is assigned now and will never change — it links every stage of this request's lifecycle

**Audit leaf written:** `INTENT_CAPTURED` — SHA-256 hash of the intent payload, signed by the API gateway service.

> **Key concept:** The consumer never chooses a provider or a datacenter. The control plane handles that.

---

## Stage 2: Layer Assembly

The Request Processor assembles the full payload by merging data layers in precedence order. Layers are organizational data — datacenter configs, environment defaults, tenant overrides, compliance requirements.

**Layer chain resolved (highest to lowest precedence):**

```
1. system/core/datacenter-layer.yaml        → data_center: "EU-WEST-DC1"
2. system/core/environment-layer.yaml        → monitoring defaults, log retention
3. system/compliance/eu-west-layer.yaml      → backup_policy: "daily-30d-eu-west"
4. org/appteam-defaults-layer.yaml           → monitoring_agent: "datadog-agent:7.42"
5. providers/openstack/vm-defaults-layer.yaml → provider-specific defaults
6. Consumer intent                            → cpu_count: 4, memory_gb: 8, ...
```

**Resulting merged payload (selected fields with provenance):**

```yaml
cpu_count:
  value: 4
  provenance: { source_type: consumer, source_uuid: f5e6d7c8-entity }

memory_gb:
  value: 8
  provenance: { source_type: consumer }

data_center:
  value: "EU-WEST-DC1"
  provenance: { source_type: base_layer, source_uuid: dc-layer-uuid }

environment:
  value: production
  provenance:
    origin: { source_type: intermediate_layer, value: dev }
    modifications:
      - previous: dev → modified: production, source_type: consumer  # consumer override

monitoring_agent:
  value: "datadog-agent:7.42"
  provenance: { source_type: intermediate_layer, source_uuid: appteam-defaults-uuid }

backup_policy:
  value: "daily-30d-eu-west"
  provenance: { source_type: intermediate_layer, source_uuid: eu-west-compliance-uuid }
```

**Key concept:** The consumer declared 6 fields. After assembly, there are 10+ fields. The extra fields come from layers — organizational data that the consumer doesn't need to know about but that provisioning requires.

**Key concept:** Every field carries provenance — where the value came from and what modified it. This is how auditors trace any value back to its origin.

**Audit leaf written:** `ASSEMBLY_COMPLETE` — hash of the assembled payload with layer chain reference.

---

## Stage 3: Policy Evaluation

The Policy Engine evaluates all matching policies against the assembled payload. Evaluation follows a three-phase model:

### Phase 1: Validation Policy (compliance check, pass/fail, no mutations)

```
Policy: vm-size-limits (Validation Policy, compliance-class)
  Match: resource_type = Compute.VirtualMachine, lifecycle_scope = initial_provisioning
  Result: APPROVED — 4 CPU within AppTeam's 16 CPU quota

Policy: approved-os-images (Validation Policy, tenant-scoped)
  Match: resource_type = Compute.VirtualMachine, tenant_uuid = AppTeam
  Result: APPROVED — rhel is in AppTeam's approved images list

Policy: eu-data-residency (Validation Policy, compliance-class, hard enforcement)
  Match: data_residency = EU-WEST
  Result: APPROVED — data_center value "EU-WEST-DC1" is within EU-WEST zone
```

### Phase 2: Transformation (mutations applied)

```
Policy: inject-monitoring-endpoint (Transformation)
  Match: environment = production, has monitoring_agent
  Action: INJECT field monitoring_endpoint
  Result:
    monitoring_endpoint:
      value: "https://metrics.internal.eu-west.example.com"
      provenance: { source_type: policy, source_uuid: inject-monitoring-policy-uuid,
                     reason: "Standard endpoint for EU-WEST production resources" }
```

The transformation pass runs again to check for convergence. No new mutations — converged in 1 pass.

### Phase 3: Post-mutation Validation Policy

```
Policy: vm-size-limits — re-evaluated after transformations
  Result: APPROVED (no relevant mutations occurred)
```

**All policies pass. Request proceeds to placement.**

**Audit leaves written:** One per policy evaluation with result, constraint emissions, and hash of the payload at evaluation time.

> **What if a policy blocked?** The request would enter `POLICY_BLOCKED` state and the consumer would receive resolution guidance — compliant values, override options, cancel, or escalate. See ADR-009.

---

## Stage 4: Dependency Resolution

Before placement can proceed, DCM checks the Resource Type Specification for `Compute.VirtualMachine` and finds a **type-level dependency**:

```yaml
# From the Resource Type Specification for Compute.VirtualMachine
resource_type: Compute.VirtualMachine
type_level_dependencies:
  - required_resource_type: Network.IPAddress
    dependency_type: hard
    cardinality: one_to_one
    description: "Every VM requires exactly one IP address"
    payload_fields:             # fields to inject from the realized IP into the VM payload
      - source: "address"
        target: "assigned_ip_address"
      - source: "subnet"
        target: "network_subnet"
      - source: "gateway"
        target: "network_gateway"
```

The VM cannot be dispatched until this dependency is satisfied. DCM creates a **sub-request** for the IP address — the consumer never sees this; it's an internal orchestration step driven by the resource type definition.

**IP Address sub-request created:**

```yaml
entity_uuid: aabb1122-ip-uuid
resource_type: Network.IPAddress
tenant_uuid: a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6   # same tenant as parent VM
parent_entity_uuid: f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0  # linked to the VM

fields:
  address_family: IPv4
  purpose: vm_interface
  environment: production
  attachment_ref: f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0   # the VM this IP is for
```

> **Key concept:** The consumer requested a VM. DCM knows a VM requires an IP address because the resource type spec declares it. The consumer doesn't manage IP allocation — DCM does.

**Audit leaf written:** `DEPENDENCY_CREATED` — hash of IP sub-request + parent VM entity_uuid.

---

## Stage 5: IP Address — Policy Evaluation and Provider Selection

The IP sub-request goes through its own policy evaluation pipeline — the same three-phase model as the parent VM, but with policies scoped to `Network.IPAddress`.

### Core Policies (system-scoped, apply to all IP allocations)

```
Policy: ip-sovereignty-zone (Validation Policy, compliance-class, hard enforcement)
  Match: resource_type = Network.IPAddress, data_residency = EU-WEST
  Check: IP pool must be in EU-WEST sovereignty zone
  Result: APPROVED — only EU-WEST pools will be considered

Policy: ip-subnet-isolation (Validation Policy, system-scoped)
  Match: resource_type = Network.IPAddress, environment = production
  Check: Production IPs must come from production-designated subnets
  Result: APPROVED — filters candidate pools to production subnets only
```

### Service Provider Policies (provider-scoped, specific to IPAM capabilities)

```
Policy: ipam-pool-selection (Transformation, provider-scoped)
  Match: resource_type = Network.IPAddress, purpose = vm_interface
  Action: Enriches request with pool selection criteria
  Result: INJECT pool_selector field
    pool_selector:
      value: { zone: "eu-west", environment: "production", address_family: "IPv4" }
      provenance: { source_type: policy, source_uuid: ipam-pool-selection-uuid,
                     reason: "Production VM interfaces use production pool in matching zone" }

Policy: ip-address-format (Validation, provider-scoped)
  Match: resource_type = Network.IPAddress
  Check: address_family is valid (IPv4 or IPv6), purpose is recognized
  Result: PASSED
```

### Placement selects IP Provider

```
Sovereignty pre-filter:
  Eligible IPAM providers must satisfy data_residency: EU-WEST
  → 2 IPAM providers in EU-WEST zone

Pool capacity query:
  EU-WEST-IPAM-1 (InfoBlox): pool 10.1.0.0/16, 65,420 available → confidence 98%
  EU-WEST-IPAM-2 (NetBox):   pool 10.2.0.0/16, 12,100 available → confidence 91%

Selection: EU-WEST-IPAM-1 (highest confidence, largest available pool)
```

**Audit leaves written:** One per IP policy evaluation + `IP_PLACEMENT_COMPLETE`.

---

## Stage 6: IP Address Realization

The IP provider (InfoBlox IPAM) receives the sub-request, naturalizes it to its native API, and allocates an address:

```
DCM sub-request → InfoBlox API call:

POST /wapi/v2.12/record:host
{
  "name": "payments-api-server-01.eu-west.internal",
  "ipv4addrs": [{ "ipv4addr": "func:nextavailableip:10.1.0.0/16" }],
  "comment": "DCM entity aabb1122-ip-uuid, tenant AppTeam"
}
```

**IP provider callback:**

```yaml
entity_uuid: aabb1122-ip-uuid
status: OPERATIONAL
provider_entity_id: "record:host/ZG5z:10.1.45.23"

realized_fields:
  address: "10.1.45.23"
  subnet: "10.1.0.0/16"
  gateway: "10.1.0.1"
  dns_name: "payments-api-server-01.eu-west.internal"
  lease_type: static
  pool_ref: "10.1.0.0/16"
```

> **Key concept:** The IP address is now a first-class DCM entity. It has its own entity_uuid, its own realized state, its own audit trail. When the VM is decommissioned, DCM knows to release this IP back to the pool.

**Audit leaf written:** `IP_REALIZED` — hash of realized IP state + IPAM provider signature.

---

## Stage 7: Dependency Injection and VM Placement

Now the IP dependency is satisfied. DCM injects the realized IP data into the VM's payload via **dependency payload passing**:

```yaml
# VM payload enriched with dependency data
fields:
  cpu_count: { value: 4, provenance: {...} }
  memory_gb: { value: 8, provenance: {...} }
  storage_gb: { value: 100, provenance: {...} }
  # ... all previously assembled fields ...

  # Injected from realized IP address dependency
  assigned_ip_address:
    value: "10.1.45.23"
    provenance:
      source_type: dependency_payload
      source_uuid: aabb1122-ip-uuid        # the IP entity
      dependency_type: Network.IPAddress
      timestamp: 2026-03-15T09:01:15Z
  network_subnet:
    value: "10.1.0.0/16"
    provenance: { source_type: dependency_payload, source_uuid: aabb1122-ip-uuid }
  network_gateway:
    value: "10.1.0.1"
    provenance: { source_type: dependency_payload, source_uuid: aabb1122-ip-uuid }

dependencies_satisfied:
  - dependency_type: Network.IPAddress
    entity_uuid: aabb1122-ip-uuid
    status: SATISFIED
    satisfied_at: 2026-03-15T09:01:15Z
```

The Placement Engine now scores VM providers (same as before, but the payload now includes the IP):

```
Sovereignty pre-filter:
  Eligible VM providers must satisfy data_residency: EU-WEST
  → 3 OpenStack instances in EU-WEST zone

Reserve query results:
  EU-WEST-Prod-1: capacity available, confidence 94%
  EU-WEST-Prod-2: capacity available, confidence 87%
  EU-WEST-Prod-3: insufficient capacity — excluded

Selection: EU-WEST-Prod-1 (highest confidence score)
```

**Requested State committed (write-once):**

```yaml
entity_uuid: f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0
resource_type: Compute.VirtualMachine
assembled_at: 2026-03-15T09:01:18Z

fields:
  cpu_count: { value: 4, provenance: {...} }
  memory_gb: { value: 8, provenance: {...} }
  storage_gb: { value: 100, provenance: {...} }
  os_family: { value: rhel, provenance: {...} }
  environment: { value: production, provenance: {...} }
  name: { value: "payments-api-server-01", provenance: {...} }
  data_center: { value: "EU-WEST-DC1", provenance: {...} }
  monitoring_agent: { value: "datadog-agent:7.42", provenance: {...} }
  backup_policy: { value: "daily-30d-eu-west", provenance: {...} }
  monitoring_endpoint: { value: "https://metrics...", provenance: {...} }
  assigned_ip_address: { value: "10.1.45.23", provenance: { source_type: dependency_payload } }
  network_subnet: { value: "10.1.0.0/16", provenance: { source_type: dependency_payload } }
  network_gateway: { value: "10.1.0.1", provenance: { source_type: dependency_payload } }

placement:
  selected_provider_uuid: eu-west-prod-1-provider-uuid
  sovereignty_satisfied: true

dependencies:
  - type: Network.IPAddress
    entity_uuid: aabb1122-ip-uuid
    status: SATISFIED
```

**Audit leaf written:** `PLACEMENT_COMPLETE` — hash of requested state + placement decision + dependency references.

> **Key concept:** Requested State is write-once. It now includes both the assembled fields AND the dependency data from the IP allocation. This is the permanent auditable record of exactly what was approved for provisioning.

---

## Stage 8: VM Provider Dispatch (Naturalization)

The Request Orchestrator sends the enriched payload to the selected VM provider. The provider **naturalizes** the DCM unified payload — including the dependency-injected IP address — into its native API format:

```
DCM unified payload → OpenStack Nova API call:

POST /servers
{
  "server": {
    "name": "payments-api-server-01",
    "flavorRef": "m1.xlarge",          ← resolved from cpu_count: 4 + memory_gb: 8
    "imageRef": "rhel-9.3-latest",     ← resolved from os_family: rhel
    "networks": [{
      "uuid": "eu-west-net-uuid",
      "fixed_ip": "10.1.45.23"        ← from dependency: Network.IPAddress
    }],
    "availability_zone": "eu-west-az1",
    "metadata": {
      "dcm_entity_uuid": "f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0",
      "dcm_tenant": "AppTeam",
      "dcm_ip_entity_uuid": "aabb1122-ip-uuid",
      "backup_policy": "daily-30d-eu-west"
    }
  }
}
```

**Key concept:** The VM provider receives the IP address as a known field in the payload — it doesn't call the IPAM system itself. DCM resolved the dependency, allocated the IP through the proper provider with full policy evaluation, and injected the result. The VM provider just uses it.

**Audit leaf written:** `DISPATCH_SENT` — hash of naturalized payload + provider identity.

---

## Stage 9: VM Provider Callback (Denaturalization)

The provider provisions the VM with the pre-allocated IP, then **denaturalizes** the result back into DCM's unified format:

```
POST /api/v1/provider/entities/f5e6d7c8-.../status
Authorization: Bearer <provider-scoped-jwt>

{
  "operation_uuid": "...",
  "status": "OPERATIONAL",
  "provider_entity_id": "vm-0a1b2c3d",
  "realized_fields": {
    "cpu_count": 4,
    "memory_gb": 8,
    "storage_gb": 102,                         ← actual (rounded up)
    "assigned_ip_address": "10.1.45.23",       ← confirmed: matches dependency
    "hypervisor_host": "compute-node-07",      ← provider-assigned
    "console_url": "https://console.eu-west.example.com/vm/0a1b2c3d"
  }
}
```

**Realized State recorded:**

```yaml
entity_uuid: f5e6d7c8-e9f0-a1b2-c3d4-e5f6a7b8c9d0
realized_at: 2026-03-15T09:03:12Z
lifecycle_state: OPERATIONAL

fields:
  cpu_count: 4
  memory_gb: 8
  storage_gb: 102
  assigned_ip_address: "10.1.45.23"
  hypervisor_host: "compute-node-07"
  console_url: "https://console.eu-west..."
  provider_entity_id: "vm-0a1b2c3d"

dependencies:
  - type: Network.IPAddress
    entity_uuid: aabb1122-ip-uuid
    realized_value: "10.1.45.23"
```

**Consumer receives status update via webhook/polling.**

**Audit leaf written:** `REALIZED` — hash of realized state + provider signature.

---

## Stage 10: Discovery Cycle (Drift Detection)

24 hours later, the Discovery service polls the provider:

```yaml
discovered_at: 2026-03-16T09:00:00Z
provider_entity_id: "vm-0a1b2c3d"
status: ACTIVE

cpu_count: 4          # matches Realized — no drift
memory_gb: 8          # matches
storage_gb: 102       # matches
assigned_ip_address: "10.1.45.23"  # matches
```

**Drift comparison: Realized ≡ Discovered. No drift detected.**

Discovery also polls the IP entity independently:

```yaml
discovered_at: 2026-03-16T09:00:05Z
provider_entity_id: "record:host/ZG5z:10.1.45.23"
status: ACTIVE

address: "10.1.45.23"   # matches IP Realized State
lease_type: static       # matches
```

If someone had manually changed the VM's IP outside DCM, the discovered IP on the VM would differ from the dependency record — that's drift on both the VM entity and the IP entity.

> **Key concept:** Both the VM and the IP are independently discoverable DCM entities. Drift detection runs on each. The dependency relationship means drift on the IP triggers review of the VM too.

---

## Stage 11: The Audit Trail

At the end of this lifecycle, the Merkle tree contains these leaves (at mutation granularity). Note how both the VM and the IP dependency have their own complete audit chains:

```
VM Request:
  Leaf 1:  INTENT_CAPTURED        hash(intent_payload) signed by api-gateway
  Leaf 2:  ASSEMBLY_COMPLETE      hash(assembled_payload) signed by request-processor
  Leaf 3:  POLICY_EVAL:vm-size    hash(eval_context + result) signed by policy-engine
  Leaf 4:  POLICY_EVAL:os-images  hash(eval_context + result) signed by policy-engine
  Leaf 5:  POLICY_EVAL:residency  hash(eval_context + result) signed by policy-engine
  Leaf 6:  POLICY_EVAL:monitoring hash(eval_context + mutation) signed by policy-engine

IP Dependency Sub-Request:
  Leaf 7:  DEPENDENCY_CREATED     hash(ip_sub_request + parent_vm_uuid) signed by orchestrator
  Leaf 8:  IP_POLICY:sovereignty  hash(eval_context + result) signed by policy-engine
  Leaf 9:  IP_POLICY:subnet-iso   hash(eval_context + result) signed by policy-engine
  Leaf 10: IP_POLICY:pool-select  hash(eval_context + mutation) signed by policy-engine
  Leaf 11: IP_PLACEMENT_COMPLETE  hash(ip_requested_state + ipam_selection) signed by placement
  Leaf 12: IP_DISPATCH_SENT       hash(naturalized_infoblox_request) signed by orchestrator
  Leaf 13: IP_REALIZED            hash(ip_realized_state) signed by ipam-provider

VM Continues After Dependency Satisfied:
  Leaf 14: DEPENDENCY_SATISFIED   hash(ip_realized_fields + vm_entity_uuid) signed by orchestrator
  Leaf 15: PLACEMENT_COMPLETE     hash(vm_requested_state + placement + deps) signed by placement
  Leaf 16: DISPATCH_SENT          hash(naturalized_nova_payload) signed by orchestrator
  Leaf 17: REALIZED               hash(vm_realized_state) signed by vm-provider
```

Any auditor can:
- **Inclusion proof:** Verify leaf 8 (IP sovereignty check) exists in the tree
- **Consistency proof:** Verify the tree has only grown since the last signed tree head
- **Dependency chain:** Follow leaf 7→13 for the complete IP allocation audit, then leaf 14→17 for the VM
- **Policy provenance:** Trace why the IP came from InfoBlox pool 10.1.0.0/16 (leaves 9-11: subnet isolation + pool selection policies)
- **Non-repudiation:** Every leaf is signed by the service that produced it (Ed25519)

---

## Summary: What Happened in 3 Minutes

| Time | Stage | What happened |
|------|-------|---------------|
| T+0s | 1. Intent | Consumer declared 6 fields via API |
| T+0.5s | 2. Assembly | 5 layers merged in, provenance tracked for all 10+ fields |
| T+1s | 3. Policy (VM) | 4 policies evaluated — all passed. 1 field injected by transformation |
| T+1.1s | 4. Dependencies | VM requires Network.IPAddress — sub-request created automatically |
| T+1.3s | 5. Policy (IP) | 4 IP policies evaluated — sovereignty, subnet isolation, pool selection, format |
| T+1.5s | 6. IP Realized | IPAM provider allocated 10.1.45.23 from EU-WEST production pool |
| T+1.6s | 7. Injection | Realized IP injected into VM payload via dependency payload passing |
| T+2s | 7. Placement (VM) | 3 VM providers scored, 1 selected based on sovereignty + confidence |
| T+3s | 8. Dispatch | Payload naturalized to OpenStack Nova API with pre-allocated IP |
| T+192s | 9. Callback | Provider returned realized state — VM running at 10.1.45.23 |
| T+86400s | 10. Discovery | Both VM and IP confirmed matching realized state — no drift |

**Consumer declared 6 fields. DCM handled everything else:** layer assembly, policy validation, data enrichment, IP allocation through the proper IPAM provider with full sovereignty and subnet policies, provider selection, API translation, state tracking, audit trail (17 Merkle leaves across 2 entities), and drift detection on both the VM and its IP dependency.

---

## Where to Go Next

- **To understand layers:** Doc 03 (Layering and Versioning)
- **To understand policies:** Doc B (Policy Contract) — start with §1-7
- **To understand providers:** Doc A (Provider Contract) — start with §1-5
- **To understand dependencies:** Doc 07 (Service Dependencies) — type-level deps, payload passing, resolution order
- **To understand audit:** Doc 16 (Universal Audit) — start with §1-3, then §8 for Merkle tree
- **To see the three-tier app example:** Doc 04 §8 (composite resource type specification with binding fields)
- **To see the IP allocation example:** Doc 04 §4 (IP Address Allocation with pool model)
- **To see all ADRs:** [Architecture Decision Records](adr/README.md)
