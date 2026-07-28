---
Document Status: ✅ Complete
Document Type: Architecture Reference — API Versioning and Lifecycle
Maps to: udlm/governance/registry-governance.md
---

# DCM Data Model — API Versioning Strategy

> **Implements contracts defined in UDLM**:
> [udlm/governance/registry-governance.md](https://github.com/croadfeldt/udlm/blob/main/governance/registry-governance.md)
> and [udlm/contracts/event-catalog.md](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md).
> UDLM defines the registry-governance versioning and deprecation lifecycle and
> the event-catalog event-versioning contract. DCM operationalizes a concrete
> versioning strategy across every public API surface — Consumer, Admin,
> Operator Interface (Provider), and Flow GUI — including URL major versioning,
> deprecation lead time, and event schema versioning.

**Document Status:** ✅ Complete
**Document Type:** Architecture Reference — API Versioning and Lifecycle
**Related Documents:** [Consumer API Specification](../../docs/specifications/consumer-api-spec.md) | [Admin API Specification](../../docs/specifications/dcm-admin-api-spec.md) | [Operator Interface Specification](../../docs/specifications/dcm-operator-interface-spec.md) | [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md) | [Registry Governance](https://github.com/croadfeldt/udlm/blob/main/governance/registry-governance.md) | [Design Priorities](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md)

> **This document governs all DCM API surfaces.** Every public API endpoint — Consumer, Admin, Operator Interface (Provider), Flow GUI — follows this versioning strategy. The strategy is designed to make the secure, compatible path the easy path: clients that do nothing get the version they requested; breaking changes are announced with sufficient lead time; the newest version is always the supported version.

---

## 1. Versioning Model

### 1.1 URL-Based Major Version

DCM APIs use **URL path versioning** for major versions. The version is the first path segment after the API surface prefix:

```
Consumer API:      https://{dcm-instance}/api/v1/
Admin API:         https://{dcm-instance}/api/v1/admin/
Provider API (OIS):https://{dcm-instance}/provider/api/v1/
Flow GUI API:      https://{dcm-instance}/flow/api/v1/
```

The version segment (`v1`, `v2`, etc.) represents a major version. It increments only on breaking changes. Multiple major versions may coexist during a transition window (see Section 4).

The four surfaces are separate because they are distinct **trust zones** — Consumer, Admin, Provider (OIS), and Flow each carry their own authentication and RBAC, and each versions independently (the Consumer API can be at `v2` while the Provider/OIS surface is still `v1`).

### 1.2 Version Granularity — Per-API, Not Per-Endpoint

Versioning is **per-API surface**, not per-endpoint. When a breaking change occurs to any endpoint within an API surface, the entire surface increments to the next major version. This means:

- `v2` of the Consumer API is a complete API surface, not a patchwork of versioned endpoints
- All endpoints within a surface version are internally consistent
- Clients target a single version for all their interactions with that surface

Individual endpoints are not independently versioned. If a single endpoint needs a breaking change, the API surface version increments and all other endpoints continue unchanged under the new version.

### 1.3 Minor and Revision Changes

DCM follows [Semantic Versioning](https://semver.org/) — that baseline (major = breaking, minor = additive, patch/revision = fixes) is assumed and not restated here. This section records only the **DCM-specific** application of it.

Non-breaking changes within a major version are documented in the API changelog but do not change the URL. Clients do not need to take any action for non-breaking changes.

- **Minor change**: new optional fields, new endpoints, expanded enum values with version-compatible defaults
- **Revision**: documentation corrections, clarifications, non-functional specification updates

---

## 2. Breaking Change Definition

A change is **breaking** if it requires any existing client to modify its code or configuration to continue working correctly. The general taxonomy below is standard REST practice — it is enumerated here not as novel guidance but as DCM's **explicit, authoritative checklist** so that "is this breaking?" has one answer across every surface. The DCM-specific entries to note are idempotency semantics, the response-envelope structure, authentication-method removal, and enum-value handling (clients MUST tolerate unknown enum values):

**Request changes:**
- Removing a field that was previously accepted
- Changing a field from optional to required
- Changing a field's type (e.g. string → integer)
- Removing an accepted enum value
- Changing URL path structure (endpoint rename or restructure)
- Changing HTTP method for an existing operation
- Removing an endpoint

**Response changes:**
- Removing a field from any response
- Changing a field's type in any response
- Changing a field's name in any response
- Removing a previously returned enum value
- Changing HTTP status code semantics (e.g. 200 → 202, or changing when 4xx vs 5xx is returned)
- Changing the response envelope structure

**Behavior changes:**
- Changing default values in ways that alter existing behavior
- Changing idempotency semantics
- Removing a previously supported authentication method
- Tightening validation (rejecting previously accepted inputs)
- Changing pagination behavior in ways that break existing cursor patterns

**The following are NOT breaking changes:**
- Adding new optional request fields (with sensible defaults)
- Adding new response fields (existing clients safely ignore unknown fields)
- Adding new endpoints
- Expanding an enum with new values (clients must handle unknown enum values gracefully)
- Relaxing validation (accepting previously rejected inputs)
- Adding new error codes (clients that handle errors generically are unaffected)
- Performance improvements, infrastructure changes, security patches
- Documentation improvements

---

## 3. Version Discovery

Clients can discover available API versions and their status without prior knowledge:

### 3.1 Well-Known Discovery Endpoint

```
GET https://{dcm-instance}/.well-known/dcm-api-versions

Response 200:
{
  "dcm_version": "1.2.0",
  "api_surfaces": {
    "consumer": {
      "current": "v2",
      "supported": ["v1", "v2"],
      "versions": {
        "v1": {
          "status": "deprecated",
          "sunset_date": "2027-06-01",
          "deprecation_date": "2026-06-01",
          "base_url": "/api/v1/",
          "changelog_url": "/api/v1/changelog"
        },
        "v2": {
          "status": "stable",
          "released_date": "2026-06-01",
          "base_url": "/api/v2/",
          "changelog_url": "/api/v2/changelog"
        }
      }
    },
    "admin": {
      "current": "v1",
      "supported": ["v1"],
      "versions": {
        "v1": { "status": "stable", "base_url": "/api/v1/admin/" }
      }
    },
    "provider": {
      "current": "v1",
      "supported": ["v1"],
      "versions": {
        "v1": { "status": "stable", "base_url": "/provider/api/v1/" }
      }
    }
  }
}
```

### 3.2 Per-Version Changelog

```
GET /api/v1/changelog

Response 200:
{
  "version": "v1",
  "changes": [
    {
      "date": "2026-01-15",
      "type": "minor",
      "description": "Added optional `score_drivers` field to request status response",
      "affected_endpoints": ["GET /api/v1/requests/{uuid}/status"]
    }
  ]
}
```

---

## 4. Deprecation and Sunset Lifecycle

### 4.1 Deprecation Timeline

When a new major version is released, the previous version enters a **deprecation period**. The deprecation timeline is profile-governed — production deployments require longer support windows than development environments:

```yaml
api_version_support_lifecycle:
  minimal:
    deprecation_notice_period: P90D    # 90 days notice before sunset
    deprecated_version_support: P180D  # old version supported 180 days after deprecation
    
  dev:
    deprecation_notice_period: P0D    # none — dev has no deprecation guarantee
    deprecated_version_support: P0D    # old versions may be removed immediately
    # Dev is for iteration, not stable consumers; versions can break without a
    # support window. Use minimal+ if you need any deprecation lead time.

  standard:
    deprecation_notice_period: P180D
    deprecated_version_support: P365D  # 1 year

  prod:
    deprecation_notice_period: P365D   # 1 year notice
    deprecated_version_support: P730D  # 2 years support after deprecation

  fsi:
    deprecation_notice_period: P548D   # 18 months notice
    deprecated_version_support: P1095D # 3 years support after deprecation

  sovereign:
    deprecation_notice_period: P730D   # 2 years notice
    deprecated_version_support: P1460D # 4 years support after deprecation
```

**Deprecation ≠ Sunset.** A deprecated version continues to function. Sunset is when it stops working. The deprecation period is the window between "we recommend you migrate" and "you must migrate."

### 4.2 Deprecation Headers

When a client calls a deprecated API version, the response includes standard deprecation headers (per [RFC 8594](https://datatracker.ietf.org/doc/html/rfc8594) and [RFC 9745](https://datatracker.ietf.org/doc/html/rfc9745)):

```http
HTTP/1.1 200 OK
Deprecation: @1749340800          # Unix timestamp when this version was deprecated
Sunset: @1781049600               # Unix timestamp when this version will stop working
Link: <https://{dcm-instance}/api/v2/>; rel="successor-version"
Link: <https://{dcm-instance}/api/v1/migration-guide>; rel="deprecation"
```

### 4.3 Deprecation Events

When a version is deprecated or sunsetted, DCM fires notification events:

- `governance.api_version_deprecated` — version entered deprecation; Sunset header begins appearing
- `governance.api_version_sunset_warning` — 30 days before sunset; high urgency
- `governance.api_version_sunset` — version has reached sunset date; calls now return 410 Gone

Platform admins should configure notification routing for these events to ensure API consumers receive timely warning.

### 4.4 Sunset Behavior

After the sunset date, calls to the deprecated version return:

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": "api_version_sunset",
  "message": "API version v1 reached its sunset date on 2027-06-01. Migrate to v2.",
  "successor_version": "v2",
  "migration_guide_url": "/api/v2/migration-guide",
  "sunset_date": "2027-06-01"
}
```

---

## 5. Version Negotiation

### 5.1 How Clients Specify a Version

The URL path is the primary versioning mechanism. No headers or query parameters are required — the URL is authoritative:

```
GET /api/v1/resources        → Consumer API v1
GET /api/v2/resources        → Consumer API v2 (when available)
```

### 5.2 Version Preference Header (Optional)

For clients that need to pin to a specific version or test against a new version before migrating, an optional `DCM-API-Version` header is supported:

```http
GET /api/v1/resources
DCM-API-Version: v1          # explicit pin; returns 406 if v1 is sunsetted
```

If the header specifies a sunsetted version, the response is `406 Not Acceptable` with a migration guide reference.

### 5.3 Latest-Version Alias

```
GET /api/latest/resources    # always routes to current stable version
```

The `latest` alias is provided for development and testing. It is **not recommended for production** — production clients should pin to a specific version to avoid inadvertent breaking changes when a new major version becomes `latest`.

---

## 6. Beta and Preview Endpoints

New capabilities that are not yet stable may be released as **preview endpoints** within the current major version:

```
GET /api/v1/preview/new-feature
```

Preview endpoints:
- Are not covered by the stability guarantees of the parent version
- May change or be removed without a major version increment
- Are marked in the API changelog and discovery endpoint as `status: preview`
- Must not be used in production automation without explicit acknowledgment of instability

```yaml
# Discovery response for a preview endpoint
"new-feature": {
  "status": "preview",
  "stability_commitment": "none",
  "planned_graduation": "v2",
  "feedback_url": "https://github.com/dcm-project/discussions"
}
```

Preview endpoints graduate to stable when they are included in a new major version release.

---

## 7. Provider API (OIS) Versioning

The Operator Interface Specification (OIS) governs how DCM calls providers. Provider implementations must support the version of the OIS they declare in their capability registration.

### 7.1 OIS Version in Capability Registration

```yaml
provider_registration:
  ois_version: "1.0"           # which OIS version this provider implements
  ois_version_min: "1.0"       # minimum OIS version supported
  ois_version_max: "1.x"       # maximum OIS version supported (x = any minor)
```

### 7.2 OIS Compatibility

DCM maintains version-compatible with registered OIS versions during the support lifecycle. A DCM instance running OIS v2 must continue to dispatch to providers registered on OIS v1 until the version is sunset.

When the OIS version is incremented:
1. DCM announces the new OIS version via the event `governance.ois_version_released`
2. Providers have the deprecation notice period to upgrade their implementation
3. DCM dispatches using the appropriate OIS version per the provider's declared capability
4. After sunset, providers still on deprecated OIS versions receive `410 Gone` on dispatch

**Why an event, not a REST response (step 1).** A version/capability change is a **one-to-many** announcement — every registered provider and every interested subscriber needs to learn about it, and they are not in the middle of a request when it happens. That is a fan-out, so it is published on the event bus (CloudEvents), not returned synchronously. By contrast, an actual **dispatch** (step 3) is **point-to-point** and needs an immediate result, so it stays a synchronous REST call. The rule across DCM: state/capability *changes* broadcast as events; *operations* that need a result are REST.

### 7.3 Provider-Initiated API Versioning

Providers that expose their own management APIs (beyond the standard OIS surface) are responsible for their own versioning. DCM does not version-manage provider-internal APIs. Providers should follow the same breaking-change definition (Section 2) and announce breaking changes via `provider_update.submitted` events.

---

## 8. Version Upgrade Path

When a new major API version is published, a machine-readable change log is available at:

```
GET /api/v{N}/migration-guide
```

This endpoint returns all breaking changes from the previous major version:

```json
{
  "from_version": "v1",
  "to_version": "v2",
  "breaking_changes": [
    {
      "change_id": "BC-001",
      "type": "field_removed",
      "endpoint": "GET /api/v2/resources/{uuid}",
      "description": "Field 'legacy_id' removed — use 'entity_uuid' instead"
    }
  ],
  "new_capabilities": []
}
```

Clients declare the API version they target via the `Accept-Version` header or URL prefix. DCM supports all non-sunset major versions simultaneously. When a version reaches sunset, responses include `Deprecation` and `Sunset` headers (RFC 8594) before support is withdrawn.

---


## 9. Internal API Versioning

DCM internal component APIs (Control Plane components communicating with each other) follow a simpler model:

- Internal APIs are not exposed externally and not subject to the external versioning lifecycle
- Internal breaking changes require a coordinated deployment of all affected components
- DCM release versions (e.g. `1.2.0`) cover the complete set of internal APIs for that release
- Operators upgrading DCM must upgrade all components together per the release upgrade guide

---

## 10. System Policies

| Policy | Rule |
|--------|------|
| `VER-001` | All DCM public API surfaces use URL path versioning. The version path segment is the only authoritative version indicator. |
| `VER-002` | A change is breaking if any existing client must modify code or configuration to continue working. When in doubt, treat a change as breaking. |
| `VER-003` | Deprecated API versions must return `Deprecation`, `Sunset`, and `Link` headers on every response during the deprecation period (per RFC 8594 / RFC 9745). |
| `VER-004` | Deprecated versions must remain fully functional until the sunset date. Bugs in deprecated versions are fixed; new features are not backported. |
| `VER-005` | The deprecation notice period and deprecated version support window are profile-governed. Production deployments require longer windows than development. See Section 4.1. |
| `VER-006` | The `latest` version alias is available but must not be recommended for production use. Production clients must pin to a specific version. |
| `VER-007` | Preview endpoints are not stable. They may change or be removed without a major version increment. They are identified by the `/preview/` path segment. |
| `VER-008` | Every new major version must publish a machine-readable migration guide at `/api/v{N}/migration-guide`. |
| `VER-009` | DCM must maintain dispatch compatibility with providers registered on supported OIS versions until the OIS version is sunset. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
