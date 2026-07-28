---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Placement and Priority Bands
Established: 2026-05-26
Maps to: udlm/topology/location-topology-layers.md
---

# Placement and Priority Bands

> **Implements contracts defined in UDLM**:
> [udlm/topology/location-topology-layers.md](https://github.com/croadfeldt/udlm/blob/main/topology/location-topology-layers.md).
> UDLM defines the layered-topology contract (layers, parent/child
> relationships, typed fields, hierarchy assembly rules, lifecycle states,
> custom/extension mechanism). DCM operationalizes the location topology
> database and query interface, priority band allocation (premium /
> standard / budget), consumer selection model, authority and ownership
> model, relationship to the placement engine, location layer lifecycle
> management, and profile-governed topology constraints.

> See [`canonical-9-layer-hierarchy.md`](canonical-9-layer-hierarchy.md) for
> DCM's specific 9-layer hierarchy (Country → Region → Zone → Site → DC →
> Hall → Cage → Rack → Unit).

---

## 1. Location topology database and query interface

DCM stores location layers in the PostgreSQL persistence layer:

```sql
CREATE TABLE location_layers (
    layer_uuid       UUID PRIMARY KEY,
    handle           VARCHAR(256) NOT NULL UNIQUE,    -- locations/{type}/{code}
    location_type    VARCHAR(32) NOT NULL,             -- country, region, zone, site, ...
    level            NUMERIC(4,1) NOT NULL,            -- 1, 2, 3, ..., 9 (or 3.5 for custom)
    parent_uuid      UUID REFERENCES location_layers(layer_uuid),
    priority         VARCHAR(32) NOT NULL,             -- "200.10.0"
    status           VARCHAR(16) NOT NULL,             -- active | deprecated | retired
    version          VARCHAR(16) NOT NULL,             -- semver "1.2.0"
    data             JSONB NOT NULL DEFAULT '{}',      -- type-specific field data
    sovereignty      JSONB NOT NULL DEFAULT '{}',      -- zone_handle, jurisdiction, residency
    placement        JSONB NOT NULL DEFAULT '{}',      -- eligible_resource_types, max_class
    concern_tags     TEXT[] NOT NULL DEFAULT '{}',
    owned_by         JSONB NOT NULL DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       UUID NOT NULL
);

CREATE INDEX idx_location_handle ON location_layers(handle);
CREATE INDEX idx_location_type ON location_layers(location_type, status);
CREATE INDEX idx_location_parent ON location_layers(parent_uuid);
CREATE INDEX idx_location_sovereignty ON location_layers((sovereignty->>'zone_handle'));
```

### 1.1 Query interface

```
# Admin API
GET    /api/v1/admin/locations
GET    /api/v1/admin/locations/{location_uuid}
POST   /api/v1/admin/locations         # via GitOps PR — not direct write
PATCH  /api/v1/admin/locations/{location_uuid}    # version bump
DELETE /api/v1/admin/locations/{location_uuid}    # deprecation start

# Consumer-facing (read-only)
GET    /api/v1/catalog/locations       # filtered by entitlement + catalog item
```

### 1.2 Sample layer instance

```yaml
layer:
  artifact_metadata:
    uuid: <uuid>
    handle: "locations/dc/fra-dc1"      # locations/{type}/{code}
    version: "1.2.0"
    status: active
    owned_by:
      display_name: "Data Center Operations — Frankfurt"
      group_handle: "groups/dc-operations-fra"
    created_via: pr
    created_at: <ISO 8601>

  layer_type: core
  location_type: data_center
  scope: type_agnostic

  priority:
    value: "500.10.0"                     # band 500 (Data Center), seq 10
    label: "core.location.dc.fra-dc1"
    category: core_location

  location_hierarchy:
    parent_handle: "locations/site/fra-campus-01"
    parent_type: site
    ancestors:
      - { handle: "locations/az/eu-west-1a", type: zone }
      - { handle: "locations/region/eu-west", type: region }
      - { handle: "locations/country/de", type: country }

  data:
    dc_name: "DC1 — Frankfurt Alpha"
    dc_code: "FRA-DC1"
    tier_classification: tier_3
    power_capacity_kw: 4000
    pue_rating: 1.35
    redundancy_model: "2N"
    network_uplinks:
      - { carrier: "DE-CIX", bandwidth_gbps: 100, redundant: true }
      - { carrier: "NTT",    bandwidth_gbps: 100, redundant: true }
    dc_operations_team: "groups/dc-operations-fra"
    certifications:
      - { standard: "ISO 27001", expires_at: "2027-06-30" }
      - { standard: "SOC 2 Type II", expires_at: "2026-12-31" }

  sovereignty:
    zone_handle: "zones/eu-west-sovereign"
    data_residency: EU
    jurisdiction_codes: [DE]
    cross_border_permitted: false

  placement:
    eligible_resource_types: []           # empty = all eligible
    ineligible_resource_types: []
    max_data_classification: restricted
    requires_accreditations: []

  concern_tags: [location, data-center, frankfurt, eu-west, tier-3]
```

---

## 2. Priority band allocation

Location layers occupy a dedicated band in the Core Layer priority space:

```
100.xx.0 — Country layers
200.xx.0 — Region layers
300.xx.0 — Zone / Availability Zone layers
400.xx.0 — Site / Campus layers
500.xx.0 — Data Center layers
600.xx.0 — Hall / Pod / Row layers
700.xx.0 — Cage / Enclosure layers
800.xx.0 — Rack layers
900.xx.0 — Unit / Slot layers (provider-managed)

xx = sequence number within the level (01, 02, ... 99)
```

This ensures hierarchy precedence is correct: Country always has lower
precedence than Region, etc.

### 2.1 Pricing tier bands (premium/standard/budget)

DCM supports an orthogonal pricing tier classification within a given
location level. Bands are configured as tags on location layers and consumed
by placement preferences:

| Pricing band | Use cases | Selection signal |
|---|---|---|
| `premium` | Production-critical, low-latency, redundant power | DC tier_classification: tier_3+, redundancy_model: 2N+ |
| `standard` | Production, normal SLA | tier_2/tier_3, N+1 redundancy |
| `budget` | Dev, test, batch, ephemeral | tier_1/tier_2, N redundancy |

Tagged via `concern_tags: [premium]` (etc.) on the location layer. Placement
filters can include `prefer_pricing_band: standard` in catalog items.

---

## 3. Consumer selection model

Consumers do not interact with location layers directly. Location selection
is part of the **catalog item field schema**. When a consumer calls
`GET /api/v1/catalog/{catalog_item_uuid}`, the `location` field constraint
of type `layer_reference` includes the `allowed_values` list — the set of
active location layer instances the consumer is entitled to and the resource
type is eligible for.

### 3.1 Consumer request

```json
POST /api/v1/requests
{
  "catalog_item_uuid": "<uuid>",
  "fields": {
    "location": "layer-uuid-fra-dc1",     // DC-level layer UUID
    "os_image": "layer-uuid-rhel-9-4",
    "cpu_count": 4
  }
}
```

If the consumer wants to express location at a coarser level (Zone or
Region), they submit the layer UUID of that level. DCM's Placement Engine
refines downward to a specific DC during placement.

### 3.2 Filtering allowed_values

The catalog item declaration controls which location layers appear via the
`filter` clause on the `layer_reference` constraint:

```yaml
constraint:
  type: layer_reference
  layer_type: location.data_center
  filter:
    tags: [production]
    min_tier: tier_3
    required_certifications: [iso_27001]
```

The Platform Team controls which DCs are eligible for each catalog item by
configuring the filter — without changing the location layers themselves.

---

## 4. Authority and ownership model

Each location type has a designated owning authority. Defaults ship with
DCM but are configurable per deployment:

```yaml
location_authority_model:
  country:
    creating_authority: Platform Governance Team
    approval_required: true
    approval_tier: platform_admin

  region:
    creating_authority: Network Operations
    approval_tier: platform_admin

  zone:
    creating_authority: Data Center Operations
    approval_tier: platform_admin

  site:
    creating_authority: Facilities Management
    approval_tier: team_lead

  data_center:
    creating_authority: Data Center Operations
    approval_tier: team_lead

  hall:
    creating_authority: Data Center Operations
    approval_tier: operator

  cage:
    creating_authority: Data Center Operations
    approval_tier: operator

  rack:
    creating_authority: Data Center Operations
    approval_tier: operator
```

All location layer changes follow the standard GitOps workflow — PRs
reviewed by the owning authority, merged on approval. Location layers are
**immutable once active** — a new version is created for any change,
preserving the full history.

---

## 5. Relationship to the Placement Engine

The Placement Manager uses location topology data at three steps of the
six-step placement algorithm (see
[`../convergence-engine/scoring.md`](../convergence-engine/scoring.md)):

### 5.1 Step 1 — Sovereignty pre-filter

Location layers carry `sovereignty.zone_handle`. The Placement Engine
eliminates any provider whose declared sovereignty zones do not include the
zone associated with the requested location. **Hard pre-filter** — not a
tie-breaker.

### 5.2 Step 3 — Capability filter

Location layers carry `placement.max_data_classification` and
`placement.requires_accreditations`. Providers that cannot satisfy these
location-level constraints are eliminated, even if they satisfy global
accreditation requirements.

### 5.3 Step 6 — Tie-breaking

When multiple providers qualify, location-level priority declarations can
be used as a tie-breaking preference (e.g., "prefer providers in the same
DC over providers in a different DC in the same zone").

### 5.4 Layer fields available to placement policies

Location layers populate `location.*` fields in the assembled payload,
which Placement policies use in their constraint expressions:

```rego
# Example: Placement policy for PHI data
placement if {
    input.payload.location.jurisdiction == "EU/GDPR"
    input.payload.location.max_data_classification == "restricted"
    "hipaa_baa" in input.payload.location.required_accreditations
}
```

---

## 6. Location layer lifecycle management

Location layers follow the standard layer lifecycle:

```
developing → proposed → active → deprecated → retired
```

### 6.1 Decommissioning a location

When a Data Center is being decommissioned:

1. Location layer transitions to `deprecated`
2. Placement Engine stops routing new requests to providers in that DC
3. Existing resources receive a `location.decommission_warning` notification
4. Resources are migrated to alternative locations
5. Layer transitions to `retired` when all resources have been migrated

### 6.2 Operational draining

For planned maintenance (not decommission), an operational draining mode is
supported:

```yaml
operational_draining:
  enabled: true
  drain_for: PT4H
  drain_reason: "Quarterly maintenance window"
  block_new_requests: true
  allow_existing_operations: true
  emergency_override: requires_platform_admin
```

During drain, placement skips this location for new requests; existing
operations continue.

### 6.3 Re-placement

When a location is permanently retired and resources must be re-placed,
DCM:

1. Generates re-placement candidates for each affected entity
2. Notifies entity owners with the proposed new location
3. Awaits owner approval or runs auto-re-placement per policy
4. Executes the re-placement as a standard request (cancel + new request, or
   migrate where supported)

### 6.4 Location data changes

When a DC gets a new network uplink or achieves a new certification, a new
version of the location layer is published (minor version bump). The
Requested State for existing resources is NOT retroactively updated —
provenance is preserved. Future requests and re-realizations pick up the
new data.

### 6.5 Capacity changes

`rack_units_available` is a mutable field, updated by Data Center Operations
as capacity changes without a new version. All other location fields
require a new version to change.

---

## 7. Profile-governed topology constraints

| Profile | Topology constraints |
|---|---|
| homelab | No constraint enforcement; sovereignty optional |
| dev | Sovereignty optional; placement filter advisory |
| standard | Sovereignty required for restricted+; placement filter enforced |
| prod | Sovereignty enforced; max_data_classification enforced |
| fsi | All topology constraints enforced; cross-jurisdiction blocked at hard rule |
| sovereign | All constraints enforced; hardware attestation required for federation |

---

## 8. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `LOC-001-DCM` | Every DCM resource entity has a resolved location_uuid at DC level or below; requests without one rejected at validation |
| `LOC-002-DCM` | Location layers are Core Layers; service-specific or provider-specific data is invalid |
| `LOC-003-DCM` | DCM validates location hierarchy acyclicity at layer submission |
| `LOC-004-DCM` | DCM rejects location layer handles not matching pattern `locations/{type}/{code}` |
| `LOC-005-DCM` | DCM Placement Engine resolves abstract location levels (Zone, Region) to specific DC before dispatch |
| `LOC-006-DCM` | DCM enforces max_data_classification as upper bound; requests exceeding it rejected at capability filter |
| `LOC-007-DCM` | DCM propagates location layer changes to registry and Service Catalog within next sync cycle |
| `LOC-008-DCM` | Custom location types use decimal levels; level values unique across all registered types |
| `LOC-009-DCM` | DCM rejects location layers without sovereignty.zone_handle or explicit sovereignty: not_applicable in standard+ profiles |
