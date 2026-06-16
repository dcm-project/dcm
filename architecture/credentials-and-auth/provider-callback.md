---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Provider Callback Authentication
Established: 2026-05-26
Maps to: udlm/contracts/provider-callback-auth.md
---

# Provider Callback Authentication — mTLS + Interaction Credential

> **Implements contracts defined in UDLM**:
> [udlm/contracts/provider-callback-auth.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-callback-auth.md).
> UDLM defines the mechanism-neutral two-layer authentication contract: any
> callback MUST be validated via two independent identity factors. DCM
> picks **mTLS as Layer 1** and **interaction credential as Layer 2** as
> its specific realization. A peer DCM realization could pick different
> layers (JWT + signed assertion, hardware-backed tokens, etc.) and remain
> UDLM-conformant — provided it declares its chosen mechanism via the
> schema-sharing protocol
> ([udlm/contracts/schema-sharing.md](https://github.com/croadfeldt/udlm/blob/main/contracts/schema-sharing.md)).

---

## 1. The mechanism

DCM realizes UDLM's two-layer auth contract with:

| Layer | UDLM contract | DCM mechanism |
|---|---|---|
| 1 (transport identity) | "any peer MUST attest provider identity at registration via a verifiable mechanism" | **mTLS** — the provider presents its registered X.509 certificate; DCM validates the chain against the registered CA |
| 2 (operation authorization) | "every callback MUST present an independently-verifiable credential scoped to the operation" | **Interaction credential** — a `dcm_interaction` typed credential issued by the Credential Provider, presented as `Authorization: Bearer <value>`, scoped to provider_uuid + allowed_operations |

Both layers are required on every callback. mTLS alone proves identity but
not authorization; credential alone proves authorization but not identity.

This mechanism is **DCM-specific**. A federation peer's DCM realization must
declare its chosen mechanism via the schema-sharing bundle so federated peers
can verify each other.

---

## 2. Provider certificate storage and validation

### 2.1 Certificate registration

At provider registration:

```yaml
provider_registration:
  certificate:
    pem: <PEM-encoded provider certificate>
    ca_chain: <PEM-encoded CA certificate chain>
    rotation_interval: P90D
```

DCM validates at registration:
- Certificate chain valid and trusted
- Certificate not in DCM's Credential Revocation Registry
- Certificate `CN` or `SAN` matches the declared `handle`
- Certificate `expires_at` not in the past

DCM stores the certificate fingerprint. On every subsequent inbound
connection, DCM validates the presented certificate against the stored
fingerprint for this provider.

### 2.2 mTLS enforcement at TLS handshake

```
Provider → DCM:
  TLS ClientHello → ServerHello + DCM certificate
  Provider verifies DCM certificate (DCM identity)
  Provider sends its certificate
  DCM validates:
    1. Certificate chain → registered CA for this provider
    2. Certificate fingerprint → matches stored fingerprint for provider_uuid
    3. Certificate not in Credential Revocation Registry
    4. Certificate expires_at not expired
  Any failure → TLS handshake rejected; connection refused
```

### 2.3 Certificate rotation

Providers rotate certificates on the declared `rotation_interval`. DCM fires
a `P14D` warning event when approaching expiry. During the rotation transition
window (P7D), DCM accepts both the current and new certificate
simultaneously. After the window, only the new certificate is accepted.

---

## 3. Interaction credential issuance and management

### 3.1 Provider callback credential

At provider activation, DCM issues a `dcm_interaction` credential through
the Credential Provider:

```yaml
provider_callback_credential:
  credential_uuid: <uuid>
  credential_type: dcm_interaction
  issued_to:
    provider_uuid: <uuid>
    provider_handle: <string>
  issued_at: <ISO 8601>
  expires_at: <ISO 8601>            # profile-governed
  operation_scope:
    allowed_operations:
      - realized_state_push
      - capacity_report
      - interim_status
      - update_notification
      - lifecycle_event
      - notification_poll
  non_transferable: true
  bound_to_ip: <IP|null>            # fsi/sovereign: required
  revocation_check_url: <DCM revocation endpoint>
```

Presented as `Authorization: Bearer <credential_value>` on all callback API calls.

**Key property:** the credential is scoped to the `provider_uuid` — not to
specific entities or operations within that provider. Entity-level scope is
enforced separately (Section 6).

### 3.2 Credential issuance lifecycle

```
Registration approved (provider status → ACTIVE)
  ▼ API Gateway requests credential from Credential Provider:
  │   credential_type: dcm_interaction
  │   issued_to.provider_uuid: <newly activated provider>
  │   allowed_operations: [<full list>]
  │   expires_at: <now + profile lifetime>
  ▼ Credential Provider issues credential
  │   Stores credential_record in Credential Store
  │   Returns credential_value (the bearer token)
  ▼ DCM delivers credential to provider via activation response
  │   POST /api/v1/admin/providers/{uuid}:approve
  │   Response includes: credential_ref (UUID for retrieval)
  ▼ Provider retrieves credential value via Credential Provider endpoint
  │   GET {service_provider_endpoint}/credentials/{credential_ref}/value
  │   (Requires the registration token used at initial registration — one-time bootstrap)
  ▼ Provider stores credential securely and uses for all callback calls
```

### 3.3 Credential lifetime by profile

| Profile | Lifetime | Rotation trigger | IP binding |
|---|---|---|---|
| minimal | PT8H | Pre-expiry P1H | No |
| dev | PT4H | Pre-expiry P30M | No |
| standard | PT1H | Pre-expiry PT10M | No |
| prod | PT30M | Pre-expiry PT5M | Optional |
| fsi | PT15M | Pre-expiry PT3M | Required |
| sovereign | PT15M + hardware attestation | Pre-expiry PT3M | Required; HSM-bound |

### 3.4 Rotation protocol

```
PT{rotation_trigger} before credential expiry:
  ▼ DCM initiates rotation
  │   Requests new credential from Credential Provider
  │   rotation_of: <current credential_uuid>
  │   same allowed_operations scope; new expires_at
  ▼ Credential Provider issues new; old NOT yet revoked
  ▼ DCM pushes rotation notification to provider
  │   POST {provider_health_endpoint}/credential-rotation (if supported)
  │   OR: credential.rotating event published to Message Bus
  ▼ Transition window: both credentials valid
  │   Duration: 50% of credential lifetime
  ▼ Transition window closes; old credential revoked
  │   Revocation event → all components update revocation cache
```

If the provider fails to pick up the new credential before the window closes,
the old credential is revoked and subsequent callbacks return `403 Forbidden`
with code `CREDENTIAL_EXPIRED`. The provider must re-register to recover.

---

## 4. mTLS enforcement at callback endpoint

The Provider Callback API endpoints all require Layer 1 (mTLS) at the TLS
termination point. If mTLS fails, the TLS handshake is rejected before
Layer 2 evaluation:

| Endpoint | mTLS required | Credential required |
|---|---|---|
| `POST /api/v1/providers` (registration) | Yes | Bootstrap registration token |
| `POST /api/v1/providers/{provider_uuid}/capacity` | Yes | dcm_interaction credential |
| `PUT /api/v1/instances/{resource_id}/status` | Yes | dcm_interaction credential |
| `POST /api/v1/provider/entities/{entity_uuid}/status` | Yes | dcm_interaction credential |
| `POST /api/v1/provider/entities/{entity_uuid}/update-notification` | Yes | dcm_interaction credential |
| `GET /api/v1/provider/notifications/{notification_uuid}` | Yes | dcm_interaction credential |
| `POST /api/v1/instances/{resource_id}/events` | Yes | dcm_interaction credential |

---

## 5. Validation logic at callback time

Layer 2 validation runs after the TLS handshake completes:

```
1. Extract credential_value from Authorization: Bearer header
   → Missing or malformed: 401 Unauthorized; MISSING_CREDENTIAL audit record

2. Look up credential_record by credential_value hash
   → Not found: 401 Unauthorized; CREDENTIAL_NOT_FOUND audit record

3. Check credential_record.status is 'active'
   → Revoked: 403 Forbidden; code: CREDENTIAL_REVOKED
   → Expired: 403 Forbidden; code: CREDENTIAL_EXPIRED

4. Check credential_record.expires_at > now
   → Expired: 403 Forbidden; code: CREDENTIAL_EXPIRED

5. Check credential_record.issued_to.provider_uuid matches:
   a. The provider_uuid in the URL path (where applicable)
   b. The mTLS certificate's registered provider (Layer 1 binding)
   → Mismatch: 403 Forbidden; code: CREDENTIAL_SCOPE_VIOLATION

6. Check operation_type for this endpoint is in allowed_operations
   → Not in scope: 403 Forbidden; code: OPERATION_NOT_IN_SCOPE

7. If bound_to_ip is set: verify client IP matches
   → Mismatch: 403 Forbidden; code: IP_BINDING_VIOLATION
```

All failures write an audit record with credential_uuid, provider_uuid,
endpoint, and failure reason.

After 5 consecutive `CREDENTIAL_SCOPE_VIOLATION` or `IP_BINDING_VIOLATION`
failures from the same provider within PT1H, DCM fires
`security.unsanctioned_provider_write` and notifies the platform admin
(urgency: critical).

---

## 6. Entity authorization checks

A valid credential proves the caller is the registered provider. It does NOT
prove the provider is authorized to act on a specific entity. Entity-level
authorization runs on each call.

### 6.1 Resource ownership binding (realized_state_push, interim_status)

```
PUT /api/v1/instances/{resource_id}/status

DCM checks:
  1. Look up Requested State record for resource_id
  2. Verify credential's provider_uuid matches provider_uuid in Requested State
  3. Verify entity is in a lifecycle state that permits this push
     (PROVISIONING, UPDATING, or DECOMMISSIONING — not OPERATIONAL, not DECOMMISSIONED)

  → Mismatch on provider_uuid: 403; code: ENTITY_NOT_OWNED_BY_PROVIDER
  → Wrong lifecycle state: 409; code: INVALID_LIFECYCLE_STATE_FOR_PUSH
```

A provider receiving a resource_id (e.g., by observing traffic) cannot push
realized state for an entity it was not dispatched to.

### 6.2 Update notification binding

```
POST /api/v1/provider/entities/{entity_uuid}/update-notification

DCM checks:
  1. Look up Realized State record for entity_uuid
  2. Verify credential's provider_uuid matches the provider_uuid in the most
     recent Realized State
  3. Verify the provider's registration includes the update_capability
     declared in the notification_type field

  → Provider not current owner: 403; code: ENTITY_NOT_OWNED_BY_PROVIDER
  → Update type not declared: 403; code: UPDATE_TYPE_NOT_DECLARED
```

### 6.3 Lifecycle event binding

```
POST /api/v1/instances/{resource_id}/events

DCM checks:
  1. Verify credential's provider_uuid matches provider on record for resource_id
  2. Verify resource is in an operational state (not DECOMMISSIONED)
  3. Verify event_type is in the standard event catalog

  → Provider not current owner: 403; code: ENTITY_NOT_OWNED_BY_PROVIDER
  → Entity decommissioned: 409; code: ENTITY_DECOMMISSIONED
  → Unknown event_type: 400; code: UNKNOWN_EVENT_TYPE
```

---

## 7. Registration token generation and validation

The initial `POST /api/v1/providers` registration call cannot use a callback
credential (none exists yet). DCM uses a single-use registration token:

```yaml
registration_token:
  token_uuid: <uuid>
  token_value: <present once; never retrievable again>
  issued_at: <ISO 8601>
  expires_at: <ISO 8601>     # typically PT72H
  scope:
    provider_type_id: service_provider
    provider_handle_pattern: "eu-west-*"
    grants_auto_approval: true | false
  used: false                # single-use; set true after first successful use
```

Passed as `Authorization: Bearer <token_value>` on the initial registration
call. After first successful registration, marked `used: true`. Re-registration
requires a new token (per `PCA-006`).

**mTLS still required for registration** — the provider must present the
certificate declared in the payload, proving private-key possession.

### 7.1 Re-registration

For re-registration (same `name`, updating version or capabilities), the
provider uses its active callback credential. Re-registration that changes
sovereignty declaration requires a new registration token (treated as a new
registration requiring new approval; `PCA-007`).

---

## 8. Revocation enforcement

### 8.1 Triggers

| Trigger | What happens |
|---|---|
| Provider deregistered | All callback credentials for provider revoked immediately |
| 5+ scope violations in PT1H | Provider suspended; credential revoked; platform admin notified |
| Provider certificate expiry without rotation | Credential revoked at certificate expiry |
| Platform admin explicit revocation | Immediate; provider must re-register |
| Provider compromise suspected | Emergency revocation; Recovery Policy evaluates affected entities |

### 8.2 Revocation cache

DCM components maintain a local Credential Revocation Cache populated from
the Message Bus `credential.revoked` event stream:

- Cache TTL matches the maximum credential lifetime for the active profile
- On cache miss: remote check against Credential Store (prevents stale cache
  from accepting revoked credentials)
- Cache invalidation is immediate on `credential.revoked` event receipt
  (not TTL-based)

The revocation cache ensures revocation propagates within PT30S even without
a cache miss triggering a remote lookup.

---

## 9. Emergency revocation

```
Platform admin triggers emergency revocation:
  POST /api/v1/admin/providers/{provider_uuid}/revoke-credential
  { reason: <string>, suspend_provider: true | false }

  ▼ DCM revokes credential immediately
  │   credential_record.status → revoked
  │   Revocation event → Message Bus
  │   All DCM components update revocation cache (within PT30S)
  ▼ If suspend_provider: true
  │   Provider status → SUSPENDED
  │   New requests not routed to this provider
  │   Active realizations enter PENDING_REVIEW state
  ▼ Recovery Policy evaluates affected entities:
      Entities currently hosted at provider: notify Tenant owners
      In-progress operations: depends on Recovery Policy profile
```

---

## 10. Schema sharing declaration

Per the UDLM compatibility model, DCM declares its chosen mechanism in its
schema bundle so federated peers can verify and interoperate:

```yaml
# Excerpt from DCM's schema bundle published per udlm/contracts/schema-sharing.md
provider_callback_auth:
  contract_version: 1.0
  layer_1_mechanism: mtls
  layer_2_mechanism: interaction_credential
  layer_1_protocol_refs:
    - rfc_5280  # X.509 PKI
    - rfc_8446  # TLS 1.3
  layer_2_credential_type: dcm_interaction
  layer_2_format: bearer_token
  layer_2_transport: Authorization HTTP header
```

A federated peer that picks a different mechanism (e.g., JWT + signed
assertion) declares its mechanism similarly; cross-peer federation
negotiation includes mechanism compatibility checks.

---

## 11. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `PCA-001-DCM` | All DCM provider calls present both valid mTLS (Layer 1) and valid interaction credential (Layer 2); neither alone is sufficient |
| `PCA-002-DCM` | Interaction credentials are scoped to provider_uuid; cannot act on entities at other providers |
| `PCA-003-DCM` | Entity-level authorization checked on every realized_state_push, update_notification, and lifecycle_event call independent of credential validity |
| `PCA-004-DCM` | Five consecutive scope or IP binding violations within PT1H triggers automatic provider suspension and admin notification |
| `PCA-005-DCM` | Interaction credentials issued by the Credential Management Service — the authoritative source for all issuance, rotation, and revocation |
| `PCA-006-DCM` | Registration tokens are single-use; a token used once is permanently invalidated regardless of expires_at |
| `PCA-007-DCM` | Re-registration changing sovereignty declaration requires a new registration token and new approval pipeline; version/capability updates do not |
| `PCA-008-DCM` | Interaction credentials must be rotated before expiry; expired without rotation → CREDENTIAL_EXPIRED; provider must obtain new via platform admin |
| `PCA-009-DCM` | For fsi/sovereign, interaction credentials are IP-bound; mismatched IP → rejected regardless of validity |
| `PCA-010-DCM` | All inbound provider calls — including rejected — produce an audit record; no silent failures |
