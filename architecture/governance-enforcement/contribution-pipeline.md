---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Contribution Pipeline
Established: 2026-05-26
Maps to: udlm/governance/federated-contribution-model.md
---

# Contribution Pipeline

> **Implements contracts defined in UDLM**:
> [udlm/governance/federated-contribution-model.md](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md).
> UDLM defines the four contributor types (Platform Admin, Consumer/Tenant,
> Service Provider, Peer DCM), the contribution artifact types, the
> universal contribution pipeline, and what each contributor type may
> contribute (the wire-level contract that defines who may write what). DCM
> operationalizes the contribution store structure, the review queue and
> approval workflow (GitOps PR mechanics), the pipeline orchestration,
> consumer/provider/federation contribution enforcement.

> **DCM-specific choice:** DCM uses GitOps PR workflow as its specific
> contribution transport. A peer DCM realization could use a different
> review channel (an internal review API, a custom UI, etc.) and still
> conform to the UDLM contributor + artifact contract.

---

## 1. Contribution store structure

All contributed artifacts are stored in the GitOps store with contributor
attribution. DCM uses this directory structure:

```
dcm-policy-store/
  system/                     # Platform admin authored; DCM built-in
    compliance/
    governance/
    orchestration/
  platform/                   # Platform admin authored; deployment-specific
    security/
    operations/
  tenant/
    <tenant-handle>/           # Consumer/Tenant authored
      gating/
      transformation/
      groups/
  provider/
    <provider-handle>/         # Provider authored
      layers/
      policies/
  federated/
    <peer-dcm-uuid>/           # Peer DCM contributed
      registry/
      policy-templates/

dcm-registry/
  core/                       # DCM project maintained
  community/                  # Community contributed (via community DCM)
    <contributor-handle>/
  organization/               # Organization contributed
    <provider-handle>/
```

### 1.1 Contributor attribution

Every artifact in the store includes a `contributed_by` block in artifact
metadata:

```yaml
artifact_metadata:
  uuid: <uuid>
  handle: "tenant/payments/gating/cost-ceiling"
  version: "1.0.0"
  status: active
  contributed_by:
    contributor_type: consumer       # platform_admin | consumer | service_provider | peer_dcm
    actor_uuid: <uuid>
    tenant_uuid: <uuid>              # for consumer contributions
    provider_uuid: <uuid>            # for provider contributions
    peer_dcm_uuid: <uuid>            # for federation contributions
    contribution_method: api         # api | flow_gui | git_pr | federation_push
    pr_url: "https://..."            # if submitted via PR
    reviewed_by: [<actor_uuid>]
    reviewed_at: <ISO 8601>
```

`contributed_by` is immutable (`FCM-001`); set at creation, never modified.

---

## 2. Review queue and approval workflow (GitOps PR mechanics)

### 2.1 The universal contribution pipeline

```
Contributor authors an artifact
  │ via one of three contribution surfaces:
  ├── Flow GUI Canvas / Policy Authoring Interface
  ├── Direct API: POST /api/v1/contribute/{artifact_type}
  └── Git PR directly to target repository
  ▼ Artifact submitted → status: developing (local only)
  ▼ Contributor submits for review → status: proposed
  │   For policies: shadow mode activates automatically
  │   For other artifacts: staged in proposed state
  ▼ Governance Matrix evaluates the contribution:
  │   Is this contributor permitted to contribute this artifact type?
  │   Is the artifact in the correct domain for this contributor?
  │   Does the artifact pass structural validation?
  │   DENY → rejected with reason; no further processing
  ▼ Review flow (per profile + artifact type):
  │   auto:       artifact activates immediately
  │   reviewed:   one platform admin or designated reviewer approves
  │   verified:   two independent reviewers approve
  │   authorized: N members of declared authority group record decisions
  ▼ On approval → status: active
  │   For policies: shadow mode results reviewed; full enforcement begins
  │   For registry entries: available in registry
  │   For catalog items: visible in service catalog (per RBAC)
  ▼ Lifecycle managed by contributor (deprecate, retire)
      Subject to platform admin override at any time
```

### 2.2 GitOps PR mechanics

For Git-PR contributions:

1. Contributor opens PR against the relevant repository (policy store,
   registry, layers)
2. PR template enforces required metadata: contributor type, target domain,
   review type, justification
3. CI runs automated validation (schema, structural, dependency resolution,
   breaking change detector)
4. DCM's GitOps Adapter watches for PRs; on PR open, posts a Governance
   Matrix evaluation result as a status check
5. If matrix DENY: PR blocked; comment explains why
6. If matrix ALLOW (or ALLOW_WITH_CONDITIONS): review continues via the
   normal Git platform workflow (reviewer assignment, comments, approval)
7. On approval and CI green: PR merges; artifact transitions to `proposed`
8. Shadow validation period runs (per `shadow_review_period`)
9. After shadow period, artifact transitions to `active`

### 2.3 Direct API contribution

For API contributions (`POST /api/v1/contribute/{artifact_type}`):

1. Request body includes the artifact YAML/JSON + contribution metadata
2. DCM Contribution Service runs structural validation
3. Governance Matrix evaluates; DENY returns 403 with rule_uuid
4. On ALLOW: artifact written to the contribution store with status
   `proposed`; shadow mode activates if policy
5. If `review_type: auto` per active profile: artifact transitions to
   `active` immediately
6. Otherwise: review pipeline kicks off (notification to required reviewers,
   PR URL returned for tracking)

Response includes:
- `contribution_uuid`
- `status`
- `review_required`
- `review_type`
- `reviewer_group`
- `pr_url` (if PR-based review applies)
- `shadow_results_url` (for policies)

---

## 3. Pipeline orchestration

The Contribution Service orchestrates the pipeline:

| Stage | DCM service |
|---|---|
| Submission | API Gateway → Contribution Service |
| Validation | Contribution Service (structural) + Policy Manager (Governance Matrix) |
| Storage | GitOps Adapter (PR creation) OR Policy Store DB write |
| Notification | Notification Router (notifies reviewers per active profile) |
| Review tracking | Approval Manager (tracks decisions, quorum, deadline) |
| Shadow mode | Policy Manager (evaluates new policy in shadow against live traffic) |
| Activation | Policy Manager (transitions status, recompiles rule set, emits `policy.activated`) |

Every stage emits an event to `pipeline_events`; downstream services
subscribe via `LISTEN/NOTIFY`.

---

## 4. Consumer contribution enforcement

DCM enforces consumer contribution scope at submission time. A consumer
submitting a policy with `domain: tenant` must belong to that Tenant; the
Governance Matrix evaluator checks this and rejects domain scope violations.

```yaml
# DCM ships this rule pre-activated
governance_matrix_rule:
  handle: "system/matrix/consumer-policy-scope"
  enforcement: hard
  match:
    subject.type: consumer
    data.artifact_type: policy
    data.domain: [system, platform]    # consumer attempting non-tenant domain
  decision: DENY
  reason: "Consumers may only contribute tenant-domain policies"
```

### 4.1 Consumer contribution API

```
POST /api/v1/contribute/policy
Authorization: Bearer <token>
X-DCM-Tenant: <tenant-uuid>
{
  "policy_type": "validation",
  "handle": "tenant/payments/gating/cost-ceiling",
  "domain": "tenant",
  "enforcement_class": "operational",
  "output_class": "advisory",
  "match": {...},
  "output": {...},
  "shadow_mode": true,
  "commit_message": "Add monthly cost ceiling compliance Validation Policy for Payments Tenant"
}

Response 202:
{
  "contribution_uuid": "<uuid>",
  "policy_handle": "tenant/payments/gating/cost-ceiling",
  "status": "proposed",
  "shadow_mode": true,
  "review_required": true,
  "review_type": "reviewed",
  "reviewer_group": "platform-admins",
  "pr_url": "https://git.corp.example.com/dcm-policies/pulls/145",
  "shadow_results_url": "/flow/api/v1/shadow/<policy_uuid>"
}
```

---

## 5. Provider contribution integration

Providers contribute Resource Type Specs, Provider Catalog Items, Service
Layers, and provider-specific policies. DCM enforces:

- Only the resource types declared at registration (`subject.declared_resource_types`)
- Catalog Items only for resource types the provider offers
- Service Layers only for resource types the provider offers
- Provider-domain policies only

```yaml
# DCM ships this rule pre-activated
governance_matrix_rule:
  handle: "system/matrix/provider-spec-scope"
  enforcement: hard
  match:
    subject.type: service_provider
    data.artifact_type: resource_type_spec
    data.resource_type_fqn:
      not_in: subject.declared_resource_types
  decision: DENY
  reason: "Providers may only contribute Resource Type Specs for resource types they offer"
```

### 5.1 Provider contribution API

```
POST /api/v1/provider/contribute/resource-type-spec
Authorization: mTLS + provider credential

{
  "resource_type_fqn": "Storage.DistributedVolume",
  "tier": "organization",
  "version": "1.0.0",
  "schema": {...},
  "portability_class": "provider_specific",
  "commit_message": "Publish DistributedVolume resource type v1.0.0"
}
```

The submission is authenticated per
[`../credentials-and-auth/provider-callback.md`](../credentials-and-auth/provider-callback.md).

---

## 6. Federation contribution synchronization

Federation peers contribute artifacts subject to their federation trust
posture:

| Peer trust posture | Review requirement | Artifact types permitted |
|---|---|---|
| `verified` | reviewed (standard+); auto (dev) | Registry entries, policy templates, service layers |
| `vouched` | reviewed always | Registry entries, service layers only |
| `provisional` | `authorized` tier approval | Registry entries only (no policies) |

### 6.1 Federation contribution flow

```
Peer DCM publishes a contribution bundle:
  Content: resource type specs, policy templates, or layers
  Transport: federation tunnel (mTLS, signed, scoped credential)
  Metadata: contributing_dcm_uuid, trust_posture, artifact_list

Receiving DCM evaluates:
  1. Governance Matrix: is this peer permitted to contribute this artifact type?
  2. Signature verification: bundle signed by peer's private key?
  3. Structural validation: artifacts conform to DCM schemas?
  4. Domain scope check: artifacts within peer's permitted domain?

On validation pass:
  Artifacts enter proposed status in receiving DCM's policy/registry store
  Review flow per receiving DCM's profile + peer trust posture

On approval:
  Artifacts become active in receiving DCM
  Source attribution: contributed_by.dcm_uuid, contributed_by.trust_posture
```

### 6.2 Hub-spoke policy distribution

In Hub-Spoke federation, Regional DCMs may subscribe to the Hub's policy
distribution feed:

```yaml
hub_policy_distribution:
  hub_dcm_uuid: <uuid>
  distribution_type: push          # Hub pushes on policy change
  auto_approve_from_hub:           # profile-governed
    minimal: true
    dev: true
    standard: true
    prod: false                    # reviewed required even from verified Hub
    fsi: false                     # verified required
    sovereign: false               # authorized approval required
  policy_handles_subscribed:
    - "system/compliance/hipaa/*"
    - "system/governance/drift-remediation"
```

**Regional DCM always reviews before activating.** Hub cannot force-activate
policies on Regional DCMs.

---

## 7. Artifact lifecycle across contributors

### 7.1 Ownership and transfer

Every artifact is owned by its contributor at creation. Transfer:

- Consumer-authored policies transfer to a new Tenant admin when original
  actor departs
- Provider-contributed catalog items remain owned by the provider registration
- Federation-contributed artifacts are owned by the contributing peer DCM

Ownership transfer requires receiving owner's explicit acceptance.

### 7.2 Platform admin override

Platform admins can override any contributor's artifact lifecycle at any
time:

- Suspend an active consumer-authored policy causing harm
- Retire a provider-contributed resource type spec no longer safe
- Reject a proposed federation contribution without public reason (security
  discretion)

Override actions are always audited with overriding admin's actor UUID and
reason (`FCM-005`).

### 7.3 Deprecation and sunset

Contributors deprecate their own artifacts:

1. Notification to all consumers of the artifact
2. Sunset period declared (minimum P30D standard; P90D for prod/fsi/sovereign)
3. During sunset: new use warned; existing resources unaffected
4. After sunset: new use blocked
5. Platform admin confirms final retirement

### 7.4 Orphaned artifacts

When a contributor's access is revoked:

- Active artifacts remain active — orphaned artifacts do not auto-deactivate
- Platform admin notified: "Artifact X has no active owner"
- Platform admin assigns new owner or explicitly retires
- Auto-retire-on-orphan is configurable per profile (`FCM-006`; enabled in
  `sovereign`)

---

## 8. Profile-governed contribution defaults

```yaml
contribution_policy:
  minimal:
    consumer_policy_auto_approve: true
    provider_spec_auto_approve: true
    federation_contribution_auto_approve: true
    shadow_mode_default: true                   # security: shadow always on

  dev:
    consumer_policy_auto_approve: true
    provider_spec_auto_approve: true
    federation_contribution_auto_approve: false
    shadow_mode_default: true

  standard:
    consumer_policy_auto_approve: false
    provider_spec_auto_approve: false
    federation_contribution_auto_approve: false
    shadow_mode_default: true
    shadow_review_period: P7D

  prod:
    consumer_policy_auto_approve: false
    consumer_governance_matrix_requires: verified
    provider_spec_requires: reviewed
    federation_contribution_requires: reviewed
    shadow_mode_default: true
    shadow_review_period: P14D

  fsi:
    consumer_policy_requires: verified
    consumer_governance_matrix_requires: verified
    provider_spec_requires: verified
    federation_contribution_requires: verified
    shadow_mode_default: true
    shadow_review_period: P30D
    min_shadow_divergence_review: true

  sovereign:
    consumer_policy_requires: authorized
    provider_spec_requires: authorized
    federation_contribution_requires: authorized
    shadow_mode_default: true
    shadow_review_period: P30D
    min_shadow_divergence_review: true
    auto_retire_orphaned_artifacts: true
```

---

## 9. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `FCM-001-DCM` | DCM records `contributed_by` in artifact_metadata at creation; immutable |
| `FCM-002-DCM` | DCM enforces contributor permissions via Governance Matrix at submission; domain scope violations are hard DENY |
| `FCM-003-DCM` | DCM routes all contributions through the GitOps PR model unless profile grants auto-approval |
| `FCM-004-DCM` | DCM enters new policies in proposed (shadow) status by default; shadow results available before shadow_review_period expires |
| `FCM-005-DCM` | DCM permits platform admin override of any contributor's artifact lifecycle; override is audited |
| `FCM-006-DCM` | DCM does not auto-deactivate orphaned artifacts; platform admin assigns new owner or retires; sovereign profile auto-retires |
| `FCM-007-DCM` | DCM scopes federation contributions by peer trust posture: verified → reviewed (standard+); vouched → reviewed always; provisional → authorized |
| `FCM-008-DCM` | DCM enforces absolute contributor-tier scope limits; consumer-authored tenant-domain policies cannot affect system/platform domain regardless of declared match conditions |
