---
Document Status: 📋 Draft — Initial Specification
Document Type: Architecture Reference — Convergence Engine
Established: 2026-05-26
Maps to: UDLM four-states contract, capability discovery contract
---

# Convergence Engine — Overview

> **Implements contracts defined in UDLM**:
> [udlm/foundations/four-states.md](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md),
> [udlm/contracts/provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md),
> [udlm/contracts/event-catalog.md](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md),
> [udlm/contracts/capability-discovery.md](https://github.com/croadfeldt/udlm/blob/main/contracts/capability-discovery.md).

The convergence engine is the heart of DCM. It walks data through the four
UDLM states — **intent → requested → realized → discovered** — and
continuously reconciles realized state against intent. Everything else in
DCM exists to support this loop.

---

## 1. What the engine does

UDLM defines the four states and the allowed transitions between them. UDLM
does **not** prescribe how a realization drives those transitions. The DCM
convergence engine is one specific answer:

1. **Accepts intent** (via the API gateway from any ingress: API, GitOps,
   CLI, message bus, scheduled trigger). Writes an Intent State record.
2. **Assembles a Requested State** by running the nine-step assembly:
   layer resolution → layer merge → policy evaluation → placement → score →
   approval routing → Requested State persistence → dispatch preparation →
   audit emission.
3. **Dispatches** to the selected provider with a scoped, short-lived
   `dcm_interaction` credential. Waits for realization within configured
   timeout.
4. **Persists Realized State** on provider callback. Updates the entity
   lifecycle state, fires `entity.realized` events.
5. **Reconciles continuously** via the Discovery Service. Polls providers
   on schedule, writes Discovered State, compares to Realized State, fires
   drift events. The Policy Engine evaluates each drift through Recovery
   Policies.

The loop runs forever — entities continuously move toward their declared
intent until decommissioned.

---

## 2. The engine's responsibilities

| Responsibility | How DCM fulfills it |
|---|---|
| Walk an entity from intent to realized | Request Orchestrator drives the nine-step pipeline; Request Processor performs assembly |
| Evaluate policy at every transition | Policy Manager evaluates Gating Policy / Validation / Transformation / Recovery / Orchestration Flow / Governance Matrix policies via OPA |
| Select a provider for placement | Placement Manager runs the six-step placement algorithm: sovereignty pre-filter → eligibility filter → capability filter → reserve query → scoring → tie-break |
| Dispatch with scoped credentials | API Gateway requests a `dcm_interaction` credential from the Credential Provider, scoped to the specific provider + entity + operation, valid for PT15M–PT1H per profile |
| React to provider events | Provider callbacks land at the Provider Callback API; the Request Orchestrator routes to Realized State persistence and event emission |
| Detect drift | Discovery Service polls per Resource Type Spec's `discovery_schedule`; Drift Detection compares Discovered to Realized field-by-field |
| Evaluate recovery on failure | Recovery Policies fire on declared triggers (timeout, cancellation failure, partial realization, compensation failure); evaluate via the same Policy Manager |
| Audit everything | Audit Service appends a record on every state transition, policy decision, credential issuance, and provider call; SHA-256 hash chain provides tamper evidence |

---

## 3. Pipeline routing — how events flow

DCM uses PostgreSQL's `LISTEN/NOTIFY` for pipeline routing in standard
deployments (Kafka added as an enhancement for high-throughput deployments).
Every state transition writes a row to `pipeline_events`; a trigger fires
`pg_notify`; subscribed services consume.

```
Consumer submits intent
    │ POST /api/v1/requests
    ▼
API Gateway — authenticates, injects X-DCM-Tenant
    │
    ▼
Request Orchestrator — writes intent_records row, emits intent.acknowledged
    │ LISTEN/NOTIFY
    ▼
Request Processor — assembles, writes requested_records row, emits requested.assembled
    │ LISTEN/NOTIFY
    ▼
Policy Manager — evaluates policies, computes score, emits policy.evaluated + score.computed
    │ LISTEN/NOTIFY
    ▼
Placement Manager — selects provider, emits placement.decided
    │ LISTEN/NOTIFY
    ▼
Request Orchestrator — issues interaction credential, dispatches to provider
    │ HTTP POST to provider's dispatch endpoint
    ▼
Provider — realizes the resource, calls back to /api/v1/instances/{id}/status
    │
    ▼
Request Orchestrator — writes Realized State, emits entity.realized
    │ LISTEN/NOTIFY
    ▼
Audit Service — appends audit record with hash chain
    │
    ▼
Discovery Service — runs scheduled discovery for the resource type
    │
    ▼
Drift Detection — compares Discovered to Realized, emits drift events if differ
    │ LISTEN/NOTIFY
    ▼
Policy Manager — evaluates Recovery Policies, fires configured action
```

Every step also writes provenance, so the full chain is reconstructable from
the audit trail.

---

## 4. Capability discovery and provider matching

UDLM's
[capability-discovery.md](https://github.com/croadfeldt/udlm/blob/main/contracts/capability-discovery.md)
defines the unified provider model: a provider is an external system that
declares **capabilities** (`realize_resources`, `serve_data`, `authenticate`,
`federate`, `execute_workflows`), not a fixed type.

DCM's provider registry implements this:

- Each provider registration includes a `capabilities` block plus declared
  `supported_resource_types`.
- The Placement Manager matches a request's resource_type and constraints
  against providers whose declared `realize_resources` capability includes
  that type.
- A provider declaring multiple capabilities (e.g., InfoBlox declaring both
  `serve_data` for IP availability queries and `realize_resources` for
  Network.IPAddress allocation) is matched separately for each capability.

**DCM exposes `GET /api/v1/capabilities`** — the machine-readable advertisement
of what this DCM instance can do (lifecycle management, policy evaluation,
cost analysis, audit trail, placement decisions, drift detection, entity
lifecycle events, subscribe endpoints). External systems (FinOps tools, audit
tools, DAV, federation peers) query this endpoint to discover DCM's
capabilities before integrating.

**Backward compatibility:** the legacy typed-provider names
(`service_provider`, `information_provider`, etc.) are retained as resolved
labels derived from declared capabilities. Existing registrations continue
to work.

System policies: `DISC-001` through `DISC-005` (in
[udlm/contracts/capability-discovery.md](https://github.com/croadfeldt/udlm/blob/main/contracts/capability-discovery.md))
govern capability advertisement authentication, tenant scoping, rate limiting,
and the advisory nature of needs_from_dcm matching.

---

## 5. State semantics — what each state means inside DCM

| State | What's in it | Where it lives in DCM | Who writes it |
|---|---|---|---|
| **Intent** | Consumer's raw declaration before any processing | `intent_records` table | Request Orchestrator on ingress |
| **Requested** | Assembled, policy-evaluated, placed payload | `requested_records` table | Request Processor after nine-step assembly |
| **Realized** | What the provider built, with provider-side fields | `realized_entities` table (versioned, `is_current` flag) | Request Orchestrator on provider callback |
| **Discovered** | What the provider currently reports | `discovered_records` table (ephemeral snapshots) | Discovery Service on scheduled poll |

The **Realized State only changes via an authorized request that produces a
corresponding Requested State record** (UDLM invariant RSE-010). Drift detection,
discovery cycles, and lifecycle events do not write to the Realized Store —
they write to other domains and trigger policy evaluation that may produce a
new Requested State.

---

## 6. Reading order for engine internals

If you're operationalizing or extending the convergence engine, read in this
order:

1. This overview.
2. [`policy-evaluation.md`](policy-evaluation.md) — how DCM evaluates the unified
   governance matrix, hard/soft enforcement, caching, sovereignty zones.
3. [`scoring.md`](scoring.md) — the hybrid scoring model, signals, approval routing.
4. [`recovery-and-retry.md`](recovery-and-retry.md) — timeouts, cancellation,
   orphan detection, recovery policy execution, compensation.
5. [`dependency-orchestration.md`](dependency-orchestration.md) — consumer
   request dependency graphs, PENDING_DEPENDENCY lifecycle, field injection,
   failure handling.

For governance enforcement specifically:
- [`../governance-enforcement/accreditation-monitor.md`](../governance-enforcement/accreditation-monitor.md)
- [`../governance-enforcement/registry-enforcement.md`](../governance-enforcement/registry-enforcement.md)
- [`../governance-enforcement/contribution-pipeline.md`](../governance-enforcement/contribution-pipeline.md)

For provider interaction:
- [`../credentials-and-auth/provider-callback.md`](../credentials-and-auth/provider-callback.md)
- [`../credentials-and-auth/credentials.md`](../credentials-and-auth/credentials.md)

---

## 7. Design invariants (DCM-level)

These hold across all profiles and deployments:

- The nine-step assembly is the only path from Intent to Requested
- The convergence loop is the only path from Requested to Realized
- The Discovery Service is the only writer of Discovered State
- Every state transition emits an event to `pipeline_events`
- Every state transition produces an audit record
- Every provider call carries a scoped, short-lived interaction credential
- Recovery Policies fire on every closed-vocabulary trigger; the action is
  evaluated through the same Policy Manager as any other policy

These are realization invariants for **DCM specifically**. A peer realization
might choose a different routing mechanism (e.g., Kafka instead of
`LISTEN/NOTIFY`), a different assembly algorithm, or a different audit
storage — and remain UDLM-conformant as long as the wire contracts are honored.
