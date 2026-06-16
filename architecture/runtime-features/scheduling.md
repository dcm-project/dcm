---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Request Scheduling
Established: 2026-05-26
Maps to: udlm/lifecycle/scheduled-requests.md
---

# Request Scheduling

> **Implements contracts defined in UDLM**:
> [udlm/lifecycle/scheduled-requests.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/scheduled-requests.md).
> UDLM defines the scheduling model (immediate / at / window / recurring),
> the SCHEDULED request state contract, the maintenance window coordination
> contract, and the deadline enforcement contract. DCM operationalizes the
> Request Scheduler component, deferred request lifecycle management,
> maintenance window scheduling logic, deadline evaluation and timeout
> enforcement, consumer API additions, new events, and profile-governed
> scheduling constraints.

---

## 1. Request Scheduler component

The Request Scheduler is a DCM control plane component (an internal function
of the Request Orchestrator per
[`../control-plane/components.md`](../control-plane/components.md), Section
5.3) responsible for:

- Maintaining a priority queue of SCHEDULED requests ordered by `not_before`
- Polling the queue; dispatching requests when `not_before` is reached
- Checking `not_after` deadlines; cancelling expired requests
- Listening for `maintenance_window` events to trigger window-scheduled
  requests
- On dispatch: handing off to Request Orchestrator (same path as immediate
  requests)
- Writing SCHEDULED status updates to Intent State
- Publishing `request.scheduled` and `request.schedule_cancelled` events

### 1.1 Implementation choice

DCM implements the Request Scheduler as a PostgreSQL-backed cron worker per
the
[`../persistence/postgres-implementation.md`](../persistence/postgres-implementation.md)
infrastructure. A `scheduled_requests` table maintains the queue; a worker
polls every PT15S for ripe requests; HA via leader election (PostgreSQL
advisory locks or a simple lease pattern).

```sql
CREATE TABLE scheduled_requests (
    request_uuid      UUID PRIMARY KEY,
    entity_uuid       UUID NOT NULL,
    tenant_uuid       UUID NOT NULL REFERENCES tenants(tenant_uuid),
    schedule_dispatch VARCHAR(16) NOT NULL,    -- at | window | recurring
    not_before        TIMESTAMPTZ NOT NULL,
    not_after         TIMESTAMPTZ,
    window_uuid       UUID,
    cron_expression   TEXT,
    max_occurrences   INTEGER,
    occurrences_so_far INTEGER DEFAULT 0,
    status            VARCHAR(16) NOT NULL DEFAULT 'SCHEDULED',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scheduled_ripe ON scheduled_requests(not_before, status)
    WHERE status = 'SCHEDULED';
```

---

## 2. Deferred request lifecycle management

A scheduled request moves through the four states with one additional
intermediate status. DCM implements:

```
Submit with schedule.dispatch: at
  ▼ ACKNOWLEDGED (Intent State created; entity_uuid assigned)
  ▼ Policy evaluation at declaration time
  │   GateKeeper policies run immediately (fail-fast)
  │   If rejected: request fails before entering queue
  │   If approved: request enters scheduled queue
  ▼ SCHEDULED (new status within Intent State)
  │   Stored in Request Scheduler queue
  │   Visible via GET /api/v1/requests/{uuid}/status
  │   Cancellable: DELETE /api/v1/requests/{uuid}
  ▼ [at not_before] → Policy re-evaluation at dispatch
  │   Transformation policies re-run (data may have changed)
  │   GateKeeper re-evaluation with current data
  │   If still approved: proceed to LAYERS_ASSEMBLED → dispatch
  │   If rejected at dispatch: FAILED with failure_reason: schedule_policy_rejection
  ▼ DISPATCHED → REALIZED (normal pipeline)
```

### 2.1 Dual policy evaluation (SCH-001)

Policies evaluate twice intentionally:

- **At declaration time** — catches obvious rejections early (fail fast)
- **At dispatch time** — catches changes since declaration (quota exhausted,
  new compliance policy activated, actor role changed, etc.)

Dispatch-time evaluation uses the **current** policy set, not the one in
effect at declaration. SCH-003: requests that fail dispatch-time policy
re-evaluation enter FAILED state with `failure_reason: schedule_policy_rejection`.
The consumer receives a `request.failed` event with the rejection detail.

---

## 3. Maintenance window scheduling logic

Maintenance Windows are reusable schedule artifacts referenced by scheduled
requests. DCM implements:

```yaml
maintenance_window:
  window_uuid: <uuid>
  window_handle: "weekly-sunday-0200-utc"
  description: "Weekly maintenance window — low traffic period"

  cron: "0 2 * * 0"           # every Sunday at 02:00 UTC
  duration: PT2H              # window is 2 hours long

  tenant_uuid: <uuid | null>  # null = platform-wide
  resource_types: [<fqn>]     # empty = all resource types

  status: active | suspended
  approved_by: <actor_uuid>
  effective_from: <ISO 8601>

  created_at: <ISO 8601>
  created_by: <actor_uuid>
```

### 3.1 Window-scheduled request flow

```
Consumer submits request with schedule.dispatch: window, window_id: <uuid>
  ▼ Request validates window exists, is active, is in scope (tenant + resource type)
  ▼ Request enters SCHEDULED with not_before = next window start
  ▼ Window scheduler periodically computes upcoming window starts via cron
  ▼ At window start: all queued requests for the window dispatch in batch
  ▼ Within the window's duration, requests dispatch normally
  ▼ Outside window duration, queued requests wait for next window
```

### 3.2 Maintenance Window API

```
# Platform admin operations
POST   /api/v1/admin/maintenance-windows
GET    /api/v1/admin/maintenance-windows
GET    /api/v1/admin/maintenance-windows/{window_uuid}
PATCH  /api/v1/admin/maintenance-windows/{window_uuid}
DELETE /api/v1/admin/maintenance-windows/{window_uuid}

# Consumer operations
GET    /api/v1/maintenance-windows          # list visible to consumer
GET    /api/v1/maintenance-windows/{uuid}   # describe a specific window
```

Window approval tier varies by profile:

| Profile | Window approval tier |
|---|---|
| minimal | auto |
| dev | auto |
| standard | reviewed |
| prod | reviewed |
| fsi | verified |
| sovereign | authorized |

---

## 4. Deadline evaluation and timeout enforcement

### 4.1 not_before enforcement

DCM validates `not_before` is a future timestamp at submission. Past
timestamps are rejected with 422 (SCH-002).

### 4.2 not_after deadline enforcement

If `not_after` is set and the deadline passes before dispatch:

```
not_after reached without dispatch
  ▼ Request status → FAILED
  │   failure_reason: schedule_deadline_missed
  ▼ request.failed event published (urgency: medium)
  ▼ Consumer notified
  ▼ Intent State marked terminal — no further retries (SCH-005)
```

The deadline worker scans every PT15S:

```sql
SELECT request_uuid FROM scheduled_requests
WHERE status = 'SCHEDULED'
  AND not_after IS NOT NULL
  AND not_after < NOW()
```

For each match: transition to FAILED, emit `request.failed`, remove from
queue.

### 4.3 Recurring schedule enforcement

```yaml
schedule:
  dispatch: recurring
  cron: "0 2 * * 0"
  max_occurrences: 4
  not_after: "2026-12-31T00:00:00Z"
```

For recurring schedules, DCM:

1. Computes next ripe time via cron
2. Dispatches; increments `occurrences_so_far`
3. If `occurrences_so_far == max_occurrences`: marks terminal
4. If `not_after` exceeded: marks terminal
5. Otherwise: re-queues with next ripe time

---

## 5. Consumer API additions

### 5.1 Submit scheduled request

Scheduling is an optional `schedule` field on the existing request endpoint:

```
POST /api/v1/requests
{
  "catalog_item_uuid": "<uuid>",
  "fields": { ... },
  "schedule": {
    "dispatch": "at",
    "not_before": "2026-04-01T02:00:00Z",
    "not_after": "2026-04-01T06:00:00Z"
  }
}

Response 202:
{
  "request_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "status": "SCHEDULED",
  "scheduled_dispatch_at": "2026-04-01T02:00:00Z",
  "schedule_deadline": "2026-04-01T06:00:00Z"
}
```

### 5.2 List scheduled requests

```
GET /api/v1/requests?status=SCHEDULED
```

### 5.3 Cancel scheduled request

Existing endpoint — no new endpoint required:

```
DELETE /api/v1/requests/{request_uuid}

# Works on SCHEDULED requests; moves status to CANCELLED
# Returns 409 if request is already dispatched (past SCHEDULED)

Response 204 No Content
```

---

## 6. New events

| Event | Urgency | Trigger |
|---|---|---|
| `request.scheduled` | info | Request entered SCHEDULED queue |
| `request.schedule_cancelled` | low | Scheduled request cancelled before dispatch |
| `request.schedule_deadline_missed` | medium | not_after passed without dispatch |

These add to the `request.*` domain in
[udlm/contracts/event-catalog.md](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md).

---

## 7. Profile-governed scheduling constraints

DCM enforces scheduling constraints per profile to reflect operational risk
tolerance:

| Profile | Max scheduling horizon | Max concurrent scheduled/actor | Recurring max frequency | Window approval tier |
|---|---|---|---|---|
| `minimal` | P365D | unlimited | PT1H | auto |
| `dev` | P365D | 50 | PT1H | auto |
| `standard` | P90D | 20 | PT4H | reviewed |
| `prod` | P30D | 10 | PT12H | reviewed |
| `fsi` | P14D | 5 | PT24H | verified |
| `sovereign` | P7D | 3 | PT24H | authorized |

- **Max scheduling horizon:** how far in the future `not_before` may be set;
  beyond → reject with 422
- **Max concurrent scheduled/actor:** how many SCHEDULED requests per actor;
  exceeded → 429
- **Recurring max frequency:** minimum interval between recurring dispatches;
  cron more frequent than this → reject
- **Window approval tier:** authority tier required to create or modify a
  Maintenance Window

---

## 8. What operations support scheduling

| Operation | Scheduling supported | Notes |
|---|---|---|
| Resource creation | ✅ | Full scheduling model |
| Resource update (PATCH) | ✅ | Full scheduling model |
| Suspend | ✅ | Full scheduling model |
| Resume | ✅ | Full scheduling model |
| Decommission | ✅ | Full scheduling model; `not_after` recommended |
| Rehydration | ✅ | Full scheduling model |
| TTL extension | ✅ | Full scheduling model |
| Discovery trigger | ❌ | Handled by Discovery Scheduler (see [`../convergence-engine/recovery-and-retry.md` §4](../convergence-engine/recovery-and-retry.md)) |

---

## 9. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `SCH-001-DCM` | DCM evaluates GateKeeper policies twice on scheduled requests: at declaration (fail-fast) and at dispatch (current state). Both must pass |
| `SCH-002-DCM` | DCM rejects scheduled requests with a past not_before (422) |
| `SCH-003-DCM` | DCM transitions requests failing dispatch-time policy re-evaluation to FAILED with failure_reason: schedule_policy_rejection |
| `SCH-004-DCM` | DCM permits cancellation of SCHEDULED requests at any time before dispatch via DELETE /api/v1/requests/{uuid} |
| `SCH-005-DCM` | DCM transitions requests with exceeded not_after to FAILED with failure_reason: schedule_deadline_missed; no retry |
| `SCH-006-DCM` | DCM treats Maintenance Windows as platform-level or tenant-scoped artifacts subject to standard DCM artifact lifecycle |
