# DCM Red Hat Developer Hub Integration Specification

**Document Status:** 🔄 In Progress
**Document Type:** Specification — RHDH / Backstage Integration Architecture
**Related Documents:** [Consumer GUI Specification](dcm-consumer-gui-spec.md) | [Admin GUI Specification](dcm-admin-gui-spec.md) | [Provider GUI Specification](dcm-provider-gui-spec.md) | [Consumer API Specification](consumer-api-spec.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Standards Catalog](https://github.com/croadfeldt/udlm/blob/main/reference/standards-catalog.md)

> **Status:** Draft — Ready for implementation feedback
>
> This specification defines the complete integration between DCM and Red Hat Developer Hub (RHDH) or upstream Backstage. It covers plugin architecture, entity model, auth delegation, permission mapping, Software Template auto-generation, and deployment.

---

## 1. Integration Architecture Overview

### 1.1 Layering Model

DCM and RHDH are separate systems that integrate at well-defined boundaries. DCM remains authoritative for all infrastructure state; RHDH provides the developer experience layer.

```
┌─────────────────────────────────────────────────────────────────┐
│                     RHDH / Backstage                            │
│   Software Catalog  │  Scaffolder  │  TechDocs  │  Search      │
│   ─────────────────────────────────────────────────────────────│
│   @dcm/plugin suite (Dynamic Plugins)                           │
│   ├── Entity Provider  ← pulls from DCM API                     │
│   ├── Scaffolder Actions  → pushes to DCM API                   │
│   ├── Frontend Plugin  ← reads DCM API via proxy                │
│   ├── Permission Policy  ↔ DCM roles                            │
│   └── Auth Bridge  ↔ DCM Auth Provider (OIDC token exchange)   │
└──────────────────────────────┬──────────────────────────────────┘
                               │ DCM Consumer API (HTTPS)
                               │ X-DCM-Tenant from RHDH group context
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DCM Control Plane                            │
│   Consumer API  │  Policy Engine  │  Scoring  │  Providers     │
│   Stores: Intent, Requested, Realized, Discovered, Audit       │
└─────────────────────────────────────────────────────────────────┘
```

**DCM is authoritative for:** resource state, policy decisions, audit trail, realized data, cost, drift detection.

**RHDH is authoritative for:** developer experience, documentation, search index, Software Templates, organization/group model.

### 1.2 Plugin Packages

The DCM RHDH integration is delivered as six npm packages, all loadable as RHDH Dynamic Plugins:

| Package | Type | Purpose |
|---------|------|---------|
| `@dcm/backstage-plugin` | Frontend | Nav, pages, entity tabs, drawers |
| `@dcm/backstage-plugin-backend` | Backend | API proxy, SSE relay, auth middleware |
| `@dcm/backstage-plugin-catalog-backend` | Backend | Entity provider, catalog processor |
| `@dcm/backstage-plugin-scaffolder-backend` | Backend | Custom scaffolder actions |
| `@dcm/backstage-permission-policy` | Backend | DCM → Backstage permission bridge |
| `@dcm/backstage-plugin-auth-backend` | Backend | RHDH as DCM Auth Provider (optional) |

---

## 2. Authentication and Token Flow

### 2.1 RHDH as DCM Auth Provider

The recommended pattern: configure RHDH (Keycloak/RHSSO) as the Auth Provider for both RHDH and DCM. DCM trusts OIDC tokens issued by the same IdP that RHDH uses.

```
User authenticates → RHDH (via Keycloak/RHSSO OIDC)
  │
  RHDH issues Backstage session token + OIDC access token
  │
  DCM plugin backend receives OIDC access token
  │
  DCM plugin backend presents OIDC token to DCM Consumer API
  (/api/v1/auth/token with grant_type: oidc_token_exchange)
  │
  DCM issues its own session token (JWT with actor_uuid, roles, tenant_scope)
  │
  DCM session token cached in RHDH backend (keyed by Backstage user entity ref)
  │
  All subsequent DCM API calls use DCM session token
```

DCM is registered as an OIDC Auth Provider with the same issuer as RHDH's Keycloak:

```yaml
# DCM Auth Provider registration
auth_provider_registration:
  provider_type: auth_provider
  auth_method: oidc
  oidc_config:
    issuer: https://keycloak.corp.com/realms/corporate
    client_id: dcm-api
    trust_level: authoritative
  role_mapping:
    group_role_map:
      - external_group: dcm-consumers
        dcm_role: consumer
      - external_group: dcm-approvers
        dcm_role: approver
      - external_group: dcm-platform-admins
        dcm_role: platform_admin
```

### 2.2 Token Lifetime and Refresh

- RHDH session: governed by Keycloak session settings (typically PT8H)
- DCM session token: PT30M (prod profile) — refreshed transparently by RHDH backend plugin
- DCM plugin backend maintains a token cache: `backstage_user_ref → dcm_session_token`
- Token refresh: triggered when DCM session token is within PT5M of expiry

### 2.3 Service Account Token for Entity Provider

The `@dcm/backstage-plugin-catalog-backend` entity provider runs as a background service, not on behalf of a user. It uses a DCM service account:

```yaml
# DCM service account for RHDH catalog entity provider
service_account:
  handle: rhdh-catalog-provider
  roles: [catalog_reader]          # read-only: catalog items + realized entities
  credential_type: api_key
  rotation: P30D
```

The service account API key is stored as a Kubernetes Secret and mounted into the RHDH backend pod.

### 2.4 Tenancy from RHDH Group Context

The active RHDH namespace/group context maps to `X-DCM-Tenant`:

```typescript
// In @dcm/backstage-plugin-backend — DCM API proxy middleware
const groupContext = request.headers['x-backstage-namespace'] || 
                     userEntity.spec?.memberOf?.[0];
const tenantUuid = await dcmTenantCache.resolveFromGroup(groupContext);
proxyRequest.headers['X-DCM-Tenant'] = tenantUuid;
```

Tenant UUID resolution: `@dcm/backstage-plugin-catalog-backend` maintains a `RHDH Group ref → DCM Tenant UUID` mapping, populated during entity sync.

---

## 3. Entity Model

### 3.1 Custom Entity Kinds

DCM introduces two custom Backstage entity kinds:

#### DCMService (catalog item)

Represents a DCM service catalog item — something a user can request.

```yaml
apiVersion: dcm.io/v1alpha1
kind: DCMService
metadata:
  name: compute-vm-standard
  namespace: dcm-catalog           # shared namespace for all DCM catalog items
  annotations:
    dcm.io/catalog-item-uuid: "<uuid>"
    dcm.io/resource-type-fqn: "Compute.VirtualMachine"
    backstage.io/techdocs-ref: url:<dcm-layer-store-url>/docs/compute-vm
  tags: [compute, infrastructure, self-service]
spec:
  type: dcm-service
  lifecycle: production
  owner: group:platform-team
  providedBy:
    providerHandle: k8s-operator-prod
    providerType: service_provider
  fieldSchema:
    # JSON Schema for the request form — auto-populated from DCM catalog item
    $ref: "dcm-api://catalog/<uuid>/schema"
  costEstimate:
    currency: USD
    estimatedMonthly: 240
    billingDimensions: [cpu_count, memory_gb]
  availability:
    quotaRemaining: 4              # computed at sync time
    sla: "99.9%"
```

#### DCMResource (realized entity)

Represents a realized DCM resource — something that exists.

```yaml
apiVersion: dcm.io/v1alpha1
kind: DCMResource
metadata:
  name: payments-api-server-01
  namespace: payments-team         # namespace = DCM tenant
  annotations:
    dcm.io/entity-uuid: "<uuid>"
    dcm.io/resource-type-fqn: "Compute.VirtualMachine"
    dcm.io/provider-uuid: "<uuid>"
    dcm.io/request-uuid: "<uuid>"  # the request that created this
    backstage.io/techdocs-ref: url:<provider-docs-url>
spec:
  type: Compute.VirtualMachine
  lifecycle: production
  owner: group:payments-team
  system: payments-platform
  realizedFields:                  # key fields from Realized State
    primary_ip: "10.42.0.105"
    hostname: "payments-api-server-01.corp.internal"
    cpu_count: 4
    memory_gb: 16
    os_family: rhel
  lifecycleState: OPERATIONAL      # DCM lifecycle state
  ttlExpiresAt: "2026-09-15"
  driftStatus: none                # none | minor | moderate | significant | critical
  providerHandle: k8s-operator-prod
  dependsOn:
    - dcmresource:payments-team/payments-db-01
```

### 3.2 Entity Provider

`@dcm/backstage-plugin-catalog-backend` implements a `EntityProvider` that:

1. On startup: fetches all DCM catalog items → emits `DCMService` entities
2. On startup: fetches all realized entities for each tenant → emits `DCMResource` entities
3. On schedule (default: every PT5M): polls for changes, emits delta mutations
4. On `dcm:catalog:refresh` scaffolder action: triggers immediate refresh for specific entity

```typescript
class DcmEntityProvider implements EntityProvider {
  async refresh(logger: Logger): Promise<void> {
    // Fetch catalog items
    const catalogItems = await this.dcmApi.getCatalogItems();
    const serviceEntities = catalogItems.map(toDCMServiceEntity);
    
    // Fetch realized resources per tenant
    const tenants = await this.dcmApi.getTenants(); // admin service account
    const resourceEntities = (await Promise.all(
      tenants.map(t => this.dcmApi.getResources(t.uuid))
    )).flat().map(toDCMResourceEntity);
    
    await this.connection.applyMutation({
      type: 'full',
      entities: [...serviceEntities, ...resourceEntities],
    });
  }
}
```

### 3.3 Catalog Processor

Handles entity validation, relationship resolution, and annotation enrichment for `DCMService` and `DCMResource` kinds.

---

## 4. Software Template Auto-Generation

### 4.1 Generation Model

`@dcm/backstage-plugin-catalog-backend` automatically generates Backstage Software Templates from DCM catalog items. No manual template authoring is needed when new resource types appear.

Generation pipeline:
```
GET /api/v1/catalog → DCM catalog items
  │
  For each catalog item:
  │  GET /api/v1/catalog/{uuid} → field schema
  │
  Transform:
  │  field schema → Backstage template parameters (JSON Schema compatible)
  │  catalog item metadata → template metadata
  │  provider info → template tags
  │
  Emit as Backstage Template entity
```

### 4.2 Schema Transformation Rules

| DCM field type | Backstage ui:widget | Notes |
|---------------|---------------------|-------|
| `enum` list | `select` | Options from DCM enum |
| `string` with pattern | `text` + pattern validation | Pattern in JSON Schema |
| `integer` range | `number` or `select` | Select if < 10 options |
| `boolean` | `checkbox` | — |
| `uuid` reference | `dcm:EntityPicker` | Custom picker component |
| `duration` (ISO 8601) | `dcm:DurationPicker` | Custom picker |
| `datetime` | `datetime` | Standard Backstage widget |
| Injected field (read-only) | `readonly` | Shows source layer in tooltip |

### 4.3 Multi-Step Template Structure

All generated templates follow a consistent multi-step structure:

```
Step 1: "Configure [Service Name]"     ← DCM required fields
Step 2: "Options"                      ← Optional DCM fields + scheduling
Step 3: "Scheduling (Optional)"        ← dispatch: immediate/at/window/recurring
Step 4: "Review"                       ← cost estimate + pre-flight check
  ← Submit ←
Step 5: "Provisioning..."              ← dcm:request:submit + dcm:request:wait (live log)
Step 6: "Complete"                     ← link to entity in catalog + resource URL
```

---

## 5. Scaffolder Actions Reference

All actions in `@dcm/backstage-plugin-scaffolder-backend`:

### `dcm:request:estimate`

```typescript
input:
  catalogItemUuid: string        // DCM catalog item UUID
  fields: object                 // field values from template parameters
  tenantUuid?: string           // defaults to RHDH group context

output:
  estimatedMonthlyCost: number
  currency: string
  breakdown: Array<{dimension: string, cost: number}>
  quotaCheck: {passes: boolean, remaining: number}
  policyPreCheck: {passes: boolean, warnings: string[]}
```

**Purpose:** Called during the Review step. Provides cost estimate, quota check, and policy pre-flight. Does not submit the request.

### `dcm:request:submit`

```typescript
input:
  catalogItemUuid: string
  fields: object
  schedule?: {dispatch: 'immediate'|'at'|'window'|'recurring', notBefore?: string, notAfter?: string, windowId?: string}
  dependsOn?: Array<{requestUuid: string, waitFor: string, injectFields?: ...}>

output:
  requestUuid: string
  entityUuid: string             // UUID the resource will have when realized
  status: string                 // typically ACKNOWLEDGED
  requestUrl: string             // link to request in DCM consumer portal
```

### `dcm:request:wait`

```typescript
input:
  requestUuid: string
  timeoutMinutes?: number        // default: 30
  pollIntervalSeconds?: number   // default: 5; uses SSE if available

output:
  status: 'REALIZED'|'FAILED'|'CANCELLED'
  entityUuid: string
  entityUrl: string              // link to entity in RHDH catalog
  realizedFields: object         // key fields from provider (IP, hostname, etc.)
  failureReason?: string
```

Streams status updates to the Scaffolder log panel:
```
[LOG] 09:01:05  Status: PROVISIONING — Step 3/7: Configuring network interfaces
[LOG] 09:03:12  ✅ REALIZED — IP: 10.42.0.105, Hostname: payments-api-server-01.corp.internal
```

### `dcm:request:group`

```typescript
input:
  groupHandle?: string
  onFailure?: 'cancel_remaining'|'continue'
  timeout?: string               // ISO 8601 duration
  requests: Array<{
    ref: string,                 // local reference within this submission
    catalogItemUuid: string,
    fields: object,
    dependsOn?: Array<{ref: string, waitFor: string, injectFields?: ...}>
  }>

output:
  groupUuid: string
  requests: Array<{ref: string, requestUuid: string, entityUuid: string}>
  groupUrl: string
```

### `dcm:catalog:refresh`

```typescript
input:
  entityUuid: string             // DCM entity UUID to refresh in RHDH catalog

output:
  entityRef: string              // Backstage entity ref: dcmresource:<ns>/<name>
  entityUrl: string              // URL to entity page in RHDH
```

Triggers immediate re-poll of the entity provider for the specified entity. The entity appears in RHDH catalog within PT30S of REALIZED status.

---

## 6. Permission Framework Integration

### 6.1 DCM Permissions in Backstage

`@dcm/backstage-permission-policy` defines DCM permissions in Backstage permission framework terms:

```typescript
// DCM permission definitions
export const dcmPermissions = {
  // Resource permissions
  resourceRead:      createPermission({name: 'dcm.resource.read', attributes: {action: 'read'}}),
  resourceUpdate:    createPermission({name: 'dcm.resource.update', attributes: {action: 'update'}}),
  resourceDelete:    createPermission({name: 'dcm.resource.delete', attributes: {action: 'delete'}}),
  
  // Catalog permissions  
  catalogRequest:    createPermission({name: 'dcm.catalog.request', attributes: {action: 'create'}}),
  
  // Approval permissions
  approvalVote:      createPermission({name: 'dcm.approval.vote', attributes: {action: 'update'}}),
  
  // Admin permissions
  tenantManage:      createPermission({name: 'dcm.tenant.manage', attributes: {action: 'update'}}),
  providerManage:    createPermission({name: 'dcm.provider.manage', attributes: {action: 'update'}}),
};
```

### 6.2 Role Mapping

The permission policy maps Backstage group membership to DCM permission grants:

```typescript
class DcmPermissionPolicy implements PermissionPolicy {
  async handle(request: PolicyQuery, user?: BackstageIdentityResponse) {
    const groups = user?.identity.ownershipEntityRefs ?? [];
    
    // Basic consumer permissions — all authenticated users
    if (isAuthenticated(user)) {
      if (DCM_READ_PERMISSIONS.includes(request.permission.name)) {
        return { result: AuthorizeResult.ALLOW };
      }
    }
    
    // Role-based grants
    if (groups.includes('group:dcm-approvers')) {
      if (request.permission.name === 'dcm.approval.vote') {
        return { result: AuthorizeResult.ALLOW };
      }
    }
    
    if (groups.includes('group:dcm-platform-admins')) {
      return { result: AuthorizeResult.ALLOW }; // all permissions
    }
    
    return { result: AuthorizeResult.DENY };
  }
}
```

### 6.3 RHDH RBAC Plugin Integration

The RHDH RBAC plugin provides a no-code UI for managing role assignments. DCM roles are represented as RHDH group memberships:

```
RHDH RBAC UI:
  Role: dcm-consumers       → Group: all-authenticated-users
  Role: dcm-approvers       → Groups: [payments-leads, platform-approvers]
  Role: dcm-platform-admins → Groups: [platform-team]
  Role: dcm-contributors    → Groups: [policy-authors, power-users]
```

Changes to group membership propagate to DCM via SCIM 2.0 (if configured) or OIDC group claims on next login.

---

## 7. Deployment

### 7.1 Dynamic Plugin Loading

All DCM plugins are deployed as RHDH Dynamic Plugins — no RHDH image rebuild required:

```yaml
# RHDH app-config.yaml additions
dynamicPlugins:
  frontend:
    dcm.backstage-plugin:
      disabled: false
  backend:
    dcm.backstage-plugin-backend:
      disabled: false
    dcm.backstage-plugin-catalog-backend:
      disabled: false
    dcm.backstage-plugin-scaffolder-backend:
      disabled: false
    dcm.backstage-permission-policy:
      disabled: false
```

Plugins loaded from OCI registry or npm. New plugin versions deployed by updating the tag — no RHDH pod rebuild.

### 7.2 RHDH Configuration

```yaml
# app-config.yaml — DCM integration configuration
dcm:
  baseUrl: https://dcm.corp.internal
  apiPath: /api/v1
  
  # Service account for catalog entity provider
  serviceAccount:
    apiKey:
      $env: DCM_SERVICE_ACCOUNT_API_KEY
  
  # Catalog entity sync configuration
  catalog:
    syncIntervalSeconds: 300      # poll DCM API every 5 minutes
    refreshOnScaffolderComplete: true
    entityNamespace: dcm-catalog  # for DCMService entities
  
  # Tenant resolution
  tenancy:
    groupNamespacePrefix: "dcm-tenant-"  # RHDH group dcm-tenant-{uuid} → tenant uuid
    fallbackTenantUuid: null             # null = require explicit group context
  
  # Auth delegation
  auth:
    oidcIssuer: https://keycloak.corp.com/realms/corporate
    clientId: dcm-rhdh-bridge
    clientSecret:
      $env: DCM_OIDC_CLIENT_SECRET

  # Feature flags
  features:
    liveStatusSse: true          # use SSE for request status (fallback to polling if false)
    costEstimateInCatalog: true  # show cost estimate on catalog cards
    quotaCheckOnBrowse: true     # show quota availability in catalog
    autoGenerateTemplates: true  # auto-generate Scaffolder templates from catalog items
```

### 7.3 Kubernetes Deployment Pattern

```yaml
# RHDH configuration in OpenShift/Kubernetes
apiVersion: v1
kind: ConfigMap
metadata:
  name: rhdh-app-config
  namespace: rhdh
data:
  app-config.dcm.yaml: |
    dcm:
      baseUrl: https://dcm-api.dcm-system.svc.cluster.local
      # ... (internal cluster DNS for in-cluster communication)

---
apiVersion: v1
kind: Secret
metadata:
  name: dcm-integration-secrets
  namespace: rhdh
stringData:
  DCM_SERVICE_ACCOUNT_API_KEY: "<api-key>"
  DCM_OIDC_CLIENT_SECRET: "<client-secret>"
```

### 7.4 Zero-Trust in Cluster

RHDH backend → DCM Consumer API communication:
- Both running in same Kubernetes cluster (typically)
- mTLS enforced by Istio service mesh (ICOM model applies to RHDH as a client)
- RHDH is not a DCM internal component — it is an external client that uses the Consumer API
- Auth: OIDC token exchange (Section 2.1) — RHDH backend presents OIDC access token; DCM issues session token

---

## 8. RHDH Pre-Built Capabilities Leveraged

### 8.1 No-Build Integrations (Immediate Value)

These work before writing any DCM-specific code:

| RHDH Feature | DCM Benefit | Config needed |
|-------------|-------------|---------------|
| Keycloak/RHSSO auth | SSO into DCM portal — same login as everything else | Configure OIDC provider |
| RBAC Plugin | No-code role management | Define DCM groups |
| TechDocs | DCM docs rendered in-portal | Add `techdocs-ref` annotations |
| Search | DCM entities searchable | Provided by catalog backend plugin |
| Kubernetes plugin | See DCM pods alongside resources | Standard RHDH Kubernetes plugin config |
| ArgoCD plugin | Layer store GitOps visibility | Standard RHDH ArgoCD plugin config |
| Tekton plugin | DCM scaffolding pipeline visibility | Standard RHDH Tekton plugin config |

### 8.2 Ansible Automation Platform Plugin

RHDH ships an existing AAP (Ansible Automation Platform) plugin. DCM Service Providers that use Ansible Automation Platform can surface AAP job status directly in RHDH:

```
DCMResource entity page
└── Additional tab contributed by AAP plugin:
    "Automation"  ← shows AAP job runs for this resource's provisioning
```

This requires no DCM code — it emerges from RHDH's existing AAP plugin + `dcm.io/aap-job-id` annotation on DCMResource entities.

### 8.3 OCM (Open Cluster Management) Plugin

Organizations using OCM for cluster lifecycle management get cluster management alongside DCM service catalog in the same portal — genuinely one pane of glass for sovereign cloud operations.

---

## 9. Deployment Options

DCM supports two frontend deployment modes that can be selected at initial deployment:

**Standalone SPA** — DCM deploys its own React-based consumer portal. No RHDH dependency. Suitable for environments where RHDH is not present.

**RHDH Mode** — DCM plugins are loaded into an existing RHDH instance. The RHDH Developer Hub becomes the consumer portal surface. Recommended for organizations already running RHDH.

Both modes use the same DCM APIs and the same authentication model. The choice is a deployment configuration, not an architectural difference.

```yaml
# dcm-config.yaml
frontend:
  mode: standalone_spa | rhdh
  rhdh_base_url: https://rhdh.internal  # only required for rhdh mode
```

---
