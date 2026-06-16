---
Document Status: ✅ Complete
Document Type: Architecture Reference — Deployment and Redundancy
---

# DCM Data Model — Deployment and Redundancy Model

> **DCM-native runtime feature; no single UDLM contract counterpart.**
> Deployment topology and redundancy are realization-layer concerns. UDLM
> does not mandate a deployment model — a peer DCM realization could choose a
> different redundancy strategy and still satisfy every UDLM contract. This
> document specifies DCM's own deployment and redundancy approach.


**Document Status:** ✅ Complete  
**Related Documents:** [Context and Purpose](https://github.com/croadfeldt/udlm/blob/main/foundations/context-and-purpose.md) | [data stores](https://github.com/croadfeldt/udlm/blob/main/contracts/storage-providers.md) | [Universal Audit Model](https://github.com/croadfeldt/udlm/blob/main/observability/universal-audit.md) | [Policy Organization](../governance-enforcement/policy-profiles.md)

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [udlm/foundations/foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: DATA + PROVIDER**
>
> Data: deployment specification. Provider: data store redundancy



---

> **Operational guidance:** GitOps the disaster recovery runbook and RTO/RPO tables are in [Operational Reference](../../reference/operational-reference.md) Section 3.

## 1. Purpose

Every DCM component, every data store, and every capability is designed for redundancy by default. Redundancy is not an add-on or an advanced configuration — it is the baseline operational posture for all profiles above `minimal`.

**The minimal profile** provides single-instance deployment for home lab and evaluation simplicity. All other profiles assume redundancy as the floor. The transition from `minimal` to `dev` is the transition from "works on my laptop" to "survives a node failure."

**Everything in DCM runs as a container in a pod.** No bare-metal DCM components. No special-case deployment paths. Every DCM component follows the same container lifecycle, the same health check model, the same rolling update pattern. DCM runs on Kubernetes — and manages Kubernetes.

**DCM is self-hosting.** DCM's own deployment is expressible as DCM resources. DCM can manage its own lifecycle, detect drift in its own components, and rehydrate its own deployment from Git. This is the ultimate expression of the data center repave use case — DCM restoring itself.

---

## 2. Design Principles

**Redundant by default.** Every component, store, and capability has a redundancy model. The `minimal` profile sets `replicas: 1`. Every other profile sets `replicas: >= 3` with quorum writes and anti-affinity scheduling.

**Everything containerized.** All DCM components run as containers in Kubernetes pods. No exceptions. This gives a consistent deployment model, rolling updates, health checks, and self-healing as first-class properties.

**Profile-governed redundancy.** Replica counts, quorum thresholds, geo-replication, and anti-affinity requirements are declared by the active Profile — not by per-component configuration. Activating a Profile configures redundancy for the entire deployment.

**Self-hosting.** DCM's own deployment is a DCM resource. DCM manages itself through the same model it uses to manage customer infrastructure.

**Stateless control plane.** All DCM control plane components are stateless — all state lives in external stores. Any component instance can fail and be replaced without data loss. State recovery means restarting a pod — not restoring a database.

**Quorum writes for durability.** All durable stores use quorum writes — a write is confirmed only when a majority of replicas acknowledge it. This ensures durability even if a minority of replicas fail simultaneously.

---

## 3. Component Redundancy Model

### 3.1 Control Plane Components

All control plane components are stateless, horizontally scalable, and deployed as Kubernetes Deployments with configurable replica counts.

```yaml
component_redundancy:
  component: request_payload_processor   # same model for all components
  deployment_type: kubernetes_deployment
  replicas: 3                    # set by active Profile
  affinity:
    anti_affinity: required      # pods spread across nodes
    zone_spread: preferred       # prefer spreading across availability zones
  disruption_budget:
    min_available: 2             # always keep 2 running during rolling updates
  health_check:
    liveness:
      path: /healthz
      interval_seconds: 10
      failure_threshold: 3
    readiness:
      path: /readyz
      interval_seconds: 5
      failure_threshold: 2
  rolling_update:
    strategy: RollingUpdate
    max_unavailable: 0           # never take a pod down before replacement is ready
    max_surge: 1
```

**Control plane components:**

| Component | Stateless? | Replica Model |
|-----------|-----------|--------------|
| API Gateway | Yes | Deployment + HorizontalPodAutoscaler |
| Request Payload Processor | Yes | Deployment |
| Policy Engine (OPA) | Yes | Deployment + PolicyBundle sidecar |
| Placement Engine | Yes | Deployment |
| Service Catalog | Yes | Deployment |
| IDM / IAM | Yes | Deployment (external IdP recommended) |
| Audit Forward Service | Yes | Deployment (1 active + 1 standby) |
| Lifecycle Constraint Enforcer | Yes | Deployment (leader election) |
| Drift Detection | Yes | Deployment (leader election for scheduling) |
| Resource Discovery | Yes | Deployment (leader election) |
| Message Bus Router | Yes | Deployment |

**Leader election** for scheduler-type components (Lifecycle Constraint Enforcer, Drift Detection, Resource Discovery): multiple replicas run but only one holds the leader lease at a time. On leader failure, a replica acquires the lease within seconds.

### 3.2 Data Store Redundancy

All DCM data stores run as containers. Each store type has a declared replication and quorum model.

#### Commit Log

```yaml
commit_log:
  replicas: 3
  write_quorum: 2               # confirmed durable when 2/3 replicas acknowledge
  read_quorum: 1                # any replica can serve reads
  affinity:
    zone_spread: required       # replicas MUST span availability zones
  implementation: etcd          # or equivalent consensus store
  # etcd is purpose-built for this pattern: Raft consensus, quorum writes,
  # sub-millisecond local writes, proven in Kubernetes itself
```

The Commit Log uses consensus protocol (Raft/equivalent). A write is confirmed when the quorum acknowledges — ensuring durability even if a minority of replicas fail simultaneously.

#### DCM database (Intent, Requested, Layers, Policies)

```yaml
gitops_store:
  implementation: gitea          # or equivalent self-hosted Git
  replicas: 3
  replication_mode: active_active  # any node can accept writes
  write_quorum: 2
  backup:
    enabled: true
    schedule: "0 */6 * * *"    # every 6 hours
    retention: 30d
```

#### pipeline_events table (Realized, Discovered, Audit Events)

```yaml
event_stream:
  implementation: kafka          # or equivalent
  brokers: 3
  replication_factor: 3
  min_insync_replicas: 2        # minimum replicas that must acknowledge a write
  partitions: 12                # enables parallel consumption
  retention:
    bytes: -1                   # unlimited — retention governed by policy
    ms: -1                      # unlimited
```

#### Audit Store

```yaml
audit_store:
  implementation: elasticsearch  # or equivalent — optimized for queryable retention
  replicas: 3
  primary_shards: 5
  replica_shards: 1             # each shard has 1 replica = 2 copies total
  geo_replicated: true          # in prod/fsi/sovereign profiles
  append_only_enforced: true    # storage layer enforces immutability
```

#### Search Index (Non-Authoritative)

```yaml
search_index:
  implementation: elasticsearch
  replicas: 2                   # lower redundancy — can rebuild from Git
  rebuild_from_git: true        # on data loss, rebuild from authoritative stores
```

### 3.3 Container Specification

Every DCM component pod follows a common security and resource model:

```yaml
pod_spec:
  security_context:
    run_as_non_root: true
    run_as_user: 65534           # nobody
    run_as_group: 65534
    fs_group: 65534
    seccomp_profile:
      type: RuntimeDefault
    capabilities:
      drop: [ALL]

  containers:
    - name: <component-name>
      image: ghcr.io/dcm-project/<component>:<version>
      image_pull_policy: IfNotPresent
      security_context:
        read_only_root_filesystem: true
        allow_privilege_escalation: false
      resources:
        requests:
          cpu: 500m
          memory: 512Mi
        limits:
          cpu: 2000m
          memory: 2Gi
      liveness_probe: <per component>
      readiness_probe: <per component>
      volume_mounts:
        - name: tmp
          mount_path: /tmp       # writable temp — no other writable paths

  volumes:
    - name: tmp
      empty_dir: {}
```

---

## 4. Redundancy by Profile

Profile activation configures redundancy for the entire deployment. Organizations do not configure replica counts individually — they activate a profile.

```yaml
# Redundancy matrix per profile
redundancy_matrix:
  minimal:
    control_plane_replicas: 1
    store_replicas: 1
    write_quorum: false
    zone_spread: false
    geo_replication: false
    anti_affinity: false
    note: "Single-instance. No redundancy. Home lab and evaluation only."

  dev:
    control_plane_replicas: 1
    store_replicas: 1
    write_quorum: false
    zone_spread: false
    geo_replication: false
    anti_affinity: false
    note: "Single-instance with backup. Basic resilience for dev environments."

  standard:
    control_plane_replicas: 3
    store_replicas: 3
    write_quorum: 2             # 2 of 3
    zone_spread: preferred
    geo_replication: false
    anti_affinity: required
    note: "Production baseline. Survives single node or zone failure."

  prod:
    control_plane_replicas: 3
    store_replicas: 3
    write_quorum: 2
    zone_spread: required
    geo_replication: true
    anti_affinity: required
    sla_disruption_budget: "always 2 replicas available"
    note: "Production with SLA. Geo-replicated stores."

  fsi:
    control_plane_replicas: 5
    store_replicas: 5
    write_quorum: 3             # 3 of 5
    zone_spread: required
    geo_replication: true
    anti_affinity: required
    audit_store_replicas: 5
    note: "FSI-grade. Higher quorum threshold. Compliance-grade audit."

  sovereign:
    control_plane_replicas: 5
    store_replicas: 5
    write_quorum: 3
    zone_spread: required
    geo_replication: true        # within sovereignty boundary only
    anti_affinity: required
    air_gap_backup: true
    sovereignty_boundary_enforced: true
    note: "Maximum. All geo-replication within sovereignty boundary."
```

---

## 5. The DCM Deployment Specification

The DCM deployment itself is a DCM resource — declared in YAML, stored in Git, governed by Policy, subject to the same four-state lifecycle as any other resource.

```yaml
dcm_deployment:
  artifact_metadata:
    uuid: <uuid>
    handle: "deployments/primary/dcm-control-plane"
    version: "1.0.0"
    status: active

  profile: system/profile/standard
  kubernetes_namespace: dcm-system

  # Redundancy — set by active Profile, overridable per component
  redundancy:
    control_plane:
      replicas: 3
      affinity:
        anti_affinity: required
        zone_spread: preferred
      disruption_budget:
        min_available: 2

    stores:
      commit_log:
        replicas: 3
        write_quorum: 2
        implementation: etcd
      gitops_store:
        replicas: 3
        write_quorum: 2
        implementation: gitea
      event_stream:
        brokers: 3
        replication_factor: 3
        min_insync_replicas: 2
        implementation: kafka
      audit_store:
        replicas: 3
        geo_replicated: false     # standard profile default
        implementation: elasticsearch
      search_index:
        replicas: 2
        implementation: elasticsearch

  # Provider health configuration
  providers:
    health_check_interval_seconds: 30
    unhealthy_threshold: 3
    automatic_failover: true

  # Self-hosting: DCM manages its own deployment
  self_managed: true
  drift_detection_enabled: true
  rehydration_enabled: true
  # DCM detects if its own components drift from declared spec
  # and can rehydrate (redeploy) from this declaration
```

---

## 6. Self-Hosting — DCM Managing Itself

DCM's own deployment is managed through the same model it uses to manage customer infrastructure. This is the **self-hosting principle** — DCM eats its own cooking.

### 6.1 What Self-Hosting Means

- DCM control plane components are defined as Resource Entities in DCM
- DCM data stores are defined as data store resources in DCM
- DCM's own Policy Groups govern DCM's own deployment constraints
- DCM runs drift detection on its own components — a component running the wrong image version is drift
- DCM can rehydrate its own deployment from the `dcm_deployment` declaration in Git

### 6.2 The Bootstrap Problem

DCM cannot manage itself before it exists. The bootstrap sequence:

```
1. Bootstrap installer deploys minimal DCM (single instance, no redundancy)
   from a declarative bootstrap manifest
   │
2. Bootstrap DCM reads the target dcm_deployment declaration from Git
   │
3. Bootstrap DCM provisions itself to the target state:
   - Scales from 1 to N replicas
   - Provisions redundant stores
   - Configures quorum
   │
4. Bootstrap instance hands off to the now-redundant DCM
   │
5. DCM manages its own lifecycle from this point forward
```

The bootstrap manifest is the only thing that exists outside DCM's management scope. It is minimal by design — just enough to get DCM running.

### 6.3 Self-Hosted Drift Detection

DCM continuously compares its own running state against the `dcm_deployment` declaration:

| Drift Type | Example | Response |
|-----------|---------|---------|
| Wrong image version | Component running v1.1.0, declared v1.2.0 | Rolling update triggered |
| Wrong replica count | 2 replicas running, declared 3 | Scale-up triggered |
| Wrong resource limits | Component using more than declared limits | Alert + potential eviction |
| Store replication mismatch | Store has 2 replicas, declared 3 | Replication repair triggered |

### 6.4 The Repave Scenario

The ultimate test of self-hosting: DCM is lost entirely (ransomware, catastrophic failure). Recovery:

```
1. Deploy bootstrap installer to new Kubernetes cluster
   │
2. Bootstrap DCM reads dcm_deployment declaration from Git backup
   │
3. DCM provisions itself — full redundant deployment
   │
4. DCM reads all resource declarations from Git
   │
5. DCM rehydrates customer workloads in dependency order
   │
6. Drift detection validates recovered state matches declared state
```

The recovery time is bounded by infrastructure provisioning speed — not by backup restoration or manual configuration. Everything is code. Everything is declarative. Everything is in Git.

---

## 7. Commit Log Redundancy — Two-Stage Audit Integration

The Commit Log is the synchronous component of the two-stage audit model. In a distributed deployment, "synchronous durable write" means quorum acknowledgment:

```
DCM component initiates change
  │
  ▼
Write to Commit Log (Raft consensus)
  │  Propose to leader
  │  Leader replicates to followers
  │  Write confirmed when quorum (2/3 or 3/5) acknowledge
  │
  ├── Replica 1 (local node)     → ACK ─┐
  ├── Replica 2 (different node) → ACK ─┤ quorum reached
  └── Replica 3 (different zone) → ACK ─┘
  │
  ▼  Operation returns success (< 1ms typical with NVMe)
  │
  ▼  [async — Audit Forward Service]
Read from any surviving Commit Log replica
  │  Enrich → write to Audit Store
  └── Clear Commit Log entry after Audit Store confirms
```

**Failure scenarios and recovery:**

| Failure | During Stage 1 | Effect |
|---------|---------------|--------|
| Single replica fails before quorum | Quorum still achievable | No impact |
| Majority fail before quorum | Commit Log unavailable | Operation aborted — no silent change |
| Leader fails after quorum | New leader elected (seconds) | In-flight writes complete on new leader |
| All replicas fail after quorum | Audit Forward Service reads from backup | Full recovery on restart |
| Audit Store unavailable | Commit Log accumulates | Forward resumes when Audit Store recovers |

---

## 8. Network Architecture

> **Full internal auth specification:** See [Internal Component Authentication](../control-plane/internal-component-auth.md) for component identity model, Internal CA, bootstrap protocol, and ICOM-001–ICOM-009 system policies.

### 8.1 Service Mesh

All DCM component-to-component communication uses a service mesh (Istio or equivalent):
- mTLS everywhere (RFC 8446 TLS 1.3 + RFC 5280 X.509) — no plaintext internal communication
- Traffic policies enforced at mesh level
- Observability: traces, metrics, logs for all inter-component calls
- Circuit breaking: prevent cascade failures

### 8.2 Ingress

External traffic enters through a redundant Ingress layer:

```
External clients
  │
  ▼
Load Balancer (external — cloud or on-premises)
  │
  ▼
Ingress Controller (replicated — 2+ instances)
  │
  ▼
API Gateway pods (3+ instances, anti-affinity)
  │
  ▼
Internal service mesh
```

### 8.3 DNS and Service Discovery

All DCM components address each other via Kubernetes Service DNS. No hardcoded IPs. Service discovery is automatic — a new pod replica is immediately addressable.

---

## 9. DCM System Policies — Redundancy

| Policy | Rule |
|--------|------|
| `RED-001` | All DCM control plane components must run as containers in Kubernetes pods |
| `RED-002` | All control plane components must be stateless — all persistent state in external stores |
| `RED-003` | In profiles above `minimal`, all control plane components must have `replicas >= 3` with anti-affinity |
| `RED-004` | All durable stores in profiles above `minimal` must use quorum writes with `write_quorum >= 2` |
| `RED-005` | The Commit Log must use consensus protocol (Raft or equivalent) with quorum writes |
| `RED-006` | The DCM deployment must be declared as a DCM resource in Git — self-hosting required |
| `RED-007` | DCM must run drift detection on its own components — version drift is treated as resource drift |
| `RED-008` | A rolling update of any DCM component must not reduce available replicas below `min_available` |
| `RED-009` | All DCM component communication must use mTLS — no plaintext internal communication |
| `RED-010` | The bootstrap manifest is the only DCM configuration outside DCM's management scope |

---

## 10. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | Should the bootstrap manifest be version-controlled and verifiable? | Bootstrap integrity | ✅ Resolved — GitOps store + hash verification at every startup; tampering prevents start; operator-signed (RED-011) |
| 2 | How does DCM handle Kubernetes cluster upgrades in sovereign deployments? | Operational | ✅ Resolved — pre-staged images via signed bundles; maintenance mode during upgrade; startup verification before resume (RED-012) |
| 3 | Should DCM support non-Kubernetes container runtimes? | Portability | ✅ Resolved — Kubernetes primary/required for production; Podman/Docker Compose for dev/community only (RED-013) |
| 4 | What is the minimum hardware specification per profile? | Implementation | ✅ Resolved — declared as DCM Resource definitions; enforced by placement engine; table documented (RED-014) |
| 5 | How does DCM's self-hosted drift detection handle DCM drifting from its own state? | Self-hosting | ✅ Resolved — DCM is DCM-managed resource; Operator reconciles; bootstrap hash provides independent check; audit hash chain externally verifiable (RED-015) |

---

## 11. Related Concepts

- **Universal Audit Model** (doc 16) — two-stage audit; Commit Log quorum model
- **Policy Organization** (doc 14) — Profile-governed redundancy configuration
- **data stores** (doc 11) — Store contracts include replication requirements
- **Four States** (doc 02) — all state stores are redundant per this model
- **Ingestion Model** (doc 13) — DCM's own deployment recovery uses the repave/rehydration pattern


## 8. Deployment Redundancy Gap Resolutions

### 8.1 Bootstrap Manifest Verification (Q1)

The bootstrap manifest is stored in the GitOps store, hash-verified at DCM startup and every restart. Tampering prevents DCM from starting.

```yaml
bootstrap_manifest:
  version: "1.0.0"
  manifest_uuid: <uuid>
  manifest_hash: <sha256>          # computed at creation; verified at every startup
  signed_by: <operator-key-ref>   # signed by deploying operator
```

DCM startup sequence: verify manifest hash → verify manifest signature → proceed with initialization. On failure: refuse to start; emit security alert; notify platform admin.

### 8.2 Kubernetes Cluster Upgrades in Sovereign Deployments (Q2)

Sovereign DCM (air-gapped) uses pre-staged container images and the maintenance mode pattern:

```
Pre-upgrade:
  1. Pre-stage all DCM container images in local registry (signed bundles)
  2. DCM enters maintenance mode — new requests queued; in-flight complete

During upgrade:
  3. Kubernetes upgrade proceeds using pre-staged images
  4. DCM components restart against new cluster version

Post-upgrade:
  5. Startup verification (bootstrap manifest hash check)
  6. DCM exits maintenance mode — queued requests resume
```

Same signed bundle model as registry updates — no new pattern needed.

### 8.3 Non-Kubernetes Container Runtime Support (Q3)

Kubernetes is DCM's primary and recommended container runtime. Non-Kubernetes runtimes (Podman, Docker Compose) are supported for development and community extension only. The DCM Operator is Kubernetes-native and not supported on other runtimes. Production deployments must use Kubernetes.

### 8.4 Minimum Hardware Specifications (Q4)

Expressed as DCM Resource definitions per profile — machine-readable and enforced by the placement engine during self-deployment.

| Profile | CPU | Memory | Storage | Replicas |
|---------|-----|--------|---------|---------|
| minimal | 2 cores | 4 Gi | 20 Gi | 1 |
| dev | 4 cores | 8 Gi | 50 Gi | 1 |
| standard | 8 cores | 16 Gi | 100 Gi | 3 |
| prod | 16 cores | 32 Gi | 200 Gi | 3 |
| fsi | 32 cores | 64 Gi | 500 Gi | 5 |
| sovereign | 32 cores | 64 Gi | 500 Gi | 5 |

These are minimums. Production workloads may require significantly more based on managed resource count.

### 8.5 DCM Self-Hosted Drift Detection (Q5)

DCM's own deployment is a DCM-managed resource subject to the same drift detection as any other resource. The DCM Operator continuously reconciles running components against the declared deployment manifest.

**The bootstrap paradox — who watches the watchman:**
- DCM Operator drifts → bootstrap manifest hash verification (RED-011) detects independently
- Audit component compromised → Audit Store hash chain break is detectable by external verification
- Full DCM compromise → signed bundle verification at import time provides external trust anchor

### 8.6 System Policies — Deployment Redundancy Gaps

| Policy | Rule |
|--------|------|
| `RED-011` | The bootstrap manifest is version-controlled in the GitOps store, hash-verified at DCM startup and every restart. Bootstrap manifest tampering prevents DCM from starting and triggers a security alert. |
| `RED-012` | Kubernetes cluster upgrades in Sovereign DCM deployments use pre-staged container images from the local signed bundle registry. DCM enters maintenance mode during upgrade. In-flight operations complete before upgrade. DCM exits maintenance mode on successful startup verification. |
| `RED-013` | Kubernetes is DCM's primary and recommended container runtime. Non-Kubernetes runtimes are supported for development and community extension purposes only. Production deployments must use Kubernetes. |
| `RED-014` | Minimum hardware specifications are expressed as DCM Resource definitions per profile and enforced by the placement engine during DCM self-deployment. |
| `RED-015` | DCM's own deployment is a DCM-managed resource subject to the same drift detection as any other resource. Bootstrap manifest hash verification (RED-011) provides independent verification. Audit Store hash chain breaks are detectable externally. |



---

## 9. Bootstrap Tenant Creation Sequence

### 9.1 The Bootstrap Problem

DCM requires every entity to belong to exactly one Tenant. But during initial deployment, no Tenants exist. The bootstrap sequence resolves this by creating the foundational Tenants as part of DCM startup, declared in the bootstrap manifest.

### 9.2 The Three Foundation Tenants

The bootstrap manifest declares three system Tenants that are created before any consumer can submit requests:

```yaml
bootstrap_tenants:
  - handle: "__platform__"
    display_name: "DCM Platform"
    purpose: "Owns DCM's own control plane resources (components, stores, providers)"
    automatically_created: true
    cannot_be_decommissioned: true

  - handle: "__transitional__"
    display_name: "Transitional"
    purpose: "Holds brownfield entities during ingestion before promotion to a real Tenant"
    automatically_created: true
    cannot_be_decommissioned: true

  - handle: "__system__"
    display_name: "System"
    purpose: "Owns system-level artifacts (system layers, system policies, system workflows)"
    automatically_created: true
    cannot_be_decommissioned: true
```

### 9.3 Bootstrap Startup Sequence

```
DCM starts
  │
  ▼ Step 1: Verify bootstrap manifest hash and signature
  │
  ▼ Step 2: Initialize storage providers
  │   GitOps stores initialized
  │   Audit Store initialized
  │   Commit Log initialized
  │
  ▼ Step 3: Create foundation Tenants (if not already existing)
  │   __platform__, __transitional__, __system__
  │
  ▼ Step 4: Create initial Platform Admin actor
  │   Declared in bootstrap manifest
  │   Assigned to __platform__ Tenant
  │   Given platform_admin role
  │
  ▼ Step 5: Activate system domain layers and policies
  │   System layers loaded from GitOps store
  │   System policies activated
  │   Built-in recovery profiles activated
  │
  ▼ Step 6: Register built-in providers
  │   Built-in Auth Provider
  │   Search Index data store
  │   Audit Store data store
  │   (All owned by __platform__ Tenant)
  │
  ▼ Step 7: DCM ready
      Consumer API, Provider API, Admin API accepting requests
      Platform Admin can now create organization Tenants
      Organization Tenants can request resources
```

### 9.4 System Policy

| Policy | Rule |
|--------|------|
| `RED-016` | The three foundation Tenants (__platform__, __transitional__, __system__) are created during bootstrap and cannot be decommissioned. All DCM control plane resources are owned by __platform__. All brownfield ingested entities enter __transitional__ before promotion. |



---

## 9. Bootstrap Sequence and Initial Tenant Creation

### 9.1 The Bootstrap Problem

The DCM data model requires every entity to be owned by a Tenant. But Tenants are themselves DCM entities. The bootstrap sequence defines how the initial Tenants and platform admin actor are created before DCM can accept external requests.

### 9.2 Bootstrap Manifest

The bootstrap manifest (RED-011) declares the initial state required for DCM to start. It includes:

```yaml
bootstrap_manifest:
  version: "1.0.0"
  signed_by: <deploying-operator-key>

  # Initial system Tenants (created before any external requests)
  system_tenants:
    - uuid: <platform-tenant-uuid>
      handle: "__platform__"
      display_name: "DCM Platform"
      description: "System Tenant owning DCM's own control plane resources"
      immutable: true             # cannot be decommissioned or modified by regular operators

    - uuid: <transitional-tenant-uuid>
      handle: "__transitional__"
      display_name: "Transitional"
      description: "Holding Tenant for brownfield ingestion (INGEST phase)"
      immutable: true

  # Initial platform admin actor
  bootstrap_admin:
    uuid: <admin-actor-uuid>
    username: "dcm-bootstrap-admin"
    auth_provider: builtin
    roles: [platform_admin]
    credential_ref: <bootstrap-admin-credential-ref>
    # This credential is rotated on first login

  # Active profile for initial deployment
  initial_profile:
    deployment_posture: minimal    # or as declared; can be changed post-bootstrap
    compliance_domains: []

  # Bootstrap admin's initial Tenant
  initial_tenant:
    uuid: <org-tenant-uuid>
    handle: "org-default"
    display_name: "Default Organization Tenant"
    owned_by: bootstrap_admin
```

### 9.3 Bootstrap Sequence

```
DCM starts → bootstrap manifest hash verified (RED-011)
  │
  ▼ System Tenants created (before Policy Engine active):
  │   __platform__ Tenant — owns DCM control plane resources
  │   __transitional__ Tenant — brownfield ingestion holding
  │   These are created by the bootstrap process itself, not through the request pipeline
  │
  ▼ Bootstrap admin actor created
  │   Auth Provider initialized with bootstrap credential
  │   Platform Admin role assigned
  │
  ▼ Initial profile activated
  │   Deployment posture policies loaded
  │   Compliance domain policies loaded (if declared)
  │
  ▼ Policy Engine comes online
  │   All subsequent operations go through the standard request pipeline
  │
  ▼ Bootstrap admin creates the initial organization Tenant (optional)
  │   First real request through the pipeline
  │   Creates the initial production Tenant for organizational resources
  │
  ▼ Bootstrap admin credential rotation notification sent
  │   Bootstrap credential must be rotated on first login
  │   After rotation, bootstrap_admin becomes a standard platform admin actor
  │
  ▼ DCM accepts external requests
```

### 9.4 System Tenants

The `__platform__` and `__transitional__` Tenants are created by the bootstrap process and are immutable:

| System Tenant | Purpose | Who can modify |
|--------------|---------|---------------|
| `__platform__` | Owns DCM's own control plane resources | Platform Admin (restricted operations only) |
| `__transitional__` | Brownfield ingestion holding area | Ingestion pipeline only |

These Tenants are exempt from the normal Tenant decommission workflow — they cannot be decommissioned while DCM is operational.

### 9.5 System Policy

| Policy | Rule |
|--------|------|
| `BOOT-001` | The __platform__ and __transitional__ system Tenants are created by the bootstrap process before the Policy Engine comes online. They are immutable and cannot be decommissioned while DCM is running. |
| `BOOT-002` | The bootstrap admin credential must be rotated on first login. The bootstrap manifest declares the initial credential reference only; the credential itself is managed by the credential management service. |
| `BOOT-003` | After bootstrap, all Tenant creation and modification goes through the standard request pipeline. The bootstrap process is a one-time operation. |


---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
