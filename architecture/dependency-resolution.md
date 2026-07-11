# Dependency resolution

**What this settles:** how DCM turns the authored UDLM estate — plus dependencies that arrive by
other means — into **one effective dependency graph** that consumers (ordered shutdown/startup,
topology visualizers, impact/blast-radius analysis) run on. The UDLM data model *stores* dependencies
several ways at the implementor's chosen granularity (see the UDLM doc: dependency modeling); DCM
*resolves* them uniformly so consumers never need to know how any dependency was authored.

Two orthogonal axes: the **authoring pattern** (the shape of a dependency) and the **insertion
mechanism** (how it reaches DCM's view). DCM merges every combination into the effective graph.

## Insertion mechanisms — how a dependency enters the graph

1. **Authored** — declared in the UDLM estate: a resource's `dependencies[]` (including an edge to a
   shared node it bundles through), a `tenant_uuid`. Versioned, reviewable; the source of truth.
2. **Discovered** — a discovery job probes reality (topology/LLDP, hypervisor inventory, cluster API,
   BMC, storage) and inserts observed edges (VM→host, NIC→switch-port, volume→pool). Keeps the graph
   synced with reality and **flags drift** where authored ≠ discovered.
3. **Derived** — computed at resolution time, never stored: scope (`tenant_uuid`) → the realm's
   identity/DNS services. This is the only real derivation — transitive chains and bundling are plain
   edges the traversal already follows; only a membership *field* like `tenant_uuid` needs edges made.
4. **Provider-reported** — a provider, realizing or managing a resource, emits the dependencies it
   alone observes at realization (workload→node, VM→host, reservation→DNS zone), as realized state.
5. **Policy-injected** — an admission/policy rule adds dependencies by condition ("any hypervisor
   depends on its rack's cooling domain"; "any realm member requires the realm IdM"), keeping broad
   invariants out of per-resource authoring.

These compose on one resource: power **authored** (PSU→feed), placement **discovered**, identity
**derived**, cooling **policy-injected**.

## The resolution pass (build-time, not stored)

DCM produces the effective graph as an ordered merge; it is recomputed on demand so it always
reflects the live model:

1. **Seed** with the authored estate edges.
2. **Union discovered** edges; where a discovered edge contradicts an authored one, keep both and
   emit a **drift** finding (authored is intent; discovered is reality).
3. **Union provider-reported** realized edges.
4. **Derive scopes** — for each resource, inject its realm's `Security.DirectoryService` /
   `Network.AddressService` from `tenant_uuid` (excluding the control-plane resources themselves, to
   avoid cycles), and any `Facility.Location`-scoped ambient dependency. This is the *only* real
   derivation: a `tenant_uuid` is a field, not an edge, so nothing else can traverse it.
5. **Apply policy injections** in a defined order.
6. **Transitive chains + bundling need no step** — `host→PSU→feed`, and *bundling* (a resource
   `depends_on` a node that carries shared dependencies) are ordinary edges; the dependents inherit
   the shared deps as secondary dependencies by graph traversal alone. There is no bundle-expansion
   pass and no bundle type — see the anti-pattern note.
7. **Detect cycles and emit them as data** (core capability — see below). An orderable estate is a
   DAG; detection runs on *every* resolution and, rather than only erroring, emits each cycle as a
   structured `DependencyCycle` finding on the effective graph. The resolver never guesses an order
   for cyclic members.

### Anti-pattern: a dedicated bundle type / expansion pass

Do not add a `DependencyBundle` type whose members "attach" and inherit its dependencies, nor a
resolution step that expands such membership. It reproduces transitivity the graph already provides —
a resource that `depends_on` a node is already downstream of that node's dependencies — for no
functional gain, at the cost of a parallel mechanism to learn and keep consistent. To bundle, declare
the shared deps on a node and depend on it. Mark a purely-abstract grouping (depended on for ordering
but never acted on) with a lightweight flag, not a type.

The result is a DAG of typed edges. Consumers run over it directly:
- **ordered shutdown/startup** — topological sort (stop dependents before dependencies; reverse to
  start), with control-plane resources held last;
- **visualizers** — render the resolved graph, distinguishing authored vs derived vs discovered;
- **impact analysis** — "what breaks if X goes down" is reachability over the same graph.

## Dependency-cycle detection — a first-class, policy-addressable output

A dependency cycle is not merely a resolver error to log — every consumer above *requires* a DAG, so
a cycle is a platform-level signal. It is exposed as **data** and governed by **policy**, decomposed
across the Data·Policy·Provider triad:

- **Data (UDLM).** Acyclicity is the declared invariant of the dependency graph (see the UDLM
  graph-integrity spec). A violation is exposed as a `DependencyCycle` diagnostic —
  `{members[], edge_chain[], severity, contributing_mechanisms[], detector}`. **Severity is derived
  from the cycle's own edges:** a cycle whose every edge is `hard` is **blocking** — no safe order
  exists; a cycle that a `soft` edge closes is **degraded** — orderable by dropping the soft edge, but
  flagged. UDLM defines the shape; it does not compute it.
- **Provider (DCM resolution).** The resolution engine computes cycles from the **effective** graph
  (so derived, discovered, and policy-injected edges are all in scope, not just authored ones):
  Kahn's longest-path leaves cyclic members with non-zero in-degree, and a DFS then extracts the
  actual chain for each. Detection is a **core, always-run** step, and every cycle is tagged with the
  insertion mechanisms that contributed its edges — so "authored ⇄ authored" is distinguishable from
  "authored ⇄ discovered" (an intent/reality conflict) or "… ⇄ policy-injected" (a rule that closed a
  loop). Provenance turns a cycle from a dead end into a diagnosable one.
- **Policy (DCM policy engine).** `DependencyCycle` findings are **policy inputs**. Admission
  default-denies a **blocking** (all-hard) cycle — a cyclic estate does not realize — while a
  **degraded** cycle is configurable: warn, quarantine the members, or auto-relax the soft edge with a
  recorded resolution. Policies match on `graph.cycles` / `graph.cycle_severity` (UDLM policy match
  sources), so the response is authored, not hard-coded in the engine.

The payoff: "the estate won't order" stops being an opaque failure and becomes a first-class,
severity-ranked, provenance-tagged, policy-governed signal — the same shape as any other finding the
platform acts on. Reference realizations already exist: the estate CI's **CYCLE-001** gate (reports
the offending chain) and the estate-explorer `/api/order` `cycles[]` output.

## Choosing an authoring pattern (best practice)

| Pattern | Granularity | Effort/resource | Fidelity | Use for |
|---|---|---|---|---|
| Direct edge | any | high | exact | specific bindings, one-offs |
| Component chain (PSU→feed) | finest | medium | redundancy-aware | power, network fabric |
| Bundling (depend on a shared node) | coarse | low | shared, via transitivity | platform services routed through a node |
| Scope-derived (field) | coarse | none | ambient | realm from tenant |

Guidance: **start coarse** (a shared node / scope) for a fast, correct-enough graph; **refine to
component-level** where redundancy or precision earns the effort. Patterns mix on one resource. Model
power at the PSU→feed level rather than a host-level UPS edge whenever redundancy matters — a coarse
edge silently drops the second rail.

## Boundary

Storage of dependencies (the patterns, the types) is UDLM's; resolution and the insertion mechanisms
are DCM's. This keeps the data model free of computed state and lets an estate be authored coarsely,
finely, or in a mix without changing the model. See `architecture/00-layering-data-model-vs-dcm.md`.
