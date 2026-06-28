---
Document Status: ✅ Complete
Document Type: Architecture Reference — Scoring Model Specification
---

# DCM Data Model — Hybrid Scoring Model

> **DCM-native scoring engine; no single UDLM contract counterpart.**
> The hybrid scoring model is a realization-layer extension of the Policy
> abstraction — UDLM defines no scoring contract. A peer DCM realization could
> use a different signal-weighting scheme and still satisfy every UDLM Policy
> and Governance Matrix contract. The Governance Matrix remains a pure boolean
> gate; scoring never applies to cross-boundary data decisions.


**Document Status:** ✅ Complete
**Document Type:** Architecture Reference — Scoring Model Specification
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md) | [Policy Profiles](../governance-enforcement/policy-profiles.md) | [Control Plane Components](../control-plane/components.md) | [Governance Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md) | [Federated Contribution Model](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md)

> **This document maps to: DATA + POLICY**
>
> The Scoring Model is an extension of the Policy abstraction. Scored signals are Data artifacts with lifecycle and provenance. Profile thresholds are Policy-governed configuration. The Governance Matrix remains a pure boolean gate — scoring never applies to cross-boundary data decisions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
> > **See also:** [Authority Tier Model](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) — the ordered authority tier list, custom tier definition, dynamic threshold format, and ATM system policies.

> **Design Priority:** The Scoring Model is the primary mechanism for Priority 2 (ease of use) in service of Priority 1 (security). The auto-approval threshold (SMX-008: ≤ 50) and compliance-class Gating Policies are non-negotiable security properties. Profile thresholds and signal weights are the ease-of-use scaling mechanism. See [Design Priorities](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md).

---

## 1. Purpose and Governing Principle

DCM uses a **hybrid scoring model**: some decisions are boolean gates (facts), others are scored signals (degrees). The governing principle is explicit:

> **Questions of fact use boolean gates. Questions of degree use scoring.**

A secondary test for any ambiguous decision:
> **Can a regulator accept "the score was below threshold" as a complete explanation? If not, the decision must be boolean.**

This document specifies the scoring half of the hybrid. For boolean decisions, see [Governance Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md) and the compliance enforcement model in [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md).

### 1.1 What This Model Does

The scoring model adds three capabilities to the existing architecture:

1. **Operational Gating policies** contribute a weighted risk score instead of producing a binary deny. The aggregate score drives approval routing.
2. **Advisory Validation policies** produce a completeness score and warning list without blocking the request.
3. **Five scoring signals** aggregate into a request risk score that determines approval routing tier — replacing the current per-policy approval flag with a continuous, profile-governed threshold system.

### 1.2 What This Model Does Not Do

The scoring model does **not**:
- Apply to Governance Matrix decisions — these remain boolean always
- Apply to compliance-class Gating policies — PHI→BAA, sovereign data→sovereign provider remain hard gates
- Apply to authentication, authorization, or five-check boundary enforcement
- Apply to lifecycle state transitions
- Replace the Policy Engine — it is a function within it

---

## 2. Gating Policy Enforcement Classes

Every Gating policy declares an `enforcement_class`. This is a required field in the Policy base contract (added in this document).

```yaml
enforcement_class: compliance | operational
```

### 2.1 Compliance Class

Behavior: **boolean gate**. A compliance-class Gating Policy that fires produces a `deny` decision. The request is halted immediately. No score is produced.

**Use for:**
- Data classification boundary rules (PHI requires BAA accreditation)
- Sovereignty violations (classified data leaving declared zone)
- Security hard requirements (unencrypted data, expired certificates)
- Regulatory mandates with no legitimate override path
- Any rule where "score-around" creates legal or compliance liability

```yaml
# Example compliance-class Gating Policy
policy_type: gating
enforcement_class: compliance
handle: "system/compliance/phi-baa-required"
match:
  payload_type: request.layers_assembled
  conditions:
    - field: payload.data_classification
      operator: contains
      value: phi
    - field: payload.provider.accreditations
      operator: not_contains
      value: baa_active
output:
  decision: deny
  reason: "PHI data requires provider with active BAA. Provider has no active BAA."
  audit_required: true
  notify_on: [DENY]
```

### 2.2 Operational Class

Behavior: **risk score contribution**. An operational-class Gating Policy that fires contributes a weighted score to the request risk score. The request is not immediately halted. Instead the aggregate score determines routing.

**Use for:**
- Cost ceiling policies (request cost exceeds Tenant recommendation)
- Resource sizing policies (CPU/memory above recommended maximums)
- Unusual timing or context (off-hours request, unusual field combinations)
- Quota pressure (Tenant approaching quota limit)
- Business rule preferences that should escalate review, not block

```yaml
# Example operational-class Gating Policy
policy_type: gating
enforcement_class: operational
handle: "tenant/payments/gating/cost-ceiling"
scoring_weight: 35           # contribution to request risk score when fired
match:
  payload_type: request.layers_assembled
  conditions:
    - field: payload.cost_estimate.per_month
      operator: gt
      value: 500
output:
  risk_score_contribution: 35
  reason: "Estimated monthly cost ${{payload.cost_estimate.per_month}} exceeds Tenant ceiling $500"
  label: "cost_ceiling_exceeded"
  audit_required: true
```

### 2.3 Profile-Level Enforcement Class Override

Profiles can override the enforcement class of individual policies. This is the mechanism for making the scoring system tunable without touching individual policies.

```yaml
# In a profile definition:
policy_enforcement_overrides:
  - policy_handle: "tenant/payments/gating/cost-ceiling"
    override_enforcement_class: compliance   # escalate to hard gate in this profile
    rationale: "FSI profile: all cost violations are hard gates"

  - policy_handle: "system/security/off-hours-request"
    override_enforcement_class: operational  # demote to soft score in dev profile
    rationale: "Dev profile: off-hours requests are expected; score but don't block"
```

**Hard constraint:** A profile can **only** override `operational → compliance` or `compliance → operational` for explicitly non-regulatory policies. Policies with `regulatory_mandate: true` in their metadata cannot be demoted to operational by any profile.

---

## 3. Validation Output Classes

Every Validation policy declares an `output_class`. This is a required field.

```yaml
output_class: structural | advisory
```

### 3.1 Structural Class

Behavior: **boolean pass/fail**. A structural Validation that fails halts the request. No score is produced.

**Use for:**
- Required field presence (missing required fields)
- Type correctness (wrong field type)
- Referential integrity (UUID references that don't resolve)
- Format validation (malformed handle, invalid semver)
- Schema conformance

### 3.2 Advisory Class

Behavior: **completeness score contribution + warning list**. An advisory Validation that fires contributes to the completeness score and adds a warning to the advisory_warnings list. The request is not halted.

**Use for:**
- Recommended fields absent (cost_center not provided)
- Unusual values (memory_gb at 1 for a database VM — unusual but not invalid)
- Low-confidence field values (field sourced from a provider with confidence < 0.5)
- Naming convention violations (non-compliant resource name — advisory only)

```yaml
policy_type: validation
output_class: advisory
handle: "platform/advisory/cost-center-recommended"
scoring_weight: 10
match:
  payload_type: request.layers_assembled
output:
  completeness_contribution: 10
  warning_code: "recommended_field_absent"
  warning_message: "cost_center not provided — cost attribution will use Tenant default"
  field: "fields.cost_center"
```

---

## 4. The Five Scoring Signals

The request risk score is assembled from five independent signals. Each signal is normalized to 0–100. The aggregate is a weighted sum, also normalized to 0–100.

### 4.1 Signal 1 — Operational Gating Policy Score

**Source:** All operational-class Gating policies that fired during policy evaluation.
**Composition:** Sum of `risk_score_contribution` values from all fired operational Gating Policies.
**Normalization:** Capped at 100 before weighting. Multiple Gating Policies can fire; their contributions accumulate.
**Default weight in aggregate:** 0.45

```yaml
operational_gating_score:
  fired_policies:
    - handle: "tenant/payments/gating/cost-ceiling"
      contribution: 35
      reason: "Cost $620/month exceeds ceiling $500"
    - handle: "platform/gating/off-hours"
      contribution: 15
      reason: "Request submitted outside business hours"
  raw_score: 50     # sum of contributions
  normalized: 50    # already within 0-100
```

### 4.2 Signal 2 — Policy Completeness Score

**Source:** All advisory-class Validation policies that fired.
**Composition:** Sum of `completeness_contribution` values from all fired advisory Validations.
**Normalization:** Capped at 100. Score represents "how incomplete is this request" — higher = more warnings.
**Default weight in aggregate:** 0.15

### 4.3 Signal 3 — Actor Risk History Score

**Source:** Decay-weighted history of the actor's previous request outcomes.
**Composition:** Each historical event has a base score contribution and a time-decay multiplier.
**Decay model:** `contribution × e^(-λt)` where `t` is days since event, `λ` = 0.1 (half-life ≈ 7 days).
**Normalization:** 0–100. A clean history = 0. Recent consecutive failures approach 100.
**Default weight in aggregate:** 0.20

```yaml
# Events that contribute to actor risk history score
actor_risk_events:
  - event: validation_failure        # base_contribution: 5
  - event: gating_deny           # base_contribution: 10
  - event: compliance_deny           # base_contribution: 20
  - event: policy_override_requested # base_contribution: 8
  - event: drift_caused              # base_contribution: 15
  - event: decommission_forced       # base_contribution: 12
  - event: request_abandoned         # base_contribution: 3
```

**Privacy constraint:** Actor risk history scores are never exposed in consumer-facing API responses beyond the actor's own history. They are available in the Admin API for platform admins and in the audit trail.

### 4.4 Signal 4 — Tenant Quota Pressure Score

**Source:** Current quota utilization for the resource type being requested.
**Composition:** `max(0, (utilization_pct - free_threshold) / (1 - free_threshold)) × 100`
**Free threshold:** 0.75 (quota pressure score = 0 below 75% utilization).
**At 100% utilization:** quota pressure = 100, but the hard quota gate also fires (blocking the request regardless of score).
**Default weight in aggregate:** 0.10

```yaml
quota_pressure_score:
  resource_type: "Compute.VirtualMachine"
  current_usage: 87
  limit: 100
  utilization_pct: 0.87
  free_threshold: 0.75
  score: 48   # (0.87 - 0.75) / (1 - 0.75) × 100 = 48
```

### 4.5 Signal 5 — Provider Accreditation Richness Score

**Source:** Accreditation portfolio of the selected/candidate provider.
**Composition:** Weighted sum of accreditation types held, normalized against the maximum possible portfolio.
**Usage:** Used in placement tie-breaking (supplements existing tie-breaking algorithm). Also contributes inversely to request risk score — a richly accredited provider reduces risk.
**Default weight in aggregate:** 0.10 (inverse — higher richness = lower risk contribution)

```yaml
accreditation_weights:
  self_declared: 5
  third_party_audit: 15
  iso_27001: 20
  soc2_type2: 20
  fedramp_moderate: 30
  fedramp_high: 40
  hipaa_baa: 25
  pci_dss: 25
  sovereign_authorization: 50

# richness_score = sum(weights for held accreditations) / max_possible × 1

# Verification currency multipliers (applied per accreditation, see doc 47)
# Multiplier reduces an accreditation's weight contribution based on how recently
# it was externally verified by the Accreditation Monitor
verification_multipliers:
  external_registry_verified_within_P1D:  1.0   # full weight — verified today
  external_registry_verified_within_P7D:  0.9
  document_verified_within_P30D:          0.85
  contract_webhook_active:                0.9
  expiry_only_no_external_check:          0.7   # never been externally verified
  verification_stale:                     0.4   # check overdue
  verification_failed_threshold_reached:  0.1   # Monitor cannot reach registry00
# risk_contribution = (1 - richness_score/100) × 10   [lower richness = higher risk]
```

### 4.6 Aggregate Request Risk Score

```
request_risk_score =
  (operational_gating_score × 0.45) +
  (completeness_score           × 0.15) +
  (actor_risk_history_score     × 0.20) +
  (quota_pressure_score         × 0.10) +
  (provider_risk_contribution   × 0.10)

# Normalized: 0–100
# 0  = clean request, no concerns
# 100 = maximum risk signal across all dimensions
```

Signal weights are profile-governed and can be adjusted per deployment. The weights above are the `standard` profile defaults.

---

## 5. Profile-Governed Thresholds

Every profile declares scoring thresholds that map the continuous risk score to a discrete approval routing decision.

```yaml
# Approval routing uses named tier thresholds — see Authority Tier Model (doc 32)
# Tier names are resolved from the ordered authority tier list; numeric weights are derived.
scoring_thresholds:
  approval_routing:
    - tier: auto
      max_score: 24          # score 0–24: auto-approve (SMX-008: never exceed 50)
    - tier: reviewed
      max_score: 59          # score 25–59: reviewed tier required
    - tier: verified
      max_score: 79          # score 60–79: verified tier required
    - tier: authorized
      max_score: 100         # score 80–100: authorized tier required
  # Custom tiers (if defined) are inserted into this list; existing names unchanged.
  # "authorized" means DCM holds the pipeline and notifies the declared DCMGroup;
  # the review process and deliberation are the organization's responsibility.
  # DCM records votes via Admin API; external systems (ServiceNow, Jira, Slack)
  # may call the API on behalf of authorized group members. See [Design Priorities](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md).
  # Note: compliance-class Gating Policy deny always halts regardless of score
```

### 5.1 Per-Profile Threshold Defaults

| Profile | auto_approve | reviewed | verified | authorized | signal_weights |
|---------|-------------|-------------|--------------|-----------|----------------|
| `minimal` | < 45 | 45–74 | 75–100 | — | default |
| `dev` | < 40 | 40–69 | 70–100 | — | default |
| `standard` | < 25 | 25–59 | 60–79 | 80–100 | default |
| `prod` | < 15 | 15–49 | 50–74 | 75–100 | gating_weight: 0.50 |
| `fsi` | < 10 | 10–39 | 40–69 | 70–100 | gating_weight: 0.55, actor_weight: 0.25 |
| `sovereign` | < 5 | 5–29 | 30–59 | 60–100 | gating_weight: 0.60 |

### 5.2 Resource-Type Threshold Overrides

Profiles can declare tighter thresholds for specific resource types:

```yaml
resource_type_threshold_overrides:
  - resource_type: "Compute.VirtualMachine"
    # tier: auto, max_score: 20  # use named-tier threshold format    # tighter than profile default
  - resource_type: "Network.VLAN"
    # tier: auto, max_score: 10  # use named-tier threshold format    # VLANs require more scrutiny
  - resource_type: "Storage.Volume"
    # tier: verified, max_score: 40  # use named-tier threshold format   # storage changes escalate earlier
```

### 5.3 Tenant Threshold Overrides

Platform admins can declare Tenant-level scoring threshold adjustments:

```yaml
tenant_scoring_config:
  tenant_uuid: <uuid>
  threshold_overrides:
    # tier: auto, max_score: 15  # use named-tier threshold format    # more conservative for this Tenant
  signal_weight_overrides:
    actor_risk_history_weight: 0.30   # higher actor scrutiny for this Tenant
  trusted_actors:
    - actor_uuid: <uuid>
      actor_risk_history_score_override: 0   # zero out risk history for trusted automation
```

### 5.4 Switching Between Scoring and Boolean Per Policy

A profile can declare that a specific operational-class policy should behave as boolean (compliance-class) in that profile's context:

```yaml
# In profile definition:
policy_enforcement_overrides:
  - policy_handle: "platform/gating/cpu-size-limit"
    override_enforcement_class: compliance
    rationale: "Prod profile: CPU limit is a hard constraint, not a risk signal"
    applies_to_resource_types: ["Compute.VirtualMachine"]
```

And conversely, a compliance-class policy that is **not** a regulatory mandate can be demoted to operational in lower-trust profiles:

```yaml
  - policy_handle: "platform/gating/naming-convention"
    override_enforcement_class: operational
    scoring_weight_override: 20
    rationale: "Dev profile: naming violations are warnings, not blocks"
    requires_regulatory_mandate_false: true   # safety check
```

---

## 6. Score Lifecycle and Audit Trail

### 6.1 Score Record Structure

Every scored evaluation produces a Score Record stored in the Audit Store alongside the standard audit record:

```yaml
score_record:
  score_record_uuid: <uuid>
  request_uuid: <uuid>
  entity_uuid: <uuid>
  evaluated_at: <ISO 8601>
  
  request_risk_score: 47
  routing_decision: reviewed
  routing_threshold_applied: 25      # the threshold that triggered this tier
  profile_uuid: <uuid>
  
  signal_breakdown:
    operational_gating:
      score: 50
      weight: 0.45
      weighted_contribution: 22.5
      fired_policies:
        - handle: "tenant/payments/gating/cost-ceiling"
          contribution: 35
        - handle: "platform/gating/off-hours"
          contribution: 15
    completeness:
      score: 20
      weight: 0.15
      weighted_contribution: 3.0
      advisory_warnings: 2
    actor_risk_history:
      score: 30
      weight: 0.20
      weighted_contribution: 6.0
      recent_events: 2
    quota_pressure:
      score: 48
      weight: 0.10
      weighted_contribution: 4.8
    provider_risk:
      score: 15
      weight: 0.10
      weighted_contribution: 1.5
  
  compliance_gates_evaluated: 3
  compliance_gates_fired: 0         # if any > 0: request halted regardless of risk score
```

### 6.2 Score Immutability

Score Records are immutable once written. Threshold changes do not retroactively alter historical Score Records. If thresholds change, requests evaluated before the change retain their original routing decisions in the audit trail.

### 6.3 Human Override of Score-Based Routing

A platform admin or reviewer can override a score-based routing decision with a recorded justification. The override is audited, but the Score Record is never modified — instead an Override Record is written referencing the original Score Record.

---

## 7. Score Exposure in APIs

### 7.1 Consumer-Facing Score Exposure

Consumers receive a simplified score view:
- `risk_score` on request status (integer 0–100)
- `routing_decision` (auto_approved | pending_review | pending_verified | pending_authorized)
- `advisory_warnings` list from advisory Validation
- `score_drivers` — human-readable list of the top 3 contributing factors (no raw weights)

Consumers **do not** receive:
- Actor risk history score breakdown (privacy)
- Signal weights
- Provider accreditation richness detail

### 7.2 Platform Admin Score Exposure

Platform admins receive full Score Record detail via the Admin API including all signal breakdowns, weights, and actor risk history detail.

---

## 8. Relationship to Existing Decision Model

The scoring model slots into the existing pipeline without replacing any component:

```
Policy Engine evaluation run:
  1. Evaluate all matching policies (existing behavior)
  2. Compliance-class Gating Policy fires → HALT (existing deny behavior)
  3. Structural Validation fails → HALT (existing fail behavior)
  4. Governance Matrix DENY fires → HALT (existing behavior, unchanged)
  5. NEW: Collect operational Gating Policy contributions → Signal 1
  6. NEW: Collect advisory Validation contributions → Signal 2
  7. NEW: Fetch actor risk history score → Signal 3
  8. NEW: Calculate quota pressure score → Signal 4
  9. NEW: Calculate provider accreditation richness → Signal 5
  10. NEW: Aggregate → request_risk_score
  11. NEW: Apply profile thresholds → routing_decision
  12. NEW: Write Score Record to Audit Store
  13. Route request: auto_approve | queue_for_review | queue_dual | queue_authorized
```

Steps 2–4 handle standard policy evaluation. Steps 5–13 extend the model with scoring and approval routing.

---

## 9. System Policies

| Policy | Rule |
|--------|------|
| `SMX-001` | Every Gating policy must declare `enforcement_class: compliance` or `enforcement_class: operational`. Policies without a declared enforcement_class are treated as compliance-class. |
| `SMX-002` | Every Validation policy must declare `output_class: structural` or `output_class: advisory`. Policies without a declared output_class are treated as structural. |
| `SMX-003` | Compliance-class Gating policies with `regulatory_mandate: true` cannot be overridden to operational by any profile. This flag is set by platform admins and is audited. |
| `SMX-004` | The Governance Matrix is always boolean. No Governance Matrix Rule may declare a scoring weight or enforcement_class. |
| `SMX-005` | Signal weights in a profile must sum to 1.00. Profiles with invalid weight sums fail validation at activation time. |
| `SMX-006` | Score Records are immutable. Threshold changes do not retroactively alter historical Score Records. |
| `SMX-007` | Actor risk history scores are not exposed to consumers beyond the actor's own history. Platform admins have full access. |
| `SMX-008` | A profile's `auto_approve_below` threshold may not exceed 50. Auto-approving requests with risk scores above 50 is prohibited in all profiles. |
| `SMX-009` | Operational-class Gating Policy `scoring_weight` values must be declared between 1 and 100. Weights above 100 are validation errors. The aggregate of all fired policies is capped at 100 before weighting. |
| `SMX-010` | Score breakdown must be included in the audit trail for every request that receives a routing decision. A request with no Score Record is an audit integrity violation. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
