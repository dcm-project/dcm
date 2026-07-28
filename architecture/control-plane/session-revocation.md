---
Maps to: udlm/governance/auth-providers.md
---

# DCM Data Model — Session Token Revocation

> **Implements contracts defined in UDLM**:
> [udlm/governance/auth-providers.md](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md).
> UDLM defines the Auth Provider model and authenticated-session contract. This document
> extends that model with the explicit session-token revocation lifecycle, triggers, and
> the Session Revocation Registry that UDLM leaves unspecified.

**Document Status:** ✅ Complete
**Document Type:** Architecture Reference — Session Lifecycle and Revocation
**Related Documents:** [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md) | [Accreditation and Zero Trust](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) | [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md) | [Design Priorities](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md)

> **This document maps to: DATA + POLICY**
>
> A session is a Data artifact with a UUID, lifecycle state, and audit trail. Session revocation is a Policy concern — it fires on triggers defined here and enforced by the Auth Provider and Ingress layer. This document extends the Auth Provider model ([auth-providers.md](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md)) with the explicit revocation lifecycle that was previously unspecified.
>
> **Relationship to credential revocation:** CPX-006 ([credentials.md](../credentials-and-auth/credentials.md)) governs credential revocation — when an actor is deprovisioned, all credentials issued to that actor are revoked. This document governs the complementary concern: active *session tokens* must also be invalidated on the same trigger. Credential revocation and session revocation are parallel processes that both fire on actor deprovisioning.

---

## 1. What a Session Is

A DCM session represents an authenticated actor's active interaction context. It is created when an actor successfully authenticates through an Auth Provider and is destroyed (or expires) when the session ends.

```yaml
session_record:
  session_uuid: <uuid>
  actor_uuid: <uuid>
  auth_provider_uuid: <uuid>           # which provider issued the session
  auth_method: oidc | ldap | api_key | mtls | built_in
  mfa_verified: <bool>                 # whether per-session MFA was completed
  step_up_verified_at: <ISO 8601 | null>  # last step-up MFA completion
  
  created_at: <ISO 8601>
  last_active_at: <ISO 8601>
  expires_at: <ISO 8601>               # absolute expiry (from token_ttl)
  
  refresh_token_uuid: <uuid | null>    # if refresh_enabled: true
  refresh_expires_at: <ISO 8601 | null>
  
  status: active | refreshing | revoked | expired
  revocation_reason: <string | null>
  revoked_at: <ISO 8601 | null>
  revoked_by: <actor_uuid | system | null>
  
  # Provenance
  client_ip: <IP | null>
  user_agent: <string | null>
  tenant_uuid: <uuid | null>
  
  # Concurrent session position
  session_sequence: <int>              # 1 = oldest active session for this actor
```

### 1.1 Session Store

Active sessions are maintained in a **Session Store** — a fast-queryable, low-latency store separate from the Realized State Store. The Session Store is not GitOps-backed; it is operational state that does not need version history.

```yaml
session_store:
  implementation: redis | postgres | in_memory   # profile-governed
  ttl_enforcement: hard                          # sessions expire at expires_at regardless
  revocation_index: true                         # fast lookup by session_uuid for revocation
  actor_index: true                              # fast lookup by actor_uuid for bulk revocation
```

**Profile-governed defaults:**

| Profile | Store | Session TTL | Refresh TTL | Max concurrent |
|---------|-------|-------------|-------------|---------------|
| `homelab` | in_memory or sqlite | PT8H | P7D | unlimited |
| `dev` | redis or postgres | PT4H | P3D | 10 |
| `standard` | redis or postgres | PT1H | P1D | 5 |
| `prod` | redis or postgres | PT30M | PT8H | 3 |
| `fsi` | redis or postgres | PT15M | PT1H | 2 |
| `sovereign` | redis or postgres (HSM-backed) | PT15M | PT30M | 1 |

---

## 2. Revocation Triggers

Session revocation invalidates a session immediately — regardless of its remaining TTL. The following triggers cause revocation:

| Trigger | Scope | Who initiates | Behavior |
|---------|-------|--------------|---------|
| `actor_logout` | Single session | Actor (self) | Immediate; that session only |
| `actor_logout_all` | All sessions for actor | Actor (self) | Immediate; all active sessions for this actor |
| `actor_deprovisioned` | All sessions for actor | SCIM / Platform admin | Immediate; fires before deprovisioning acknowledged |
| `actor_suspended` | All sessions for actor | Platform admin | Immediate |
| `security_event` | Specified sessions or all | Platform admin / security automation | Immediate; emergency channel notification |
| `concurrent_limit_exceeded` | Oldest session(s) | System | Oldest session revoked when new session created beyond limit |
| `auth_provider_deregistered` | All sessions from that provider | Platform admin | Immediate; actors must re-authenticate via another provider |
| `credential_compromised` | All sessions for actor | Security automation | Immediate; correlates with CPX emergency rotation |
| `admin_forced_logout` | Specified session(s) | Platform admin | Immediate |

---

## 3. Revocation Lifecycle

### 3.1 Standard Revocation

```
Revocation trigger fires
  │
  ▼ Session record status → revoked
  │   revoked_at, revocation_reason, revoked_by written
  │
  ▼ Refresh token invalidated (if exists)
  │   Cannot be exchanged; refresh endpoint returns 401
  │
  ▼ Session UUID added to Session Revocation Registry
  │   (fast-queryable; all DCM components check this on every request)
  │
  ▼ Revocation event published to Message Bus
  │   event_type: auth.session_revoked
  │   session_uuid, actor_uuid, revocation_trigger, revoked_at
  │
  ▼ Audit record written
      session_uuid, actor_uuid, revocation_trigger, revoked_by, revoked_at
```

### 3.2 Actor Deprovisioning Revocation (parallel with CPX-006)

Actor deprovisioning fires both credential revocation (CPX-006) and session revocation simultaneously. Neither blocks the other; both must complete before the deprovisioning is acknowledged.

```
Actor deprovisioning initiated
  │
  ├──→ Credential revocation (CPX-006)
  │     All credentials issued to actor_uuid → revoked
  │     Credential Revocation Registry updated
  │
  └──→ Session revocation (this document)
        All active sessions for actor_uuid → revoked
        Session Revocation Registry updated
        auth.session_revoked events published per session
  │
  ▼ Both complete → deprovisioning acknowledged
    actor_deprovisioned event published
    Audit record for deprovisioning written
```

### 3.3 Emergency Revocation (Security Event)

Security events bypass the standard pipeline. Revocation is immediate with no grace period.

```
Security event detected
  │
  ▼ Target sessions determined
  │   (single session, all sessions for actor, or all sessions from a provider)
  │
  ▼ Sessions → revoked immediately
  │   Session Revocation Registry updated within SLA:
  │     standard/prod: PT30S
  │     fsi: PT10S
  │     sovereign: PT5S
  │
  ▼ auth.security_session_revoked event published (critical urgency)
  │   Routed to security team via configured notification service
  │
  ▼ Platform admin notified regardless of profile
  │
  ▼ All in-flight requests from these sessions → 401 Unauthorized
```

---

## 4. Session Revocation Registry

The Session Revocation Registry is the authoritative list of revoked-but-not-yet-expired session UUIDs. Every DCM component that accepts bearer tokens must check this registry on each request.

```yaml
session_revocation_registry:
  # Session UUID → revocation record
  # Fast in-memory cache with TTL equal to original session TTL
  # After the original session TTL would have expired, the entry is
  # removed (the session would have been invalid anyway)
  
  entry:
    session_uuid: <uuid>
    revoked_at: <ISO 8601>
    original_expires_at: <ISO 8601>    # entry removed after this time
    revocation_trigger: <string>
```

**Cache refresh behavior by profile:**

| Profile | Max cache age | Behavior on cache miss |
|---------|--------------|----------------------|
| `homelab` | PT5M | Check authoritative store; cache result |
| `standard` | PT1M | Check authoritative store; cache result |
| `prod` | PT30S | Check authoritative store; cache result |
| `fsi` | PT10S | Check authoritative store; cache result |
| `sovereign` | PT5S | No cache — always check authoritative store |

---

## 5. Token Introspection

DCM's Ingress layer exposes a token introspection endpoint for internal components and external systems that need to validate a token without maintaining their own cache:

```
POST /api/v1/auth:introspect

Authorization: Bearer <api-key-with-introspection-scope>
Content-Type: application/json

{
  "token": "<bearer-token-to-check>"
}

Response 200 (active session):
{
  "active": true,
  "session_uuid": "<uuid>",
  "actor_uuid": "<uuid>",
  "expires_at": "<ISO 8601>",
  "mfa_verified": true,
  "tenant_uuid": "<uuid | null>",
  "roles": ["consumer"],
  "scopes": ["read", "write"]
}

Response 200 (revoked or expired):
{
  "active": false,
  "reason": "revoked | expired | not_found"
}
```

Session tokens use JWT format (RFC 7519). This introspection endpoint follows [RFC 7662 (OAuth 2.0 Token Introspection)](https://datatracker.ietf.org/doc/html/rfc7662).

---

## 6. Consumer API — Session Management Endpoints

### 6.1 Logout (Single Session)

```
DELETE /api/v1/auth/session

Response 204 No Content
```

Revokes the session corresponding to the bearer token in the `Authorization` header. No body required.

### 6.2 Logout All Sessions

```
DELETE /api/v1/auth/sessions

Response 204 No Content
```

Revokes all active sessions for the authenticated actor.

### 6.3 List Active Sessions

```
GET /api/v1/auth/sessions

Response 200:
{
  "items": [
    {
      "session_uuid": "<uuid>",
      "created_at": "<ISO 8601>",
      "last_active_at": "<ISO 8601>",
      "expires_at": "<ISO 8601>",
      "auth_method": "oidc",
      "client_ip": "<IP | null>",
      "current": true    // true for the session making this request
    }
  ],
  "total": 2
}
```

### 6.4 Revoke Specific Session

```
DELETE /api/v1/auth/sessions/{session_uuid}

Response 204 No Content
Response 404: session not found or does not belong to this actor
```

### 6.5 Admin: Force Revoke Session(s)

```
POST /api/v1/admin/actors/{actor_uuid}:revoke-sessions

{
  "scope": "all | session",
  "session_uuid": "<uuid | null>",    // required if scope: session
  "reason": "<string>"               // required for audit trail
}

Response 204 No Content
Response 404: actor not found
```

---

## 7. Concurrent Session Enforcement

When `concurrent_sessions: N` is declared and a new session would exceed the limit, the oldest active session is revoked automatically:

```
New authentication succeeds
  │
  ▼ Count active sessions for actor_uuid
  │   If count >= concurrent_sessions limit:
  │     Revoke oldest session (by created_at)
  │     Trigger: concurrent_limit_exceeded
  │
  ▼ New session created
```

The evicted actor receives an `auth.session_revoked` notification if a notification service is configured with the actor's notification preferences. The event does not block the new session creation.

---

## 8. Relationship to the Credential Revocation Model

Session revocation (this document) and credential revocation ([credentials.md](../credentials-and-auth/credentials.md), CPX-001–CPX-012) are parallel but distinct:

| | Session Revocation | Credential Revocation |
|--|---|---|
| **What** | Bearer token / session cookie validity | API key, x509, SSH key, service account token |
| **Store** | Session Revocation Registry | Credential Revocation Registry |
| **Propagation** | Auth layer cache refresh | Message Bus → all components |
| **Actor deprovision** | All sessions revoked | All credentials revoked |
| **TTL** | Session TTL (minutes to hours) | Credential TTL (hours to years) |
| **Emergency SLA** | PT5S–PT30S | PT30S–PT5M |
| **Event** | `auth.session_revoked` | `credential.revoked` |

**AUTH-016:** On actor deprovisioning, session revocation and credential revocation are parallel operations. The deprovisioning is not acknowledged until both are confirmed complete.

---

## 9. System Policies

| Policy | Rule |
|--------|------|
| `AUTH-016` | On actor deprovisioning, session revocation and credential revocation (CPX-006) are parallel operations. Deprovisioning is not acknowledged until both complete. |
| `AUTH-017` | **SESSION-REGISTRY SLA (owner):** session revocation must propagate to the Session Revocation Registry within the profile-governed SLA: homelab PT5M, dev PT5M, standard PT1M, prod PT30S, fsi PT10S, sovereign PT5S. (Distinct from the credential CACHE-PROPAGATION TTL and PROVIDER-INVALIDATION SLA — credentials.md §5.) |
| `AUTH-018` | All DCM components that accept bearer tokens must check the Session Revocation Registry on each request. Cache age must not exceed the profile-governed maximum (sovereign: no cache). |
| `AUTH-019` | Emergency session revocation (security_event trigger) fires immediately with no grace period. The `auth.security_session_revoked` event has `urgency: critical` and is non-suppressable. |
| `AUTH-020` | The token introspection endpoint (`POST /api/v1/auth:introspect`) must be authenticated. Access requires an actor or service account with the `introspection` scope. |
| `AUTH-021` | When concurrent session limits are enforced, the oldest session is revoked before the new session is created. The evicted actor is notified via notification service if configured. |
| `AUTH-022` | Refresh tokens are invalidated when their parent session is revoked. A revoked refresh token returns 401 on exchange; it cannot be used to create a new session. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
