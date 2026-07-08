---
Document Status: ✅ Stable — DCM implementation
Document Type: Reference — Implementation Standards
Established: 2026-05-26
Maps to: udlm/reference/standards-catalog.md
---

# DCM Implementation Standards

> **Selects implementations of the standards listed in UDLM**:
> [udlm/reference/standards-catalog.md](https://github.com/croadfeldt/udlm/blob/main/reference/standards-catalog.md).
> UDLM lists the normative external standards that any DCM-conformant
> realization must consume. This document records the specific
> implementation choices DCM makes: which algorithms, which protocol
> implementations, which OpenAPI conventions, which observability stack,
> which K8s integration, and which compliance configurations per profile.

---

## 1. Cryptographic implementation details

DCM selects specific algorithms from the UDLM-approved set, profile-governed.

### 1.1 Algorithm choices by credential type

| Credential type | Algorithm | Key size | Profile |
|---|---|---|---|
| `api_key` | Cryptographically random | 256 bits min | All |
| `x509_certificate` | Ed25519 (preferred) | 256-bit | standard/prod |
| `x509_certificate` | ECDSA P-384 | 384-bit | fsi/sovereign (FIPS) |
| `x509_certificate` | RSA-4096 | 4096-bit | Permitted for compatibility |
| `ssh_key` | Ed25519 (preferred) | 256-bit | standard/prod |
| `ssh_key` | ECDSA P-384 | 384-bit | fsi (FIPS) |
| `service_account_token` | ES256 (preferred) | P-256 | standard/prod |
| `service_account_token` | RS256 | RSA 4096 | Compatibility |
| `database_password` | Cryptographically random | 128-bit printable | standard |
| `database_password` | Cryptographically random | 256-bit | fsi/sovereign |
| `dcm_interaction` | HS256 or ES256 | 256-bit | All |
| `hsm_backed_key` | ECDSA P-384 | HSM-generated | fsi/sovereign |

### 1.2 Forbidden algorithms (all profiles)

DCM rejects credentials using these at issuance regardless of profile:

- MD5, SHA-1
- DES, 3DES
- RC4
- RSA < 2048
- ECDSA curves weaker than P-256
- DSA-1024

The negative list applies even in `minimal`/`dev` — real attacks hit all
deployments. Homelab is not exempt.

### 1.3 Hash and integrity

| Use | Algorithm | Profile |
|---|---|---|
| Audit hash chain | SHA-256 | All (minimum) |
| Audit hash chain | SHA-384 / SHA-512 | fsi/sovereign (preferred) |
| TLS cipher suites | per RFC 8446 (TLS 1.3 mandatory) | All |
| Audit signing | Ed25519 or ECDSA P-384 | All |

### 1.4 Symmetric encryption

| Use | Algorithm | Profile |
|---|---|---|
| Credential at-rest | AES-256-GCM | standard+ |
| Credential at-rest | AES-128-GCM permitted | minimal/dev (performance trade) |
| Pipeline payload encryption | AES-256-GCM (envelope) | All |
| Audit record encryption | AES-256-GCM (sovereign) | sovereign |

### 1.5 FIPS level per profile

| Profile | FIPS 140 level |
|---|---|
| `minimal` | None required |
| `dev` | None required |
| `standard` | None required |
| `prod` | Level 1 (software-only acceptable) |
| `fsi` | Level 2 (role-based authentication) |
| `sovereign` | Level 3 (physical tamper evidence + identity-based auth) |

---

## 2. Certificate and key management procedures

### 2.1 Internal CA (built-in)

DCM ships with an internal CA that issues mTLS certificates to control plane
components. Default configuration:

```yaml
internal_ca:
  algorithm: ECDSA-P-384
  certificate_lifetime: P90D       # rotates quarterly
  ca_root_lifetime: P10Y           # long-lived; offline backup
  ocsp_endpoint: /api/v1/internal/ocsp
  crl_endpoint: /api/v1/internal/crl
  bootstrap_token_lifetime: PT24H  # for new component enrollment
```

The CA root is stored in DCM's internal secrets table with HSM-backed
encryption in `fsi`/`sovereign` profiles.

### 2.2 External CA integration (recommended for fsi/sovereign)

DCM supports replacing the internal CA with an external enterprise CA via
the Credential Provider model. Supported protocols:

| Protocol | RFC | Implementations |
|---|---|---|
| ACME | RFC 8555 | Let's Encrypt, cert-manager, Venafi, DigiCert |
| EST | RFC 7030 | Cisco CA, Microsoft NDES, Venafi |
| SCEP | RFC 8894 | Microsoft NDES, Cisco iOS CA |
| CMP | RFC 4210 | EJBCA, OpenXPKI |
| Native API | — | HashiCorp Vault PKI, AWS ACM PCA, Azure Key Vault |

This makes DCM's internal mTLS fully auditable through existing enterprise
PKI infrastructure — a key requirement for fsi/sovereign profiles.

### 2.3 Certificate rotation

- Internal CA-issued certs rotate at P90D (default); P30D in fsi/sovereign
- External CA-issued certs rotate per CA's protocol (ACME orders are
  short-lived; EST/SCEP follow enterprise schedule)
- Rotation overlap window: P7D — both old and new certs accepted during
  the window
- Pre-expiry warning: P14D before expiry

### 2.4 OCSP and CRL

- Internal CA exposes OCSP per RFC 6960 with `ocsp_stapling: true`
- CRL refresh: PT5M cache (standard); PT1M (fsi); PT30S (sovereign)
- External CA OCSP/CRL endpoints consumed via standard PKI library

---

## 3. Authentication protocol integration

### 3.1 OIDC implementation

DCM uses standard OIDC discovery via the `/.well-known/openid-configuration`
endpoint. ID tokens validated per RFC 7519. Claims mapping configurable per
Auth Provider registration:

```yaml
claims_mapping:
  username:    preferred_username
  email:       email
  display_name: name
  groups:      groups            # mapped to DCM roles per group_role_map
  department:  department         # custom claim
  cost_center: cost_center        # custom claim
```

### 3.2 LDAP/AD implementation

- RFC 4511 LDAP v3
- StartTLS (RFC 4513) or LDAPS (port 636) — mandatory in standard+
- Bind operation for authentication
- Group membership via `member` attribute or RFC 4510 `LDAP_MATCHING_RULE_IN_CHAIN`
  (1.2.840.113556.1.4.1941) for AD nested group resolution
- Connection pooling; idle timeout PT5M; max idle conns: 10 per pool

### 3.3 SCIM 2.0 implementation

- RFC 7643 (Core Schema) + RFC 7644 (Protocol)
- Endpoint: `/scim/v2/Users` and `/scim/v2/Groups`
- Bearer-token authenticated; token rotation per AUTH-014
- Deprovision (DELETE /Users/{id}) triggers AUTH-016 (session revoke) +
  CPX-006 (credential revoke) in parallel
- Roles NOT SCIM-provisioned — explicit DCM policy authorization required

### 3.4 SAML 2.0 (optional)

- OASIS SAML 2.0 assertion parsing
- Signing cert + encryption cert via Credential Management Service
- AttributeStatement → DCM claims mapping

### 3.5 OAuth 2.0 (RFC 6749)

- Authorization Code flow for OIDC Auth Providers
- Client Credentials flow for service account API keys
- Token introspection per RFC 7662 at `POST /api/v1/auth:introspect`

---

## 4. OpenAPI implementation specifics

DCM uses OpenAPI 3.1 (OpenAPI Initiative 3.1) for all REST APIs.

### 4.1 API specification locations

| API | Spec file |
|---|---|
| Consumer API | `schemas/openapi/dcm-consumer-api.yaml` |
| Admin API | `schemas/openapi/dcm-admin-api.yaml` |
| Provider Callback API | `schemas/openapi/dcm-provider-callback-api.yaml` |
| Operator Interface | `schemas/openapi/dcm-operator-api.yaml` |

### 4.2 Endpoint conventions

DCM follows [AEP (API Enhancement Proposals)](https://aep.dev) conventions:

- Resource-oriented URLs: `/api/v1/{resource_collection}/{resource_id}`
- Custom methods use colon syntax: `/api/v1/requests/{uuid}:cancel`
- Async operations return Operation resources for long-running work
- Pagination: `page_size` + `page_token` (cursor-based)
- Filtering: `filter` query param with simple expression language
- Field masks: `fields` query param for partial response

### 4.3 Versioning headers

- `Sunset` header (RFC 8594) on deprecated endpoints
- `Deprecation` header (RFC 9745) paired with Sunset
- `Link: rel="successor-version"` on deprecated responses
- Version negotiation via `Accept: application/vnd.dcm.v2+json`

### 4.4 Error format

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Resource type Compute.VirtualMachine version 2.0.0 not active",
    "details": {
      "resource_type": "Compute.VirtualMachine",
      "version": "2.0.0",
      "current_version": "1.5.3"
    },
    "request_id": "<uuid>",
    "documentation_url": "https://docs.dcm-project/errors/VALIDATION_FAILED"
  }
}
```

---

## 5. Observability implementation

### 5.1 Metrics (Prometheus / OpenMetrics)

DCM exposes Prometheus exposition format at `GET /metrics` on each control
plane component. Standard metric families:

| Family | Description |
|---|---|
| `dcm_requests_total` | Counter — requests by tenant, resource_type, status |
| `dcm_requests_duration_seconds` | Histogram — request pipeline duration |
| `dcm_provider_health_status` | Gauge — 1=healthy, 0=unhealthy per provider |
| `dcm_policy_evaluation_seconds` | Histogram — policy evaluation duration |
| `dcm_placement_decisions_total` | Counter — placement outcomes by provider |
| `dcm_audit_records_total` | Counter — audit volume |
| `dcm_credential_operations_total` | Counter — by operation type, profile |
| `dcm_realized_entities` | Gauge — current entities by resource_type, tenant |

Metrics are scraped by Prometheus; profile-governed visibility (some sensitive
metrics hidden in `sovereign` per HLT-005).

### 5.2 Distributed tracing (OpenTelemetry)

DCM emits OTel spans for the request pipeline:

| Span | Parent |
|---|---|
| `dcm.request.submit` | — (root) |
| `dcm.request.assemble` | dcm.request.submit |
| `dcm.policy.evaluate` | dcm.request.assemble |
| `dcm.scoring.compute` | dcm.policy.evaluate |
| `dcm.placement.decide` | dcm.request.assemble |
| `dcm.provider.dispatch` | dcm.request.assemble |
| `dcm.provider.callback` | — (linked via X-DCM-Correlation-ID) |
| `dcm.realized.persist` | dcm.provider.callback |

`X-DCM-Correlation-ID` header propagated across all service boundaries;
maps to the OTel trace ID for cross-service tracing.

### 5.3 Logging

- Structured JSON logs at all log levels
- `correlation_id`, `request_id`, `actor_uuid`, `tenant_uuid` in every log
  entry
- Log levels: `error`, `warn`, `info`, `debug`
- Profile defaults: `info` for standard+, `debug` for dev/minimal
- Log aggregation: not prescribed (Loki, Elasticsearch, Splunk all supported)

### 5.4 Health endpoints

- `/livez` — process liveness; unauthenticated
- `/readyz` — ready to serve traffic; unauthenticated
- `/api/v1/admin/health` — detailed component health; authenticated
- `/api/v1/admin/health/dependencies` — external dependency status

Format: IANA `application/health+json` per RFC 8615.

---

## 6. Kubernetes integration

DCM is designed for K8s deployment but does not require it. K8s-specific
features when deployed on K8s:

### 6.1 K8s manifests

- Deployment / StatefulSet per control plane component
- Service for internal service discovery
- HorizontalPodAutoscaler for stateless services
- PodDisruptionBudget for stateful components
- NetworkPolicy for component-to-component allowed paths
- ServiceAccount per component with minimum-necessary RBAC

### 6.2 CRD-based DCM Operator

Optional DCM Operator translates DCM artifacts to/from K8s CRDs:

| CRD | DCM artifact |
|---|---|
| `DCMRequest` | Resource request (consumer-friendly K8s-native intent) |
| `DCMPolicy` | Policy artifact |
| `DCMProvider` | Provider registration |
| `DCMTenant` | Tenant configuration |

CRDs enable `kubectl apply -f` workflow as an ingress alongside the API.

### 6.3 Probes

- Liveness probe: `GET /livez` every PT10S; failureThreshold 3
- Readiness probe: `GET /readyz` every PT5S; failureThreshold 1
- Startup probe: `GET /livez` every PT5S; failureThreshold 12 (PT60S total)

### 6.4 Service mesh integration

Optional service mesh (Istio, OpenShift Service Mesh, Linkerd) replaces
application-level TLS for internal component communication. DCM's
implementation-specifications.md documents the recommended mesh config.

---

## 7. Compliance configuration

DCM ships profile-specific compliance overlays. Per profile, the following
standards are enforced:

### 7.1 Profile → compliance mapping

| Profile | Standards |
|---|---|
| `minimal` | None enforced |
| `dev` | None enforced |
| `standard` | ISO 27001 (advisory); SOC 2 (advisory) |
| `prod` | ISO 27001; SOC 2 Type II; NIST 800-53 (Moderate baseline advisory) |
| `fsi` | All of prod + PCI DSS overlay + HIPAA overlay (when active) + FedRAMP Moderate + DoD IL4 + FIPS 140-2 Level 2 |
| `sovereign` | All of fsi + sovereign-specific overlay + FIPS 140-3 Level 3 + air-gapped enforcement |

### 7.2 Compliance overlay activation

Compliance domains are activated additively:

```yaml
active_profile: prod
active_compliance_domains: [hipaa, pci_dss]
```

DCM applies the union of profile defaults and all active compliance domain
overlays. Compliance overlays always tighten (never relax) the base profile
(`CPX-011`).

### 7.3 Standard-to-DCM-feature mapping

| Standard | DCM features |
|---|---|
| NIST SP 800-53 | Policy domains map to control families; access control, audit, configuration management |
| FedRAMP Moderate | Profile `fedramp_moderate`; NIST baseline; FIPS 140-2 Level 1+ |
| FedRAMP High | Profile `fedramp_high`; NIST baseline; FIPS 140-2 Level 2+; enhanced audit retention |
| DoD IL4 | Profile `dod_il4`; FIPS 140-2 Level 2; hardware attestation; enhanced logging |
| PCI DSS v4 | Req 8.3.9: P90D max credential rotation enforced; segmentation via sovereignty; cardholder data logging; 12-month audit retention |
| HIPAA | Profile `fsi` or `hipaa` overlay; PHI access logging; minimum necessary RBAC; transmission security TLS 1.2+; workforce MFA |
| SOC 2 | profile standard+; Type II audit trail; availability/security/confidentiality; GitOps change management |
| ISO 27001 | All profiles; risk-based approach; asset management; access control; cryptography |
| GDPR | Sovereignty constraints; data classification; right to erasure (entity decommission + audit retention) |
| Schrems II | Sovereignty + federation boundaries; data transfer restrictions |

### 7.4 Authentication Assurance Levels (NIST SP 800-63B)

DCM maps profiles to AAL:

| Profile | AAL | Requirements |
|---|---|---|
| `minimal` | AAL1 | Single-factor; password or API key |
| `dev` | AAL1 | Single-factor |
| `standard` | AAL2 | MFA required for actor sessions |
| `prod` | AAL2 | MFA required; TOTP, FIDO2, or hardware token |
| `fsi` | AAL2+ | MFA required; phishing-resistant (FIDO2/hardware) |
| `sovereign` | AAL3 | Hardware-based authenticator; verifier impersonation resistance |

---

## 8. ITSM integration standards

| Standard | Use | Obligation |
|---|---|---|
| ServiceNow REST Table API | Primary ServiceNow integration | Normative for ServiceNow provider |
| Jira REST API v3 | Primary Jira Service Management | Normative for Jira provider |
| BMC AR REST API v1 | BMC Remedy/Helix ITSM | Normative for BMC provider |
| PagerDuty Events API v2 | Incident creation for alert-type integrations | Normative for PagerDuty |
| HMAC-SHA256 | Inbound webhook signature verification | Normative |
| ITIL v4 Change Management | DCM change record lifecycle mapping | Informative |
| JSON:API | Several ITSM REST APIs response formatting | Informative |
| JSONPath | Template expression for `generic_rest` action payloads | Normative for generic_rest |

See [`../architecture/integrations/itsm.md`](../architecture/integrations/itsm.md)
for the ITSM integration implementation.

---

## 9. CNCF ecosystem

DCM is designed for CNCF ecosystem compatibility:

| Project | CNCF Status | DCM Use |
|---|---|---|
| Kubernetes | Graduated | Deployment target; DCM Operator |
| Open Policy Agent (OPA) | Graduated | Policy evaluation engine; Rego for Gating Policy, Validation |
| Prometheus | Graduated | Metrics exposition |
| OpenTelemetry | Graduated | Distributed tracing; correlation ID propagation |
| Istio | Graduated | Optional service mesh for internal mTLS |
| Argo CD / Flux | Graduated | GitOps delivery for DCM layers/policies |

---

## 10a. Identifier implementation (UUID — RFC 9562)

DCM realizes udlm `contracts/identifier-scheme.md` §2.1 (normative). Implementation requirements:

- **Generation:** entity/artifact identity = **UUIDv4** from the platform CSPRNG
  (`uuid.uuid4()`, `crypto.randomUUID()`, `gen_random_uuid()`); audit-chain leaves and event ids =
  **UUIDv7** (RFC 9562 §5.7) for index locality + total order. No other versions are ever minted.
- **Validation at ingest (every API boundary):** reject malformed UUIDs and prohibited versions —
  check the version nibble AND variant bits
  (`^[0-9a-f]{8}-[0-9a-f]{4}-[47][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`, version per field
  schema). Error: `validation.identifier_invalid`.
- **Canonical form everywhere:** lowercase hyphenated, no braces, no `urn:` prefix — normalize on
  write, compare case-insensitively never (storage is already canonical).
- **Storage:** native `uuid` column type where the store supports it (Postgres `uuid`,
  `gen_random_uuid()` default for v4); never store as free text.
- **Resolution:** cross-entity references resolve by `uuid` (authoritative); `handle` is advisory
  display/lookup sugar and every handle change is audited (identifier-scheme §2.2). Resolution by
  name alone is a conformance violation (udlm SPEC-DESIGN hard constraint 30).
- **Lifecycle:** uuids are minted exactly once, survive tenant/realization migration, remain
  resolvable after `retired` (tombstone, DEP-007), and are NEVER reused (identifier-scheme §5).

## 10. Policy-family-to-standard mapping (DCM realization)

| Policy family | Standards basis |
|---|---|
| `AUTH-001-DCM` through `AUTH-015-DCM` | RFC 6749, RFC 7519, OIDC Core, NIST SP 800-63B, RFC 7643/7644 |
| `SES-001-DCM` through `SES-005-DCM` | RFC 7662, RFC 7009, OAuth 2.0 best practices |
| `CPX-001-DCM` through `CPX-012-DCM` | FIPS 140-2/3, RFC 5280, RFC 8555/7030/8894/4210, NIST SP 800-57 |
| `ATM-001-DCM` through `ATM-012-DCM` | ISO 27001 change management |
| `EVT-001-DCM` through `EVT-007-DCM` | OpenTelemetry, CNCF event-driven best practices |
| `VER-001-DCM` through `VER-009-DCM` | RFC 8594, RFC 9745, industry API lifecycle |
| `ICOM-001-DCM` through `ICOM-009-DCM` | RFC 8446, RFC 5280, SPIFFE conceptual, FIPS 140 |
| `HLT-001-DCM` through `HLT-006-DCM` | RFC 8615, K8s probe conventions, Prometheus OpenMetrics |
| `ZTS-001-DCM` through `ZTS-005-DCM` | Zero Trust Architecture (NIST SP 800-207), NIST SP 800-63B |

The full list of policy IDs lives in each subsystem document under
`../architecture/`.
