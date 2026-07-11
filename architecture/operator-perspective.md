---
Document Status: 📋 Draft — Initial Specification
Document Type: Operator/Implementer Narrative
Established: 2026-05-26
Maps to: UDLM operationalization
---

# DCM Operator Perspective — the DMV Operator's Manual

> **Implements contracts defined in UDLM**: this is the operator-side
> companion to UDLM's `udlm/docs/consumer-perspective.md` (the consumer's
> driver's handbook). Together the two perspectives cover the system from
> both sides — the consumer who submits intent and waits for realized state,
> and the operator who runs the platform that makes realization happen.

This document is for people who must **run DCM**. Not consume it from the
outside (that's the consumer perspective in UDLM); **operationalize it**.

---

## 1. Mental model — DCM is UDLM's operationalization

UDLM tells you what data exists, what states it can be in, what wire contracts
peers must honor, and what the lifecycle invariants are. UDLM does not tell
you:

- Where the data lives on disk
- Which programming language runs the convergence loop
- How requests are queued and dispatched
- Which database your audit chain is stored in
- Whether a service mesh handles mTLS
- How many control-plane services you deploy

Those are realization choices. **DCM is one set of answers to those questions** —
a specific, opinionated, operationally proven set.

The driving analogy: UDLM is the published rules of the road (what cars exist,
what driving means, what licenses are required). DCM is the actual road, the
turn signals, the traffic lights, the cars driving, the DMV that issues licenses.
A peer of DCM in a different jurisdiction could pave the road in concrete instead
of asphalt and still be a valid road — provided cars conformant to the rules of
the road can drive on it.

---

## 2. Where the substrate ends and the realization begins

When you read a UDLM document like `udlm/lifecycle/operational-models.md`,
you'll see contracts like:

- *"a realization MUST honor timeout contracts on dispatch"*
- *"cancellation MUST follow the best-effort propagation model"*
- *"orphan detection MUST be triggered after compensation failure"*

When you read the corresponding DCM document
[`convergence-engine/recovery-and-retry.md`](convergence-engine/recovery-and-retry.md),
you'll see implementation:

- *"DCM enforces dispatch_timeout via per-step deadlines computed as fractions of assembly_timeout"*
- *"DCM's cancellation execution sends a cancel payload to the provider's declared cancellation endpoint and waits up to PT30S for acknowledgement"*
- *"DCM's orphan detection runs an immediate Mode 1 capacity-and-listing query against the provider after COMPENSATION_FAILED"*

This pattern repeats across every DCM document. The UDLM contract is the
"what must be true"; the DCM document is "here is how DCM makes it true."

When you write your own DCM-internal documentation or extend an existing area,
**stay in operationalization voice**: "DCM evaluates X using algorithm A",
"DCM enforces Y at boundary Z", "DCM persists Q in table R". Avoid re-stating
the UDLM contract; link to it.

---

## 3. Where the operational concerns live in this repo

The DCM repo is organized by **architectural concern**, not by document number.
Use this map to find what you need.

### 3.1 Running the platform

| You need to... | Look in |
|---|---|
| Understand what services to deploy | [`control-plane/components.md`](control-plane/components.md) |
| Set up internal mTLS between services | [`control-plane/internal-component-auth.md`](control-plane/internal-component-auth.md) |
| Configure health checks and probes | [`control-plane/self-health.md`](control-plane/self-health.md) |
| Manage API versioning | [`control-plane/api-versioning.md`](control-plane/api-versioning.md) |
| Manage session revocation | [`control-plane/session-revocation.md`](control-plane/session-revocation.md) |
| Choose a deployment topology | [`runtime-features/deployment-redundancy.md`](runtime-features/deployment-redundancy.md) |
| Set up the database | [`persistence/postgres-mandate.md`](persistence/postgres-mandate.md), [`persistence/postgres-implementation.md`](persistence/postgres-implementation.md) |

### 3.2 The convergence engine — the heart of DCM

| You need to... | Look in |
|---|---|
| Understand the intent→realized loop | [`convergence-engine/overview.md`](convergence-engine/overview.md) |
| Understand policy evaluation mechanics | [`convergence-engine/policy-evaluation.md`](convergence-engine/policy-evaluation.md) |
| Understand placement scoring | [`convergence-engine/scoring.md`](convergence-engine/scoring.md) |
| Handle timeouts, retries, cancellations | [`convergence-engine/recovery-and-retry.md`](convergence-engine/recovery-and-retry.md) |
| Orchestrate dependent requests | [`convergence-engine/dependency-orchestration.md`](convergence-engine/dependency-orchestration.md) |

### 3.3 Bringing infrastructure into the platform

| You need to... | Look in |
|---|---|
| Onboard brownfield infrastructure | [`ingestion/engine.md`](ingestion/engine.md) |
| Analyze workload placement | [`ingestion/workload-analysis.md`](ingestion/workload-analysis.md) |

### 3.4 Credentials, auth, governance enforcement

| You need to... | Look in |
|---|---|
| Configure auth providers | [`credentials-and-auth/auth-implementation.md`](credentials-and-auth/auth-implementation.md) |
| Manage credentials lifecycle | [`credentials-and-auth/credentials.md`](credentials-and-auth/credentials.md) |
| Set up provider callback auth (mTLS + interaction credential) | [`credentials-and-auth/provider-callback.md`](credentials-and-auth/provider-callback.md) |
| Enforce authority tier on approvals | [`credentials-and-auth/authority-enforcement.md`](credentials-and-auth/authority-enforcement.md) |
| Enforce the governance matrix | [`convergence-engine/policy-evaluation.md`](convergence-engine/policy-evaluation.md) |
| Monitor accreditation status | [`governance-enforcement/accreditation-monitor.md`](governance-enforcement/accreditation-monitor.md) |
| Govern registry contributions | [`governance-enforcement/registry-enforcement.md`](governance-enforcement/registry-enforcement.md) |
| Run the contribution pipeline (GitOps PRs) | [`governance-enforcement/contribution-pipeline.md`](governance-enforcement/contribution-pipeline.md) |
| Configure policy profiles | [`governance-enforcement/policy-profiles.md`](governance-enforcement/policy-profiles.md) |

### 3.5 Runtime features

| You need to... | Look in |
|---|---|
| Set up scheduled requests + maintenance windows | [`runtime-features/scheduling.md`](runtime-features/scheduling.md) |
| Configure notification delivery | [`runtime-features/notifications.md`](runtime-features/notifications.md) |
| Set up webhooks and messaging | [`runtime-features/webhooks-messaging.md`](runtime-features/webhooks-messaging.md) |
| Configure DCM-to-DCM federation runtime | [`runtime-features/federation-runtime.md`](runtime-features/federation-runtime.md) |

### 3.6 Topology and placement

| You need to... | Look in |
|---|---|
| Set up the 9-layer location hierarchy | [`topology/canonical-9-layer-hierarchy.md`](topology/canonical-9-layer-hierarchy.md) |
| Configure placement and priority bands | [`topology/placement-and-priority-bands.md`](topology/placement-and-priority-bands.md) |

### 3.7 Integrations and reference

| You need to... | Look in |
|---|---|
| Integrate with ITSM (ServiceNow, Jira, Remedy) | [`integrations/itsm.md`](integrations/itsm.md) |
| Read the Kessel integration evaluation | [`integrations/kessel-evaluation.md`](integrations/kessel-evaluation.md) |
| Look up implementation standards (algorithms, RFCs, FIPS levels) | [`../reference/implementation-standards.md`](../reference/implementation-standards.md) |
| Operational runbooks and CLI reference | [`../reference/operational-reference.md`](../reference/operational-reference.md) |
| Implementation specifications | [`../reference/implementation-specifications.md`](../reference/implementation-specifications.md) |
| See orchestration scenarios | [`../examples/orchestration-scenarios.md`](../examples/orchestration-scenarios.md) |

---

## 4. The operational rhythm

DCM is a convergence-driven control plane. The operational rhythm has four
repeating beats:

1. **Ingress** — a consumer submits intent (via API, GitOps PR, CLI, message bus,
   or scheduled trigger). The API gateway authenticates, the Request Orchestrator
   acknowledges.
2. **Assemble** — the Request Processor performs nine-step assembly: layer
   resolution, policy evaluation, scoring, placement. A new Requested State is
   written.
3. **Dispatch and realize** — the Request Orchestrator dispatches to the selected
   provider with a scoped, short-lived interaction credential. The provider
   realizes; DCM persists the Realized State.
4. **Reconcile** — the Discovery Service polls providers on schedule, compares
   Discovered State to Realized State, fires drift events. The Policy Engine
   evaluates each drift through Recovery Policies. The loop continues.

Most operator work is configuring the policies, profiles, and providers that
shape this loop — not writing the loop itself.

---

## 5. The profile system is your primary configuration lever

DCM ships with six built-in profiles: `minimal`, `dev`, `standard`, `prod`,
`fsi`, `sovereign`. The profile controls dozens of enforcement and threshold
settings simultaneously: credential lifetimes, TLS requirements, MFA
requirements, scoring thresholds, approval routing tiers, scheduling horizons,
audit retention, and more.

**Pick the profile that matches your operational risk tolerance and let it
drive the defaults.** Override individual settings only when you have a
specific reason.

The profile is not a UDLM concept — it's a DCM ease-of-use scaling mechanism.
A peer realization could choose a different scaling axis. UDLM only requires
that the chosen mechanism produce wire-compatible behavior.

See [`governance-enforcement/policy-profiles.md`](governance-enforcement/policy-profiles.md).

### 5.1 Profiles govern the control plane, not the managed infrastructure

Profiles are purely a control-plane lever: they govern *how* the control plane
behaves — strictness, thresholds, automation level, review windows. They do not
shape the infrastructure DCM manages. That is a different set of levers:

- **Placement / validation / transformation policies** — what may be built,
  where, and under what constraints.
- **Catalog and composite-service definitions** — what infrastructure shapes
  are offerable in the first place.
- **Provider capability declarations** — what a provider can actually realize.

Put simply: the **profile** decides how the control plane operates; **policy +
catalog + provider** decide what infrastructure gets built and under what
constraints. When tuning behavior, reach for the profile; when changing what
DCM can provision, reach for policies, the catalog, and provider capabilities.

---

## 6. Common pitfalls

- **Don't author against UDLM contracts thinking they're DCM.** UDLM defines
  the abstract two-layer provider callback auth contract; DCM picks mTLS +
  interaction credential. If your peer realization picks JWT + signed
  assertion instead, you're still UDLM-conformant — but you're not DCM.

- **Don't assume PostgreSQL is the only valid persistence.** UDLM requires
  persistence; DCM mandates PostgreSQL for *this realization*. A peer
  realization could use a different SQL category and still conform. See
  [`persistence/postgres-mandate.md`](persistence/postgres-mandate.md) for
  why DCM made this specific choice.

- **Don't treat the 9-layer location hierarchy as substrate.** UDLM defines
  the layered-topology contract abstractly. DCM picks Country → Region →
  Zone → Site → Data Center → Hall → Cage → Rack → Unit as its canonical
  default. A peer could pick a 6-layer hierarchy or a 12-layer hierarchy and
  remain UDLM-conformant.

- **Don't reach for new mechanisms before extending existing ones.** Most
  needs can be expressed through the existing profile + policy + provider
  capability extension system. New mechanisms are a last resort.

---

## 7. When you contribute back

If you find yourself wanting to change something:

1. Does the change affect wire-level compatibility (data shapes, event
   payloads, contract surfaces)? **It belongs in UDLM**, not here.
2. Does it change DCM's realization choices (which database, which auth
   mechanism, how the convergence loop works)? **It belongs here.**
3. Does it sit on the boundary? Apply the test from
   [layering.md](layering.md): *"could a peer of DCM choose differently?"*
   If yes → DCM. If no → UDLM.

The split manifest at [`00-split-manifest.md`](00-split-manifest.md) is the
durable record of how this boundary was originally drawn. Read it before
proposing structural changes.
