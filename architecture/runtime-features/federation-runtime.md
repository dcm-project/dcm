---
Document Status: ✅ Complete
Document Type: Architecture Reference — Federation Runtime
Maps to: udlm/governance/federated-contribution-model.md
---

# DCM Data Model — DCM Federation, Peering, and Cross-Instance Coordination

> **Implements contracts defined in UDLM**:
> [udlm/governance/federated-contribution-model.md](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md).
> UDLM defines the federated contribution model — how peer DCM instances
> contribute, share, and govern data across instance boundaries, including
> the contribution authority and cross-instance trust contracts. DCM
> operationalizes peer DCMs as typed Providers, the peering and tunnel
> runtime, and the cross-instance coordination of contributed data.


**Document Status:** ✅ Complete  
**Related Documents:** [Federated Contribution Model](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md) | [Universal Group Model](https://github.com/croadfeldt/udlm/blob/main/observability/universal-groups.md) | [data stores](https://github.com/croadfeldt/udlm/blob/main/contracts/storage-providers.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Information Providers Advanced](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers-advanced.md)

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [udlm/foundations/foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: PROVIDER + POLICY**
>
> Provider: Peer DCM as typed Provider. Policy: federation governance rules



---

> **Federated Contribution:** Federation contribution follows the [Federated Contribution Model](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md) — peer DCMs are contributors to each other's artifact stores, scoped by their federation trust posture.

## 1. Purpose

DCM instances do not operate in isolation. Organizations with multiple data centers, regions, or organizational boundaries may run multiple DCM instances that need to coordinate, share resources, and maintain consistent governance. This document defines how DCM instances relate to each other — as peers, in parent-child hierarchies, or as hub-and-spoke configurations — and the mechanisms for cross-instance resource sharing, data export/import, and provider federation eligibility.

---

## 2. DCM-to-DCM Relationship Types

### 2.1 Three Relationship Types

**Peer DCM** — two DCM instances at the same organizational level that share resources or information. Regional DCM instances sharing VLAN allocations. Campus DCM instances sharing compute capacity across departments.

**Parent-Child DCM** — hierarchical relationship where the parent has governance overlay authority over child instances. Corporate DCM with regional children. Service provider DCM with customer children. Parent does not own child resources — it has governance visibility and policy overlay authority (same model as nested Tenants in the Universal Group Model).

**Hub DCM** — specialized Parent DCM acting as a clearinghouse for resource allocation across multiple children. The Hub holds the master resource inventory; children request allocations from the Hub.

### 2.2 Relationship Mapping to Universal Group Model

DCM-to-DCM relationships use the existing Universal Group Model:

```yaml
# Peer relationship — federation group
dcm_group:
  group_class: federation
  name: "EU-US Regional Federation"
  members:
    - member_uuid: <eu-dcm-instance-uuid>
      member_type: dcm_peer
      member_role: eu_region_dcm
    - member_uuid: <us-dcm-instance-uuid>
      member_type: dcm_peer
      member_role: us_region_dcm
  federation_config:
    shared_policy_inheritance: opt_in
    cross_member_visibility: audit_only

# Parent-Child relationship — nesting
dcm_group:
  group_class: tenant_boundary
  name: "Corporate DCM"
  child_groups:
    - <region-eu-dcm-uuid>
    - <region-us-dcm-uuid>
  policy_inheritance: opt_out      # parent policies cascade unless child excludes
```

---

## 3. Provider Federation Eligibility

### 3.1 Concept

Every provider registration carries a `federation_eligibility` declaration — whether the provider can participate in cross-DCM federation, with whom, and under what conditions. This is **layer-defined** (static organizational knowledge) and **policy-enforced** (runtime governance).

### 3.2 Federation Eligibility on Provider Registration

```yaml
provider_registration:
  handle: "providers/service/eu-compute-primary"

  federation_eligibility:
    mode: <none|selective|open>
    # none:      Provider cannot participate in any DCM federation
    #            (sovereign, classified, or compliance-restricted providers)
    # selective: Federation permitted only with explicitly declared partners
    # open:      Federation permitted with any trusted DCM peer
    #            (sovereignty checks always apply regardless)

    permitted_partners:
      - partner_type: <dcm_peer|dcm_child|dcm_parent|dcm_hub>
        dcm_instance_uuids: [<uuid>]          # specific instances
        dcm_instance_tags: [region-eu, internal]  # tag-based matching
        dcm_certification_required: [ISO-27001, GDPR-compliant]
        relationship_requires_approval: true   # bilateral approval required

    federation_scope:
      permitted_resource_types:
        - resource_type: Compute.VirtualMachine
          operations: [allocate, query_capacity]
          # NOT: decommission — remote DCMs cannot decommission local resources
        - resource_type: Network.VLAN
          operations: [allocate, query_capacity, release]
      data_sharing:
        capacity_data: true
        realized_state: false           # do not share realized state details
        pricing_data: true
        sovereignty_declaration: true   # always share — required for federation
      max_allocations_per_partner: 100
      max_concurrent_allocations: 500

    override_reason: null               # populated when overriding layer default
```

### 3.3 Layer-Defined Federation Defaults

Federation eligibility defaults live in a `platform` domain layer — static organizational knowledge inherited by all providers unless overridden. Individual provider registrations may be **more restrictive** than the layer default (always permitted); **less restrictive** requires GateKeeper policy approval.

```yaml
layer:
  handle: "platform/federation/provider-federation-defaults"
  domain: platform
  priority: 600.0.0
  fields:
    provider_federation_defaults:
      compute_providers:
        federation_eligibility:
          mode: selective
          permitted_partners:
            - partner_type: dcm_peer
              dcm_instance_tags: [internal, eu-region]
              dcm_certification_required: [ISO-27001]
          federation_scope:
            permitted_resource_types:
              - resource_type: Compute.VirtualMachine
                operations: [allocate, query_capacity]
      (prescribed infrastructure)s:
        federation_eligibility:
          mode: none                    # storage never federated — data sovereignty
      network_providers:
        federation_eligibility:
          mode: selective
          permitted_partners:
            - partner_type: dcm_peer
              dcm_instance_tags: [internal]
      information_providers:
        federation_eligibility:
          mode: selective
          data_sharing_restrictions:
            max_classification: internal   # never share confidential/restricted
```

### 3.4 Policy Enforcement on Federation

Policies act on federation eligibility at three enforcement points:

**At tunnel establishment:**
```yaml
policy:
  type: gatekeeper
  target: dcm_tunnel_establishment
  rule: >
    If provider.federation_eligibility.mode == none
    THEN gatekeep: "Provider is not eligible for federation"

policy:
  type: gatekeeper
  target: dcm_tunnel_establishment
  rule: >
    If remote_dcm.sovereignty_zone NOT IN permitted_sovereignty_zones
    THEN gatekeep: "Remote DCM sovereignty zone incompatible with local requirements"

policy:
  type: gatekeeper
  target: dcm_tunnel_establishment
  rule: >
    If remote_dcm.certifications NOT CONTAINS
       provider.federation_eligibility.permitted_partners.dcm_certification_required
    THEN gatekeep: "Remote DCM does not hold required certifications"
```

**At allocation time:**
```yaml
policy:
  type: gatekeeper
  target: cross_dcm_allocation
  rule: >
    If resource_type NOT IN provider.federation_eligibility.federation_scope.permitted_resource_types
    THEN gatekeep: "Resource type not permitted through this federation tunnel"

policy:
  type: gatekeeper
  target: cross_dcm_allocation
  rule: >
    If cross_dcm_allocations_active > provider.federation_eligibility.max_concurrent_allocations
    THEN gatekeep: "Maximum concurrent federation allocations exceeded"
```

**At data egress:**
```yaml
policy:
  type: gatekeeper
  target: dcm_tunnel_data_egress
  rule: >
    If data.classification > remote_dcm.max_data_classification_receivable
    THEN gatekeep: "Data classification exceeds remote DCM authorization"
```

---

## 4. The DCM Provider — Cross-Instance Tunneling

### 4.1 Concept

A **DCM Provider** is a ninth provider type that wraps another DCM instance's API, enabling one DCM to consume resources managed by another DCM as if they were local providers.

| # | Type | Purpose |
|---|------|---------|
| 1 | Service Provider | Realizes resources |
| 2 | Information Provider | Serves authoritative external data |
| 3 | composite service definition | Composes multiple providers |
| 4 | data store | Persists DCM state |
| 5 | External Policy Evaluator | Supplies and evaluates policies |
| 6 | event routing service | Bridges internal/external event streams |
| 7 | credential management service | Resolves secrets |
| 8 | Auth Provider | Authenticates identities |
| 9 | **DCM Provider** | Wraps another DCM instance's API |

### 4.2 DCM Provider Registration

```yaml
dcm_provider_registration:
  artifact_metadata:
    uuid: <uuid>
    handle: "providers/dcm/region-eu-dcm"
    status: active

  provider_type: dcm_provider
  relationship_type: <peer|parent|child|hub>

  remote_dcm:
    instance_uuid: <remote-dcm-uuid>
    endpoint: https://dcm.region-eu.corp.example.com
    dcm_version: "2.1.0"          # minimum compatible version
    sovereignty_declaration_ref: <uuid>  # verified at registration time

  # Authentication — always mTLS for DCM-to-DCM
  auth:
    mode: mtls
    client_cert_ref:
      service_provider_uuid: <uuid>
      path: "dcm/dcm-providers/region-eu/client-cert"
    server_ca_ref:
      service_provider_uuid: <uuid>
      path: "dcm/dcm-providers/region-eu/server-ca"

  # Tunnel configuration
  tunnel_config:
    encrypted: true                # always — not configurable
    sovereignty_boundary_check: true  # always — not configurable
    permitted_resource_types: [Compute.VirtualMachine, Network.VLAN]
    max_allocation_per_request: 10
    audit_forwarding: true         # forward audit records to local Audit Store
    observability_forwarding: true

  # Sovereignty — must be compatible with local requirements
  sovereignty_declaration:
    remote_jurisdiction: eu-west
    data_residency_guarantee: true
    certifications: [ISO-27001, GDPR-compliant]

  # Health check
  health_check:
    endpoint: /api/v1/health
    interval_seconds: 60
    on_unhealthy: suspend_allocations
```

### 4.3 Primary Concerns on All DCM Tunnels

These are non-negotiable on every DCM-to-DCM connection:

| Concern | Enforcement |
|---------|-----------|
| **Sovereignty** | Sovereignty_declaration verified before tunnel establishment; data classification checked before every egress |
| **Authentication** | Always mTLS — no API key, no bearer token — mutual certificate authentication between DCM instances |
| **Authorization** | Local DCM policies govern ALL resources obtained through a tunnel; remote DCM's policies do not override local |
| **Audit** | All cross-DCM operations produce audit records in BOTH DCM instances; shared `correlation_id` links the two trails |
| **Observability** | Cross-DCM resource allocation visible in both instances' observability stores |
| **Governance** | Local GateKeeper policies apply to all resources from any tunnel source |

---

## 5. Cross-DCM Confidence Scoring

Resources obtained through a DCM tunnel carry compound confidence scores — the resource's confidence in its source DCM, degraded by the tunnel trust score:

```
cross_dcm_confidence = source_resource_confidence × (tunnel_trust_score / 100)
```

A resource with confidence 90 in source DCM, through a tunnel with trust score 85: `90 × 85/100 = 76.5` → **77**

### 5.1 Federation Trust Score

```yaml
dcm_federation_trust_score:
  remote_dcm_uuid: <uuid>
  score: 84                        # 0-100
  scored_at: <ISO 8601>
  decay_rate: per_30_days
  factors:
    identity_verified: true        # mTLS certificate chain verified
    sovereignty_compatible: true
    certifications_current: true
    audit_trail_integrity: true    # audit hash chains verified on sample
    uptime_score: 0.98
    compliance_score: 0.90         # policy compliance in recent operations
    data_completeness: 0.92
  action_on_score_below:
    threshold: 60
    action: <suspend_tunnel|alert|reduce_allocation_limit>
```

---

## 6. DCM Export and Import

### 6.1 Export Package

DCM state is fully exportable as a signed package — for disaster recovery, migration, cross-DCM sharing, and Hub DCM onboarding.

```yaml
dcm_export_package:
  package_uuid: <uuid>
  exported_at: <ISO 8601>
  exported_by: <actor>
  dcm_version: <version>
  signed_by: <org-signing-key>

  scope:
    tenants: [<uuid>, ...]
    resource_types: all
    layers: [platform, tenant]
    policies: [platform, tenant]
    providers: registrations_only   # not credentials — never export credentials
    entities: [intent_state, requested_state]   # not realized (that's provider state)
    groups: all
    audit_records:
      date_range: [<from>, <to>]
      include_hash_chain: true      # for audit trail verification on import

  sovereignty:
    classification: internal
    permitted_import_jurisdictions: [eu-west]
    signed: true
    encryption: aes256_gcm
```

### 6.2 Import Trust Score

When importing from another DCM instance, each imported resource carries a trust score:

```yaml
import_trust_score:
  score: 78                        # 0-100
  factors:
    source_dcm_verified: true      # source DCM identity verified
    sovereignty_compatible: true
    data_completeness: 0.92
    schema_compatibility: 1.00     # source schema matches current version
    audit_trail_complete: true     # audit records included and hash chain valid
    certifications_current: true
  action_on_low_score: <reject|import_with_warning|escalate>
  threshold: 70                    # reject if below
```

### 6.3 Scoring in Resource Definition and Allocation

Resources imported from or allocated through peer DCMs carry their compound confidence score throughout their lifecycle in the importing DCM. The score is visible to the placement engine, Cost Analysis, and the Policy Engine — enabling policies that prefer locally-managed resources over federated resources when scores are comparable.

---

## 7. Profile-Appropriate Federation Policy Groups

DCM ships built-in federation policy groups activated by default per profile:

| Group | Profile | Behavior |
|-------|---------|---------|
| `system/group/federation-minimal` | minimal | No federation — single instance only |
| `system/group/federation-dev` | dev | Peer federation permitted; advisory only |
| `system/group/federation-standard` | standard | Peer federation with certification requirements |
| `system/group/federation-prod` | prod | Selective federation; bilateral approval; audit forwarding |
| `system/group/federation-fsi` | fsi | Strict federation; within-jurisdiction only; full audit; no storage federation |
| `system/group/federation-sovereign` | sovereign | No external federation; internal peer federation within sovereignty boundary only |

---

## 8. DCM System Policies — Federation

| Policy | Rule |
|--------|------|
| `DCM-001` | DCM instances may establish peer, parent-child, or hub relationships using the Universal Group Model federation and nesting constructs. |
| `DCM-002` | All DCM-to-DCM communication uses mTLS. No API key or bearer token. Sovereignty checks are mandatory before tunnel establishment. These requirements are non-configurable. |
| `DCM-003` | Local DCM policies govern all resources obtained through DCM tunnels. Cross-DCM operations produce audit records in both DCM instances with a shared correlation_id. |
| `DCM-004` | DCM state is exportable as a signed package. Imported packages carry a trust score (0-100) computed from source verification, sovereignty compatibility, data completeness, schema compatibility, and audit trail integrity. |
| `DCM-005` | Resources obtained through DCM tunnels carry compound confidence scores: source_resource_confidence × (tunnel_trust_score / 100). |
| `DCM-006` | Every provider registration must declare federation_eligibility (mode: none, selective, or open). Federation eligibility defaults are declared in platform domain layers. Individual provider registrations may be more restrictive — never more permissive without GateKeeper policy approval. |
| `DCM-007` | Provider federation scope declares: permitted resource types, permitted operations per type, data sharing permissions, and allocation limits. Remote DCMs cannot decommission local resources through a federation tunnel. |
| `DCM-008` | Storage providers default to federation_eligibility.mode: none. Data sovereignty constraints prohibit storage federation unless explicitly authorized by sovereign policy with full justification. |

---

## 9. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | How are DCM-to-DCM certificate rotation and renewal handled — coordinated or independent? | Operations | ✅ Resolved — independent rotation with P30D overlap; peer notification 60 days before expiry via Message Bus; auto-renewal at 90 days (DCM-009) |
| 2 | Should Hub DCM relationships support automatic load balancing across child DCMs? | Architecture | ✅ Resolved — full placement engine logic at DCM instance level; sovereignty as hard pre-filter; tie-breaking hierarchy same as provider selection; sub-regional routing recursive (DCM-010) |
| 3 | How does drift detection work for resources allocated from a peer DCM — who is responsible for discovery? | Operational | ✅ Resolved — provider-side DCM discovers; consumer-side DCM compares; events via federation Message Bus; peer unavailable = alert-and-hold (DCM-011) |
| 4 | Should cross-DCM audit records be synchronized — so each DCM has the other's audit records? | Compliance | ✅ Resolved — correlation_id reference model; no full sync; on-demand pull with platform admin auth + sovereignty check (DCM-012) |
| 5 | What is the maximum supported federation depth (peer of peer of peer)? | Architecture | ✅ Resolved — profile-governed max depth: minimal/dev=5, standard/prod=3, fsi/sovereign=2; measured as hops from deepest to Hub (DCM-013) |


## 11. Federation Gap Resolutions

### 11.1 Certificate Rotation and Renewal (Q1)

DCM-to-DCM mTLS certificates rotate independently per instance with a coordinated notification model. Coordinated simultaneous rotation would create a single point of failure.

```yaml
dcm_federation_cert_rotation:
  rotation_model: independent_with_overlap
  overlap_period: P30D              # old cert valid for 30 days after new cert issued
  notification:
    notify_peers_at: P60D_before_expiry
    notification_channel: message_bus
    notification_payload:
      new_cert_public_key: <pem>
      new_cert_valid_from: <ISO 8601>
      old_cert_expires_at: <ISO 8601>
  automatic_renewal:
    trigger_at: P90D_before_expiry
    requires_approval: false          # renewal is automatic; elevation requires approval
```

The P30D overlap allows peers to update their trust stores at their own pace without service interruption.

### 11.2 Federation Routing — Placement Engine at the DCM Level (Q2)

**Hub DCM federation routing follows the same placement engine logic as provider selection.** Regional DCMs are treated as DCM Provider instances in the placement engine.

**Sovereignty is a hard pre-filter — not a preference:**

```
Before placement loop:
  Filter eligible Regional DCMs where:
    sovereignty_declaration satisfies request constraints
    operating_jurisdictions includes required jurisdictions
    sovereignty_zone matches tenant.sovereignty_zone
  
  If no eligible Regional DCMs → Reject with clear error
  Only eligible DCMs enter the placement loop
```

**The full federation routing flow:**

```
Request arrives at Hub DCM
  │
  ▼ Steps 1-5: Standard nine-step assembly (layers, policies, placement constraints)
  │  Pre-placement policies may declare federation routing constraints:
  │    "This resource must be in a Regional DCM with EU sovereignty"
  │    "This Tenant's resources must stay in Regional DCM-EU-West"
  │
  ▼ Step 6: Placement loop — at the DCM instance level
  │  Reserve query to eligible Regional DCMs:
  │    capacity available? sovereignty compatible? trust score adequate?
  │
  ▼ Tie-breaking (same hierarchy as provider selection):
  │  1. Policy preference (policy declares preferred Regional DCM)
  │  2. Federation priority (numeric priority on DCM Provider registration)
  │  3. Tenant affinity (Tenant's resources prefer a specific Regional DCM)
  │  4. Sovereignty match quality (exact match over partial match)
  │  5. Geographic affinity (closest regional to consumer)
  │  6. Least loaded (capacity utilization across instances)
  │  7. Consistent hash (deterministic tiebreaker)
  │
  ▼ Selected Regional DCM receives assembled request payload
  │  Runs its own local assembly and placement (regional layers, regional providers)
  │  Returns realization result to Hub DCM → forwarded to consumer
  │
  ▼ Sub-regional routing: Regional DCM acts as Hub for its children
    Same logic applies recursively within federation depth limit (DCM-013)
```

**Load balancing is the least-loaded step in the hierarchy** — not a primary strategy. Sovereignty, policy, and tenant affinity all take precedence. Optional `hub_dcm_load_balancing` configuration:

```yaml
hub_dcm_load_balancing:
  enabled: true                     # default: true
  sovereignty_override: true        # always — sovereignty is a hard pre-filter
  fallback_on_regional_unavailable: route_to_next_eligible
```

### 11.3 Federated Drift Detection Ownership (Q3)

Provider-side DCM is responsible for discovery; consumer-side DCM is responsible for drift comparison.

```yaml
federated_drift_detection:
  discovery_responsibility: provider_side_dcm
  comparison_responsibility: consumer_side_dcm
  mechanism:
    provider_dcm:
      - Run standard discovery against its providers
      - Publish Discovered State events to federation Message Bus
      - Tagged with: entity_uuid + consumer_dcm_uuid + correlation_id
    consumer_dcm:
      - Subscribe to Discovered State events for its federated entities
      - Compare against its Requested State
      - Trigger drift response policy if drift detected
  on_peer_dcm_unavailable:
    action: alert_and_hold            # not assumed drift
    max_hold_period: PT24H
    on_hold_exceeded: escalate_to_platform_admin
```

### 11.4 Cross-DCM Audit Record Correlation (Q4)

No full synchronization. Each DCM keeps its own authoritative audit trail. Cross-DCM correlation uses correlation_id references and on-demand pull.

```yaml
cross_dcm_audit_correlation:
  model: correlation_id_reference
  local_audit_record:
    action: ALLOCATE_FROM_PEER
    correlation_id: <uuid>
    peer_dcm_uuid: <uuid>
    peer_audit_record_uuid: <uuid>    # reference — not a copy
  on_demand_pull:
    endpoint: GET /api/v1/audit/cross-dcm/{correlation_id}
    requires: platform_admin + peer_dcm_authorization + sovereignty_check
```

Full synchronization is not required — auditors follow correlation_id to the peer DCM on demand.

### 11.5 Maximum Federation Depth (Q5)

```yaml
federation_depth_policy:
  max_depth: 3                        # profile-governed
  on_max_exceeded: reject_federation_establishment
  profile_defaults:
    minimal: 5
    dev: 5
    standard: 3
    prod: 3
    fsi: 2
    sovereign: 2
```

Depth is measured as hops from the deepest instance to the Hub DCM. Depth 3 covers Hub → Regional → Sub-Regional → Edge — sufficient for most real-world architectures.

### 11.6 System Policies — Federation Gaps

| Policy | Rule |
|--------|------|
| `DCM-009` | DCM-to-DCM mTLS certificates rotate independently per instance with a P30D overlap period. Peers are notified 60 days before expiry via Message Bus. Automatic renewal triggers 90 days before expiry. The overlap period allows peers to update trust stores without coordinated downtime. |
| `DCM-010` | Hub DCM federation routing follows the same placement engine logic as provider selection. Sovereignty is a hard pre-filter — only Regional DCMs satisfying all sovereignty constraints enter the placement loop. The tie-breaking hierarchy applies at the DCM instance level: policy preference → federation priority → tenant affinity → sovereignty match quality → geographic affinity → least loaded → consistent hash. Regional DCMs are treated as DCM Provider instances. Sub-regional routing applies the same logic recursively within the federation depth limit. |
| `DCM-011` | For resources allocated from peer DCMs, the provider-side DCM is responsible for discovery. The consumer-side DCM is responsible for drift comparison. Discovered State events are published via federation Message Bus with correlation_id. Peer DCM unavailability triggers alert-and-hold — not assumed drift. |
| `DCM-012` | Cross-DCM audit records are referenced via correlation_id — not fully synchronized. Each DCM keeps its own authoritative audit trail. Cross-DCM correlation uses on-demand pull with platform admin authorization and sovereignty check. |
| `DCM-013` | Federation depth is limited to a profile-governed maximum (default: 3 for standard/prod; 2 for fsi/sovereign; 5 for minimal/dev). Requests to establish federation beyond the maximum depth are rejected. Depth is measured as hops from the deepest instance to the Hub DCM. |


---

## 10. Related Concepts

- **Universal Group Model** (doc 15) — federation and nesting group classes
- **data stores** (doc 11) — storage never federated by default
- **Auth Providers** (doc 19) — mTLS for DCM-to-DCM authentication
- **Universal Audit Model** (doc 16) — audit records in both DCM instances; correlation_id
- **Registry Governance** (doc 20) — signed bundles for air-gapped registry updates
- **Information Providers Advanced** (doc 21) — confidence scoring used in cross-DCM context

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*

---

## 12. Federation Tunnel Establishment and Maintenance

> **Implements contracts defined in UDLM**:
> [udlm/governance/accreditation-and-authorization-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md).
> UDLM defines the Federation Tunnel Model as the contract for secure
> inter-DCM channels. This section operationalizes the establishment and
> maintenance of those tunnels.

### 12.1 Tunnel as zero-trust boundary

A federation tunnel is a mutually authenticated, encrypted, scoped channel —
**not a VPN**. It establishes secure transport, not perimeter trust. Every
message crossing the tunnel is authenticated, authorized, and subject to the
five-check boundary model defined in
[udlm/governance/accreditation-and-authorization-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md).

### 12.2 Tunnel structure

```yaml
federation_tunnel:
  uuid: <uuid>
  local_dcm_uuid: <uuid>
  remote_dcm_uuid: <uuid>
  tunnel_type: peer | parent_child | hub_spoke
  trust_model: zero_trust               # always; non-negotiable

  # Mutual authentication
  authentication:
    protocol: mtls
    local_certificate_ref: <cert-uuid>
    remote_certificate_pin: <fingerprint>  # pinned; not just chain-valid
    trust_anchor: <CA-uuid>
    certificate_rotation_interval: P90D
    revocation_check: ocsp_stapling

  # Per-message signing
  message_integrity:
    signing_algorithm: ed25519
    local_signing_key_ref: <key-uuid>
    remote_verification_key_ref: <key-uuid>
    replay_protection: true               # nonce + timestamp window PT5M

  # Inbound authorization — what remote may request from this DCM
  inbound_authorization:
    - operation: catalog_query
      permitted_resource_types: [Compute.VirtualMachine, Network.VLAN]
      requires_cross_tenant_authorization: true
    - operation: allocation_request
      permitted_resource_types: [Network.IPAddress]
      max_allocations_per_request: 10
      requires_cross_tenant_authorization: true

  # Outbound authorization — what this DCM may request from remote
  outbound_authorization:
    - operation: placement_query
      permitted_resource_types: [Compute.VirtualMachine]
    - operation: realized_state_query
      permitted_entity_uuids: [<uuid>]   # scoped to specific entities

  # Data classification boundary (hard constraints)
  data_boundary:
    max_outbound_classification: restricted  # never send sovereign/classified
    max_inbound_classification: restricted
    # sovereign profile: max_*_classification: internal
    # classified profile: no federation permitted

  # Sovereignty scope
  sovereignty_scope:
    local_jurisdiction: EU
    remote_jurisdiction: EU
    cross_jurisdiction_permitted: false   # fsi/sovereign: always false
```

### 12.3 Federation credential scoping

Federation credentials are scoped to specific tunnel operations:

```yaml
federation_credential:
  credential_uuid: <uuid>
  issued_by_dcm_uuid: <local-uuid>
  issued_to_dcm_uuid: <remote-uuid>
  expires_at: <ISO 8601>             # PT15M for fsi/sovereign
  operation_scope: catalog_query
  scoped_resource_types: [Compute.VirtualMachine]
  non_transferable: true
  tunnel_uuid: <uuid>                 # bound to specific tunnel
```

A federation credential issued for `catalog_query` cannot be used for
`allocation_request`.

### 12.4 Establishment flow

```
Local DCM initiates establishment with Remote DCM:
  ▼ Mutual mTLS handshake
  │   Validate remote certificate against trust_anchor and pin
  │   OCSP stapling for real-time revocation check
  ▼ Sovereignty compatibility check (hard pre-filter)
  │   Local + remote sovereignty zones must satisfy declared requirements
  │   Cross-jurisdiction blocked in fsi/sovereign
  ▼ Accreditation verification
  │   Remote DCM's accreditations checked via Accreditation Monitor
  │   Required accreditations per profile
  ▼ Tunnel record created (status: establishing)
  ▼ Initial federation credential issued (scoped to limited ops)
  ▼ Health probe exchange to verify bidirectional connectivity
  ▼ Tunnel transitions to active
  ▼ Audit record written: federation.tunnel_established
```

### 12.5 Tunnel maintenance

DCM maintains tunnel health via:

- **Health probes** every PT60S (configurable)
- **Certificate rotation** independent per side with P30D overlap (DCM-009)
- **Federation trust score** updated continuously per
  [udlm/contracts/information-providers-advanced.md](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers-advanced.md)
- **Sovereignty re-verification** on configurable cadence; tunnel suspended
  if sovereignty becomes incompatible
- **Federation depth enforcement** per DCM-013 (profile-governed max depth)

On tunnel degradation:
- Trust score drops below 60 → action per `action_on_score_below` config
- Sovereignty incompatibility → tunnel suspended immediately; admin notified
- Certificate revocation → tunnel suspended; new credential required

### 12.6 Hub-spoke zero trust

In hub-spoke federation, the Hub DCM coordinates Regional DCMs. Zero trust
means:

- The Hub DCM does not have root-level access to Regional DCMs — only
  explicitly scoped federation credentials
- A Regional DCM cannot impersonate the Hub to another Regional DCM
- Cross-Regional-DCM operations route through the Hub with the **Hub's
  authorization**, not the originating Regional DCM's authorization
- The Hub DCM's accreditation is visible to Regional DCMs — they can verify
  the Hub before accepting federation messages

```
RegionalDCM-A → HubDCM:  authenticated; scoped to allocation_request
HubDCM → RegionalDCM-B:  authenticated; scoped to realization_request
                          Hub presents its own credential to RegionalDCM-B
                          Not RegionalDCM-A's credential
RegionalDCM-B verifies:  Hub certificate; Hub accreditation; data boundary
```
