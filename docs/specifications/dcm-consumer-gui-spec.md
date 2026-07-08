# DCM Consumer Web GUI Specification

> **AEP Alignment:** Consumer API endpoints referenced in this spec follow [AEP](https://aep.dev) conventions — custom methods use colon syntax, async operations return `Operation` resources, and `operation_uuid == request_uuid`. See `schemas/openapi/dcm-consumer-api.yaml` for the normative specification.


**Document Status:** 🔄 In Progress
**Document Type:** Specification — Consumer Web Interface
**Related Documents:** [RHDH Integration Specification](dcm-rhdh-integration-spec.md) | [Consumer API Specification](consumer-api-spec.md) | [Admin GUI Specification](dcm-admin-gui-spec.md) | [Provider GUI Specification](dcm-provider-gui-spec.md) | [Flow GUI Specification](dcm-flow-gui-spec.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Session Revocation](../../architecture/control-plane/session-revocation.md)

> **Status:** Draft — Ready for implementation feedback
>
> **Primary deployment target:** Red Hat Developer Hub (RHDH) or upstream Backstage. The DCM Consumer Portal is implemented as a Backstage plugin suite. The standalone SPA mode is an alternative for deployments that do not run RHDH. See [RHDH Integration Specification](dcm-rhdh-integration-spec.md) for the complete Backstage plugin architecture.
>
> **Design goals (in priority order):**
> 1. **Low time to market** — RHDH brings auth, search, TechDocs, RBAC, GitOps integration, and a full component library pre-built. DCM plugins extend rather than rebuild.
> 2. **Ease of use** — familiar mental models (PatternFly/OpenShift language); task-oriented navigation; zero-ticket provisioning.
> 3. **Extensible** — plugin architecture means new resource types surface automatically; no GUI code changes for new catalog items.
> 4. **Security and governance by design** — tenancy, RBAC, audit, and policy constraints are architectural, not add-ons.

---

## 1. Deployment Models

### 1.1 RHDH / Backstage Mode (Primary)

DCM is implemented as a Backstage plugin suite loaded into an RHDH or Backstage instance. DCM capabilities appear as a first-class section within the existing RHDH navigation.

```
RHDH Instance
├── Pre-built RHDH capabilities (Catalog, Create, TechDocs, Search, ...)
│     └── These work unchanged — DCM augments them
│
└── DCM Plugin Suite (loaded as Dynamic Plugins)
      ├── @dcm/plugin                 frontend plugin — nav + pages + entity tabs
      ├── @dcm/plugin-backend         backend plugin — API proxy, SSE relay, auth
      ├── @dcm/plugin-catalog-backend catalog processor + entity provider
      ├── @dcm/plugin-scaffolder-backend custom scaffolder actions
      └── @dcm/permission-policy      DCM → Backstage permission bridge
```

**Why RHDH first:**
- Auth (RHSSO/Keycloak/OIDC) is already configured — no auth plumbing
- RBAC plugin already provides no-code permission management
- Search indexes DCM entities alongside existing catalog entities
- TechDocs renders DCM data model docs and runbooks in-portal
- Dynamic Plugins — DCM plugins load without rebuilding the RHDH image (OCI or npm)
- Existing integrations: ArgoCD/GitOps (layer store visibility), Tekton (scaffolding pipelines), AAP (DCM providers that use Ansible), OCM (cluster management alongside DCM service catalog)

### 1.2 Standalone SPA Mode (Alternative)

For deployments without RHDH, DCM ships a standalone React SPA using PatternFly components. The same plugin modules are used; the host application is a lightweight Backstage-compatible shell rather than full RHDH.

```
Standalone DCM App
├── PatternFly Page shell (Header, Sidebar, Content)
├── Auth: DCM Auth Provider (OIDC/LDAP/built-in)
└── DCM plugin modules (same packages as RHDH mode)
```

The standalone mode provides feature parity. RHDH mode is recommended because it provides broader platform capabilities without additional investment.

---

## 2. Navigation Architecture

### 2.1 Design Principles

**Organized by what users want to accomplish, not by API object.** A user who wants to "check on my database VM" thinks "My Resources" — not "Realized State Entity Management." The navigation labels match the user's mental model.

**PatternFly grouped hierarchical left nav.** Following OpenShift console and PatternFly's recommended pattern for administrative interfaces with multiple entity types. Consistent with what Red Hat users already know.

**Stable groups, role-gated items.** Group headings are always visible; items within them hide (not disable) based on the actor's roles. A user who gains the `approver` role sees Approvals appear without any change to the application.

**Tenant context in the header, not in the nav.** Following RHDH's namespace/group context selector pattern — the active tenant is ambient context shown in the masthead, switchable without navigating away.

### 2.2 Navigation Structure

```
[RHDH Masthead]
┌──────────────────────────────────────────────────────────────┐
│ ⬡ Red Hat Developer Hub     [Search]    👤 User  🏢 Tenant  │
└──────────────────────────────────────────────────────────────┘

[Sidebar — DCM section within RHDH nav]
━━━━━━━━━━━━━━━━━━
 DCM                           ← Section header in RHDH sidebar
━━━━━━━━━━━━━━━━━━
 🏪 Service Catalog

 MY WORK                       ← NavGroup (non-clickable group label)
   📋 Requests
   🖥  Resources
   🔗 Dependency Groups

 🔔 Approvals        [3]       ← NavItem with NotificationBadge (orange, count)

 GOVERNANCE                    ← NavGroup
   💰 Cost & Quota
   📤 Contributions            ← hidden if not contributor role

 SETTINGS                      ← NavGroup
   🔔 Notifications
   🔐 Sessions
━━━━━━━━━━━━━━━━━━
```

**PatternFly components used:**
- `Nav` with `variant="default"` — left sidebar navigation
- `NavGroup` — non-clickable group labels (MY WORK, GOVERNANCE, SETTINGS)
- `NavItem` — clickable navigation items with optional `<NotificationBadge>`
- `NavItemSeparator` — visual divider between major areas
- `PageHeader` with `Masthead` — tenant context selector (ContextSelector component)

### 2.3 Tenant Context Selector

The active tenant is displayed in the masthead as a `ContextSelector` (PatternFly):

```
[Masthead right side]
  👤 alice@corp.com    🏢 Payments Team ▾
                            ├── Payments Team      ← current
                            ├── Platform Team
                            └── ─────────────
                                All My Tenants
```

- Single-tenant actors: selector hidden; tenant name displayed static
- Multi-tenant actors: dropdown triggers `X-DCM-Tenant` header change; page data refreshes
- Tenant switch does not navigate; current page re-fetches with new tenant context

### 2.4 Role-Gating Rules

| NavItem | Visible when actor has |
|---------|----------------------|
| Service Catalog | Any role (always visible) |
| Requests | `consumer` or any role |
| Resources | `consumer` or any role |
| Dependency Groups | `consumer` or any role |
| Approvals + badge | `approver` role |
| Cost & Quota | `consumer` or `tenant_admin` |
| Contributions | `contributor` role |
| Notifications | Any role |
| Sessions | Any role |

Items not shown for a role are **hidden entirely** — no disabled states in the nav.

---

## 3. Service Catalog

**Route:** `/dcm/catalog`  
**API:** `GET /api/v1/catalog`, `GET /api/v1/catalog/{uuid}`, `GET /api/v1/catalog/search`

### 3.1 In RHDH Mode — Software Templates Integration

In RHDH, DCM catalog items are exposed as **Backstage Software Templates**. The standard RHDH "Create" page becomes the DCM service catalog.

```
RHDH "Create" page
└── DCM Templates category
      ├── 🖥  Standard VM (t-shirt sizes)
      ├── 🗄  Database — PostgreSQL
      ├── 🌐  Virtual Network
      ├── 🔒  TLS Certificate
      └── 📦  [More DCM catalog items...]
```

Templates are auto-generated by `@dcm/plugin-catalog-backend` — it reads `GET /api/v1/catalog` and emits one Template entity per DCM catalog item. The template's input schema is derived directly from the DCM catalog item's field schema. No manual template authoring needed when a new resource type appears.

DCM-specific catalog view at `/dcm/catalog` provides additional DCM context:
- Cost estimate per item (calls `POST /api/v1/cost/estimate` with default values)
- Availability indicator (quota headroom)
- Dependency graph preview
- Provider badge and SLA indicators

### 3.2 Catalog Browser

- **Card grid** — PatternFly `Gallery` with `GalleryItem` cards
- **Filter toolbar** — PatternFly `Toolbar` with category chips, tag filter, search input
- Card shows: name, description, provider type badge, cost estimate, availability
- Quick-request button opens the scaffolder template directly from the card

### 3.3 Catalog Item Detail

- Full description, field schema viewer, dependency declaration, TechDocs link
- Live cost estimate — updates as user adjusts quantity/size fields (debounced)
- Quota check: remaining quota for this resource type in active tenant
- "Request This Service" → opens Scaffolder wizard

---

## 4. Request Submission — Scaffolder Integration

**In RHDH mode:** Request submission uses the Backstage Scaffolder. DCM does not build a separate request form. The Scaffolder is the request form.

### 4.1 Template Structure

Each DCM catalog item generates a Backstage Software Template:

```yaml
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: dcm-compute-vm-standard
  title: "Standard VM"
  description: "Provision a standard virtual machine"
  annotations:
    dcm.io/catalog-item-uuid: "<uuid>"
    dcm.io/resource-type: "Compute.VirtualMachine"
  tags: [dcm, compute, infrastructure]
spec:
  type: dcm-resource
  parameters:
    # Auto-generated from DCM catalog item field schema
    - title: "Configure Your VM"
      required: [cpu_count, memory_gb, os_family, name]
      properties:
        cpu_count:
          title: CPU Cores
          type: integer
          enum: [2, 4, 8, 16, 32]
          default: 4
          ui:widget: select
        memory_gb:
          title: Memory (GB)
          type: integer
          enum: [8, 16, 32, 64, 128]
          default: 16
        name:
          title: Resource Name
          type: string
          pattern: "^[a-z0-9-]{3,63}$"
          ui:help: "Lowercase letters, numbers, hyphens. 3-63 characters."

    - title: "Scheduling (Optional)"
      properties:
        dispatch:
          title: When to provision
          type: string
          enum: [immediate, at, window]
          default: immediate
        not_before:
          title: Not before (UTC)
          type: string
          format: date-time
          ui:widget: datetime
          ui:if: "dispatch === 'at'"
        window_id:
          title: Maintenance Window
          type: string
          ui:field: dcm:MaintenanceWindowPicker
          ui:if: "dispatch === 'window'"

    - title: "Review"
      # Auto-populated review step showing cost estimate and policy pre-check

  steps:
    - id: dcm-cost-estimate
      name: "Estimate cost"
      action: dcm:request:estimate
      input:
        catalogItemUuid: "${{ parameters.catalog_item_uuid }}"
        fields: "${{ parameters }}"

    - id: dcm-submit
      name: "Submit request"
      action: dcm:request:submit
      input:
        catalogItemUuid: "${{ parameters.catalog_item_uuid }}"
        fields: "${{ parameters }}"
        schedule:
          dispatch: "${{ parameters.dispatch }}"
          notBefore: "${{ parameters.not_before }}"

    - id: dcm-wait
      name: "Waiting for provisioning..."
      action: dcm:request:wait
      input:
        requestUuid: "${{ steps.dcm-submit.output.requestUuid }}"
        timeoutMinutes: 30

    - id: register
      name: "Register in catalog"
      action: dcm:catalog:refresh
      input:
        entityUuid: "${{ steps.dcm-submit.output.entityUuid }}"

  output:
    links:
      - title: "View Resource"
        url: "${{ steps.dcm-wait.output.entityUrl }}"
      - title: "View Request"
        url: "${{ steps.dcm-submit.output.requestUrl }}"
```

### 4.2 Custom Scaffolder Actions

Provided by `@dcm/plugin-scaffolder-backend`:

| Action | Description |
|--------|-------------|
| `dcm:request:estimate` | Call `POST /api/v1/cost/estimate`; output cost breakdown for review step |
| `dcm:request:submit` | `POST /api/v1/requests`; output requestUuid, entityUuid |
| `dcm:request:wait` | Poll `GET /api/v1/requests/{uuid}/status` (or SSE); surface live status in Scaffolder log; resolve on terminal state |
| `dcm:request:group` | `POST /api/v1/request-groups`; submit multiple requests with dependency graph |
| `dcm:catalog:refresh` | Trigger entity provider refresh for new entity; output entityUrl for output links |
| `dcm:approval:notify` | Fire notification to approver group when approval required |

### 4.3 Live Status in Scaffolder

The `dcm:request:wait` action streams progress to the Scaffolder log panel using the Scaffolder's built-in log streaming UI:

```
⏳  Waiting for provisioning...
    09:00:05  Status: ACKNOWLEDGED
    09:00:07  Status: ASSEMBLING layers
    09:00:12  Status: DISPATCHED to provider
    09:01:05  Status: PROVISIONING
              Step 3/7: Configuring network interfaces
              ████████████░░░░░░░░  3 of 7 complete
    09:03:12  ✅ Status: REALIZED
              Resource: payments-api-server-01
              IP: 10.42.0.105
```

This reuses the Scaffolder's existing log streaming rather than building a custom progress component.

---

## 5. My Work — Requests

**Route:** `/dcm/requests`  
**API:** `GET /api/v1/requests`, `GET /api/v1/requests/{uuid}/status`, `GET /api/v1/requests/{uuid}/stream`, `DELETE /api/v1/requests/{uuid}`

### 5.1 Requests List

PatternFly `Table` with Toolbar filter:

```
[MY REQUESTS]
Filter: [Status ▾] [Resource Type ▾] [Date Range ▾]   [Search name...]

  Name                    Type         Status           Submitted
  ─────────────────────────────────────────────────────────────────
  payments-api-server-01  Compute.VM   ● REALIZED       2h ago
  dev-db-postgres-02      Database     ⏳ PROVISIONING  15m ago   [Live ▶]
  uat-lb-internal         LoadBalancer ⚠ REQUIRES APPR. 1h ago   [Review →]
  batch-runner-scheduled  Compute.VM   🕐 SCHEDULED     Tomorrow
```

Status badges use PatternFly `Label` component:
- `● REALIZED` — green Label
- `⏳ PROVISIONING` — blue Label + spinner
- `⚠ REQUIRES APPROVAL` — orange Label
- `🕐 SCHEDULED` — grey Label
- `✗ FAILED` — red Label

"Live ▶" button opens an inline `Drawer` (PatternFly) showing the SSE status stream — no page navigation required.

### 5.2 Live Status Drawer

Clicking "Live ▶" opens a right-side Drawer anchored to the page:

```
┌─── Request Status ───────────────────────────────── ✕ ─┐
│  dev-db-postgres-02            ⏳ PROVISIONING          │
│                                                          │
│  Timeline:                                              │
│  ✅ 09:00:00  ACKNOWLEDGED                              │
│  ✅ 09:00:02  ASSEMBLING                                │
│  ✅ 09:00:47  DISPATCHED → provider-postgres-prod       │
│  ⏳ 09:01:05  PROVISIONING                              │
│                                                          │
│  Progress: Step 3 of 7                                  │
│  Configuring network interfaces                          │
│  ████████████░░░░░░░░░░░░  43%                          │
│                                                          │
│  Est. completion: ~4 minutes                            │
│                               [Cancel Request]          │
└──────────────────────────────────────────────────────────┘
```

Powered by `GET /api/v1/requests/{uuid}/stream` (SSE). Drawer closes automatically on terminal status, replaces status badge in the table row.

---

## 6. My Work — Resources

**Route:** `/dcm/resources`  
**API:** `GET /api/v1/resources`, resource sub-resource endpoints

### 6.1 Resource List

```
[MY RESOURCES]
Filter: [State ▾] [Type ▾] [Group ▾] [Tag ▾]       [Search...]    [Table/Card ▾]

  ● 3 resources with drift detected  [View Drift Report →]

  Name                  Type        State        Provider     TTL
  ────────────────────────────────────────────────────────────────
  payments-api-01  ⚡  Compute.VM   ✅ OPER.      k8s-prod    87d   [···]
  dev-db-001            Database    ✅ OPER.      db-prod     —     [···]
  uat-loadbalancer  🔴  Network.LB  ⚠ DRIFT      net-prod    —     [···]
```

Icons:
- `⚡` — TTL warning (< 14 days)
- `🔴` dot — open drift record
- `···` — action menu (Suspend, Update, Extend TTL, Transfer, Decommission)

State badges use PatternFly `Label`:
- `✅ OPERATIONAL` — green
- `🟡 SUSPENDED` — yellow
- `🔵 MAINTENANCE` — blue
- `⚠ DRIFT` — orange (custom — shows worst drift severity)
- `✗ FAILED` — red

### 6.2 Resource Entity Page

Clicking a resource opens its **Backstage entity page** (standard RHDH pattern). DCM contributes tabs via entity page tab extensions:

```
[Entity Header]
payments-api-server-01                               ✅ OPERATIONAL
Compute.VirtualMachine  |  provider: k8s-prod  |  owner: payments-team

[Tabs]
  Overview │ Drift 🔴 │ Audit │ Cost │ Credentials │ Relations │ Docs
```

**Overview tab:** IP address, hostname, CPU, memory, OS, provider, realized date, TTL, all realized fields from provider.

**Drift tab 🔴** (badge shows drift severity):
```
Open Drift Records (1 significant, 1 minor)

  Field          Realized Value    Discovered Value    Severity
  cpu_count      4                 8                   ⚠ significant
  memory_gb      16                16                  ✅ no drift
  tags           [app:api]         [app:api, env:prod]  ℹ minor

  Actions: [Revert All]  [Accept Changes (Update Definition)]  [Acknowledge Minor]
```

**Cost tab:** Actual cost from `GET /api/v1/resources/{uuid}/cost`. PatternFly `ChartBar` for cost by billing dimension.

**Credentials tab:**
```
  Credential           Type         Expires      Last Retrieved
  ssh-key-payments-01  ssh_key      2027-06-01   2 days ago
  api-key-svc-acct     api_key      never         —

  [Retrieve Value →]   ← triggers inline step-up MFA prompt
  [Request Rotation →]
```

**Relations tab:** PatternFly `TopologyView` or a simple dependency graph showing what this resource depends on and what depends on it.

### 6.3 Drift Report — Cross-Resource View

**Route:** `/dcm/resources/drift`  
Accessible via "View Drift Report →" banner on resource list when drift exists.

```
[DRIFT REPORT — Payments Team]           3 resources with open drift

  Severity  Resource              Field           Realized    Discovered  Since
  ──────────────────────────────────────────────────────────────────────────────
  ● Critical  prod-db-primary     replication      enabled     disabled    4h
  ● Signif.   uat-lb-internal     cpu_count        4           8           2d
  ● Minor     dev-app-01          tag:env          staging     (missing)   1w

  [Revert All Critical]   [Export Drift Report]   [Configure Drift Alerts]

  Auto-remediation status:
  prod-db-primary: REVERT_PENDING — waiting for maintenance window
```

Severity filter chips at top (PatternFly `ChipGroup`). Clicking a row opens the resource entity Drift tab.


---

## 7. My Work — Dependency Groups

**Route:** `/dcm/dependency-groups`  
**API:** `GET /api/v1/request-groups`, `GET /api/v1/request-groups/{uuid}`, `DELETE /api/v1/request-groups/{uuid}`

```
[MY DEPENDENCY GROUPS]

  three-tier-app-deploy          in_progress          Started 30m ago
  ├── db          ✅ REALIZED    payments-db-01        09:01
  ├── app         ⏳ DISPATCHED  (pending db IP → db_host injected)
  └── lb          ○ PENDING      (waiting for app)

  [Cancel Group]  [View All Requests]
```

Progress bar shows N of M constituents realized.

---

## 8. ITSM Integration

DCM is designed to eliminate the infrastructure ticket as the primary provisioning mechanism. However, organizations that operate ITSM systems (ServiceNow, Jira Service Management, Remedy) still require bidirectional traceability — change records for compliance, incident linkage for troubleshooting, and CMDB accuracy.

DCM's ITSM integration is a **bridge, not a dependency.** DCM does not require an ITSM system to function. ITSM integration is additive — it enriches DCM entities with ITSM metadata and notifies ITSM of DCM lifecycle events.

### 8.1 ITSM Reference Linking

Every DCM resource entity supports an optional `itsm_references` metadata block in its business data:

```
[Resource Entity Header]
payments-api-server-01                                ✅ OPERATIONAL

[ITSM References — visible as a metadata card on Overview tab]
  Change Record    CHG0012345    Approved 2026-03-15   [View in ServiceNow ↗]
  Incident         INC0048291    (linked on creation)  [View in Jira ↗]
  CMDB Item        CI-VM-08821   Auto-synced           [View in CMDB ↗]
```

References are stored as business data fields on the entity — they follow the entity through its full lifecycle and appear in audit records. They are **not** required for DCM to function.

### 8.2 ITSM Event Webhook Integration

DCM fires lifecycle events to the Message Bus. An ITSM notification service subscribes to these events and creates/updates ITSM records accordingly:

| DCM Event | ITSM Action (configurable) |
|-----------|---------------------------|
| `request.requires_approval` | Create Change Request draft in ServiceNow / Jira |
| `request.realized` | Close Change Request; update CMDB CI |
| `request.failed` | Create Incident; link to Change Request |
| `entity.state_changed` | Update CMDB CI state |
| `drift.detected` (significant/critical) | Create Incident in ITSM |
| `entity.decommissioned` | Retire CMDB CI; close related Change Requests |

This is implemented as a **notification service** registered in DCM — a webhook consumer that translates DCM events to ITSM API calls. No changes to DCM core are needed.

### 8.3 ITSM Ticket as Approval Mechanism

For organizations that require ITSM change board approval, DCM's `authorized` tier approval mechanism accepts votes recorded via the ITSM system:

```
[Request reaches authorized tier → approval required]
  │
  ▼ DCM fires request.requires_approval
  │   notification service creates Change Request in ServiceNow
  │
  ▼ Change Board reviews in ServiceNow (existing process unchanged)
  │   Approval decision → ServiceNow calls DCM Admin API:
  │   POST /api/v1/admin/approvals/{uuid}:vote
  │   { "decision": "approve", "recorded_via": "servicenow", "voter_uuid": "..." }
  │
  ▼ DCM records vote; quorum tracked by DCM
  │   Audit trail includes: who voted, via which system, at what time
```

The approval decision is made in ServiceNow using the organization's existing CAB process. DCM records the outcome. Neither system depends on the other's internal workflow model.

### 8.4 ITSM Reference UI

In the Consumer GUI, ITSM references surface in two places:

**On resource entity Overview tab** — ITSM References card (shown only when references exist):
```
ITSM References
  ┌────────────────────────────────────────────────────────┐
  │  CHG0012345  Change Request   Approved  [Open ↗]      │
  │  INC0048291  Incident         Resolved  [Open ↗]      │
  └────────────────────────────────────────────────────────┘
  [Add Reference]  (opens modal: type, ID, system URL)
```

**On request status page** — when a request is at `requires_approval` and an ITSM reference is attached:
```
⏳ REQUIRES APPROVAL — verified tier
   Approval being tracked via ServiceNow Change Board
   CHG0012345 [View in ServiceNow ↗]
   Quorum: 0 / 2 votes recorded
```

### 8.5 CMDB Sync

DCM entities are the **system of record** for realized state. The CMDB is a **consumer** of DCM data, not a producer. CMDB sync flows one way: DCM → CMDB.

The sync is implemented via the notification service subscription to `entity.*` events. A CMDB sync notification service maps DCM entity fields to CMDB CI attributes and calls the CMDB API on every state change.

**CMDB field mapping** is declared in the provider registration — it is not hardcoded. Different CMDB systems (ServiceNow CMDB, iTop, Device42) use the same event subscription pattern with different field mapping configurations.

---

## 9. Approvals

**Route:** `/dcm/approvals`  
**API:** `GET /api/v1/approvals/pending`, `POST /api/v1/approvals/{uuid}`

Visible only to actors with `approver` role. NavItem shows orange badge with pending count.

```
[PENDING APPROVALS — 3]

  Request                  Tenant      Tier       Risk   Expires
  ────────────────────────────────────────────────────────────────
  Large GPU VM (8x A100)   AI Team     verified    72/100  2h 14m
  Prod DB 32-core          Data Team   reviewed    41/100  23h
  Bulk decommission (12)   Platform    authorized  88/100  45m  ← quorum 1/3

  [Review →]
```

Clicking "Review →" opens the Approval Detail page:
- Full request payload summary
- Risk score breakdown (signal chart)
- Policy evaluation results (which policies flagged this)
- Existing votes (for authorized tier quorum tracking)
- [Approve] [Reject] buttons with required comment field
- Approver cannot vote on own requests (blocked UI-side + server-side)

---

## 10. Governance — Cost and Quota

**Route:** `/dcm/cost`

```
[COST & QUOTA — Payments Team]   This month: $12,450   vs budget: $15,000

  Quota Utilization
  Compute.VM          ████████████████░░░░  80%  (16/20 allocated)  ⚠
  Storage.Block       ████░░░░░░░░░░░░░░░░  22%  (11/50 TB)
  Network.LB          ██░░░░░░░░░░░░░░░░░░   8%  (2/25 units)

  Cost by Resource Type (last 30 days)
  [PatternFly ChartDonut or ChartBar]

  Top Cost Resources
  payments-api-01    Compute.VM    $3,200/mo
  payments-db-01     Database      $2,800/mo
  ...

  [Export CSV]  [View All Resources]
```

---

## 11. Governance — Audit Trail

**Route:** `/dcm/audit`  
**API:** `GET /api/v1/resources/{uuid}/audit`, `GET /api/v1/audit/correlation/{correlation_id}`

Visible to all actors for their own resources. Cross-tenant audit is in the Admin Panel.

```
[MY AUDIT TRAIL]
Filter: [Resource Type ▾] [Operation ▾] [Date Range ▾]   [Correlation ID search...]

  Time          Resource                Operation        Actor
  ─────────────────────────────────────────────────────────────────────
  5m ago        payments-api-01         PATCH            alice@corp.com
  2h ago        dev-db-001              DRIFT_REVERT     system
  Yesterday     uat-lb-internal         REALIZED         alice@corp.com
  2 days ago    batch-runner-01         DECOMMISSIONED   bob@corp.com

  [View Full Record →]   [Export CSV]
```

**Record detail drawer:** Operation, Resource, Actor (with auth method), Time, Correlation ID trace, fields changed, policy evaluations, risk score.

**Correlation ID trace:** links to full request pipeline view — Intent → Requested → Dispatch → Realized → Provider chain — for the actor's own requests.

---

## 12. Governance — Contributions

**Route:** `/dcm/contributions`  
**API:** `GET /api/v1/contribute`, `POST /api/v1/contribute/policy`, `DELETE /api/v1/contribute/{uuid}`

Visible only to actors with `contributor` role.

```
[MY CONTRIBUTIONS]

  Handle                     Type              Status         Submitted
  ─────────────────────────────────────────────────────────────────────
  payments-network-policy    policy            ● active       3 months ago
  gpu-quota-validator        policy            🔵 shadow      1 week ago   [Divergence: 2.3%]
  ml-resource-group          resource_group    ⏳ reviewing   2 days ago

  [Submit New Policy]  [Submit Resource Group]
```

Shadow divergence percentage shown for shadow-mode contributions — clicking opens divergence case viewer.

---

## 13. Settings — Notifications

**Route:** `/dcm/notifications`  
**API:** `GET /api/v1/notifications`, `GET /api/v1/webhooks`, `POST /api/v1/webhooks`

```
[NOTIFICATIONS]     [Mark All Read]

  🔔 Request REALIZED: payments-api-server-01          2m ago   [View →]
  ⚠  Drift detected: uat-loadbalancer (significant)    1h ago   [View →]
  ⏰ TTL Warning: dev-db-001 expires in 7 days          3h ago   [Extend →]

  ─────────────────
  [WEBHOOK SUBSCRIPTIONS]

  URL                                  Events                Status
  https://my-system/dcm-webhook        request.*, drift.*    ✅ active  [Test] [Delete]

  [Add Webhook]
```

---

## 14. Settings — Sessions

**Route:** `/dcm/sessions`  
**API:** `GET /api/v1/auth/sessions`, `DELETE /api/v1/auth/sessions/{uuid}`

```
[ACTIVE SESSIONS]

  Device                    Auth Method   Created         Last Active
  ──────────────────────────────────────────────────────────────────
  This session ●            OIDC          Today 09:00     Active now
  Chrome / Mac (10.0.1.5)   OIDC          Yesterday       2h ago       [Revoke]
  API Client (svc-acct)     api_key       3 days ago      1h ago       [Revoke]

  [Sign Out All Other Sessions]
```

---

## 15. In RHDH — TechDocs Integration

DCM publishes TechDocs for:
- Service catalog item documentation (from DCM layer store)
- Resource type specifications
- DCM data model documentation (this spec set)

TechDocs are indexed by RHDH search — users can search "how do I provision a GPU cluster" and find both the catalog item and the documentation.

DCM entity pages link to TechDocs automatically via `backstage.io/techdocs-ref` annotation on generated catalog entities.

---

## 16. Search Integration

In RHDH mode, DCM entities are indexed in Backstage search:

- DCM catalog items indexed as `DCMService` entities — searchable by name, description, tags
- DCM realized resources indexed as `DCMResource` entities — searchable by handle, IP, type
- TechDocs content indexed — searchable documentation
- Search collator provided by `@dcm/plugin-catalog-backend`

Search result rendering:
```
  🖥 payments-api-server-01    DCMResource    Compute.VM    ● OPERATIONAL
     10.42.0.105 · k8s-prod · payments-team
```

---


### 16.1 Global Search Bar

PatternFly `SearchInput` in masthead — keyboard shortcut `/` to focus. Searches across catalog items, resources, requests, and TechDocs (RHDH mode).

### 16.2 Search Results Page

**Route:** `/dcm/search?q=<query>`

```
[SEARCH RESULTS: "payments db"]                    12 results

  [All ▾] [Catalog Items] [Resources] [Requests] [Docs]   ← filter chips

  CATALOG ITEMS (2)
  ● Database.PostgreSQL   Managed PostgreSQL instance   [Request →]
  ● Database.MySQL        Managed MySQL instance        [Request →]

  MY RESOURCES (3)
  ● payments-db-primary   Database.PostgreSQL  ✅ OPERATIONAL  [View →]
  ● payments-db-replica   Database.PostgreSQL  ✅ OPERATIONAL  [View →]

  MY REQUESTS (1)
  ● payments-db-archive   SCHEDULED  Tomorrow 02:00  [View →]
```

Results render incrementally per category with PatternFly `Spinner` while loading. Keyboard navigation through results supported.

## 17. Path to Production — Effort Reduction Summary

| Traditional Workflow | DCM + RHDH |
|---------------------|------------|
| Submit infrastructure ticket | Browse catalog → click "Request" → Scaffolder wizard |
| Wait for human review (hours/days) | Policy engine auto-approves in seconds; escalates if needed |
| Infrastructure team provisions manually | DCM dispatches to provider automatically |
| Receive confirmation email | SSE live status in Scaffolder; notification in portal |
| Manually update CMDB | Entity appears in RHDH catalog automatically after REALIZED |
| Track cost in spreadsheet | Cost tab on every resource entity page |
| Periodic compliance audits | Drift detection continuous; audit trail always current |
| Decommission via ticket | Self-service Delete with stake resolution |
| Document runbooks separately | TechDocs in same portal, linked from entity pages |
| Separate access management | RHDH RBAC + DCM permission policy — one place |

**Time to first production resource (new user):**
1. Log in (SSO — already have corporate credentials)
2. Browse catalog or search for service
3. Fill in Scaffolder form (5–10 fields, schema-driven, cost estimate live)
4. Submit → watch live provisioning log
5. Resource appears in catalog and "My Resources"

**Target: < 10 minutes from login to operational resource.**

---

## 18. Security Model

### 16.1 Tenancy Enforcement

- Active tenant: RHDH Group context → `X-DCM-Tenant` header on all DCM API calls
- All data filtered server-side by DCM Consumer API (defense in depth)
- Entity ownership in RHDH catalog: `spec.owner = group:<tenant-uuid>` — users see only own-tenant entities

### 16.2 RBAC

- RHDH RBAC plugin maps Backstage permissions to DCM roles
- DCM roles in session token drive nav visibility (client-side, defense-in-depth)
- DCM Consumer API enforces roles server-side on every request
- New roles propagate from IdP via SCIM or OIDC claims — no manual assignment

### 16.3 Step-Up MFA

Credential retrieval, ownership transfer, and bulk decommission trigger inline MFA:
- PatternFly `Modal` overlay — no page navigation
- User completes second factor in RHDH auth provider
- Step-up token cached PT10M (per session model)

### 16.4 Content Security Policy (Standalone Mode)

- `default-src 'self'`
- `connect-src 'self' <dcm-api-origin> <rhdh-origin>`
- No inline scripts; no eval(); SRI on external assets

### 16.5 Governance and Regulatory Compliance

All compliance constraints are enforced by the DCM control plane — the GUI is a client. The GUI surfaces compliance state:
- Data classification badges on entity detail pages (from `data_classification` fields)
- Sovereignty constraint indicators on entities with cross-boundary restrictions
- Accreditation status visible in entity overview
- Audit trail always accessible; chain integrity status shown

The GUI cannot be used to bypass policy — every action goes through the Consumer API which applies the full five-check boundary model (doc 26), scoring, Validation Policy, and policy evaluation.

---

## 19. Extensibility

### 17.1 New Resource Types — Zero GUI Code

When a new resource type is registered in DCM:
1. `@dcm/plugin-catalog-backend` detects it via the resource type registry
2. A new Software Template is auto-generated from the field schema
3. A new `DCMService` catalog entity appears in RHDH
4. The template's input form renders from JSON Schema — no UI code needed
5. The resource entity page uses the same Overview/Drift/Audit/Cost/Credentials/Relations tabs — no new tabs needed for standard resource types

Resource type-specific UI extensions are possible via entity page tab contributions if a resource type requires specialized visualization (e.g. a topology view for network types).

### 17.2 Custom Plugin Extensions

Teams can contribute additional entity page tabs, catalog cards, or nav items via standard Backstage plugin extension points. DCM plugin APIs for contributing extensions:

```typescript
// Register a custom entity tab for a specific resource type
dcmPlugin.registerEntityTab({
  resourceType: 'Network.VirtualNetwork',
  component: NetworkTopologyTab,
  title: 'Topology',
  icon: NetworkIcon,
});

// Register a custom catalog card
dcmPlugin.registerCatalogCard({
  component: GPUAvailabilityCard,
  position: 'right',
});
```

### 17.3 Multi-Portal Deployments

Large organizations with multiple RHDH instances (one per business unit) can:
- Point multiple RHDH instances at the same DCM control plane
- Each RHDH instance filters DCM entities to its tenant scope
- DCM federation handles cross-instance resource visibility where permitted

---

## 20. Conformance

A conforming Consumer GUI implementation must:

1. Implement all DCM nav groups: Service Catalog, My Work (Requests/Resources/Groups), Approvals, Governance (Cost & Quota/Contributions), Settings
2. Implement SSE-based live status with constituent tracking (with polling fallback)
3. Enforce tenancy context (`X-DCM-Tenant`) on all API calls
4. Hide (not disable) role-gated navigation items
5. Implement step-up MFA inline for gated operations
6. Surface drift, audit, cost, credentials, and relationships as entity page tabs
7. In RHDH mode: implement all six plugin packages with the specified capabilities
8. Auto-generate Software Templates from DCM catalog item schemas (RHDH mode)

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
