---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Registry Enforcement
Established: 2026-05-26
Maps to: udlm/governance/registry-governance.md
---

# Registry Enforcement

> **Implements contracts defined in UDLM**:
> [udlm/governance/registry-governance.md](https://github.com/croadfeldt/udlm/blob/main/governance/registry-governance.md).
> UDLM defines the three-tier registry model (Core, Verified Community,
> Organization), the proposal/review/publication workflow, the versioning
> and deprecation lifecycle contract, and the Resource Type Registry
> extension contract. DCM operationalizes the enforcement: provider selection
> tie-breaking, artifact lifecycle management, and the review queue and
> approval workflow.

---

## 1. Registry governance enforcement

DCM enforces the three-tier registry workflow through the Registry Manager
service:

- **Tier 1 (DCM Core)** — write access restricted to DCM Project maintainer
  identities; PRs against the DCM core registry repository require 2
  maintainer approvals + automated validation gates + shadow validation
  period
- **Tier 2 (Verified Community)** — write access scoped to named community
  maintainers per artifact; PRs require maintainer + DCM oversight approval
- **Tier 3 (Organization)** — write access scoped to the deploying
  organization's contributors per the Contribution Pipeline (see
  [`contribution-pipeline.md`](contribution-pipeline.md))

### 1.1 Validation gates (must all pass before review)

The Registry Manager runs these gates on every PR before review begins:

1. **Schema validator** — artifact conforms to the declared type schema
2. **FQN conflict check** — no conflict with existing active entries
3. **Dependency resolution** — all declared dependencies resolve
4. **Breaking change detector** (if version > 1.0.0) — detects field
   removals, type changes, semantic shifts
5. **Test case coverage** — at least one valid example payload

A PR that fails any gate is blocked from entering review until resolved.

### 1.2 Review period enforcement

Per UDLM Section 3.2, DCM enforces minimum review periods by change type
through the PR pipeline:

| Change type | Min review | Shadow validation | Approvers |
|---|---|---|---|
| New Tier 1 type | 14 days | 14 days | 2 DCM maintainers |
| New Tier 2 type | 7 days | 7 days | 1 DCM maintainer + named tier maintainer |
| Minor version (non-breaking) | 7 days | 7 days | 1 DCM maintainer |
| Revision (config data only) | 3 days | 3 days | 1 DCM maintainer (or auto if CI passes) |
| Breaking change (major) | 21 days | 21 days | 2 DCM maintainers + community comment period |
| Deprecation | 30 days | N/A | 2 DCM maintainers + affected provider notification |
| Emergency (security) | Waived | 7 days minimum | 2 DCM maintainers + immediate notification |

The Registry Manager rejects merge attempts that violate the minimum review
period.

---

## 2. Provider selection tie-breaking

UDLM defines the registry as the source of provider definitions. DCM uses
the registry data plus runtime metrics for placement tie-breaking. When the
Placement Manager has multiple viable candidates that satisfy all
constraints equally, DCM applies this hierarchy deterministically:

```
Priority  Factor                 Condition
────────  ─────────────────────  ─────────────────────────────────────────
1         Policy preference      A Transformation policy injected a
                                 preference_score or preferred_provider_uuid

2         Provider priority      Numeric priority on provider registration
                                 Higher value = preferred (default: 50)

3         Tenant affinity        Tenant's Policy Group declares preferred
                                 providers for specific resource types

4         Cost analysis          Cost Analysis component has current data
                                 AND cost is determinable for candidates
                                 Prefer lower total cost (CapEx + OpEx)
                                 SKIP if cost data absent or incomparable

5         Least loaded           Current utilization from reserve_query
                                 If utilization differs > 10%: prefer less loaded
                                 SKIP if utilization data unavailable

6         Consistent hash        SHA-256(request_uuid + resource_type +
                                          sorted_candidate_uuids)
                                 Deterministic — same request always resolves
                                 to same provider in a stable cluster
                                 Never round-robin
```

### 2.1 Cost analysis integration

Cost analysis ranks above operational load because cost is a business
decision. When cost data is available and comparable:

- **CapEx:** provider infrastructure cost allocation per resource type
- **OpEx:** operational overhead, licensing, support costs per resource unit
- **Comparability:** same currency and time period; if not comparable
  (different currencies, missing data), skip to step 5

Cost data sourced from the Cost Analysis control plane component. If Cost
Analysis is not deployed or has no current data, the step is skipped
without blocking placement.

```yaml
placement_cost_evaluation:
  enabled: true                  # false if Cost Analysis unavailable
  data_freshness_max: PT1H       # reject cost data older than 1 hour
  comparison_threshold: 0.05     # 5% cost difference to trigger preference
  cost_components:
    - capex_allocation_per_unit
    - opex_per_unit_per_hour
    - licensing_per_unit
```

### 2.2 Provider priority declaration

```yaml
provider_registration:
  provider_priority: 100   # default 50; higher = preferred when equal
  cost_metadata:
    capex_allocation_per_unit: 12.50    # USD per VM-month
    opex_per_unit_per_hour: 0.08
    currency: USD
    last_updated: <ISO 8601>
```

Provider cost metadata may be declared statically or sourced dynamically
from Cost Analysis (`REG-011`); hybrid mode uses Cost Analysis when
available and falls back to static.

---

## 3. Artifact lifecycle management

DCM enforces the deprecation lifecycle per UDLM contracts (REG-DP-001
through REG-DP-007). The Registry Manager handles:

### 3.1 Default deprecation lifecycle policies

```yaml
deprecation_lifecycle_policies:
  REG-DP-001: { value: P30D, override: allow }         # notification period
  REG-DP-002:                                          # sunset by tier
    tier_1: P12M
    tier_2: P6M
    tier_3: organization_governed
    profile_locks: { fsi: immutable, sovereign: immutable }
  REG-DP-003: { value: P90D, override: allow }         # migration window
  REG-DP-004: { requirement: required_in_deprecation_notice, override: allow }
  REG-DP-005: { value: reject, override: not_permitted }   # retirement behavior
  REG-DP-006: { value: deprecated_runtime_state, override: allow }
  REG-DP-007: { value: P30D, override: not_permitted }     # emergency floor
```

### 3.2 Deprecation flow

```
Resource Type in active status
  ▼ Deprecation proposal (PR + 30 day review)
Status: deprecated
  │  Notifications to:
  │  - All registered providers implementing this type
  │  - All organizations with active realizations
  │  - All webhook subscriptions to registry events
  ▼ Sunset period (P12M Tier 1 / P6M Tier 2)
  │  During sunset:
  │  - New requests: succeed with deprecation warning
  │  - Existing realizations: unaffected
  │  - Drift detection: continues
  │  - Provider implementations: remain valid
  ▼ Retirement (status: retired)
  │  Existing realizations → DEPRECATED_RUNTIME state
  │  New requests → rejected (REG-DP-005)
  ▼ Migration window (P90D)
  │  Organizations migrate realizations to successor type
  │  DEPRECATED_RUNTIME entities can be decommissioned or migrated
  ▼ Post-migration window
     DEPRECATED_RUNTIME entities remain operational but unsupported
     Drift detection: continues but remediation is manual
```

### 3.3 Override defaults

Organizations override via standard policy priority:

```yaml
policy:
  domain: platform
  priority: 600.0.0
  type: gatekeeper
  rule: >
    If registry.deprecation.tier == tier_2
    THEN override: sunset_period = P12M
```

`fsi`/`sovereign` profiles lock REG-DP-002 as immutable.

---

## 4. Review queue and approval workflow

The Registry Manager exposes a review queue:

```
GET /api/v1/admin/registry/review-queue
  ?tier=1|2|3
  &change_type=new|minor|breaking|deprecation
  &assigned_to=<actor_uuid>
  &status=pending_validation|pending_review|pending_shadow|ready_to_merge
```

### 4.1 Reviewer workflow

1. Reviewer picks an item from queue
2. Inspects the PR diff, schema validation results, test cases, breaking
   change detector output
3. Records decision via `POST /api/v1/admin/registry/{pr_id}:vote`
4. On final approval: Registry Manager merges PR; artifact transitions to
   `proposed` (shadow validation period)
5. After shadow validation period without critical issues: transitions to
   `active`; available in registry feed

### 4.2 Auto-approval for low-risk changes

Per profile, certain change types may auto-approve if CI gates pass:

- Revision (config-only change): auto if CI passes in `minimal`/`dev`
  profiles
- Minor version of existing type: auto with maintainer sign-off in `dev`
- Major versions and new Tier 1: always require human review regardless of
  profile

---

## 5. Resource Type Registry — Information Provider sub-type

The Resource Type Registry is a specialized sub-type of Information Provider
(`provider_type: registry`). DCM treats it like any registered Information
Provider with extra capabilities:

```yaml
internal_registry_registration:
  provider_type: registry
  registry_url: https://registry.corp.example.com
  tier_1_source: https://registry.dcm-project.github.io
  tier_2_sources:
    - https://registry.dcm-project.github.io
    - https://registry.partner-org.example.com

  sync:
    schedule: "0 2 * * *"
    on_sync_failure: alert | use_cached | block_new_requests
    cache_ttl: P7D

  offline_mode: false
  signed_bundle_import: false
  bundle_signing_key_ref:
    service_provider_uuid: <uuid>
    secret_path: "dcm/registry/bundle-verification-key"

  sovereignty_filter:
    enabled: true
    permitted_jurisdictions: [eu-west, eu-central]

  vendor_allowlist:
    enabled: false
    permitted_vendors: [dcm-project, vmware, redhat, hashicorp]
```

Sync is event-driven via `LISTEN/NOTIFY`; the Registry Sync worker pulls
upstream on the configured schedule and applies the federated registry
model (organization mirror + air-gapped bundle import).

### 5.1 Air-gapped signed bundle

```
Online workstation (with registry access)
  Pull registry delta since last sync
  Sign with organization private key (via Credential Management Service)
  Package: registry-update-YYYY-MM-DD.bundle

  ▼ Transfer via approved secure channel

Air-gapped DCM deployment
  Verify signature against organization public key
  Import bundle → update local registry
  Emit: registry.sync_completed audit event
```

---

## 6. Registry policy enforcement

The Resource Type Registry is policy-governed. DCM enforces:

| Policy target | Example rule |
|---|---|
| `registry_sync` | If resource_type.jurisdiction_compatibility NOT CONTAINS tenant.sovereignty_zone → reject_activation |
| `registry_activation` | If resource_type.publisher NOT IN approved_vendor_list → gatekeep: require_manual_approval |
| `registry_bundle_import` | If bundle.signature_valid == false → reject: unsigned bundles not permitted |
| `registry_sync` (prod) | If active_profile == prod AND resource_type.version_delta.type == major → gatekeep: major version upgrades require manual approval |
| `registry_sync` (audit) | Always inject: sync_audit.required = true, sync_audit.reviewer = platform_admin |

### 6.1 Profile-appropriate registry policy groups

DCM ships built-in registry policy groups, activated automatically per
profile:

| Group | Profile | Behaviors |
|---|---|---|
| `system/group/registry-minimal` | minimal | Advisory; pull everything; no restrictions |
| `system/group/registry-dev` | dev | Warn on unverified sources; no vendor restrictions |
| `system/group/registry-standard` | standard | Block unverified; Tier 1+2 only; sovereignty filter |
| `system/group/registry-prod` | prod | Strict version pinning; approved vendor list; major version manual |
| `system/group/registry-fsi` | fsi | Exact version pinning; immutable sunset; dual approval |
| `system/group/registry-sovereign` | sovereign | Signed bundles only; offline; no external connectivity |

---

## 7. Version policy enforcement

DCM enforces version constraints strictly — never silently resolves to a
different version than declared:

```yaml
resource_type_version_constraint:
  resource_type: Compute.VirtualMachine
  version_policy: exact | compatible | latest_minor | latest
  pinned_version: "1.2.3"   # required if version_policy: exact
```

**DCM never automatically upgrades across major versions** regardless of
`version_policy`. Moving from v1.x to v2.x always requires explicit
consumer action.

| Profile | Default version policy |
|---|---|
| minimal | latest |
| dev | compatible |
| standard | compatible |
| prod | compatible |
| fsi | exact |
| sovereign | exact |

---

## 8. Resource Type Authority enforcement

DCM enforces the Resource Type Authority model:

- The PR submitter becomes the Resource Type Authority unless `owned_by` is
  declared otherwise
- The authority is the required approver for all future version PRs
- No new version of a spec activates without the authority's approval
- Authority transfer requires a formal transfer PR

The Registry Manager refuses to merge a version PR without the declared
authority's approval (or successor designated by formal transfer).

---

## 9. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `REG-001-DCM` | DCM enforces PR-based GitOps proposals with automated validation gates that all pass before review |
| `REG-002-DCM` | DCM enforces minimum review periods and mandatory shadow validation in `proposed` status before promotion to `active` |
| `REG-003-DCM` | DCM applies deprecation lifecycle policies REG-DP-001 through REG-DP-007; overridable except where locked by profile |
| `REG-004-DCM` | DCM enforces version constraints strictly; never automatically upgrades across major versions |
| `REG-005-DCM` | DCM applies the placement tie-breaking hierarchy: policy preference → provider priority → tenant affinity → cost analysis → least loaded → consistent hash |
| `REG-006-DCM` | DCM supports federated registry with signed bundle import for air-gapped/sovereign deployments |
| `REG-007-DCM` | DCM activates profile-appropriate registry policy groups by default; organizations may extend or replace |
| `REG-011-DCM` | DCM supports static, Cost Analysis, or hybrid provider cost metadata sources; placement uses freshest available |
