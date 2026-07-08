# Trust & attestation — accepted methods by operational profile (homelab → sovereign)

**Principle:** trust/attestation strength is a **definable parameter with per-profile defaults** in DCM operational profiles — *and* DCM must carry the **mechanisms** to actually satisfy each target framework (declaration without enforcement is theater). Everything below is **adopt-by-reference** (ADR-021): real, accepted standards, not invented. Each cell is the *default floor* for that profile; a request may tighten (never loosen below the floor — governance).

Profiles (existing DCM ladder; **homelab** = the relaxed end of `minimal`):
`homelab/dev → minimal → standard → fsi → sovereign`

---

## The matrix — accepted method per trust plane × profile

### Identity & transport (who is talking)
| | method (default floor) |
|---|---|
| homelab/dev | internal/self-signed CA; TLS optional; bearer between components |
| minimal | internal CA; TLS 1.2+; mTLS optional |
| standard | **mTLS everywhere**; real PKI (internal CA or ACME/Let's Encrypt); TLS 1.3; short-lived certs; **SPIFFE/SPIRE** workload identity (CNCF) recommended |
| fsi | mTLS mandatory; enterprise PKI w/ documented chain; OCSP stapling; cert lifetimes ≤ 90d; HSM-protected CA keys |
| sovereign | mTLS mandatory; **accredited** PKI; in-jurisdiction CA; hardware-protected CA (FIPS L3 HSM); RATS remote attestation of endpoints (RFC 9334) |

### Anchor — root of trust (`anchor_type`, ADR-022)
*Suggested methods + the settable minimum per profile. `anchor_type` is a pluggable, declared dimension (ADR-022) — public-acme, internal-ca, private-acme, enterprise-pki, authority-list, hardware-rats, transparency-log, spiffe-bundle, tofu, did/ledger, threshold.*
| | suggested anchor(s) | minimum requirement |
|---|---|---|
| homelab/dev | **`public-acme` (Let's Encrypt → ISRG root) for the public TLS edge** + **`internal-ca` or `private-acme` (step-ca) for the mesh/mTLS**; `tofu` bootstrap OK | any rooted anchor (internal-ca / private-acme / public-acme). *Note: a Let's Encrypt **leaf** can root the public edge but **cannot issue** mesh/client certs (CA:FALSE) — use step-ca/internal CA for mTLS.* self-signed only for throwaway dev |
| minimal | `internal-ca` or `private-acme` (step-ca) mesh; `public-acme` edge optional | a real issuing root (internal-ca / private-acme) — no bare self-signed for the mesh |
| standard | internal/enterprise PKI or `private-acme` mesh + `public-acme` edge; **`transparency-log` (CT/Sigstore)** recommended; `spiffe-bundle` optional | real CA + CRL/OCSP; transparency-logging recommended |
| fsi | `enterprise-pki` (documented chain) with **HSM-protected issuing root**; `authority-list` for attestation; CT | HSM-protected issuing CA **+** external `authority-list` for assurance claims |
| sovereign | **accredited, in-jurisdiction, HSM-L3 issuing root**, root key **`threshold`/ceremony-protected**; external authority roots (CMVP/eIDAS) **+ `hardware-rats`**; disconnected = import + re-anchor | accredited + HSM-L3 issuing root, external-authority attestation, hardware-attested (top tier), quorum-protected root key |

### Authorization (what they may do)
| | method |
|---|---|
| homelab/dev | static token / basic OIDC; long-ish sessions |
| minimal | OIDC (Keycloak/RHSSO); JWT; introspection optional |
| standard | OIDC + **token introspection (RFC 7662)** + JWKS rotation; session revocation registry; AAL1–2 |
| fsi | OIDC + **AAL2 hardware MFA**; step-up-MFA for sensitive ops; short token TTL; dual-control on privileged actions |
| sovereign | **AAL3** hardware-bound (FIDO2/PIV/CAC); step-up everywhere; PT-scale token TTL; full revocation propagation |

### Credential issuance / retrieval (ADR-022 selected spec)
| | x509 | tokens | keys |
|---|---|---|---|
| homelab/dev | self-signed / internal ACME | OAuth2 | software keys |
| standard | **ACME** (RFC 8555) / internal CA | OAuth2 + OIDC | software or KMS |
| fsi | **EST/CMP** to enterprise CA; ≤90d | OAuth2, short TTL | **HSM/KMIP**, FIPS 140-3 |
| sovereign | EST/CMP to accredited CA, in-jurisdiction | mTLS-bound tokens | **HSM L3 + key ceremony**, split-knowledge (NIST SP 800-57) |

### Attestation (the trust backing — ADR-022 ladder)
| | default tier + accepted frameworks |
|---|---|
| homelab/dev | `self_asserted` |
| minimal | `self_asserted` → `vendor_attested` |
| standard | `vendor_attested` / `independently_verified`; SOC 2; ISO 27001; FIPS via CMVP if claimed |
| fsi | `independently_verified`+; **PCI-DSS, SOC 2 Type II, FIPS 140-3 CMVP** |
| sovereign | `accredited` + `hardware_attested`; market authority: **FedRAMP High + FIPS 140-3 L3 + Common Criteria** (US), **eIDAS QTSP / SecNumCloud / BSI C5 / EUCS** (EU), **IRAP** (AU), **ISMAP** (JP); TPM/HSM remote attestation; confidential-compute attestation (SEV-SNP/TDX/SGX) where applicable |

### Federation (trusting another DCM/provider)
| | method |
|---|---|
| homelab/dev | manual trust-anchor add |
| standard | exchange trust anchors; verify CONFORMANCE declaration |
| fsi | + verify `independently_verified` attestation before federating |
| sovereign | + verify `accredited` posture, jurisdiction match, and live attestation; no federation to lower-posture peers |

Cross-cutting baseline (ALL profiles, including homelab — strictness scales, existence doesn't): zero-trust posture (NIST SP 800-207); CPX-001 (values never transit DCM); audit of every trust decision (ADR-010); forbidden-weak-algorithm baseline; supply-chain integrity (SLSA / signed artifacts) recommended standard+.

---

## Mechanisms DCM must implement (to *support*, not just declare, the targets)
1. **PKI/PKIX + mTLS** stack with trust-anchor management, chain validation, **CRL + OCSP** checking (ICOM-009).
2. **ACME / EST / SCEP / CMP** client(s) for cert issuance/rotation; SPIFFE/SPIRE integration option.
3. **OIDC relying-party + token introspection (RFC 7662) + JWKS** rotation; session revocation registry; step-up-MFA hook.
4. **HSM / PKCS#11 / KMIP** integration for key custody; BYOK/HYOK; key-ceremony + split-knowledge support.
5. **Attestation verification**: ingest + validate Accreditation artifacts (cert id, validity, revocation); **RATS remote attestation** (RFC 9334) for TPM/HSM/confidential-compute quotes.
6. **Accreditation/conformance registry** surface — queryable trust posture (provider + DCM's own), exposed at well-known endpoints.
7. **Profile engine**: the trust/attestation floor is a profile parameter; the selection/gate engine (ADR-022) enforces it per request, market-graded.

> A profile may *require* a framework only if DCM has the mechanism to verify it. Gap = a tracked conformance item, not a silent pass. Where a mechanism is absent, the profile cannot claim that target (fail-safe).

---

## The definable parameter (ties to DCM operational profiles)
```yaml
profile: sovereign
region: eu
trust_floor:                      # default per profile; request may tighten only
  anchor:        { allowed_types: [accredited-pki, hardware-rats],   # the pluggable anchor_type set
                   root_protection: threshold, in_jurisdiction: true,
                   external_authority_required: true }               # homelab e.g.: { allowed_types: [public-acme, internal-ca, private-acme, tofu] }
  identity:      { mtls: required, ca: accredited, endpoint_attestation: required }
  authorization: { min_aal: aal3, step_up: required }
  attestation:   { min_tier: accredited, require_hardware_attested: true,
                   accepted_frameworks: [eidas-qtsp, secnumcloud, bsi-c5, fips-140-3] }
  key_custody:   { hsm: required, fips_level: 140-3-L3, jurisdiction_in: [eu] }
  federation:    { min_peer_tier: accredited, jurisdiction_match: true }
```
Defaults shipped for `homelab/dev`, `minimal`, `standard`, `fsi`, `sovereign`; operators override within governance bounds. This makes "what trust is required here" a **declared, queryable, governable** profile parameter — selected and enforced by the ADR-022/023 engine.
