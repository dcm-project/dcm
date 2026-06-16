---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Authority Tier Enforcement
Established: 2026-05-26
Maps to: udlm/governance/authority-tier-model.md
---

# Authority Enforcement

> **Implements contracts defined in UDLM**:
> [udlm/governance/authority-tier-model.md](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md).
> UDLM defines the core authority tier model (auto / reviewed / verified /
> authorized), the decision_gravity vocabulary, the custom tier definition
> contract, the tier registry change impact detection contract, and the
> degradation review gate contract. DCM operationalizes the tier evaluation
> algorithm, approval authority mapping, profile threshold configuration,
> DCMGroup assignment, tier enforcement at decision points, and the
> degradation review orchestration.

---

## 1. Tier evaluation algorithm

DCM evaluates required tier at every approval-gated decision point. The
algorithm:

```
At decision evaluation time:
  ▼ 1. Compute the request risk score (0–100) via the Scoring Model
  ▼ 2. Load the active profile's threshold list
  ▼ 3. Walk the list in order; the first tier whose max_score ≥ risk_score
       is the required tier
  ▼ 4. Resolve the numeric weight of the required tier from the ordered
       tier registry
  ▼ 5. Create an approval record with the required tier name and weight
```

The tier **name** (not the weight) is what's stored in the approval record
and shown to reviewers. The weight is used for comparison operations
(e.g., "is this action at least as significant as `verified`?").

### 1.1 Approval record

```yaml
approval_record:
  approval_uuid: <uuid>
  subject_uuid: <uuid>
  subject_type: request | policy_contribution | provider_registration | federation_contribution
  required_tier: verified           # tier name — stable reference
  required_tier_weight: 3           # resolved at creation; point-in-time audit
  required_tier_gravity: elevated
  dcmgroup_uuid: <uuid | null>      # non-null only for dcmgroup_required: true tiers
  quorum_threshold: <N | null>
  status: pending_reviewed | pending_verified | pending_authorized | pending_<custom_tier>
  created_at: <ISO 8601>
  window_expires_at: <ISO 8601>
  decisions: []
```

The `required_tier_weight` is **stored at creation** (`ATM-008`). If the
tier registry changes later, the stored weight reflects the state at
creation — point-in-time audit.

---

## 2. Approval authority mapping

DCM enforces each tier per the contract:

| Tier | DCM gate |
|---|---|
| `auto` | All structural and governance validation checks pass; automatic activation |
| `reviewed` | One actor with reviewer role records a decision via `POST /api/v1/admin/approvals/{uuid}:vote` |
| `verified` | Two distinct actors with reviewer role each record a decision (DCM enforces actor distinctness — same actor cannot satisfy both) |
| `authorized` | N members of a declared DCMGroup record decisions; DCM tracks quorum (N of M); pipeline advances when N reached |

### 2.1 Admin API as integration point

DCM's vote-recording endpoint is designed for external system integration,
not only humans-in-UI:

```
POST /api/v1/admin/approvals/{approval_uuid}:vote
Authorization: Bearer <token>     # any actor who is a member of the required DCMGroup
{
  "decision": "approve | reject",
  "reason": "<human-readable rationale>",
  "recorded_via": "dcm_admin_ui | servicenow | jira | slack_bot | api_direct | other",
  "external_reference": "<ticket or case ID — optional>"
}
→ {
    "approval_uuid": "<uuid>",
    "voter_uuid": "<uuid>",
    "decision": "approve",
    "votes_recorded": 2,
    "quorum_required": 3,
    "quorum_reached": false,
    "pipeline_status": "pending_authorized"
  }
```

The `recorded_via` field provides audit provenance — informational, not
enforced. DCM does not care whether the vote came from a Slack bot, ServiceNow
integration, Jira plugin, or direct API call — only that an authorized actor
recorded it.

### 2.2 Deadline and escalation

```yaml
approval_window:
  reviewed: PT72H
  verified: PT72H
  authorized: P7D
  on_expiry:
    reviewed:  escalate
    verified:  escalate
    authorized: reject
```

When the window expires without a decision, DCM fires an escalation
notification. For `reviewed` and `verified`, escalates to platform admin or
the next tier. For `authorized`, rejects (cannot lower the authority gate
silently).

---

## 3. Profile threshold configuration

DCM ships per-profile threshold defaults:

```yaml
profile_approval_thresholds:
  minimal:
    - { tier: auto,       max_score: 44 }
    - { tier: reviewed,   max_score: 100 }

  dev:
    - { tier: auto,       max_score: 39 }
    - { tier: reviewed,   max_score: 69 }
    - { tier: verified,   max_score: 100 }

  standard:
    - { tier: auto,       max_score: 24 }
    - { tier: reviewed,   max_score: 59 }
    - { tier: verified,   max_score: 79 }
    - { tier: authorized, max_score: 100 }

  prod:
    - { tier: auto,       max_score: 14 }
    - { tier: reviewed,   max_score: 49 }
    - { tier: verified,   max_score: 74 }
    - { tier: authorized, max_score: 100 }

  fsi:
    - { tier: auto,       max_score: 9 }
    - { tier: reviewed,   max_score: 39 }
    - { tier: verified,   max_score: 69 }
    - { tier: authorized, max_score: 100 }

  sovereign:
    - { tier: auto,       max_score: 4 }
    - { tier: reviewed,   max_score: 29 }
    - { tier: verified,   max_score: 59 }
    - { tier: authorized, max_score: 100 }
```

**SMX-008 in the dynamic model:** `auto.max_score` may never exceed 50 in any
profile, regardless of custom tier additions. DCM enforces this at profile
contribution time (`ATM-002`).

### 3.1 Custom tier insertion

When an organization adds a custom tier (e.g., `compliance_reviewed` between
`verified` and `authorized`), DCM:

1. Validates `decision_gravity` is consistent with position (`ATM-003`)
2. Requires `verified` tier approval to add the tier (`ATM-004`)
3. Re-resolves numeric weights from list position (`ATM-001`)
4. Triggers the Tier Registry Change Impact Detection pipeline (Section 5)

Existing references to `authorized` continue to work — the name is stable;
the weight is updated.

---

## 4. DCMGroup assignment

When a decision requires the `authorized` tier (or any custom tier with
`dcmgroup_required: true`), DCM resolves the required DCMGroup and quorum
threshold from the profile or per-action-type config:

```yaml
authorized_tier_configuration:
  default_dcmgroup_handle: platform/security-council
  quorum_threshold: "2 of 5"

  # Per-action-type overrides
  action_type_overrides:
    - subject_type: provider_registration
      provider_type: service_provider
      dcmgroup_handle: platform/credential-governance
      quorum_threshold: "3 of 5"
    - subject_type: federation_contribution
      dcmgroup_handle: platform/federation-council
      quorum_threshold: "2 of 3"
    - subject_type: policy_contribution
      policy_domain: system
      dcmgroup_handle: platform/policy-governance
      quorum_threshold: "3 of 5"
```

DCM enforces:
- Required DCMGroup must be declared before the tier can be used as a
  routing target (`ATM-006`)
- Each decision is attributed to the specific DCMGroup member who recorded it
- The audit record links to the DCMGroup at decision time (point-in-time
  membership)

---

## 5. Tier enforcement at decision points

DCM applies the tier evaluation algorithm at every decision point:

| Decision point | Trigger |
|---|---|
| Resource request | Risk score computed; threshold resolved; approval record created (if non-auto) |
| Policy contribution | Per `contribution_policy` in active profile; tier resolved based on contributor + artifact type + profile |
| Provider registration | Per `provider_type_registry.default_approval_method`; tier resolved at registration submission |
| Federation contribution | Per peer trust posture × profile contribution_policy |
| Sovereignty zone change | Tier resolved at change submission; typically `authorized` |
| Auth Provider update | Tier resolved at update; typically `verified` in standard+ |
| Federation policy update | Tier resolved per policy domain |

In every case, the approval record drives the pipeline. The pipeline holds
in `pending_<tier>` state until quorum is reached or the deadline expires.

---

## 6. Degradation review orchestration

UDLM defines the tier registry change impact detection contract. DCM
operationalizes the detection pipeline.

### 6.1 Tier impact diff computation

When a tier registry change is proposed, DCM computes the diff before
activation:

```yaml
tier_impact_diff:
  registry_change_uuid: <uuid>
  proposed_at: <ISO 8601>
  proposed_by: <actor_uuid>

  tier_changes:
    - tier_name: verified
      change_type: POSITION_CHANGED    # NEW | REMOVED | POSITION_CHANGED | GRAVITY_CHANGED | UNCHANGED
      old_position: 3
      new_position: 4
      old_gravity: elevated
      new_gravity: elevated
      net_effect: UPGRADED             # UPGRADED | DEGRADED | NEW | REMOVED | UNCHANGED

  security_degradations: []
  profile_gaps: []
  broken_references: []
```

### 6.2 Affected item query

For each changed tier, DCM queries for affected items:

| Category | Query |
|---|---|
| Pending approval records | WHERE required_tier IN (changed_tier_names) AND status LIKE 'pending_%' |
| Profile threshold configs | WHERE tier_registry_version < new_registry_version |
| Provider registration requirements | WHERE default_approval_method IN (changed_tier_names) |
| FCM contribution policy requirements | WHERE any tier reference IN (changed_tier_names) |
| Active policy sets | WHERE policy_content CONTAINS tier_name_reference |

### 6.3 Impact classification

Each affected item receives one or more classifications:

| Classification | Condition | Required action |
|---|---|---|
| `SECURITY_DEGRADATION` | Item references a tier whose gravity decreased OR position decreased | **Blocks activation** — must be reviewed and accepted |
| `SECURITY_UPGRADE` | Item references a tier whose gravity or position increased | Informational |
| `BROKEN_REFERENCE` | Item references a tier name that no longer exists | **Blocks activation** — must be resolved |
| `PROFILE_GAP` | Profile threshold list incomplete after new tier insertion | **Warning** — does not block |
| `STALE_WEIGHT` | Pending approval's stored_tier_weight differs from current | Informational |

### 6.4 Degradation review gate

Security degradations block activation. The gate requires:

1. Each `SECURITY_DEGRADATION` item presented to a reviewer at `verified` or above
2. The reviewer records an explicit acceptance via Admin API
3. The acceptance includes a reason; written to audit trail
4. Only after ALL degradations accepted does the tier registry change activate

```
POST /api/v1/admin/tier-registry/{change_uuid}:accept-degradation
{
  "affected_item_uuid": "<uuid>",
  "affected_item_type": "provider_registration_requirement",
  "degradation_classification": "SECURITY_DEGRADATION",
  "acceptance_reason": "<required — what compensating controls exist>",
  "accepted_by": "<actor_uuid>"
}
```

Broken references **cannot be accepted** — they must be resolved (tier
restored, item updated, or item cancelled). DCM will not activate a
registry change that leaves unresolvable references (`ATM-010`).

### 6.5 Impact report

DCM generates a tier registry impact report at proposed time and again at
activation time:

```yaml
tier_registry_impact_report:
  registry_change_uuid: <uuid>
  report_generated_at: <ISO 8601>
  stage: proposed | accepted | activated

  summary:
    degradations: 0
    upgrades: 3
    new_tiers: 1
    broken_references: 0
    profile_gaps: 2
    stale_weight_records: 4

  degradations: []
  upgrades: [...]
  profile_gaps: [...]

  notification_targets:
    - platform_admin
    - provider_owners
    - affected_actor_groups
```

The report is stored in the Audit Store and linked to the tier registry
version (`ATM-011`).

### 6.6 Audit trail

Every tier registry change produces:

- Registry change proposal record
- Tier impact diff record (all changes, all affected items, all classifications)
- Per-degradation acceptance records (if any)
- Registry activation record (actual effective timestamp)
- Per-affected-item notification records

---

## 7. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `ATM-001-DCM` | DCM identifies tiers by name; numeric weight resolved from list position at evaluation time |
| `ATM-002-DCM` | DCM enforces auto.max_score ≤ 50 in any profile regardless of custom tier additions |
| `ATM-003-DCM` | DCM validates custom tier decision_gravity is consistent with position |
| `ATM-004-DCM` | DCM requires verified tier approval for custom tier contributions |
| `ATM-005-DCM` | DCM rejects custom tier definitions that alter dcm_gate semantics of system tiers |
| `ATM-006-DCM` | For dcmgroup_required tiers, DCMGroup and quorum threshold must be declared before tier becomes a routing target |
| `ATM-008-DCM` | DCM stores tier name and resolved weight in approval records at creation — point-in-time audit |
| `ATM-009-DCM` | DCM blocks tier registry activation on SECURITY_DEGRADATION until each is explicitly accepted by verified-tier reviewer |
| `ATM-010-DCM` | DCM blocks tier registry activation on BROKEN_REFERENCE; must be resolved |
| `ATM-011-DCM` | DCM produces tier impact report stored in Audit Store linked to registry version |
| `ATM-012-DCM` | DCM generates warning notification for PROFILE_GAP; change may activate; admins update or acknowledge within approval window |
