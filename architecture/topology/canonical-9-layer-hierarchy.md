---
Document Status: ✅ Stable — DCM canonical default
Document Type: Architecture Reference — Topology Hierarchy
Established: 2026-05-26
Maps to: udlm/topology/location-topology-layers.md
---

# Canonical 9-Layer Location Hierarchy

> **Implements contracts defined in UDLM**:
> [udlm/topology/location-topology-layers.md](https://github.com/croadfeldt/udlm/blob/main/topology/location-topology-layers.md)
> realizes the layered-topology contract in UDLM with DCM's canonical 9-layer
> scheme. UDLM defines the abstract layered-topology contract (layers have
> parent/child relationships, carry typed fields, follow lifecycle states).
> DCM picks the specific Country → Region → Zone → Site → Data Center →
> Hall → Cage → Rack → Unit hierarchy as its canonical default. A peer
> DCM realization could pick a different hierarchy and remain
> UDLM-conformant.

---

## 1. The DCM canonical hierarchy

DCM ships with nine standard location types. The hierarchy is ordered from
broadest to most specific. Each type has a standard name, a short code for
handles and references, and a set of standard data fields.

```
Level 1 — Country (CTY)
Level 2 — Region (RGN)
Level 3 — Zone / Availability Zone (AZ)
Level 4 — Campus / Site (SITE)
Level 5 — Data Center / Facility (DC)
Level 6 — Hall / Pod / Row (HALL)      [optional]
Level 7 — Cage / Enclosure (CAGE)     [optional]
Level 8 — Rack (RACK)
Level 9 — Unit / Slot (UNIT)           [optional — typically provider-managed]
```

Levels marked `[optional]` may be omitted if not relevant to an organization's
estate. The hierarchy is still valid when levels are skipped — a Rack can be
a direct child of a Data Center if Halls and Cages are not used.

**Custom types** may be inserted at any level via decimal-numbered insertion
(e.g., `level: 3.5` between Zone and Site). Custom types follow the same
format as standard types and are registered in the Location Type Registry.
A Navy deployment, for example, might insert Fleet (3.5) and Ship (4.5)
between Zone and Site, and Site and Data Center respectively.

---

## 2. Standard type definitions

Each standard type has a defined schema of fields. These fields become the
data carried by location layer instances of that type.

### 2.1 Country (CTY)

```yaml
location_type: country
code: CTY
level: 1

standard_fields:
  country_name:                  { type: string, required: true, example: "Germany" }
  iso_3166_1_alpha2:             { type: string, pattern: '^[A-Z]{2}$', required: true, example: "DE" }
  iso_3166_1_alpha3:             { type: string, pattern: '^[A-Z]{3}$', required: true, example: "DEU" }
  data_sovereignty_jurisdiction: { type: string, required: true, example: "EU/GDPR" }
  regulatory_frameworks:         { type: array, items: string, example: [GDPR, NIS2, eIDAS] }
  primary_currency:              { type: string, format: ISO-4217, example: "EUR" }
  utc_offsets:                   { type: array, items: string, example: ["UTC+1", "UTC+2"] }

owning_authority_default: Platform Governance Team
```

### 2.2 Region (RGN)

```yaml
location_type: region
code: RGN
level: 2
parent_type: country

standard_fields:
  region_name:           { type: string, required: true, example: "EU West" }
  region_code:           { type: string, required: true, example: "eu-west" }
  geographic_bounds:     { type: object, properties: { lat_min, lat_max, lon_min, lon_max } }
  primary_interconnect:  { type: string, example: "DE-CIX Frankfurt" }
  failover_region:       { type: string, format: location-handle, example: "regions/eu-north" }
  latency_profile:
    intra_region_ms:     2
    to_regions:          { "eu-north": 15, "us-east": 85 }

owning_authority_default: Network Operations
```

### 2.3 Zone / Availability Zone (AZ)

```yaml
location_type: zone
code: AZ
level: 3
parent_type: region

standard_fields:
  zone_name:                { type: string, required: true, example: "EU West Zone A" }
  zone_code:                { type: string, required: true, example: "eu-west-1a" }
  isolation_boundary:       { enum: [independent_power, independent_cooling, independent_network, full], required: true }
  high_availability_peer_zones: { type: array, items: location-handle }
  target_rpo_minutes:       { type: integer }
  target_rto_minutes:       { type: integer }

owning_authority_default: Data Center Operations
```

### 2.4 Campus / Site (SITE)

```yaml
location_type: site
code: SITE
level: 4
parent_type: zone

standard_fields:
  site_name:        { type: string, required: true, example: "Frankfurt Campus" }
  site_code:        { type: string, required: true, example: "FRA-CAMPUS-01" }
  physical_address: { required: true, properties: { street, city, postal_code, country } }
  owned_or_leased:  { enum: [owned, leased, colocation, shared], required: true }
  security_tier:    { enum: [1, 2, 3, 4] }
  noc_contact:      { properties: { email, phone, escalation_url } }

owning_authority_default: Facilities Management
```

### 2.5 Data Center / Facility (DC)

```yaml
location_type: data_center
code: DC
level: 5
parent_type: site

standard_fields:
  dc_name:             { type: string, required: true, example: "DC1 — Frankfurt Alpha" }
  dc_code:             { type: string, required: true, example: "FRA-DC1" }
  tier_classification: { enum: [tier_1, tier_2, tier_3, tier_4] }
  power_capacity_kw:   { type: number }
  cooling_capacity_kw: { type: number }
  pue_rating:          { type: number, example: 1.35 }
  redundancy_model:    { enum: [N, N+1, 2N, 2N+1] }
  network_uplinks:     { type: array, items: { carrier, bandwidth_gbps, redundant } }
  on_site_contact:     { properties: { role, email, phone } }
  dc_operations_team:  { type: string, format: group-handle, required: true }
  certifications:      { type: array, items: { standard, expires_at } }

owning_authority_default: Data Center Operations
```

### 2.6 Hall / Pod / Row (HALL) — optional

```yaml
location_type: hall
code: HALL
level: 6
parent_type: data_center
optional: true

standard_fields:
  hall_name:        { type: string, required: true, example: "Hall A — High Density" }
  hall_code:        { type: string, required: true, example: "FRA-DC1-HALL-A" }
  network_segment:  { type: string }
  power_phase:      { type: string }
  cooling_type:     { enum: [air, liquid, rear_door, immersion] }
  max_rack_units:   { type: integer }

owning_authority_default: Data Center Operations
```

### 2.7 Cage / Enclosure (CAGE) — optional

```yaml
location_type: cage
code: CAGE
level: 7
parent_type: hall
optional: true

standard_fields:
  cage_name:                  { type: string, required: true, example: "Cage 12 — Payments Isolated Zone" }
  cage_code:                  { type: string, required: true, example: "FRA-DC1-HALL-A-CAGE-12" }
  tenant_uuid:                { type: string, format: uuid }
  security_classification:    { type: string, example: "restricted" }
  access_control_system:      { type: string, example: "Lenel S2" }

owning_authority_default: Data Center Operations
```

### 2.8 Rack (RACK)

```yaml
location_type: rack
code: RACK
level: 8
parent_type: cage    # or hall or data_center if cage/hall levels are omitted

standard_fields:
  rack_name:              { type: string, required: true, example: "Rack A-12-03" }
  rack_code:              { type: string, required: true, example: "FRA-DC1-A-12-03" }
  rack_units:             { type: integer, required: true, example: 42 }
  rack_units_available:   { type: integer }
  power_circuits:         { type: array, items: { circuit_id, amperage, phase, redundant } }
  max_power_kw:           { type: number }
  network_top_of_rack:    { properties: { switch_model, uplink_gbps, port_count, vlan_range } }
  patch_panel_id:         { type: string }

owning_authority_default: Data Center Operations
```

### 2.9 Unit / Slot (UNIT) — optional

The Unit/Slot level is typically provider-managed; DCM does not prescribe
fields. A blade chassis slot, an HSM slot, or similar fine-grained
positioning may be tracked at this level by providers that need it.

---

## 3. Hierarchy assembly

When a consumer selects a location, DCM resolves the full ancestor chain
and assembles all location layers into the request payload in hierarchy
order (lowest precedence first):

```
Layer resolution (Core Layer phase of nine-step assembly):

  1. Country layer:    locations/country/de
  2. Region layer:     locations/region/eu-west
  3. Zone layer:       locations/az/eu-west-1a
  4. Site layer:       locations/site/fra-campus-01
  5. Data Center:      locations/dc/fra-dc1
  6. Hall layer:       locations/hall/fra-dc1-hall-a
  7. Rack layer:       locations/rack/fra-dc1-a-12-03

Assembled location context in payload:
  location.country_code: DE
  location.jurisdiction: EU/GDPR
  location.regulatory_frameworks: [GDPR, NIS2]
  location.region_code: eu-west
  location.zone_code: eu-west-1a
  location.dc_code: FRA-DC1
  location.rack_code: FRA-DC1-A-12-03
  location.sovereignty_zone: eu-west-sovereign
  location.max_data_classification: restricted
  location.certifications: [ISO 27001, SOC 2 Type II]
  ... (all ancestor fields available to policies and providers)
```

Higher-precedence (more specific) location layers override lower-precedence
ones for the same field. A Rack layer declaring
`max_data_classification: internal` overrides the DC layer's `restricted` —
the most specific declaration wins.

---

## 4. Priority band allocation

Location layers occupy a dedicated 100–900 band in the Core Layer priority space, one
hundred-band per level (Country lowest, Unit/Slot highest), so precedence always follows
specificity. The band table and allocation rules are owned by
[`placement-and-priority-bands.md`](placement-and-priority-bands.md) §2.

---

## 5. Custom location types

Organizations may insert custom types at any level via decimal-numbered
insertion. Custom types follow the same format as standard types.

Example: Navy deployment with Fleet (level 3.5) and Ship (level 4.5):

```yaml
custom_location_type:
  type_name: fleet
  code: FLEET
  display_name: "Fleet"
  level: 3.5              # inserted between Zone (3) and Site (4)
  parent_type: zone
  child_type: ship

  standard_fields:
    fleet_name:      { type: string, required: true }
    fleet_code:      { type: string, required: true }
    command_node:    { type: string }
    operating_area:  { type: string }

  owning_authority: Fleet Operations Command

---
custom_location_type:
  type_name: ship
  code: SHIP
  display_name: "Ship / Vessel"
  level: 4.5              # inserted between Site (4) and Data Center (5)
  parent_type: fleet
  child_type: data_center

  standard_fields:
    vessel_name:           { type: string, required: true }
    hull_number:           { type: string, required: true }
    vessel_class:          { type: string }
    home_port:             { type: string }
    current_location_lat:  { type: number }
    current_location_lon:  { type: number }
    connectivity_profile:  { enum: [satcom, fiber_pier, disconnected], required: true }

  owning_authority: Fleet Data Center Operations
```

Custom type instances are created and managed exactly like standard type
instances — GitOps PRs, owned by the designated authority, versioned and
immutable.

---

## 6. Layer instance format

Each location node is a Core Layer artifact stored in GitOps and registered
in DCM. See [`placement-and-priority-bands.md`](placement-and-priority-bands.md)
for the standard layer instance format, the database/query interface,
priority band allocation in detail, and lifecycle management.

---

## 7. Realization note

The specific 9-layer hierarchy (Country, Region, Zone, Site, DC, Hall,
Cage, Rack, Unit) is **DCM's canonical default**. A peer DCM realization
operating in a different domain (a Navy fleet, a hyperscale cloud, a
mining operation, a satellite network) could pick a different hierarchy:
- A satellite network might use Constellation → Orbital Plane → Satellite → Module
- A mining operation might use Region → Site → Pit → Bench → Machine

The layered-topology contract in
[udlm/topology/location-topology-layers.md](https://github.com/croadfeldt/udlm/blob/main/topology/location-topology-layers.md)
remains the wire contract; the specific layers and field definitions
above are this realization's choice.
