---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Recovery and Retry
Established: 2026-05-26
Maps to: udlm/lifecycle/operational-models.md
---

# Convergence Engine — Recovery and Retry

> **Implements contracts defined in UDLM**:
> [udlm/lifecycle/operational-models.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/operational-models.md).
> UDLM defines the timeout model and state machine, the cancellation
> propagation contract, the orphan-detection contract, the discovery
> scheduling contract, the recovery policy model, and the compensation
> contract. DCM operationalizes the timeout enforcement, cancellation
> execution, orphan detection, discovery job scheduling, recovery policy
> evaluation, and compensation execution.

---

## 1. Timeout enforcement mechanisms

UDLM defines three independent timeout scopes (assembly, dispatch,
reserve_query). DCM enforces each with per-step deadlines and dedicated
recovery triggers.

### 1.1 Assembly timeout enforcement

The Request Processor runs the nine-step assembly inside a budget governed
by `assembly_timeout` (profile-governed; see table below). The total budget
is allocated across steps as proportional fractions:

| Step | Fraction of assembly_timeout |
|------|----------------------------|
| Layer Resolution | 20% |
| Layer Merge | 10% |
| Policy Evaluation (each) | 15% total; 5% per Mode 1/2; 30s per Internal policy; PT2M per External evaluator |
| Placement Engine Loop | 40% |
| Requested State Persistence | 10% |

DCM enforces sub-step deadlines via `context.WithDeadline` (Go) or equivalent
in the Request Processor. A step exceeding its sub-deadline immediately fires
`ASSEMBLY_TIMEOUT` recovery trigger regardless of overall budget remaining.

A external policy evaluation that exceeds PT2M per query causes
`ASSEMBLY_TIMEOUT` even if the overall assembly budget would tolerate it —
this prevents a single slow External Policy Evaluator from consuming the
entire assembly budget.

| Profile | assembly_timeout default |
|---|---|
| homelab | PT5M |
| dev | PT5M |
| standard | PT3M |
| prod | PT2M |
| fsi | PT2M |
| sovereign | PT2M |

### 1.2 Dispatch timeout enforcement

The Request Orchestrator starts a dispatch deadline timer when it sends the
dispatch payload to the provider. If the provider has not posted a final
Realized State callback by the deadline, `DISPATCH_TIMEOUT` fires.

| Profile | dispatch_timeout default |
|---|---|
| homelab | PT2H |
| dev | PT1H |
| standard | PT1H |
| prod | PT30M |
| fsi | PT30M |
| sovereign | PT30M |

Resource-type overrides extend the timeout for legitimately long-running
provisioning (Compute.BareMetalServer: PT4H, Storage.LargeVolume: PT2H).
Overrides are declared in the Resource Type Specification.

### 1.3 Reserve query timeout enforcement

The Placement Manager queries each eligible provider's reserve endpoint in
parallel during the placement loop, with a short per-call deadline:

| Profile | reserve_query_timeout default |
|---|---|
| homelab | PT30S |
| dev | PT30S |
| standard | PT10S |
| prod | PT5S |
| fsi | PT5S |
| sovereign | PT10S |

A reserve query timeout does NOT immediately fire a recovery trigger — the
Placement Manager skips the timed-out provider and continues the placement
loop with remaining candidates. Only when ALL candidates have timed out or
been rejected does `RESERVE_QUERY_ALL_EXHAUSTED` fire.

### 1.4 Timeout audit records

Every timeout writes an audit record:

```yaml
audit_record:
  action: ASSEMBLY_TIMEOUT | DISPATCH_TIMEOUT | RESERVE_QUERY_TIMEOUT |
          RESERVE_QUERY_ALL_EXHAUSTED
  actor:
    type: system
    system_actor:
      component: request_processor | request_orchestrator | placement_manager
      trigger: timeout
  entity_uuid: <uuid>
  details:
    timeout_duration: <configured>
    actual_elapsed: <ISO 8601 duration>
    step_at_timeout: <step name>
    recovery_policy_triggered: <policy uuid>
```

---

## 2. Cancellation execution and cleanup

UDLM defines the three cancellation scenarios (pre-dispatch, post-dispatch
not-yet-started, mid-execution) and the propagation model. DCM enforces:

### 2.1 Pre-dispatch cancellation (Scenario 1)

Consumer submits `DELETE /api/v1/requests/{uuid}` while entity is in
pre-DISPATCHED state. DCM:

1. Marks the Intent State record CANCELLED
2. Halts assembly immediately (cancels the in-flight Request Processor context)
3. Transitions entity to CANCELLED (terminal)
4. Writes `REQUEST_CANCELLED` audit record
5. No recovery policy triggered (clean cancel)
6. Returns `200 OK` with `{ "status": "CANCELLED" }`

### 2.2 Post-dispatch, provider not yet started (Scenario 2)

DCM sends cancellation payload to the provider's declared `cancellation_endpoint`
(if provider declares `supports_cancellation: true`). The provider acknowledges;
DCM transitions entity to CANCELLED. Response is `202 Accepted` while DCM
awaits provider confirmation; consumer polls status for the final CANCELLED.

### 2.3 Mid-execution cancellation (Scenario 3)

DCM consults `provider.supports_cancellation` and `provider.cancellation_supported_during`:

- If provider supports cancellation during PROVISIONING: DCM sends the cancellation
  payload; provider attempts rollback. Outcomes:
  - Rollback clean → entity → CANCELLED (terminal)
  - Rollback partial → fires `CANCELLATION_FAILED` recovery trigger
  - No response → fires `CANCELLATION_FAILED` recovery trigger
- If provider does NOT support cancellation: entity enters `CANCEL_PENDING`;
  DCM waits for provider to complete normally; on completion, fires
  `LATE_RESPONSE_RECEIVED` (action typically `DISCARD_AND_REQUEUE` in
  cancellation context)

### 2.4 Cancellation payload

```json
{
  "cancellation_uuid": "<uuid>",
  "entity_uuid": "<uuid>",
  "requested_state_uuid": "<uuid>",
  "reason": "consumer_requested | timeout | policy_triggered",
  "requested_at": "<ISO 8601>",
  "best_effort": true
}
```

`best_effort: true` is always set — DCM never guarantees cancellation success.

---

## 3. Orphan detection implementation

When cleanup cannot be guaranteed, DCM runs an orphan detection pass to find
provider resources with no corresponding DCM Realized State record.

### 3.1 Triggers

DCM fires orphan detection on:

- Dispatch timeout with cancellation sent
- Cancellation failed
- Compensation failed
- `DISCARD_NO_REQUEUE` action taken
- Manual platform admin trigger

### 3.2 Query implementation

The Orphan Detection Service queries the provider's discovery endpoint with
narrow criteria:

```yaml
orphan_detection_query:
  provider_uuid: <uuid>
  time_window:
    from: <request_dispatched_at - PT5M>
    to: <now>
  match_criteria:
    resource_type: <from Requested State>
    characteristics:
      name_pattern: <if name was declared>
      size_class: <cpu/memory range>
      tags: <tags from request>
  exclude:
    known_realized_state_uuids: [<list>]
```

DCM compares discovery results against known Realized State entities;
unmatched provider-side entities are flagged as orphan candidates.

### 3.3 Orphan candidate lifecycle

Orphan candidates enter the platform admin review queue:

```yaml
orphan_candidate:
  orphan_candidate_uuid: <uuid>
  suspected_request_uuid: <uuid>
  provider_entity_id: <string>
  provider_uuid: <uuid>
  discovered_at: <ISO 8601>
  characteristics: { ... }
  status: under_review | confirmed_orphan | adopted | false_positive
  resolution:
    action: manual_decommission | adopt_into_dcm | mark_false_positive
    resolved_by: <actor_uuid>
    resolved_at: <ISO 8601>
```

Orphan candidates surface in the Platform Admin dashboard and generate a
notification with `urgency: high`.

---

## 4. Discovery job scheduling and execution

The Discovery Scheduler maintains a priority queue and dispatches discovery
jobs to provider discovery endpoints. UDLM defines the three trigger types
(scheduled / event / on-demand); DCM implements the queue and dispatcher.

### 4.1 Priority queue

```
Priority order:
  1. Critical  — COMPENSATION_FAILED orphan detection, sovereignty violation
  2. High      — on-demand from platform admin, event-triggered (provider.degraded)
  3. Standard  — event-triggered (entity.realized, drift.resolved)
  4. Background — scheduled discovery passes
```

Queue depth is bounded per profile. When the queue is full, new Background
items are dropped (with a log entry). Standard and above are never dropped —
they wait.

### 4.2 Scheduled discovery

Resource Type Specifications declare `discovery_schedule.default_interval`,
overridable per profile. The Discovery Scheduler runs each schedule via cron
(LISTEN/NOTIFY-based timer + work-stealing across Discovery Service replicas
for HA).

### 4.3 Event-triggered discovery

Specific DCM events automatically enqueue an out-of-cycle discovery:

| Event | Delay | Scope | Reason |
|---|---|---|---|
| `entity.realized` | PT30S | this_entity | Confirm realization matches Requested State |
| `drift.resolved` | PT60S | this_entity | Confirm remediation took effect |
| `provider_update.approved` | PT30S | this_entity | Confirm provider update reflected |
| `provider.degraded` | PT0S | all_entities_on_provider | Assess impact |
| `TIMEOUT_PENDING` | PT5M | this_entity | Orphan detection after timeout |
| `COMPENSATION_FAILED` | PT0S | this_entity_and_dependents | Find orphans |

### 4.4 On-demand discovery API

```
POST /api/v1/admin/discovery:trigger
{
  "scope": "entity | resource_type | provider | tenant",
  "entity_uuid": "<uuid>",
  "resource_type": "<fqn>",
  "provider_uuid": "<uuid>",
  "tenant_uuid": "<uuid>",
  "reason": "incident investigation",
  "priority": "high"
}
```

### 4.5 Discovery audit

Every discovery cycle writes an audit record:

```yaml
audit_record:
  action: DISCOVERY_CYCLE_COMPLETED | DISCOVERY_CYCLE_FAILED
  actor:
    type: system
    system_actor:
      component: discovery_scheduler
      trigger: scheduled | event_triggered | on_demand
      trigger_event_uuid: <uuid|null>
  entity_uuid: <uuid|null>
  details:
    entities_discovered: 47
    new_entities_found: 2
    duration: PT8S
```

---

## 5. Recovery policy evaluation

UDLM defines Recovery Policies as a formal policy type alongside Validation
and Transformation. DCM evaluates Recovery Policies via the same
Policy Manager. The evaluation precedence is the same as all other policies:

```
1. Resource-type-level override (most specific)
2. Tenant-level override
3. Active profile's recovery posture group
4. System default (recovery-automated-reconciliation)

First matching policy for the trigger condition wins.
Multiple recovery policies for the same trigger at the same domain level
→ policy conflict; CONFLICT_ERROR at ingestion; platform admin notified.
```

### 5.1 Built-in recovery profile groups

DCM ships four built-in recovery profile groups (declared as Policy Groups
with `concern_type: recovery_posture`):

| Group | Posture |
|---|---|
| `recovery-automated-reconciliation` | Let drift detection converge; default for homelab/dev/standard |
| `recovery-discard-and-requeue` | On ambiguity, clean up and start fresh — prioritize consistency |
| `recovery-notify-and-wait` | Never act automatically — always notify and wait for human; default for prod/fsi/sovereign |
| `recovery-aggressive-retry` | Retry everything before giving up |

Profile bindings:

```yaml
profile_recovery_defaults:
  minimal:    recovery-automated-reconciliation
  dev:        recovery-automated-reconciliation
  standard:   recovery-automated-reconciliation
  prod:       recovery-notify-and-wait
  fsi:        recovery-notify-and-wait
  sovereign:  recovery-notify-and-wait
```

Tenant and resource-type overrides are permitted; resource-type overrides
the most specific.

### 5.2 NOTIFY_AND_WAIT consumer interface

When a recovery policy fires `NOTIFY_AND_WAIT`, DCM sends a notification to
the entity owner with a time-bounded decision interface:

```
GET /api/v1/resources/{entity_uuid}/recovery-decisions
→ {
    "recovery_decision_uuid": "<uuid>",
    "trigger": "DISPATCH_TIMEOUT",
    "entity_uuid": "<uuid>",
    "deadline": "<ISO 8601>",
    "available_actions": [
      { "action": "DRIFT_RECONCILE", "description": "..." },
      { "action": "DISCARD_AND_REQUEUE", "description": "..." },
      { "action": "DISCARD_NO_REQUEUE", "description": "..." }
    ]
  }

POST /api/v1/resources/{entity_uuid}/recovery-decisions/{recovery_decision_uuid}
{
  "action": "DISCARD_AND_REQUEUE",
  "reason": "Provider was known to be degraded at time of timeout"
}
```

If the deadline passes without resolution, the configured
`on_deadline_exceeded` action fires automatically.

---

## 6. Compensation execution

UDLM defines the composite service compensation contract (reverse-dependency
ordering, declarative per-component compensation behavior). DCM executes:

### 6.1 Reverse-order execution

When a composite service partially fails:

```
Successful so far: vm ✓, ip ✓
Failed: dns ✗ (atomic)

Compensation triggered:
  Step 1: decommission vm (compensation_order: 3 → runs first in reverse)
  Step 2: release ip allocation (compensation_order: 1 → runs second in reverse)
  Compound entity → FAILED (terminal for this request cycle)
```

The Composite Service Orchestrator maintains the dependency graph from the
composite service spec and walks it in reverse for compensation.

### 6.2 Compensation failure

If a compensation step itself fails:

1. Entity enters `COMPENSATION_FAILED` state
2. `COMPENSATION_FAILED` recovery trigger fires (default action: `ESCALATE`)
3. Orphan detection triggered immediately, scoped to provider + entity
   characteristics
4. ORPHAN_CANDIDATE record created
5. Platform admin notified

---

## 7. New lifecycle states (DCM-internal)

DCM adds five lifecycle states to operationalize the UDLM recovery contracts:

| State | Meaning | Recovery trigger |
|---|---|---|
| `TIMEOUT_PENDING` | Dispatch timeout fired; cancellation sent; awaiting outcome | `DISPATCH_TIMEOUT` |
| `LATE_REALIZATION_PENDING` | Provider responded after timeout; NOTIFY_AND_WAIT active | `LATE_RESPONSE_RECEIVED` |
| `INDETERMINATE_REALIZATION` | State ambiguous; drift detection resolving | — |
| `COMPENSATION_IN_PROGRESS` | Composite service rollback underway | — |
| `COMPENSATION_FAILED` | Rollback itself failed; orphaned resources possible | `COMPENSATION_FAILED` |

These states are DCM-internal — they describe the recovery pipeline mechanics
and are mapped to UDLM lifecycle states (typically as sub-states of
PROVISIONING or FAILED) for external interop.

---

## 8. Policy IDs

DCM-side policy IDs governing recovery and retry execution:

| Policy | Rule |
|---|---|
| `OPS-010-DCM` | DCM enforces assembly, dispatch, and reserve-query timeouts independently with profile-governed defaults and resource-type overrides |
| `OPS-011-DCM` | DCM cancellation is always best-effort; outcomes flow through Recovery Policy evaluation |
| `OPS-014-DCM` | DCM evaluates Recovery Policies via the same Policy Manager as all other policy types; same shadow mode, same audit |
| `OPS-017-DCM` | DCM runs composite compensation in reverse dependency order; compensation failure fires immediate orphan detection |
| `OPS-019-DCM` | DCM's NOTIFY_AND_WAIT actions carry a deadline; if exceeded, the configured `on_deadline_exceeded` action fires automatically |
