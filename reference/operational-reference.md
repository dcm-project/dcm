# DCM Data Model — Operational Reference

**Document Status:** 🔄 In Progress
**Document Type:** SRE Reference — GitOps Scale, Store Migration, Disaster Recovery
**Related Documents:** [data stores](https://github.com/croadfeldt/udlm/blob/main/contracts/storage-providers.md) | [Deployment and Redundancy](../architecture/runtime-features/deployment-redundancy.md) | [Four States Model](https://github.com/croadfeldt/udlm/blob/main/foundations/four-states.md) | [Internal Component Authentication](../architecture/control-plane/internal-component-auth.md) | [DCM Self-Health Endpoints](../architecture/control-plane/self-health.md)

> **Audience:** Platform engineers and SREs operating DCM in production. This document covers three operational concerns that require guidance beyond the architectural specifications: GitOps store partitioning at large scale, migrating between store implementations, and recovering from failure scenarios.

---

## 1. DCM database Scale and Partitioning

### 1.1 When a Repo Becomes Too Large

The default DCM GitOps layout uses one repository per store type (Intent, Requested, Layer, Policy). For most deployments this is correct. At large scale — tens of thousands of active entities or hundreds of active tenants — a single repository can exhibit:

- Git operation latency (clone, fetch, log) growing beyond SLA
- CI/CD pipeline fan-out delays as every write triggers the full repository
- Access control granularity limits (all tenants share one repo)
- Search index sync lag from large diffs

**Thresholds that suggest partitioning:**

| Signal | Threshold | Recommended action |
|--------|-----------|-------------------|
| Entities in Intent/Requested store | > 50,000 active | Consider tenant-shard partitioning |
| Git clone time | > PT30S | Add shallow-clone depth; consider partitioning |
| PR merge latency | > PT5M | Partition or add write buffer |
| Tenant count | > 500 | Consider per-tenant repositories |
| Repository size on disk | > 10 GB | Partition |

These are guidelines, not hard limits. Profile, hardware, and Git host performance all affect the actual inflection point.

### 1.2 Partitioning Strategies

DCM supports three partitioning strategies. All are compatible with the storage contract — partitioning changes how stores are organized, not what the store contract requires.

#### Strategy A — Tenant Shard Partitioning (recommended for most)

Split each store type into N shard repositories, with tenants assigned to shards by a deterministic hash of `tenant_uuid`:

```
shard = hash(tenant_uuid) % N

dcm-intent-shard-0/     ← tenants whose hash(uuid) % N == 0
dcm-intent-shard-1/     ← tenants whose hash(uuid) % N == 1
  tenants/
    {tenant-uuid}/
      requests/
        {request-uuid}/
          intent.yaml
```

**DCM configuration:**
```yaml
gitops_store:
  intent_store:
    partitioning: tenant_shard
    shard_count: 8
    shard_routing: hash_mod    # deterministic; no routing table needed
    repositories:
      - shard: 0
        url: https://git.corp/dcm/dcm-intent-shard-0
      - shard: 1
        url: https://git.corp/dcm/dcm-intent-shard-1
      # ...
```

**Operational implications:** Adding shards requires re-hashing. Plan shard counts for 3–5 years of expected growth; use a power of 2 to simplify future doubling.

#### Strategy B — Per-Tenant Repositories (for strict isolation)

Each tenant has its own set of store repositories. Used when:
- Tenants are separate organizations (MSP model)
- Compliance requires complete data isolation per tenant
- Different retention policies per tenant

```
dcm-intent-{tenant-uuid}/    ← one repository per tenant
  requests/
    {request-uuid}/
      intent.yaml
```

**Operational implications:** Repository count scales with tenant count. Requires automation for tenant onboarding (repository creation, access provisioning). Git host must support large numbers of repositories.

#### Strategy C — Time-Based Archiving (for retention management)

Active entities stay in the primary repository. Entities past a declared age threshold are archived to read-only archive repositories:

```
dcm-intent-active/           ← current entities (hot)
dcm-intent-archive-2025/     ← entities from 2025 (cold, read-only)
dcm-intent-archive-2024/     ← entities from 2024 (cold, read-only)
```

DCM's audit and search components are configured with both active and archive repository lists. Strategy C is typically combined with Strategy A or B.

### 1.3 Large-Scale Layer Store Partitioning

The Layer Store grows more slowly than the Intent/Requested stores (layers are reused across requests). Layer Store partitioning is by domain rather than by tenant:

```
dcm-layers-compute/        ← Compute.* resource type layers
dcm-layers-network/        ← Network.* resource type layers
dcm-layers-storage/        ← Storage.* resource type layers
dcm-layers-platform/       ← Platform.* and cross-cutting layers
dcm-policies-core/         ← System and core policies
dcm-policies-tenant/       ← Tenant-contributed policies (per tenant or sharded)
```

Domain-partitioned Layer stores are configured in DCM's layer assembly engine:

```yaml
layer_store:
  repositories:
    - domain: Compute.*
      url: https://git.corp/dcm/dcm-layers-compute
      priority: provider_contribution  # provider contributions go here
    - domain: Network.*
      url: https://git.corp/dcm/dcm-layers-network
    - domain: "*"                       # catch-all for uncategorized
      url: https://git.corp/dcm/dcm-layers-platform
```

### 1.4 Shallow Clones and Read-Only Mirrors

For read-heavy operations (audit, search index rebuild, drift reconciliation) that do not need full Git history:

```yaml
gitops_store:
  read_operations:
    clone_depth: 1           # shallow clone for read-only consumers
    use_mirror: true         # read from read-only mirror; writes go to primary
    mirror_url: https://git-mirror.corp/dcm/
    mirror_sync_lag_max: PT5M  # alert if mirror is more than 5 minutes behind
```

---

## 2. Store Migration

### 2.1 Migration Principles

DCM store migrations follow three invariants:

1. **No data loss** — every record in the source store must exist in the target store after migration
2. **Audit chain continuity** — the audit hash chain must be unbroken across the migration; audit records written before and after must chain correctly
3. **Read availability during migration** — DCM continues serving read requests throughout; write availability may be briefly paused during cutover

### 2.2 Migration Playbook Structure

Every store migration follows this pattern regardless of source or target implementation:

```
Phase 1 — Prepare
  │  Provision target store alongside source
  │  Validate target store meets storage contract (health check, write test, read test)
  │  Configure DCM to write to BOTH source and target (dual-write mode)
  │
Phase 2 — Backfill
  │  Export all existing records from source
  │  Import records to target in chronological order (preserving provenance timestamps)
  │  Verify record counts match; spot-check content hashes
  │
Phase 3 — Validate
  │  Run DCM's store validation suite against target
  │  Verify audit chain integrity on target store
  │  Verify search index can be rebuilt from target store
  │
Phase 4 — Cutover
  │  Brief write pause (PT30S–PT5M depending on profile)
  │  Disable dual-write; switch DCM to target as primary
  │  Verify /readyz returns healthy
  │  Resume writes to target only
  │
Phase 5 — Decommission source (after burn-in period)
     Default burn-in: P30D (standard), P90D (fsi/sovereign)
     Keep source in read-only mode during burn-in for rollback
```

### 2.3 Common Migration Paths

#### SQLite → PostgreSQL (minimal/dev → standard)

Typical trigger: scaling beyond single-node evaluation environment.

```bash
# Step 1: Export from SQLite
dcm-admin store export \
  --store realized \
  --format jsonl \
  --output realized-export.jsonl

# Step 2: Import to PostgreSQL
dcm-admin store import \
  --store realized \
  --source realized-export.jsonl \
  --target postgres://pg-host:5432/dcm_realized \
  --validate-chain

# Step 3: Enable dual-write
dcm-admin store dual-write enable \
  --store realized \
  --primary sqlite://dcm-realized.db \
  --secondary postgres://pg-host:5432/dcm_realized

# Step 4: Validate
dcm-admin store validate \
  --store realized \
  --target postgres://pg-host:5432/dcm_realized \
  --check-count --check-chain --check-spot-sample 0.05

# Step 5: Cutover
dcm-admin store cutover \
  --store realized \
  --target postgres://pg-host:5432/dcm_realized
```

#### PostgreSQL single-instance → CockroachDB / PostgreSQL HA

Typical trigger: HA requirement for production; multi-region deployment.

**Key difference from SQLite → PostgreSQL:** CockroachDB uses serializable isolation and distributed transactions. Test write throughput under realistic load before cutover — CockroachDB's latency profile differs from single-node PostgreSQL.

```yaml
# Pre-migration checklist
migration_checklist:
  - Load test target under realistic DCM write volume (PT4H minimum)
  - Verify CockroachDB schema compatibility (DCM uses standard PostgreSQL wire protocol)
  - Configure connection pooler (PgBouncer or similar) — CockroachDB default connection count
  - Verify time synchronization (CockroachDB requires NTP within PT500MS across nodes)
  - Test audit chain write under partition scenario
```

#### DCM database — Repo Restructuring

Restructuring a GitOps repository (e.g. monorepo to sharded) requires special handling because Git history must be preserved.

```
Step 1: Enable write buffer — all new writes queue while migration proceeds
Step 2: git filter-repo or git subtree to extract tenant directories to shard repos
Step 3: Validate file counts and content hashes in each shard
Step 4: Update DCM gitops_store configuration to point to shards
Step 5: Drain write buffer — queued writes replay to new shard repos
Step 6: Verify search index rebuild from shards
Step 7: Archive or delete monorepo after burn-in period
```

### 2.4 Rollback Procedure

If migration fails before cutover: disable dual-write, discard target, no impact to production.

If migration fails after cutover (during burn-in):

```
1. Alert: /readyz reports degraded or source store discrepancy detected
2. dcm-admin store rollback --store <name> --to source
   (requires source still in read-only mode — NOT decommissioned)
3. DCM restarts reads/writes from source
4. Export any writes that reached target but not source (if any, during dual-write gap)
5. Import gap records to source
6. Re-enable source as primary
```

**This is why burn-in period exists.** Do not decommission source stores until burn-in completes.

### 2.5 Profile-Governed Migration Constraints

| Profile | Min dual-write duration | Max cutover pause | Burn-in period |
|---------|------------------------|-------------------|----------------|
| `minimal` | P1D | PT5M | P7D |
| `dev` | P3D | PT5M | P14D |
| `standard` | P7D | PT2M | P30D |
| `prod` | P14D | PT1M | P30D |
| `fsi` | P30D | PT30S | P90D |
| `sovereign` | P60D | PT30S | P90D |

---

## 3. Disaster Recovery Runbook

### 3.1 DCM Recovery Architecture

DCM's recovery model is built on a key property: **all durable state is in the stores, not in the control plane.** Control plane components (Policy Engine, Request Orchestrator, etc.) are stateless and can be restarted without data loss. Recovery from most failures is component restart, not data restoration.

The five DCM stores and their recovery characteristics:

| Store | Implementation | Data durability | Recovery method |
|-------|---------------|----------------|-----------------|
| Intent Store | GitOps (Git) | Git replication + remote | Re-clone from remote |
| Requested Store | GitOps or write-once | Git replication / DB replication | Re-clone or DB restore |
| Layer Store | GitOps (Git) | Git replication + remote | Re-clone from remote |
| Realized Store | Write-once (PostgreSQL/CockroachDB) | DB replication / WAL | DB failover or restore |
| Audit Store | Append-only (Kafka/PostgreSQL) | Replication / WAL | Kafka failover or restore |

### 3.2 Recovery Scenarios and Procedures

#### Scenario 1: Single Component Failure (Most Common)

**Symptoms:** One DCM component (e.g. Policy Engine) is unhealthy. `/readyz` shows degraded. Requests may be delayed but not lost.

**RTO:** PT5M  
**RPO:** 0 (no data loss — components are stateless)

```
1. Identify failing component via GET /api/v1/admin/health
2. Check component logs for panic/OOM/deadlock
3. Kubernetes: pod restart is automatic (liveness probe)
   Manual: kubectl rollout restart deployment/dcm-policy-engine
4. Monitor /readyz — should recover within PT2M of pod restart
5. If component repeatedly fails: check Internal CA cert expiry (ICOM-006)
   dcm-admin component cert-status --component policy-engine
6. Write post-incident note to DCM audit store
```

#### Scenario 2: Store Failure (Database / Kafka)

**Symptoms:** `/readyz` fails specific store check. Requests queue or fail depending on which store.

**Realized Store failure (highest severity — blocks realization):**

```
RTO target: PT30M (standard), PT15M (prod), PT5M (fsi/sovereign)
RPO: 0 for PostgreSQL HA (synchronous replication); near-zero for async

1. Confirm store failure: GET /api/v1/admin/health → realized_store: fail
2. If HA: check if automatic failover occurred
   kubectl get pods -n dcm-stores | grep postgres
   Check PostgreSQL replication lag / CockroachDB node status
3. Manual failover if automatic did not trigger:
   dcm-admin store failover --store realized --target replica-2
4. Verify replication caught up: dcm-admin store lag --store realized
5. Verify /readyz recovers
6. Root cause analysis: WAL lag, disk full, network partition
```

**Audit Store failure:**

```
RTO: PT1H acceptable (audit trail can tolerate temporary buffering)
RPO: profile-governed — see Audit Store write buffer policy

1. DCM buffers audit records locally (Commit Log) during store outage
   Write buffer capacity: profile-governed (PT1H standard, PT15M sovereign)
2. Restore Kafka cluster from replica or snapshot
3. DCM drains buffer to restored store automatically on reconnection
4. Verify chain integrity: dcm-admin audit chain-verify --since <outage-start>
```

**DCM database failure (Intent/Requested/Layer):**

```
RTO: PT30M (stores are remountable from Git remote)
RPO: 0 (all writes go to Git remote; loss only if remote is also lost)

1. Git remote unreachable: check network connectivity
2. If Git host is down: DCM switches to cached/buffered mode
   New requests queue in write buffer; reads served from local clone
3. Write buffer capacity: PT4H (standard) — configure per deployment
4. When Git host recovers: buffer drains automatically
5. Force drain: dcm-admin store drain-buffer --store intent
```

#### Scenario 3: Full Control Plane Loss

**Symptoms:** All DCM pods down. Stores intact. Users cannot submit requests.

**RTO:** PT15M (kubernetes deployment restart)  
**RPO:** 0 (stores are external — no data in pods)

```
1. Verify stores are healthy (connect directly):
   dcm-admin store health-check --all --direct

2. Verify Internal CA is available:
   curl -k https://dcm-internal-ca.dcm-system.svc.cluster.local/health

3. Restart DCM deployment (Kubernetes):
   kubectl rollout restart deployment -n dcm-system

4. Monitor /readyz — startup sequence should complete within PT3M:
   watch -n 5 kubectl get pods -n dcm-system

5. Verify session store recovers:
   GET /api/v1/admin/health → session_store: pass

6. Alert consumers: any in-flight requests at time of failure
   are in ACKNOWLEDGED/DISPATCHED state and may need status check
   dcm-admin requests find --status in-flight --since <failure-time>
```

#### Scenario 4: Partial Region Loss (Multi-Region Deployments)

**Symptoms:** One region's DCM instance degraded. Other regions operational.

```
1. DCM federation routes requests away from degraded region (automatic)
   Verify: GET /api/v1/admin/health → federation peer status

2. If region is sovereign-scoped (data must not leave): 
   Alert: sovereignty.migration_required event fires
   Consumers in that region may be blocked until region recovers

3. For non-sovereign regions: traffic reroutes automatically
   Monitor: dcm_requests_total{region} for traffic shift

4. Region recovery: standard Scenario 3 procedure
   After recovery: drift detection validates recovered state
```

#### Scenario 5: Complete Loss (Repave)

The nuclear scenario: entire DCM installation destroyed. Git remote intact.

**RTO:** PT4H–PT24H (depends on infrastructure provisioning speed)  
**RPO:** 0 for GitOps stores; near-zero for Realized/Audit stores

```
1. Provision new Kubernetes cluster (or equivalent)

2. Deploy DCM bootstrap installer:
   helm install dcm-bootstrap dcm/dcm-bootstrap \
     --set gitops.manifest_url=https://git.corp/dcm/dcm-deployment \
     --set gitops.manifest_ref=<last-known-good-commit>

3. DCM bootstrap reads dcm_deployment manifest from Git
   Provisions itself: control plane, Internal CA, stores

4. Restore Realized Store from backup:
   dcm-admin store restore --store realized \
     --from s3://dcm-backups/realized/latest \
     --validate-chain

5. Restore Audit Store from backup or Kafka snapshot:
   dcm-admin store restore --store audit \
     --from s3://dcm-backups/audit/latest \
     --chain-verify

6. Intent/Requested/Layer stores: re-clone from Git remote (already current)

7. DCM rehydrates managed resources in dependency order:
   dcm-admin rehydrate --all-tenants --dry-run  # verify plan first
   dcm-admin rehydrate --all-tenants

8. Drift detection validates recovered state matches declared state:
   dcm-admin drift scan --all --post-recovery

9. Re-issue Internal CA certificates for all components:
   (handled automatically by bootstrap — components acquire new certs)

10. Notify consumers: recovery complete; request status available
```

### 3.3 Recovery Time Objectives by Profile

| Profile | Scenario 1 (component) | Scenario 2 (store) | Scenario 3 (full CP) | Scenario 5 (repave) |
|---------|------------------------|--------------------|-----------------------|---------------------|
| `minimal` | PT15M | PT2H | PT30M | PT24H |
| `standard` | PT5M | PT30M | PT15M | PT8H |
| `prod` | PT2M | PT15M | PT10M | PT4H |
| `fsi` | PT2M | PT5M | PT5M | PT2H |
| `sovereign` | PT1M | PT5M | PT5M | PT2H |

### 3.4 Recovery Point Objectives

| Store | Standard RPO | fsi/sovereign RPO | Notes |
|-------|-------------|------------------|-------|
| Intent Store | 0 | 0 | Git remote is source of truth |
| Requested Store | 0 | 0 | Write-once; replicated |
| Layer Store | 0 | 0 | Git remote is source of truth |
| Realized Store | PT5M | PT1M | Async replication lag |
| Audit Store | PT15M | PT1M | Kafka replication + write buffer |

### 3.5 Backup Schedule

DCM does not manage backups of infrastructure stores directly — that responsibility belongs to the storage platform. Recommended schedules by store:

| Store | Backup method | Frequency | Retention |
|-------|--------------|-----------|-----------|
| Intent / Requested / Layer | Git push to offsite remote | Continuous | Per Git host policy |
| Realized Store | PostgreSQL PITR + daily snapshot | Continuous WAL + P1D snapshot | P90D (standard), P365D (fsi/sovereign) |
| Audit Store | Kafka topic snapshot | P4H | P365D (all profiles — regulatory minimum) |
| Internal CA | Key material backup to HSM/Vault | On change | P7Y (key material outlives certs) |

### 3.6 Post-Recovery Validation Checklist

Run after any Scenario 3+ recovery:

```
□ /livez returns pass on all control plane pods
□ /readyz returns pass (all 5 core dependencies green)
□ GET /api/v1/admin/health shows all components pass
□ dcm-admin audit chain-verify --full returns no broken links
□ dcm-admin store validate --all returns no discrepancies
□ dcm-admin drift scan --all returns no unexpected drift
□ Internal CA certificates valid for all components (ICOM-006)
□ At least one Auth Provider healthy (GET /api/v1/admin/health → auth_providers)
□ Search index rebuild complete (if search index store was affected)
□ Session Store empty (expected — all sessions expired during outage; users re-authenticate)
□ Write post-incident note to audit store with recovery timeline
□ Notify consumers of recovery completion
```

---

## 4. System Policies

| Policy | Rule |
|--------|------|
| `OPS-001` | GitOps store partitioning strategy must be declared in the DCM deployment manifest. Changes to partitioning strategy require dual-write migration procedure (Section 2). |
| `OPS-002` | Store migrations must maintain audit chain continuity across cutover. Audit records written to the source store before cutover and to the target store after cutover must form an unbroken chain. |
| `OPS-003` | Source stores must remain accessible in read-only mode for the profile-governed burn-in period after cutover. Source stores must not be decommissioned until the burn-in period completes and rollback is confirmed unnecessary. |
| `OPS-004` | Recovery from Scenario 3 (full control plane loss) must complete within the profile-governed RTO. If RTO cannot be met, the incident must be escalated and root cause must address the recovery path. |
| `OPS-005` | The post-recovery validation checklist (Section 3.6) must be completed and its results written to the audit store before declaring an incident resolved. |
| `OPS-006` | Audit Store backups must be retained for a minimum of P365D in all profiles, regardless of other data retention policies, to satisfy regulatory audit trail requirements. |
| `OPS-007` | Git remote repositories serving as GitOps stores must be configured with push access from at least two geographically separated locations to prevent single-point-of-failure data loss. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
