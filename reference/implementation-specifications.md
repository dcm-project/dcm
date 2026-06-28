# DCM Data Model — Implementation Specifications

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Implementation Reference
**Related Documents:** [Control Plane Components](../architecture/control-plane/components.md) | [data stores](https://github.com/croadfeldt/udlm/blob/main/contracts/storage-providers.md) | [Universal Audit](https://github.com/croadfeldt/udlm/blob/main/observability/universal-audit.md) | [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md) | [Deployment Redundancy](../architecture/runtime-features/deployment-redundancy.md) | [Session Revocation](../architecture/control-plane/session-revocation.md)

> **AEP Alignment:** API endpoints follow [AEP](https://aep.dev) conventions.
> See `schemas/openapi/dcm-admin-api.yaml` and `dcm-consumer-api.yaml` for normative specs.

---

## 1. Purpose

This document specifies the implementation mechanics for capabilities that are architecturally defined elsewhere but whose runtime behavior — enforcement location, algorithm, data structure — has not been fully specified. It closes implementation gaps identified in the architecture gap analysis.

---

## 2. Rate Limiting — Enforcement Implementation

Rate limiting is defined at the interface level in the Consumer API Specification (§1.6) and the Admin API. This section specifies *how* it is enforced.

### 2.1 Enforcement Location

Rate limiting is enforced by the **API Gateway** component — the single ingress point for all consumer and admin API traffic. It is enforced before the request reaches any pipeline component. The Request Orchestrator never sees rate-limited requests.

Rate limiting is **not** enforced at the network layer (load balancer) or application layer (Request Payload Processor). A single enforcement point at the API Gateway ensures:
- Consistent limits across all consumer paths (Web UI, direct API, CI/CD)
- No rate limit bypass via internal component calls
- Single source of rate limit state for accurate tracking

### 2.2 Token Bucket Algorithm

DCM uses the **token bucket** algorithm with a per-actor bucket:

```
Actor makes request:
  │
  ▼ API Gateway looks up actor_uuid in rate limit store
  │   (in-memory cache backed by a fast PostgreSQL store contract)
  │
  ▼ Current bucket state:
  │   tokens_remaining: <current count>
  │   last_refill_at: <timestamp>
  │
  ▼ Refill calculation:
  │   elapsed_seconds = now - last_refill_at
  │   tokens_to_add = elapsed_seconds × (rate_limit / 60)
  │   tokens_remaining = min(bucket_max, tokens_remaining + tokens_to_add)
  │   last_refill_at = now
  │
  ▼ Token check:
  ├── tokens_remaining >= 1:
  │     tokens_remaining -= 1
  │     Request proceeds
  │     Response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
  │
  └── tokens_remaining < 1:
        Request rejected: 429 Too Many Requests
        Response headers: Retry-After, X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        Audit record written: rate_limit_exceeded
```

### 2.3 Bucket Parameters by Profile

| Profile | Rate (req/min) | Burst Max | Bucket Max |
|---------|---------------|-----------|------------|
| `minimal` | 60 | 20 | 80 |
| `dev` | 120 | 40 | 160 |
| `standard` | 300 | 100 | 400 |
| `prod` | 600 | 200 | 800 |
| `fsi` | 600 | 200 | 800 |
| `sovereign` | 600 | 200 | 800 |

System components (service accounts, provider callbacks) use `prod` bucket parameters regardless of profile.

### 2.4 Rate Limit State Store

The rate limit state is stored in a **dedicated in-memory cache** backed by a fast data store:
- Cache TTL: 2× the rate limit window (120 seconds for 60 req/min rate)
- PostgreSQL store contract: key-value (Redis or equivalent)
- Consistency: eventual — brief over-counting tolerated to avoid distributed lock overhead
- Cross-replica sharing: rate limit state is shared across all API Gateway replicas via the backing store

### 2.5 Exemptions

The following are exempt from consumer rate limits:
- Admin API calls (separate rate limit bucket, 3× profile limit)
- Provider callback endpoints (authenticated via provider callback credential; separate per-provider bucket)
- Internal DCM component calls (authenticated via mTLS + interaction credential; not rate limited)
- Health check endpoints (`/livez`, `/readyz`, `/metrics`)

### 2.6 System Policies

| Policy | Rule |
|--------|------|
| `RLM-001` | Rate limiting is enforced at the API Gateway. No other component enforces rate limits. |
| `RLM-002` | Rate limit buckets are per authenticated actor (actor_uuid). Unauthenticated requests are rejected at auth before reaching the rate limiter. |
| `RLM-003` | All rate limit rejections produce an audit record with actor_uuid, endpoint, and timestamp. |
| `RLM-004` | Rate limit parameters are governed by the active Profile. Operators may increase but not decrease profile-defined limits. |
| `RLM-005` | Rate limit state is not persisted across API Gateway restarts. Buckets refill from empty after restart — brief over-serving is acceptable. |

---

## 3. Audit Log Hash Chain — Verification Schedule and Implementation

The hash chain structure is defined in [Universal Audit](https://github.com/croadfeldt/udlm/blob/main/observability/universal-audit.md) §8. This section specifies the verification schedule, triggering component, and response protocol.

### 3.1 Hash Computation

Each audit record's `record_hash` is computed as:

```
record_hash = SHA-256(
    record_uuid ||
    record_timestamp ||
    entity_uuid ||
    action ||
    actor.immediate.uuid ||
    subject_handle ||
    chain_sequence ||
    previous_record_hash
)

Where || denotes canonical concatenation with a field separator (0x1F — ASCII unit separator).
The hash is stored as a lowercase hex string.
```

The `previous_record_hash` for the first record in an entity's chain is `SHA-256("GENESIS")` — a known constant, not null.

### 3.2 Verification Schedule

Hash chain verification runs on two schedules:

**Continuous verification (per-write):**
Every audit record write triggers an immediate verification of that record against its predecessor. This catches chain breaks at write time — before the record is committed. A write that would break the chain is rejected and triggers `audit.chain_integrity_alert`.

**Periodic batch verification (scheduled):**
The Audit component runs a full-chain verification sweep on a profile-governed schedule:

| Profile | Sweep interval | Scope per sweep |
|---------|---------------|-----------------|
| `dev` | P7D | All entities modified in the last 7 days |
| `standard` | P1D | All entities modified in the last 24 hours |
| `prod` | PT12H | All entities modified in the last 12 hours |
| `fsi` | PT6H | All entities + random 5% sample of all-time records |
| `sovereign` | PT1H | All entities + random 10% sample of all-time records |

### 3.3 Owning Component

Hash chain verification is owned by the **Audit component** — the same component that writes audit records. It is not a separate service. The Audit component runs verification as a background goroutine with no external trigger required.

For data store implementations: the Audit Store must support ordered range queries by `(entity_uuid, chain_sequence)` to enable efficient sweep verification.

### 3.4 Breach Response Protocol

```
Chain break detected (during write-time or sweep verification):
  │
  ▼ Affected records flagged: integrity_status = chain_break
  │   Break point: chain_sequence N where hash mismatch occurs
  │   All records with chain_sequence > N for this entity: integrity_status = unverified
  │
  ▼ audit.chain_integrity_alert event fired (urgency: critical, non-suppressable)
  │   payload: {entity_uuid, entity_type, break_at_sequence, break_detected_at, sweep_type}
  │
  ▼ Notifications dispatched:
  │   → Platform Admin (urgency: critical)
  │   → Security team (if configured in notification routing)
  │
  ▼ Affected entity flagged in audit dashboard
  │   Consumer-visible: "Audit integrity alert — contact platform admin"
  │
  └── Human investigation required:
        Normal resolution paths:
        - store failure caused write corruption → data store replacement
        - Clock skew between replicas caused ordering issue → Non-malicious; document and reseal
        - Administrative error (direct DB edit) → Incident report, access review
        - Malicious tampering → Security incident declared
```

### 3.5 Chain Resealing

After a chain break is investigated and root cause documented, a platform admin may reseal the chain:

```
POST /api/v1/admin/audit/entities/{entity_uuid}:reseal-chain
  {
    "investigation_reference": "INC-2026-042",
    "root_cause": "storage_failure",
    "resolution_notes": "PostgreSQL WAL corruption during storage migration"
  }

Response:
  {
    "entity_uuid": "<uuid>",
    "chain_resealed_at": "<ISO 8601>",
    "records_affected": 7,
    "new_chain_anchor": "<hash of last verified record>",
    "audit_record_uuid": "<uuid of the reseal audit record itself>"
  }
```

The reseal itself produces an audit record that references the investigation. Chain integrity is restored from the reseal point forward.

---

## 4. Multi-Tenancy at the Storage Layer

Tenant isolation in DCM is enforced at the data model level (every entity carries `tenant_uuid`) and at the API level (all consumer endpoints are scoped to the authenticated actor's tenant). This section specifies the storage-layer enforcement mechanisms.

### 4.1 Isolation Strategy by Store Type

| Store Type | Isolation Strategy | Implementation Notes |
|-----------|-------------------|---------------------|
| **DCM database** (Intent/Requested State) | Directory namespace per tenant | `/tenants/{tenant_uuid}/intents/`, `/tenants/{tenant_uuid}/requests/` — Git ACLs enforce read/write scope |
| **pipeline_events table** (Audit) | Separate stream per tenant | `dcm.audit.{tenant_uuid}` stream; Kafka topic ACLs restrict producer/consumer access |
| **realized data domain** (Realized State) | Row-level filter + column-level encryption | `tenant_uuid` column indexed; all queries mandatory-include `WHERE tenant_uuid = ?`; tenant-scoped encryption key |
| **Search Index** | Index namespace per tenant | Separate index prefix `tenant_{uuid}_*`; query routing enforces tenant scope |
| **Rate Limit Cache** | Key-namespaced per actor (actor carries tenant context) | `rl:{tenant_uuid}:{actor_uuid}` key structure |

### 4.2 realized data domain — Row-Level Security Implementation

The realized data domain (Realized State) uses row-level security as the primary isolation mechanism:

```sql
-- PostgreSQL row-level security policy
CREATE POLICY tenant_isolation ON realized_state_records
  USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);

-- Every connection sets tenant context before any query:
SET LOCAL dcm.current_tenant_uuid = '<tenant_uuid>';

-- This makes it impossible to query across tenant boundaries,
-- even with direct database access using the application credential.
-- Platform admin access uses a separate role without the RLS policy.
```

### 4.3 Tenant-Scoped Encryption

For `fsi` and `sovereign` profiles, realized state records are encrypted at rest using a per-tenant encryption key:

```
Tenant provisioned:
  │
  ▼ credential management service generates tenant encryption key (AES-256-GCM)
  │   Key stored in: credential management service (e.g., Vault)
  │   Key reference stored in: Tenant record as tenant_encryption_key_ref
  │
  ▼ On write to realized data domain:
  │   API Gateway fetches tenant encryption key
  │   Payload encrypted with tenant key before storage
  │   data store stores ciphertext only
  │
  ▼ On read from realized data domain:
  │   API Gateway fetches tenant encryption key
  │   Decrypts payload in memory
  │   Plaintext never written to data store logs
  │
  ▼ Tenant decommission:
      Tenant encryption key revoked in credential management service
      All tenant data becomes unreadable without external recovery
      This is the cryptographic equivalent of data deletion
```

### 4.4 Cross-Tenant Query Prevention

Platform admin endpoints that query across tenants use a separate database role with explicit permission grants — they do not bypass RLS, they use a role that has cross-tenant read permission with full audit logging. The principle is: cross-tenant reads are possible only through intentional, audited, privileged operations.

### 4.5 System Policies

| Policy | Rule |
|--------|------|
| `STI-001` | Every query to a tenant-scoped store must include `tenant_uuid` as a mandatory predicate. Queries without tenant scope are rejected by the storage layer. |
| `STI-002` | Row-level security is enabled on all relational snapshot stores. Disabling RLS requires platform admin action and produces an audit record. |
| `STI-003` | For `fsi` and `sovereign` profiles, tenant-scoped encryption is mandatory. Key rotation is performed on a profile-governed schedule (P90D for fsi; P30D for sovereign). |
| `STI-004` | data store implementations must declare their tenant isolation strategy at registration. DCM validates the declared strategy against the active profile's isolation requirements during the registration approval pipeline. |

---

## 5. Cross-Region Data Replication

DCM's multi-region deployment model is specified in [Deployment Redundancy](../architecture/runtime-features/deployment-redundancy.md). This section specifies the replication mechanics and sovereignty enforcement at the replication layer.

### 5.1 What Replicates Where

| Store Type | Replication Model | Sovereignty Constraint |
|-----------|------------------|----------------------|
| **DCM database** (Intent State) | Git push/pull — upstream-downstream replication | Intent records tagged with `sovereignty_zone`; replicated only to stores within the declared zone |
| **pipeline_events table** (Audit) | Stream mirroring with lag monitoring | Audit records replicated to all authorized regions; cross-sovereignty replication requires explicit consent |
| **realized data domain** (Realized State) | Synchronous within-zone; async cross-zone with consent | `sovereignty_zone` on entity governs which regions may hold a copy |
| **Search Index** | Async replication; eventual consistency acceptable | Same sovereignty rules as realized data domain |

### 5.2 Sovereignty-Aware Replication

Every entity carries `sovereignty_zone` declarations that constrain which data store instances may hold copies:

```yaml
entity:
  entity_uuid: <uuid>
  sovereignty_zones:
    - zone_id: EU-WEST
      data_classifications: [restricted, phi]   # these classifications must stay in EU-WEST
    - zone_id: "*"
      data_classifications: [internal]           # internal data may replicate anywhere
```

The replication controller evaluates `sovereignty_zones` before routing any replication event. Replication to a non-authorized region for a given data classification is blocked at the replication layer — the storage provider receives a `SOVEREIGNTY_VIOLATION` rejection.

### 5.3 Replication Lag Monitoring

```
data store declares: max_replication_lag: PT30S

DCM monitoring:
  Every PT10S: measure replication lag across all replica pairs
  
  If lag > max_replication_lag:
    storage.replication_lag_exceeded event (urgency: medium)
    
  If lag > 5 × max_replication_lag:
    storage.replication_degraded event (urgency: high)
    Affected region marked: capacity_status = degraded
    New requests avoid degraded region for placement
    
  If replica unreachable:
    storage.replica_unavailable event (urgency: critical)
    Affected region marked: capacity_status = unavailable
    Requests that require this region: held pending recovery
```

### 5.4 Conflict Resolution

DCM uses a **last-write-wins with causality tracking** model for cross-region conflicts:

- All writes carry a vector clock `{region_id: sequence_number}`
- Concurrent writes (same entity, different regions) are detected by vector clock comparison
- Resolution: the write with higher aggregate sequence number wins
- Losing write: preserved as a `conflict_record` in the Audit Store (never silently dropped)
- Platform admin notified of conflicts above a configurable threshold

---

## 6. Secret Zero — Initial Credential Bootstrap

The bootstrap sequence is specified in [Deployment Redundancy](../architecture/runtime-features/deployment-redundancy.md) §6. This section specifies the credential bootstrap specifically — how DCM components authenticate to each other before the credential management service is running.

### 6.1 The Bootstrap Credential Problem

At day-0, no credential management service exists. DCM components need credentials to communicate. The resolution is a **declarative bootstrap manifest** that contains one-time bootstrap credentials, plus a mandatory rotation on first successful startup.

### 6.2 Bootstrap Sequence — Credential Perspective

```
1. Bootstrap manifest contains:
   bootstrap_credentials:
     internal_ca:
       cert_pem: <base64-encoded self-signed CA certificate>
       key_pem: <base64-encoded CA private key>   # sealed with bootstrap passphrase
       
     bootstrap_admin:
       username: bootstrap-admin
       password_hash: <bcrypt hash of one-time password>  # operator sets this
       
     component_credentials:
       # Pre-shared credentials for component-to-component auth
       # until mTLS internal CA is operational
       api_gateway:    {shared_secret: <random 256-bit hex>}
       orchestrator:   {shared_secret: <random 256-bit hex>}
       policy_engine:  {shared_secret: <random 256-bit hex>}
       audit:          {shared_secret: <random 256-bit hex>}

2. Bootstrap DCM starts:
   - Internal CA initialized from bootstrap_credentials.internal_ca
   - Components issued mTLS certificates from Internal CA
   - Pre-shared secrets replaced by mTLS certificates on first successful CA handshake
   - Pre-shared secrets deleted from memory and manifest after replacement

3. credential management service starts:
   - Bootstrapped with Internal CA certificate (trusts DCM's CA)
   - Registered as the primary credential management service via bootstrap admin credential
   - Takes ownership of internal CA key management
   - Internal CA private key: transferred to credential management service, deleted from bootstrap manifest

4. Bootstrap admin credential rotation (BOOT-002 — mandatory):
   - Bootstrap admin password must be rotated on first login
   - New credential issued by credential management service (not the bootstrap manifest)
   - Old password hash deleted from manifest
   - Manifest sealed: no more secrets, only configuration

5. Bootstrap manifest after completion:
   - Contains only: DCM deployment configuration, Git remote, profile
   - No secrets remain in the manifest
   - Manifest committed to Git (now safe, secret-free)
```

### 6.3 Air-Gapped Bootstrap

For sovereign/air-gapped deployments where the credential management service requires network access to an external vault:

```
Option A — Embedded credential management service:
  Use a locally-running credential management service (e.g., HashiCorp Vault in dev mode)
  bootstrapped from the bootstrap manifest.
  Upgrade to production Vault config post-bootstrap.

Option B — Operator-held keys:
  Bootstrap manifest contains encrypted key material.
  Operator provides passphrase at bootstrap time via stdin or hardware token.
  Keys are never stored unencrypted at rest.
  
Option C — HSM-backed bootstrap:
  Internal CA private key is generated inside an HSM.
  Bootstrap manifest contains only the HSM endpoint and slot reference.
  Requires HSM to be available before DCM bootstrap begins.
```

### 6.4 System Policies

| Policy | Rule |
|--------|------|
| `BOOT-001` | The bootstrap manifest must not contain secrets after bootstrap completion. Any secret that persists in the manifest after first successful startup is a security violation. |
| `BOOT-002` | The bootstrap admin credential must be rotated on first login. DCM enforces this — the bootstrap admin account is locked from normal use until rotation is complete. |
| `BOOT-003` | Pre-shared component credentials must be replaced by mTLS certificates within PT5M of Internal CA startup. Any component still using pre-shared secrets after this window generates a security alert. |
| `BOOT-004` | The Internal CA private key must be transferred to the credential management service on credential management service registration. The key must not remain in any component's memory or storage after transfer is confirmed. |

---

## 7. Ownership Ambiguities — Resolved

### 7.1 Who Issues `operation_uuid`?

**Decision: The API Gateway issues `operation_uuid` at request ingress.**

Rationale: The API Gateway is the component that receives the POST request and must return the Operation response immediately. It assigns the UUID synchronously before any pipeline processing begins. The `operation_uuid` equals the `request_uuid` — they are the same UUID, assigned at ingress.

```
Consumer: POST /api/v1/requests {...}

API Gateway:
  1. Authenticates consumer (checks session token)
  2. Assigns request_uuid = operation_uuid = UUID4()  ← here
  3. Writes initial request record to Intent Store (status: INITIATED)
  4. Publishes request.initiated event to Request Orchestrator (with request_uuid)
  5. Returns Operation{name: /api/v1/operations/{request_uuid}, done: false}

Request Orchestrator:
  Receives request.initiated event with request_uuid
  Uses the already-assigned request_uuid throughout the pipeline
  Never assigns a new UUID
```

The Operation resource lives in a fast-queryable store owned by the API Gateway. When the pipeline progresses, the Request Orchestrator updates the Operation status by writing to this store (it has write access; the API Gateway reads from it for GET /api/v1/operations/{uuid} responses).

### 7.2 Who Owns the Credential Revocation Registry?

**Decision: The credential management service owns the Credential Revocation Registry.**

Rationale: The credential management service is the authoritative source of credential lifecycle state. It issues credentials, rotates them, and revokes them. The revocation registry is a projection of that lifecycle state optimized for fast lookup.

```
Credential Revocation Registry:
  Owner: credential management service
  Storage: dedicated fast cache (Redis or equivalent)
  Key structure: credential_uuid → {revoked_at, revocation_reason, effective_at}
  TTL: max(credential_ttl, P90D)  — persists at minimum 90 days after revocation

Access model:
  Write: credential management service (on revocation event)
  Read:  All DCM components (via credential management service query API)
         OR via local cache synced from credential management service push events

Cache sync protocol:
  credential management service publishes: credential.revoked event (Message Bus)
  All subscribed components update local revocation cache
  Cache TTL: PT1M standard; PT30S fsi/sovereign
  On cache miss: component queries credential management service directly (not the cache)

Session Revocation Registry: separate, owned by the Auth component
  (Session revocation is distinct from credential revocation)
```

---

## 8. Security Posture Specifications

### 8.1 Threat Model — Attack Surface Summary

DCM's attack surface has five distinct boundaries. Each boundary has a specific trust model and mitigation set.

**Boundary 1 — Consumer Ingress (Web UI, Consumer API)**
- Threat: Credential theft / session hijacking
- Mitigations: mTLS optional at consumer boundary; bearer tokens with short TTL (PT1H standard); session revocation registry checked on every request; rate limiting at API Gateway
- Threat: Tenant escape (accessing another tenant's data)
- Mitigations: All queries mandatory-include tenant_uuid; row-level security on storage; Governance Matrix enforced before any read

**Boundary 2 — Provider Interface (Operator Interface, Callback API)**
- Threat: Provider impersonation (malicious actor claims to be a legitimate provider)
- Mitigations: mTLS required at provider boundary; provider callback credential required for callbacks; API Gateway validates dcm_entity_uuid in every callback against provider's registered entity scope
- Threat: Malicious provider payload (provider sends crafted Realized State payload)
- Mitigations: Realized State payloads validated against Resource Type Specification schema on receipt; Gating policies evaluate provider-supplied data before it enters DCM state

**Boundary 3 — Admin Interface (Admin API)**
- Threat: Unauthorized platform admin action
- Mitigations: Authority Tier model enforces multi-tier approval for high-impact actions; all admin actions produce non-suppressable audit records; emergency admin access (break-glass) triggers immediate security notification
- Threat: Configuration injection via GitOps
- Mitigations: All GitOps PRs require domain-appropriate review before merge; policy contributions enter shadow mode before activation; Gating policies validate all contributions at submission

**Boundary 4 — Internal Component Communication**
- Threat: Component impersonation (compromised component issues requests as another)
- Mitigations: mTLS with Internal CA for all component-to-component calls; interaction credentials checked on every call; Credential Revocation Registry queried on credential use
- Threat: Lateral movement after component compromise
- Mitigations: Each component holds minimum-scope interaction credentials; no component has write access to stores it does not own; audit records cannot be deleted by any component

**Boundary 5 — Storage Layer**
- Threat: Direct database access bypassing application controls
- Mitigations: Row-level security enforces tenant isolation even with direct DB access using application credentials; platform admin credentials are separate, audited, and require MFA; data store provenance emission means all direct writes are detectable

**Highest-risk paths (not mitigated by single control):**
1. credential management service compromise → cascading trust failure. Mitigation: credential management service is air-gapped from consumer traffic; HSM-backed key storage for sovereign profiles; separate backup credential authority.
2. Internal CA compromise → all component trust fails. Mitigation: CA private key held only in credential management service (HSM-backed for fsi/sovereign); CA certificate rotation procedure documented.

### 8.2 Supply Chain Security

**Provider OpenAPI Spec Signing:**
All Service Provider OpenAPI specifications submitted at registration must be signed using the provider's private key (corresponding to the public key in their mTLS certificate). DCM verifies the signature before the spec is processed. Unsigned specs are rejected with `SPEC_UNSIGNED` at GATE-SP-01.

**Operator Container Image Provenance:**
The DCM reference implementation containers are signed using Sigstore (Cosign). Deployment manifests declare the expected image digest. Any container running a different digest triggers drift detection on DCM's own deployment.

**DCM database Secrets Scanning:**
All content committed to DCM's GitOps stores passes through a secrets scanner before being accepted. The scanner checks for:
- High-entropy strings matching known secret patterns (API keys, tokens, private keys)
- Known credential formats (AWS access keys, GitHub PATs, JWT secrets)
- PEM-encoded private key blocks

A commit containing detected secrets is rejected with `SECRETS_DETECTED` and an audit record is written. The committing actor is notified.

**SBOM Declaration:**
Service Providers must declare a Software Bill of Materials reference at registration (optional for Tier 1 `dev` profiles; required for `fsi` and `sovereign`). The SBOM reference is stored in the provider record and included in accreditation evidence.

### 8.3 System Policies

| Policy | Rule |
|--------|------|
| `SEC-001` | All provider OpenAPI specs submitted at registration must be signed. Signature verification is performed at GATE-SP-01. |
| `SEC-002` | DCM GitOps stores enforce secrets scanning on all commits. Commits with detected secrets are rejected. |
| `SEC-003` | For `fsi` and `sovereign` profiles, SBOM declaration is mandatory for all Service Providers before activation. |
| `SEC-004` | The Internal CA private key must be stored in an HSM for `sovereign` profile deployments. Software-only key storage is not permitted at sovereign profile. |
| `SEC-005` | Any direct database write to a DCM store that bypasses the application layer is detectable via data store provenance emission. Detection triggers `audit.chain_integrity_alert` for affected records. |

---

## 9. Experience Gap Specifications

### 9.1 New Tenant Onboarding Flow

```
Platform Admin initiates tenant creation:
  POST /api/v1/admin/tenants
  {
    "display_name": "Payments Platform",
    "handle": "payments-platform",
    "group_class": "tenant_boundary",
    "initial_quota_profile": "standard",
    "billing_contact": "payments-ops@corp.example.com",
    "data_classifications_permitted": ["internal", "restricted"],
    "sovereignty_zones": ["EU-WEST"]
  }

DCM auto-provisions:
  1. Tenant entity created (tenant_uuid assigned)
  2. Default resource groups created:
     - payments-platform/default (general resources)
     - payments-platform/admins (tenant admin group)
  3. Initial quota applied per quota_profile declaration
  4. Tenant admin actor created (if initial_admin_email provided):
     - Actor record created
     - Welcome notification dispatched with first-login credential
  5. Tenant Git namespace provisioned in GitOps store:
     - /tenants/payments-platform/ directory created
     - Initial tenant-scope policy stubs committed (shadow mode)
  6. Search index namespace initialized
  7. Audit stream created: dcm.audit.{tenant_uuid}

Tenant admin completes setup:
  1. First login → mandatory credential rotation (BOOT-002 equivalent)
  2. Configure Auth Provider (or inherit platform default)
  3. Add tenant members (invite by email or LDAP group mapping)
  4. Review and activate initial policy stubs
  5. Submit first service request (onboarding validation complete)

Onboarding event sequence:
  tenant.created → Platform Admin
  tenant.member_added × N → new members (welcome email)
  tenant.quota_configured → Platform Admin
  tenant.onboarding_complete → Platform Admin + Tenant Admin
  (fired when first OPERATIONAL entity exists in the tenant)
```

### 9.2 Pre-Request Cost Estimation UX

The consumer experience for cost estimation before committing a request:

```
Step 1: Consumer browses catalog
  GET /api/v1/catalog/{catalog_item_uuid}
  Response includes: cost_estimate: {monthly_usd: 45.00, basis: "declared_static"}

Step 2: Consumer configures request fields (e.g., selects VM size)
  POST /api/v1/cost/estimate
  {
    "catalog_item_uuid": "<uuid>",
    "fields": {"cpu": 8, "ram_gb": 32, "storage_gb": 200, "environment": "prod"}
  }
  Response:
  {
    "estimated_monthly_usd": 187.50,
    "cost_basis": "dynamic",
    "cost_breakdown": [
      {"component": "compute", "monthly_usd": 120.00},
      {"component": "storage", "monthly_usd": 40.00},
      {"component": "network_egress", "monthly_usd": 27.50}
    ],
    "disclaimer": "Estimate based on declared provider rates. Actual costs may vary.",
    "provider_uuid": null  // not yet placed; estimate is across eligible providers
  }

Step 3: Consumer submits request with dry_run: true (optional pre-flight)
  POST /api/v1/requests
  {
    "catalog_item_uuid": "<uuid>",
    "fields": {...},
    "dry_run": true    // evaluate policy and placement; do not dispatch
  }
  Response: Operation with metadata.dry_run_result:
  {
    "policy_result": "PASS",
    "placement_result": {
      "selected_provider": "eu-west-prod-1",
      "cost_at_selected_provider": 182.00
    },
    "gating_gates": [],
    "warnings": ["Storage class 'premium' requested; 'standard' also eligible at $35.00/mo"]
  }

Step 4: Consumer submits without dry_run → actual request
```

### 9.3 Provider Sandbox / Test Mode

Providers can register in sandbox mode for development and certification testing without affecting production routing:

```yaml
provider_registration:
  # ...standard registration fields...
  sandbox_mode: true           # this provider never receives production requests
  sandbox_profile: dev         # sandbox providers only activated under dev profile
  
  # Sandbox providers:
  # - Appear in the provider registry with status: sandbox
  # - Can be explicitly targeted by test requests (fields.target_provider_uuid)
  # - Never appear in placement engine candidate selection for non-test requests
  # - Produce full audit records (useful for certification evidence)
  # - Subject to same API validation as production providers
  # - Can graduate to production via standard registration approval flow
```

Test request targeting a sandbox provider:
```
POST /api/v1/requests
{
  "catalog_item_uuid": "<uuid>",
  "fields": { ... },
  "_test_context": {
    "target_provider_uuid": "<sandbox-provider-uuid>",
    "suppress_billing": true,
    "test_label": "certification-run-2026-04-01"
  }
}
```

### 9.4 SLA/SLO Tracking

DCM tracks service delivery against declared SLOs at the Resource Type level:

```yaml
# Declared in Resource Type Specification (doc 05)
resource_type_slo:
  resource_type: Compute.VirtualMachine
  
  slos:
    - metric: time_to_operational
      target_percentile: p95
      target_value: PT30M       # 95% of VMs should be OPERATIONAL within 30 minutes
      measurement_window: P7D   # measured over trailing 7 days
      
    - metric: uptime
      target_percentile: p99
      target_value: "99.5%"     # 99.5% uptime over trailing 30 days
      measurement_window: P30D
      
    - metric: drift_detection_latency
      target_percentile: p90
      target_value: PT1H        # drift detected within 1 hour of occurrence
      measurement_window: P7D
```

SLO breach detection:
```
DCM computes SLO metrics continuously from audit records and entity lifecycle events.

When a metric crosses a threshold:
  slo.breach_approaching (urgency: medium) — at 90% of SLO budget consumed
  slo.breach_detected (urgency: high) — SLO violated
    payload: {resource_type, slo_metric, target, actual, measurement_window}

Consumer-facing:
  GET /api/v1/resources/{entity_uuid}/slo-status
  Returns: current SLO metrics for the entity's resource type
  
Platform admin:
  GET /api/v1/admin/slo/report?resource_type=Compute.VirtualMachine&window=P7D
  Returns: aggregate SLO performance across all entities of this type
```

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
