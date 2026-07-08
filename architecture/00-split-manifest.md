---
status: ✅ Decisions locked — ready for execution
created: 2026-05-26
purpose: Plan and record the split of architecture/data-model/ into two repos (udlm + dcm)
permanence: Kept in dcm as a permanent contextual artifact (helps future contributors understand the boundary)
---

# UDLM / DCM Split Manifest

This document is the **plan of record** for splitting the existing
`architecture/data-model/` directory into two independent repos:

- **`udlm`** — Universal Data Lifecycle Model (substrate) — `github.com/croadfeldt/udlm`
- **`dcm`** — Data Center Management (operational platform built on udlm) — this repo

This document is kept in dcm as a **permanent contextual artifact**. It captures
the rationale and boundary work that drove the split; future contributors can
read it to understand why files live where they do and which decisions are
load-bearing.

Companion doc: [`00-layering-data-model-vs-dcm.md`](00-layering-data-model-vs-dcm.md)
— captures the conceptual layering that justifies this split. (Held uncommitted
until the split lands so its repo references can be made concrete.)

---

## The boundary rule (recap)

For each file or section, the test is:

> *"Could a peer of DCM, built independently, choose to do this differently and
> still be a valid realization of the same data?"*

- **Yes →** belongs in **dcm** (it's an implementation choice)
- **No, it would break interop or invalidate the data →** belongs in **udlm**
  (it's a substrate invariant)

**udlm owns** entity types, four states + transitions + invariants, contracts
(provider, policy, event payloads, data store), provenance, identity, reference
taxonomies. The state vocabulary lives here because peers must share it to
interoperate.

**dcm owns** the convergence engine, runtime/orchestration, deployment topology,
monitors, integrations with specific external systems, ease-of-use packaging,
implementation specifics.

### Compatibility model (LOCKED)

**udlm enforces wire-level compatibility at the data/event/contract boundary;
it does not enforce implementation portability.**

Concretely:
- Any system conformant to udlm version X produces data that any other system
  conformant to the same major version of udlm can read, interpret, and
  exchange — **versioning applicability rules withstanding**.
- Federation between peers is **literal interop**, not "architecturally similar
  systems requiring adapters."
- A peer realization's storage, internal APIs, control-plane components, and
  runtime mechanics are NOT constrained by udlm — those are dcm-layer choices.

**Implications for udlm spec authoring:**
1. Wire formats are **normative** (identifier strings, timestamps, event payloads, error envelopes).
2. Error/code/state vocabularies that cross interop boundaries are **closed**.
3. udlm **must** define a schema-sharing mechanism so peers can exchange schemas
   for their custom types and resolve each other's data with context.
4. Versioning is a first-class concern — every wire contract carries a version
   and a compatibility window.

This position is the K8s precedent: K8s API + CRDs are wire-compatible across
distributions; controllers are not portable. We are in the same shape.

### Sidebar — the validating analogy

A useful test (user-provided, captured here for future contributors):

| Analogy | Layer |
|---|---|
| **Directions** — where you can go, what destinations exist | udlm |
| **Goals** for the rules of the road (safety, predictability, interop) | udlm |
| **Rules-of-the-road requirements** (what cars + drivers must satisfy) | udlm |
| **Driver requirements** (license classes, competencies) | udlm |
| **Published rules-of-the-road manual** (RFCs, NIST cited as substrate) | udlm |
| **The road itself** (control-plane components, persistence) | dcm |
| **Turn signals** (the physical lights and signaling infrastructure) | dcm |
| **Cars actually driving** (convergence engine, the intent→realized loop) | dcm |
| **Actual rules of the road** (specific enforcement, matrix evaluator) | dcm |
| **DMV licensing process** (profile thresholds, approval enforcement, GitOps PR) | dcm |

The analogy stress-tests classifications. When unsure: "is this a *direction
or requirement* (udlm) or *infrastructure or enforcement* (dcm)?"

---

## File-level classification (61 files total)

Counts: **udlm 22 / dcm 18 / both 21** = 61. (Plus 7 net-new udlm contract docs
authored during the split — see "Newly identified udlm contracts" below.)

### Pure udlm (22 files) — move as-is

```
00-context-and-purpose.md       12-audit-provenance-observability.md
00-foundations.md                15-universal-groups.md
01-entity-types.md               16-universal-audit.md
02-four-states.md                30-composite-service-model.md
03-layering-and-versioning.md    33-event-catalog.md
04b-ownership-sharing-allocation.md  50-subscription-lifecycle.md
05-resource-type-hierarchy.md    52-test-framework-specification.md
07-service-dependencies.md       A-provider-contract.md
08-resource-grouping.md          B-policy-contract.md
09-entity-relationships.md
10-information-providers.md
11-data-store-contracts.md
11-storage-providers.md
```

### Pure dcm (18 files) — move as-is

```
14-policy-profiles.md            39-dcm-self-health.md
17-deployment-redundancy.md      41-operational-reference.md
18-webhooks-messaging.md         42-itsm-integration.md
22-dcm-federation.md             44-kessel-integration-evaluation.md
23-notification-model.md         45-consistency-review.md
25-control-plane-components.md   46-workload-analysis.md
29-scoring-model.md              47-accreditation-monitor.md
34-api-versioning-strategy.md    49-implementation-specifications.md
35-session-revocation.md
36-internal-component-auth.md
```

### Needs per-section split (21 files) — see detail below

```
00-design-priorities.md          31-credential-management.md
04-examples.md                   31-credential-provider-model.md
06-resource-service-entities.md  32-authority-tier-model.md
13-ingestion-model.md            37-scheduled-requests.md
19-auth-providers.md             38-request-dependency-graph.md
20-registry-governance.md        40-standards-catalog.md
21-information-providers-advanced.md  43-provider-callback-auth.md
24-operational-models.md         48-location-topology-layers.md
26-accreditation-and-authorization-matrix.md  51-infrastructure-optimization.md
27-governance-matrix.md          53-capability-discovery.md
28-federated-contribution-model.md
```

---

## Proposed `udlm` repo layout (LOCKED — numeric prefixes dropped)

```
udlm/
├── README.md                       # what udlm is, who consumes it, how to extend
├── CONFORMANCE.md                  # NEW — what a conformant realization must provide (wire contract surface)
├── foundations/
│   ├── context-and-purpose.md
│   ├── foundations.md
│   ├── entity-types.md
│   ├── four-states.md
│   ├── layering-and-versioning.md
│   ├── examples.md                 # ALL examples (kept clean — see resolved #1)
│   └── ownership-sharing-allocation.md
├── entities/
│   ├── resource-type-hierarchy.md
│   ├── resource-service-entities.md   # udlm portion
│   ├── service-dependencies.md
│   ├── resource-grouping.md
│   ├── entity-relationships.md
│   └── composite-service-model.md
├── contracts/
│   ├── provider-contract.md        # was A-
│   ├── policy-contract.md          # was B-
│   ├── information-providers.md
│   ├── data-store-contracts.md
│   ├── storage-providers.md
│   ├── information-providers-advanced.md  # udlm portion
│   ├── event-catalog.md
│   ├── provider-callback-auth.md   # udlm portion (mechanism-neutral two-layer abstract — see resolved #3)
│   ├── capability-discovery.md     # udlm portion
│   ├── identifier-scheme.md        # NEW
│   ├── time-and-clock.md           # NEW
│   ├── error-model.md              # NEW
│   ├── retry-semantics.md          # NEW (extract from 24/25/recovery profiles)
│   ├── rate-limit-and-backpressure.md  # NEW (extract from 49)
│   └── schema-sharing.md           # NEW (peer schema exchange — required by wire-compat)
├── lifecycle/
│   ├── ingestion-model.md          # udlm portion
│   ├── operational-models.md       # udlm portion (timeouts, cancellation, orphan contracts)
│   ├── scheduled-requests.md       # udlm portion
│   ├── request-dependency-graph.md # udlm portion
│   └── subscription-lifecycle.md
├── governance/
│   ├── auth-providers.md           # udlm portion (auth mode taxonomy)
│   ├── registry-governance.md      # udlm portion
│   ├── accreditation-and-authorization-matrix.md  # udlm portion
│   ├── governance-matrix.md        # udlm portion
│   ├── federated-contribution-model.md  # udlm portion
│   ├── credentials.md              # NEW — merged 31a + 31b (see resolved #6)
│   └── authority-tier-model.md     # udlm portion
├── observability/
│   ├── audit-provenance-observability.md
│   ├── universal-groups.md
│   └── universal-audit.md
├── topology/
│   └── location-topology-layers.md # udlm portion: layered-topology contract + assembly rules + lifecycle ONLY (specific 9-layer hierarchy moved to dcm — see resolved #4)
├── design-principles/
│   ├── design-priorities.md        # udlm portion (the four principles as contracts)
│   └── infrastructure-optimization.md  # udlm portion (data-contract principle + four domains; PostgreSQL mandate moved to dcm — see resolved #5)
├── reference/
│   └── standards-catalog.md        # udlm portion (the normative external standards list)
├── docs/
│   └── consumer-perspective.md     # NEW — the "driver's handbook" (narrative perspective for consumers)
└── tests/
    └── test-framework-specification.md
```

**Notes on the layout:**
- Numeric prefixes dropped. Reading order is conveyed by README + section names.
- `CONFORMANCE.md` at top-level: defines what any peer realization must provide
  to be wire-compatible. This is the conformance surface DAV will validate
  against.
- `contracts/` is the wire-compatibility surface — every doc here is normative.
- `docs/` is the single narrative directory (no separate `guides/`).
- udlm has no `deployment/`, no `mcp-servers/`, no API surface — it's pure
  specification.

---

## Proposed `dcm` repo layout

dcm gets a layout shaped around its concerns, not mirroring udlm:

```
dcm/
├── README.md                       # what dcm is, links to udlm
├── architecture/
│   ├── overview.md                 # links to udlm as substrate
│   ├── layering.md                 # adapted from 00-layering-data-model-vs-dcm.md
│   ├── control-plane/
│   │   ├── components.md           # ← 25-control-plane-components
│   │   ├── self-health.md          # ← 39-dcm-self-health
│   │   ├── internal-component-auth.md  # ← 36
│   │   ├── session-revocation.md   # ← 35
│   │   └── api-versioning.md       # ← 34
│   ├── convergence-engine/
│   │   ├── overview.md             # new — the intent → realized loop
│   │   ├── policy-evaluation.md    # ← 14, dcm parts of 27
│   │   ├── scoring.md              # ← 29
│   │   ├── recovery-and-retry.md   # ← dcm parts of 24
│   │   └── dependency-orchestration.md  # ← dcm parts of 38
│   ├── ingestion/
│   │   ├── engine.md               # ← dcm parts of 13
│   │   └── workload-analysis.md    # ← 46
│   ├── credentials-and-auth/
│   │   ├── auth-implementation.md  # ← dcm parts of 19
│   │   ├── credentials.md          # ← dcm parts of 31a + 31b (CONSOLIDATED)
│   │   ├── provider-callback.md    # ← dcm parts of 43 (mTLS + interaction credential mechanism)
│   │   └── authority-enforcement.md # ← dcm parts of 32
│   ├── governance-enforcement/
│   │   │   # NOTE: matrix-evaluator content merged into convergence-engine/policy-evaluation.md (← dcm parts of 27)
│   │   ├── accreditation-monitor.md  # ← 47, dcm parts of 26
│   │   ├── registry-enforcement.md # ← dcm parts of 20
│   │   ├── contribution-pipeline.md # ← dcm parts of 28
│   │   └── policy-profiles.md      # ← 14
│   ├── runtime-features/
│   │   ├── scheduling.md           # ← dcm parts of 37
│   │   ├── notifications.md        # ← 23
│   │   ├── webhooks-messaging.md   # ← 18
│   │   └── federation-runtime.md   # ← 22
│   ├── topology/
│   │   ├── canonical-9-layer-hierarchy.md  # ← MOVED from udlm 48 (Country → ... → Unit as DCM's canonical default)
│   │   └── placement-and-priority-bands.md  # ← dcm parts of 48
│   ├── persistence/
│   │   ├── postgres-mandate.md     # ← MOVED from udlm 51 (single-required-infrastructure decision)
│   │   └── postgres-implementation.md  # ← dcm parts of 51
│   ├── integrations/
│   │   ├── itsm.md                 # ← 42
│   │   └── kessel-evaluation.md    # ← 44
│   ├── design-principles.md        # ← dcm parts of 00-design-priorities
│   ├── operator-perspective.md     # NEW — how to operationalize udlm (companion to udlm's consumer-perspective)
│   └── consistency-review.md       # ← 45 (meta doc, lives here)
├── deployment/                     # (existing)
├── requirements/
│   └── dcm-platform-requirements.md
├── examples/
│   └── three-tier-application.md   # ← dcm parts of 04-examples (orchestration scenarios)
└── reference/
    └── implementation-standards.md # ← dcm parts of 40-standards-catalog
```

**Notes on the dcm layout:**
- Organized by **architectural concern**, not by file number. Numbers were
  scaffolding; the split is the moment to drop them.
- Every dcm spec opens with: `> Implements contracts defined in udlm: [link]`
- The `convergence-engine/` group is new — it's the heart of dcm and currently
  scattered across 24, 27, 38, 14. Worth consolidating.
- `runtime-features/` is the catch-all for "things dcm does that aren't core
  convergence": scheduling, notifications, federation, webhooks.

---

## Per-section split for the 21 "both" files

For each file: which sections go to udlm, which to dcm, and how the dcm doc
references the udlm doc.

> **Note on paths**: the path references in the per-section blocks below use
> the **legacy numeric layout** (e.g., `udlm/40-governance/27-...md`). The final
> layout drops numeric prefixes per the LOCKED udlm layout above. Mapping is
> mechanical: drop the numeric directory prefix, drop the numeric file prefix.
> Example: `udlm/40-governance/27-governance-matrix.md` →
> `udlm/governance/governance-matrix.md`. The execution phase will apply this
> rename uniformly.

### 1. `00-design-priorities.md`

**udlm sections** → `udlm/70-design-principles/00-design-priorities.md`
- *Design Principles as Interoperability Substrate* — Four invariant principles (consumer sovereignty, zero trust, federation, policy as code) form the contract foundation any realization must honor.
- *Authority Tiers (model definition)* — Ordered decision authority vocabulary (auto, reviewed, verified, authorized) plus custom extensions.
- *Profile Scaling Model (definition)* — Named profiles (minimal, dev, standard, prod, fsi, sovereign) with constraint matrices.

**dcm sections** → `dcm/architecture/design-principles.md`
- *Design Priorities: Implementation Choices* — Specific trade-offs (latency vs governance rigor, velocity vs stability).
- *Approval Tier Model (runtime enforcement)* — Tier-to-capability mappings and enforcement gates.
- *Profile-Governed System Constraints* — Per-profile enforcement of limits and validation modes.
- *Policy as Code Requirement* — Integration with external policy engines (OPA, etc.) and audit logging.
- *Documentation Discipline Requirements* — Internal governance for document lifecycle (status badges, related-doc links).

**Cross-ref:** dcm doc opens with: *"Implements the design principles defined in [udlm/70-design-principles/00-design-priorities.md]."*

---

### 2. `04-examples.md` — **resolved: all examples → udlm, separate dcm doc**

**udlm sections** → `udlm/00-foundations/04-examples.md` (kept clean — all examples)
- *VM Provisioning Example (basic intent-to-realized lifecycle)*
- *IP Allocation Example (allocation ownership)*
- *VLAN Attachment Example (cross-entity coordination)*
- *Brownfield Ingestion Example*
- *Drift Detection Example*

  Each example is rewritten to stay contract-level — describe what happens at
  each state without orchestration mechanics. Any paragraphs that wandered into
  "DCM does X" get dropped (those scenarios re-surface in the dcm examples doc).

**dcm sections** → `dcm/examples/orchestration-scenarios.md` (new — composed scenarios)
- *Three-Tier Application Example (full dependency group orchestration)*
- *VM Provisioning with timeout/cancellation propagation*
- *IP Allocation with provider's internal lifecycle reconciliation*
- New scenarios specific to dcm features (retry, scoring-driven placement, etc.)

**Cross-ref:** dcm doc opens with: *"Builds on the canonical examples in [udlm/00-foundations/04-examples.md] to illustrate dcm-specific orchestration features."*

**Resolution:** Originally proposed per-paragraph splitting; analogy made the
cleaner answer obvious — keep all udlm examples as clean contract illustrations,
let dcm write its own orchestration-scenarios doc fresh.

---

### 3. `06-resource-service-entities.md`

**udlm sections** → `udlm/10-entities/06-resource-service-entities.md`
- *Resource/Service Request vs Entity (fundamental distinction)*
- *Ownership Models (allocation, whole_allocation, full_transfer, hybrid_transfer)*
- *Entity Lifecycle (provider-side: requested, creating, created, deleting, deleted)*
- *Provider Internal Lifecycle and Notification Model* — what events providers emit and what fields they may update.

**dcm sections** → distributed across `dcm/architecture/convergence-engine/` and `dcm/architecture/control-plane/`
- *Request/Entity Relationship Management* — operational tracking → `convergence-engine/`
- *Ownership Model Enforcement at Dispatch* — dispatcher logic → `convergence-engine/`
- *Provider Notification Consumption* — receipt, validation, reconciliation → `runtime-features/` or `convergence-engine/`
- *Entity Lifecycle Monitoring* — polling/webhook detection → `runtime-features/`

**Cross-ref:** dcm convergence engine doc cites this udlm doc as the authoritative entity-lifecycle contract.

---

### 4. `13-ingestion-model.md`

**udlm sections** → `udlm/30-lifecycle/13-ingestion-model.md`
- *Brownfield Ingestion Problem Statement and Flow*
- *Enrichment Stages (discovery, enrichment, readiness)*
- *Transitional Tenant Mechanism*
- *Auto-Assignment Signals* — the contract; rules of which signals exist.
- *Ingestion Lifecycle (states: discovered, enriching, ready, ingested)*

**dcm sections** → `dcm/architecture/ingestion/engine.md`
- *Ingestion Engine Implementation*
- *Information Provider Integration (polling/webhook orchestration)*
- *Enrichment Policy Enforcement (specific rules, profile-driven)*
- *Transitional Tenant and Auto-Assignment Execution*
- *Ingestion Scheduling*

**Cross-ref:** dcm engine doc opens: *"Realizes the ingestion contract defined in [udlm/30-lifecycle/13-ingestion-model.md]."*

---

### 5. `19-auth-providers.md`

**udlm sections** → `udlm/40-governance/19-auth-providers.md`
- *Authentication Modes (built-in, GitHub/GitLab OAuth, LDAP, AD, OIDC, mTLS)* — taxonomy of supported mechanisms.
- *Multiple Provider Authentication* — multi-provider routing as a contract.
- *Credential Types and Issuance* — data model only.

**dcm sections** → `dcm/architecture/credentials-and-auth/auth-implementation.md`
- *Authentication Implementation within DCM* — library choices, integration mechanics.
- *Credential Management Service Integration*
- *Provider Authentication Routing Logic*
- *Session Management and Token Lifecycle*

**Cross-ref:** dcm doc cites udlm/40-governance/19-auth-providers.md as the mode-taxonomy contract.

---

### 6. `20-registry-governance.md`

**udlm sections** → `udlm/40-governance/20-registry-governance.md`
- *Three-Tier Registry Model (submission, review, publication)*
- *Proposal/Review/Publication Workflow* — the artifact lifecycle contract.
- *Versioning and Deprecation Lifecycle*
- *Resource Type Registry (standard type definitions + extension contract)*

**dcm sections** → `dcm/architecture/governance-enforcement/registry-enforcement.md`
- *Registry Governance Enforcement* — operational enforcement of the three-tier workflow.
- *Provider Selection Tie-Breaking* — selection algorithm when multiple providers match.
- *Artifact Lifecycle Management* — storage, versioning, deprecation warnings.
- *Review Queue and Approval Workflow* — review-tier mechanics.

**Cross-ref:** dcm doc: *"Enforces the registry contract in [udlm/40-governance/20-registry-governance.md]."*

---

### 7. `21-information-providers-advanced.md`

**udlm sections** → `udlm/20-contracts/21-information-providers-advanced.md`
- *Confidence Scoring and Hybrid Descriptor Model*
- *Authority and Priority Declarations*
- *Schema Versioning for Providers*
- *Well-Known Provider Registry (the contract for canonical providers)*

**dcm sections** → fold into `dcm/architecture/ingestion/engine.md`
- *Ingestion-Time Conflict Detection and Resolution*
- *Write-Back Capability Implementation*
- *Air-Gapped Verification Model*
- *Provider Priority and Fallback Logic*

**Cross-ref:** dcm ingestion engine doc cites this udlm doc as the trust/authority contract.

---

### 8. `24-operational-models.md`

**udlm sections** → `udlm/30-lifecycle/24-operational-models.md`
- *Timeout Model and State Machine* — deadline contract.
- *Cancellation Request and Propagation Model* — cancel state contract.
- *Orphan Detection and Prevention* — accountability contract.
- *Discovery Scheduling and Continuous Reconciliation* — reality-vs-intent contract.
- *Recovery Policy Model* — failure semantics contracts.
- *Compensation* — rollback contract.

**dcm sections** → `dcm/architecture/convergence-engine/recovery-and-retry.md`
- *Timeout Enforcement Mechanisms*
- *Cancellation Execution and Cleanup*
- *Orphan Detection Implementation*
- *Discovery Job Scheduling and Execution*
- *Recovery Policy Evaluation*
- *Compensation Execution*

**Cross-ref:** dcm doc: *"Implements the operational contracts in [udlm/30-lifecycle/24-operational-models.md]."*

---

### 9. `26-accreditation-and-authorization-matrix.md`

**udlm sections** → `udlm/40-governance/26-accreditation-and-authorization-matrix.md`
- *Data Classification Levels (restricted, sensitive, internal, public)*
- *Accreditation Model and Lifecycle*
- *Accreditation Gap Handling (policy options)*
- *Authorization Matrix (data/capability × subject/context)*
- *Zero Trust Interaction Model (five-check boundary)*
- *Federation Tunnel Model (the contract for secure inter-DCM channels)*

**dcm sections** → split between `dcm/architecture/governance-enforcement/accreditation-monitor.md` and `dcm/architecture/runtime-features/federation-runtime.md`
- *Accreditation Governance Enforcement* → accreditation-monitor
- *Authorization Evaluation at Runtime* → governance-enforcement
- *Zero Trust Boundary Implementation* → spans multiple dcm areas
- *Federation Tunnel Establishment and Maintenance* → federation-runtime
- *Profile-Governed Accreditation Constraints* → governance-enforcement

**Cross-ref:** all dcm fragments cite this udlm doc as the security-substrate contract.

---

### 10. `27-governance-matrix.md`

**udlm sections** → `udlm/40-governance/27-governance-matrix.md`
- *Unified Governance Matrix as Single Enforcement Point* (the architectural invariant)
- *Matrix Four Axes (Subject/Data/Target/Context)*
- *Rule Structure and Decision Vocabulary (ALLOW, DENY, STRIP_FIELD, REDACT, AUDIT_ONLY)*
- *Soft vs Hard Enforcement* (the distinction as a contract)
- *Field-Level Controls* (the granular policy contract)

**dcm sections** → `dcm/architecture/convergence-engine/policy-evaluation.md` (matrix-evaluator content merged here; no separate matrix-evaluator.md)
- *Evaluation Algorithm*
- *Hard Enforcement Mechanics*
- *Soft Enforcement Execution*
- *Sovereignty Zone Management*
- *Profile-Governed Policy Configurations*
- *Policy Caching and Invalidation*

**Cross-ref:** dcm doc: *"Implements the governance matrix contract in [udlm/40-governance/27-governance-matrix.md]."*

---

### 11. `28-federated-contribution-model.md` — **resolved by wire-compat decision**

**udlm sections** → `udlm/40-governance/28-federated-contribution-model.md`
- *Four Contributor Types (Platform Admin, Consumer/Tenant, Service Provider, Peer DCM)* — federated actor taxonomy.
- *Contribution Artifact Types (resource types, policies, profiles, accreditations, locations, credentials, provider definitions)*
- *Universal Contribution Pipeline (submission → review → publication)* — governance invariant.
- *Consumer/Provider/Federation Contribution Models* — what each contributor type may contribute (this is contract: who may write what).
- *Artifact Lifecycle and Versioning*

**dcm sections** → `dcm/architecture/governance-enforcement/contribution-pipeline.md`
- *Contribution Store Structure*
- *Review Queue and Approval Workflow* (GitOps PR mechanics live here)
- *Contribution Pipeline Orchestration*
- *Consumer Contribution Enforcement*
- *Provider Contribution Integration*
- *Federation Contribution Synchronization*

**Cross-ref:** dcm doc: *"Operationalizes the contribution contract in [udlm/40-governance/28-federated-contribution-model.md] via a GitOps-style PR workflow."*

**Note:** The GitOps-specific bits (PR review, branch protection rules) are a dcm choice. A peer of dcm could use a different review channel.

---

### 12 + 13. `31-credential-management.md` + `31-credential-provider-model.md` — **resolved: merged on both sides**

**udlm sections** → `udlm/governance/credentials.md` (one consolidated doc)
- *Credential Scope (DCM-internal vs consumer-facing)*
- *Credential Types (api_key, JWT, mTLS cert, SSH key, secret, signing key, HSM-backed, dcm_interaction)* — full taxonomy
- *Credential Lifecycle (issuance, active, rotation, revocation, expired)*
- *Rotation Protocol (parallel validity windows)* — contract
- *Revocation Model and Propagation* — contract
- *Consumer Credential Delivery* — the contract, not the mechanism
- *Provider API Contract for Credentials* — how providers accept credentials
- *Cryptographic Requirements* (defers to standards catalog)
- *Registration and Profile-Governed Configuration* — the constraint vocabulary

**dcm sections** → `dcm/architecture/credentials-and-auth/credentials.md` (one consolidated doc)
- *Credential Storage and Access Control*
- *Credential Generation Implementation*
- *Issuance Flow Orchestration*
- *Rotation Job Scheduling and Execution*
- *Revocation Enforcement Across Providers*
- *Consumer Delivery Mechanics*
- *Provider Authentication Validation*
- *Profile-Governed Constraints (enforcement)*
- *Integration with External Services*

**Cross-ref:** dcm doc opens: *"Implements the credential contracts in [udlm/governance/credentials.md]."*

**Resolution:** The historical 31a/31b split (management vs provider-model) was confusing — heavy overlap, unclear boundary. Wire-compat decision forced consolidation: peers must agree on a single credential model for interop.

---

### 14. `32-authority-tier-model.md`

**udlm sections** → `udlm/40-governance/32-authority-tier-model.md`
- *Core Authority Tier Model (auto, reviewed, verified, authorized)*
- *Decision Gravity Vocabulary* — what decisions require what tiers.
- *Custom Tier Definition and Contribution* — extension contract.
- *Tier Registry Change Impact Detection with Degradation Review Gate* — approval continuity contract.

**dcm sections** → `dcm/architecture/credentials-and-auth/authority-enforcement.md`
- *Tier Evaluation Algorithm*
- *Approval Authority Mapping*
- *Profile Threshold Configuration*
- *DCMGroup Assignment*
- *Tier Enforcement at Decision Points*
- *Degradation Review Orchestration*

**Cross-ref:** dcm doc: *"Enforces the authority tier contract in [udlm/40-governance/32-authority-tier-model.md]."*

---

### 15. `37-scheduled-requests.md`

**udlm sections** → `udlm/30-lifecycle/37-scheduled-requests.md`
- *Scheduling Model (immediate, at, window, recurring)* — deferral contract.
- *Request State During Deferral (SCHEDULED state, paused at ACKNOWLEDGED)*
- *Maintenance Windows* — coordination contract.
- *Deadline Enforcement* — scheduling deadline contract.

**dcm sections** → `dcm/architecture/runtime-features/scheduling.md`
- *Request Scheduler Component*
- *Deferred Request Lifecycle Management*
- *Maintenance Window Scheduling Logic*
- *Deadline Evaluation and Timeout Enforcement*
- *Consumer API Additions* (endpoints)
- *New Events* (request.scheduled, request.activation_pending, etc.)
- *Profile-Governed Scheduling Constraints*

**Cross-ref:** dcm doc: *"Implements the scheduling contract in [udlm/30-lifecycle/37-scheduled-requests.md]."*

---

### 16. `38-request-dependency-graph.md`

**udlm sections** → `udlm/30-lifecycle/38-request-dependency-graph.md`
- *Request Dependency Group Structure* (group_uuid, group_handle, member set)
- *wait_for Values (acknowledged, approved, dispatched, realized)* — activation contract.
- *Field Injection Mechanism* — propagation contract.
- *PENDING_DEPENDENCY Status* — blocked-state contract.
- *Failure Handling (on_failure: cancel_remaining | continue)* — propagation policy contract.
- *Group Timeout* — group-level deadline contract.
- *Relationship to composite service definitions* — scoping guidance.

**dcm sections** → `dcm/architecture/convergence-engine/dependency-orchestration.md`
- *Request Dependency Graph Submission and Parsing*
- *Dependency Resolution and Dispatch Orchestration*
- *PENDING_DEPENDENCY State Lifecycle*
- *Failure Handling Execution*
- *Group Timeout Enforcement*
- *Consumer API Endpoints*
- *New Events*
- *Profile-Governed Constraints*

**Cross-ref:** dcm doc cites this udlm doc as the multi-request coordination contract.

**Note:** Agent's output referenced `30-meta-provider-model.md` which doesn't exist — actual file is `30-composite-service-model.md`. Reference is to **composite service model**, which is pre-defined ordering vs ad-hoc dependency groups.

---

### 17. `40-standards-catalog.md`

**udlm sections** → `udlm/90-reference/40-standards-catalog.md`
- All six normative standards groups (identity/access, auth protocols, crypto, data model/serialization, operational, compliance) — these are external standards we cite as substrate requirements.

**dcm sections** → `dcm/reference/implementation-standards.md`
- *Cryptographic Implementation Details* (which algorithms chosen)
- *Certificate and Key Management Procedures*
- *Authentication Protocol Integration* (which OAuth/OIDC/LDAP impl)
- *OpenAPI Implementation* (endpoint design choices)
- *Observability Implementation* (Prometheus/OTel choices)
- *Kubernetes Integration*
- *Compliance Configuration* (which standards enforced per profile)

**Cross-ref:** dcm doc: *"Selects implementations of the standards listed in [udlm/90-reference/40-standards-catalog.md]."*

**Note:** udlm portion is reference-only (citations, not new substrate). Still belongs in udlm because peers consuming udlm need to know what standards apply.

---

### 18. `43-provider-callback-auth.md` — **resolved: udlm contract is mechanism-neutral**

**udlm sections** → `udlm/contracts/provider-callback-auth.md` (mechanism-neutral two-layer contract)
- *Two-Layer Authentication Contract* — abstract: any callback MUST be validated via two independent identity factors. Specific mechanisms (mTLS, JWT, signed assertions, etc.) are realization choices declared via schema-sharing.
- *Provider Identity Attestation Contract* — peers MUST attest provider identity at registration via a verifiable mechanism (the verification approach is realization-declared).
- *Callback Credential Lifecycle* — issuance, active, rotation, revocation states (technology-neutral).
- *Authentication-at-Callback-Time Contract* — every callback MUST present both factors; the receiving peer MUST validate both before accepting.
- *Entity-Level Authorization Contract* — credentials are scoped; peer MUST verify the provider's authorization to update the target entity.
- *Bootstrap Contract* — initial registration requires an authenticated single-use token; mechanism is realization-declared.
- *Credential Revocation Contract* — revocation is immediate; peers MUST recognize and reject revoked credentials.

**dcm sections** → `dcm/architecture/credentials-and-auth/provider-callback.md` (DCM's specific mechanism: mTLS + interaction credential)
- *mTLS as Layer 1 — DCM's identity-attestation mechanism*
- *Interaction Credential as Layer 2 — DCM's credential mechanism*
- *Provider Certificate Storage and Validation*
- *Interaction Credential Issuance and Management*
- *mTLS Enforcement at Callback Endpoint*
- *Credential Validation Logic at Callback Time*
- *Entity Authorization Checks*
- *Registration Token Generation and Validation*
- *Revocation Enforcement*
- *Emergency Revocation Response*

**Cross-ref:** dcm doc opens: *"Realizes the two-layer auth contract in [udlm/contracts/provider-callback-auth.md] using mTLS + interaction credential. The specific mechanism is declared in DCM's schema bundle per [udlm/contracts/schema-sharing.md]."*

**Resolution:** Per user direction — udlm defines abstract contract; dcm picks specific mechanism. Peer realizations declare their chosen mechanism via the schema-sharing protocol so federation peers can interoperate.

---

### 19. `48-location-topology-layers.md` — **resolved: tighten udlm to contract-only; hierarchy moves to dcm**

**udlm sections** → `udlm/60-topology/48-location-topology-layers.md` (contract only)
- *Layered-Topology Contract* — "topology consists of layers; layers have parent/child relationships; layers carry typed fields" (abstract, not the specific 9 layers)
- *Location Layer Instance Format* — the data structure for representing a layer instance
- *Hierarchy Assembly Rules* — what makes a parent/child relationship valid (contract, not the specific tree)
- *Location Layer Lifecycle (active, deprecated, decommissioned)*
- *Custom/Extension Mechanism* — how new layer types are added

**dcm sections** → split between:
1. `dcm/architecture/topology/canonical-9-layer-hierarchy.md` — the specific Country → Region → Zone → Site → Data Center → Hall → Cage → Rack → Unit hierarchy (DCM's canonical default; a peer realization could pick differently)
2. `dcm/architecture/topology/placement-and-priority-bands.md`
   - *Location Topology Database and Query Interface*
   - *Priority Band Allocation* (premium/standard/budget)
   - *Consumer Selection Model* (preference matching)
   - *Authority and Ownership Model*
   - *Relationship to Placement Engine*
   - *Location Layer Lifecycle Management* (operational draining, re-placement)
   - *Profile-Governed Topology Constraints*

**Cross-ref:** dcm hierarchy doc opens: *"Realizes the layered-topology contract in [udlm/60-topology/48-location-topology-layers.md] with DCM's canonical 9-layer scheme."*

**Resolution:** Analogy made the call clear — "addresses are layered" is rule of the road; "the layers are Country, Region, Zone..." is the specific addressing scheme this jurisdiction picked.

---

### 20. `51-infrastructure-optimization.md` — **resolved: PostgreSQL mandate moves to dcm**

**udlm sections** → `udlm/70-design-principles/51-infrastructure-optimization.md`
- *Data Contracts vs Abstraction Layers* (the principle — no abstraction-hiding allowed)
- *Four Data Domains (Intent, Requested, Realized, Discovered)* — restatement as foundational domains.
- *Mandatory Persistence Requirement* — the contract that all four domains must be persistently queryable. **Note: persistence is required; the technology is not specified here.**

**dcm sections** → split between:
1. `dcm/architecture/persistence/postgres-mandate.md` — the decision that this dcm realization mandates PostgreSQL (a dcm-level architectural choice; a peer realization could pick differently while honoring the udlm persistence contract)
2. `dcm/architecture/persistence/postgres-implementation.md`
   - *Enforcement Mechanisms for Required Infrastructure*
   - *Data Domain Implementation Details* (table structures, schema)
   - *Query Optimization and Indexing*
   - *Data Retention and Archival Policies*

**Cross-ref:** dcm doc: *"Realizes the persistence contract in [udlm/70-design-principles/51-infrastructure-optimization.md] by mandating PostgreSQL for DCM."*

**Resolution:** Per analogy — "must have a road" is rule of the road; "the road is paved asphalt with painted lines" is a jurisdictional infrastructure choice.

---

### 21. `53-capability-discovery.md`

**udlm sections** → `udlm/20-contracts/53-capability-discovery.md`
- *Problem Statement (types vs capabilities)* — modeling contract.
- *Unified Provider Model* — provider registration contract.
- *Capability Declaration Format and Semantics* — provider description contract.

**dcm sections** → fold into `dcm/architecture/convergence-engine/overview.md` (or new file)
- *Provider Registry Implementation with Capabilities*
- *Capability Matching for Dispatch Decisions*
- *Backward Compatibility with Type-Based Model*
- *Capability Validation and Conflict Resolution*

**Cross-ref:** dcm doc cites this udlm doc as the capability declaration contract.

---

## Hardest calls — all resolved by wire-compatibility decision

1. ~~**`04-examples.md`**~~ — **RESOLVED**: all examples kept clean in udlm; dcm gets its own `orchestration-scenarios.md`. No per-paragraph splitting.

2. ~~**`28-federated-contribution-model.md`**~~ — **RESOLVED**: split as proposed. Wire-compatibility means contributor types + artifact formats ARE wire-level concerns peers must agree on; GitOps PR is dcm's transport for contributions, not the contract.

3. ~~**`43-provider-callback-auth.md`**~~ — **RESOLVED**: udlm defines the **two-layer auth contract abstractly** (any peer must validate provider identity via two independent factors). dcm specifies **mTLS + interaction credential** as its specific mechanism. Peer realizations could pick different layers and still conform — provided they declare their auth mechanism via the schema-sharing protocol.

4. ~~**`48-location-topology-layers.md`**~~ — **RESOLVED**: layered-topology contract + assembly rules + lifecycle → udlm. Specific 9-layer hierarchy → dcm canonical default.

5. ~~**`51-infrastructure-optimization.md`**~~ — **RESOLVED**: PostgreSQL mandate moves to dcm. udlm keeps data-contract principle + four-domains contract + persistence-required contract (technology-neutral).

6. ~~**`31-credential-management.md` + `31-credential-provider-model.md`**~~ — **RESOLVED**: merge to `udlm/governance/credentials.md` (udlm side) and `dcm/architecture/credentials-and-auth/credentials.md` (dcm side).

---

## Newly identified udlm contracts (from "rules of the road" sweep)

User clarification (a/b/c) and a follow-up sweep of existing docs surfaced
**7 net-new substrate documents** that were missing, partially specified, or
scattered. **All 7 have been drafted** in `architecture/data-model/` and will
migrate to udlm during the split.

### Created (drafts in dcm/architecture/data-model/, target paths in udlm shown)

| Doc | Target path | Draft location | Status |
|---|---|---|---|
| **Identifier scheme contract** | `udlm/contracts/identifier-scheme.md` | `architecture/data-model/identifier-scheme.md` | ✅ Drafted |
| **Time and clock model** | `udlm/contracts/time-and-clock.md` | `architecture/data-model/time-and-clock.md` | ✅ Drafted |
| **Error model contract** | `udlm/contracts/error-model.md` | `architecture/data-model/error-model.md` | ✅ Drafted (incl. `conformance.*` namespace) |
| **Retry semantics contract** | `udlm/contracts/retry-semantics.md` | `architecture/data-model/retry-semantics.md` | ✅ Drafted |
| **Rate limit + backpressure contract** | `udlm/contracts/rate-limit-and-backpressure.md` | `architecture/data-model/rate-limit-and-backpressure.md` | ✅ Drafted |
| **Schema sharing protocol** | `udlm/contracts/schema-sharing.md` | `architecture/data-model/schema-sharing.md` | ✅ Drafted |
| **Conformance specification** | `udlm/CONFORMANCE.md` | `architecture/data-model/CONFORMANCE.md` | ✅ Drafted |

### Sufficient as-is (no new doc needed)

- **Idempotency contract** — `33-event-catalog.md` already covers it at substrate quality (event_uuid as idempotency key, at-least-once semantics, consumer-supplied Idempotency-Key). Just needs to be cross-referenced from new related docs.

### Perspective docs (the "handbooks") — authored

Two complementary perspective docs, one per layer. **Authored** during the
split execution phase:

| Doc | Target path | Purpose | Status |
|---|---|---|---|
| **Consumer perspective (driver's handbook)** | `udlm/docs/consumer-perspective.md` | How a consumer sees the system: onboarding, mental models, request lifecycle, common patterns, troubleshooting — written from the user's POV against the substrate | ✅ Done |
| **Operator perspective (DMV operator's manual)** | `dcm/architecture/operator-perspective.md` | How an implementer/operator sees the system: how DCM operationalizes udlm, where the realization choices live, deployment perspective, ops playbook entry point | ✅ Done |

### Sweep findings — what was checked and verdict

| Concept | Found | Verdict |
|---|---|---|
| Identifier scheme | Scattered across 06, 02, 33, A, 45 | Gap — needs new substrate doc |
| Idempotency | Thorough in 33, 18, 06, 23, 25, 31b, A | Substrate quality — keep |
| Backpressure / rate limit | Strong in 49, 18, 37, 53 | Mixed — extract substrate portion |
| Time / clock model | Scattered in 40, 33, 16, 12, 37, 52 | Gap — needs new substrate doc (UTC contract, ms precision, skew tolerance, total ordering) |
| Error model | Minimal in consumer-api-spec, 31b, B | Gap — needs new substrate doc with closed error vocabulary |
| Retry semantics | Operational in 24, 25, 7, 30, 37, 23, 50 | Partial — extract + new substrate framing |
| Consumer perspective | Minimal (04-examples is closest) | Gap — needs net-new driver's handbook |

---

## Execution sequence (Phase 2-3)

Mechanical work, in order:

1. **Create empty `udlm` git repo** at `github.com/croadfeldt/udlm`.
2. **Use `git filter-repo`** to extract `architecture/data-model/` history into the new repo, preserving commits. Reorganize into the LOCKED udlm layout in a single restructure commit (drop all numeric prefixes; move files into their target directories).
3. **For each "both" file**: split into udlm + dcm fragments per the per-section blocks above. Apply the rename mapping at the same time. Single commit per file ("split N-foo.md: udlm/dcm portions").
4. ~~Author the 6 new udlm contract docs + CONFORMANCE.md~~ ✅ **DONE** — drafted in `architecture/data-model/`. Execution moves them to their target paths in udlm during step 2.
5. ~~Author the two perspective docs~~ ✅ **DONE** — authored at `udlm/docs/consumer-perspective.md` and `dcm/architecture/operator-perspective.md`.
6. **Update cross-references**: add the `> Implements...` header to every dcm doc that has a udlm counterpart. Cross-link the new substrate docs from anywhere they're referenced. Update intra-doc references in the 7 new contract docs to drop their `(N-...)` legacy path hints.
7. ~~Add `conformance.version_deprecated` federation event~~ ✅ **DONE** — wired into `udlm/contracts/event-catalog.md` (introduced by `CONFORMANCE.md` §9.2).
8. **Delete migrated files from dcm** in one cleanup commit.
9. **Update dcm `README.md` and `project-overview`** to reference udlm as the substrate spec.
10. **Commit `00-layering-data-model-vs-dcm.md`** with concrete repo links now resolvable.

## After split (Phase 4-5) — DAV plumbing

- DAV MCP doc-fetcher gets two source repos (`udlm` + `dcm`).
- UC YAML `spec_refs` use namespaced paths: `udlm/governance/governance-matrix.md` and `dcm/architecture/convergence-engine/policy-evaluation.md`.
- Source ConfigMap split: separate mountpaths.
- Run one sample UC eval to validate cross-repo resolution.

---

## Decision log

All blocking decisions are settled. This section is the durable record of
what was decided and why.

### Locked decisions

- ✅ **Compatibility model**: wire-compatible at data/event/contract boundary (versioning rules apply). udlm is K8s-shaped: API + CRD wire-compatible across distributions; controllers not portable.
- ✅ **Repo location**: `github.com/croadfeldt/udlm`
- ✅ **udlm numbering**: dropped (directory structure carries ordering)
- ✅ **dcm numbering**: dropped (flat, organized by concern)
- ✅ **Split manifest**: kept as permanent contextual doc in dcm (helps future contributors understand the boundary)
- ✅ **Examples**: all-udlm + new dcm `orchestration-scenarios.md`
- ✅ **Location topology**: contract → udlm, specific 9-layer hierarchy → dcm canonical default
- ✅ **PostgreSQL mandate**: → dcm (substrate requires persistence; technology choice is dcm-level)
- ✅ **Credentials (31a + 31b)**: merged on both sides (`udlm/governance/credentials.md`, `dcm/architecture/credentials-and-auth/credentials.md`)
- ✅ **Federated contribution**: split (wire-compat makes contributor types + artifact format a peer contract; GitOps PR is dcm's transport)
- ✅ **Provider callback auth**: udlm = abstract two-layer auth contract; dcm = mTLS + interaction credential mechanism; peers declare their chosen mechanism via schema-sharing
- ✅ **7 new udlm substrate docs drafted**: identifier-scheme, time-and-clock, error-model (with `conformance.*` namespace), retry-semantics, rate-limit-and-backpressure, schema-sharing, CONFORMANCE
- ✅ **Consumer perspective + operator perspective**: paired narrative docs authored at `udlm/docs/consumer-perspective.md` and `dcm/architecture/operator-perspective.md`
- ✅ **Single narrative directory**: `docs/` (no separate `guides/`)

### Open items (cosmetic / non-blocking)

- [ ] Final read-through could flag any reclassifications on the pure-udlm and pure-dcm file lists. Default: trust the agent's classification + the analogy validation.

### Items deferred to execution phase

- Path rename: per-section split blocks (1-21 above) reference legacy numeric paths. Execution will apply the mapping uniformly (drop numeric prefixes from directories and filenames).
- ✅ `conformance.version_deprecated` federation event wired into `udlm/contracts/event-catalog.md` (introduced by CONFORMANCE.md §9.2).
- ✅ Two perspective docs authored (consumer-perspective.md, operator-perspective.md).
