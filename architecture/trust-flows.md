# Trust & Credential Flows — expressed via existing DCM primitives

The operational flows behind ADR-022 (DCM Trust Model, incl. Credential API Selection). **Design intent: express every flow in terms of primitives DCM already has; where a primitive is genuinely missing, propose one that follows DCM's own methodology and industry best practice.** This is the layer between the requirements (ADR-022) and engineering — engineering implements *named flows over named primitives*, it does not invent them.

## Primitives reused (no change)
| Primitive | Role in trust/credential flows |
|---|---|
| **Request Orchestrator** (event bus) | carries `credential.requested` / lifecycle events to subscribers |
| **Placement Engine** (sovereignty pre-filter → accreditation filter → capability filter → score → select) | **is** the credential-API selection engine — credential capability is the capability dimension, attestation is the accreditation filter |
| **Policy Engine** — Gating Policy / Validation / Transformation / Recovery | profile gating, requirement validation, provenance on mutations, failure handling |
| **Governance Matrix** (`boundary_control`) | evaluated at the consumer↔producer boundary crossing |
| **Accreditation** artifact (versioned, time-bounded) | carries `attestation[]`; the accreditation filter reads it |
| **Audit & Tamper Evidence** (ADR-010) + field provenance | every match/gate/introduction/issuance recorded |
| **Credential / Session Revocation Registry**, **Transition Window**, **Emergency Rotation** | rotation + revocation |
| **Discovery Service** (scheduled polling, configurable interval) | the scheduler for rotation/re-attestation |
| **Provider registration + lifecycle-event endpoint**, **Provider Callback Auth (PCA, mTLS)**, **Component Identity**, **Trust Anchor / Internal+External CA (ICOM-009)**, **Token Introspection (RFC 7662) / JWKS / well-known** | identity, transport, exposure |

---

## Flow 1 — Broker introduction (request → direct issuance)
1. Consumer submits `credential_requirements` → `credential.requested` on the **Request Orchestrator**. *[reuse]*
2. **Placement Engine** runs as the selection engine: **sovereignty pre-filter** → **accreditation filter** (= attestation gate, ADR-022) → **capability filter** (credential_capability match) → **score** (credential scoring profile — *new, §P4*) → select producer + spec. *[reuse + P4]*
3. **Gating Policy/Governance-Matrix** gate the selection on the profile floor (tier/frameworks/FIPS/AAL/residency; vendor-native opt-in). *[reuse]*
4. DCM mints an **Introduction Grant** (*new, §P1*) — short-lived, audience-scoped to (consumer, producer, request) — and returns it + producer endpoint + trust anchors. *[P1]*
5. Consumer connects **directly** to the producer's selected-spec endpoint, presents the Grant; producer validates it against DCM's **JWKS/introspection** (DCM's "expose"). *[reuse + P1]*
6. Producer issues the credential **direct to consumer** over the standard spec (ACME/EST/OAuth/KMIP). **Value never transits DCM** (CPX-001). *[reuse]*
7. Introduction + issuance-confirmation recorded in **Audit** with the attestation that justified it. *[reuse]*

## Flow 2 — Attestation verification
1. On registration/update, a producer's `attestation[]` lands as **Accreditation** artifacts. *[reuse]*
2. **Attestation Verifier** (*new, §P2*) validates each: signature → issuing authority is a **recognized Accreditation Authority** (*new registry, §P2*, modeled on **Trust Anchor**) → validity window → revocation (OCSP/CRL). For `hardware_attested`, runtime **RATS** quote (RFC 9334). *[P2]*
3. Verified attestation tier/framework is cached (profile-governed TTL) and is what the **accreditation filter** (Flow 1.2) reads. *[reuse]*
4. Verification result + provenance → **Audit**. *[reuse]*

## Flow 3 — Bootstrap (pre-registration trust)
1. Before any Credential Provider is registered, DCM uses a **Bootstrap Trust Anchor** + one-time **bootstrap token** (*new but small, §P3*) — out-of-band installed root + short-lived enrolment token. *[P3]*
2. First provider registers over PCA mTLS, presenting the bootstrap token; DCM validates against the bootstrap anchor (ICOM-009). *[reuse + P3]*
3. After bootstrap, all issuance flows through registered, attested providers via Flow 1; the bootstrap token is single-use and expires. *[reuse]*

## Flow 4 — Rotation & revocation
1. **Discovery-Service-style scheduler** fires a rotation trigger at the declared interval (or on `expires_at` approach). *[reuse]*
2. An **Orchestration-Flow Policy** re-runs Flow 1 for the resource; **Transition Window** keeps old+new valid; cutover; old retired. *[reuse]*
3. Revocation (scheduled or **Emergency Rotation** on a security event) writes the **Credential/Session Revocation Registry**; producers + components check it per use. *[reuse]*
4. Re-attestation: the scheduler also re-runs Flow 2 before an Accreditation's `valid_until`; an expired/revoked attestation drops the provider from the accreditation filter (fail-safe). *[reuse]*

## Flow 5 — Selection algorithm detail
The **Placement Engine scoring model** with a **credential scoring profile** (*new, §P4*): hard **filter/gate** = security + trust(attestation) + fit-for-purpose; **score/tie-break** = portability (standardized > vendor-native) + attestation-strength + lifetime fit. Portability is a tiebreak weight, never a gate (ADR-022 inversion). *[reuse + P4]*

## Flow 6 — DCM as participant (its own credentials)
DCM, needing a credential for its own identity/user-auth, is just another **consumer**: it runs Flow 1 through the same orchestrator/placement/gating (no privileged bypass), obtaining from a registered producer or its **Internal CA** (self-producer, own components only). DCM-operational secrets are held + protected per profile (ADR-022). *[reuse]*

---

## Proposed NEW primitives (the genuine gaps)

> **v1 scope (ADR-022):** only **P1** is required for v1. **P2** ships thin (self/vendor tiers; accredited + RATS deferred), **P3** is small, **P4** is configuration. Accredited/hardware mechanisms are *declared-but-deferred* until a market needs them (fail-safe rule).

### P1 — Introduction Grant
A short-lived, audience-scoped, signed token DCM mints to authorize a **direct** consumer↔producer credential exchange — DCM's "introduction," then it steps out (ADR-022 broker boundary).
- **Why new:** the existing **DCM Interaction Credential** authorizes *DCM→provider dispatch* (PCA); there is no token for brokering a *consumer↔producer* direct channel. This is that.
- **Basis:** OAuth 2.0 / **Token Exchange (RFC 8693)** + audience-restricted JWT; producer validates against DCM JWKS — standard, and reuses DCM's existing JWKS/introspection. Conceptually a capability token (cf. macaroons, SPIFFE JWT-SVID).
- **Fits:** minted in Flow 1.4; a Validation/Gating Policy-class artifact; audited.

### P2 — Attestation Verifier + Accreditation Authority registry
A verifier that turns a *claimed* attestation into a *trusted* one, and a registry of recognized authorities per framework/market.
- **Why new:** DCM has the **Accreditation** artifact + an accreditation *filter*, but not the **verification** (signature/authority/validity/revocation) nor a registry of *which* authorities are recognized for *which* market.
- **Basis:** extend the **Trust Anchor** model (ICOM-009) to accreditation authorities (CMVP/CC/FedRAMP/eIDAS/…); **RATS (RFC 9334)** for hardware/TEE remote attestation; OCSP/CRL for cert validity. A **Validation Policy** type runs it.
- **Fits:** Flow 2; feeds the accreditation filter in Flow 1.2.

### P3 — Bootstrap Trust Anchor + bootstrap token
A minimal, out-of-band root + single-use enrolment token for the pre-registration chicken-and-egg.
- **Why new:** referenced in `credentials.md` but not specified as a primitive.
- **Basis:** kubeadm bootstrap tokens / SPIRE node attestation / TOFU-with-OOB-verification — established patterns; reuses ICOM-009 trust-anchor validation.
- **Fits:** Flow 3.

### P4 — Credential scoring profile
A scoring profile for the existing Placement scoring model that encodes the credential priority order.
- **Why new:** it's a *configuration* of the existing scoring engine, not a new engine — but it must exist so portability scores as a **tiebreak**, not a filter (the ADR-022 inversion), with attestation-strength weighted.
- **Basis:** the existing Placement scoring model (ADR-007 / scoring.md) — just a new named profile.
- **Fits:** Flow 1.2 / Flow 5.

---

## Net assessment
**~80% reuse.** The selection engine, gating, audit, accreditation artifact, revocation, rotation windows, scheduler, identity/transport, and exposure are all existing DCM primitives. **Four net-new pieces**, each grounded in an existing DCM mechanism *and* an industry standard: **P1** Introduction Grant (RFC 8693), **P2** Attestation Verifier + Authority registry (Trust-Anchor model + RATS RFC 9334), **P3** Bootstrap anchor/token (kubeadm/SPIRE), **P4** credential scoring profile (Placement scoring). Only P1 and P2 are substantive; P3 is small, P4 is configuration. Engineering then implements named flows over named primitives.

## Data · Policy · Provider
- **Data (UDLM):** Introduction Grant shape, attestation/accreditation records, credential scoring inputs — declared/auditable.
- **Policy (DCM):** the flows are Placement + Policy-Engine + Governance-Matrix compositions; P2/P4 are policy/engine config; P1 is a minted, gated artifact.
- **Provider:** presents attestation + identity, implements the selected spec, issues direct to the consumer under the Introduction Grant.
