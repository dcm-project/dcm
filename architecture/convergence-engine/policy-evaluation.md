---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Governance Matrix Evaluator
Established: 2026-05-26
Maps to: udlm/governance/governance-matrix.md
---

# Convergence Engine — Policy Evaluation (Governance Matrix Evaluator)

> **Implements contracts defined in UDLM**:
> [udlm/governance/governance-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md).
> UDLM defines the unified governance matrix as the single enforcement point
> for cross-boundary decisions, the four matrix axes (subject / data / target /
> context), the decision vocabulary (ALLOW / DENY / ALLOW_WITH_CONDITIONS /
> STRIP_FIELD / REDACT / AUDIT_ONLY), the hard-vs-soft enforcement
> distinction, and field-level controls. DCM operationalizes the evaluation
> algorithm, the caching, the sovereignty zone management, and the integration
> with the convergence pipeline.

> **Manifest note**: this file is THE matrix evaluator. The DCM split
> manifest had a duplication bug that listed file 14-policy-profiles under
> both `convergence-engine/policy-evaluation.md` and
> `governance-enforcement/policy-profiles.md`. Resolution: file 14 lives at
> `governance-enforcement/policy-profiles.md` (it's pure-dcm and already
> moved). This file holds only the DCM matrix evaluator content from #10
> (27-governance-matrix). The redundant `governance-enforcement/matrix-evaluator.md`
> was not created — see report.

---

## 1. Evaluation algorithm

The Policy Manager evaluates the governance matrix at every interaction
boundary: provider dispatch, federation tunnel data transmission,
notification delivery, registration acceptance, and any cross-boundary
capability invocation. The evaluation runs the same algorithm against the
same rule set on every interaction. No parallel enforcement paths exist.

```
Interaction attempt arrives at boundary:
  subject  = { type, identity, accreditation_level, tenant }
  data     = { classification, resource_type, field_paths, capability }
  target   = { type, identity, sovereignty_zone, accreditation_held, trust_posture }
  context  = { profile, zero_trust_posture, federated, cross_jurisdiction, ... }

Step 1: Collect matching rules
  Load all active governance matrix rules across all tiers (system, platform,
    tenant, resource_type, entity)
  For each rule: evaluate the four axes against the interaction
  Result: set of matching rules with decisions and enforcement levels

Step 2: Evaluate hard constraints first
  For each hard DENY rule that matches → DENY immediately; record rule_uuid;
    no further evaluation
  For each hard ALLOW rule that matches → record as hard allow candidate
  If hard DENY exists → terminal decision = DENY

Step 3: Evaluate soft constraints by domain precedence
  Sort matching soft rules: entity > resource_type > tenant > platform > system
  At each precedence level, most restrictive wins:
    DENY > STRIP_FIELD > REDACT > ALLOW_WITH_CONDITIONS > AUDIT_ONLY > ALLOW
  If DENY at any level → terminal decision = DENY

Step 4: Evaluate conditions for ALLOW_WITH_CONDITIONS
  For each ALLOW_WITH_CONDITIONS rule that survived Steps 2-3:
    Evaluate all declared conditions
    If any condition fails → downgrade to DENY
    If all conditions pass → decision remains ALLOW_WITH_CONDITIONS

Step 5: Apply field permissions
  If terminal decision is ALLOW or ALLOW_WITH_CONDITIONS:
    Apply field_permissions per governing rule:
      allowlist mode: strip all fields not in allowed list
      blocklist mode: strip all fields in blocked list
      passthrough mode: all fields pass
    For each stripped field:
      If field is required → escalate to DENY_REQUEST
      If field is optional → STRIP_FIELD (proceed without it)

Step 6: Produce audit record
  Record: interaction_uuid, all matching rules, terminal decision,
          fields stripped or redacted, governing rule_uuid
  Notification: if terminal decision is in rule's notification_on list

Step 7: Enforce decision
  ALLOW / ALLOW_WITH_CONDITIONS → interaction proceeds with permitted fields
  DENY → interaction blocked; 403 response with governance_matrix_rule_uuid
  STRIP_FIELD → interaction proceeds with stripped payload
  REDACT → interaction proceeds with redacted field values
  AUDIT_ONLY → interaction proceeds; flagged audit record written
```

---

## 2. Hard enforcement mechanics

Hard rules (UDLM contract: `enforcement: hard`) cannot be relaxed by any
downstream rule at any domain level. DCM enforces this by:

- At evaluation time, **hard DENY short-circuits** the entire rule set —
  Steps 3-5 are skipped
- **No tenant-level, entity-level, or operator override** can permit an
  interaction blocked by a hard DENY; the override is rejected at policy
  contribution time by the Governance Matrix evaluator itself (the meta-rule
  that consumer/tenant policies cannot modify system-domain hard rules)
- **Hard ALLOW** is rare and explicitly tracked; auditors can query for all
  hard ALLOW rules to confirm none have been added inadvertently

DCM ships pre-configured hard DENY rules for:

- `sovereign` and `classified` data classifications crossing any boundary in
  any profile (GMX-004)
- PHI without HIPAA BAA at federation boundaries (HIPAA compliance domain)
- Cross-jurisdiction transfer of restricted data in `fsi` profile

These hard rules are activated automatically by the active profile and
compliance domain. The set is documented in the profile activation manifest.

---

## 3. Soft enforcement execution

Soft rules establish defaults that downstream (more specific) rules can
tighten — but never relax. DCM enforces this by:

- Sorting matching rules by domain precedence: entity > resource_type >
  tenant > platform > system
- At each level, computing the most restrictive decision across all matching
  rules at that level (`DENY > STRIP_FIELD > REDACT > ALLOW_WITH_CONDITIONS
  > AUDIT_ONLY > ALLOW`)
- Walking precedence levels from most-specific to least-specific; **a more
  restrictive decision at any level wins**; a less restrictive decision at a
  more specific level is rejected at policy contribution time (the rule never
  becomes active)

A soft DENY at the system level cannot be relaxed to ALLOW by a
tenant-level rule. The Governance Matrix evaluator detects the attempted
relaxation and rejects the policy contribution at submission time with
`GMX_SOFT_DENY_CANNOT_BE_RELAXED`.

---

## 4. Caching and invalidation

Policy evaluation is on the hot path for every interaction. DCM caches:

- **Compiled rule sets** — the active matrix rule set is compiled to an
  in-memory evaluation tree per Policy Manager instance; recompiled on rule
  change events (`policy.activated`, `policy.deactivated`,
  `policy.deprecated`)
- **Per-actor permission cache** — for a session, the actor's role/tenant
  scope and matching subject-axis rules are cached for the session TTL
  (PT15M–PT8H per profile)
- **Per-provider accreditation cache** — accreditation state for target
  evaluations cached for `accreditation_cache_ttl` per profile (PT5M
  standard, PT1M fsi/sovereign)

**Invalidation triggers:**

- Policy activation/deactivation event → recompile rule set; emit
  `policy.cache_invalidated` to all Policy Manager instances
- Actor session revocation (via SES-001 model) → drop actor's permission cache
- Accreditation status change (from Accreditation Monitor) → drop provider's
  accreditation cache entry
- Credential revocation event → permission cache entries referencing the
  credential are dropped

Cache invalidation propagates via PostgreSQL `LISTEN/NOTIFY` and completes
within PT5S in standard deployments. In `fsi`/`sovereign` profiles,
cache TTL is shortened to PT1M (or per-call evaluation in `sovereign`) to
limit stale-cache risk.

---

## 5. Sovereignty zone management

Sovereignty zones are first-class UDLM artifacts (
[udlm/governance/governance-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md)).
DCM operationalizes them via:

- **Zone registry** — sovereignty zones stored as DCM artifacts with handle,
  jurisdictions, regulatory frameworks, data residency guarantee, inter-zone
  agreements
- **Resolution layer** — at policy evaluation, target sovereignty zone is
  resolved from the target's registration (provider sovereignty declaration,
  peer DCM zone, etc.)
- **Hard rule for sovereign data** — sovereign-classified data carries a
  hard DENY for all federation and external-provider interactions in all
  profiles including minimal; the rule is shipped pre-activated and cannot
  be modified by tenant or platform policies

### 5.1 Zone evaluation in placement

When the Placement Manager runs Step 1 (sovereignty pre-filter), it queries
the sovereignty zone of every eligible provider and eliminates any provider
whose zone is not in the request's permitted zones list. This is a
pre-filter, not a tie-breaker — sovereignty failures eliminate providers
from the placement loop entirely.

### 5.2 Inter-zone agreements

A sovereignty zone may declare `inter_zone_agreements` — explicit data
transfer agreements with other zones (e.g., EU adequacy decision for
transfers within EU member states). The matrix evaluator consults
`inter_zone_agreements` when evaluating cross-zone interactions; transfers
permitted by an agreement are evaluated at the agreement's permitted
classification cap.

---

## 6. Profile-governed policy configurations

DCM ships pre-configured rule sets per profile. The rule set is activated
automatically when the profile is set:

| Profile | Rule set characteristics |
|---|---|
| `minimal` | Hard DENY only for sovereign/classified; soft ALLOW for public/internal; permissive |
| `dev` | Inherits minimal; adds soft ALLOW_WITH_CONDITIONS for confidential to verified targets |
| `standard` | Inherits minimal; adds soft ALLOW_WITH_CONDITIONS for restricted (third_party accreditation required); soft DENY for PHI without HIPAA |
| `prod` | Inherits standard; tightens federation to verified peers only for confidential+; STRIP_FIELD for restricted in notifications |
| `fsi` | Inherits prod; hard DENY for cross-jurisdiction with regulated data; hard ALLOW_WITH_CONDITIONS for PHI requiring HIPAA BAA + verified + ZT full |
| `sovereign` | Inherits fsi; hard DENY for any sensitive data crossing DCM federation; hardware attestation required for any federation |

When a compliance domain is active (HIPAA, GDPR, PCI-DSS, FedRAMP), its
matrix rules are automatically added to the active rule set. They compose
with profile rules — they do not replace them.

See [`../governance-enforcement/policy-profiles.md`](../governance-enforcement/policy-profiles.md)
for the complete profile definitions.

---

## 7. Where the evaluator runs

The Policy Manager service hosts the matrix evaluator. It is invoked from:

| Call site | When |
|---|---|
| Request Processor (during assembly) | Step 5 of nine-step assembly — evaluates all GateKeeper + Validation + Transformation + Governance Matrix rules against the assembled payload |
| Provider Dispatcher | Before provider dispatch — evaluates outbound governance matrix against the dispatch payload + target provider |
| Federation Tunnel | Before every cross-DCM message — evaluates outbound governance matrix against the message + remote DCM peer |
| Notification Router | Before every notification delivery — evaluates outbound governance matrix against the notification payload + destination |
| Webhook Subscription Resolver | When a webhook subscription is established — evaluates the matrix on the subscriber's authority for the subscribed event domain |
| Contribution Submission | When any contributor submits an artifact — evaluates contributor-permission matrix rules (see [`../governance-enforcement/contribution-pipeline.md`](../governance-enforcement/contribution-pipeline.md)) |

Every invocation produces an audit record (GMX-005), regardless of outcome.

---

## 8. Realization-specific notes

- **OPA as the evaluation engine.** DCM uses OPA (Open Policy Agent) to
  evaluate matrix rules; rules are translated to Rego at compile time. A peer
  DCM realization could use a different engine while remaining UDLM-conformant.
- **PostgreSQL as the rule store.** Active rules live in the `policies`
  table with status `active` and tier metadata. A peer could use a different
  store.
- **`LISTEN/NOTIFY` for invalidation propagation.** A peer could use Kafka
  or any other pub/sub.

These are DCM implementation choices, not UDLM contracts.
