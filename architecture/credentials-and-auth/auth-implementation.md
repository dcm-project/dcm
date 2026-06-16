---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Authentication Implementation
Established: 2026-05-26
Maps to: udlm/governance/auth-providers.md
---

# Authentication Implementation

> **Implements contracts defined in UDLM**:
> [udlm/governance/auth-providers.md](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md).
> UDLM defines the Auth Provider taxonomy (built-in, static API key, local
> users, GitHub/GitLab OAuth, LDAP, FreeIPA, AD, OIDC, SAML, mTLS, SCIM 2.0),
> the multi-provider authentication contract, and the credential
> types/issuance taxonomy. DCM operationalizes the implementation: library
> choices, integration mechanics, routing logic, session management, and
> token lifecycle.

---

## 1. Authentication implementation within DCM

The DCM API Gateway is the single ingress for all authenticated requests. It
performs the following on every request:

1. Extract the authentication signal (mTLS cert, Bearer token, Basic auth,
   HMAC signature)
2. Route to the appropriate registered Auth Provider per the resolution order
3. Validate the credential through the provider
4. Resolve the actor's roles, groups, and tenant scope
5. Inject `X-DCM-Tenant`, `X-DCM-Actor-Uuid`, `X-Request-ID` headers for
   downstream services
6. Apply rate limiting per the authenticated actor

The Built-in Auth Provider ships with DCM and is always registered. It
provides static API key, local user/password, and optional GitHub/GitLab
OAuth (opt-in via configuration).

### 1.1 Library and protocol choices

| Mechanism | DCM library / protocol |
|---|---|
| OIDC / OAuth 2.0 | Standard OIDC discovery + JWKS endpoint validation; ID token format per RFC 7519 |
| SAML 2.0 | OASIS SAML 2.0 assertion parsing; optional Auth Provider type |
| LDAP / FreeIPA / AD | RFC 4511 LDAP v3; bind operation for authentication; group membership via filter (LDAP_MATCHING_RULE_IN_CHAIN for AD nested groups) |
| Kerberos (FreeIPA SSO) | GSSAPI; keytab-based service principal |
| mTLS | RFC 5280 X.509 chain validation; CN → actor mapping |
| SCIM 2.0 | RFC 7643/7644 endpoints at `/scim/v2/Users` and `/scim/v2/Groups` |
| Local users | argon2id password hashing; SQLite (minimal/dev) or PostgreSQL (standard+) backend |
| Sessions | RFC 7519 JWT for stateless session tokens; refresh tokens stored in DB |

### 1.2 Internal vs External mode

DCM follows the same Internal/External pattern as policy evaluation and
secrets management:

- **Internal mode (default):** local user accounts in the `actors` table;
  passwords as argon2id hashes; DCM-issued JWT session tokens with
  configurable expiry. Zero external dependencies — bootstrap with a local
  admin account and start.
- **External mode (optional):** register one or more `auth_provider`
  instances; DCM validates their tokens, extracts claims, maps groups to
  DCM roles. Multiple providers enable tenant-routed authentication
  (Tenant A through AD, Tenant B through Okta).

External Auth Providers register through the standard provider registration
contract with `provider_type: auth_provider` and capability declaration.

---

## 2. Credential Management Service integration

DCM never stores credentials directly. The Built-in Auth Provider's secret
storage uses the same envelope encryption mechanism as DCM internal secrets:

| KEK source | Profile |
|---|---|
| Environment variable | minimal, dev (homelab) |
| Kubernetes Secret | standard, prod |
| HSM via PKCS#11 | fsi, sovereign |

For external Auth Providers, DCM resolves bind passwords, OAuth client
secrets, SAML signing certificates, and all other secrets via the registered
Credential Management Service (see
[`credentials.md`](credentials.md)).

### 2.1 Secret references

Every Auth Provider configuration references secrets, never embeds them:

```yaml
auth_provider:
  provider_type: freeipa
  config:
    bind_password_ref:
      service_provider_uuid: <uuid>
      secret_path: "dcm/auth/freeipa/bind-password"
```

DCM resolves the reference at runtime via the Credential Management Service.
Plaintext credentials in registration payloads are rejected (`AUTH-007`).

---

## 3. Provider authentication routing logic

The API Gateway routes incoming requests to the appropriate Auth Provider
based on the authentication signal:

```yaml
auth_provider_resolution:
  resolution_order:
    - signal: mtls_client_cert
      provider_uuid: <mtls-provider-uuid>
    - signal: bearer_token_oidc
      provider_uuid: <corporate-oidc-uuid>
    - signal: bearer_token_apikey
      provider_uuid: <api-key-provider-uuid>
    - signal: basic_auth
      provider_uuid: <freeipa-ldap-uuid>
    - signal: hmac_signature
      provider_uuid: <webhook-auth-provider-uuid>
    - signal: none
      action: reject                        # always — no anonymous access
```

The resolution order is declared in DCM configuration; the API Gateway walks
it on every request. The first match wins.

### 3.1 Auth Provider chain (enrichment + augmentation)

A request can authenticate with one provider and enrich claims via another:

```yaml
auth_provider_chain:
  authentication:
    provider_uuid: <freeipa-ldap-uuid>     # fast LDAP bind
  enrichment:
    provider_uuid: <freeipa-ldap-uuid>     # LDAP group membership
  augmentation:
    provider_uuid: <corporate-oidc-uuid>   # OIDC userinfo for rich claims (dept, cost_center, project codes)
```

The API Gateway invokes each stage; failure at enrichment or augmentation is
logged but does not block the request unless the active profile requires
all stages to succeed (`fsi`/`sovereign`).

### 3.2 Failover behavior (AUTH-013)

When an Auth Provider becomes unhealthy:

- **In-flight requests** authenticated before the failure continue using
  cached session tokens
- **New requests** follow the declared failover chain
- **Session expiry during outage** requires re-authentication via available
  failover provider; if all providers unavailable → reject with clear error

```yaml
auth_failover_config:
  primary_provider_uuid: <ldap-uuid>
  failover_chain:
    - provider_uuid: <oidc-backup-uuid>
      promotion_delay: PT30S
    - provider_uuid: <local-users-uuid>
  session_cache:
    enabled: true
    ttl: PT8H
```

---

## 4. Session management and token lifecycle

DCM issues its own session tokens (JWT) for actors authenticated through any
Auth Provider. Session tokens carry: `actor_uuid`, `roles`, `tenant_scope`,
`auth_provider_uuid`, `exp`, `iat`.

### 4.1 Session configuration

```yaml
session:
  token_ttl: PT8H              # per-profile default
  refresh_enabled: true
  refresh_ttl: P7D
  concurrent_sessions: 3       # max per actor; enforced via session_store
```

The `sessions` table stores active session metadata; revocation is a status
update. Token introspection per RFC 7662 is exposed at
`POST /api/v1/auth:introspect`.

### 4.2 MFA enforcement (AUTH-014)

DCM implements two-tier MFA:

- **Per-session MFA:** validated at login; captured in the JWT `mfa_verified` claim
- **Step-up MFA:** additional challenge at sensitive operations within an
  already-authenticated session; results in a short-lived (PT10M) step-up
  token

```yaml
step_up_mfa_config:
  step_up_required_for:
    - platform_policy_activate
    - provider_decommission
    - tenant_decommission
    - sovereignty_zone_change
    - auth_provider_update
    - manual_rehydration
  step_up_method: totp | push_notification | hardware_token | sms
  step_up_token_ttl: PT10M
  step_up_challenge_max_age: PT5M
```

Profile defaults govern which operations require step-up:

| Profile | Per-Session MFA | Step-Up Required |
|---|---|---|
| minimal | No | No |
| dev | No | No |
| standard | Recommended | Optional |
| prod | Required | Destructive operations |
| fsi | Required | All policy changes |
| sovereign | Required (hardware token) | All administrative operations |

### 4.3 Session revocation

Session revocation follows the SES-001 model (in
[`../control-plane/session-revocation.md`](../control-plane/session-revocation.md)).
Triggers include actor deprovisioning, manual admin revocation, password
change, and security event.

When a session is revoked, the Auth Implementation:

1. Marks the session row status: `revoked`
2. Publishes `session.revoked` event to `pipeline_events`
3. All Policy Manager and API Gateway instances invalidate their permission
   cache entries for the actor

### 4.4 SCIM 2.0 deprovisioning

When SCIM signals an actor deprovision:

1. Actor's session(s) revoked immediately
2. All credentials issued to actor revoked (per `CPX-006`)
3. In-flight requests complete on cached tokens; new requests rejected
4. Audit record written with `source: scim_deprovision`

The SCIM endpoint at `/scim/v2/Users/{id}` (DELETE) triggers
`AUTH-016`/`SES-001`/`CPX-006` in parallel.

---

## 5. Git PR actor identity resolution

When DCM processes Git PR ingress, the Git server's authenticated user must
resolve to the same DCM actor as if they had logged into the web UI:

```
Git server authenticates user → PR merge webhook → DCM Auth Provider resolution → DCM actor
```

DCM trusts the Git server's verified identity assertion — not user-declared
Git config. Resolution methods:

| Method | When |
|---|---|
| `oidc_subject_lookup` | Git server uses same OIDC/OAuth IdP as DCM |
| `ldap_username_lookup` | Git server authenticates via LDAP/AD |
| `ssh_key_fingerprint` | SSH key-authenticated Git workflows |
| `webhook_service_account` | Automated CI/CD Git workflows |

The resolved actor carries identical role, group, and tenant scope to the
same user authenticating via web UI (`AUTH-011`). Git PR ingress does not
grant different permissions than any other ingress surface.

---

## 6. Authentication ladder (DCM realization)

Every rung is authenticated. The ladder is about setup effort — not whether
authentication exists.

| Profile | Modes available | Setup effort |
|---|---|---|
| `minimal` | Static API key, Local user/password | 30 seconds – 2 minutes |
| `dev` | + GitHub/GitLab OAuth, FreeIPA/AD direct bind | 5–15 minutes |
| `standard` | + OIDC via broker (Dex/Keycloak), AD/FreeIPA direct | 30–60 minutes |
| `prod` | + OIDC direct, MFA | 1–2 hours |
| `fsi` | + mTLS required, MFA required | 4–8 hours |
| `sovereign` | + Air-gapped OIDC/mTLS | 1–2 days |

### 6.1 Built-in Auth Provider storage backend (AUTH-015)

```yaml
builtin_auth_provider_config:
  user_store:
    profile_defaults:
      minimal: sqlite            # zero infrastructure; single-file
      dev: sqlite
      standard: postgresql
      prod: postgresql
      fsi: postgresql            # encrypted (TDE required)
      sovereign: postgresql      # HSM-backed encryption required
    encryption_at_rest:
      required_profiles: [fsi, sovereign]
      key_ref:
        service_provider_uuid: <uuid>
        path: "dcm/auth/builtin/encryption-key"
```

The local user store should only contain: bootstrap users, service accounts,
and API key holders. Enterprise users belong in external Auth Providers
(LDAP, OIDC, SCIM).

---

## 7. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `AUTH-001-DCM` | All DCM authentication is handled through a registered Auth Provider; the built-in is always available |
| `AUTH-002-DCM` | DCM routes to the appropriate Auth Provider based on the authentication signal in the request |
| `AUTH-005-DCM` | When an Auth Provider becomes unhealthy, existing sessions remain valid until TTL expiry; new auth follows failover chain or is rejected |
| `AUTH-006-DCM` | DCM records the Auth Provider used in the ingress block and carries it into the audit record |
| `AUTH-007-DCM` | DCM rejects Auth Provider configurations containing plaintext credentials; secret references required |
| `AUTH-008-DCM` | DCM permits no anonymous access in any profile; minimal/dev support lightweight authenticated modes |
| `AUTH-009-DCM` | DCM always requires authentication on webhook and message bus inbound surfaces regardless of profile |
| `AUTH-010-DCM` | DCM enforces rate limiting per authenticated actor; limits declared on Auth Provider or webhook registration |
| `AUTH-011-DCM` | DCM resolves Git PR actor identity through the registered Auth Provider; resolved actor carries same role/group/tenant scope as web UI authentication |
| `AUTH-013-DCM` | In-flight requests continue on cached tokens during Auth Provider outage; new auth follows failover chain |
| `AUTH-014-DCM` | DCM enforces two-tier MFA: per-session (mfa_verified claim) and step-up (short-lived token) for sensitive operations per policy |
| `AUTH-015-DCM` | DCM's built-in Auth Provider uses SQLite for minimal/dev, PostgreSQL for standard+; encryption-at-rest required in fsi/sovereign |
