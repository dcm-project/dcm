---
Maps to: udlm/governance/accreditation-and-authorization-matrix.md
---

# DCM Data Model — Internal Component Authentication

> **Implements contracts defined in UDLM**:
> [udlm/governance/accreditation-and-authorization-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md).
> UDLM defines the five-check boundary model and the "network position grants zero trust"
> principle. This document specifies how DCM applies that boundary model to internal
> control-plane component-to-component authentication.

**Document Status:** ✅ Complete
**Document Type:** Architecture Reference — Zero Trust Internal Auth
**Related Documents:** [Accreditation and Zero Trust](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) | [Deployment and Redundancy](../runtime-features/deployment-redundancy.md) | [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Session Revocation](session-revocation.md) | [Design Priorities](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md)

> **This document maps to: DATA + POLICY**
>
> Internal component identities are Data — each component has a UUID, certificate, and service account. Internal auth is Policy — the same five-check boundary model from doc 26 applies at every internal call boundary, with no exceptions for "trusted internal network." This document specifies how DCM's control plane components authenticate to each other in a distributed deployment.

---

## 1. The Core Principle

**Network position grants zero trust.** This is stated in doc 26 for external interactions. It applies equally to internal component communication. A call from the Policy Engine to the Placement Engine receives the same boundary checks as a call from an external consumer. The service mesh enforces this at the infrastructure level; DCM enforces it at the application level.

**Two-layer enforcement:**
1. **Mesh layer (infrastructure):** mTLS mutual authentication (RFC 8446 TLS 1.3), certificate validation (RFC 5280), traffic policies — enforced by the service mesh (Istio or equivalent)
2. **Application layer (DCM):** component identity verification, operation authorization, scoped interaction credentials — enforced by DCM's Ingress and Auth subsystems

Neither layer alone is sufficient. The mesh layer prevents impersonation at the transport level; the application layer enforces what each component is permitted to do.

---

## 2. Component Identity Model

Every DCM control plane component has a **component identity** — a stable, verifiable identity used for both mTLS and application-layer authorization.

```yaml
component_identity:
  component_uuid: <uuid>           # stable; assigned at deployment time
  component_type: api_gateway | policy_engine | placement_engine | request_orchestrator |
                  scoring_engine | drift_reconciler | lifecycle_enforcer | notification_router |
                  audit_store | session_store | message_bus | service_provider_proxy
  component_name: <string>         # human-readable; e.g. "policy-engine-eu-west-1"
  deployment_uuid: <uuid>          # identifies the DCM deployment instance
  
  # Certificate identity
  mtls_certificate:
    subject: "CN=<component_type>-<component_uuid>,O=dcm-internal"
    san: [<component_uuid>, <component_name>, <internal-dns-name>]
    issuer_ca: <internal_ca_uuid>
    issued_at: <ISO 8601>
    expires_at: <ISO 8601>
    
  # Service account (application layer)
  service_account_uuid: <uuid>     # DCM actor of type "component_service_account"
  allowed_operations: [<operation_type>]   # what this component may call
  allowed_targets: [<component_type>]      # which components it may call
```

### 2.1 Component Types and Communication Graph

Not every component may call every other. The allowed communication graph is declared and enforced:

```
Consumer/Admin/Provider → API Gateway
API Gateway → Request Orchestrator
API Gateway → Policy Engine (for direct policy evaluation)
API Gateway → Session Store (token validation)

Request Orchestrator → Policy Engine
Request Orchestrator → Placement Engine  
Request Orchestrator → Scoring Engine
Request Orchestrator → Audit Store
Request Orchestrator → Message Bus

Policy Engine → Audit Store
Policy Engine → Message Bus (policy evaluation events)

Placement Engine → Audit Store
Placement Engine → Message Bus

Scoring Engine → Audit Store

Drift Reconciler → API Gateway (discovery dispatch)
Drift Reconciler → Audit Store
Drift Reconciler → Message Bus

Lifecycle Enforcer → API Gateway (decommission dispatch)
Lifecycle Enforcer → Audit Store
Lifecycle Enforcer → Message Bus

Notification Router → Message Bus (subscribe)
Notification Router → credential management service Proxy (notification channel credentials)

All components → Session Store (revocation check)
All components → credential management service Proxy (interaction credential requests)
```

**ICOM-004:** Components may only call components declared in their `allowed_targets` list. A call from an unexpected source component is rejected with `403 Forbidden` and an audit record.

---

## 3. Certificate Issuance and Internal CA

### 3.1 Certificate Authority for Internal Components

Each DCM deployment uses a **registered Certificate Authority (CA)** for issuing component mTLS certificates. This may be:

**Option A — Built-in Internal CA (default):** DCM operates its own CA per deployment. Simple to configure; no external dependencies; suitable for minimal through standard profiles.

**Option B — External CA via credential management service:** An enterprise CA registered as a credential management service (HashiCorp Vault PKI, Venafi TLS Protect, EJBCA, AWS ACM Private CA, Azure Key Vault). The external CA issues component certificates using the standard credential management service interface — DCM requests certificates via the provider's API (ACME/EST/SCEP/CMP). See [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md) for registration. Recommended for fsi and sovereign profiles where the enterprise PKI chain must be maintained.

Both options satisfy ICOM-001 (mTLS required). The distinction is who issues the certificates, not whether mTLS is used.

**The registered CA's root certificate is installed in all component trust stores at deployment time.** For Option B, the credential management service's CA root (which may itself be a subordinate of an enterprise root) is the trust anchor.

```yaml
internal_ca:
  ca_uuid: <uuid>
  deployment_uuid: <uuid>
  ca_type: built_in | external_service_provider
  service_provider_uuid: <uuid | null>  # if ca_type: external
  external_ca_protocol: acme | est | scep | cmp | null  # if external
  root_cert_fingerprint: <sha256>
  certificate_lifetime: P90D           # profile-governed — see table below
  renewal_trigger: P14D
  algorithm: ECDSA-P-384               # FIPS-compliant; all profiles
  crl_endpoint: <url>
  ocsp_endpoint: <url>
```

```yaml
internal_ca:
  ca_uuid: <uuid>
  deployment_uuid: <uuid>
  root_cert_fingerprint: <sha256>
  certificate_lifetime: P90D           # all component certs valid 90 days
  renewal_trigger: P14D                # renew 14 days before expiry
  algorithm: ECDSA-P-384               # FIPS-compliant for all profiles
  crl_endpoint: <internal-url>         # revocation list for component certs
  ocsp_endpoint: <internal-url>        # online status check
```

### 3.2 Profile-Governed Certificate Configuration

| Profile | Cert lifetime | Renewal trigger | Bootstrap token TTL | Min key algorithm |
|---------|--------------|-----------------|--------------------|--------------------|
| `minimal` | P180D | P30D | PT4H | RSA-2048 (min) |
| `dev` | P90D | P14D | PT1H | RSA-2048 (min) |
| `standard` | P90D | P14D | PT1H | ECDSA-P-256 (min) |
| `prod` | P90D | P14D | PT1H | ECDSA-P-384 |
| `fsi` | P30D | P7D | PT30M | ECDSA-P-384 |
| `sovereign` | P14D | P3D | PT15M | ECDSA-P-384 (HSM-backed if hardware_attested) |

> **sovereign profile:** Certificates must be HSM-backed if the deployment posture is `hardware_attested`. The external CA option (Option B) using an HSM-backed Vault PKI backend satisfies this requirement.

### 3.3 Certificate Lifecycle

```
Component starts
  │
  ▼ Does component have a valid certificate?
  │   YES → Use existing certificate
  │   NO (first start or expired) → Request certificate from Internal CA
  │
  ▼ Certificate request to Internal CA:
  │   component_uuid, component_type, deployment_uuid
  │   CSR signed with bootstrap key (see Section 5)
  │
  ▼ Internal CA issues certificate
  │   Subject: CN=<component_type>-<component_uuid>,O=dcm-internal
  │   SAN: component_uuid, component_name, internal DNS name
  │   Valid for: P90D (profile-governed)
  │
  ▼ Component stores certificate; begins accepting mTLS connections
  │
  ▼ 14 days before expiry: auto-renewal
      Background thread requests new certificate
      Transition: both old and new cert valid for PT1H
      Old cert retired after transition
```

---

## 4. Application-Layer Authorization

mTLS verifies **who** is calling. Application-layer authorization verifies **what** the caller is permitted to do.

### 4.1 Interaction Credential for Internal Calls

Every internal component call follows the same ZTS-002 scoped interaction credential model used for external provider dispatch:

```
Component A prepares to call Component B
  │
  ▼ Request interaction credential from credential management service Proxy:
  │   credential_type: dcm_interaction
  │   issued_to.component_uuid: <component_a_uuid>
  │   scope.operations: [<specific_operation>]
  │   scope.target_component: <component_b_uuid>
  │   expires_at: <now + PT5M>
  │
  ▼ Call Component B with:
  │   mTLS certificate (transport identity)
  │   Interaction credential in Authorization header (operation authorization)
  │   Correlation ID (tracing)
  │
  ▼ Component B validates:
  │   1. mTLS cert from Component A's known CA ✓
  │   2. Interaction credential: not revoked, not expired, scoped to this operation ✓
  │   3. Component A is in allowed_sources for this endpoint ✓
  │   4. Operation matches declared scope ✓
  │   → All pass: process request
  │   → Any fail: 403 + audit record ICOM_AUTH_FAILURE
```

### 4.2 Internal Endpoint Authorization

Each internal component endpoint declares which source components are permitted to call it:

```yaml
internal_endpoint:
  component: policy_engine
  endpoint: POST /internal/evaluate
  allowed_sources:
    - api_gateway
    - request_orchestrator
  required_scope: policy.evaluate
  audit_every_call: true           # all internal calls are audited
```

**ICOM-003:** Internal endpoints that receive calls from unauthorized source components return 403 and write an `ICOM_UNAUTHORIZED_SOURCE` audit record. This audit record has urgency: high — unexpected internal call patterns are security signals.

---

## 5. Bootstrap — First Certificate

The bootstrap problem: a new component needs a certificate, but it has no certificate yet to authenticate its request. DCM solves this with a **bootstrap token** mechanism.

### 5.1 Bootstrap Token

At deployment time, the platform admin generates a one-time bootstrap token for each component:

```
POST /api/v1/admin/components/bootstrap-tokens

{
  "component_type": "policy_engine",
  "component_uuid": "<pre-assigned-uuid>",
  "deployment_uuid": "<uuid>",
  "expires_at": "<ISO 8601>"     // short-lived: PT1H maximum
}

Response 201:
{
  "bootstrap_token": "<opaque-token>",    // one-time use; stored as env var or secret
  "component_uuid": "<uuid>",
  "expires_at": "<ISO 8601>"
}
```

### 5.2 First Certificate Acquisition

```
New component starts with bootstrap_token in environment
  │
  ▼ POST /internal/ca/issue-certificate
  │   Authorization: Bootstrap <bootstrap_token>
  │   Body: { component_uuid, component_type, deployment_uuid, csr_pem }
  │
  ▼ Internal CA validates:
  │   Bootstrap token not expired
  │   Bootstrap token not previously used (one-time)
  │   component_uuid matches token's declared component_uuid
  │
  ▼ Certificate issued
  │   Bootstrap token invalidated immediately after use
  │
  ▼ Component uses certificate for all subsequent communication
    No further need for bootstrap token
```

**ICOM-007:** Bootstrap tokens are one-time-use and must expire within PT1H of creation. A bootstrap token that is not used within PT1H is automatically invalidated. Platform admins must generate new tokens if a component fails to start within the window.

### 5.3 Kubernetes Deployment Integration

In Kubernetes deployments, bootstrap tokens are injected as Kubernetes Secrets and mounted as environment variables. The component reads the bootstrap token on startup, acquires its certificate, then deletes the Kubernetes Secret. This ensures the bootstrap credential is not persisted beyond initial use.

```yaml
# Kubernetes Secret (deleted by component after first cert acquisition)
apiVersion: v1
kind: Secret
metadata:
  name: dcm-policy-engine-bootstrap
type: Opaque
stringData:
  DCM_BOOTSTRAP_TOKEN: "<token>"
  DCM_COMPONENT_UUID: "<uuid>"
  DCM_INTERNAL_CA_ENDPOINT: "https://dcm-internal-ca.dcm-system.svc.cluster.local"
```

---

## 6. Certificate Compromise Response

If a component certificate is compromised, the response follows the same emergency pattern as credential compromise:

```
Certificate compromise detected
  │
  ▼ Compromised cert added to Internal CA CRL
  │   CRL update propagated to all components within SLA:
  │     standard/prod: PT1M
  │     fsi/sovereign: PT15S
  │
  ▼ Component identity suspended in DCM
  │   All active interaction credentials for this component → revoked
  │   ICOM_CERT_COMPROMISED audit record written
  │
  ▼ Platform admin notified (urgency: critical)
  │
  ▼ New certificate issued for legitimate component instance
  │   Previous certificate remains in CRL permanently
  │
  ▼ Component resumes with new certificate
```

**ICOM-008:** Compromised internal component certificates are added to the Internal CA CRL immediately. All other components refresh their CRL cache within the profile-governed SLA and reject connections presenting the revoked certificate.

---

## 7. Deployment Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    DCM Control Plane                             │
│                                                                  │
│  ┌──────────┐  mTLS+cred  ┌──────────────────┐                  │
│  │API Gateway│───────────→│Request Orchestrator│                 │
│  └──────────┘             └────────┬─────────┘                  │
│                                    │ mTLS+cred (each call)       │
│                    ┌───────────────┼───────────────┐            │
│                    ↓               ↓               ↓            │
│             ┌─────────────┐ ┌──────────┐ ┌──────────────┐      │
│             │Policy Engine│ │Placement │ │Scoring Engine│      │
│             └─────────────┘ │Engine    │ └──────────────┘      │
│                             └──────────┘                        │
│                                                                  │
│  ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │credential management service│  │Session Store│  │Internal CA       │   │
│  │Proxy             │  │             │  │(cert authority)   │   │
│  └──────────────────┘  └─────────────┘  └──────────────────┘   │
│                                                                  │
│  Service Mesh (Istio): mTLS enforcement at transport layer      │
│  All calls: authenticated + authorized + audited                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. System Policies

| Policy | Rule |
|--------|------|
| `ICOM-001` | All internal component-to-component communication must use mTLS with certificates issued by the deployment's Internal CA. Plaintext internal communication is prohibited in all profiles. |
| `ICOM-002` | Every internal call must present a scoped interaction credential (ZTS-002) in addition to the mTLS certificate. The mTLS certificate proves identity; the interaction credential proves authorization for the specific operation. |
| `ICOM-003` | Internal endpoints reject calls from components not in their `allowed_sources` list with 403 and an `ICOM_UNAUTHORIZED_SOURCE` audit record (urgency: high). |
| `ICOM-004` | Components may only call components declared in their `allowed_targets` list. Attempts to call unauthorized components are rejected at the mesh layer (traffic policy) and, if they reach the application layer, at the application layer. |
| `ICOM-005` | All internal component calls are audited: source component, target component, operation, interaction credential UUID, outcome. Internal audit records are written to the same Audit Store as external interactions. |
| `ICOM-006` | Component certificates are issued by the Internal CA with a maximum validity of P90D and renewed automatically P14D before expiry. Component certificates may not be issued by external CAs. |
| `ICOM-007` | Bootstrap tokens are one-time-use and expire within PT1H. A bootstrap token that has been used is immediately invalidated. Unused tokens are invalidated at expiry. |
| `ICOM-008` | Compromised internal component certificates are added to the Internal CA CRL immediately. All components refresh their CRL cache within the profile-governed SLA. |
| `ICOM-009` | The trust anchor for internal component mTLS is a registered root or intermediate CA whose certificate is installed in all component trust stores at deployment time. The trust anchor may be the built-in Internal CA or an external CA registered as a Certificate Provider (e.g. HashiCorp Vault PKI, Venafi, EJBCA) — see [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md) Section on External CAs. Components do not accept certificates from unregistered trust anchors. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
