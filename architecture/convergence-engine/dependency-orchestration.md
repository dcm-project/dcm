---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Dependency Orchestration
Established: 2026-05-26
Maps to: udlm/lifecycle/request-dependency-graph.md
---

# Convergence Engine — Dependency Orchestration

> **Implements contracts defined in UDLM**:
> [udlm/lifecycle/request-dependency-graph.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/request-dependency-graph.md).
> UDLM defines the Request Dependency Group structure, `wait_for` values,
> field injection mechanism, `PENDING_DEPENDENCY` state contract, failure
> handling propagation policy, group timeout contract, and the relationship
> to composite service definitions. DCM operationalizes the submission,
> parsing, dispatch orchestration, state lifecycle, failure execution, and
> consumer API.

---

## 1. Request dependency graph submission and parsing

Consumers submit ad-hoc cross-request ordering via the dependency group
endpoint:

```
POST /api/v1/request-groups

{
  "group_handle": "three-tier-app-deploy",
  "on_failure": "cancel_remaining",
  "timeout": "PT2H",
  "requests": [
    { "ref": "db",
      "catalog_item_uuid": "<uuid>",
      "fields": { ... } },
    { "ref": "app",
      "catalog_item_uuid": "<uuid>",
      "fields": { ... },
      "depends_on": [
        { "ref": "db",
          "wait_for": "realized",
          "inject_fields": [
            { "from_field": "realized_fields.primary_ip",
              "to_field": "fields.db_host" }
          ]
        }
      ]
    },
    { "ref": "lb",
      "catalog_item_uuid": "<uuid>",
      "fields": { ... },
      "depends_on": [
        { "ref": "app", "wait_for": "realized",
          "inject_fields": [ ... ] }
      ]
    }
  ]
}
```

### 1.1 Parsing and validation

The Request Orchestrator parses the submission and:

1. **Validates DAG-ness** — runs a topological sort; rejects with 422 if a
   cycle is detected (`RDG-001`)
2. **Validates group size** — rejects with 422 if request count exceeds the
   profile's max_group_size
3. **Validates nesting depth** — rejects with 422 if dependency chain depth
   exceeds the profile's max_nesting_depth
4. **Validates field injection paths** — checks `from_field` paths against
   the dependency's resource type spec; per profile, validation may be
   advisory (warn), enforced (reject), or policy-gated (also pass through
   Gating Policy)
5. **Allocates entity UUIDs** for each request (so the group response can
   return entity_uuid immediately)
6. **Resolves local refs** to actual entity UUIDs in the dependency graph

On valid submission, DCM writes the group record and returns 202 with the
full request list in `PENDING_DEPENDENCY` status.

### 1.2 Quota enforcement at group submission

`PENDING_DEPENDENCY` requests count against the consumer's quota immediately
(`RDG-004`). Resources are reserved at group submission, not at dispatch
time. This prevents a consumer from submitting a 50-request group and then
finding only 30 fit in their quota when they start dispatching.

---

## 2. PENDING_DEPENDENCY state mechanics

`PENDING_DEPENDENCY` is a new status DCM adds to the Intent State lifecycle:

```
ACKNOWLEDGED → PENDING_DEPENDENCY → [dependency met] → LAYERS_ASSEMBLED → ... → REALIZED
```

PENDING_DEPENDENCY requests:

- Are visible via `GET /api/v1/requests?status=PENDING_DEPENDENCY`
- Are cancellable via `DELETE /api/v1/requests/{uuid}`
- Receive a `request.pending_dependency` event (urgency: info)
- Do NOT have independent timeouts — the group-level `timeout` governs

The Request Orchestrator maintains an in-memory dependency graph per group
plus a persistent state in `request_dependency_groups` and
`request_dependencies` tables. On every dependency state change, the
orchestrator re-evaluates dependents: when a dependency reaches its
`wait_for` state, blocked dependents transition out of `PENDING_DEPENDENCY`
and enter the standard assembly pipeline.

### 2.1 Field injection execution

When a dependency reaches its `wait_for` state and dependents have
`inject_fields`:

```
Dependency realized → Realized State written
  │
  ▼ Request Orchestrator looks up inject_fields declarations for dependents
  │   For each injection:
  │     Extract from_field path from Realized State
  │     If extraction fails: per profile, warn (advisory) or fail dispatch (enforced)
  │     Inject value at to_field path in dependent's fields
  │
  ▼ Dependent request transitions out of PENDING_DEPENDENCY
  │   Enters standard nine-step assembly with injected fields
  │
  ▼ Injected values pass through Transformation policies normally (RDG-003)
```

Injected values are not exempt from policy evaluation. A Transformation
policy that modifies `db_host` will modify the injected value just as it
would a consumer-declared one.

---

## 3. wait_for state evaluation

DCM tracks four `wait_for` states:

| Value | Triggered when |
|---|---|
| `acknowledged` | Dependency has entity_uuid (post-Request Orchestrator acknowledgment) |
| `approved` | Dependency has passed all approvals (post-approval tier evaluation) |
| `dispatched` | Dependency has been sent to its provider |
| `realized` | Dependency is fully realized (Realized State written, entity.realized event emitted) |

The Request Orchestrator subscribes to the events that mark each
transition; when any dependency state matches a dependent's `wait_for`,
the orchestrator unblocks the dependent.

`realized` is the most common and default.

---

## 4. Failure handling execution

UDLM defines two propagation policies: `cancel_remaining` and `continue`.
DCM executes:

### 4.1 cancel_remaining

```
Request fails (provider error, recovery policy DISCARD_NO_REQUEUE, etc.)
  │
  ▼ Orchestrator inspects the group's on_failure policy
  │   on_failure: cancel_remaining
  │
  ▼ For all requests in the group with status in
  │   {PENDING_DEPENDENCY, ACKNOWLEDGED}:
  │     Transition to CANCELLED
  │     failure_reason: dependency_failed
  │     Emit request.cancelled event
  │
  ▼ For already-dispatched requests: follow standard cancellation model
  │   (Section 3 in recovery-and-retry.md)
  │
  ▼ Emit request.failed for the original failure
  │   Emit request.group_failed for the group
  │
  ▼ Group status → failed
```

### 4.2 continue

The failed request is marked FAILED. Dependents that depended on it are also
marked FAILED with `failure_reason: dependency_failed`. Independent requests
in the group continue unaffected. The group transitions to `failed` once all
requests reach a terminal state.

---

## 5. Group timeout enforcement

The Request Orchestrator maintains a per-group timer. When `timeout` elapses
without all requests reaching a terminal state:

```
Group timeout reached
  │
  ▼ For all non-terminal requests in the group:
  │     Transition to FAILED
  │     failure_reason: group_timeout
  │     Emit request.failed event
  │
  ▼ Group status → failed
  │ Emit request.group_failed event
```

Group timeout is measured from group submission (not from first dispatch).
Individual requests do not have independent timeouts while in
PENDING_DEPENDENCY status — only the group timeout governs that window
(`RDG-005`).

---

## 6. Consumer API endpoints

### 6.1 Submit dependency group

```
POST /api/v1/request-groups
```

See Section 1 above for the request body schema.

Response 202:
```json
{
  "group_uuid": "<uuid>",
  "group_handle": "three-tier-app-deploy",
  "requests": [
    { "ref": "db",  "request_uuid": "<uuid>", "entity_uuid": "<uuid>", "status": "ACKNOWLEDGED" },
    { "ref": "app", "request_uuid": "<uuid>", "entity_uuid": "<uuid>", "status": "PENDING_DEPENDENCY" },
    { "ref": "lb",  "request_uuid": "<uuid>", "entity_uuid": "<uuid>", "status": "PENDING_DEPENDENCY" }
  ],
  "estimated_completion": "<ISO 8601>"
}
```

### 6.2 Add a request to an existing group

```
POST /api/v1/request-groups/{group_uuid}/members
{
  "request_uuid": "<uuid>",
  "depends_on": [ ... ]
}
```

A request may belong to at most one group (`RDG-006`); adding to a second
group returns 409 Conflict.

### 6.3 Query group status

```
GET /api/v1/request-groups/{group_uuid}

→ {
    "group_uuid": "<uuid>",
    "group_handle": "three-tier-app-deploy",
    "status": "in_progress | completed | failed | cancelled",
    "requests": [
      { "request_uuid": "<uuid>", "ref": "db",  "status": "REALIZED" },
      { "request_uuid": "<uuid>", "ref": "app", "status": "DISPATCHED" },
      { "request_uuid": "<uuid>", "ref": "lb",  "status": "PENDING_DEPENDENCY" }
    ],
    "created_at": "<ISO 8601>",
    "timeout_at": "<ISO 8601>"
  }
```

### 6.4 Cancel a group

```
DELETE /api/v1/request-groups/{group_uuid}

# Cancels all PENDING_DEPENDENCY and ACKNOWLEDGED requests in the group.
# Already-dispatched requests follow the standard cancellation model.
Response 204
```

---

## 7. New events

| Event | Urgency | Trigger |
|---|---|---|
| `request.pending_dependency` | info | Request entered PENDING_DEPENDENCY |
| `request.dependency_met` | info | Dependency reached wait_for state; request proceeding |
| `request.group_completed` | medium | All requests in group reached terminal state |
| `request.group_failed` | high | Group failed or timed out |

These events are added to the UDLM event catalog (
[udlm/contracts/event-catalog.md](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md))
under the `request.*` domain.

---

## 8. Profile-governed constraints

| Profile | Max group size | Max timeout | Field injection validation | Max nesting depth |
|---|---|---|---|---|
| minimal | 100 | P30D | advisory | 3 |
| dev | 100 | P7D | advisory | 3 |
| standard | 50 | P3D | enforced | 3 |
| prod | 25 | P1D | enforced + audited | 3 |
| fsi | 10 | PT8H | enforced + audited + policy gated | 2 |
| sovereign | 5 | PT4H | enforced + audited + policy gated | 2 |

`RDG-002` sets an absolute upper bound of 100 — profiles may set lower limits
but no profile may set higher.

---

## 9. Relationship to composite service definitions

Request dependency groups and composite service definitions solve overlapping
but distinct problems:

| | Request Dependency Group | Composite Service Definition |
|---|---|---|
| Who declares | Consumer at request time | Platform team at catalog time |
| Reusable | No — ad hoc | Yes — catalog item |
| Type constraints | None — any resources | Defined by composite spec |
| Policy governance | Standard consumer request policies | Composite Service policies (CMP-*) |
| Field injection | Consumer-declared inject_fields | Composite handles internally |
| Use case | Ad-hoc deployment ordering | Standard composite service |

When a standard composite service exists as a composite service definition,
consumers should use it. Request dependency groups are for deployments that
don't fit a predefined composite pattern.

---

## 10. Policy IDs (DCM realization)

| Policy | Rule |
|---|---|
| `RDG-001-DCM` | DCM rejects circular dependency graphs at submission time (422) via topological sort validation |
| `RDG-002-DCM` | DCM enforces a profile-governed maximum group size with absolute upper bound of 100 |
| `RDG-003-DCM` | DCM applies all active Transformation policies to injected field values; injection does not bypass policy |
| `RDG-004-DCM` | DCM counts PENDING_DEPENDENCY requests against consumer quota at group submission time |
| `RDG-005-DCM` | DCM enforces group-level timeout from group submission; individual requests have no independent timeout while PENDING_DEPENDENCY |
| `RDG-006-DCM` | DCM enforces single-group membership; attempts to add a request to a second group return 409 Conflict |
