# DCM — Data Center Management

DCM is a framework for sovereign private cloud management. It provides a
declarative control plane for managing the lifecycle of arbitrary infrastructure
resources across an enterprise — from bare metal and VMs to containers,
applications, and managed services.

**DCM is one realization of [UDLM](https://github.com/croadfeldt/udlm)**, the
Universal Data Lifecycle Model. UDLM is the wire-compatible substrate
(entity types, four-state lifecycle, contracts, identifiers, events). DCM is
the operational platform built on it — convergence engine, control-plane
components, deployment topology, persistence, runtime features, governance
enforcement, credentials, and integrations.

**Three foundational abstractions:** Data · Provider · Policy
**License:** Apache 2.0

---

## Repository Structure

```
dcm/
├── architecture/
│   ├── overview.md                        ← Start here — DCM architecture entry point
│   ├── layering.md                        ← UDLM/DCM boundary and how they relate
│   ├── operator-perspective.md            ← Narrative operator/implementer handbook
│   ├── design-principles.md               ← DCM-specific implementation choices
│   ├── 00-split-manifest.md               ← Permanent record of the UDLM/DCM split
│   ├── 00-layering-data-model-vs-dcm.md   ← Superseded stub — see layering.md
│   ├── control-plane/                     ← Components, self-health, internal auth,
│   │                                        session revocation, API versioning
│   ├── convergence-engine/                ← The intent→realized loop:
│   │                                        overview, policy evaluation (matrix
│   │                                        evaluator), scoring, recovery/retry,
│   │                                        dependency orchestration
│   ├── ingestion/                         ← Brownfield ingestion engine + workload analysis
│   ├── credentials-and-auth/              ← Auth implementation, credentials,
│   │                                        provider callback mechanism (mTLS + cred),
│   │                                        authority enforcement
│   ├── governance-enforcement/            ← Accreditation monitor, registry
│   │                                        enforcement, contribution pipeline,
│   │                                        policy profiles
│   ├── runtime-features/                  ← Scheduling, notifications, webhooks/
│   │                                        messaging, federation runtime,
│   │                                        deployment redundancy
│   ├── topology/                          ← DCM's canonical 9-layer location
│   │                                        hierarchy + placement/priority bands
│   ├── persistence/                       ← PostgreSQL mandate + implementation
│   ├── integrations/                      ← ITSM, Kessel evaluation
│   ├── adr/                               ← Architectural Decision Records
│   ├── DCM-Capabilities-Matrix.md
│   ├── DISCUSSION-TOPICS.md
├── examples/
│   └── orchestration-scenarios.md         ← DCM-specific orchestration (builds on
│                                            UDLM canonical examples)
├── reference/
│   ├── implementation-standards.md        ← Specific algorithms, libs, configs DCM uses
│   ├── implementation-specifications.md
│   └── operational-reference.md
├── docs/                                  ← Index: docs/README.md
│   ├── specifications/                    ← Prose specification documents
│   ├── flows/                             ← Stage/play flow docs (request-realization, by-persona)
│   ├── how-to/                            ← How-to guides (profiles, migration/rehydration)
│   └── engineering/                       ← Engineering alignment + reconciliation
├── taxonomy/DCM-Taxonomy.md
├── schemas/                               ← OpenAPI, JSON Schema, SQL
├── dav/                                   ← validation/assessment testbed (non-normative consumer)
├── project-overview.md
├── LICENSE
└── README.md
```

For the substrate (entity types, four states, wire contracts, identifiers,
events, schema sharing, conformance), see
**[github.com/croadfeldt/udlm](https://github.com/croadfeldt/udlm)**.

## Key Facts

| Metric | Value |
|--------|-------|
| Architecture documents | 58 data model + 15 specifications |
| Capabilities | 322 across 39 domains |
| Provider types | 6 (service, information, meta, auth, peer_dcm, process) |
| Policy evaluation modes | 2 (Internal via OPA, External via provider) |
| Control plane services | 9 |
| Required infrastructure | 1 (PostgreSQL-compatible DB) — auth, secrets, events handled internally |
| Consumer API | 74 paths |
| Admin API | 61 paths |
| Event catalog | 101 payloads across 22 domains |

## Getting Started

1. **Understand the substrate first** — read [UDLM's README and CONFORMANCE.md](https://github.com/croadfeldt/udlm). DCM only makes sense if you know what it's a realization of.
2. **Read DCM's architecture overview** — [`architecture/overview.md`](architecture/overview.md), then [`architecture/layering.md`](architecture/layering.md) for the UDLM/DCM boundary.
3. **Read the operator perspective** — [`architecture/operator-perspective.md`](architecture/operator-perspective.md) — narrative handbook for running DCM.
4. **Dive into the convergence engine** — [`architecture/convergence-engine/overview.md`](architecture/convergence-engine/overview.md) — the heart of DCM.
5. **Learn the vocabulary** — read [`taxonomy/DCM-Taxonomy.md`](taxonomy/DCM-Taxonomy.md).
6. **See what DCM can do** — browse [`architecture/DCM-Capabilities-Matrix.md`](architecture/DCM-Capabilities-Matrix.md).
7. **Build a service** — start with the OpenAPI specs in [`schemas/openapi/`](schemas/openapi/) and the engineering guide in [`docs/engineering/ENGINEERING-ALIGNMENT.md`](docs/engineering/ENGINEERING-ALIGNMENT.md).
8. **Deploy an example** — see [dcm-examples](https://github.com/dcm-project/dcm-examples).

## Related Repositories

| Repository | Purpose |
|-----------|---------|
| [control-plane](https://github.com/dcm-project/control-plane) | The DCM control plane — runtime source for the catalog, placement, policy, and service-provider domains in a single process |
| [cli](https://github.com/dcm-project/cli) | `dcm` command-line client (catalog, policy, provider operations) |
| [kubevirt-service-provider](https://github.com/dcm-project/kubevirt-service-provider) | Service provider — VMs via KubeVirt/CNV |
| [k8s-container-service-provider](https://github.com/dcm-project/k8s-container-service-provider) | Service provider — containers via Kubernetes Deployments/Services |
| [acm-cluster-service-provider](https://github.com/dcm-project/acm-cluster-service-provider) | Service provider — OpenShift clusters via ACM/HyperShift |
| [dcm-examples](https://github.com/dcm-project/dcm-examples) | Reference implementations — Summit demo with Go services, Ansible, OpenShift manifests |
| [dcm-project.github.io](https://github.com/dcm-project/dcm-project.github.io) | Project website — documentation segmented by domain |
| [enhancements](https://github.com/dcm-project/enhancements) | Design proposals |
| [shared-workflows](https://github.com/dcm-project/shared-workflows) | CI/CD workflows |

> **Runtime topology note.** The catalog, placement, policy, and service-provider domains were originally separate
> services (`catalog-manager`, `placement-manager`, `policy-manager`, `service-provider-manager`, `api-gateway`).
> They were consolidated into the single **control-plane** process in May 2026 — they now call each other in-process
> on the provisioning path rather than over HTTP — and those five repositories are archived. The architecture docs
> in this repository describe the logical decomposition (the control plane's internal services); the table above
> lists the repositories that hold the current runtime.
