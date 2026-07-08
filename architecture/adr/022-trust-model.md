# ADR-022: DCM Trust Model (incl. Credential API Selection)

**Status:** Proposed
**Date:** 2026-06-28
**Type:** Architecture Decision Record (a `DecisionRecord` with architecture scope)
**Related:** ADR-005 (Provider Abstraction), ADR-007 (Placement Engine), ADR-010 (Audit & Tamper Evidence), ADR-011 (Sovereignty), ADR-021 (Adopting External Standards by Reference); UDLM ADR-004 (Provider capability declaration); CPX-001…012; AAL (NIST 800-63B); NIST SP 800-207 (Zero Trust). **Flows:** [`architecture/trust-flows.md`](../trust-flows.md). **Profiles:** [`architecture/trust-profiles.md`](../trust-profiles.md). **Attestation of this model:** [`architecture/trust-attestation.md`](../trust-attestation.md).
**Note:** consolidates the credential-API-selection and trust-model drafts into one ADR (minimize surface / avoid drift).

## Context

Trust in DCM cannot be self-declared — not for the platform and not for a provider. DCM spans organizational and sovereign boundaries, so it must be a **first-class participant in the standard trust fabric** (PKI/TLS, OAuth2/OIDC, attestation), not a bespoke trust island. And **a declared capability is only a *claim*** — "I support FIPS L3" is not trustworthy because the provider says so; trust must be backed by **external attestation** of a strength the target market demands.

## DCM's role: trust **broker** (introducer/matchmaker), not credential authority

DCM/UDLM **broker** trust; they do **not** custody, pass, or negotiate brokered credentials.

- **DCM does** — discover + **match** producer↔consumer; **gate** on attestation; **broker the bootstrap** (endpoints + trust anchors + a short-lived, scoped **Introduction Grant**) so the parties stand up a **direct, mutually-authenticated** channel; **audit**.
- **DCM does NOT** — hold/pass credential **values** (CPX-001) or sit in the credential **negotiation** path. The consumer speaks the *selected* standard API (ACME/EST/OAuth/KMIP) **directly** to the producer.
- **"Trusted" = introduction integrity, not secret custody** — a minimal surface: a compromised broker can't leak secrets (it never holds them); at worst it mis-introduces, which mutual-auth + audit catch.

**DCM's second hat — participant for its OWN needs.** DCM also *consumes* credentials (component mTLS, user auth, internal trust) and *produces* its own component identity (Internal CA), through the **same** declare→select→attest machinery (no bypass). Two custody categories:

| Category | Owner | Custody |
|---|---|---|
| **Managed** (brokered consumer↔producer) | the parties | **CPX-001 — value never in DCM** |
| **DCM-operational** (own TLS/JWKS/component keys) | DCM | DCM **must** hold these — protected per profile (sw → HSM), attested, rotated |

## Decision — one trust model across five planes (adopt-by-reference, ADR-021)

Each plane is **upheld** (enforced on every interaction), **participated-in** (DCM is a member of the standard system), and **exposed** (DCM publishes its own verifiable posture). DCM's posture across all five is *broker*.

| Plane | Standards (referenced) | Uphold / Participate / Expose |
|---|---|---|
| **Identity & transport** | X.509/PKIX (RFC 5280), mTLS, Trust Anchors, PCA, SPIFFE (opt) | validate chain→anchor + revocation / present own cert + accept external CAs / publish anchors + certs |
| **Authorization** | OAuth2 (RFC 6749), OIDC, introspection (RFC 7662), JWKS, revocation | verify every token / integrate any OIDC IdP / own introspection+JWKS |
| **Credential issuance** | ACME/EST/SCEP/CMP, OAuth, KMIP — **selected** (below) | gate on capability+attestation / naturalize any compliant backend / publish the capability+attestation matrix |
| **Attestation** | CMVP(FIPS 140-3), CC, FedRAMP, eIDAS, PCI-DSS, SOC 2, SecNumCloud, C5, IRAP; RATS (RFC 9334) | gate on tier+framework / consume recognized authorities / publish own + providers' attestations |
| **Federation** | peer posture exchange; CONFORMANCE verification | verify peer before federating / exchange anchors / expose posture |

Invariants: **CPX-001**; **everything declared data** (anchors, identities, attestations) → queryable + governable; **market-appropriate strength** set by `profile × region`; every trust decision **audited** (ADR-010).

## Credential API Selection (the credential-issuance plane in detail)

Credentials are brokered like **placement** (ADR-007): providers **declare** a granular credential capability matrix (per type × operation: API specs, algorithms, `key_usage`, AAL/FIPS/HSM, lifetime, rotation, revocation, retrieval transport+auth, residency, **attestation**); requests state **requirements**; DCM **selects** — `sovereignty pre-filter → accreditation (attestation) filter → capability filter → score → select → negotiate` — then mints the Introduction Grant and steps out. A provider exposing only a native API **fails the filter** for any standardized requirement.

- **Attestation ladder** (gate on the attestation, not the claim): `self_asserted → vendor_attested → independently_verified → accredited → hardware_attested`; the profile sets the minimum tier + accepted frameworks for the market. Carried on the existing **Accreditation** artifact.
- **Priority — security/trust/fit-for-purpose first, portability retained but subordinate.** A *deliberate inversion* of the general UDLM stance (where portability is near-sacrosanct): for credentials, security+trust+fit are the **hard gate**; portability is a **scoring tiebreak** (prefer standardized > `vendor-native`), never traded below the security floor. `vendor-native` is opt-in (`portability: provider-specific`), selected only when it's the fit-for-purpose secure choice the market needs *and* the request permits.
- **Queryable + governable:** the matrix is registry data ("who issues x509/ACME at FIPS L3 with EU custody?"), and `credential_profile`/Governance-Matrix gate on the *declared* fields before selection.
- **Per-type adopt-by-reference:** x509→ACME/EST/SCEP/CMP; token→OAuth2+RFC7662; key→KMIP/PKCS#11 — the standard *is* the API; the thin DCM envelope is only the selection/negotiation wrapper.

## Anchoring & the internal TLS root

**Can all trust anchor to one internal TLS certificate root? For the operational majority, yes — and at homelab, for *everything*. For attestation, deliberately no.**

- **Identity / transport / issuance-brokering** (mTLS between components, PCA, the consumer↔producer channel, and the Introduction Grant signed by DCM and validated via DCM's JWKS) **all chain to a single internal TLS root.** This is the largest trust surface and the **default + bootstrap anchor** (ICOM-009 — components accept only registered anchors). At **homelab/minimal**, the internal root anchors *everything*, because the only attestation tier there is `self_asserted` (self-rooted by definition).
- **Attestation deliberately extends to *external* roots as assurance rises.** You cannot self-certify FIPS L3 / eIDAS / FedRAMP — those must be signed by a **recognized external authority** (CMVP roots, accreditation bodies, TEE/HSM manufacturer attestation roots for RATS). Anchoring attestation to your own internal root *is* `self_asserted` — meaningless for regulated markets. So `accredited` / `hardware_attested` (fsi/sovereign) add external anchors; they don't replace the internal root, they sit alongside it for the assurance claims. **This is not a limitation — it is the entire reason the attestation plane is separate from identity.**
- The internal root's **own** trust scales by profile: a software root (homelab) → an **HSM-protected / externally-attested** root (sovereign), with standard PKI hygiene (offline root, intermediates, rotation). A single root is also a single point of compromise — so higher profiles protect/attest the root itself.

- **Disconnected / air-gapped sovereign:** where no external authority is reachable, external attestations are **imported** — their signed evidence pre-validated out-of-band and cached as **Accreditation** artifacts re-anchored into the local trust domain — rather than fetched live. The internal root can then anchor *everything operationally* in a self-contained domain, while the assurance still **derives from the original external authority's signature** (imported), not from self-assertion. This is how a sovereign disconnected cloud keeps high-assurance trust without live connectivity.

**Summary:** internal TLS root = the universal anchor for *identity/transport/brokering* (and the homelab-everything anchor); external roots are *added* for *attestation* as the market bar rises.

### Anchor methods (`anchor_type` — pluggable, extensible)

The root of trust is **not** fixed to PKI. The trust anchor is declared data (ICOM-009), so **`anchor_type` is a pluggable dimension**: support a small core now, extend by configuration (adopt-by-reference, profile-gated) without redesign. Each profile lists *suggested* methods + a *settable minimum* (see `trust-profiles.md`).

| Family | `anchor_type` | Anchor = trust in… | Tier |
|---|---|---|---|
| Hierarchical PKI | `internal-ca`, `public-acme` (LE/ISRG), `private-acme` (step-ca), `enterprise-pki` | a root cert chained to | **v1 core** |
| Federated identity | `spiffe-bundle`, OIDC/JWKS | node/platform attestation + bundle | core (OIDC) / deferred (SPIFFE) |
| Out-of-band | `tofu` (pin/PSK) | first-seen key / manual install | **v1 core** (bootstrap) |
| Authority / trust-list | `authority-list` (eIDAS Trusted Lists, CMVP, root stores) | a curated, signed authority list | deferred (= attestation plane) |
| Hardware / silicon | `hardware-rats` (TPM/HSM/TEE: SGX/SEV-SNP/TDX/CCA) | manufacturer root, appraised via RATS (RFC 9334) | deferred (fsi/sovereign) |
| Transparency-backed | `transparency-log` (Certificate Transparency, **Sigstore** Fulcio/Rekor) | append-only public logs + auditability | deferred (recommended standard+) |
| Decentralized | `did` / `ledger` (W3C DIDs+VCs), web-of-trust | distributed proofs / peer endorsement | declare-extensible only (not built) |
| Quorum | `threshold` (m-of-n / MPC / key ceremony) | N parties must agree | **root-protection** (sovereign root key), not a general anchor |

**Core (v1):** `internal-ca` / `public-acme` / `private-acme` + OIDC + `tofu` bootstrap. **Deferred (declared, built when a market needs it):** `authority-list`, `hardware-rats`, `transparency-log`, `spiffe-bundle`. **Declare-extensible only:** `did`/`ledger`, web-of-trust. **`threshold`** is the answer to "a single root is a single point of compromise" — used to protect the sovereign root key (cf. DNSSEC root KSK ceremony), not as a day-to-day anchor.

Caveat (homelab): a **`public-acme` (Let's Encrypt) leaf can root the public TLS edge but cannot issue mesh/client certs** (`CA:FALSE`) — pair it with `internal-ca` or `private-acme` (step-ca) for mTLS/workload identity.

## v1 mandated core vs declared-but-deferred (minimization)

The model is comprehensive; the **mandated v1 implementation is small**, and unbuilt mechanisms are *declared but deferred* — gated by the fail-safe rule: **a profile may require a framework only if the mechanism to verify it exists.**

| v1 mandated DCM core (implement now) | Declared, deferred (build when a market needs it) |
|---|---|
| X.509/mTLS identity + Trust Anchors (internal root) | accredited-authority registry + accredited-tier verification |
| OIDC + JWKS + introspection (RFC 7662) | hardware attestation (RATS RFC 9334), TEE/HSM |
| **Introduction Grant** (P1) | HSM/PKCS#11/KMIP key custody |
| minimal attestation (`self_asserted`/`vendor_attested`) + revocation | external CA protocols beyond the default (EST/SCEP/CMP) — *producer-side anyway* |

**The broker boundary is the great minimizer:** because DCM only brokers, it does **not** implement the credential-type protocols (ACME/EST/SCEP/CMP/KMIP/PKCS#11) — those are **producer-side**. DCM core ≈ four things: mTLS, OIDC, Introduction Grant, attestation-verify+revocation.

## Proposed new primitives (the only net-new — see trust-flows.md)
- **P1 — Introduction Grant** *(required v1)*: short-lived, audience-scoped token for direct consumer↔producer issuance (OAuth2 Token Exchange RFC 8693; validated vs DCM JWKS). **Introduction-only** — the producer still independently authenticates the consumer per the selected spec; it must never become a bearer-secret.
- **P2 — Attestation Verifier + Accreditation-Authority registry** *(thin v1: self/vendor; accredited+RATS deferred)*: extends the Trust-Anchor model + RATS.
- **P3 — Bootstrap anchor/token** *(small)*: kubeadm/SPIRE-style one-time enrolment; *is* the internal root install.
- **P4 — Credential scoring profile** *(config, not new engine)*: portability as tiebreak.

## Trust attestation (we attest to ourselves)
DCM/UDLM earn trust by **self-application** — running this model on themselves and publishing a verifiable **Trust Posture Statement** (a *projection* of existing records: DecisionRecord + Accreditation + CONFORMANCE + Audit; **zero new primitives**) at `/.well-known/udlm/trust-posture`. Same bar, same tooling we require of producers. The render/assess role is fulfilled by **any conformant, independent assessor** — *non-normative*; nothing here names or depends on a specific tool. (A separate assessment/testbed consumer may exercise it.) Full model: `trust-attestation.md`.

## Options considered
- **Implicit/internal trust (assert our own trustworthiness)** — rejected: unverifiable across boundaries.
- **Invent a DCM trust/credential framework** — rejected (ADR-021): adopt PKI/OAuth/OIDC/CMVP/CC/eIDAS/RATS.
- **Route credential values through DCM to normalize** — rejected (CPX-001).
- **Single fixed credential envelope** — rejected: re-specs solved standards, loses per-type fidelity.
- **Capability-declared / requirement-selected, value direct, broker-mediated, attestation-gated, market-graded** — **chosen.**

## Data · Policy · Provider
- **Data (UDLM):** `credential_capability` + `attestation[]` + `trust_posture` on the provider declaration; `credential_requirements` on the request; the Trust Posture projection.
- **Policy (DCM):** selection (filter/gate/score/select/negotiate) + the five-plane enforcement + profile gating, all audited; broker — never in the value/negotiation path.
- **Provider:** declares the matrix, furnishes market-required attestation, implements the selected spec, issues **direct** to the consumer under the Introduction Grant.

## Consequences
- One coherent model over mostly-existing primitives (Placement, Policy Engine, Governance Matrix, Accreditation, revocation, PCA/Trust-Anchors, OIDC/introspection, Audit). Net-new ≈ P1 + thin P2.
- New UDLM data: provider capability declaration gains `credential_capability` + `trust_posture`; request gains `credential_requirements`.
- New conformance: a realization **exposes** its trust posture and **upholds** validation on every plane; a Credential Provider implements each spec it declares + furnishes market-required attestation.
- Trust becomes **provably** market-appropriate (gated on attested, validatable data) and **self-attested** (we hold ourselves to the same bar).
