# DCM Registration Specification

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Registration Specification


> **AEP Alignment:** Registration API endpoints follow [AEP](https://aep.dev) conventions — custom methods use colon syntax (`POST /admin/registrations/{uuid}:approve`). `resource_type` in provider capabilities accepts FQN string or Registry UUID. See `schemas/openapi/dcm-admin-api.yaml` for the normative specification.


> **📋 Draft**
>
> This specification has been promoted from Work in Progress to Draft status. All questions resolved. Complete registration pipeline for all 11 provider types with full capability declaration schemas and federation trust model. It is ready for implementation feedback but has not yet been formally reviewed for final release.
>
> This specification defines the unified registration flow for all DCM provider types. Published to share design direction and invite feedback.

**Version:** 0.1.0-draft
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Specification
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [Control Plane Components](../../architecture/control-plane/components.md) | [Governance Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md) | [Accreditation and Authorization Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) | [Policy Profiles](../../architecture/governance-enforcement/policy-profiles.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md)

---

## Abstract

This specification defines the unified registration flow by which all DCM provider types establish a trusted, governed relationship with a DCM deployment. It covers: the Provider Type Registry, the registration token model, the approval method configuration, the step-by-step registration pipeline, trust establishment, the per-type capability declaration schemas, the ongoing lifecycle after activation, federated trust configuration, and profile-bound registration policy defaults.

---

## 1. Provider Type Registry

The Provider Type Registry is the authoritative list of provider types that a DCM deployment will accept registrations for. It follows the same three-tier registry model as the Resource Type Registry.

### 1.1 Registry Tiers

| Tier | Maintained By | Examples |
|------|--------------|---------|
| **Core** | DCM Project | The eleven built-in provider types |
| **Verified Community** | Named community maintainers | Domain-specific provider types |
| **Organization** | Deploying organization | Custom/proprietary integrations |

### 1.2 Provider Type Registry Entry

```yaml
provider_type_registry_entry:
  artifact_metadata:
    uuid: <uuid>
    handle: "provider-types/service-provider"
    version: "1.0.0"
    status: active
    tier: core

  provider_type_id: service_provider
  display_name: "Service Provider"
  description: "Realizes infrastructure resources for DCM"

  # What this provider type is permitted to do
  permissions:
    may_receive_assembled_payload: true
    may_write_realized_state: true
    may_write_discovered_state: true
    may_receive_scoped_credentials: true
    may_receive_phi_by_default: false          # requires HIPAA accreditation
    may_receive_sovereign_data: false          # hard limit; never overridden

  # Approval method defaults (profile may override — see Section 4)
  default_approval_method: reviewed        # auto | reviewed | verified | authorized

  # Minimum trust level granted after approval
  default_trust_level: standard               # minimal | standard | elevated | high

  # Which deployment profiles permit this provider type
  enabled_in_profiles: [minimal, dev, standard, prod, fsi, sovereign]

  # Capability declaration schema reference
  capability_schema_ref: "schemas/service-provider-capabilities-v1.0.0"

  # Health check requirements
  health_check:
    endpoint_required: true
    minimum_check_interval: PT1M
    failure_threshold: 3                       # failures before degraded status
```

### 1.3 The Eleven Core Provider Types

| # | provider_type_id | Default Approval | Enabled In |
|---|-----------------|-----------------|------------|
| 1 | `service_provider` | reviewed | all profiles |
| 2 | `information_provider` | reviewed | all profiles |
| 3 | `composite service` | verified | standard+ |
| 4 | `(prescribed infrastructure)` | verified | all profiles |
| 5 | `(optional infrastructure)` | reviewed | dev+ (external endpoints: standard+) |
| 6 | `external_policy_evaluation` (Mode 1-2) | reviewed | all profiles |
| 7 | `external_policy_evaluation` (Internal and External) | verified | standard+ |
| 8 | `service_provider` | verified | standard+ |
| 9 | `auth_provider` | verified | all profiles |
| 10 | `service_provider` | reviewed | all profiles |

Note: Internal and External External Policy Evaluators are treated as a separate registry entry from Mode 1-2 due to the elevated trust requirements.

---

## 2. Registration Token Model

Registration tokens are pre-issued by platform admins to authorize specific registrations without requiring full manual review at submission time.

### 2.1 Token Structure

```yaml
registration_token:
  token_uuid: <uuid>
  token_value: <cryptographically random; 32 bytes base64url>
  issued_by: <platform_admin_actor_uuid>
  issued_at: <ISO 8601>
  expires_at: <ISO 8601>                     # short-lived; default PT72H
  single_use: true                           # token invalidated after first use

  scope:
    provider_type_id: service_provider       # which provider type this authorizes
    provider_handle_pattern: "eu-west-*"     # optional: restrict to matching handles
    sovereignty_zone: eu-west-sovereign      # optional: restrict to this zone
    grants_auto_approval: true               # whether token enables auto-approval
    # grants_auto_approval: false = token still required but human review still needed
    # (useful for tracking/auditing expected registrations without bypassing review)

  max_trust_level_granted: standard          # token cannot grant higher than this
```

### 2.2 Token Issuance

```
POST /api/v1/admin/registration-tokens
Role: platform_admin

{
  "provider_type_id": "service_provider",
  "expires_in": "PT72H",
  "scope": {
    "provider_handle_pattern": "eu-west-*",
    "sovereignty_zone": "eu-west-sovereign",
    "grants_auto_approval": true
  },
  "purpose": "EU-WEST production compute provider onboarding"
}

Response 201 Created:
{
  "token_uuid": "<uuid>",
  "token_value": "<present once; never retrievable again>",
  "expires_at": "<ISO 8601>",
  "scope": { ... }
}
```

Token values are presented exactly once — at creation. They are never retrievable again (stored as a hash). Platform admins must transmit the token securely to the provider operator.

---

## 3. Approval Method Configuration

> **Authority Tier Model:** Approval methods (`reviewed`, `verified`, `authorized`) are defined in the [Authority Tier Model](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) as a named, ordered list. Organizations may insert custom tiers. The effective method resolution (Section 3.2) uses tier names; DCM resolves numeric weight from the ordered list at evaluation time (ATM-001).

### 3.1 The Four Approval Methods

| Method | Description | Approval path |
|--------|-------------|--------------|
| `auto` | DCM validates automatically; activates without human review | All validation checks pass → active |
| `reviewed` | One platform admin must explicitly approve | Submitted → validated → pending_approval → one admin approves → active |
| `verified` | Two platform admins must independently approve | Submitted → validated → pending_approval → two admins approve → active |
| `authorized` | N members of a declared DCMGroup must record decisions via the Admin API; quorum tracked by DCM; deliberation process is the organization's responsibility | Submitted → validated → pending_approval → DCMGroup members record votes via Admin API (or external systems calling API) → quorum → active |

### 3.2 Effective Approval Method Resolution

The effective approval method for a specific registration is the most restrictive result of:

```
effective_method = most_restrictive(
  provider_type_registry.default_approval_method,
  active_profile.registration_policy.min_approval_method,
  registration_token.grants_auto_approval ? relax_to_auto : no_change
)
```

Resolution rules:
- Profile minimum overrides provider type default (always upward; profiles can only tighten)
- A valid registration token can relax the effective method to `auto` ONLY if the profile's `allow_token_auto_approval` is true
- `authorized` cannot be relaxed by any token

### 3.3 Profile Registration Policy Defaults

```yaml
profile_registration_policy:
  minimal:
    min_approval_method: reviewed
    allow_token_auto_approval: true        # token can enable auto for any type
    require_sovereignty_declaration: false
    require_health_check_before_approval: false

  dev:
    min_approval_method: reviewed
    allow_token_auto_approval: true
    require_sovereignty_declaration: false
    require_health_check_before_approval: true

  standard:
    min_approval_method: reviewed
    allow_token_auto_approval: true        # tokens can auto-approve non-elevated types
    token_auto_approval_max_trust: standard  # tokens cannot auto-approve elevated types
    require_sovereignty_declaration: true
    require_health_check_before_approval: true

  prod:
    min_approval_method: reviewed
    high_trust_types_require: verified  # storage, auth, policy-mode3-4, credential
    allow_token_auto_approval: false          # no auto-approval in prod
    require_sovereignty_declaration: true
    require_accreditation_submission: true   # must submit at least self_declared
    require_health_check_before_approval: true
    approval_timeout: P7D                    # auto-reject if not approved within 7 days

  fsi:
    min_approval_method: verified       # everything requires dual approval
    allow_token_auto_approval: false
    require_sovereignty_declaration: true
    require_accreditation_submission: true
    minimum_accreditation_type: third_party  # self_declared not accepted
    require_health_check_before_approval: true
    require_governance_matrix_check: true    # governance matrix evaluated at registration
    approval_timeout: P14D

  sovereign:
    min_approval_method: authorized           # everything requires authorized approval
    allow_token_auto_approval: false
    require_sovereignty_declaration: true
    require_accreditation_submission: true
    minimum_accreditation_type: regulatory_certification
    require_hardware_attestation: true
    require_governance_matrix_check: true
    authorized_group_handle: "platform/registration-authorized"
    approval_timeout: P30D
```

---

## 4. Registration Pipeline

### 4.1 Lifecycle States

```
SUBMITTED → VALIDATING → PENDING_APPROVAL → ACTIVE
                       ↘ REJECTED (validation failure)
                                         ↘ REJECTED (approval denied)

Additional states:
ACTIVE → SUSPENDED (platform admin action or health failure)
ACTIVE → DEREGISTERING → DEREGISTERED (graceful removal)
ACTIVE → FORCED_DEREGISTERED (immediate removal)
```

### 4.2 Step 1 — Submission

Provider submits registration payload to DCM:

```
POST /api/v1/provider/register
Content-Type: application/json
X-DCM-Registration-Token: <token_value>    # optional; enables auto-approval if valid

{
  "provider_type_id": "service_provider",
  "handle": "eu-west-prod-1",
  "display_name": "EU West Production Compute Provider",
  "version": "2.1.0",

  # Mutual TLS certificate presented at connection level
  # DCM extracts the certificate fingerprint from the TLS handshake

  "sovereignty_declaration": { ... },
  "accreditations": [ ... ],
  "capabilities": { ... },              # per-type capability declaration
  "health_endpoint": "https://provider.example.com/health",
  "delivery_endpoint": "https://provider.example.com/dispatch"
}

Response 202 Accepted:
{
  "registration_uuid": "<uuid>",
  "status": "VALIDATING",
  "token_recognized": true,
  "auto_approval_eligible": true,
  "estimated_activation": "<ISO 8601>"
}
```

### 4.3 Step 2 — Validation (automated)

DCM runs automated validation checks. All must pass before advancing to PENDING_APPROVAL:

```
Validation checks:
  V1: Provider type permitted in active profile
      → Check Provider Type Registry: enabled_in_profiles includes active posture
      → FAIL: REJECTED with reason "provider_type_not_enabled_in_profile"

  V2: Governance Matrix pre-check
      → Evaluate matrix: is a provider of this type, in this zone, with these
        accreditations, permitted to register?
      → FAIL: REJECTED with reason "governance_matrix_denied" + rule_uuid

  V3: Registration token validation (if provided)
      → Token exists and not expired
      → Token matches provider_type_id and handle pattern
      → Token not already used
      → FAIL: Token invalid; fall back to non-token approval method

  V4: Certificate validation
      → mTLS certificate presented and valid
      → Certificate chain acceptable (registered CA or pinned self-signed)
      → Certificate not in revocation list
      → FAIL: REJECTED with reason "certificate_invalid"

  V5: Sovereignty declaration completeness
      → Required fields present (if profile requires declaration)
      → Jurisdiction codes valid
      → FAIL: REJECTED with reason "sovereignty_declaration_incomplete"

  V6: Capability declaration consistency
      → Declared capabilities consistent with provider type
      → No contradictory declarations
      → FAIL: REJECTED with reason "capability_declaration_invalid"

  V7: Health endpoint reachability
      → DCM contacts health_endpoint
      → Provider responds with valid health payload
      → FAIL: status → PENDING_APPROVAL with warning (profile may require passing)

  V8: Accreditation submission check
      → If profile requires accreditation submission: at least one accreditation present
      → Accreditation type meets profile minimum
      → FAIL: REJECTED with reason "accreditation_insufficient"
```

### 4.4 Step 3 — Approval

Approval flow depends on effective_approval_method:

**auto:** Registration immediately advances to ACTIVE after validation passes.

**reviewed:**
```
Registration enters PENDING_APPROVAL
Platform admin notification dispatched (urgency: medium)
Platform admin reviews in Admin API or Flow GUI:
  GET /api/v1/admin/registrations/pending
  POST /api/v1/admin/registrations/{registration_uuid}:approve
  POST /api/v1/admin/registrations/{registration_uuid}:reject
On approval: → ACTIVE
On rejection: → REJECTED with required reason field
On timeout (approval_timeout): → REJECTED with reason "approval_timeout"
```

**verified:**
```
Registration enters PENDING_APPROVAL
Two independent platform admins must approve
First approval: recorded; notification sent to other admins for second approval
Second approval by different actor: → ACTIVE
Same actor cannot approve twice
On timeout: → REJECTED
```

**authorized:**
```
Registration enters PENDING_APPROVAL
Authority group notified (all members)
Members vote via Admin API within declared quorum window
Quorum reached: → ACTIVE
Quorum not reached within approval_timeout: → REJECTED
```

### 4.5 Step 4 — Activation

On ACTIVE status:
- Provider enters the DCM provider registry
- Governance matrix rules are re-evaluated with this provider now active
- Capacity monitoring begins (if Service or Information Provider)
- Health check polling begins
- Certificate rotation schedule established
- Activation audit record written: PROVIDER_ACTIVATED
- Notification: platform admin + Tenant admins (if Tenant-scoped provider)

---

## 5. Per-Type Capability Declaration Schemas

### 5.1 Service Provider Capabilities

```yaml
service_provider_capabilities:
  resource_types:
    - resource_type_fqn: Compute.VirtualMachine
      resource_type_spec_version: "2.1.0"
      catalog_item_uuid: <uuid>
      availability_zones: [eu-west-1a, eu-west-1b]
      max_instances: 1000

  capacity_model:
    reporting_method: reserve_query | static_declaration | both
    reserve_query_endpoint: /reserve
    reserve_query_timeout: PT10S
    static_capacity:
      Compute.VirtualMachine: 500

  cancellation:
    supports_cancellation: true
    cancellation_supported_during: [DISPATCHED, PROVISIONING]
    partial_rollback_possible: true

  discovery:
    supports_discovery: true
    discovery_endpoint: /discover
    discovery_method: api_query | passive_event | hybrid
    supports_incremental_discovery: true

  monitoring:
    # Prometheus metrics endpoint — required for 1.0 readiness
    metrics_endpoint: /metrics            # must return Prometheus text format
    metrics_port: 8080                    # or same as operator endpoint
    
    # Required metric families (must be present at activation):
    required_metrics:
      - dcm_provider_dispatches_total      # {resource_type, outcome}
      - dcm_provider_dispatch_duration_seconds  # {resource_type, quantile}
      - dcm_provider_realizations_total    # {resource_type, status}
      - dcm_provider_health_status         # 1=healthy, 0=unhealthy
    
    # Optional but recommended:
    optional_metrics:
      - dcm_provider_queue_depth           # pending dispatch requests
      - dcm_provider_capacity_remaining    # {resource_type}
    
    # AEP.DEV linting — required for 1.0 readiness gate
    aep_linting:
      passes_aep_linting: true            # must pass aep.dev linter before activation
      linting_report_ref: <url>           # link to linting report
    
    # Tenant metadata endpoint — required for multi-tenant readiness
    tenant_metadata_endpoint: /api/v1/tenants/{tenant_uuid}/metadata
    # Returns: usage by tenant, quota consumed, active resources by type

  naturalization:
    target_format: openstack_nova | vmware_vsphere | custom
    custom_schema_ref: <url>

  cost_metadata:
    capex_allocation_per_unit: 12.50
    opex_per_unit_per_hour: 0.28
    currency: USD
    cost_data_dynamic_source: null | <cost_api_endpoint>

  data_handling:
    max_data_classification_accepted: restricted
    phi_capable: false                   # true requires HIPAA BAA accreditation
    pci_capable: false
```

### 5.2 Information Provider Capabilities

```yaml
information_provider_capabilities:
  data_domains:
    - domain: business_data
      data_types: [business_unit, cost_center, product_owner]
      authority_level: primary | secondary | supplementary
      schema_version: "1.0.0"
      query_endpoint: /query
      write_back_supported: false

  query_capacity:
    max_queries_per_second: 100
    rate_limit_window: 60s
    burst_capacity: 200

  confidence_model:
    data_freshness_sla: PT1H
    corroboration_sources: [cmdb, hr_system]

  caching:
    cacheable: true
    cache_ttl: PT15M
    cache_invalidation_webhook: /invalidate
```

### 5.3 data store Capabilities

```yaml
(prescribed infrastructure)_capabilities:
  store_types_supported:
    - store_type: gitops
      branch_per_request: true
      pr_semantics: true
      search_index_companion: true
    - store_type: write_once_snapshot
      entity_uuid_keyed: true
      hash_chain_integrity: true
      point_in_time_query: true

  consistency:
    guarantee: strong | eventual | bounded_staleness
    bounded_staleness_max: PT5M

  replication:
    geo_replicated: true
    replication_regions: [eu-west, eu-north]
    synchronous_replication: true

  encryption:
    at_rest: AES-256
    hsm_backed: false
    key_management: provider_managed | customer_managed | hsm

  retention:
    supports_retention_policy: true
    minimum_retention: P1Y
    maximum_retention: P10Y
    tamper_evident: true
```

### 5.4 External Policy Evaluator Capabilities

```yaml
external_policy_evaluation_capabilities:
  mode: 1 | 2 | 3 | 4
  policy_types_supported:
    - gating
    - validation
    - transformation
    - recovery
    - orchestration_flow

  framework: opa | cedar | custom
  rego_version: "1.0"                # for OPA providers

  # Internal/External specific
  remote_endpoint: https://policy.example.com/evaluate
  endpoint_sovereignty_zone: eu-west-sovereign
  evaluation_latency_p95: PT200MS
  supports_bundle_push: true
  supports_bundle_pull: true

  shadow_mode_supported: true
  test_harness_endpoint: /test
```

### 5.5 Auth Provider Capabilities

```yaml
auth_provider_capabilities:
  authentication_modes:
    - api_key
    - ldap
    - oidc
    - oidc_mfa
    - saml
    - mtls
    - hardware_token
    - hardware_token_mfa

  mfa_methods:
    - totp
    - push_notification
    - hardware_token

  rbac_model: flat | hierarchical | attribute_based
  external_idp_integration: true
  idp_protocols: [oidc, saml, ldap]

  token_lifetime_config:
    default_lifetime: PT1H
    min_lifetime: PT5M
    max_lifetime: PT8H
    step_up_supported: true

  builtin: false                       # true for DCM's built-in auth provider
```

### 5.6 notification service Capabilities

```yaml
service_provider_capabilities:
  delivery_channels:
    - channel_type: slack
      supports_threading: true
      supports_urgency_routing: true
      config_schema_ref: <schema_uuid>
    - channel_type: pagerduty
      supports_escalation: true
      config_schema_ref: <schema_uuid>
    - channel_type: webhook
      protocols: [https]
      auth_modes: [hmac_sha256, mtls, bearer]
      config_schema_ref: <schema_uuid>
    - channel_type: email
      html_supported: true

  delivery_guarantees:
    at_least_once: true
    idempotency_key: notification_uuid
    max_delivery_latency_seconds: 30
    retry_policy:
      max_attempts: 7
      backoff: exponential
      on_exhaustion: dead_letter

  sovereignty_aware_delivery: true    # checks endpoint jurisdiction before delivery
```

### 5.7 credential management service Capabilities

```yaml
service_provider_capabilities:
  credential_types:
    - api_key
    - x509_certificate
    - ssh_key
    - service_account_token
    - database_password
    - hsm_backed_key

  secret_engines:
    - vault
    - aws_secrets_manager
    - azure_key_vault
    - gcp_secret_manager

  rotation_support: true
  hsm_backed: false
  fips_140_2_level: 1 | 2 | 3        # for sovereign deployments
  dynamic_secrets: true               # generate credentials on demand
```

### 5.8 event routing service Capabilities

```yaml
(optional infrastructure)_capabilities:
  protocols: [kafka, amqp, mqtt, grpc]
  persistence: true
  durability: at_least_once | exactly_once
  max_throughput_msg_per_sec: 100000
  retention:
    message_retention: P7D
    retention_configurable: true
  external_endpoints: false           # true if messages can leave sovereignty boundary
  encryption_in_transit: TLS-1.3
  encryption_at_rest: AES-256
```

### 5.9 composite service definition Capabilities

```yaml
composite service_capabilities:
  constituent_provider_types:
    - service_provider
    - information_provider

  composition_model: sequential | parallel | conditional
  partial_delivery_supported: true
  compensation_supported: true

  resource_types_composed:
    - resource_type_fqn: ApplicationStack.WebApp
      constituent_resource_types:
        - Compute.VirtualMachine
        - Network.IPAddress
        - DNS.Record
        - Network.LoadBalancer
```

---

## 6. Federated Trust Configuration

### 6.1 Federation Trust Postures

| Posture | Description | Operations permitted |
|---------|-------------|---------------------|
| `verified` | Manually verified and approved by local platform admin | Full declared scope per tunnel authorization |
| `vouched` | Introduced through a trusted Hub DCM | Vouching authority's declared scope; cannot exceed voucher's scope |
| `provisional` | Cryptographically verified but not yet manually approved | catalog_query only (if profile permits) |

### 6.2 Federation Trust Registration Flow

```
Remote DCM requests federation peering
  │
  ▼ Cryptographic verification (always):
  │   mTLS certificate validation
  │   Certificate not in revocation list
  │   Certificate signed by acceptable CA

  ▼ Governance matrix pre-check:
  │   Is federation with this peer's jurisdiction/accreditation permitted?

  ▼ Trust posture determination:
  │   Prior record of this remote UUID? → verified or vouched (per prior record)
  │   No prior record → provisional

  ▼ Approval flow (per profile):
  │   dev:      provisional auto-promoted to verified (if governance matrix permits)
  │   standard: reviewed for verified promotion; provisional gets limited scope
  │   prod:     verified for verified promotion; no provisional operations
  │   fsi:      verified + accreditation check; no provisional
  │   sovereign: authorized_approval + hardware attestation; no provisional

  ▼ Scope assignment per trust posture

  ▼ Tunnel established with governance matrix enforcement
```

### 6.3 Profile Federation Trust Policy

```yaml
profile_federation_policy:
  minimal:
    permitted_trust_postures: [verified, vouched, provisional]
    auto_promote_provisional: true
    cross_jurisdiction_permitted: true
    accreditation_required_for_federation: false

  dev:
    permitted_trust_postures: [verified, vouched, provisional]
    auto_promote_provisional: true
    provisional_permitted_operations: [catalog_query, resource_query]
    cross_jurisdiction_permitted: true

  standard:
    permitted_trust_postures: [verified, vouched]
    approval_method_for_verified: reviewed
    cross_jurisdiction_permitted: true
    accreditation_required_for_federation: false

  prod:
    permitted_trust_postures: [verified]
    approval_method_for_verified: verified
    cross_jurisdiction_permitted: true
    accreditation_required_for_federation: false

  fsi:
    permitted_trust_postures: [verified]
    approval_method_for_verified: verified
    cross_jurisdiction_permitted: false
    accreditation_required_for_federation: true
    minimum_peer_accreditation: third_party
    re_verification_interval: PT8H

  sovereign:
    permitted_trust_postures: [verified]
    approval_method_for_verified: authorized
    cross_jurisdiction_permitted: false
    accreditation_required_for_federation: true
    minimum_peer_accreditation: sovereign_authorization
    hardware_attestation_required: true
    data_classification_boundary: internal
    re_verification_interval: PT4H
```

---

## 7. Ongoing Lifecycle After Activation

### 7.1 Health Monitoring

```
DCM polls provider health endpoint every health_check_interval
  │
  ├── Response: healthy → no action; next poll scheduled
  ├── Response: degraded → DCM updates capacity rating; reduces routing preference
  ├── No response (1 failure) → warning; retry at shorter interval
  ├── No response (failure_threshold reached) → provider status → DEGRADED
  │   Notification: platform admin (urgency: high)
  │   New requests no longer routed to this provider
  └── No response (2× failure_threshold) → provider status → UNAVAILABLE
      Active entities checked; drift detection triggered
      Platform admin notification (urgency: critical)
```

### 7.2 Certificate Rotation

```yaml
certificate_rotation:
  rotation_interval: P90D           # profile-governed default
  transition_window: P7D            # old cert valid during transition
  pre_rotation_warning: P14D        # warn provider P14D before expiry

# Rotation flow:
POST /api/v1/provider/certificates:rotate
{
  "new_certificate_pem": "<PEM>",
  "transition_window": "P7D"
}
# DCM accepts both old and new certificates during transition window
# After transition window: old certificate rejected
```

### 7.3 Capability Updates

Providers may update their capability declarations (new resource types, updated capacity models, new accreditations). Capability updates go through a simplified registration amendment flow:

```
POST /api/v1/provider/capabilities/update
{
  "amendment_type": "add_resource_type | remove_resource_type | update_capacity | add_accreditation",
  "changes": { ... }
}

→ VALIDATING (automated checks only)
→ PENDING_APPROVAL (if amendment_type is add_resource_type or sovereignty change)
→ ACTIVE (capability declarations updated)
```

### 7.4 Deregistration

**Graceful deregistration:**
```
Provider submits deregistration intent
DCM checks: active entities hosted at this provider
If active entities > 0:
  Decision required: migrate_entities | decommission_entities | reject_deregistration
Platform admin approves deregistration plan
Provider enters DEREGISTERING state
Entity migration or decommission completes
Provider status → DEREGISTERED
```

**Forced deregistration:**
```
POST /api/v1/admin/providers/{provider_uuid}/force-deregister
Role: platform_admin
Requires: verified (fsi/sovereign: authorized)

Immediate effect:
  Provider status → FORCED_DEREGISTERED
  All active entities → INDETERMINATE_REALIZATION
  Governance matrix re-evaluated for all affected entities
  Recovery policy fires: DRIFT_RECONCILE or NOTIFY_AND_WAIT per profile
```

---

### 7.2 Provider 1.0 Readiness Gates

Before a Service Provider can be activated in `standard`, `prod`, `fsi`, or `sovereign`
profiles, the following readiness gates must pass. These align with the DCM roadmap's
1.0 criteria for Service Provider deployment:

| Gate | Requirement | Profiles Required |
|------|------------|-------------------|
| `GATE-SP-01` | Simple OpenAPI Spec — declared at registration, URL reachable | all |
| `GATE-SP-02` | Healthy API — health endpoint returns `{"status": "healthy"}` at activation | all |
| `GATE-SP-03` | State Management — implements realized_state_push callback | all |
| `GATE-SP-04` | Tenant Metadata — endpoint declared or implemented | standard+ |
| `GATE-SP-05` | Prometheus Metrics — required metric families present at declared endpoint | standard+ |
| `GATE-SP-06` | AEP.DEV Linting — OpenAPI spec passes AEP linter with no errors | standard+ |
| `GATE-SP-07` | Multi-Tenant Ready — accepts tenant_uuid in all dispatch payloads | standard+ |

DCM evaluates readiness gates automatically during the approval pipeline. A provider
that fails a gate is rejected with a `READINESS_GATE_FAILED` error listing which
gates failed and what is needed to pass.

**Required metric families (GATE-SP-05):**

```
dcm_provider_dispatches_total{resource_type, outcome}
dcm_provider_dispatch_duration_seconds{resource_type, quantile}
dcm_provider_realizations_total{resource_type, status}
dcm_provider_health_status   # 1=healthy, 0=unhealthy/degraded
```

**AEP linting (GATE-SP-06):**
Run the AEP linter against the provider's OpenAPI spec before registration.
Common failures: slash-verb paths instead of colon syntax, missing page_size
on list endpoints, 202 responses without Operation resource on async operations.
The linting report URL should be included in the monitoring capability declaration.

---


## 8. Error Model

| Error Code | Meaning |
|-----------|---------|
| `provider_type_not_enabled` | Provider type not permitted in active profile |
| `governance_matrix_denied` | Governance matrix pre-check denied registration |
| `certificate_invalid` | mTLS certificate invalid or not from acceptable CA |
| `token_invalid` | Registration token expired, used, or type mismatch |
| `token_insufficient_scope` | Token present but does not grant required approval level |
| `sovereignty_declaration_incomplete` | Required sovereignty fields missing |
| `accreditation_insufficient` | Active profile requires higher accreditation type |
| `capability_declaration_invalid` | Capability declarations internally inconsistent |
| `approval_timeout` | Registration not approved within approval_timeout period |
| `health_check_failed` | Provider health endpoint unreachable during validation |
| `duplicate_handle` | A provider with this handle already exists in active status |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
