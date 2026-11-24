# Trust Attestation — how DCM/UDLM attest to, build, and ensure trust

**Goal:** earn and ensure trust for **customers, users, producers, and consumers** — not by assertion ("trust us"), but by making the trust model itself **transparent, standards-grounded, validation-backed, and independently verifiable**, and by **holding ourselves to the same bar we require of producers** (self-application). "We don't ask you to trust us — we give you what you need to *verify* us, by the same rules we apply to everyone."

## Minimization first: this is a *projection*, not a new framework — ZERO new primitives

A **Trust Attestation** composes records UDLM already has. We invent nothing:

| Existing record (reused) | Contribution to the attestation |
|---|---|
| **DecisionRecord** (the WHY; reaches `CANONICAL` only with passing use-case validation) | **why** the process is the way it is — *validation-backed*, so the rationale is evidenced, not asserted |
| **Accreditation** artifact (versioned, time-bounded conformance to a framework) | **what** it conforms to + the attestation **tier** of that claim |
| **CONFORMANCE** declaration + independent-verifier flow | **self-declaration + third-party verification** of what's implemented |
| **Audit & Tamper-Evidence** (ADR-010) + field provenance | the **evidence** trail |
| **trust_posture** (ADR-022) exposed at well-known endpoints | **publication** — any party fetches + verifies |

The Trust Attestation is the **assembled, signed, published view** of these. (One thin addition: a *projection/exposure* — not a new data primitive.)

## The artifact — a Trust Posture Statement
A signed, versioned record any party can fetch and verify, composed of six parts:

1. **Rationale (why).** The governing DecisionRecords — ADR-022 (credential API selection), ADR-022 (trust model), the design priorities (broker-not-authority, claim≠trust, security/trust/fit > portability, CPX-001 value-never-in-DCM). Each is validation-backed → the *why* is demonstrably sound, not just stated.
2. **Standards followed.** The adopt-by-reference catalog, version-pinned + conformance refs: X.509/PKIX, ACME/EST/SCEP/CMP, OAuth2/OIDC/RFC7662, RFC 8693, KMIP/PKCS#11, RATS (RFC 9334), NIST 800-63B (AAL), FIPS 140-3, Common Criteria, eIDAS, PCI-DSS, SOC 2, SecNumCloud, C5, IRAP.
3. **Best practices followed.** Zero-trust (**NIST SP 800-207**), least-privilege, short-lived credentials, defense-in-depth, **minimal trust surface** (broker — DCM holds no managed secrets), value-never-in-control-plane (CPX-001), separation of duties, auditability.
4. **Conformance claim.** What DCM/UDLM *implements*, at which **profile** (homelab→sovereign), **plus the attestation tier of the claim itself** (`self_asserted` → `independently_verified` → `accredited`) — the *same ladder* we apply to producers (ADR-022). A sovereign customer sees an accredited claim or it doesn't count.
5. **Evidence.** Audit/provenance + use-case validation results; and, by reference where a market needs them: supply-chain provenance (**in-toto / SLSA**), runtime attestation (**RATS**), and formal conformity assessments (SOC 2 / CC / eIDAS).
6. **Exposure.** Signed, versioned, served at a well-known endpoint (`/.well-known/udlm/trust-posture`) so customers/peers verify it without asking — the ADR-022 "expose" obligation, applied to ourselves.

## Self-application — the credibility multiplier
DCM runs its **own** trust model **on itself**: its trust posture is declared, attested, and verified by the *same* machinery and at the *same* tiers it demands of producers. This is the strongest possible attestation — we are not exempt from our own rules. It also means a producer or customer evaluating DCM uses the *same* tooling they'd use to evaluate any provider (no special case).

## Per-audience projection (one source, scoped views)
Same record, audience-scoped lenses (one source, many projections):
- **Customer** (regulated): the accreditation evidence + conformity assessments for *their* market (FedRAMP/eIDAS/PCI…).
- **User**: the identity + authorization posture (how they're authenticated, session/revocation guarantees).
- **Producer**: what DCM requires to register + how DCM authenticates the introductions it brokers.
- **Consumer**: what's brokered, the CPX-001 guarantee (DCM never sees the value), and the selection/attestation guarantees.

**Renderer/assessor is an abstract role — non-normative.** The Trust Posture Statement is rendered/verified by **any conformant, independent assessor**; the model names no specific tool and depends on none. An external assessment consumer or testbed *may* exercise this role to produce/validate the views, but that is illustrative, not a structural dependency.

## Adopt-by-reference for the *form* of attestation too (don't invent)
Even the *shape* of the attestation follows established forms — **SOC 2 / ISO conformity assessment**, **eIDAS conformity**, **C2PA / in-toto / SLSA** provenance, **RATS** runtime attestation, and the **trust-center / well-known-endpoint** publication pattern. We map onto these, we don't define a new attestation language.

## Data · Policy · Provider
- **Data (UDLM):** the Trust Posture Statement = a projection over DecisionRecord + Accreditation + CONFORMANCE + Audit (all existing UDLM records); the `trust_posture` exposure shape.
- **Policy (DCM):** assembles, signs, and serves the statement; gates federation/selection on peers' statements; re-verifies on schedule.
- **Provider:** publishes its own posture the same way; DCM (as a participant) publishes *its* posture identically.

## Net
**Zero new data primitives** — the attestation is a signed, published *projection* of records UDLM already defines, plus a well-known exposure endpoint. It earns trust by transparency + validation-backing + self-application + independent verifiability, all adopt-by-reference. Fully consistent with the minimize-standards/processes priority: it adds **publication + projection**, not a new framework.
