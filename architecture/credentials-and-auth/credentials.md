---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Credential Management
Established: 2026-05-26
Maps to: udlm/governance/credentials.md
---

# Credentials

> **Implements contracts defined in UDLM**:
> [udlm/governance/credentials.md](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md).
> UDLM defines the credential scope (internal vs consumer-facing), the
> credential type taxonomy (api_key, JWT, mTLS cert, SSH key, secret,
> signing key, HSM-backed, dcm_interaction), the credential lifecycle
> (issuance / active / rotation / revocation / expired), the rotation
> protocol with parallel validity windows, the revocation propagation
> contract, consumer credential delivery, provider API contract, and
> cryptographic requirements (deferred to standards catalog). DCM
> operationalizes the storage, generation, issuance flow, rotation
> execution, revocation enforcement, delivery mechanics, validation, and
> profile-governed configuration.

---

## 1. Credential storage and access control

DCM operates at two levels of credential management:

### 1.1 Internal — DCM operational secrets

DCM's own operational secrets use envelope encryption in the PostgreSQL
`secrets` table. Each value is encrypted with AES-256-GCM using a per-secret
data encryption key (DEK); DEKs are encrypted with a master key (KEK)
sourced from the deployment environment.

| KEK source | Profile | Security level |
|---|---|---|
| Environment variable | minimal, dev | Basic — protects against database theft |
| Kubernetes Secret | standard, prod | Good — K8s RBAC + etcd encryption |
| HSM via PKCS#11 | fsi, sovereign | Strong — KEK never leaves the HSM |

The `secrets` table has the same RLS, append-only audit, and tenant isolation
as every other DCM table. Used for: provider authentication credentials
(values referenced from PCA records), encryption keys for sensitive JSONB
fields (PHI, PCI), audit signing keys, internal service credentials.

### 1.2 Consumer-facing — Credential Provider

Consumer-facing credentials (kubeconfigs, database passwords, API keys, SSH
keys, service account tokens) flow through a registered Credential Provider
(a service_provider with `Credential.*` in supported_resource_types).

**Credential values are never stored in DCM** (`CPX-001` — non-negotiable in
all profiles). DCM stores only credential metadata: UUID, type, scope,
expiry, status. The actual value is held exclusively by the Credential
Provider, retrieved by the authorized consumer via the provider's
`value_retrieval_endpoint`.

External Credential Providers are registered via the standard provider
registration contract:

```yaml
provider:
  provider_type: service_provider
  supported_resource_types:
    - "Credential.Secret"
    - "Credential.Certificate"
    - "Credential.SSHKey"
    - "Credential.APIKey"
  capability_extension:
    hsm_support: true
    rotation_protocol: automatic
    max_secret_size_bytes: 65536
    supported_algorithms: [rsa-2048, rsa-4096, ecdsa-p256, ecdsa-p384, ed25519]
```

---

## 2. Credential generation implementation

DCM does not generate credential values itself (except bootstrap tokens during
initial registration). Generation is delegated to the registered Credential
Provider per the contract in
[udlm/governance/credentials.md](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md).

DCM's role at generation time:

1. Validate the issuance request matches an authorized DCM operation (e.g.,
   resource realization triggered the request)
2. Compute the `expires_at` based on the active profile's max_lifetime
3. Build the scope: `issued_to`, `operations`, `resource_types`, `tenant_uuid`
4. Apply profile-governed bindings: `bound_to_ip` if required, hardware
   attestation flag if sovereign
5. Submit to the Credential Provider's `issue_endpoint`
6. Persist the returned credential_record metadata in `credentials` table
7. Return credential metadata to the consumer (never the value)

---

## 3. Issuance flow orchestration

### 3.1 Resource credential issuance (consumer-facing)

Credentials issued as part of resource realization flow through the standard
provider dispatch pipeline:

```
Consumer requests resource (e.g., Compute.VirtualMachine)
  ▼ Layer assembly + policy evaluation
  │   Transformation policy may inject credential_requirements:
  │     - credential_type: ssh_key
  │       issued_to: requesting_actor
  │       scope: [ssh_access]
  ▼ Placement selects Service Provider for the VM
  ▼ After VM realization: Credential Provider dispatched
  │   Sub-request issued to Credential Provider with:
  │     entity_uuid, credential_type, issued_to.actor_uuid,
  │     scope.operations, scope.resource_types, expires_at
  ▼ Credential Provider issues credential; returns credential_record
  ▼ DCM writes credential_record to Realized State; links credential_uuid to entity_uuid
  ▼ Consumer receives realized entity + credential metadata
  │   Consumer calls value_retrieval_endpoint to get actual credential
  │   (step-up MFA may be required per profile)
```

### 3.2 DCM interaction credential issuance

DCM interaction credentials are issued automatically before each provider
interaction. They implement the Zero Trust scoped credential model:

```
DCM prepares to dispatch to a provider
  ▼ API Gateway requests interaction credential from Credential Provider:
  │   credential_type: dcm_interaction
  │   issued_to.component_uuid: <api_gateway_uuid>
  │   issued_to.provider_uuid: <target_provider_uuid>
  │   scope.operations: [dispatch]
  │   scope.resource_types: [Compute.VirtualMachine]
  │   entity_uuid: <entity_being_dispatched>
  │   expires_at: <now + PT15M>  (max; profile-governed)
  ▼ DCM includes credential in provider dispatch
  ▼ Provider validates credential scope before executing
  ▼ Credential expires after PT15M regardless of use
  │   (no renewal; new credential issued for next interaction)
```

### 3.3 Bootstrap credential issuance

During bootstrap (before Credential Provider is registered), DCM uses a
bootstrap credential mechanism. After bootstrap, all credentials are issued
through a registered Credential Provider.

---

## 4. Rotation job scheduling and execution

DCM operationalizes the UDLM rotation contract through scheduled rotation
jobs (no transition window for emergency rotations).

### 4.1 Rotation triggers

| Trigger | DCM mechanism |
|---|---|
| `scheduled` | Cron-based rotation per credential type interval |
| `pre_expiry` | Time-based: rotation initiated `pre_expiry_window` before expires_at; PT5M for dcm_interaction, P14D for x509, P7D for ssh_key |
| `provider_initiated` | Provider's update notification (PCA model) triggers rotation |
| `security_event` | Emergency revocation triggers — no transition window |
| `actor_request` | Consumer requests via API; rate-limited per policy |

### 4.2 Rotation protocol execution

```
Rotation initiated (any trigger):
  ▼ DCM requests new credential from Credential Provider
  │   rotation_of: <old_credential_uuid>
  │   same scope; new expires_at
  ▼ Credential Provider issues new credential
  │   Returns new credential_record; old NOT yet revoked
  ▼ New credential delivered to authorized consumer/component
  ▼ Transition window: both credentials valid
  │   Duration: P1D for consumer credentials (default)
  │             PT5M for dcm_interaction
  │             P7D for x509_certificate
  ▼ Old credential revoked at end of transition window
  │   Revocation propagated to all registered consumers
  ▼ Rotation record written to audit trail
```

### 4.3 Pre-expiry rotation scheduler

A background worker per Credential Provider scans for credentials approaching
expiry:

```sql
SELECT credential_uuid, expires_at
FROM credentials
WHERE status = 'active'
  AND expires_at - pre_expiry_window <= now()
  AND rotation_in_progress = false
```

For each match, the rotation pipeline kicks off automatically. The worker
runs on the cadence of the shortest pre_expiry_window across active
credential types (typically PT1M for dcm_interaction credentials).

### 4.4 Emergency rotation (security event)

```
Triggers: security.credential_compromised, security.anomalous_usage_detected,
          actor.deprovisioned, provider.deregistered, accreditation.revoked
  ▼ No transition window
  ▼ Old credential revoked immediately
  ▼ New credential issued and delivered via fastest available channel
  ▼ Security event record written with full context
  ▼ Compliance-class GateKeeper firing audited against the event
  ▼ Platform admin notified regardless of profile
```

---

## 5. Revocation enforcement across providers

### 5.1 Revocation triggers

| Trigger | DCM Behavior |
|---|---|
| `actor_deprovisioned` | All credentials for actor revoked; propagated via SCIM (per `CPX-006`) |
| `entity_decommissioned` | All credentials scoped to entity revoked before decommission confirmed (per `CPX-007`) |
| `security_event` | Immediate; no transition window |
| `provider_deregistered` | All interaction credentials for provider revoked |
| `actor_request` | Consumer may revoke their own credentials |
| `ttl_expired` | Lifecycle Constraint Enforcer triggers revocation |

### 5.2 Revocation propagation

DCM maintains a Credential Revocation Registry — fast-queryable store of
revoked credential UUIDs. All components that receive interaction credentials
must check this registry on each use, not just at issuance.

```
Credential revoked
  ▼ credential record status: active → revoked
  ▼ revoked_at, revocation_reason persisted
  ▼ credential.revoked event published to pipeline_events
  ▼ All subscribed components update local revocation cache
  │   Cache TTL: PT1M standard, PT30S fsi/sovereign
  ▼ Credential Provider notified to invalidate stored value
  │   Provider must honor within revocation_sla
  │   standard/prod: PT5M
  │   fsi/sovereign: PT1M
  ▼ Audit record: credential_uuid, revocation_trigger, revoked_by_actor
```

### 5.3 Revocation check at use

Providers receiving DCM interaction credentials must validate at use time,
not only at receipt:

1. Verify credential signature (if signed)
2. Check credential UUID against local revocation cache
3. Verify credential has not expired (`expires_at`)
4. Verify operation is within credential scope
5. Verify IP binding if `bound_to_ip` is set

Failure → return `403 Forbidden` with `credential_revoked` or
`credential_expired` error code.

---

## 6. Consumer delivery mechanics

After resource realization with associated credential, the consumer receives
`credential_record` metadata in the realized entity response. The actual
value is retrieved separately:

```
GET /api/v1/resources/{entity_uuid}/credentials
→ {
    "credentials": [
      {
        "credential_uuid": "<uuid>",
        "credential_type": "ssh_key",
        "status": "active",
        "issued_at": "<ISO 8601>",
        "expires_at": "<ISO 8601>",
        "scope": {...},
        "retrieval": {
          "endpoint": "/api/v1/credentials/<uuid>/value",
          "auth_required": "step_up_mfa",
          "retrieval_count": 1,
          "last_retrieved_at": "<ISO 8601>"
        },
        "rotation_schedule": {...}
      }
    ]
  }
```

### 6.1 Value retrieval

```
GET /api/v1/credentials/{credential_uuid}/value
Authorization: Bearer <session-token>
X-DCM-StepUp-Token: <completed-challenge>     # if auth_required: step_up_mfa
→ {
    "credential_uuid": "<uuid>",
    "credential_type": "ssh_key",
    "value": { "private_key": "...", "public_key": "...", "username": "..." },
    "expires_at": "<ISO 8601>",
    "retrieval_uuid": "<uuid>"     # idempotency key; audited
  }
```

Every retrieval is audited: credential_uuid, actor_uuid, retrieved_at,
retrieval_uuid (`CPX-005`).

---

## 7. Provider authentication validation

The Credential Provider must validate at use time (see Section 5.3 above):
- Signature verification
- Revocation cache check
- Expiry check
- Scope check
- IP binding (if bound)
- `key_usage` enforcement — a credential issued for `authentication` cannot
  be used for `signing` (`CPX-009`)

---

## 8. Profile-governed constraints (enforcement)

DCM enforces the credential profile configuration at issuance and use.

| Setting | minimal/dev | standard/prod | fsi/sovereign |
|---|---|---|---|
| Default TTL | P365D | P90D | P30D |
| Max TTL | unlimited | P365D | P90D |
| Rotation grace period | P7D | P3D | P1D |
| HSM required | No | No | Yes (signing keys) |
| Idle credential detection | Disabled | P90D warning | P30D auto-revoke |
| IP binding | Optional | Optional | Required |
| FIPS level | None | Level 1 | Level 2 (fsi) / Level 3 (sovereign) |

Full per-profile configuration matrix is in
[udlm/governance/credentials.md Section 12.1](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md).
DCM applies these constants at issuance — Credential Provider may issue
shorter than max_lifetime; never longer.

### 8.1 Algorithm enforcement

DCM rejects credentials with forbidden algorithms (MD5, SHA-1, DES, 3DES,
RC4, RSA < 2048, ECDSA < P-256) at issuance regardless of profile. Approved
algorithms vary per profile:

- `minimal/dev`: negative list (forbidden_algorithms enforced; everything
  else permitted)
- `standard+`: positive list per credential type
- `fsi`: FIPS-approved subset (Ed25519 excluded from FIPS 140-2 in `fsi`;
  permitted in standard)
- `sovereign`: hsm_backed_only across all types

See [`../reference/implementation-standards.md`](../../reference/implementation-standards.md)
for the algorithm and FIPS-level decisions DCM makes.

---

## 9. Integration with external services

| External system | Integration |
|---|---|
| HashiCorp Vault PKI | Register as Credential Provider with `secret_engine: vault`; supports x509_certificate, secrets, dynamic secrets |
| AWS Secrets Manager | Register as Credential Provider with `secret_engine: aws_secrets_manager` |
| Azure Key Vault | Register as Credential Provider with `secret_engine: azure_key_vault` |
| GCP Secret Manager | Register as Credential Provider with `secret_engine: gcp_secret_manager` |
| Local HSM (sovereign) | Register as Credential Provider with `secret_engine: local_hsm`; FIPS 140-2 Level 3 |
| Enterprise CA (cert-manager / Venafi / EJBCA) | Register as Credential Provider with `external_ca_config` supporting ACME / EST / SCEP / CMP |

### 9.1 External CA integration

DCM's Credential Provider model natively supports external CAs as backends
for x509_certificate. When configured as the trust anchor for internal
component auth, DCM's component certificate requests flow through the
Credential Provider interface instead of the built-in Internal CA. This
makes DCM's internal mTLS fully auditable through existing enterprise PKI
infrastructure — a key requirement for fsi/sovereign profiles.

```yaml
external_ca_config:
  ca_protocol: acme | est | scep | cmp | vault_pki | aws_acm_pca | azure_key_vault
  ca_endpoint: <url>
  issued_cert_lifetime: P90D
  subject_template: "CN={{component_type}}-{{component_uuid}},O=dcm-internal"
```

---

## 10. Idle credential detection

A credential issued but never retrieved within the declared threshold
triggers an idle alert:

```yaml
idle_credential_record:
  credential_uuid: <uuid>
  issued_at: <ISO 8601>
  threshold_hours: 48
  last_checked_at: <ISO 8601>
  retrieval_count: 0
  status: idle_alert_pending
```

Idle threshold by profile: P30D (minimal) → PT12H (sovereign). The credential
is NOT automatically revoked at the threshold — alert only. Auto-revocation
after 2× threshold is profile-configurable (`CPX-010`).

---

## 11. Lifecycle state machine (DCM realization)

```
                    ┌──────────────┐
        issuance    │              │    expiry / explicit
  ─────────────────►│    ACTIVE    │────revocation──────────►  REVOKED / EXPIRED
                    │              │
                    └──────┬───────┘
                           │ rotation initiated
                           ▼
                    ┌──────────────┐
                    │   ROTATING   │  both old and new valid
                    │              │  during transition window
                    └──────┬───────┘
                           │ transition window ends
                           │ or emergency revocation
                           ▼
                       REVOKED
```

Every transition writes an audit record with `credential_uuid`, transition
type, and trigger metadata.

---

## 12. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `CPX-001-DCM` | DCM stores only credential metadata; credential values never in DCM data model, GitOps stores, Realized State Store, or Audit Store |
| `CPX-002-DCM` | Every DCM provider interaction presents a scoped, short-lived `dcm_interaction` credential; providers reject calls without one (403) |
| `CPX-003-DCM` | DCM propagates revocation within profile-governed cache TTL (PT1M standard; PT30S fsi/sovereign) |
| `CPX-004-DCM` | DCM emergency rotation has no transition window; old revoked immediately; new delivered via fastest channel |
| `CPX-005-DCM` | DCM audits first credential value retrieval in all profiles; subsequent retrievals in standard+ |
| `CPX-006-DCM` | Actor deprovisioning triggers immediate revocation of all credentials issued to the actor (parallel with session revocation) |
| `CPX-007-DCM` | Entity decommissioning triggers revocation of all credentials scoped to entity before decommission confirmed |
| `CPX-008-DCM` | DCM rejects unbound credentials in fsi/sovereign; IP-bound or HSM-backed required |
| `CPX-009-DCM` | DCM declares algorithm + key_usage on every credential at issuance (standard+); enforces key_usage at validation |
| `CPX-010-DCM` | DCM fires idle detection at profile threshold; alert-only; auto-revocation after 2× threshold profile-configurable |
| `CPX-011-DCM` | DCM compliance overlays always tighten (never relax) base profile credential requirements |
| `CPX-012-DCM` | CPX-001-DCM applies in ALL profiles including minimal; no profile permits credential values in DCM stores |
