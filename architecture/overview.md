---
Document Status: ✅ Stable — DCM architecture entry point
Document Type: Architecture Overview
Established: 2026-05-26
---

# DCM Architecture Overview

> **Implements contracts defined in UDLM**: this entire DCM repo realizes the
> substrate specified at [github.com/croadfeldt/udlm](https://github.com/croadfeldt/udlm).
> Every architectural choice documented here is one possible realization of
> a UDLM-conformant peer.

DCM (Data Center Management) is a concrete operational platform built on
**UDLM (Universal Data Lifecycle Model)**. UDLM owns the substrate — entity
types, the four states (intent / requested / realized / discovered), state
transitions and invariants, wire contracts (provider, policy, events, data
store), provenance, identity, reference taxonomies. UDLM is what peers must
share to interoperate.

DCM owns the operationalization — the convergence engine, control-plane
components, deployment topology, persistence mandate, runtime features,
governance enforcement, credentials, and integrations with specific external
systems.

For the deeper conceptual layering and the boundary test ("could a peer of
DCM, built independently, choose to do this differently and still be a valid
realization of the same data?"), see [layering.md](layering.md). For the
narrative operator perspective, see [operator-perspective.md](operator-perspective.md).

---

## Reading order for new contributors

1. Read this overview.
2. Read [layering.md](layering.md) for the UDLM/DCM boundary.
3. Read [operator-perspective.md](operator-perspective.md) for the operator narrative.
4. Read [convergence-engine/overview.md](convergence-engine/overview.md) for how DCM walks data through the four states.
5. Use the per-concern subdirectory READMEs to dive into specific areas as needed.

---

## How this repo is organized

DCM groups documentation by **architectural concern**, not by file number.

| Subdirectory | What lives here |
|---|---|
| [`control-plane/`](control-plane/) | The deployable services — API gateway, components, self-health, internal component auth, session revocation, API versioning |
| [`convergence-engine/`](convergence-engine/) | The intent→realized loop — policy evaluation, scoring, recovery and retry, dependency orchestration, provider matching |
| [`ingestion/`](ingestion/) | Brownfield ingestion engine and workload analysis |
| [`credentials-and-auth/`](credentials-and-auth/) | Auth implementation, credential management, provider callback auth, authority tier enforcement |
| [`governance-enforcement/`](governance-enforcement/) | Matrix evaluator, accreditation monitor, registry enforcement, contribution pipeline, policy profiles |
| [`runtime-features/`](runtime-features/) | Scheduling, notifications, webhooks/messaging, federation runtime, deployment redundancy |
| [`topology/`](topology/) | DCM's canonical 9-layer location hierarchy and placement/priority bands |
| [`persistence/`](persistence/) | The PostgreSQL mandate and its implementation |
| [`integrations/`](integrations/) | ITSM and Kessel evaluation |

Adjacent top-level directories:

| Directory | What lives here |
|---|---|
| [`../examples/`](../examples/) | DCM-specific orchestration scenarios that build on UDLM canonical examples |
| [`../reference/`](../reference/) | Implementation standards, operational reference, implementation specifications |
| `deployment/` *(planned — not yet in the repo)* | Deployment topology, Kubernetes manifests |

---

## Permanent split context

The DCM repo split from a single combined `architecture/data-model/` tree in
2026-05-26. The split planning record is preserved at
[`00-split-manifest.md`](00-split-manifest.md) — kept as a permanent contextual
artifact so future contributors can understand which decisions are load-bearing
and why files live where they do.
