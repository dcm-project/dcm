# DCM Admin API Specification

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** API Narrative Specification


> **📋 Draft**
>
> This specification has been promoted from Work in Progress to Draft status. Complete Admin API covering all platform admin operations with request/response examples. It is ready for implementation feedback but has not yet been formally reviewed for final release.
>
> This specification defines the DCM Admin API — the platform administration interface. Published to share design direction and invite feedback. Do not build production integrations against this specification until it reaches draft status.

**Version:** 0.1.0-draft
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Specification
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [Consumer API Specification](consumer-api-spec.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md) | [Control Plane Components](../../architecture/control-plane/components.md) | [Accreditation and Authorization Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md)

---

## Abstract

The Admin API is the platform administration interface for DCM. It is served through the same Ingress API as the Consumer API and Provider API but is restricted to actors with `platform_admin` or `tenant_admin` roles. It covers operations that consumers cannot perform — Tenant lifecycle management, provider registration review, accreditation approval, quota administration, discovery management, orphan resolution, recovery decision escalation, and bootstrap operations.

---


> **AEP Alignment:** This specification follows [AEP](https://aep.dev) conventions.
> Custom methods use colon syntax (`POST /admin/providers/{uuid}:approve`).
> Async operations return an `Operation` resource (AEP-136 LRO).
> List pagination uses `page_size` and `page_token` parameters.
> See the normative OpenAPI specification: `schemas/openapi/dcm-admin-api.yaml`

## 1. Authentication and Authorization

All Admin API endpoints require Bearer token authentication (same as Consumer API). Role requirements are declared per endpoint:

| Role | Scope |
|------|-------|
| `platform_admin` | All Admin API operations across all Tenants |
| `tenant_admin` | Tenant-scoped Admin API operations for their own Tenant only |

> **Governed RBAC (ADR-RBAC-001).** These role names are governed **access-role** TaxonomyTerms — the full set (`platform_admin`, `tenant_admin`, `sre`, `auditor`, `security`, `policy_owner`, `finops`, `provider_owner`, `consumer`, `system`) lives in `udlm/registry/instances/access-role-taxonomy.yaml`, not ad-hoc strings. Each endpoint's `Role:` gate resolves to a **dcm-function** permission (e.g. `provider.capability.admit`, `provider.register.approve`), and the role→function grant is the `FunctionCapabilityMatrix` (`udlm/registry/function-capability-matrix.schema.json`). Authorization is **default-deny**, enforced by the one Governance Matrix: an actor holds a function only via a `role_assignment` binding it — an `Identity.Person`/`ServiceAccount` actor, or an `access_grouping` DCMGroup, → role.

Base URL: `/api/v1/admin/`

> **Versioning:** See [API Versioning Strategy](../../architecture/control-plane/api-versioning.md). Breaking changes increment the major version. The Admin API follows the same deprecation lifecycle as the Consumer API, with profile-governed support windows.

Step-up MFA is required for destructive operations (Tenant decommission, accreditation revocation, bootstrap credential rotation) regardless of session MFA status.

---

### 1.1 Rate Limiting

Admin API endpoints have separate rate limits from the Consumer API, applied per authenticated admin actor:

| Profile | Requests/minute | Burst |
|---------|----------------|-------|
| All profiles | 120 | 40 |

Rate-limited responses include `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining` headers.

### 1.2 Request and Correlation IDs

All responses include `X-DCM-Request-ID` and `X-DCM-Correlation-ID` headers (same model as Consumer API).

### 1.3 Response Envelopes

List responses use `{"items": [...], "total": N, "next_cursor": "..."}`. Single resources returned directly. Errors use `{"error": "...", "message": "...", "request_id": "..."}`.

---

## 2. Tenant Management

### 2.1 List Tenants

```
GET /api/v1/admin/tenants
Role: platform_admin

Query params: status=<active|suspended|decommissioned>, page, page_size

Response 200:
{
  "tenants": [
    {
      "tenant_uuid": "<uuid>",
      "handle": "payments-team",
      "display_name": "Payments Platform",
      "status": "active",
      "deployment_posture": "prod",
      "compliance_domains": ["hipaa"],
      "recovery_profile": "notify-and-wait",
      "entity_count": 142,
      "created_at": "<ISO 8601>"
    }
  ],
  "total": 12
}
```

### 2.2 Create Tenant

```
POST /api/v1/admin/tenants
Role: platform_admin

{
  "handle": "new-team",
  "display_name": "New Team",
  "deployment_posture": "standard",
  "compliance_domains": [],
  "recovery_profile_override": null,
  "initial_admin_actor_uuid": "<uuid>"
}

Response 201 Created:
{
  "tenant_uuid": "<uuid>",
  "status": "active"
}
```

### 2.3 Suspend / Reinstate Tenant

```
POST /api/v1/admin/tenants/{tenant_uuid}:suspend
POST /api/v1/admin/tenants/{tenant_uuid}:reinstate
Role: platform_admin

{
  "reason": "<human-readable reason>",
  "notify_tenant_admin": true
}
```

### 2.4 Decommission Tenant

```
DELETE /api/v1/admin/tenants/{tenant_uuid}
Role: platform_admin
Requires: step-up MFA

{
  "reason": "<required>",
  "force": false,          # true: decommission even if active entities remain
  "notify_tenant_admin": true
}

Response 409 Conflict (if active entities and force=false):
{
  "error": "tenant_has_active_entities",
  "active_entity_count": 47,
  "resolution": "Decommission all entities first, or use force=true"
}
```

---

## 3. Provider Management

### 3.1 List Registered Providers

```
GET /api/v1/admin/providers
Role: platform_admin

Query params: type=<service|policy|storage|notification|information>, status=<active|suspended>

Response 200:
{
  "providers": [
    {
      "provider_uuid": "<uuid>",
      "handle": "eu-west-prod-1",
      "provider_type": "service",
      "status": "active",
      "health": "healthy",
      "accreditation_count": 2,
      "max_data_classification": "phi"
    }
  ]
}
```

### 3.2 Review Provider Registration

New provider registrations in `proposed` status require platform admin review:

```
GET /api/v1/admin/providers/pending
Role: platform_admin

POST /api/v1/admin/providers/{provider_uuid}:approve
POST /api/v1/admin/providers/{provider_uuid}:reject
{
  "reason": "<required for reject>"
}
```

### 3.3 Suspend Provider

```
POST /api/v1/admin/providers/{provider_uuid}:suspend
Role: platform_admin

{
  "reason": "<human-readable reason>",
  "affect_existing_entities": "notify_only | block_new_requests | migrate"
}
```

---

## 4. Accreditation Management

### 4.1 List Accreditations

```
GET /api/v1/admin/accreditations
Role: platform_admin

Query params: subject_type, framework, status=<active|proposed|expiring|expired>

Response 200:
{
  "accreditations": [
    {
      "accreditation_uuid": "<uuid>",
      "subject_uuid": "<uuid>",
      "subject_type": "service_provider",
      "framework": "hipaa",
      "accreditation_type": "baa",
      "status": "active",
      "expires_at": "<ISO 8601>",
      "days_until_expiry": 89
    }
  ]
}
```

### 4.2 Approve Accreditation

```
POST /api/v1/admin/accreditations/{accreditation_uuid}:approve
Role: platform_admin
Requires: step-up MFA

{
  "review_notes": "<required — document basis for approval>",
  "certificate_verified": true
}
```

### 4.3 Revoke Accreditation

```
DELETE /api/v1/admin/accreditations/{accreditation_uuid}
Role: platform_admin
Requires: step-up MFA

{
  "revocation_reason": "<required>",
  "affected_entity_action": "notify_only | block_new_requests | migrate_entities"
}
```

---

## 5. Discovery Management

### 5.1 Trigger Discovery

```
POST /api/v1/admin/discovery:trigger
Role: platform_admin | tenant_admin

{
  "scope": "entity | resource_type | provider | tenant",
  "entity_uuid": "<uuid>",
  "resource_type": "Compute.VirtualMachine",
  "provider_uuid": "<uuid>",
  "tenant_uuid": "<uuid>",
  "reason": "incident investigation",
  "priority": "high | standard | background"
}

Response 202 Accepted:
{
  "discovery_job_uuid": "<uuid>",
  "status": "queued",
  "priority": "high",
  "estimated_start": "<ISO 8601>"
}
```

### 5.2 Discovery Job Status

```
GET /api/v1/admin/discovery/jobs/{discovery_job_uuid}

Response 200:
{
  "discovery_job_uuid": "<uuid>",
  "status": "running | completed | failed",
  "entities_discovered": 47,
  "new_entities_found": 2,
  "started_at": "<ISO 8601>",
  "completed_at": "<ISO 8601|null>",
  "orphan_candidates_found": 1
}
```

---

## 6. Orphan Management

### 6.1 List Orphan Candidates

```
GET /api/v1/admin/orphans
Role: platform_admin

Query params: provider_uuid, status=<under_review|confirmed|resolved>

Response 200:
{
  "orphan_candidates": [
    {
      "orphan_candidate_uuid": "<uuid>",
      "provider_uuid": "<uuid>",
      "provider_entity_id": "vm-0a1b2c3d",
      "suspected_request_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "discovered_at": "<ISO 8601>",
      "status": "under_review"
    }
  ]
}
```

### 6.2 Resolve Orphan Candidate

```
POST /api/v1/admin/orphans/{orphan_candidate_uuid}/resolve
Role: platform_admin

{
  "resolution": "manual_decommission | adopt_into_dcm | mark_false_positive",
  "reason": "<required>",
  "target_tenant_uuid": "<uuid>"    # required if resolution=adopt_into_dcm
}
```

---

## 7. Recovery Decision Management

Platform admins can resolve pending recovery decisions for any entity:

```
GET /api/v1/admin/recovery-decisions/pending
Role: platform_admin

Response 200:
{
  "pending_decisions": [
    {
      "recovery_decision_uuid": "<uuid>",
      "entity_uuid": "<uuid>",
      "trigger": "DISPATCH_TIMEOUT",
      "entity_state": "TIMEOUT_PENDING",
      "deadline": "<ISO 8601>",
      "tenant_uuid": "<uuid>"
    }
  ]
}

POST /api/v1/admin/recovery-decisions/{recovery_decision_uuid}
Role: platform_admin

{
  "action": "DRIFT_RECONCILE | DISCARD_AND_REQUEUE | DISCARD_NO_REQUEUE",
  "reason": "<required>"
}
```

---

## 8. Quota Management

### 8.1 View Tenant Quotas

```
GET /api/v1/admin/tenants/{tenant_uuid}/quotas
Role: platform_admin | tenant_admin

Response 200:
{
  "quotas": [
    {
      "resource_type": "Compute.VirtualMachine",
      "limit": 100,
      "current_usage": 47,
      "policy_uuid": "<uuid>"
    }
  ]
}
```

### 8.2 Update Quota

```
PUT /api/v1/admin/tenants/{tenant_uuid}/quotas/{resource_type}
Role: platform_admin

{
  "new_limit": 150,
  "reason": "Q2 capacity increase approved by FinOps"
}
```

---

## 9. Search Index Management

```
POST /api/v1/admin/search-index:rebuild
Role: platform_admin

{
  "scope": "full | tenant | resource_type",
  "tenant_uuid": "<uuid>",
  "reason": "Recovery after index corruption"
}

Response 202 Accepted:
{
  "rebuild_job_uuid": "<uuid>",
  "estimated_duration": "PT2H",
  "degraded_during_rebuild": true
}

GET /api/v1/admin/search-index/status

Response 200:
{
  "status": "healthy | degraded | rebuilding | unavailable",
  "staleness_seconds": 42,
  "last_full_rebuild": "<ISO 8601>",
  "entity_count": 8421
}
```

---

## 10. Bootstrap Operations

### 10.1 Rotate Bootstrap Admin Credential

```
POST /api/v1/admin/bootstrap:rotate-credential
Role: platform_admin
Requires: step-up MFA (hardware_token_mfa for fsi/sovereign)

{
  "new_credential_ref": "<credential provider reference>",
  "reason": "Initial bootstrap credential rotation"
}
```

### 10.2 Deployment Health

```
GET /api/v1/admin/health

Response 200:
{
  "overall": "healthy | degraded | critical",
  "components": [
    { "component": "request_orchestrator", "status": "healthy" },
    { "component": "policy_engine", "status": "healthy" },
    { "component": "placement_engine", "status": "healthy" },
    { "component": "lifecycle_constraint_enforcer", "status": "healthy" },
    { "component": "discovery_scheduler", "status": "healthy" },
    { "component": "notification_router", "status": "healthy" },
    { "component": "cost_analysis", "status": "healthy" },
    { "component": "search_index", "status": "degraded", "staleness_seconds": 180 },
    { "component": "intent_store", "status": "healthy" },
    { "component": "requested_store", "status": "healthy" },
    { "component": "realized_store", "status": "healthy" }
  ],
  "active_profile": {
    "deployment_posture": "prod",
    "compliance_domains": ["hipaa"],
    "recovery_posture": "notify-and-wait",
    "zero_trust_posture": "full"
  }
}
```

---

## 13. DCM Self-Health Endpoints

DCM exposes three health endpoints, each with a distinct purpose:

```http
# Liveness — is the process alive? (Kubernetes liveness probe)
GET /livez
# No auth required. Max response time: PT5S.
# Returns 200 OK with {"status":"ok"} if alive.
# Returns 503 if process is deadlocked or unresponsive.

# Readiness — is DCM ready to serve traffic? (Kubernetes readiness probe)
GET /readyz
# No auth required. Max response time: PT10S.
# Returns 200 OK with {"status":"ready"} if all required stores are reachable.
# Returns 503 with {"status":"not_ready","reasons":["store_unreachable"]} otherwise.

# Operational health — rich health for operators and monitoring systems
GET /api/v1/admin/health
Authorization: Bearer <admin-token>

Response 200:
{
  "dcm_version": "<semver>",
  "profile": "prod",
  "status": "healthy",           // healthy | degraded | critical
  "components": {
    "request_orchestrator": { "status": "healthy" },
    "policy_engine":        { "status": "healthy" },
    "placement_engine":     { "status": "healthy" },
    "service_provider":  { "status": "degraded", "reason": "rotation_pending" }
  },
  "stores": {
    "intent_store":    { "status": "healthy", "latency_p99_ms": 12 },
    "requested_store": { "status": "healthy", "latency_p99_ms": 8 },
    "realized_store":  { "status": "healthy", "latency_p99_ms": 9 }
  },
  "providers": {
    "total": 4,
    "healthy": 3,
    "degraded": 1,
    "unhealthy": 0
  }
}

# Prometheus metrics
GET /metrics
# Unauthenticated (secured by network policy in production).
# Returns Prometheus text format metrics.
```

> **Full model:** See [DCM Self-Health](../../architecture/control-plane/self-health.md) — HLT-001–HLT-006.


## 12. Session Management (Admin)

Platform admins can force-revoke sessions for any actor — used on actor compromise, policy violation, or deprovisioning.

```http
# Force-revoke all sessions for an actor
POST /api/v1/admin/actors/{actor_uuid}:revoke-sessions
Authorization: Bearer <admin-token>

{
  "reason": "security_event",        // REQUIRED
  "notify_actor": true               // send notification event
}

Response 202 Accepted:
{
  "sessions_revoked": 3,
  "actor_uuid": "<uuid>",
  "revocation_propagated_at": "<ISO 8601>"
}
```

```http
# List active sessions for any actor (admin view)
GET /api/v1/admin/actors/{actor_uuid}/sessions
Authorization: Bearer <admin-token>

Response 200:
{
  "items": [
    {
      "session_uuid": "<uuid>",
      "created_at": "<ISO 8601>",
      "expires_at": "<ISO 8601>",
      "auth_method": "ldap",
      "mfa_verified": true,
      "status": "active"
    }
  ],
  "total": 1
}
```

**Error codes specific to session management:**

| Error Code | HTTP | When |
|-----------|------|------|
| `actor_not_found` | 404 | Actor UUID not found |
| `no_active_sessions` | 404 | Actor has no active sessions |

> **Full model:** See [Session Token Revocation](../../architecture/control-plane/session-revocation.md) — AUTH-016–AUTH-022.


## 11. Error Model

All Admin API errors use the same envelope as the Consumer API:

```json
{
  "error": "<error_code>",    // machine-readable snake_case code
  "message": "<string>",      // human-readable description
  "request_id": "<uuid>",     // matches X-DCM-Request-ID header
  "details": {}               // optional: field-level details
}
```

**Admin-specific error codes:**

| Error Code | HTTP Status | When |
|-----------|-------------|------|
| `insufficient_admin_role` | 403 | Actor lacks required admin role |
| `tenant_not_found` | 404 | Tenant UUID not found |
| `provider_not_found` | 404 | Provider UUID not found |
| `approval_already_voted` | 409 | Actor has already voted on this approval |
| `approval_window_expired` | 410 | Approval window has passed |
| `degradation_already_accepted` | 409 | Degradation item already accepted |
| `tier_registry_blocked` | 409 | Registry change has unresolved blocking items |
| `quota_below_current_usage` | 422 | New quota would be below current consumption |

All error responses include `X-DCM-Request-ID` and `X-DCM-Correlation-ID` headers.


## Scoring Model Administration

> Approval routing thresholds use named-tier dynamic format. See [Authority Tier Model](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) for the complete specification.

### Get Scoring Thresholds for Profile

```
GET /api/v1/admin/profiles/{profile_name}/scoring

Response 200:
{
  "profile": "standard",
  "scoring_thresholds": {
    "auto_approve_below": 25,
    "approval_routing": [
      { "tier": "reviewed", "max_score": 59 },
      { "tier": "verified", "max_score": 79 },
      { "tier": "authorized", "max_score": 100 }
    ]
  },
  "signal_weights": {
    "operational_gating": 0.45,
    "completeness": 0.15,
    "actor_risk_history": 0.20,
    "quota_pressure": 0.10,
    "provider_risk": 0.10
  },
  "policy_enforcement_overrides": []
}
```

### Update Scoring Thresholds

```
PATCH /api/v1/admin/profiles/{profile_name}/scoring
{
  "scoring_thresholds": {
    "auto_approve_below": 20,
    "approval_routing": [
      { "tier": "reviewed", "max_score": 59 },
      { "tier": "verified", "max_score": 79 },
      { "tier": "authorized", "max_score": 100 }
    ]
  }
}

Response 200: { "profile": "standard", "updated_at": "<ISO 8601>", "effective_immediately": true }
Response 422: { "error": "threshold_invalid", "reason": "auto_approve_below exceeds maximum of 50 (SMX-008)" }
```

### Add Policy Enforcement Override

```
POST /api/v1/admin/profiles/{profile_name}/scoring/overrides
{
  "policy_handle": "platform/gating/cpu-size-limit",
  "override_enforcement_class": "compliance",
  "rationale": "Prod profile: CPU limit is a hard constraint",
  "applies_to_resource_types": ["Compute.VirtualMachine"]
}

Response 201 Created:
{ "override_uuid": "<uuid>", "policy_handle": "...", "effective_immediately": true }
```

### Actor Risk History

```
GET /api/v1/admin/actors/{actor_uuid}/risk-history

Response 200:
{
  "actor_uuid": "<uuid>",
  "current_score": 30,
  "events": [
    {
      "event_type": "validation_failure",
      "occurred_at": "<ISO 8601>",
      "request_uuid": "<uuid>",
      "base_contribution": 5,
      "decayed_contribution": 3.2,
      "days_ago": 4
    }
  ],
  "decay_lambda": 0.1,
  "score_half_life_days": 7
}

POST /api/v1/admin/actors/{actor_uuid}/risk-history:reset
{
  "reason": "Actor confirmed as trusted automation account",
  "audit_note": "Reviewed and approved by platform admin"
}
```

### Score Audit Trail

```
GET /api/v1/admin/scoring/audit

Query parameters:
  from=<ISO 8601>
  to=<ISO 8601>
  routing_decision=<auto_approved|pending_review|pending_verified|pending_authorized>
  risk_score_above=<int>
  actor_uuid=<uuid>
  resource_type=<fqn>

Response 200:
{
  "score_records": [
    {
      "score_record_uuid": "<uuid>",
      "request_uuid": "<uuid>",
      "risk_score": 47,
      "routing_decision": "reviewed",
      "signal_breakdown": { ... },
      "evaluated_at": "<ISO 8601>"
    }
  ]
}
```


---

## Approval Management

DCM provides approval gates for requests, policy contributions, provider registrations, and federation contributions. The Admin API is the integration point for recording decisions — it is designed to be called by both human reviewers in the DCM UI and by external systems (ServiceNow, Jira, Slack bots, workflow automation).

### List Pending Approvals

```
GET /api/v1/admin/approvals/pending

Query parameters:
  approval_type=<request | policy_contribution | provider_registration | federation_contribution>
  tier=<reviewed | verified | authorized>
  reviewer_uuid=<uuid>       # approvals where this actor is an eligible reviewer

Response 200:
{
  "pending_approvals": [
    {
      "approval_uuid": "<uuid>",
      "approval_type": "policy_contribution",
      "tier": "authorized",
      "subject_uuid": "<policy_uuid>",
      "subject_handle": "tenant/payments/gating/cost-ceiling",
      "required_dcmgroup_uuid": "<uuid>",     # for authorized tier
      "quorum_required": 3,
      "votes_recorded": 1,
      "submitted_at": "<ISO 8601>",
      "window_expires_at": "<ISO 8601>",
      "submitted_by": { "uuid": "<uuid>", "display_name": "Bob Smith" }
    }
  ]
}
```

### Record an Approval Decision

```
POST /api/v1/admin/approvals/{approval_uuid}:vote

{
  "decision": "approve | reject",
  "reason": "<required for reject; optional for approve>",
  "recorded_via": "dcm_admin_ui | servicenow | jira | slack_bot | api_direct | other",
  "external_reference": "<ticket or case ID in external system — optional, for audit>"
}

Response 200:
{
  "approval_uuid": "<uuid>",
  "voter_uuid": "<uuid>",
  "decision": "approve",
  "votes_recorded": 2,
  "quorum_required": 3,
  "quorum_reached": false,
  "pipeline_status": "pending_authorized"
}

# When quorum is reached or reviewed/verified satisfied:
{
  "approval_uuid": "<uuid>",
  "voter_uuid": "<uuid>",
  "decision": "approve",
  "votes_recorded": 3,
  "quorum_required": 3,
  "quorum_reached": true,
  "pipeline_status": "activating"
}

Response 403: actor is not a member of the required authority group (authorized tier) or not in reviewer role
Response 409: actor has already voted on this approval (verified and authorized tiers enforce distinct voters)
Response 410: approval window has expired
```

### Get Approval Detail

```
GET /api/v1/admin/approvals/{approval_uuid}

Response 200:
{
  "approval_uuid": "<uuid>",
  "approval_type": "authorized",
  "subject_uuid": "<uuid>",
  "tier": "authorized",
  "required_dcmgroup_uuid": "<uuid>",
  "quorum_required": 3,
  "window_expires_at": "<ISO 8601>",
  "votes": [
    {
      "voter_uuid": "<uuid>",
      "voter_display_name": "Alice Chen",
      "decision": "approve",
      "recorded_at": "<ISO 8601>",
      "recorded_via": "servicenow",
      "external_reference": "CHG0012345"
    }
  ],
  "status": "pending_authorized",
  "quorum_reached": false
}
```


---

## Authority Tier Registry Management

> **Implementation note:** The tier registry change impact detection pipeline is specified in [Authority Tier Model](https://github.com/croadfeldt/udlm/blob/main/governance/authority-tier-model.md) Section 7. The endpoints below are the Admin API surface for proposing, reviewing, and activating tier registry changes. The detection mechanism (tier impact diff computation, affected item query, degradation gate) is an implementation responsibility.

### Propose a Tier Registry Change

```
POST /api/v1/admin/tier-registry/changes

{
  "proposed_tiers": [
    { "name": "auto",                 "insert_after": null,       "decision_gravity": "none" },
    { "name": "reviewed",             "insert_after": "auto",     "decision_gravity": "routine" },
    { "name": "verified",             "insert_after": "reviewed", "decision_gravity": "elevated" },
    { "name": "compliance_reviewed",  "insert_after": "verified", "decision_gravity": "elevated" },
    { "name": "authorized",           "insert_after": "compliance_reviewed", "decision_gravity": "critical" }
  ],
  "reason": "Adding compliance_reviewed tier for PCI-DSS regulated actions"
}

Response 202 Accepted:
{
  "registry_change_uuid": "<uuid>",
  "status": "impact_assessment_pending",
  "estimated_ready_at": "<ISO 8601>"
}
```

### Get Tier Registry Impact Report

```
GET /api/v1/admin/tier-registry/changes/{change_uuid}/impact

Response 200:
{
  "registry_change_uuid": "<uuid>",
  "status": "impact_assessed | pending_degradation_review | ready_to_activate | blocked",
  "summary": {
    "degradations": 0,
    "upgrades": 3,
    "new_tiers": 1,
    "broken_references": 0,
    "profile_gaps": 2
  },
  "degradations": [],
  "upgrades": [ ... ],
  "profile_gaps": [
    {
      "profile": "standard",
      "missing_tiers": ["compliance_reviewed"],
      "gap_effect": "Requests scoring in the compliance_reviewed range will route to verified tier until threshold list is updated"
    }
  ],
  "blocking_items": []
}
```

### Accept a Security Degradation

```
POST /api/v1/admin/tier-registry/changes/{change_uuid}:accept-degradation

{
  "affected_item_uuid": "<uuid>",
  "affected_item_type": "provider_registration_requirement",
  "acceptance_reason": "<required — what compensating controls justify this degradation>",
  "accepted_by": "<actor_uuid>"
}

Response 200:
{
  "acceptance_uuid": "<uuid>",
  "degradation_accepted": true,
  "remaining_degradations": 0,
  "change_status": "ready_to_activate"
}

Response 403: actor does not hold verified or authorized tier reviewer role
Response 409: degradation already accepted
```

### Activate a Tier Registry Change

```
POST /api/v1/admin/tier-registry/changes/{change_uuid}:activate

Response 200:
{
  "registry_change_uuid": "<uuid>",
  "activated_at": "<ISO 8601>",
  "new_registry_version": "1.1.0",
  "impact_report_uuid": "<uuid>"
}

Response 409: change has unresolved blocking items (broken_references or unaccepted degradations)
```

### List Historical Registry Changes

```
GET /api/v1/admin/tier-registry/changes?status=activated&page_size=20

Response 200:
{
  "changes": [
    {
      "registry_change_uuid": "<uuid>",
      "status": "activated",
      "activated_at": "<ISO 8601>",
      "proposed_by": { "uuid": "<uuid>", "display_name": "Alice Chen" },
      "summary": { "degradations": 0, "upgrades": 2, "new_tiers": 1 },
      "impact_report_uuid": "<uuid>"
    }
  ]
}
```

