# DCM Consumer API Specification

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** API Narrative Specification


> **📋 Draft**
>
> This specification covers the full Consumer API surface. Endpoint paths, request/response structures, and authentication flows represent design intent and will be refined as implementation proceeds. Feedback and contributions welcome via [GitHub Issues](https://github.com/dcm-project/issues).

**Version:** 0.1.0-draft
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Specification
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md) | [Four States](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Webhooks and Messaging](../../architecture/runtime-features/webhooks-messaging.md)

---

## Abstract

This specification defines the interface by which consumers interact with the DCM Control Plane. It is the counterpart to the [Operator Interface Specification](dcm-operator-interface-spec.md), which covers what Service Providers implement. This specification covers what consumers call.

The Consumer API is the boundary between the Application domain and the Control Plane. It exposes DCM's service catalog, request submission, resource management, and audit capabilities in a unified interface. All operations are authenticated, authorized against the actor's Tenant scope, and fully audited.

---

> **AEP Alignment:** This specification follows [AEP](https://aep.dev) conventions.
> Custom methods use colon syntax (`POST /resources/{name}:suspend`).
> Async operations return an `Operation` resource (AEP-136 LRO) — poll `operation.name` for completion.
> List pagination uses `page_size` and `page_token` parameters.
> See the normative OpenAPI specification: `schemas/openapi/dcm-consumer-api.yaml`

## 1. Introduction

### 1.1 Scope

This specification covers:
- Authentication and session management
- Service Catalog browsing and discovery
- Resource request submission (all ingress paths)
- Resource lifecycle management (updates, suspension, decommission, rehydration)
- Request and resource status
- Audit trail access

It does not cover:
- Platform administration operations (covered by future Admin API spec)
- Service Provider registration and management (covered by Operator Interface Spec)
- Webhook and Message Bus subscription management (covered by doc 18)

### 1.2 Ingress Surfaces

The Consumer API is accessible via three ingress surfaces. All three are authenticated. All three run the same governance pipeline. The ingress surface affects the review workflow, never governance.

| Surface | Protocol | Review Model | Use Case |
|---------|----------|-------------|----------|
| **REST API** | HTTPS REST | Synchronous acknowledgment; async realization | Programmatic consumers, automation, Terraform providers |
| **Web UI** | Browser | Interactive PR-like review flow | Human consumers, Service Catalog browsing |
| **Git PR Ingress** | Git + webhook | Full GitOps PR workflow | GitOps-native teams, infrastructure-as-code workflows |

This specification primarily documents the REST API surface. The Git PR ingress YAML structure is documented in [Worked Examples](https://github.com/croadfeldt/udlm/blob/main/foundations/examples.md), Section 2.

### 1.3 Base URL and Versioning

```
https://{dcm-instance}/api/v1/
```

All Consumer API endpoints are versioned. Breaking changes increment the major version segment (`v1` → `v2`). Non-breaking additions do not change the version.

> **Full versioning strategy:** See [API Versioning Strategy](../../architecture/control-plane/api-versioning.md) for the complete definition of breaking changes, deprecation timeline, version discovery, sunset behavior, deprecation headers, and VER-001–VER-009 system policies.

**Key rules for Consumer API consumers:**
- Pin to a specific version (`/api/v1/`) in production — do not use the `/api/latest/` alias
- When a version is deprecated, responses include `Deprecation` and `Sunset` headers (RFC 8594/RFC 9745)
- Deprecated versions remain functional until the sunset date — bugs fixed, features not backported
- Version discovery: `GET /.well-known/dcm-api-versions`
- Migration guide: `GET /api/v{N}/migration-guide`

**What is a breaking change in the Consumer API:**
Removing a field, changing a field type, removing an endpoint, changing HTTP status semantics, tightening validation, changing URL structure. New optional fields, new endpoints, and expanded enums are not breaking.

**Support windows (profile-governed):**
- `minimal`: 90 days notice, 180 days deprecated support
- `standard`: 180 days notice, 365 days deprecated support
- `prod`: 365 days notice, 730 days (2 years) deprecated support
- `fsi`: 18 months notice, 3 years deprecated support
- `sovereign`: 2 years notice, 4 years deprecated support

### 1.4 Content Type

All requests and responses use `application/json`. The DCM Unified Data Model is expressed as JSON throughout the Consumer API.

### 1.5 Idempotency

DCM's request model provides built-in idempotency for `POST /api/v1/requests`. Each request submission produces an `entity_uuid` at Intent State creation. If a client retries a request submission (e.g. after a network timeout), it may receive a duplicate Intent State — but DCM's deduplication layer detects identical payloads from the same actor within a 5-minute window and returns the existing request record rather than creating a second one.

For operations where explicit idempotency control is needed, clients may supply an `Idempotency-Key` header:

```http
POST /api/v1/requests
Idempotency-Key: <client-generated-uuid>
```

If DCM receives two requests with the same `Idempotency-Key` from the same authenticated actor within PT24H, the second request returns the response from the first. The idempotency key is stored for PT24H then discarded.

**Which endpoints support `Idempotency-Key`:**
- `POST /api/v1/requests` — resource request submission
- `POST /api/v1/credentials/{uuid}:rotate` — credential rotation request
- `POST /api/v1/resources/{uuid}:rehydrate` — rehydration trigger

### 1.6 Rate Limiting

Rate limits are profile-governed and apply per authenticated actor:

| Profile | Requests/minute | Burst allowance | Rate page_size header |
|---------|----------------|-----------------|-------------------|
| `minimal` | 60 | 20 | Yes |
| `standard` | 300 | 100 | Yes |
| `prod` | 600 | 200 | Yes |
| `fsi` | 600 | 200 | Yes |
| `sovereign` | 600 | 200 | Yes |

When rate limited, DCM returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 12
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1749340800

{
  "error": "rate_limit_exceeded",
  "message": "Request rate page_size exceeded. Retry after 12 seconds.",
  "retry_after_seconds": 12
}
```

### 1.7 Request and Correlation IDs

Every DCM API response includes:

```http
X-DCM-Request-ID: <uuid>       # unique ID for this HTTP request; use for support
X-DCM-Correlation-ID: <uuid>   # links related requests across the pipeline
```

Include `X-DCM-Request-ID` when contacting support. Use `X-DCM-Correlation-ID` to trace a request through the audit trail (`GET /api/v1/audit/correlation/{correlation_id}`).

---

### 1.8 Standard Response Envelopes

**List responses** always use this envelope:
```json
{
  "items": [...],           // always "items" regardless of resource type
  "total": 142,             // total matching records (before pagination)
  "page_size": 25,
  "next_page_token": "<string>" // null if no more pages; use as ?page_token= on next request
}
```

**Single resource responses** return the resource object directly (no wrapper).

**Error responses** always use:
```json
{
  "error": "<error_code>",    // machine-readable snake_case code
  "message": "<string>",      // human-readable description
  "request_id": "<uuid>",     // matches X-DCM-Request-ID header
  "details": {}               // optional: field-level validation errors etc.
}
```

## 2. Authentication

### 2.1 Token Acquisition

Consumers obtain a session token from the Auth Provider. The token acquisition method depends on the configured Auth Provider:

```
POST /api/v1/auth/token

# OIDC flow (most common):
{
  "grant_type": "authorization_code",
  "code": "<oidc-authorization-code>",
  "redirect_uri": "<registered-redirect-uri>"
}

# API key flow (service accounts):
{
  "grant_type": "api_key",
  "api_key": "<api-key-value>"
}

# Response:
{
  "token": "<session-token>",
  "token_type": "Bearer",
  "expires_at": "<ISO 8601>",
  "actor_uuid": "<uuid>",
  "mfa_verified": true,
  "scopes": ["read:catalog", "request:compute", "manage:owned"]
}
```

### 2.2 Request Authentication

All requests carry the session token as a Bearer token:

```
Authorization: Bearer <session-token>
```

### 2.3 Tenant Context

Actors may have access to multiple Tenants. The Tenant context for a request is declared in the header:

```
X-DCM-Tenant: <tenant-uuid>
```

If omitted and the actor has access to exactly one Tenant, that Tenant is used. If the actor has access to multiple Tenants and no Tenant header is provided, the request is rejected with `400 Bad Request` — Tenant ambiguity is never resolved silently.

### 2.4 Step-Up MFA

Some operations require step-up MFA regardless of session MFA status. When a step-up challenge is required, the API returns `403 Forbidden` with a challenge token:

```json
{
  "error": "step_up_required",
  "challenge_token": "<uuid>",
  "challenge_expires_at": "<ISO 8601>",
  "allowed_methods": ["totp", "push_notification"]
}
```

The consumer completes the MFA challenge and retries the request with the completed challenge token:

```
X-DCM-StepUp-Token: <completed-challenge-token>
```

---

### 2.5 Session Management

DCM issues a session token on successful authentication. Sessions can be managed and revoked by the authenticated actor.

```http
# Log out current session
DELETE /api/v1/auth/session
Authorization: Bearer <token>

Response 204 No Content
```

```http
# Log out all sessions for this actor
DELETE /api/v1/auth/sessions
Authorization: Bearer <token>

Response 204 No Content
```

```http
# List active sessions for this actor
GET /api/v1/auth/sessions
Authorization: Bearer <token>

Response 200:
{
  "items": [
    {
      "session_uuid": "<uuid>",
      "created_at": "<ISO 8601>",
      "expires_at": "<ISO 8601>",
      "auth_method": "oidc",
      "mfa_verified": true,
      "last_active_at": "<ISO 8601>",
      "is_current": true
    }
  ],
  "total": 2
}
```

```http
# Revoke a specific session
DELETE /api/v1/auth/sessions/{session_uuid}
Authorization: Bearer <token>

Response 204 No Content
```

```http
# Token introspection (RFC 7662) — for internal components and trusted integrations
POST /api/v1/auth:introspect
Authorization: Bearer <service-token>

{ "token": "<token-to-inspect>" }

Response 200:
{
  "active": true,
  "session_uuid": "<uuid>",
  "actor_uuid": "<uuid>",
  "tenant_uuid": "<uuid>",
  "expires_at": "<ISO 8601>",
  "mfa_verified": true,
  "auth_method": "oidc"
}
```

> **Session revocation model:** See [Session Token Revocation](../../architecture/control-plane/session-revocation.md) for the complete session lifecycle, revocation triggers, revocation registry, profile-governed TTLs, and AUTH-016–AUTH-022 system policies.


## 3. Service Catalog

### 3.1 List Catalog Items

Returns catalog items available to the authenticated actor in their Tenant, filtered by RBAC.

```
GET /api/v1/catalog

Query parameters:
  category=<resource-type-category>    e.g., Compute, Network, Storage
  search=<string>                      full-text search across name and description
  tag=<string>                         filter by tag (repeatable)
  page=<int>                           pagination (default: 1)
  page_size=<int>                      results per page (default: 25, max: 100)

Response 200:
{
  "catalog_items": [
    {
      "catalog_item_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "provider_uuid": "<uuid>",
      "display_name": "Standard Linux VM",
      "description": "General-purpose virtual machine with standard OS images",
      "tier": 1,
      "portability_class": "portable",
      "estimated_cost": {
        "unit": "per-hour",
        "amount": 0.32,
        "currency": "USD",
        "cost_confidence": "high"
      },
      "tags": ["compute", "linux", "general-purpose"],
      "deprecated": false
    }
  ],
  "total": 47,
  "page": 1,
  "page_size": 25
}
```

### 3.2 Describe Catalog Item

Returns the full schema for a catalog item — all fields, constraints, editability declarations, dependencies, and cost estimate.

```
GET /api/v1/catalog/{catalog_item_uuid}

Response 200:
{
  "catalog_item_uuid": "<uuid>",
  "resource_type": "Compute.VirtualMachine",
  "resource_type_spec_version": "2.1.0",
  "display_name": "Standard Linux VM",

  "schema": {
    "fields": [

      // ── Static constraint fields ───────────────────────────────────────────
      {
        "field_name": "cpu_count",
        "display_name": "CPU Cores",
        "type": "integer",
        "required": true,
        "editable_post_realization": false,
        "constraint": {
          "visibility": "full",
          "type": "enum",
          "allowed_values": [1, 2, 4, 8, 16, 32],
          "default": 4,
          "reason": "CPU counts must be powers of 2 for NUMA alignment"
        }
      },

      // ── Layer-referenced field: OS image ───────────────────────────────────
      // Allowed values come from active os_image Reference Data Layers.
      // Each entry carries the full structured layer data the GUI needs.
      // Consumer submits the layer UUID; DCM injects all image metadata into payload.
      {
        "field_name": "os_image",
        "display_name": "Operating System Image",
        "type": "string",
        "required": true,
        "editable_post_realization": false,
        "constraint": {
          "visibility": "full",
          "type": "layer_reference",
          "layer_type": "os_image",
          "allowed_values": [
            {
              "value": "layer-uuid-rhel-9-4",
              "display_name": "RHEL 9.4",
              "os_family": "rhel",
              "version": "9.4",
              "fips_compliant": true,
              "eol_date": "2032-05-31",
              "approved_for_classifications": ["public","internal","confidential","restricted"]
            },
            {
              "value": "layer-uuid-ubuntu-24-04",
              "display_name": "Ubuntu 24.04 LTS",
              "os_family": "ubuntu",
              "version": "24.04",
              "fips_compliant": false,
              "eol_date": "2029-04-30",
              "approved_for_classifications": ["public","internal"]
            }
          ]
        }
      },

      // ── Layer-referenced field: location ───────────────────────────────────
      // Allowed values come from active location.data_center layers the
      // consumer is entitled to and that this catalog item is eligible for.
      // Selecting a location causes the full location layer chain
      // (Country → Region → Zone → Site → DC) to assemble into the payload.
      {
        "field_name": "location",
        "display_name": "Allocation Location",
        "type": "string",
        "required": true,
        "editable_post_realization": false,
        "constraint": {
          "visibility": "full",
          "type": "layer_reference",
          "layer_type": "location.data_center",
          "allowed_values": [
            {
              "value": "layer-uuid-fra-dc1",
              "display_name": "DC1 — Frankfurt Alpha",
              "code": "FRA-DC1",
              "zone": "eu-west-1a",
              "region": "EU West",
              "sovereignty": "EU/GDPR",
              "certifications": ["ISO 27001", "SOC 2 Type II"],
              "max_data_classification": "restricted",
              "capacity_status": "available"
            },
            {
              "value": "layer-uuid-ams-dc2",
              "display_name": "DC2 — Amsterdam Beta",
              "code": "AMS-DC2",
              "zone": "eu-west-1b",
              "region": "EU West",
              "sovereignty": "EU/GDPR",
              "certifications": ["ISO 27001"],
              "max_data_classification": "confidential",
              "capacity_status": "limited"
            }
          ]
        }
      },

      // ── Layer-referenced field: approved_size ──────────────────────────────
      // Allowed values come from active vm_size Reference Data Layers.
      // Selecting a size injects CPU, RAM, and storage defaults into the payload
      // (which the consumer can override within the size's declared constraints).
      {
        "field_name": "size",
        "display_name": "VM Size",
        "type": "string",
        "required": false,
        "editable_post_realization": false,
        "constraint": {
          "visibility": "full",
          "type": "layer_reference",
          "layer_type": "vm_size",
          "allowed_values": [
            {
              "value": "layer-uuid-small",
              "display_name": "Small (2 CPU / 8 GB)",
              "cpu_count": 2, "memory_gb": 8, "storage_gb": 40
            },
            {
              "value": "layer-uuid-medium",
              "display_name": "Medium (8 CPU / 32 GB)",
              "cpu_count": 8, "memory_gb": 32, "storage_gb": 80
            },
            {
              "value": "layer-uuid-large",
              "display_name": "Large (16 CPU / 64 GB)",
              "cpu_count": 16, "memory_gb": 64, "storage_gb": 160
            }
          ]
        }
      },

      // ── Policy-injected hidden field ───────────────────────────────────────
      {
        "field_name": "monitoring_agent",
        "type": "string",
        "required": false,
        "editable_post_realization": false,
        "constraint": {
          "visibility": "hidden",
          "override": "immutable",
          "note": "Injected by policy — consumer cannot set or view"
        }
      }

    ]
  },

  "dependencies": [
    {
      "resource_type": "Network.IPAddress",
      "relationship": "requires",
      "fulfillment": "automatic",          # DCM auto-allocates; consumer does not need to request separately
      "count": 1
    }
  ],

  "estimated_cost": {
    "breakdown": [
      { "component": "compute", "unit": "per-hour", "amount": 0.28, "currency": "USD" },
      { "component": "ip-allocation", "unit": "per-hour", "amount": 0.04, "currency": "USD" }
    ],
    "total_per_hour": 0.32,
    "currency": "USD"
  },

  "sovereignty": {
    "available_in_regions": ["EU-WEST", "EU-NORTH"],
    "data_residency_guarantee": "EU"
  },
  "accreditations": [
    {
      "framework": "hipaa",
      "accreditation_type": "baa",
      "status": "active",
      "expires_at": "<ISO 8601>",
      "max_data_classification": "phi"
    }
  ],
  "zero_trust_posture": "full",
  "max_data_classification_accepted": "phi"
}
```

### 3.3 Catalog Search

```
GET /api/v1/catalog/search?q=<query>

Returns catalog items matching the query across name, description, resource type, and tags.
Same response shape as List Catalog Items.
```

---

## 4. Request Submission and Lifecycle

### 4.1 Submit Resource Request

Submits a new resource request. Returns immediately with an acknowledgment — realization is asynchronous.

```
POST /api/v1/requests

Request body:
{
  "catalog_item_uuid": "<uuid>",
  "fields": {
    "cpu_count": 4,
    "memory_gb": 8,
    "storage_gb": 100,
    "os_family": "rhel",
    "name": "payments-api-server-01"
  },
  "options": {
    "auto_approve": true,              # request auto-approval if policy permits
    "notify_on_completion": true,
    "notification_endpoint": "https://my-system.example.com/dcm/webhook"
  }
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",            # the UUID the entity will have when realized
  "status": "ACKNOWLEDGED",
  "intent_state_ref": "<uuid>",
  "estimated_completion": "<ISO 8601>",
  "status_url": "/api/v1/requests/{request_uuid}/status",
  "dry_run_result": null,             # null if auto-approve; populated if review required
  "risk_score": 47,                   # aggregate request risk score (0–100)
  "routing_decision": "reviewed", # auto_approved | pending_review | pending_verified | pending_authorized
  "score_drivers": [                  # top 3 contributing factors (human-readable)
    "Estimated monthly cost exceeds Tenant ceiling",
    "Request submitted outside business hours",
    "Actor has 2 recent validation failures"
  ],
  "advisory_warnings": [              # from advisory-class Validation policies
    {
      "warning_code": "recommended_field_absent",
      "warning_message": "cost_center not provided — cost attribution will use Tenant default",
      "field": "fields.cost_center"
    }
  ]
}

Response 200 OK (if policy requires pre-validation report before submission):
{
  "dry_run": true,
  "validation_result": {
    "policies_evaluated": [...],
    "gatekeeper_decisions": [{ "policy": "vm-size-limits", "result": "approved" }],
    "estimated_cost": {...},
    "sovereignty_check": { "satisfied": true, "constraints": ["data_residency: EU"] },
    "would_auto_approve": true
  }
}
```

### 4.2 Request Status

```
GET /api/v1/requests/{request_uuid}/status

Response 200:
{
  "request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "PROVISIONING",
  "status_history": [
    { "status": "ACKNOWLEDGED", "at": "2026-03-15T09:00:00Z" },
    { "status": "ASSEMBLING",   "at": "2026-03-15T09:00:02Z" },
    { "status": "DISPATCHED",   "at": "2026-03-15T09:00:47Z" },
    { "status": "PROVISIONING", "at": "2026-03-15T09:01:05Z" }
  ],
  "current_step": "Provider is provisioning the resource",
  "estimated_completion": "2026-03-15T09:05:00Z"
}

# Terminal status response:
{
  "request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "COMPLETED",
  "completed_at": "2026-03-15T09:03:12Z",
  "resource_url": "/api/v1/resources/{entity_uuid}"
}

# Failed request:
{
  "request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "FAILED",
  "failed_at": "2026-03-15T09:02:45Z",
  "failure_reason": "Provider capacity exhausted — all eligible providers at capacity",
  "retry_eligible": true,
  "retry_after": "PT15M"
}
```

### 4.3 Live Request Status Stream (Server-Sent Events)

For consumers that want live status updates without polling, DCM exposes a Server-Sent Events (SSE) stream per request:

```
GET /api/v1/requests/{request_uuid}/stream
Accept: text/event-stream
Authorization: Bearer <token>

# Response: HTTP 200, Content-Type: text/event-stream
# Connection stays open; events pushed as state changes

event: status_change
data: {"status":"PROVISIONING","at":"2026-04-01T02:00:05Z","current_step":"Configuring network interfaces"}

event: progress_updated
data: {"step_current":3,"step_total":7,"step_label":"Configuring network interfaces","constituent_status":[{"ref":"vm","status":"REALIZED"},{"ref":"dns","status":"PROVISIONING"}]}

event: status_change
data: {"status":"COMPLETED","at":"2026-04-01T02:03:12Z"}

# Stream closes on terminal status (COMPLETED, FAILED, CANCELLED)
```

**SSE events on this stream:**

| Event name | When | Data fields |
|------------|------|-------------|
| `status_change` | Request status changes | status, at, current_step |
| `progress_updated` | Provider sends interim progress | step_current, step_total, step_label, constituent_status |
| `approval_required` | Request routed to approval tier | approval_uuid, required_tier, window_expires_at |
| `approval_recorded` | A reviewer votes | votes_recorded, quorum_required, quorum_reached |
| `heartbeat` | Every 30s (keep-alive) | ts |

**Constituent status** (for compound/composite service definition requests):
```json
{
  "constituent_status": [
    { "ref": "vm",      "status": "REALIZED",     "entity_uuid": "<uuid>" },
    { "ref": "ip",      "status": "REALIZED",     "entity_uuid": "<uuid>" },
    { "ref": "dns",     "status": "PROVISIONING", "entity_uuid": null },
    { "ref": "storage", "status": "PENDING",      "entity_uuid": null }
  ]
}
```

**Fallback:** Consumers that cannot use SSE (e.g. some proxy configurations) should use polling via `GET /api/v1/requests/{uuid}/status` with an appropriate interval.

**Connection limits:** One SSE stream per request_uuid per actor. Opening a second stream closes the first.


### 4.4 Consumer Request Status Lifecycle

```
ACKNOWLEDGED            → request received; intent created
ASSEMBLING              → Request Payload Processor running layer assembly
AWAITING_APPROVAL       → policy requires human review before dispatch
APPROVED                → proceeding to assembly and dispatch
DISPATCHED              → provider received payload; awaiting confirmation
PROVISIONING            → provider executing
COMPLETED               → provider confirmed realization; Realized State written
FAILED                  → terminal; failure_reason and retry_eligible populated
CANCELLED               → consumer-initiated cancellation; clean terminal
CANCELLING              → cancellation in progress; provider notified
TIMEOUT_PENDING         → dispatch timeout fired; recovery policy evaluating
LATE_REALIZATION_PENDING → provider responded after timeout; recovery decision pending
INDETERMINATE_REALIZATION → state ambiguous; drift detection resolving
COMPENSATION_IN_PROGRESS → composite service rollback underway
COMPENSATION_FAILED     → rollback failed; platform admin notified; orphan detection active
PENDING_REVIEW          → conflict detected requiring human resolution
```

### 4.5 Cancel Request

Cancellation is only available before the PROVISIONING state. Once a provider is executing, cancellation moves to CANCELLING and depends on provider support.

```
DELETE /api/v1/requests/{request_uuid}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "request_uuid": "<uuid>",
  "status": "CANCELLING",
  "message": "Cancellation requested. Provider will be notified if dispatch has occurred."
}

Response 409 Conflict (if cancellation not possible):
{
  "error": "cancellation_not_available",
  "reason": "Resource is in PROVISIONING state. Cancellation requires provider support.",
  "provider_supports_cancellation": false
}
```

---

### 4.5 Request Groups (Dependency Graph)

Consumers can declare an ordered dependency graph across independent requests using request groups. DCM dispatches constituent requests in dependency order.

```http
# Create a request group
POST /api/v1/request-groups
Authorization: Bearer <token>

{
  "label": "provision-web-stack",
  "requests": [
    { "request_uuid": "<db-request-uuid>", "depends_on": [] },
    { "request_uuid": "<app-request-uuid>", "depends_on": ["<db-request-uuid>"] },
    { "request_uuid": "<lb-request-uuid>", "depends_on": ["<app-request-uuid>"] }
  ]
}

Response 201:
{
  "request_group_uuid": "<uuid>",
  "label": "provision-web-stack",
  "status": "pending",
  "requests": [...]
}
```

```http
# Get request group status
GET /api/v1/request-groups/{group_uuid}
Authorization: Bearer <token>

Response 200:
{
  "request_group_uuid": "<uuid>",
  "status": "in_progress",
  "requests": [
    { "request_uuid": "<uuid>", "status": "realized", "dispatched_at": "..." },
    { "request_uuid": "<uuid>", "status": "dispatched", "dispatched_at": "..." },
    { "request_uuid": "<uuid>", "status": "pending_dependency", "blocked_by": ["<uuid>"] }
  ]
}
```

> **Request dependency graph model:** See [Request Dependency Graph](https://github.com/croadfeldt/udlm/blob/main/lifecycle/request-dependency-graph.md) for cycle detection, partial failure handling, and RDG-001–RDG-006 system policies.


## 5. Resource Management

### 5.1 List Owned Resources

```
GET /api/v1/resources

Query parameters:
  resource_type=<fqn>
  lifecycle_state=<state>
  drift_status=<clean|drifted|unknown>
  tag=<string>
  page=<int>
  page_size=<int>

Response 200:
{
  "resources": [
    {
      "entity_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "display_name": "payments-api-server-01",
      "lifecycle_state": "OPERATIONAL",
      "drift_status": "clean",
      "owned_by_tenant_uuid": "<uuid>",
      "created_at": "<ISO 8601>",
      "provider_uuid": "<uuid>",
      "estimated_cost_per_hour": 0.32
    }
  ],
  "total": 12
}
```

### 5.2 Describe Resource

```
GET /api/v1/resources/{entity_uuid}

Response 200:
{
  "entity_uuid": "<uuid>",
  "resource_type": "Compute.VirtualMachine",
  "lifecycle_state": "OPERATIONAL",
  "drift_status": "clean",
  "last_discovered_at": "<ISO 8601>",

  "fields": {
    "cpu_count": {
      "value": 4,
      "confidence": { "band": "very_high", "score": 98 },
      "editable": false
    },
    "memory_gb": {
      "value": 8,
      "confidence": { "band": "very_high", "score": 98 },
      "editable": false
    }
  },

  "relationships": [
    {
      "type": "attached_to",
      "related_entity_uuid": "<vlan-uuid>",
      "related_entity_type": "Network.VLAN",
      "stake_strength": "required"
    }
  ],

  "cost": {
    "current_billing_state": "billable",
    "estimated_cost_per_hour": 0.32,
    "currency": "USD"
  },

  "rehydration_constraints": {
    "min_auth_level": "oidc_mfa"
  },

  "data_classification_summary": {
    "fields_with_phi": 0,
    "fields_with_restricted": 2,
    "highest_classification": "restricted"
  },

  "pending_provider_notifications": [
    {
      "notification_uuid": "<uuid>",
      "notification_type": "auto_scale",
      "submitted_at": "<ISO 8601>",
      "status": "pending_approval",
      "changed_fields": ["memory_gb"],
      "approval_url": "/api/v1/resources/{entity_uuid}/provider-notifications/{notification_uuid}:approve"
    }
  ]
}
```

### 5.3 Update Editable Fields (Targeted Delta)

Updates one or more editable fields on a realized resource. Does not re-run layer assembly — only the declared changes are dispatched to the provider.

```
PATCH /api/v1/resources/{entity_uuid}

Request body:
{
  "updates": {
    "name": "payments-api-server-01-renamed"
  },
  "reason": "Renamed to align with new naming convention"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "update_request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "DISPATCHED",
  "fields_updated": ["name"],
  "status_url": "/api/v1/requests/{update_request_uuid}/status"
}

Response 422 Unprocessable (if field is not editable):
{
  "error": "field_not_editable",
  "field": "cpu_count",
  "reason": "cpu_count is not declared as editable post-realization for this resource type"
}
```

### 5.4 Suspend Resource

```
POST /api/v1/resources/{entity_uuid}:suspend

Request body:
{
  "reason": "Taking offline for maintenance window",
  "auto_resume_at": "2026-03-16T06:00:00Z"    # optional
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "entity_uuid": "<uuid>",
  "status": "SUSPENDING",
  "auto_resume_at": "2026-03-16T06:00:00Z"
}
```

### 5.5 Decommission Resource

```
DELETE /api/v1/resources/{entity_uuid}

Request body:
{
  "reason": "Project completed — resource no longer needed",
  "force": false    # true to force even if non-required stakes/relationships exist
                    # cannot force decommission if required stakes exist
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "entity_uuid": "<uuid>",
  "status": "DECOMMISSIONING"
}

Response 409 Conflict (required stakes or dependencies active):
{
  "error": "decommission_deferred",
  "reason": "Resource has active required stake relationships",
  "active_required_stakes": [
    {
      "stakeholder_entity_uuid": "<uuid>",
      "stakeholder_resource_type": "Compute.VirtualMachine",
      "stake_strength": "required"
    }
  ],
  "resolution": "Release all required stakes before decommissioning, or request stakeholders to migrate"
}
```

### 5.6 Trigger Rehydration

```
POST /api/v1/resources/{entity_uuid}:rehydrate

Request body:
{
  "source": "realized",              # intent | requested | realized
  "placement": {
    "re_evaluate": false
  },
  "governance": {
    "policy_version": "current"
  },
  "reason": "Provider migration — EU-WEST-Prod-1 being decommissioned"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "rehydration_request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "ACKNOWLEDGED",
  "lease_uuid": "<uuid>",
  "status_url": "/api/v1/requests/{rehydration_request_uuid}/status"
}

Response 409 Conflict (rehydration lease already held):
{
  "error": "rehydration_lease_held",
  "lease_held_since": "<ISO 8601>",
  "lease_expires_at": "<ISO 8601>",
  "retry_after": "PT2H"
}

Response 403 Forbidden (step-up MFA required):
{
  "error": "step_up_required",
  "reason": "Entity min_auth_level requires hardware_token_mfa for rehydration"
}
```

---


### 5.7 Provider Update Notification Approval

When a provider submits an update notification that requires consumer approval, the consumer receives a notification and the resource enters `PENDING_REVIEW` state. The consumer approves or rejects via this endpoint.

```
GET /api/v1/resources/{entity_uuid}/provider-notifications

Response 200:
{
  "notifications": [
    {
      "notification_uuid": "<uuid>",
      "notification_type": "auto_scale",
      "provider_uuid": "<uuid>",
      "submitted_at": "<ISO 8601>",
      "status": "pending_approval",
      "change_summary": "Provider reports memory_gb increased from 8 to 16",
      "change_reason": "Auto-scale policy triggered at 85% memory utilization",
      "changed_fields": {
        "memory_gb": { "previous_value": 8, "new_value": 16 }
      }
    }
  ]
}

POST /api/v1/resources/{entity_uuid}/provider-notifications/{notification_uuid}:approve
{
  "decision": "approve | reject",
  "reason": "<optional human-readable reason>"
}

Response 202 Accepted:
{
  "notification_uuid": "<uuid>",
  "decision": "approve",
  "processed_at": "<ISO 8601>",
  "realized_state_uuid": "<uuid | null>"
}
```

**On approval:** A new Requested State record is created (`source_type: provider_update`, actor: consumer approver). A new Realized State snapshot is written. The entity exits PENDING_REVIEW.

**On rejection:** The notification is rejected. The discrepancy between provider state and DCM Realized State becomes a drift event. The entity exits PENDING_REVIEW with an active drift record.



### 5.8 Recovery Decisions

When a recovery policy fires `NOTIFY_AND_WAIT`, the entity owner can query and respond to the pending decision.

```
GET /api/v1/resources/{entity_uuid}/recovery-decisions

Response 200:
{
  "recovery_decision_uuid": "<uuid>",
  "trigger": "DISPATCH_TIMEOUT",
  "entity_uuid": "<uuid>",
  "entity_state": "TIMEOUT_PENDING",
  "deadline": "<ISO 8601>",
  "deadline_action": "ESCALATE",
  "context": {
    "timeout_fired_at": "<ISO 8601>",
    "cancellation_sent": true,
    "cancellation_status": "unknown"
  },
  "available_actions": [
    {
      "action": "DRIFT_RECONCILE",
      "description": "Let discovery determine actual state and reconcile automatically"
    },
    {
      "action": "DISCARD_AND_REQUEUE",
      "description": "Best-effort cleanup; new request cycle created immediately"
    },
    {
      "action": "DISCARD_NO_REQUEUE",
      "description": "Best-effort cleanup only; no automatic requeue"
    }
  ]
}

POST /api/v1/resources/{entity_uuid}/recovery-decisions/{recovery_decision_uuid}
{
  "action": "DISCARD_AND_REQUEUE",
  "reason": "Provider was known degraded; clean restart preferred"
}

Response 202 Accepted:
{
  "recovery_decision_uuid": "<uuid>",
  "action_taken": "DISCARD_AND_REQUEUE",
  "new_request_uuid": "<uuid>"    # the new request cycle UUID
}
```

**Note:** Recovery decisions are only available when the active recovery profile includes `NOTIFY_AND_WAIT`. With other profiles (automated-reconciliation, discard-and-requeue) the system acts automatically and no decision endpoint is exposed.




### 5.13 Bulk Decommission

Decommissions all resources matching a filter. Creates individual decommission requests for each resource. Useful for teardown of environments or project cleanup.

```
POST /api/v1/resources:bulk-decommission

Request body:
{
  "filter": {
    "group_uuid": "<uuid>",           # all resources in a group
    "tag": "environment:dev",         # all resources with a tag
    "resource_type": "Compute.VirtualMachine"   # combined with other filters
  },
  "reason": "Dev environment teardown — project complete",
  "dry_run": true,                    # true: return what would be decommissioned; no action taken
  "force": false
}

Response 200 (dry_run=true):
{
  "dry_run": true,
  "would_decommission": [
    { "entity_uuid": "<uuid>", "display_name": "dev-vm-01", "resource_type": "Compute.VirtualMachine" },
    { "entity_uuid": "<uuid>", "display_name": "dev-vm-02", "resource_type": "Compute.VirtualMachine" }
  ],
  "blocked": [
    {
      "entity_uuid": "<uuid>",
      "display_name": "shared-vlan-01",
      "reason": "Active required stakes from resources outside the decommission set"
    }
  ]
}

Response 200 OK — returns `Operation` (dry_run=false):
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "bulk_decommission_uuid": "<uuid>",
  "decommission_requests": [
    { "entity_uuid": "<uuid>", "request_uuid": "<uuid>" },
    { "entity_uuid": "<uuid>", "request_uuid": "<uuid>" }
  ],
  "blocked_count": 1
}
```


### 5.9 Resume Resource

Resumes a suspended resource. The resource must be in SUSPENDED lifecycle state.

```
POST /api/v1/resources/{entity_uuid}:resume

Request body:
{
  "reason": "Maintenance window complete"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "entity_uuid": "<uuid>",
  "status": "RESUMING"
}

Response 409 Conflict:
{
  "error": "not_suspended",
  "reason": "Resource is not in SUSPENDED state",
  "current_state": "OPERATIONAL"
}
```

---

### 5.10 Ownership Transfer

Transfers ownership of a resource entity to a different Tenant. Both Tenants must have an active cross-tenant authorization record permitting the transfer. The receiving Tenant admin must confirm the transfer.

```
POST /api/v1/resources/{entity_uuid}:transfer

Request body:
{
  "target_tenant_uuid": "<uuid>",
  "reason": "Project moving from Dev to Production Tenant",
  "notify_target_tenant_admin": true
}

Response 202 Accepted:
{
  "transfer_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "from_tenant_uuid": "<uuid>",
  "to_tenant_uuid": "<uuid>",
  "status": "PENDING_TARGET_ACCEPTANCE",
  "expires_at": "<ISO 8601>"    # transfer offer expires after PT72H
}

Response 403 Forbidden:
{
  "error": "transfer_not_authorized",
  "reason": "No cross-tenant authorization record between source and target Tenant"
}
```

Target Tenant admin accepts or rejects:

```
POST /api/v1/resources/transfers/{transfer_uuid}:accept
POST /api/v1/resources/transfers/{transfer_uuid}:reject
{
  "reason": "<optional>"
}
```

---

### 5.11 Extend Resource TTL

Extends the TTL of a resource entity that has a lifecycle time constraint declared. Extension is subject to policy — a GateKeeper may reject or cap the extension.

```
POST /api/v1/resources/{entity_uuid}:extend-ttl

Request body:
{
  "extend_by": "P30D",           # ISO 8601 duration
  "reason": "Project deadline extended by one month"
}

Response 200:
{
  "entity_uuid": "<uuid>",
  "previous_expiry": "<ISO 8601>",
  "new_expiry": "<ISO 8601>",
  "extension_granted": "P30D"
}

Response 422 Unprocessable:
{
  "error": "ttl_extension_rejected",
  "reason": "Policy limits maximum TTL extension to P14D for this resource type",
  "max_extension": "P14D",
  "policy_uuid": "<uuid>"
}

Response 404 Not Found:
{
  "error": "no_ttl_constraint",
  "reason": "Resource has no declared lifecycle time constraint"
}
```

---

### 5.12 List Expiring Resources

Returns resources approaching their TTL expiry, sorted by time remaining.

```
GET /api/v1/resources/expiring

Query parameters:
  within=<ISO 8601 duration>    resources expiring within this duration (default: P7D)
  resource_type=<fqn>
  page=<int>
  page_size=<int>

Response 200:
{
  "expiring_resources": [
    {
      "entity_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "display_name": "lab-server-01",
      "expires_at": "<ISO 8601>",
      "time_remaining": "P2DT4H",
      "on_expiry_action": "decommission",
      "extend_url": "/api/v1/resources/{entity_uuid}:extend-ttl"
    }
  ],
  "total": 3
}
```

---

## 6. Drift Management

### 5b.1 List Drift Records for a Resource

```
GET /api/v1/resources/{entity_uuid}/drift

Query parameters:
  status=<open|acknowledged|resolved|escalated>
  severity=<minor|significant|critical>
  page=<int>
  page_size=<int>

Response 200:
{
  "drift_records": [
    {
      "drift_uuid": "<uuid>",
      "detected_at": "<ISO 8601>",
      "overall_severity": "significant",
      "unsanctioned": true,
      "status": "open",
      "drifted_fields": [
        {
          "field_path": "fields.memory_gb",
          "realized_value": 8,
          "discovered_value": 16,
          "field_severity": "significant"
        }
      ],
      "available_actions": ["REVERT", "ACCEPT_DRIFT", "ESCALATE"]
    }
  ],
  "total": 1
}
```

### 5b.2 Acknowledge Drift Record

Marks a drift record as acknowledged. The entity remains drifted — this signals the owner has reviewed it.

```
POST /api/v1/resources/{entity_uuid}/drift/{drift_uuid}:acknowledge
{
  "reason": "Reviewing with provider before deciding on action"
}

Response 200:
{
  "drift_uuid": "<uuid>",
  "status": "acknowledged",
  "acknowledged_at": "<ISO 8601>"
}
```

### 5b.3 Accept Drift (Update Definition)

Accepts the discovered state as the new authoritative desired state. Creates a new Requested State and Realized State snapshot reflecting the discovered values. Resolves the drift record.

```
POST /api/v1/resources/{entity_uuid}/drift/{drift_uuid}:accept
{
  "accept_all_fields": true,         # accept all drifted fields
  "accept_fields": ["fields.memory_gb"],   # or select specific fields
  "reason": "Auto-scale event was legitimate; accepting new memory configuration"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "drift_uuid": "<uuid>",
  "status": "resolved",
  "resolution_type": "updated_definition",
  "new_realized_state_uuid": "<uuid>"
}
```

### 5b.4 Revert Drift

Submits a revert request — dispatches a new request to restore the resource to its Realized State values.

```
POST /api/v1/resources/{entity_uuid}/drift/{drift_uuid}:revert
{
  "reason": "Unauthorized change — reverting to declared state"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "drift_uuid": "<uuid>",
  "revert_request_uuid": "<uuid>",
  "status": "DISPATCHED",
  "status_url": "/api/v1/requests/{revert_request_uuid}/status"
}
```

---

## 7. Groups and Relationships

### 5c.1 List Resource Groups

Returns all Resource Groups in the actor's Tenant.

```
GET /api/v1/groups

Query parameters:
  group_class=<resource_grouping|policy_collection|composite>
  tag=<string>
  page=<int>
  page_size=<int>

Response 200:
{
  "groups": [
    {
      "group_uuid": "<uuid>",
      "handle": "tenant/payments/prod-vms",
      "display_name": "Production VMs — Payments",
      "group_class": "resource_grouping",
      "member_count": 12,
      "tags": ["production", "payments"]
    }
  ],
  "total": 4
}
```

### 5c.2 Describe Group

```
GET /api/v1/groups/{group_uuid}

Response 200:
{
  "group_uuid": "<uuid>",
  "handle": "tenant/payments/prod-vms",
  "display_name": "Production VMs — Payments",
  "group_class": "resource_grouping",
  "members": [
    {
      "entity_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "display_name": "payments-api-01",
      "membership_expires_at": null     # null = permanent membership
    }
  ],
  "tags": ["production", "payments"]
}
```

### 5c.3 Add Resource to Group

```
POST /api/v1/groups/{group_uuid}/members
{
  "entity_uuid": "<uuid>",
  "expires_at": "2026-12-31T23:59:59Z"   # optional; null = permanent
}

Response 201 Created:
{
  "group_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "membership_created_at": "<ISO 8601>"
}
```

### 5c.4 Remove Resource from Group

```
DELETE /api/v1/groups/{group_uuid}/members/{entity_uuid}

Response 204 No Content
```

### 5c.5 View Resource Relationships

```
GET /api/v1/resources/{entity_uuid}/relationships

Query parameters:
  relationship_type=<type>     filter by relationship type
  direction=<inbound|outbound|both>   default: both

Response 200:
{
  "relationships": [
    {
      "relationship_uuid": "<uuid>",
      "relationship_type": "attached_to",
      "direction": "outbound",
      "related_entity_uuid": "<uuid>",
      "related_entity_type": "Network.VLAN",
      "related_entity_display_name": "VLAN-100",
      "stake_strength": "required",
      "nature": "operational"
    }
  ],
  "total": 3
}
```

---

## 8. Requests and Approvals

### 6b.1 List Requests

```
GET /api/v1/requests

Query parameters:
  status=<status>               filter by lifecycle status (see 4.3)
  resource_type=<fqn>
  from=<ISO 8601>
  to=<ISO 8601>
  page=<int>
  page_size=<int>

Response 200:
{
  "requests": [
    {
      "request_uuid": "<uuid>",
      "entity_uuid": "<uuid>",
      "catalog_item_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "status": "COMPLETED",
      "submitted_at": "<ISO 8601>",
      "completed_at": "<ISO 8601>"
    }
  ],
  "total": 47
}
```

### 6b.2 List Pending Approvals (as Approver)

Returns requests awaiting approval where the authenticated actor is an eligible approver (by role or group membership).

```
GET /api/v1/approvals/pending

Response 200:
{
  "pending_approvals": [
    {
      "approval_uuid": "<uuid>",
      "request_uuid": "<uuid>",
      "entity_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "requester": { "uuid": "<uuid>", "display_name": "Bob Smith" },
      "estimated_cost_per_month": 230.40,
      "submitted_at": "<ISO 8601>",
      "deadline": "<ISO 8601>",
      "risk_score": 47,
      "risk_score_explanation": {
        "score_drivers": [
          "Estimated monthly cost exceeds Tenant ceiling (+35)",
          "Request submitted outside business hours (+15)",
          "Actor has 2 recent validation failures (+15)"
        ],
        "routing_threshold": 25,
        "profile": "standard"
      },
      "advisory_warnings": 1,
      "policy_name": "scoring-threshold: standard/reviewed"
    }
  ],
  "total": 2
}
```

### 6b.3 Approve or Reject a Request

This endpoint is used by reviewers with the appropriate role. It is designed to be callable by external systems (ServiceNow, Jira workflow integrations, Slack bots) that act on behalf of a reviewer — the `Authorization` header identifies which reviewer is recording the decision. DCM provides the gate and audit trail; the review process is the organization's responsibility. See [Design Priorities — Approval Tier Model](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md).

```
POST /api/v1/approvals/{approval_uuid}
{
  "decision": "approve | reject",
  "reason": "<required for reject; optional for approve>",
  "recorded_via": "dcm_ui | servicenow | jira | slack_bot | api_direct | other",
  "external_reference": "<optional ticket ID for audit trail>"
}

Response 202 Accepted:
{
  "approval_uuid": "<uuid>",
  "decision": "approve",
  "processed_at": "<ISO 8601>",
  "request_uuid": "<uuid>",
  "request_status": "ASSEMBLING"   # pipeline resumes on approve
}
```

---

## 9. Cost and Quota

### 7b.1 Get Cost Estimate (Pre-Submission)

Returns a cost estimate for a hypothetical request without submitting it.

```
POST /api/v1/cost/estimate
{
  "catalog_item_uuid": "<uuid>",
  "fields": {
    "cpu_count": 4,
    "memory_gb": 8
  }
}

Response 200:
{
  "estimated_cost": {
    "breakdown": [
      { "component": "compute", "unit": "per-hour", "amount": 0.28, "currency": "USD" },
      { "component": "ip-allocation", "unit": "per-hour", "amount": 0.04, "currency": "USD" }
    ],
    "total_per_hour": 0.32,
    "total_per_month": 230.40,
    "currency": "USD"
  },
  "cost_confidence": "high"
}
```

### 7b.2 Get Cost Actuals for a Resource

```
GET /api/v1/resources/{entity_uuid}/cost

Query parameters:
  from=<ISO 8601>    start of billing period (default: start of current month)
  to=<ISO 8601>      end of billing period (default: now)

Response 200:
{
  "entity_uuid": "<uuid>",
  "billing_state": "billable",
  "period": {
    "from": "2026-03-01T00:00:00Z",
    "to": "2026-03-28T15:00:00Z"
  },
  "actuals": {
    "total": 168.96,
    "currency": "USD",
    "breakdown": [
      { "component": "compute", "hours": 651, "amount": 182.28 },
      { "component": "ip-allocation", "hours": 651, "amount": 26.04 }
    ]
  },
  "current_rate_per_hour": 0.32
}
```

### 7b.3 View Quota Usage

Returns current quota consumption for the authenticated Tenant.

```
GET /api/v1/quota

Response 200:
{
  "tenant_uuid": "<uuid>",
  "quotas": [
    {
      "resource_type": "Compute.VirtualMachine",
      "limit": 100,
      "current_usage": 47,
      "percent_used": 47,
      "reserved": 3           # in-flight requests consuming quota
    },
    {
      "resource_type": "Network.IPAddress",
      "limit": 500,
      "current_usage": 189,
      "percent_used": 37.8,
      "reserved": 0
    }
  ]
}
```

---

## 10. Notifications and Webhooks

### 7c.1 List Notifications

Returns notifications delivered to the authenticated actor, most recent first.

```
GET /api/v1/notifications

Query parameters:
  status=<unread|read|all>   default: unread
  urgency=<low|medium|high|critical>
  event_type=<type>
  page=<int>
  page_size=<int>

Response 200:
{
  "notifications": [
    {
      "notification_uuid": "<uuid>",
      "event_type": "entity.decommissioning",
      "urgency": "high",
      "status": "unread",
      "delivered_at": "<ISO 8601>",
      "entity_uuid": "<uuid>",
      "entity_display_name": "VLAN-100",
      "audience_role": "stakeholder",
      "summary": "VLAN-100 is being decommissioned. Your resource VM-A is attached.",
      "action_url": "/api/v1/resources/<uuid>"
    }
  ],
  "total_unread": 3,
  "total": 47
}
```

### 7c.2 Mark Notification Read

```
POST /api/v1/notifications/{notification_uuid}/read

Response 200:
{
  "notification_uuid": "<uuid>",
  "status": "read",
  "read_at": "<ISO 8601>"
}

POST /api/v1/notifications:read-all    # mark all unread as read

Response 200:
{
  "marked_read": 3
}
```

### 7c.3 Manage Webhook Subscriptions

```
GET /api/v1/webhooks

Response 200:
{
  "subscriptions": [
    {
      "webhook_uuid": "<uuid>",
      "endpoint_url": "https://my-system.example.com/dcm/events",
      "events": ["entity.provisioned", "entity.decommissioned", "drift.detected"],
      "status": "active",
      "created_at": "<ISO 8601>"
    }
  ]
}

POST /api/v1/webhooks
{
  "endpoint_url": "https://my-system.example.com/dcm/events",
  "events": ["entity.provisioned", "entity.decommissioned"],
  "hmac_secret": "<consumer-generated-secret>",   # used for payload signing
  "description": "Production event sink"
}

Response 201 Created:
{
  "webhook_uuid": "<uuid>",
  "status": "active",
  "test_event_sent": true
}

DELETE /api/v1/webhooks/{webhook_uuid}
Response 204 No Content
```

---

## 11. Search

### 8b.1 Cross-Resource Search

Full-text and structured search across all resources in the actor's Tenant. Served from the Search Index — non-authoritative but fast.

```
GET /api/v1/search

Query parameters:
  q=<string>                  full-text query
  resource_type=<fqn>
  lifecycle_state=<state>
  drift_status=<clean|drifted|unknown>
  tag=<string>                repeatable
  compliance_domain=<domain>
  data_classification=<level> filter by highest data classification
  page=<int>
  page_size=<int>

Response 200:
{
  "results": [
    {
      "entity_uuid": "<uuid>",
      "resource_type": "Compute.VirtualMachine",
      "display_name": "payments-api-server-01",
      "lifecycle_state": "OPERATIONAL",
      "drift_status": "clean",
      "tags": ["production", "payments"],
      "resource_url": "/api/v1/resources/{entity_uuid}",
      "score": 0.98           # relevance score for text queries
    }
  ],
  "total": 3,
  "search_index_staleness_seconds": 12,
  "authoritative_store_ref": "/api/v1/resources?..."   # fallback URL if stale
}
```


## 12. Audit Trail

### 6.1 Query Audit Records for a Resource

```
GET /api/v1/resources/{entity_uuid}/audit

Query parameters:
  from=<ISO 8601>         start of time range
  to=<ISO 8601>           end of time range
  action=<action>         filter by action type
  actor_type=<human|service_account|system>
  page=<int>
  page_size=<int>

Response 200:
{
  "audit_records": [
    {
      "record_uuid": "<uuid>",
      "timestamp": "<ISO 8601>",
      "action": "PROVISION",
      "actor": {
        "uuid": "<uuid>",
        "type": "human",
        "display_name": "Jane Smith"
      },
      "summary": "VirtualMachine provisioned via EU-WEST-Prod-1",
      "correlation_id": "<uuid>"
    }
  ],
  "total": 47,
  "chain_integrity": "verified"      # verified | unverifiable | compromised
}
```

### 6.2 Follow Correlation ID

For cross-state correlation — following a request from Intent through all states:

```
GET /api/v1/audit/correlation/{correlation_id}

Response 200:
{
  "correlation_id": "<uuid>",
  "entity_uuid": "<uuid>",
  "timeline": [
    { "state": "intent",     "record_uuid": "<uuid>", "timestamp": "..." },
    { "state": "requested",  "record_uuid": "<uuid>", "timestamp": "..." },
    { "state": "realized",   "record_uuid": "<uuid>", "timestamp": "..." }
  ],
  "cross_dcm_refs": []               # cross-DCM records if federation involved
}
```

---

## 13. Error Model

All error responses follow a consistent structure:

```json
{
  "error": "<error_code>",
  "message": "<human-readable description>",
  "request_id": "<uuid>",
  "timestamp": "<ISO 8601>",
  "details": {}                      # error-specific additional context
}
```

**Standard error codes:**

| HTTP Status | Error Code | Meaning |
|-------------|-----------|---------|
| 400 | `invalid_request` | Malformed request or missing required fields |
| 400 | `tenant_ambiguous` | Actor has multiple Tenants; X-DCM-Tenant header required |
| 401 | `authentication_required` | No token or expired token |
| 403 | `authorization_denied` | Token valid but insufficient permissions |
| 403 | `step_up_required` | Operation requires step-up MFA challenge |
| 404 | `not_found` | Entity, catalog item, or request not found |
| 409 | `decommission_deferred` | Decommission blocked by active stakes or dependencies |
| 409 | `rehydration_lease_held` | Entity already being rehydrated |
| 409 | `field_not_editable` | Targeted delta attempted on non-editable field |
| 409 | `not_suspended` | Resume attempted on a non-suspended resource |
| 409 | `transfer_not_authorized` | No cross-tenant authorization between source and target Tenant |
| 409 | `no_ttl_constraint` | TTL extension attempted on resource with no time constraint |
| 422 | `policy_rejected` | GateKeeper policy rejected the request |
| 422 | `constraint_violated` | Field value violates declared constraint |
| 422 | `ttl_extension_rejected` | Policy rejected or capped the TTL extension request |
| 429 | `rate_limit_exceeded` | Actor has exceeded request rate page_size |
| 503 | `assembly_unavailable` | Request Payload Processor temporarily unavailable |
| 503 | `search_index_degraded` | Search index unavailable; use authoritative_store_ref fallback |

---


---

## 14. Consumer Contributions

Consumers with `policy_author` or `tenant_admin` role can contribute tenant-scoped artifacts directly via the Consumer API. All contributions flow through the GitOps PR model — DCM generates a PR and activates the artifact after the required review period. See [Federated Contribution Model](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md) for the complete contributor permission table.

### 9.1 Submit Policy Contribution

```
POST /api/v1/contribute/policy
X-DCM-Tenant: <tenant-uuid>

{
  "policy_type": "gatekeeper | transformation | recovery | lifecycle | orchestration_flow | governance_matrix_rule",
  "handle": "tenant/{tenant-handle}/gatekeeper/{name}",
  "domain": "tenant",
  "concern_type": "operational | security | compliance",
  "enforcement": "soft | hard",
  "match": { ... },
  "output": { ... },
  "shadow_mode": true,
  "commit_message": "<human-readable description of what this policy does>"
}

Response 202 Accepted:
{
  "contribution_uuid": "<uuid>",
  "policy_handle": "tenant/payments/gatekeeper/cost-ceiling",
  "status": "proposed",
  "shadow_mode": true,
  "review_required": true,
  "review_type": "reviewed",
  "pr_url": "https://git.corp.example.com/dcm-policies/pulls/145",
  "shadow_results_url": "/flow/api/v1/shadow/<policy_uuid>"
}
```

### 9.2 Submit Resource Group Definition

```
POST /api/v1/contribute/resource-group
X-DCM-Tenant: <tenant-uuid>

{
  "handle": "tenant/{tenant-handle}/groups/{name}",
  "display_name": "<human-readable name>",
  "group_class": "resource_grouping",
  "description": "<purpose of this group>",
  "membership_policy": {
    "auto_include": {
      "resource_type": "Compute.VirtualMachine",
      "tags": { "team": "payments", "env": "production" }
    }
  }
}

Response 201 Created:
{
  "group_uuid": "<uuid>",
  "handle": "tenant/payments/groups/prod-vms",
  "status": "active"             # resource groups activate immediately (no policy review)
}
```

### 9.3 List Contributions

```
GET /api/v1/contribute
X-DCM-Tenant: <tenant-uuid>

Query parameters:
  artifact_type=<policy | resource-group | catalog-item>
  status=<proposed | active | deprecated>

Response 200:
{
  "contributions": [
    {
      "contribution_uuid": "<uuid>",
      "artifact_type": "policy",
      "handle": "tenant/payments/gatekeeper/cost-ceiling",
      "status": "proposed",
      "shadow_mode": true,
      "pr_url": "https://...",
      "submitted_at": "<ISO 8601>",
      "review_status": "pending"
    }
  ]
}
```

### 9.4 Withdraw Contribution

```
DELETE /api/v1/contribute/{contribution_uuid}

Response 200:
{
  "contribution_uuid": "<uuid>",
  "status": "withdrawn",
  "pr_closed": true
}
```



---

## 15. Credential Management

### 9b.1 List Credentials for a Resource

```
GET /api/v1/resources/{entity_uuid}/credentials

Response 200:
{
  "credentials": [
    {
      "credential_uuid": "<uuid>",
      "credential_type": "ssh_key",
      "status": "active",
      "issued_at": "<ISO 8601>",
      "expires_at": "<ISO 8601>",
      "scope": { "operations": ["ssh_access"] },
      "retrieval": {
        "endpoint": "/api/v1/credentials/<uuid>/value",
        "auth_required": "step_up_mfa",
        "retrieval_count": 1,
        "last_retrieved_at": "<ISO 8601>"
      },
      "rotation_schedule": {
        "next_rotation_at": "<ISO 8601>",
        "rotation_trigger": "scheduled"
      }
    }
  ]
}
```

### 9b.2 Retrieve Credential Value

```
GET /api/v1/credentials/{credential_uuid}/value
X-DCM-StepUp-Token: <completed-challenge>  # if auth_required: step_up_mfa

Response 200:
{
  "credential_uuid": "<uuid>",
  "credential_type": "ssh_key",
  "value": { "private_key": "...", "public_key": "...", "username": "dcm-provisioned" },
  "expires_at": "<ISO 8601>",
  "retrieval_uuid": "<uuid>"
}

Response 410 Gone:  { "error": "credential_revoked_or_expired" }
```

### 9b.3 Request Credential Rotation

```
POST /api/v1/credentials/{credential_uuid}:rotate
{
  "reason": "Scheduled rotation per security policy"
}

Response 200 OK — returns `Operation`:
> Returns `Operation` resource. Poll `operation.name` for completion.
{
  "old_credential_uuid": "<uuid>",
  "new_credential_uuid": "<uuid>",
  "transition_window_ends": "<ISO 8601>",
  "new_retrieval_url": "/api/v1/credentials/<new_uuid>/value"
}
```


## 16. Conformance Levels

The Consumer API defines three conformance levels, mirroring the Operator Interface Specification model:

**Level 1 — Read-Only:** Catalog browsing, resource listing, status queries, search, cost estimates, quota views, and notification listing. No request submission or resource management. Suitable for reporting, dashboards, and read-only portal integrations.

**Level 2 — Standard:** All Level 1 operations plus request submission, status tracking, approvals, basic resource management (update editable fields, suspend/resume, decommission, bulk decommission, TTL extension, group management), and consumer contribution endpoints (policy authoring, resource group definitions). Required for all self-service portal implementations.

**Level 3 — Full:** All Level 2 operations plus rehydration, ownership transfer, drift management (acknowledge, accept, revert), audit trail access, correlation queries, webhook subscription management, and cost actuals. Required for ITSM integrations, compliance tooling, and full GitOps automation.

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*


## Operations — Polling Long-Running Requests

All async mutating operations return an `Operation` resource. The `operation.name` field
is the stable polling URL: `GET /api/v1/operations/{operation_uuid}`.

**Key relationship:** `operation_uuid == request_uuid`. The same UUID is used in both the
AEP-standard Operation endpoint and the DCM-native Request Status endpoint. Two polling
views are available — use whichever fits your client:

| Endpoint | Schema | Best for |
|----------|--------|----------|
| `GET /api/v1/operations/{uuid}` | `Operation` — `done`, `metadata`, `response/error` | AEP-compatible clients, simple polling |
| `GET /api/v1/requests/{uuid}/status` | `RequestStatus` — `pipeline_stage`, full status history, `entity_uuid` | DCM-native clients, debugging, rich UI |

Both endpoints reflect the same underlying state. When `done: true`, `operation.response`
contains the realized entity (same as the resource returned by `GET /api/v1/resources/{entity_uuid}`).

```
POST /api/v1/requests

Response 200 OK — returns Operation:
{
  "name": "/api/v1/operations/{request_uuid}",
  "done": false,
  "metadata": {
    "stage": "INITIATED",
    "resource_uuid": "{entity_uuid}",   // set immediately on entity creation
    "request_uuid": "{request_uuid}"    // == operation_uuid
  }
}
```

**Polling `GET /api/v1/operations/{operation_uuid}`:**

```
# While in progress:
{
  "name": "/api/v1/operations/{uuid}",
  "done": false,
  "metadata": {
    "stage": "PROVISIONING",
    "progress_pct": 45,
    "resource_uuid": "{entity_uuid}",
    "request_uuid": "{uuid}"
  }
}

# On success:
{
  "name": "/api/v1/operations/{uuid}",
  "done": true,
  "metadata": { "stage": "OPERATIONAL", "resource_uuid": "{entity_uuid}", "request_uuid": "{uuid}" },
  "response": { ... }   // the realized entity
}

# On failure:
{
  "name": "/api/v1/operations/{uuid}",
  "done": true,
  "metadata": { "stage": "FAILED", "request_uuid": "{uuid}" },
  "error": {
    "code": "PROVIDER_TIMEOUT",
    "message": "Provider did not respond within the configured timeout",
    "details": []
  }
}
```

**Polling guidance:** Use exponential backoff (1s → 2s → 5s → 10s → 30s).
For push-based updates, subscribe to the `request.progress_updated` webhook event.
For real-time browser monitoring, use the SSE stream: `GET /api/v1/requests/{uuid}/stream`.

**Cancellation:** `DELETE /api/v1/requests/{uuid}` cancels an in-progress operation.
The request enters CANCELLING state; cancellation success depends on provider support.

