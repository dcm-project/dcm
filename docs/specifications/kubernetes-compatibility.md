# DCM — Kubernetes Compatibility and Concept Mappings


> ## 📋 Draft — Promoted from Work in Progress
>
> All questions resolved. Cluster-as-a-Service model defined. Namespace-to-Tenant mapping, admission webhook model, and managed K8s integration all specified.
>
> **This section is explicitly a work in progress and is less mature than the core DCM data model and architecture documentation.**
>
> The Kubernetes operator integration layer — including the Operator Interface Specification, Operator SDK API, and Kubernetes compatibility mappings — represents design intent that has not yet been validated against implementation. Specific interface contracts, API signatures, SDK method names, and CRD structures **will change** as implementation work begins.
>
> **Do not build against these specifications yet.** They are published to share design direction and invite feedback, not as stable contracts.
>
> Known gaps and open items for this section:
> - Operator Interface Specification: reconciliation hook signatures are provisional
> - Operator SDK API: Go module structure and dependency model not yet finalized
> - Kubernetes Compatibility Mappings: some concept mappings remain under discussion
> - SDK code examples are illustrative only — not yet tested against a real implementation
>
> Feedback and contributions welcome via [GitHub Issues](https://github.com/dcm-project/issues).



**Document Status:** ✅ Complete
**Document Type:** Architecture Reference  
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) | [Resource Type Hierarchy](https://github.com/croadfeldt/udlm/blob/main/entities/resource-type-hierarchy.md) | [Resource/Service Entities](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md)

---

## 1. Purpose

> **AEP Alignment:** API endpoint references in this document follow [AEP](https://aep.dev) conventions
> (custom methods use colon syntax). See `schemas/openapi/dcm-consumer-api.yaml` for the
> normative OpenAPI specification.


DCM is designed as a **superset of Kubernetes** — extending Kubernetes' declarative, controller-based model upward to provide unified management across multiple clusters, infrastructure types, and organizational boundaries that Kubernetes alone cannot address.

This document serves three purposes:

1. **Defines the formal mapping** between Kubernetes concepts and DCM concepts — enabling implementors to understand how the two models relate and where DCM extends beyond Kubernetes
2. **Establishes DCM Resource Types** for standard Kubernetes resources — so that Kubernetes-managed resources participate in the DCM registry alongside non-Kubernetes resources
3. **Documents the boundary** between what Kubernetes governs and what DCM governs — making clear that DCM extends Kubernetes rather than replacing it

---

## 2. The Superset Relationship

DCM is a superset of Kubernetes in the sense that it provides all the capabilities Kubernetes provides — and more. An organization running Kubernetes exclusively is using a subset of what DCM can manage. DCM does not replace Kubernetes; it manages the lifecycle of Kubernetes clusters and the resources running on them.

The superset relationship means DCM can manage Kubernetes-native resources (Deployments, Services, PersistentVolumes) through conformant operators, and it can manage the clusters themselves as catalog items. It also means DCM manages resources that have no Kubernetes equivalent — bare metal, VMs, VLANs, IP allocations, and organizational data entities.

### 2.1 What Kubernetes Provides

Kubernetes is a container orchestration platform that provides:
- Declarative desired-state management within a single cluster
- A controller/operator pattern for extending resource management
- Namespace-based isolation within a cluster
- RBAC for access control within a cluster
- A rich ecosystem of operators for managing complex stateful resources

### 2.2 What DCM Adds

DCM extends Kubernetes upward by providing:

| Capability | Kubernetes | DCM |
|------------|-----------|-----|
| Scope | Single cluster | Multi-cluster, multi-infrastructure |
| Tenancy | Namespace isolation | First-class Tenant model with ownership |
| Policy | RBAC + admission webhooks | Full Policy Engine with Validation/Transformation |
| Data lineage | Not provided | Field-level provenance on all data |
| Cost attribution | Not provided | Full lifecycle cost analysis |
| Drift detection | Basic — controller reconciles | Full four-state model with Intent/Requested/Realized/Discovered |
| Service catalog | Not provided | Full self-service catalog with RBAC-governed presentation |
| Sovereignty | Not provided | Sovereignty declarations, placement constraints, compliance evidence |
| Information context | Labels/annotations | First-class Information Provider relationships |
| Non-Kubernetes resources | Not provided | VMware, bare metal, OpenStack, etc. all managed through same model |

### 2.3 What DCM Does Not Replace

DCM does not replace Kubernetes at the runtime level. Kubernetes continues to:
- Schedule and run containers
- Manage Pod lifecycle within a cluster
- Enforce network policies within a cluster
- Provide the Kubernetes API for cluster-native tooling
- Run operators that manage complex stateful resources

DCM manages the management plane — the lifecycle of what gets requested, provisioned, owned, governed, and decommissioned. Kubernetes manages the execution plane — the runtime behavior of what is running.

---

## 3. Core Concept Mappings

### 3.1 Resource Model

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| Custom Resource Definition (CRD) | Resource Type Specification | CRD schema → DCM Resource Type fields | DCM Resource Type is the portable, provider-agnostic equivalent. CRD is the Kubernetes-specific implementation schema. |
| Custom Resource (CR) | Requested State payload → Realized State entity | CR is the naturalized form of the DCM payload | The operator translates DCM Requested State into a CR (Naturalization) and translates CR status back to DCM Realized State (Denaturalization). |
| Built-in resource (Pod, Service, PV) | DCM Resource Type in Compute.*, Network.*, Storage.* | Kubernetes built-ins are valid DCM Resource Types | See Section 5 for standard Kubernetes resource type mappings. |
| Kubernetes object | Resource/Service Entity | Every Kubernetes object managed by DCM has a corresponding DCM entity with UUID and provenance | |

### 3.2 Control Loop

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| Operator reconciliation loop | Realization + Drift Detection combined | Reconciliation IS the realization process — the operator drives actual state toward desired state | DCM's Drift Detection compares Discovered State against Realized State. The operator's reconciliation loop is the mechanism that corrects drift. |
| Desired state (CR spec) | Requested State | CR spec is the naturalized form of the DCM Requested State | DCM stores the Requested State in DCM format. The operator translates it to CR spec format. |
| Actual state (CR status) | Realized State | CR status is the Kubernetes-native form of the DCM Realized State | The operator must denaturalize CR status back to DCM Realized State format and report it to DCM. |
| Watch/Inform pattern | DCM Discovered State polling | Kubernetes watch events are the mechanism for keeping DCM Discovered State current | |

### 3.3 Isolation and Multi-tenancy

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| Namespace | DCM Tenant boundary | One namespace per DCM Tenant (per_tenant strategy) | Kubernetes namespace provides the physical isolation enforcement. DCM Tenant provides the ownership and governance model. A single DCM Tenant maps to exactly one namespace per cluster. |
| Namespace | DCM Resource Group | In shared namespace strategies, Resource Group labels replace namespace isolation | When multiple Tenants share a namespace, DCM Resource Group labels provide logical separation. |
| Kubernetes RBAC | DCM IDM/IAM + Policy Engine | Kubernetes RBAC is the runtime enforcement mechanism. DCM Policy Engine governs who can request what via the service catalog. | DCM policies determine what a user can request. Kubernetes RBAC determines what a running workload can do. These are complementary, not duplicative. |
| ServiceAccount | DCM Identity.ServiceAccount Information Type | Kubernetes ServiceAccounts that DCM provisions or references are modeled as DCM Information Type entities | |

### 3.4 Relationships and Dependencies

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| ownerReference | Entity Relationship (`contains`/`contained_by`) | Kubernetes ownerReferences are a subset of DCM entity relationships — ownership only | DCM relationships are richer — supporting `requires`, `depends_on`, `references`, `peer`, `manages` in addition to ownership. During Denaturalization, ownerReferences are translated to DCM `contains` relationships. |
| Finalizers | Lifecycle policy (`retain`, `detach`) | Kubernetes finalizers implement DCM lifecycle policies at the Kubernetes level | When DCM declares `on_parent_destroy: retain` for a storage entity, the operator implements this using Kubernetes finalizers to prevent deletion until DCM confirms the lifecycle policy has been applied. |
| Label selectors | Resource Group membership | Kubernetes label selectors used for DCM Resource Group filtering | DCM mandatory labels (`dcm-tenant-id`, `dcm-entity-id`) are used as label selectors for Resource Group queries. |

### 3.5 Data Model

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| Labels | DCM entity metadata + relationships | DCM-mandatory labels (`dcm-managed`, `dcm-tenant-id`, `dcm-entity-id`, etc.) carry core DCM identity data. Custom labels may map to DCM Information Type relationships. | |
| Annotations | DCM field-level provenance + metadata | Annotations used by DCM to carry request correlation data during the request lifecycle | `dcm-request-id` annotation on a CR identifies the DCM request that created or last modified it — enabling unsanctioned change detection. |
| Resource version | Entity version (Revision component) | Kubernetes resource versions map to DCM entity Revision increments | Major and Minor versions are managed by DCM based on breaking/non-breaking changes. Kubernetes resource version increments map to DCM Revision increments. |
| Generation | Requested State version | CR generation increments correspond to new DCM Requested State records | Each new generation of a CR corresponds to a new intent/request cycle in DCM. |

### 3.6 Lifecycle

| Kubernetes Concept | DCM Concept | Relationship | Notes |
|-------------------|-------------|--------------|-------|
| Pod phases (Pending, Running, Succeeded, Failed, Unknown) | DCM lifecycle states | Pod phases map to DCM lifecycle states via condition_mappings declaration | |
| CRD conditions | DCM lifecycle states and events | Standard conditions (Ready, Degraded, Progressing) map to DCM states and events via the field mapping specification | |
| Kubernetes events | DCM lifecycle events | Kubernetes watch events trigger DCM lifecycle event reports | The operator translates Kubernetes events into DCM lifecycle event types (ENTITY_HEALTH_CHANGE, DEGRADATION, UNSANCTIONED_CHANGE, etc.) |
| Cluster deletion | DCM decommission workflow | Cluster deletion triggers DCM's full decommission lifecycle — lifecycle policies applied to all related entities | |

---


## 3a. Cluster as a Service — The Primary Model

A Kubernetes cluster is a first-class catalog item in DCM. Any authorized Tenant can request and own a cluster through the service catalog, the same way they request a VM or a network. This is not a special case — it is the expected primary consumption model for Kubernetes infrastructure in DCM.

**How it works:**

```yaml
catalog_item: Platform.KubernetesCluster
provider: CAPI-based Service Provider (or managed K8s Service Provider)
tenant_uuid: <requesting-tenant-uuid>

entity:
  resource_type: Platform.KubernetesCluster
  tenant_uuid: <requesting-tenant-uuid>   # Tenant owns the cluster
  lifecycle_state: OPERATIONAL
  fields:
    kubernetes_version: "1.29"
    node_count: 3
    api_endpoint: "https://cluster-01.eu-west.example.com"
    kubeconfig_ref: <credential-provider-ref>  # via Credential Provider
```

**Ownership scope:** When a Tenant owns a `Platform.KubernetesCluster` entity, that Tenant owns everything within the cluster boundary — including cluster-scoped resources (ClusterRoles, StorageClasses, PersistentVolumes, CRDs registered for that cluster). The cluster entity is the ownership boundary. DCM treats the cluster as an opaque resource from a Tenant ownership perspective — the Tenant gets the cluster; what's inside it belongs to them.

**The Composite Service pattern:** A Cluster-as-a-Service catalog item typically composes multiple constituent resources:
```yaml
Platform.KubernetesCluster → constituent providers:
  - Compute resources (control plane + worker nodes)
  - Network resources (load balancer, ingress)
  - Storage resources (CSI driver + storage class)
  - DNS records (cluster API endpoint)
  - Credential issuance (kubeconfig via Credential Provider)
```

This is a Composite Service — the cluster catalog item registers a composite definition listing the constituents, and DCM dispatches and aggregates them, presenting a single Composite Entity to the Tenant.

**Sovereignty and accreditation:** Cluster placement follows the standard Placement Engine model. Sovereignty constraints declared by the Tenant apply to cluster placement — a GDPR-scoped Tenant requesting a cluster gets a cluster placed in an EU sovereignty zone. The CAPI provider (or managed K8s Service Provider) must hold appropriate accreditations.

**Post-provision:** Once the cluster is OPERATIONAL, it can optionally register with DCM as a nested Service Provider for workload resources. The Tenant can then request workload resources (Deployments, Services, PersistentVolumes) against their cluster through the same DCM service catalog. This creates the superset model: DCM provisions the cluster → cluster becomes a workload Service Provider → Tenant uses DCM to manage workloads on their cluster.


## 4. Where DCM Extends Beyond Kubernetes

These are capabilities that exist in DCM but have no Kubernetes equivalent. None of these require Kubernetes to be present — they operate across all provider types. For organizations running pure Kubernetes estates, these are the capabilities DCM brings that Kubernetes tooling alone cannot provide.

**Summary of extensions:**

| DCM Capability | Kubernetes Gap |
|---------------|---------------|
| Intent State | No concept of original consumer intent separate from desired state |
| Field-Level Provenance | No field lineage — a field is a field |
| Data Layers and Assembly | No layering model — manifests are flat declarations |
| Policy Engine | Admission webhooks are cluster-scoped, admission-time only |
| Cost Analysis | No native cost attribution in the request lifecycle |
| Information Providers | No structured external organizational data relationships |
| Cross-Cluster Lifecycle | Single-cluster scope — multi-cluster requires external tooling |

These are concepts that exist in DCM but have no Kubernetes equivalent. They are the capabilities DCM adds that justify the superset positioning.

### 4.1 Intent State

Kubernetes has no concept of a consumer's original intent separate from the desired state. Once you apply a manifest, Kubernetes only knows the current desired state — not what the consumer originally asked for or why.

DCM's Intent State is the immutable record of what the consumer asked for, stored before any policy processing or layer enrichment. This enables:
- Rehydration — replaying the original intent through current policies to produce a new request
- Intent portability — the same intent applied to a different provider
- Audit — answering "what did the consumer originally ask for?" independently of what was realized

### 4.2 Field-Level Provenance

Kubernetes has no concept of where a field value came from or why it was set. A field in a CR spec is a field — there is no lineage.

DCM's field-level provenance carries the full lineage of every field value through the entire lifecycle — which layer set it, which policy modified it, which provider realized it, and why each change was made. This enables complete audit trails and sovereignty evidence.

### 4.3 Data Layers and Assembly

Kubernetes has no equivalent to DCM's layering model. A Kubernetes manifest is a flat declaration — there is no concept of organizational standards, site-specific configuration, and service-specific configuration being separate layers that compose into a final manifest.

DCM's layering model enables 36 layer definitions to govern 40,000 VMs without duplication — impossible in the Kubernetes model.

### 4.4 Policy Engine

Kubernetes admission webhooks provide some policy capability (validation, mutation) but are cluster-scoped, apply at admission time only, and have no concept of hierarchy (Global → Tenant → User policy levels) or field-level override control.

DCM's Policy Engine operates at the management plane level, applies across all clusters and providers, enforces a three-level hierarchy with field-level override control (allow/constrained/immutable), and carries policy decisions as provenance metadata in the payload.

### 4.5 Cost Analysis

Kubernetes has no native cost attribution model. Tools like Kubecost exist but are add-ons with no integration into the request lifecycle.

DCM's cost analysis is built into the lifecycle model — cost attribution is tracked from request time through realization, operation, and decommission for every entity.

### 4.6 Information Providers

Kubernetes has no concept of structured relationships to external organizational data (Business Units, Cost Centers, Product Owners). Labels and annotations are unstructured key-value pairs with no type safety, no external system integration, and no verification model.

DCM's Information Provider model gives every entity structured, verified, versioned relationships to external organizational data with a stable external key model.

### 4.7 Cross-Cluster Lifecycle

Kubernetes manages resources within a single cluster. Multi-cluster management requires additional tools (ACM, Argo CD, Fleet) that are not part of the core Kubernetes model.

DCM manages the lifecycle of resources across multiple clusters as a first-class capability — the same Resource Type can be instantiated on any cluster that has a conformant Service Provider registered.

---

## 5. Standard Kubernetes Resource Type Mappings

These are the DCM Resource Type registry entries for standard Kubernetes resource types. Operators implementing these types should use these registry UUIDs and field definitions.

### 5.1 Compute

| DCM Resource Type | Kubernetes Equivalent | Notes |
|------------------|----------------------|-------|
| `Compute.Pod` | Pod | Lowest-level compute unit |
| `Compute.Container` | Container (within a Pod) | Sub-entity of Pod — expanded via bundled declaration |
| `Compute.Deployment` | Deployment | Managed set of Pods |
| `Compute.StatefulSet` | StatefulSet | Stateful managed set of Pods |
| `Compute.Job` | Job | One-time execution workload |
| `Compute.CronJob` | CronJob | Scheduled execution workload |

### 5.2 Network

| DCM Resource Type | Kubernetes Equivalent | Notes |
|------------------|----------------------|-------|
| `Network.Service` | Service | In-cluster service discovery and load balancing |
| `Network.Ingress` | Ingress | External HTTP/HTTPS routing |
| `Network.NetworkPolicy` | NetworkPolicy | In-cluster network isolation |

### 5.3 Storage

| DCM Resource Type | Kubernetes Equivalent | Notes |
|------------------|----------------------|-------|
| `Storage.PersistentVolume` | PersistentVolume | Cluster-level storage resource |
| `Storage.PersistentVolumeClaim` | PersistentVolumeClaim | Consumer's storage declaration — expanded into Storage.PersistentVolume relationship |
| `Storage.StorageClass` | StorageClass | Storage type definition — maps to DCM Provider Catalog Item |
| `Storage.ConfigMap` | ConfigMap | Configuration data storage |
| `Storage.Secret` | Secret | Sensitive data storage |

### 5.4 Platform

| DCM Resource Type | Kubernetes Equivalent | Notes |
|------------------|----------------------|-------|
| `Platform.KubernetesCluster` | Kubernetes Cluster (via CAPI or managed service) | The cluster itself is a DCM-managed resource |
| `Platform.Namespace` | Namespace | Maps to DCM Tenant boundary in per_tenant strategy |
| `Platform.CustomResourceDefinition` | CRD | CRD registration maps to DCM Resource Type registration |

### 5.5 Identity

| DCM Resource Type | Kubernetes Equivalent | Notes |
|------------------|----------------------|-------|
| `Security.ServiceAccount` | ServiceAccount | Kubernetes identity for workloads |
| `Security.Role` | Role / ClusterRole | Kubernetes RBAC role |
| `Security.RoleBinding` | RoleBinding / ClusterRoleBinding | Kubernetes RBAC binding |

---

## 6. The Kubernetes Information Provider

Kubernetes clusters function as both Service Providers (for provisioning resources) and Information Providers (for querying existing state). As an Information Provider, a Kubernetes cluster exposes its current resource state to DCM for:

- **Brownfield ingestion** — discovering existing resources and bringing them under DCM lifecycle management
- **Discovered State** — DCM's Discovered State for Kubernetes resources comes from querying the Kubernetes API
- **Drift detection** — comparing DCM Realized State against what Kubernetes actually has

### 6.1 Kubernetes as Information Provider Registration

```yaml
information_provider_registration:
  name: kubernetes-cluster-01
  implements:
    - information_type: Platform.KubernetesCluster
    - information_type: Compute.Pod
    - information_type: Storage.PersistentVolume
    # ... all resource types the cluster contains
  endpoint: <Kubernetes API server endpoint>
  kubernetes_credentials:
    auth_method: <service_account|kubeconfig|oidc>
  discovery_capabilities:
    label_selector: "dcm-managed=true"
    # Only returns DCM-managed resources by default
    full_discovery: true
    # Can also return all resources for brownfield ingestion
```

### 6.2 Discovered State from Kubernetes

DCM queries the Kubernetes API using the Kubernetes Information Provider to populate Discovered State:

```
DCM Drift Detection
  │
  ▼
Kubernetes Information Provider
  │  GET /apis/{group}/{version}/namespaces/{ns}/{kind}
  │  Filter: label dcm-entity-id = {entity_uuid}
  ▼
Discovered State payload (DCM format)
  │  Kubernetes object denaturalized to DCM format
  ▼
Compare against Realized State
  │  Field-by-field comparison
  ▼
UNSANCTIONED_CHANGE if differences found
  │  Reported to Policy Engine for response determination
```

---

## 7. Kubernetes-Native Patterns and DCM Equivalents

### 7.1 GitOps

Kubernetes GitOps (Argo CD, Flux) manages Kubernetes manifests in Git and synchronizes them to clusters. DCM's data model is also Git-based — all layers, Resource Type definitions, and policy definitions are stored in Git.

The relationship: DCM manages the **request lifecycle** (what gets asked for, approved, and provisioned). GitOps manages the **deployment lifecycle** (what gets deployed to a cluster from a Git repository). These are complementary:

- DCM governs the provisioning request — "is this consumer allowed to provision this resource?"
- GitOps deploys application code to the provisioned resource
- DCM and GitOps together form a complete lifecycle: DCM provisions the cluster, GitOps deploys applications to it

### 7.2 Helm

Helm charts are packages of Kubernetes manifests that can be parameterized. In DCM terms, a Helm chart is a form of Catalog Item — a curated, parameterized offering of a set of Kubernetes resources.

DCM does not replace Helm — it can use Helm as a delivery mechanism inside a Service Provider. The Service Provider receives the DCM Requested State, translates it to Helm values, and uses Helm to deploy the resources. The operator pattern is preferred for Day 2 management (Helm has limited reconciliation), but Helm remains valid for initial provisioning.

### 7.3 Cluster API (CAPI)

CAPI is the Kubernetes sub-project for managing Kubernetes clusters themselves using the Kubernetes API and operator pattern. CAPI clusters are a natural fit for DCM's `Platform.KubernetesCluster` Resource Type — a CAPI-based operator would be the Service Provider for provisioning new Kubernetes clusters as DCM-managed resources.

This is particularly significant: DCM managing the lifecycle of Kubernetes clusters through CAPI means DCM can provision the very infrastructure that operators run on. The superset relationship becomes concrete — DCM provisions the cluster, the cluster runs the operators, the operators provision the resources that DCM manages.

---

## 8. Incremental Adoption — Kubernetes-Native to DCM-Managed

Organizations running Kubernetes can adopt DCM incrementally across these phases:

### Phase 1 — Observation (no operator changes)
Deploy DCM with the Kubernetes Information Provider. DCM observes existing resources via the Kubernetes API and builds a Discovered State inventory. No changes to existing operators or workloads.

### Phase 2 — Brownfield Ingestion (no operator changes)
DCM promotes Discovered State records to Realized State — assuming lifecycle management of existing resources. Resources get DCM UUIDs, Tenant assignments, and provenance records. Existing resources are now DCM-managed without any operator changes.

### Phase 3 — Level 1 Conformance (minimal operator changes)
Operators implement Level 1 of this specification via the DCM Operator SDK. New resources are provisioned through DCM's service catalog. Existing resources managed via brownfield ingestion continue as-is.

### Phase 4 — Level 2 Conformance (moderate operator changes)
Operators implement Level 2 — full field mappings, capacity reporting, lifecycle events. DCM gains placement intelligence, drift detection, and cross-cluster management capabilities.

### Phase 5 — Level 3 Conformance (complete integration)
Operators implement Level 3 — sovereignty declarations, provenance, discovery endpoint. Full DCM capabilities available.

---

## 9. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | How does the Namespace-to-Tenant mapping work when a cluster has existing namespaces that predate DCM adoption? | Brownfield migration | ✅ Resolved |
| 2 | Should `Platform.KubernetesCluster` be the boundary for a DCM deployment, or can DCM manage resources across clusters without treating the cluster as a DCM entity? | Architecture scope | ✅ Resolved |
| 3 | How does DCM interact with Kubernetes admission webhooks — do they duplicate Policy Engine functions or complement them? | Policy model | ✅ Resolved |
| 4 | Should the Kubernetes Information Provider be a built-in DCM component or a separately deployed provider? | Deployment architecture | ✅ Resolved |
| 5 | How does the DCM superset model interact with managed Kubernetes services (EKS, GKE, AKS) where cluster management is outside the user's control? | Cloud provider integration | ✅ Resolved |

---

## 10. Related Concepts

- **DCM Operator Interface Specification** — the technical contract for operators integrating with DCM
- **DCM Operator SDK** — Go library implementing this specification for operator developers
- **Entity Relationships** — DCM's universal relationship model, of which Kubernetes ownerReferences are a subset
- **Resource Type Hierarchy** — the DCM registry where Kubernetes Resource Types are registered
- **Information Providers** — the DCM model for the Kubernetes API as a discoverable information source
- **Four States** — DCM's Intent/Requested/Realized/Discovered model, which extends Kubernetes' desired/actual model

---



## Resolution Notes

**Q1:** Pre-existing namespaces are handled by the brownfield ingestion model. Each namespace maps to one DCM Tenant. Resources without clear ownership land in the `__transitional__` Tenant and are promoted by a platform admin. Same flow as brownfield VM ingestion — no special handling required.

**Q2:** DCM manages resources across multiple clusters simultaneously. `Platform.KubernetesCluster` is a DCM-managed resource type — both something DCM provisions as a catalog item (Cluster as a Service) and something DCM tracks when externally provisioned. A Tenant can own a full cluster as a catalog item; the cluster is not the boundary of a DCM deployment. DCM's organizational boundary is the Tenant. A single DCM deployment routes requests to Service Providers across many clusters, and can provision new clusters as service catalog items.

**Q3:** Admission webhooks and the DCM Policy Engine are complementary layers, not duplicates. Admission webhooks enforce cluster-native policy (security contexts, image policies, resource quotas). The DCM Policy Engine enforces DCM request policy (business rules, data governance, sovereignty). A DCM-managed workload resource is validated by both — DCM Policy Engine before dispatch, admission webhook at the cluster. This is defense in depth.

**Q4:** The Kubernetes Information Provider is a separately deployed provider that registers with DCM as a standard Information Provider. It serves cluster state, namespace inventory, and workload status. There are no built-in Information Providers in DCM's architecture — all Information Providers follow the unified base contract and are independently deployable.

**Q5:** Managed Kubernetes services (EKS, GKE, AKS) register as Service Providers of resource type `Platform.ManagedKubernetesCluster`. DCM manages workload resources within the cluster (Deployments, Services, PersistentVolumes) but explicitly does not manage the cluster control plane. Sovereignty enforcement applies at cluster selection — DCM places workloads on clusters satisfying sovereignty constraints. The cloud provider manages cluster infrastructure.

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
