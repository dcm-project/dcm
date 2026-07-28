# Policy obligations delegated from UDLM

**What this is.** The register of policy work UDLM has *delegated to DCM*. UDLM fixes an invariant every
conformant realization must honor; where UDLM applies the ADR-008 peer test and finds that a conformant
peer could legitimately decide the *mechanism* or the *exception* differently, it stops there and hands the
operational choice to the realization. Each row below is one such hand-off: the UDLM invariant DCM **must
satisfy**, and the policy DCM **must decide** to satisfy it.

This register is the DCM-side counterpart of those ADRs. An obligation is `open` until DCM ships the policy
that discharges it. Add a row whenever a UDLM ADR carries a "Delegated work — the DCM policy obligation"
section.

| ID | Obligation | UDLM source | Status |
|---|---|---|---|
| OBL-001 | Credential-material intake mechanism | UDLM ADR-049 | **open** |
| OBL-002 | Provider-pin eligibility bypass | UDLM ADR-050 | **open** |

---

## OBL-001 — Credential-material intake mechanism

**UDLM invariant DCM must satisfy** (ADR-049 / `CPX-013`/`CPX-014`): a credential *literal* submitted where
a *reference* is required is detected and refused; the detection is **ordered before** the intent is
persisted; and the rejecting path persists neither the material nor an echo of it — not in the (immutable)
Intent store, not in the error payload, not in the audit `detail`. Ordering is part of the invariant: a
correct decision taken *after* the write is a failed decision, because the store cannot take it back out.

**Policy DCM must decide:**
- **The mechanism.** Scan-before-persist, intake-time coercion-to-a-reference, or another shape that meets
  the invariant. (ADR-049's catalogue is informative — the honest costs are laid out there so this decision
  need not rediscover them.)
- **The profile floor.** Which profiles accept detect-and-refuse, and which **raise the floor to coercion**
  (the credential provider stores the literal and returns a reference; the persisted intent is well-formed).
  Same profile-priced rigor as bare-vs-governed vocabulary.
- **The false-positive remedy** for the scan path — most plausibly a reviewable per-field opt-out declared
  on the type.
- **Under coercion:** record the transformation + provenance (the vocabulary-ladder discipline), and price
  the narrow `CPX-001` exception — hand-off only, never at rest, never logged.

**Definition of done:** a profile-governed policy that meets the invariant on the consumer-intent path, and
a passing run of UDLM must-reject `003-inline-credential-literal-refused` under DCM's realization.

---

## OBL-002 — Provider-pin eligibility bypass

**UDLM invariant DCM must satisfy** (ADR-050 / `PRV-009`/`PRV-011`): the `effective_capabilities` ceiling
**always applies at the dispatch boundary, on every path**. A pin is **preference among eligible providers**
— it decides *which* eligible provider, never *whether* an ineligible one is reached. A pin naming an
ineligible provider yields `placement.capability_mismatch` **before dispatch**. A capability mismatch is a
`policy_violation`, never a `provider.*` failure (the provider did not break; it was never eligible).

**Policy DCM must decide:**
- **Whether a deliberate bypass exists at all**, per profile — the genuine case of a provider that *can* do
  the work but never declared it. If permitted, its shape: the **override-record flow** (approver, reason,
  scope, time bound — the priced default) or a two-field split (clarity at the cost of a larger surface).
- **The deprecation window** for operators relying on today's absolute-pin behaviour, and the
  declaration-defect remedy (fix the stale declaration) named in the same change — so no operator's pin
  simply "stops working" without a path.
- **The placement-algorithm text**: amend the step that describes the pin as skipping the remaining steps,
  so the eligibility check is unconditional at the dispatch boundary.

**Definition of done:** placement enforces the ceiling on every path (pin included); any bypass is a
recorded, approved, time-bounded override whose permissibility is set per profile; a passing run of UDLM
must-reject `005-provider-capability-mismatch-refused`, typed `policy_violation`.
