---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Ingestion Engine
Established: 2026-05-26
Maps to: udlm/lifecycle/ingestion-model.md, udlm/contracts/information-providers-advanced.md
---

# Ingestion Engine

> **Implements contracts defined in UDLM**:
> [udlm/lifecycle/ingestion-model.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/ingestion-model.md),
> [udlm/contracts/information-providers-advanced.md](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers-advanced.md).
> UDLM defines the brownfield ingestion problem statement, the ingest →
> enrich → promote pattern, the transitional tenant mechanism, the
> auto-assignment signal contract, the ingestion lifecycle states, the
> confidence scoring contract, and the authority/priority declaration
> contract. DCM operationalizes the engine implementation, info provider
> integration, enrichment policy enforcement, transitional tenant execution,
> ingestion scheduling, conflict detection and resolution, write-back
> implementation, air-gapped verification, and provider priority/fallback.

---

## 1. Ingestion engine implementation

The Ingestion Engine is a DCM control plane service that drives the
ingest → enrich → promote pipeline. It owns:

- The Discovery Service callback handler (incoming brownfield discoveries)
- The Manual Import API (`POST /api/v1/admin/ingest`)
- The ingestion record store (`ingestion_records` table)
- The transitional tenant residency monitor
- The enrichment policy evaluator (delegated to Policy Manager)
- The promotion gate

The engine is event-driven via `pipeline_events`: a new Discovered State
record without a matching Realized State triggers an
`ingestion.candidate_identified` event; the engine subscribes and creates
the ingestion record.

---

## 2. Information Provider integration

The engine supports two integration modes per Information Provider:

| Mode | When | DCM Behavior |
|---|---|---|
| **Polling** | Provider does not support push | Engine polls provider's discovery endpoint on the schedule declared in the provider registration; each poll cycle's results are ingested through the standard pipeline |
| **Webhook (push)** | Provider supports `POST /api/v1/provider/ingest` | Provider pushes new data on its own cadence; DCM authenticates via the provider callback credential (see [`../credentials-and-auth/provider-callback.md`](../credentials-and-auth/provider-callback.md)) |

Polling implementation: a per-provider goroutine (or equivalent worker) runs
the declared interval; each tick fires the provider's discovery endpoint with
the standard query payload. The Discovery Service shares the same scheduler
infrastructure used for Realized State drift detection (see
[`../convergence-engine/recovery-and-retry.md` §4](../convergence-engine/recovery-and-retry.md)).

Push implementation: providers POST to the provider callback API; the
Provider Callback API validates mTLS + interaction credential per
[`../credentials-and-auth/provider-callback.md`](../credentials-and-auth/provider-callback.md),
then routes the payload to the engine.

---

## 3. Enrichment policy enforcement

UDLM defines auto-assignment signal priority (explicit tag → resource group →
request history → network/location → naming → provider context → none). DCM
enforces the priority order via a Transformation policy that evaluates against
each candidate signal and produces the assignment decision.

### 3.1 Signal evaluation algorithm

```
For each newly ingested entity:
  ▼ Run the signal priority chain (declared in platform layer)
  │   For each signal in priority order:
  │     Evaluate signal against entity metadata
  │     If signal produces an unambiguous tenant_uuid → use it
  │     Else continue to next signal
  │
  ▼ If two or more signals produce conflicting tenant_uuids:
  │   Higher-priority signal wins
  │   Record conflict in ingestion_record (ingestion_confidence: medium regardless)
  │
  ▼ If no signal produces a result:
  │   Assign to __transitional__ tenant
  │   ingestion_confidence: low
  │
  ▼ Write ingestion_record with assignment_method, assignment_signal,
    and ingestion_confidence
```

### 3.2 Profile-driven enrichment policy

Profiles control:

- Whether auto-assignment is permitted (always permitted; what varies is the
  confidence threshold for auto-promotion)
- Which signals are enabled (organizations can disable signals via platform layer)
- Whether enrichment must complete within a deadline before escalation

Per-profile signal priority is declared in
`platform/ingestion/signal-priority` (per `ING-012`). `explicit_tenant_tag`
always has highest priority; `default_tenant` always has lowest; middle
signals are reorderable.

---

## 4. Transitional tenant execution

The `__transitional__` tenant is a DCM system-managed artifact created at
bootstrap. The engine ensures:

- It cannot be deleted (ING-003)
- It cannot be renamed (ING-003)
- It cannot be used for new resource provisioning (only ingestion assignment)
- Entities in it are fully auditable and visible

### 4.1 Residency monitor

A background worker scans the transitional tenant on the cadence declared in
its governance config (default daily):

```
For each entity in __transitional__:
  ▼ age = now - ingestion_timestamp
  ▼ If age > max_residency_days (default 90):
  │   Apply on_max_residency action:
  │     escalate → notification to platform admin
  │     block    → entity flagged; no further enrichment until resolved
  │     alert    → notification to ingestion administrator
```

The action is configurable per deployment. `fsi`/`sovereign` profiles default
to `block` and shorter `max_residency_days`.

---

## 5. Ingestion scheduling

The engine maintains a priority queue for ingestion work (separate from the
Discovery Scheduler's queue, but using the same infrastructure):

```
Priority order:
  1. Critical  — security-relevant brownfield (unknown resource at sensitive provider)
  2. High      — manual import + active enrichment requests
  3. Standard  — scheduled brownfield discovery passes
  4. Background — bulk migration ingestion
```

Bulk promotion is supported with profile-governed batch sizes and rollback
windows (per `ING-013`):

| Profile | Max per Bulk | Approval Required |
|---|---|---|
| minimal | Unlimited | No |
| dev | 1000 | No |
| standard | 500 | Recommended |
| prod | 100 | Yes |
| fsi | 50 | Yes + dual approval |
| sovereign | 25 | Yes + dual approval |

A single `BULK_PROMOTE` audit record covers each bulk action with the full
member list.

---

## 6. Conflict detection and resolution

UDLM defines the confidence descriptor model and the authority declaration
contract. DCM performs ingestion-time conflict detection per
[udlm/contracts/information-providers-advanced.md](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers-advanced.md):

```
Information Provider push event received
  │
  ▼ 1. Schema validation against provider's declared schema version
  │   Strict reject on violation OR lenient warn per policy
  │
  ▼ 2. Authority scope check
  │   Is provider authorized to assert these fields on this entity?
  │   Reject unauthorized field assertions (INF-001)
  │
  ▼ 3. Confidence score computation
  │   Per-field score using standard formula (UDLM Section 2.5)
  │
  ▼ 4. Conflict detection
  │   For each field:
  │     Same value across providers → corroboration (confidence multiplier 1.15)
  │     Different value → conflict record created
  │     No existing value → new assertion (accept)
  │
  ▼ 5. Conflict resolution policy
  │   Apply declared strategy:
  │     higher_authority_wins   → use higher authority_level value
  │     higher_confidence_wins  → use higher computed score
  │     higher_priority_wins    → use value from higher-priority provider
  │     escalate                → conflict record; existing value retained; human resolves
  │     merge                   → combine values (array/set fields only)
  │
  ▼ 6. Entity record update with full field provenance
  │
  ▼ 7. INGEST audit record with all field changes, conflicts, scores
```

### 6.1 Authority scope conflict at registration

When a new provider declares authority over a field already claimed at the
same or higher level:

```
DCM checks for existing primary authority on the field
  │
  ├── No existing primary → register; no conflict
  │
  └── Existing primary provider found:
        Create authority_scope_conflict_record
        Action required:
          - Demote new to secondary, or
          - Demote existing to secondary, or
          - Declare explicit resolution strategy
        Provider registration blocked until resolved
```

---

## 7. Write-back implementation

Information Providers may declare write-back capability. DCM triggers
write-back only via policy — never automatically (`INF-002`).

```yaml
# Policy that triggers write-back:
policy:
  type: transformation
  placement_phase: post
  rule: >
    If action IN [CREATE, STATE_TRANSITION, DELETE]
    AND resource_type == Compute.VirtualMachine
    THEN trigger_write_back:
      provider_uuid: <cmdb-uuid>
      operation: update
      fields: [hostname, ip_address, lifecycle_state, owner_business_unit]
```

DCM's write-back executor:

1. Resolves the provider's write-back endpoint from its registration
2. Issues a `dcm_interaction` credential scoped to the provider + operation
3. Sends the write-back payload (only fields declared in the policy)
4. Records an `ENRICH` audit record with `source_type: information_provider_write_back`
5. On failure: retries per the policy's retry config, then logs and notifies
   the policy owner

---

## 8. Air-gapped verification

UDLM defines three modes for Information Provider verification in air-gapped
environments. DCM implements all three:

### 8.1 Mode 1 — Pre-verified signed bundle (recommended)

A signed YAML bundle is generated on an online workstation, transferred via
approved secure channel, and imported on the air-gapped DCM:

```
DCM bundle import endpoint receives air_gapped_provider_bundle
  │
  ▼ Verify signature against organization's pre-installed public key
  ▼ Verify bundle expires_at not exceeded
  ▼ Extract provider_registration, tls_certificate_chain, schema_definitions
  ▼ Submit through standard provider registration flow with bundle attribution
  ▼ Provider is registered without external internet contact
```

### 8.2 Mode 2 — Internal mTLS (internal providers)

Providers internal to the organization register with
`air_gap_mode: internal_only`. DCM validates using internal mTLS certificates
issued by the organization's internal CA (FreeIPA CA or equivalent). No
external connectivity required.

### 8.3 Mode 3 — Periodic online re-verification

For environments air-gapped most of the time but with occasional connectivity
windows:

```yaml
provider_verification:
  mode: periodic_online
  cache_ttl: P30D
  on_cache_expiry:
    minimal: continue
    dev: alert
    standard: alert
    prod: suspend
    fsi: suspend
    sovereign: suspend
```

DCM's verification scheduler attempts a re-verification at the cache_ttl;
on failure, applies the profile's expiry behavior.

---

## 9. Provider priority and fallback logic

When multiple Information Providers assert values for the same field and a
priority must be resolved, DCM applies (per `INF-007`):

```
1. Authority level (primary > secondary > advisory)
2. Within same authority level: provider priority (numeric, higher wins)
3. If still tied: most recent timestamp wins
```

On provider degradation or suspension (trust score < 60 per `INF-009`):

- `degraded`: confidence multiplier reduces to 0.75; provider continues to
  serve data but with reduced effective confidence
- `suspended`: provider stops accepting new pushes; existing data remains
  but ages out per freshness multipliers; fallback providers in the priority
  chain take over

Fallback registration is via the provider's registration:

```yaml
information_provider_registration:
  authority_level: primary
  fallback_providers:
    - provider_uuid: <secondary-uuid>
      activate_when: this_provider_suspended | this_provider_degraded
```

---

## 10. Confidence aggregation API (DCM implementation of INF-010)

DCM exposes the per-entity confidence aggregation endpoint:

```
GET /api/v1/entities/{uuid}/confidence
→ {
    "entity_uuid": "<uuid>",
    "overall_band": "high",                       # lowest band across all fields
    "field_summaries": [
      { "field": "owner_business_unit", "band": "high", "score": 86, ... },
      { "field": "cost_center", "band": "medium", "score": 54, "corroboration": "contested" }
    ],
    "lowest_confidence_fields": [
      { "field": "cost_center", "reason": "contested" },
      { "field": "asset_tag", "reason": "stale" }
    ],
    "computed_at": "<ISO 8601>"
  }
```

Overall band reflects the lowest field band (conservative). Aggregation is
computed on demand — never stored (freshness changes continuously).

---

## 11. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `ING-001-DCM` | DCM assigns every ingested entity to exactly one Tenant (real or __transitional__) before it is eligible for new requests |
| `ING-002-DCM` | DCM blocks PENDING/ENRICHING entities from being parent for new allocated resource claims |
| `ING-003-DCM` | DCM's __transitional__ tenant is system-managed; cannot be deleted, renamed, or used for new provisioning |
| `ING-004-DCM` | Every DCM-ingested entity carries an ingestion_record in its provenance chain |
| `ING-005-DCM` | DCM fires escalation action on entities exceeding max_residency_days in __transitional__ |
| `ING-006-DCM` | DCM requires explicit actor authorization before promoting brownfield entities to PROMOTED state |
| `ING-007-DCM` | At promotion, DCM promotes the Discovered State record to Realized State |
