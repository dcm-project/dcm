# DCM — CNCF Strategy and Community Engagement Plan

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Strategy Document




**Version:** 0.1.0-draft  
**Status:** Draft  
**Document Type:** Strategic Planning  
**Maintainers:** Red Hat FlightPath Team  
**Last Updated:** 2026-03

---

## 1. Strategic Intent

DCM's goal is to become the community standard for enterprise data center and private cloud management — a neutral, open standard that the industry adopts the way it adopted CSI, CNI, and CRI. This requires DCM to exist in a community-trusted home, not as a vendor product.

The CNCF (Cloud Native Computing Foundation) is the appropriate home. It provides the neutral governance model, the community infrastructure, and the ecosystem relationships needed to drive broad adoption. The FSI consortium already engaging with DCM (leading FSI consortium members and others) provides the multi-organization sponsorship and real production use case evidence needed for a credible CNCF proposal.

---

## 2. CNCF Landscape and Positioning

### 2.1 Where DCM Fits

The CNCF landscape has strong coverage of Kubernetes runtime concerns — container runtimes, networking, storage, service mesh, observability. It has weaker coverage of the management plane — the layer above Kubernetes that governs what gets provisioned, owned, and decommissioned across multiple clusters and infrastructure types.

DCM fills this gap. It is not competing with existing CNCF projects — it extends and governs them.

**Related CNCF projects and how DCM relates:**

| CNCF Project | Relationship to DCM |
|-------------|---------------------|
| **Kubernetes** | DCM is a superset — extends Kubernetes upward to the management plane |
| **Crossplane** | Complementary — Crossplane provisions cloud resources via Kubernetes CRDs; DCM governs what Crossplane provisions and adds the management plane |
| **Cluster API (CAPI)** | DCM can manage Kubernetes clusters via CAPI as a Service Provider |
| **Argo CD / Flux** | Complementary — DCM governs provisioning requests; GitOps manages deployment |
| **OpenCost** | DCM's cost analysis is a superset — OpenCost data can feed DCM cost attribution |
| **Kessel** | Shares inventory and relationship goals — potential collaboration or alignment |
| **OPA/Gatekeeper** | DCM's Policy Engine uses OPA internally; Gatekeeper is the cluster-level enforcement |

### 2.2 The Gap DCM Fills

No current CNCF project addresses all of:
- Multi-cluster, multi-infrastructure lifecycle management from a single control plane
- First-class multi-tenancy with Tenant ownership model
- Policy governance with field-level override control across the full request lifecycle
- Data sovereignty and compliance evidence for regulated industries
- Service catalog with self-service consumer experience
- Cost attribution across heterogeneous infrastructure

This is the gap DCM fills. The positioning is not "another Kubernetes tool" — it is "the management plane that governs your entire data center, of which Kubernetes is one component."

---

## 3. CNCF Submission Path

### 3.1 CNCF Maturity Levels

CNCF accepts projects at three maturity levels:

| Level | Requirements | DCM Target Timeline |
|-------|-------------|---------------------|
| **Sandbox** | Alignment with CNCF mission, basic governance, active development | Target for initial submission |
| **Incubating** | Production users, healthy contributor base, defined governance, security audit | 12-18 months post-Sandbox |
| **Graduated** | Broad adoption, stable API, long-term maintainer commitment | 24-36 months post-Sandbox |

### 3.2 Sandbox Submission Requirements

For CNCF Sandbox acceptance, DCM needs:

**Technical requirements:**
- Clear alignment with CNCF's cloud native mission
- Open source license (Apache 2.0 — already in place)
- Publicly accessible source code (GitHub — already in place)
- Documented roadmap
- Basic security practices (vulnerability disclosure process, etc.)

**Governance requirements:**
- Defined governance model (maintainers, decision process)
- Code of conduct
- Multi-organization contributor base (this is the key requirement — Red Hat alone is insufficient)

**Community requirements:**
- Evidence of community interest beyond the founding organization
- At least one non-founding organization actively contributing

**DCM's strong position:**
The FSI consortium provides exactly the multi-organization evidence CNCF requires. Having leading FSI consortium members as active contributors or committed users is an unusually strong foundation for a Sandbox proposal. Most projects submit to Sandbox without any production users — DCM can submit with evidence of production interest from systemically important financial institutions.

### 3.3 Recommended Submission Path

**Step 1 — CNCF TAG (Technical Advisory Group) engagement**
Before formal submission, engage with CNCF TAG App Delivery and TAG Runtime. These groups review cloud native tooling proposals and can provide informal feedback before the formal Due Diligence process. Presenting DCM at a TAG meeting builds awareness and surfaces concerns early.

**Step 2 — Prepare the Due Diligence document**
The CNCF Due Diligence document is a detailed technical and governance questionnaire. Key sections: project description, statement on alignment with CNCF mission, comparison to similar projects, security practices, roadmap, adopters. The FSI consortium adopters section will be a significant differentiator.

**Step 3 — TOC sponsor identification**
CNCF Technical Oversight Committee (TOC) members sponsor project proposals. Red Hat's relationships in the Kubernetes community make identifying a TOC sponsor feasible. Target TOC members with expertise in multi-cluster management or enterprise Kubernetes.

**Step 4 — Sandbox vote**
TOC votes on Sandbox acceptance. With a strong Due Diligence document, FSI adopter evidence, and a TOC sponsor, acceptance probability is high.

---

## 4. Community Engagement Strategy

### 4.1 Operator Ecosystem — The Primary Leverage Point

The DCM Operator Interface Specification is the primary community artifact for driving ecosystem adoption. The strategy is to make conformance attractive enough that operator maintainers want to implement it.

**Priority operator communities for engagement:**

| Operator | Community | Why Priority | Engagement Approach |
|----------|-----------|-------------|---------------------|
| **KubeVirt** | Red Hat/Community | Active DCM development already | Direct contribution — DCM team contributes Level 2 support |
| **CloudNativePG** | CNPG Community | High FSI adoption — databases in regulated environments | Present DCM at CNPG community calls, contribute SDK example |
| **Strimzi (Kafka)** | Red Hat/Community | Messaging infrastructure — DCM Message Bus use case | Direct contribution via Red Hat maintainership |
| **Cert-Manager** | Jetstack/Venafi | Security resources — every DCM deployment needs certificates | SDK contribution, present at KubeCon |
| **ACM** | Red Hat | Cluster management — natural DCM complement | Direct — internal Red Hat alignment |
| **Rook (Ceph)** | CNCF | Storage operator — core DCM service provider use case | CNCF relationship — present at SIG Storage |

### 4.2 KubeCon Strategy

KubeCon is the primary conference for Kubernetes ecosystem influence. DCM needs a presence at KubeCon North America and Europe:

**KubeCon NA (target — next edition):**
- Submit a talk: "DCM — Managing the Management Plane: Kubernetes as a Component of Enterprise Infrastructure"
- Submit a contribfest session: hands-on DCM Operator SDK implementation workshop
- Engage Kubernetes SIG Cluster Lifecycle about CAPI integration

**KubeCon EU (following year):**
- Present CNCF Sandbox submission (if accepted by then)
- Case study talk with FSI consortium member (FSI consortium members presenting their DCM deployment)
- Operator Interface Specification BOF (Birds of a Feather) session

### 4.3 The Developer Value Proposition — What We Need to Communicate

The community message must be concrete and compelling, not abstract. Avoid "unified management plane" as the opener — lead with what operators get:

**For operator developers:**
> "Add DCM support to your operator and your users get self-service catalog, multi-tenancy, cost attribution, and cross-cluster management — for free. It takes one day using our SDK."

**For platform engineering teams:**
> "Manage your entire data center from one control plane. VMs, databases, Kubernetes clusters, networking — all with the same declarative model, the same policy engine, and the same audit trail."

**For FSI/regulated industry teams:**
> "Every provisioning request produces a complete audit chain — who asked for what, what policies applied, what was approved, what was built. Sovereignty constraints enforced at the management plane, not bolted on afterward."

### 4.4 Contributor Onboarding

A project cannot become a standard without contributors beyond the founding organization. The contributor onboarding strategy:

**Good first issues:**
Maintain a curated list of well-scoped, well-documented issues labeled `good-first-issue`. These should be achievable in a few hours without deep DCM knowledge — documentation improvements, test coverage, example implementations, SDK feature additions.

**Operator SDK examples:**
Each operator SDK example is a potential contributor touchpoint. An operator maintainer who wants to add DCM support to their operator is a natural contributor. The example for their specific CRD framework (kubebuilder, operator-sdk, raw controller-runtime) lowers the barrier.

**RFC process:**
Establish a lightweight RFC (Request for Comments) process for significant changes to the DCM Operator Interface Specification. This gives external contributors a formal path to influence the specification direction — which is essential for community trust.

**Monthly community calls:**
Regular community calls (video, recorded, published) signal active project health and give contributors a forum to discuss ideas. Target: bi-weekly during active development, monthly once stable.

---

## 5. Standards Positioning

Beyond CNCF, DCM should engage with relevant standards bodies where appropriate:

### 5.1 DMTF (Distributed Management Task Force)
DMTF maintains the TOSCA (Topology and Orchestration Specification for Cloud Applications) and other cloud management standards. DCM's data model has some conceptual overlap with TOSCA. Rather than competing, DCM should position as a Kubernetes-native, GitOps-native evolution of the same problem TOSCA addressed — bringing the conversation into the cloud native era.

### 5.2 FinOS Foundation
FinOS is the open source community for financial services. The FSI consortium involvement makes FinOS a natural secondary community for DCM. Presenting DCM at FinOS events reaches exactly the regulated industry audience that benefits most from DCM's sovereignty and compliance capabilities.

### 5.3 OpenInfra Foundation
The OpenInfra Foundation hosts OpenStack, Kata Containers, and StarlingX — all relevant to DCM's target environments (private cloud, edge, regulated infrastructure). DCM should present at OpenInfra Summit to the platform engineering teams who manage these environments.

---

## 6. What Needs to Exist Before CNCF Submission

The following artifacts must be ready before a CNCF Sandbox submission is credible:

| Artifact | Status | Owner | Target |
|----------|--------|-------|--------|
| DCM Operator Interface Specification v1.0 | 🔄 Draft | DCM Project | Ready |
| DCM Operator SDK v0.1.0 (Level 1 + Level 2) | 📋 Not started | DCM Project | 3-6 months |
| KubeVirt reference implementation (Level 2) | 🔄 In progress | DCM/KubeVirt teams | 3-6 months |
| Conformance test suite (Level 1 + Level 2) | 📋 Not started | DCM Project | 3-6 months |
| CNCF Due Diligence document | 📋 Not started | DCM Project | 6 months |
| Governance model document | 📋 Not started | Red Hat/Consortium | 3 months |
| Security vulnerability disclosure process | 📋 Not started | Red Hat Security | 1 month |
| FSI consortium adopter statements | 📋 Not started | Consortium members | 3 months |
| Second non-Red Hat maintainer | 📋 Not started | Community | 6 months |

---

## 7. Risk Considerations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CNCF TAG sees overlap with Crossplane | Medium | Medium | Prepare clear differentiation — DCM governs, Crossplane provisions; they are complementary |
| Operator communities resist specification adoption | Medium | High | Lead with SDK ease, reference implementations, concrete value; don't mandate, make it attractive |
| Red Hat perceived as controlling the standard | Medium | High | Establish CNCF governance early, actively recruit non-Red Hat maintainers, FSI consortium co-ownership |
| Specification fragmentation — forks or competing standards | Low | High | CNCF neutral governance prevents this; be the first mover in this space |
| Key contributor departure | Low | Medium | CNCF governance ensures project continuity beyond any single contributor |

---

## 8. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | Should the CNCF submission be for DCM as a whole or for the DCM Operator Interface Specification as a standalone standard? | Scope of submission | ✅ Resolved |
| 2 | Which FSI consortium members are willing to be named as public adopters in the CNCF submission? | Submission strength | ✅ Resolved |
| 3 | Is there a TOC member with relevant expertise who could sponsor the DCM proposal? | Submission path | ✅ Resolved |
| 4 | Should DCM engage with the Kubernetes SIG structure before or after CNCF Sandbox submission? | Community positioning | ✅ Resolved |
| 5 | What is the timeline for the KubeVirt reference implementation reaching Level 2 conformance? | Readiness milestone | ✅ Resolved |

---



## Resolution Notes

**Q1:** Submit the DCM Operator Interface Specification as a CNCF specification project first. CNCF Sandbox project submission for DCM as a whole follows once a reference implementation reaches Level 2 conformance. Submitting the specification standard separately lowers the implementation bar for initial acceptance and establishes the interface contract independently of any single implementation.

**Q2:** Identify a minimum of two named production evaluators and one FSI design partner before submission. At least one named organization should be willing to go on record. This is a project team action item — the architecture does not determine who those organizations are.

**Q3:** Target the App Delivery TAG and Runtime TAG for initial sponsor identification. Engage SIG App Delivery and SIG Cluster Lifecycle before submission — SIG members frequently become TOC sponsors. Project team action item.

**Q4:** SIG engagement comes before Sandbox submission. SIG App Delivery and SIG Cluster Lifecycle are the primary targets. The Cluster API overlap specifically must be addressed with SIG Cluster Lifecycle before submission. Pre-submission SIG engagement surfaces conflicts, identifies sponsors, and positions DCM as a collaborative project rather than a competing one.

**Q5:** Level 2 conformance requires: full dispatch/cancel/discover cycle, full realized state reporting, governance matrix enforcement at the provider boundary, and health check compliance. These requirements are now formally defined in the Operator Interface Specification. The project team estimates timeline based on available engineering resources against this defined scope.

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*

## Red Hat Developer Hub / Backstage Integration

DCM implements a Backstage plugin suite (`@dcm/backstage-plugin-*`) for deployment as RHDH Dynamic Plugins. This is the primary consumer-facing deployment model. See [RHDH Integration Specification](dcm-rhdh-integration-spec.md) for the complete architecture.

**CNCF alignment:** Backstage is a CNCF incubating project. DCM's RHDH integration follows CNCF best practices for developer portals and internal developer platforms (IDPs).

| Component | CNCF Status | DCM Use |
|-----------|------------|---------|
| Backstage | Incubating | Primary consumer GUI platform |
| Backstage Software Templates | Backstage feature | Auto-generated from DCM catalog items |
| Backstage Catalog | Backstage feature | DCMService and DCMResource entity kinds |
| Backstage Permission Framework | Backstage feature | DCM role → Backstage permission bridge |
