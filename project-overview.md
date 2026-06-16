# DCM — Project Overview

**GitHub:** https://github.com/dcm-project  
**License:** Apache 2.0

---

## What DCM Is

Data Center Management (DCM) is an open-source framework that gives enterprise IT organizations a hyperscaler-like cloud experience on infrastructure they own and control. It is the governing control plane that sits above provisioning tools, automation platforms, and infrastructure systems — making them coherent, governed, and self-service.

DCM is not a deployment tool, a configuration manager, or an automation platform. It is the management plane that connects them: a unified control plane with a declarative data model, a policy engine that enforces organizational standards automatically, and a service provider interface that integrates with the automation tools organizations already have.

### Architecture in One Sentence

DCM is built on three foundational abstractions — **Data**, **Provider**, and **Policy** — connected by a policy-driven event loop. Every concept in the architecture maps to one of these three.

```
Event (Data state change)
  → Policy Engine evaluates all matching Policies
  → Policies produce decisions / mutations / actions
  → Actions invoke Providers or produce new Data
  → New Data triggers new Events
  → Repeat
```

---

## The Problem DCM Solves

Enterprise on-premises infrastructure is managed by dozens of disconnected tools, teams, and manual processes. A single virtual machine might require five teams, three ticketing systems, and two weeks to provision. No one has a trustworthy, real-time answer to: *what exists, what was requested, what was actually provisioned, and does the current state match what was intended?*

The gap between intended state and actual state is where compliance risk, operational toil, and security incidents live.

Specifically:

**Fragmented operations.** Organizations spend engineering capacity stitching together disparate automation efforts rather than delivering services. Functionality is trapped in monoliths or siloed teams. There is no unified service catalog or API interface — capabilities that public clouds provide as table stakes.

**Long time-to-market.** The lifecycle of a single infrastructure asset is managed by many teams, with approvals, provisioning, and auditing taking weeks. Operations teams face high toil in day-to-day management.

**The private cloud gap.** True private cloud requires networking, storage, identity, catalogs, FinOps, observability, auditing, and risk management — not just on-premises compute. Most organizations have the compute but not the surrounding governance layer.

**Unreliable data.** There is typically no reconciliation between discovered inventory (what actually exists) and intended inventory (what was requested). Without a unified data model, it is impossible to know whether current state is aligned with deployed state, and intended state is often not stored at all.

**Compliance overhead.** In regulated environments (financial services, government, defense, healthcare), compliance evidence must be produced manually from systems that were not designed to provide it. DCM makes compliance evidence a structural property of every operation — built into the data, not reconstructed after the fact.

---

## What DCM Does

DCM manages the complete lifecycle of infrastructure resources — from bare metal hardware and network gear at the physical layer through virtual machines, containers, Kubernetes clusters, and application platforms. The lifecycle includes Day 0 (standing up new infrastructure), Day 1 (provisioning resources), Day 2 (operating and managing), and Day N (decommissioning and releasing).

### The Three Foundational Abstractions

**Data** is everything that exists in DCM — resource entities, policy definitions, data layers, audit records, accreditations, group memberships. Every artifact has a UUID, a lifecycle state, a schema type, and complete field-level provenance recording where every value came from and why it changed. Data flows through the system in four states:

| State | What It Represents |
|-------|-------------------|
| **Intent** | What the consumer originally asked for — immutable after submission |
| **Requested** | The fully assembled, policy-approved dispatch payload — what was sent to the provider |
| **Realized** | What the provider actually provisioned — the authoritative record of what exists |
| **Discovered** | What currently exists in the environment — used to detect drift |

Comparing these four states continuously is how DCM detects drift, enforces governance, and enables rehydration (replaying original intent through current policies to reproduce a resource in a new location or after failure).

**Policy** is every rule that governs DCM behavior — expressed as code, stored in Git, versioned, tested in shadow mode before activation, and enforced deterministically. Eight typed policy schemas cover every governance need:

| Policy Type | What It Does |
|-------------|-------------|
| **GateKeeper** | Halts requests or contributes weighted risk scores for approval routing |
| **Validation** | Checks structural correctness; halts on failure or accumulates advisory warnings |
| **Transformation** | Automatically enriches request payloads (injects values, enforces field locks) |
| **Orchestration Flow** | Defines named workflows as explicit, ordered pipeline steps |
| **Recovery** | Governs what DCM does when things go wrong (timeout, failure, drift) |
| **Governance Matrix Rule** | Enforces data classification and sovereignty boundaries at every cross-boundary interaction |
| **Lifecycle** | Triggers actions on entity state changes (TTL expiry, scheduled operations) |
| **ITSM Action** | Creates and updates records in connected ITSM systems as a side-effect of pipeline events |

Every business rule, every compliance constraint, every operational standard is a Policy — never hard-coded, always auditable, always testable in shadow mode before enforcement.

**Providers** are everything external that DCM integrates with. Six provider types share a common base contract (registration, health, mTLS, sovereignty declaration, accreditation, governance matrix enforcement) and add typed capability extensions:

| Provider Type | Capability |
|--------------|-----------|
| **Service Provider** | Realizes infrastructure resources (VMs, networks, storage, containers, bare metal). Also covers credentials (internal or Vault), notifications (email/Slack), and ITSM integration via resource type declarations. |
| **Information Provider** | Serves authoritative external data (CMDB, HR, finance, identity systems) |
| **Composite Service** | A catalog item composed of multiple constituent resource types (a "three-tier web app" as a single catalog entry); registered by an ordinary Service Provider, not a separate provider type |
| **Auth Provider** | Authenticates identities; resolves role and group memberships. Multiple auth providers enable tenant-routed authentication. |
| **Peer DCM** | Another DCM instance participating in federated deployment |
| **Process Provider** | Executes ephemeral workflows (software install, backup, migration, compliance scan) via automation platforms (AAP, Tekton) |

### What This Enables

A consumer can browse a Service Catalog showing only the resources they are entitled to request, configure their requirements, submit a request, and receive a provisioned resource — with full cost attribution, audit trail, drift monitoring, and decommissioning capability — without ever interacting with any underlying automation tool directly.

Organizational standards, security requirements, placement constraints, and data sovereignty rules are enforced automatically by the Policy Engine before anything is dispatched to a provider. There are no runbooks to follow correctly. The correct behavior is structural.

---

## Who Benefits

### Consumers — Application Teams and Developers

Self-service infrastructure that matches the experience of public cloud, on infrastructure the organization controls. Browse a catalog, configure requirements, submit a request, receive a provisioned resource. No tickets to raise, no teams to coordinate with, no runbooks to follow.

### Platform Engineers and Infrastructure Operations

A single control plane rather than a collection of disconnected tools. Define the service catalog, write policies that enforce organizational standards, manage the provider ecosystem. Provisioning consistency is structural. Drift is detected automatically. Day 2 toil is governed by policy, not enforced by individual operators following runbooks.

### Security and Compliance Teams

Policy-as-code tested before activation (shadow mode), enforced at every pipeline stage, producing a tamper-evident audit trail at every state transition. Data classification (PHI, restricted, sovereign) is a first-class concept enforced at the Governance Matrix layer — always boolean, never scoreable around. Accreditation monitoring automatically verifies provider certifications against external registries (FedRAMP marketplace, CMMC AB, ISO IAF CertSearch) so compliance posture is continuously verified rather than point-in-time attested.

### SRE and Operations Teams

Complete observability into what was requested, what was provisioned, whether it matches, and what changed. Drift detection compares Realized State against Discovered State and triggers remediation per policy. Four states give a complete picture of the gap between intent and reality at any moment.

### Auditors

A complete, chronological, tamper-evident record of every change to every artifact — who made it, when, through what authorization chain, and what the values were before and after. The audit hash chain means any deleted or modified record is detectable. Field-level provenance means every value in every record can be traced to its origin.

### FinOps and Business Leadership

Cost attribution built into the provisioning pipeline. Every resource has a cost estimate before provisioning and ongoing cost attribution to the owning Tenant and business unit throughout its lifecycle. Pre-request cost estimates, placement tie-breaking by cost, and consumer-visible cost views are all standard capabilities.

---

## Where DCM Operates

DCM operates in the control plane layer of an enterprise data center estate. It is infrastructure-agnostic — it does not care whether the underlying infrastructure is bare metal servers, VMware clusters, OpenStack clouds, Kubernetes clusters, or network equipment. Service Providers abstract those differences. DCM manages all of them through the same interface and data model.

### Deployment Topology

| Mode | Description |
|------|-------------|
| **Single-region** | One DCM instance governs one data center or regional infrastructure estate |
| **Federated multi-instance** | Multiple DCM instances with declared trust relationships route requests across regional and organizational boundaries |
| **Hub/Regional** | Hub DCM holds the authoritative registry and global policy hierarchy; Regional instances handle local provider routing and operate independently during hub unavailability |
| **Sovereign/Air-gapped** | Full air-gapped operation with HSM-backed key storage, local credential management, and no external network dependencies |

### Data Sovereignty

DCM enforces data sovereignty as a structural property, not a configuration option. Every entity carries sovereignty zone declarations that constrain which stores may hold copies and which Service Providers may handle the data. The Governance Matrix enforces these boundaries at every cross-boundary interaction — and it is always boolean. No scoring, no exceptions, no policy can route around a declared sovereignty constraint.

### Target Environments

DCM specifically targets organizations with on-premises infrastructure that must behave like a cloud — particularly in regulated industries:

- **Financial services** — where public cloud is constrained by regulatory requirements, data residency, and audit obligations
- **Government and defense** — where FedRAMP, CMMC, DoD Impact Level authorization, and air-gapped operation are operational requirements
- **Healthcare** — where HIPAA BAA requirements and PHI data classification impose specific placement and access constraints
- **Critical infrastructure** — where sovereignty over the infrastructure itself is as important as sovereignty over the data

These are also the environments where the gap between what on-premises infrastructure currently provides and what organizations need is widest — and where DCM's compliance framework integrations (FedRAMP, CMMC, HIPAA, SOC 2, ISO 27001, PCI DSS, DoD Impact Levels) are built directly into the accreditation model rather than added as an afterthought.

---

## How DCM Works

### The Event Loop

DCM's runtime is a policy-driven event loop. There is no hard-coded pipeline — the pipeline is the sum of active policies responding to data state changes.

```
Event (Data state change — e.g., request submitted)
  → Policy Engine evaluates all matching Policies
  → Policies produce typed outputs:
      GateKeeper: approve / halt / risk score
      Validation: pass / fail / warning
      Transformation: inject fields / lock values / annotate provenance
      Placement: constraints + preferences → Provider selected
      Orchestration Flow: ordered step sequence
      Recovery: action when things go wrong
      Governance Matrix: ALLOW / DENY / STRIP / REDACT
  → Outputs invoke Providers or produce new Data
  → New Data changes trigger new Events
  → Repeat until terminal state
```

Every step is audited. Every field mutation carries provenance. Every decision is deterministic — the same data, evaluated by the same policies, produces the same outcome regardless of who submitted it or when.

### The Request Lifecycle

When a consumer submits a service request, DCM executes a governed assembly pipeline:

```
1. Consumer submits request (intent declared)
   → Intent State written (immutable snapshot of original ask)

2. Layer assembly
   → Core Layers applied (datacenter, rack, network zone, location)
   → Service Layers applied (resource-type-specific configuration)
   → Consumer fields merged
   → Transformation Policies inject and lock required fields

3. Policy evaluation
   → Validation Policies check structural correctness
   → GateKeeper Policies assess risk and enforce business rules
   → Placement Engine selects provider (constraints + scoring)
   → Requested State written (the approved, assembled dispatch payload)

4. Dispatch
   → CreateRequest sent to selected Service Provider
   → Provider naturalizes (translates DCM model to native format)
   → Provider executes
   → Provider denaturalizes (translates result back to DCM model)
   → Realized State written (what was actually provisioned)

5. Ongoing lifecycle
   → Discovery Scheduler polls for drift between Realized and Discovered State
   → Drift triggers Recovery Policy evaluation
   → TTL, scheduled operations, and rehydration operate on Realized State
   → Decommission mirrors provisioning in reverse
```

### How Policy Replaces Hard-Coded Logic

Every business rule in DCM is a Policy artifact — stored in Git, versioned, tested in shadow mode before activation, and enforced deterministically. There are no approval workflows embedded in code, no hard-coded placement rules, no statically defined pipeline stages.

This means:
- Adding a new approval step = writing a GateKeeper policy
- Changing where a resource is placed = updating a Placement policy  
- Auto-injecting a required field = writing a Transformation policy
- Defining what happens on failure = writing a Recovery policy
- Building a named multi-step workflow = writing an Orchestration Flow policy

Policy authoring is not an engineering task requiring code deployment. Policies are GitOps artifacts. They go through PR review, shadow evaluation (running against real traffic without enforcing), and staged activation. A new policy can go from idea to enforced governance without a code release.

### How Providers Integrate

Every provider implements one base contract: registration, health check, mTLS identity, sovereignty declaration, and governance matrix enforcement. What varies between provider types is the capability extension — the typed set of additional endpoints and behaviors that define what the provider can do.

This means DCM does not need to know in advance what automation tools an organization uses. A VMware vSphere cluster, a bare metal Redfish endpoint, a Kubernetes cluster via CAPI, and an OpenStack cloud all register as Service Providers. DCM speaks the same language to all of them. The provider handles translation to and from the native tool format — Naturalization (DCM → native) and Denaturalization (native → DCM).

Organizations do not replace their existing automation. They wrap it in the Provider interface. The investment in Ansible playbooks, Terraform modules, and vendor APIs is preserved — DCM adds the governance layer above it.

### How Data Sovereignty Is Enforced

Data sovereignty is not a configuration flag — it is a structural property evaluated at every boundary crossing. Every entity carries `sovereignty_zone` declarations. The Governance Matrix evaluates these at every provider dispatch, storage write, and federation routing decision. The result is always boolean: ALLOW or DENY. There is no scoring that can route around a sovereignty constraint.

For regulated environments: PHI data cannot be dispatched to a provider without a HIPAA BAA accreditation. Restricted data cannot leave a declared sovereignty zone. Classified data cannot be held by a provider without the declared authorization level. These are not policies an administrator can override — they are matrix rules with hard enforcement.

---

## Ethos

DCM is built on a specific set of values that drive every design decision. These are not marketing statements — they are the decision framework applied when priorities conflict.

### Security Is the Baseline, Not a Feature

Security properties are architecturally present in every profile, including the minimal development profile. What profiles control is enforcement strictness and operational overhead — not whether the property applies.

The `minimal` profile is "security with minimal operational overhead" — not "minimal security." It rotates credentials, audits first access, maintains a revocation registry, and runs shadow mode on all contributed policies. The intervals are longer, the triggers are more permissive, and manual steps replace automated ones — but the security model is present and correct.

When security and convenience conflict, security wins. But the design obligation is not just to enforce security — it is to make the secure path the easy path. A security model that is routinely bypassed because it is too burdensome has failed at both security and usability. The profile system exists precisely to make secure behavior automatic rather than effortful.

### The Governed Path Must Also Be the Easy Path

Self-service is not a nice-to-have — it is the mechanism through which governance is achieved at scale. If consuming resources through DCM is harder than raising a ticket or writing a one-off script, application teams will find the path of least resistance and all of DCM's governance benefits evaporate.

This principle shapes every interface decision: request submission should be a single API call; ordinary requests should auto-approve; policy authoring should not require Rego expertise for common cases; cost estimates should appear before a consumer commits. The score-driven auto-approval system exists specifically so that clean, standard requests are not gated on human review that adds no value.

Ease of use is not in tension with governance — it is the delivery mechanism for governance. Organizations that find DCM's governed path easier than ungoverned alternatives will use it. Those that do not will route around it.

### Compliance Is Constructed, Not Audited

Compliance evidence in DCM is a structural product of every operation, not something reconstructed after the fact. The audit trail is written at every state transition. Provenance is embedded in every field. The Governance Matrix enforces data classification boundaries at every crossing. Accreditation status is continuously monitored against external registries.

The implication: when an auditor asks "show me every person who touched this data between these dates," DCM can answer that question directly from the audit store without any manual evidence gathering. When a regulator asks "prove this data never left the EU," the Governance Matrix enforcement log answers the question with cryptographic tamper evidence.

This is different from compliance tooling that inspects systems and produces reports. DCM does not inspect systems and report findings — it governs operations and makes compliance a property of the operations themselves.

### The Architecture Should Be Easy to Implement and Extend

DCM is designed so that new capabilities fit within the existing three-abstraction model without modifying the core. A new provider type is a new implementation of the base contract with a new capability extension — no core changes. A new policy type is a new output schema — no core changes. A new data entity type is a new schema registration — no core changes.

This is the test: if a new capability can be expressed as Data, Provider, or Policy, it belongs in DCM and requires no architectural changes. If it cannot be expressed within these three abstractions, it is either a runtime implementation detail or a signal that the abstractions need to be reconsidered.

The same principle applies to organizations deploying DCM. They should not need to modify DCM source code to adapt it to their environment. New compliance requirements become policy additions. New infrastructure types become new provider implementations. New approval processes become custom authority tier definitions. DCM provides the framework; organizations provide the domain knowledge.

### No Silent Behavior

Every operation in DCM produces an observable artifact. No change is silent. No failure disappears into a log that no one reads. Every state transition produces an audit record. Every policy decision produces a typed output with a score driver. Every drift detection produces a record that links current state to intended state.

This is not just an audit requirement — it is an architectural property that makes debugging, compliance, and operational understanding possible. When something goes wrong in a governed system, the question "what happened and why" should always be answerable from the data the system produced as part of its normal operation.

---


## Key Facts

| | |
|-|-|
| **Architecture** | Three abstractions (Data, Provider, Policy) · Policy-driven event loop |
| **Provider types** | 12 (unified base contract + typed capability extensions) |
| **Policy types** | 8 (typed output schemas with deterministic evaluation) |
| **Entity lifecycle states** | 4 (Intent · Requested · Realized · Discovered) |
| **Capabilities** | 331 across 39 domains |
| **Data model documents** | 58 |
| **Specifications** | 15 |
| **OpenAPI paths** | 63 consumer · 57 admin · 5 operator · 7 provider callback |
| **Compliance frameworks** | FedRAMP · CMMC · HIPAA · SOC 2 · ISO 27001 · PCI DSS · DoD IL2–IL6 |
| **Deployment profiles** | minimal · dev · standard · prod · fsi · sovereign |
| **License** | Apache 2.0 |
| **Reference Implementation** | | **Reference Implementation** | [dcm-project/dcm-examples](https://github.com/dcm-project/dcm-examples) — Example #1: Summit Demo (OpenShift + AAP + ACM + RHDH) | — OpenShift + AAP + ACM + RHDH |
| **GitHub** | https://github.com/dcm-project |

---

## Core Design Principles

1. **Declarative** — data describes desired state, not procedures
2. **API-First** — every capability available via standard AEP-aligned API
3. **Policy-Governed** — all business logic through the Policy Engine, never hard-coded
4. **Idempotent** — applying the same data multiple times produces the same result
5. **Immutable if Versioned** — published versions never change; changes produce new versions
6. **Provider-Agnostic** — DCM defines contracts, not implementations
7. **GitOps-Native** — intent and policy artifacts are Git-native; versioned, reviewable, auditable
8. **Federated** — all authorized actor types contribute within permitted scope; no single administrator bottleneck
9. **Compliance by Construction** — audit trail, provenance, and sovereignty enforcement are structural, not added post-hoc

---

*DCM is open-source. Contributions, feedback, and discussion welcome at https://github.com/dcm-project*
