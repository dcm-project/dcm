# DCM Admin Web GUI Specification

> **AEP Alignment:** Admin API endpoints referenced in this spec follow [AEP](https://aep.dev) conventions — custom methods use colon syntax (`POST /admin/providers/{uuid}:approve`). See `schemas/openapi/dcm-admin-api.yaml` for the normative specification.


**Document Status:** 🔄 In Progress
**Document Type:** Specification — Platform Administration Interface
**Related Documents:** [Admin API Specification](dcm-admin-api-spec.md) | [Consumer GUI Specification](dcm-consumer-gui-spec.md) | [Provider GUI Specification](dcm-provider-gui-spec.md) | [Flow GUI Specification](dcm-flow-gui-spec.md)

> **Status:** Draft — Ready for implementation feedback
>
> The Admin GUI is the platform operations console for Platform Admins, SREs, Policy Owners, Security teams, and Auditors. It wraps the Admin API and exposes all platform management capabilities. Like the Consumer GUI, it participates in the same session model — same login, role-gated access to the admin panel.

---

## 1. Architecture

### 1.1 Unified Shell Model

The Admin GUI is not a separate application. It is an **additional surface within the DCM web application**, revealed when the authenticated actor holds a platform-level role (`platform_admin`, `sre`, `auditor`, `security`, `policy_owner`).

```
DCM Web Application
├── Consumer Portal (visible to all authenticated actors)
│     └── [section 2–11 of Consumer GUI spec]
│
├── Admin Panel (visible to platform-level role holders)
│     └── [this spec — section 2–11]
│
├── Provider Management (visible to provider owner roles)
│     └── [Provider GUI spec — dcm-provider-gui-spec.md]
│
└── Flow GUI (linked / embedded for policy_owner and sre)
      └── [dcm-flow-gui-spec.md]
```

Navigation adapts to the actor's highest privilege level. A Platform Admin sees all three surfaces. A consumer-only actor sees only the Consumer Portal.

### 1.2 Authentication and Role Mapping

The Admin GUI requires the session to carry a platform-level role. The role check is performed client-side on every page load and server-enforced by the Admin API on every request.

| Role | Admin sections available |
|------|--------------------------|
| `platform_admin` | All Admin sections |
| `sre` | Health, Discovery, Orphan Management, Scoring, Session Management |
| `security` | Audit, Session Management (force revoke), Accreditation |
| `policy_owner` | Policy management, Approval management, Tier Registry |
| `auditor` | Audit (read-only), Scoring audit trail |
| `finops` | Quota management, Cost aggregation (if FinOps module enabled) |

---

## 2. Platform Overview Dashboard

Landing page for all platform-level roles. Data aggregated from `GET /api/v1/admin/health` and related endpoints.

```
┌─────────────────────────────────────────────────────────────────┐
│  DCM Platform Health                              ● All Systems ✅│
│  ─────────────────────────────────────────────────────────────  │
│  Control Plane                    Providers                      │
│  API Gateway      ✅ pass         Registered:    12             │
│  Policy Engine    ✅ pass         Healthy:       11             │
│  Scoring Engine   ✅ pass         Degraded:       1  ⚠️         │
│  Request Sched.   ✅ pass         Unhealthy:      0             │
│  Drift Reconciler ✅ pass                                        │
│                                   Auth Providers                 │
│  Stores                           Registered:     2             │
│  Session Store    ✅ pass         Healthy:        2             │
│  Audit Store      ✅ pass                                        │
│  ─────────────────────────────────────────────────────────────  │
│  Pending Approvals: 3 🔔  |  Open Drift Records: 7  |  Orphans: 0│
└─────────────────────────────────────────────────────────────────┘
```

Dashboard widgets (configurable per role):
- Control plane component health grid
- Provider health summary with degraded/unhealthy callouts
- Pending approvals count (with link to approval queue)
- Open drift records by severity
- Active sessions count
- Request pipeline throughput (requests/minute, last 1 hour)
- Scheduled requests queue depth

---

## 3. Tenant Management

**API:** `GET /api/v1/admin/tenants`, `POST /api/v1/admin/tenants`, `POST /api/v1/admin/tenants/{uuid}:suspend`, `POST /api/v1/admin/tenants/{uuid}:reinstate`, `DELETE /api/v1/admin/tenants/{uuid}`

- Tenant list with status, member count, resource count, quota utilization
- Create tenant form: name, description, initial quota set, initial admin member
- Tenant detail: members, resource count by type, quota view, active sessions count
- Suspend / reinstate / decommission with confirmation dialog requiring typed tenant name
- Tenant audit trail: all admin actions taken on this tenant

---

## 4. Provider Management

**API:** `GET /api/v1/admin/providers`, `GET /api/v1/admin/providers/pending`, `POST /api/v1/admin/providers/{uuid}:approve`, `POST /api/v1/admin/providers/{uuid}:reject`, `POST /api/v1/admin/providers/{uuid}:suspend`

> **Full provider management** (configuration, capacity, entity lists, type-specific management) is in the **[Provider GUI](dcm-provider-gui-spec.md)**. This section covers the admin-level registration approval workflow.

- Pending registrations list: provider type, submitter, submission time, capability declaration summary
- Registration review: full capability declaration YAML, validation result, automated checks passed/failed
- Approve / reject with comment (recorded in audit trail)
- Active providers list: health status, entity count, last health check time
- Suspend provider: warns if active entities will be affected and shows count

---

## 5. Accreditation Management

**API:** `GET /api/v1/admin/accreditations`, `POST /api/v1/admin/accreditations/{uuid}:approve`, `DELETE /api/v1/admin/accreditations/{uuid}`

- Pending accreditations queue with submission detail
- Approve / revoke with required comment
- Accreditation expiry calendar: upcoming renewals in P90D window highlighted
- Accreditation gap detection: data classifications that require accreditations not currently held

---

## 6. Discovery and Orphan Management

**API:** `POST /api/v1/admin/discovery:trigger`, `GET /api/v1/admin/discovery/jobs/{uuid}`, `GET /api/v1/admin/orphans`, `POST /api/v1/admin/orphans/{uuid}/resolve`

### 6.1 Discovery Console

- Trigger on-demand discovery by resource type and provider
- Discovery job status with progress (resources scanned, new discoveries, changes detected)
- Discovery history: recent jobs with outcome summary

### 6.2 Orphan Resolution Queue

- List orphan candidates: resources discovered in provider that have no DCM Realized State record
- Per-orphan action: Ingest (create Realized State record), Decommission (instruct provider to delete), Ignore (mark as known-unmanaged)
- Bulk actions for same-type orphans

---

## 7. Quota Management

**API:** `GET /api/v1/admin/tenants/{uuid}/quotas`, `PUT /api/v1/admin/tenants/{uuid}/quotas/{resource_type}`

- Per-tenant quota view: current limits vs current usage vs projected usage
- Inline edit quota values; save triggers `PUT /api/v1/admin/tenants/{uuid}/quotas/{resource_type}`
- Quota utilization heatmap across all tenants (who is using the most of what)
- Quota alert configuration: threshold for "approaching limit" notifications

---

## 8. Scoring Model Administration

**API:** `GET /api/v1/admin/profiles/{name}/scoring`, `PATCH /api/v1/admin/profiles/{name}/scoring`, `POST /api/v1/admin/profiles/{name}/scoring/overrides`, `GET /api/v1/admin/scoring/audit`, `GET /api/v1/admin/actors/{uuid}/risk-history`

### 8.1 Profile Scoring Configuration

- Score threshold table per profile: approval routing tiers vs score ranges
- Visual slider interface for threshold adjustment (guardrail: auto_approve_below ≤ 50 enforced — slider hard-stops at 50)
- Signal weight editor: operational_gatekeeper (45%), completeness (15%), actor_risk_history (20%), quota_pressure (10%), provider_accreditation (10%) — weights must sum to 100%
- Preview: submit a sample request to see the score it would receive under current config

### 8.2 Policy Enforcement Override

- Per-policy enforcement class override: escalate operational → compliance, or demote compliance → operational
- Required justification field; change recorded in audit trail
- Shadow policies table with divergence rates — promotes action for high-divergence policies

### 8.3 Actor Risk History

- Search by actor UUID or handle
- Risk signal history timeline: what events contributed to elevated risk score
- Manual reset capability (requires `platform_admin` role + comment)

---

## 9. Approval Management

**API:** `GET /api/v1/admin/approvals/pending`, `POST /api/v1/admin/approvals/{uuid}:vote`, `GET /api/v1/admin/approvals/{uuid}`

- All pending approvals across all tenants (Platform Admin view) vs own queue (approver view)
- Filter by tier (reviewed / verified / authorized), resource type, tenant, age
- Approval detail: request payload, risk score breakdown, policy evaluation results, existing votes
- Vote with comment; authorized-tier quorum tracker
- Expired approvals: review and optionally reopen

---

## 10. Authority Tier Registry

**API:** `POST /api/v1/admin/tier-registry/changes`, `GET /api/v1/admin/tier-registry/changes/{uuid}/impact`, `POST /api/v1/admin/tier-registry/changes/{uuid}:accept-degradation`, `POST /api/v1/admin/tier-registry/changes/{uuid}:activate`

- Current tier registry: ordered list display (auto → reviewed → verified → authorized → [custom tiers])
- Propose change: drag-and-drop reordering with add/remove custom tier
- Impact report: automatically fetched after proposal; displays SECURITY_DEGRADATION (red), BROKEN_REFERENCE (orange), PROFILE_GAP (yellow), SECURITY_UPGRADE (green)
- Degradation acceptance: per-item accept flow with required compensating control rationale
- Activate button disabled until all blocking items are resolved

---

## 11. Audit and Compliance

**API:** `GET /api/v1/audit/...` (admin-scoped, cross-tenant)

Visible to `auditor` and `platform_admin` roles.

- **Platform-wide audit trail**: all DCM actions across all tenants; filterable by actor, tenant, resource type, operation, date range
- **Compliance reports**: pre-built reports for common frameworks (SOC 2 Type II, FedRAMP, HIPAA) — export to PDF/CSV
- **Audit chain integrity status**: last verification timestamp; trigger re-verification; alert on chain break
- **Cross-tenant correlation**: enter correlation ID to trace a request end-to-end across tenants and providers

---

## 12. Session and Security Management

**API:** `GET /api/v1/admin/actors/{uuid}/...`, `POST /api/v1/admin/actors/{uuid}:revoke-sessions`

Visible to `security` and `platform_admin` roles.

- **Active sessions**: all active sessions across all actors; filterable by auth provider, role, tenant
- **Force revoke**: select one or all sessions for an actor; requires reason (logged to audit)
- **Security events**: real-time feed of auth.security_session_revoked and ICOM_UNAUTHORIZED_SOURCE events
- **Internal component certificates**: table of component cert expiry dates; alert on certs expiring within P14D; ICOM-006 compliance view

---

## 13. Health and Operations

**API:** `GET /api/v1/admin/health`, `GET /api/v1/admin/discovery:trigger`, `POST /api/v1/admin/search-index:rebuild`

Visible to `sre` and `platform_admin` roles.

- Full component health detail (Section 2 dashboard expanded view)
- Prometheus metrics viewer (embedded Grafana or linked)
- Manual operations: trigger discovery, rebuild search index, rotate bootstrap credential
- Deployment info: DCM version, instance UUID, profile, uptime
- **Runbook links**: direct links to doc 41 (Operational Reference) scenarios from health page

---

## 14. Flow GUI Integration

The Flow GUI (policy authoring tool — separate spec) is accessible to actors with `policy_owner` or `sre` roles:

- **Link** from the Admin Panel navigation to the Flow GUI
- **Embedded iframe** option for deployments that want a unified navigation experience
- Active profile and policy summary widgets from Flow GUI embeddable on the Admin dashboard

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
