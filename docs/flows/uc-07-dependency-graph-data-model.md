# UC-07 · Dependency graph as first-class data — the play

**Purpose:** how DCM runs this case, on top of [request-realization](request-realization.md) — only the UC-specific mechanics. Here that's reading ordering and impact *out of* the UDLM graph rather than maintaining a separate dependency map.

> **Use Case:** `dcm-core/standard/udlm-dependency-graph-data-model` · **Persona:** platform-operator.

## What's different in the engine

- **No parallel dependency store.** DCM queries the UDLM graph directly for the two authored edge kinds — containment and `depends_on` — instead of building its own; fault-domain co-membership is **derived**, not a third edge (UDLM ADR-010: a fault domain is *not an authored edge kind* — resources that transitively reference the same fault-domain anchor share it).
- **Two derived reads, one source.** A topological sort over `depends_on` + containment yields convergence order; a reverse-reachability walk over the same edges yields blast-radius, and shared-anchor co-reference yields fault-domain redundancy.
- **Edges written where they're known.** Containment edges are recorded at realization (which host, which pool); `depends_on` edges come from the resource spec; fault-domain grouping is computed from the recorded anchor references, never authored.

## Sequence — only the UC-specific part

```mermaid
sequenceDiagram
    actor Op as Platform-operator
    participant G as UDLM graph
    participant Ord as Ordering query
    participant Imp as Impact query

    Op->>G: realize resources, record edges (containment, depends_on) + anchor refs
    Op->>Ord: what order is safe?
    Ord->>G: topological sort over depends_on + containment
    G-->>Ord: convergence order
    Op->>Imp: what falls if this node fails?
    Imp->>G: reverse-reachability over the same edges
    G-->>Imp: blast-radius and surviving redundancy
```

## What an engineer adds

- Population of the three edge kinds as resources realize — no separate ordering table.
- Two graph queries (topological sort, reverse-reachability) that read the UDLM graph as their only source of truth.

## Pointers

- Stage: [udlm request-realization](https://github.com/croadfeldt/udlm/tree/main/docs/flows/request-realization.md). UC source: `dcm-core/standard/udlm-dependency-graph-data-model`.
