---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — PostgreSQL Implementation
Established: 2026-05-26
Maps to: udlm/design-principles/infrastructure-optimization.md
---

# PostgreSQL Implementation

> **Implements contracts defined in UDLM**:
> [udlm/design-principles/infrastructure-optimization.md](https://github.com/croadfeldt/udlm/blob/main/design-principles/infrastructure-optimization.md).
> UDLM requires that the four data domains be persistently queryable with
> declared immutability invariants. This document specifies DCM's
> PostgreSQL realization: schema, enforcement mechanisms, query optimization,
> and retention policies.

> See [`postgres-mandate.md`](postgres-mandate.md) for the architectural
> decision and rationale.

---

## 1. Schema design

DCM's database schema enforces the four-domain contracts through PostgreSQL
native features.

### 1.1 Intent domain

```sql
-- Append-only. Raw consumer declarations. Never modified after write.

CREATE TABLE intent_records (
    intent_uuid         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_uuid         UUID NOT NULL,
    tenant_uuid         UUID NOT NULL REFERENCES tenants(tenant_uuid),
    catalog_item_uuid   UUID NOT NULL,
    submitted_by        UUID NOT NULL,
    submitted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_via       VARCHAR(32) NOT NULL
                            CHECK (submitted_via IN ('api', 'gitops', 'cli', 'message_bus')),
    intent_version      INTEGER NOT NULL DEFAULT 1,
    fields              JSONB NOT NULL DEFAULT '{}',
    provenance          JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_intent_entity ON intent_records(entity_uuid, intent_version);
CREATE INDEX idx_intent_tenant ON intent_records(tenant_uuid, submitted_at);

REVOKE UPDATE, DELETE ON intent_records FROM dcm_app;
```

### 1.2 Requested domain

```sql
-- Append-only. Assembled, policy-evaluated, placed payloads.

CREATE TABLE requested_records (
    requested_uuid      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_uuid         UUID NOT NULL,
    tenant_uuid         UUID NOT NULL REFERENCES tenants(tenant_uuid),
    operation_uuid      UUID NOT NULL REFERENCES operations(operation_uuid),
    intent_uuid         UUID NOT NULL REFERENCES intent_records(intent_uuid),
    resource_type       VARCHAR(256) NOT NULL,
    provider_uuid       UUID NOT NULL,
    assembled_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assembled_payload   JSONB NOT NULL DEFAULT '{}',
    layer_sources       JSONB NOT NULL DEFAULT '[]',
    policy_results      JSONB NOT NULL DEFAULT '{}',
    placement_result    JSONB NOT NULL DEFAULT '{}',
    provenance          JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_requested_entity ON requested_records(entity_uuid);
CREATE INDEX idx_requested_tenant ON requested_records(tenant_uuid);
CREATE INDEX idx_requested_operation ON requested_records(operation_uuid);

REVOKE UPDATE, DELETE ON requested_records FROM dcm_app;
```

### 1.3 Realized domain

```sql
-- Versioned rows. is_current flag. Append-on-change semantics.

CREATE TABLE realized_entities (
    realized_uuid       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_uuid         UUID NOT NULL,
    tenant_uuid         UUID NOT NULL REFERENCES tenants(tenant_uuid),
    resource_type       VARCHAR(256) NOT NULL,
    provider_uuid       UUID NOT NULL,
    requested_uuid      UUID NOT NULL REFERENCES requested_records(requested_uuid),
    realized_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version_major       INTEGER NOT NULL,
    version_minor       INTEGER NOT NULL,
    version_revision    INTEGER NOT NULL,
    is_current          BOOLEAN NOT NULL,
    lifecycle_state     VARCHAR(32) NOT NULL,
    realized_payload    JSONB NOT NULL DEFAULT '{}',
    provider_metadata   JSONB NOT NULL DEFAULT '{}',
    provenance          JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_realized_entity_current ON realized_entities(entity_uuid)
    WHERE is_current = true;
CREATE INDEX idx_realized_entity_history ON realized_entities(entity_uuid, realized_at);
CREATE INDEX idx_realized_tenant ON realized_entities(tenant_uuid, realized_at);
CREATE INDEX idx_realized_provider ON realized_entities(provider_uuid, realized_at);

-- Append-on-change enforced via trigger that updates is_current on previous version
-- when a new version is inserted; the previous row's is_current flips to false.
```

### 1.4 Discovered domain

```sql
-- Ephemeral snapshots from provider discovery runs.

CREATE TABLE discovered_records (
    discovery_uuid      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_uuid         UUID,                       -- null for orphans
    tenant_uuid         UUID REFERENCES tenants(tenant_uuid),
    provider_uuid       UUID NOT NULL,
    resource_type       VARCHAR(256) NOT NULL,
    discovered_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    discovery_run_uuid  UUID NOT NULL,
    discovered_fields   JSONB NOT NULL DEFAULT '{}',
    provider_native_id  VARCHAR(512),
    match_confidence    VARCHAR(16) DEFAULT 'exact'
                            CHECK (match_confidence IN ('exact', 'high', 'low', 'unmatched'))
);

CREATE INDEX idx_discovered_entity ON discovered_records(entity_uuid, discovered_at);
CREATE INDEX idx_discovered_run ON discovered_records(discovery_run_uuid);
CREATE INDEX idx_discovered_orphans ON discovered_records(entity_uuid)
    WHERE entity_uuid IS NULL;
```

### 1.5 Pipeline events

```sql
-- Append-only event log. Replaces Kafka for pipeline routing in standard deployments.
-- LISTEN/NOTIFY provides real-time notification to pipeline consumers.

CREATE TABLE pipeline_events (
    event_uuid          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type          VARCHAR(128) NOT NULL,
    entity_uuid         UUID,
    request_uuid        UUID,
    tenant_uuid         UUID,
    actor_uuid          UUID,
    payload             JSONB NOT NULL DEFAULT '{}',
    published_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consumed_by         JSONB NOT NULL DEFAULT '[]',
    consumed_at         TIMESTAMPTZ
);

CREATE INDEX idx_events_type ON pipeline_events(event_type, published_at);
CREATE INDEX idx_events_entity ON pipeline_events(entity_uuid, published_at);
CREATE INDEX idx_events_unconsumed ON pipeline_events(event_type, published_at)
    WHERE consumed_at IS NULL;

REVOKE UPDATE, DELETE ON pipeline_events FROM dcm_app;

-- Notify function for real-time pipeline routing
CREATE OR REPLACE FUNCTION notify_pipeline_event() RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('dcm_pipeline', json_build_object(
        'event_uuid', NEW.event_uuid,
        'event_type', NEW.event_type,
        'entity_uuid', NEW.entity_uuid
    )::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pipeline_event_notify
    AFTER INSERT ON pipeline_events
    FOR EACH ROW EXECUTE FUNCTION notify_pipeline_event();
```

---

## 2. Enforcement mechanisms

### 2.1 Append-only via REVOKE

The application role (`dcm_app`) has only INSERT and SELECT permissions on
append-only tables. UPDATE and DELETE are revoked:

```sql
REVOKE UPDATE, DELETE ON intent_records FROM dcm_app;
REVOKE UPDATE, DELETE ON requested_records FROM dcm_app;
REVOKE UPDATE, DELETE ON pipeline_events FROM dcm_app;
REVOKE UPDATE, DELETE ON audit_records FROM dcm_app;
```

Database administration roles retain full access for operational concerns
(point-in-time recovery, planned schema migrations), but the application
cannot mutate append-only data.

### 2.2 Row-Level Security (tenant isolation)

Every table with tenant data has RLS enforced:

```sql
ALTER TABLE intent_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE requested_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE realized_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE discovered_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_intent ON intent_records
    FOR ALL TO dcm_app
    USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);

CREATE POLICY tenant_isolation_requested ON requested_records
    FOR ALL TO dcm_app
    USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);

CREATE POLICY tenant_isolation_realized ON realized_entities
    FOR ALL TO dcm_app
    USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);

CREATE POLICY tenant_isolation_discovered ON discovered_records
    FOR ALL TO dcm_app
    USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);

CREATE POLICY tenant_isolation_events ON pipeline_events
    FOR SELECT TO dcm_app
    USING (tenant_uuid = current_setting('dcm.current_tenant_uuid')::uuid);
```

The API Gateway sets `dcm.current_tenant_uuid` at session startup per the
authenticated request's tenant scope. RLS enforces that no query can return
rows from other tenants — even with a buggy WHERE clause (STI-001, STI-002).

Platform admin queries set `dcm.current_tenant_uuid = '*'` (resolved via a
separate RLS policy that grants cross-tenant access only to platform_admin
role).

### 2.3 Merkle tree (audit integrity)

Audit integrity follows the **RFC 9162 Merkle-tree** model (DCM ADR-010; the
normative contract is UDLM `AUD-006` / universal-audit §8) — **not** a linked
hash chain. Each `audit_records` row is a **leaf**: `record_hash` is the
SHA-256 of the record's canonical content (the Merkle leaf hash), and
`leaf_index` is its append-only position in the tree. `previous_leaf_hash`
survives only as the per-request **chain-of-custody** link
(`output_payload_hash[N] == input_payload_hash[N+1]`); it is not the integrity
mechanism. The root of trust is a periodically **signed tree head**.

```sql
CREATE TABLE audit_records (
    audit_uuid          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    leaf_index          BIGINT NOT NULL,            -- append-only position in the Merkle tree
    request_uuid        UUID,                       -- chain-of-custody grouping
    entity_uuid         UUID,
    tenant_uuid         UUID,
    action              VARCHAR(64) NOT NULL,
    actor_uuid          UUID,
    actor_type          VARCHAR(32) NOT NULL,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload             JSONB NOT NULL DEFAULT '{}',
    previous_leaf_hash  CHAR(64),                   -- per-request chain of custody, not the integrity root
    record_hash         CHAR(64) NOT NULL,          -- SHA-256 of canonical content = the Merkle leaf hash
    UNIQUE (leaf_index)
);

-- Signed Tree Heads: the root of trust (AUD-006 §8.3). Recomputed and signed
-- every N leaves or T seconds (profile-governed).
CREATE TABLE audit_signed_tree_heads (
    tree_size           BIGINT NOT NULL,            -- number of leaves covered
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sha256_root_hash    CHAR(64) NOT NULL,          -- Merkle root
    signature           BYTEA NOT NULL,             -- Ed25519, DCM's audit signing key
    PRIMARY KEY (tree_size)
);

CREATE INDEX idx_audit_entity ON audit_records(entity_uuid, timestamp);
CREATE INDEX idx_audit_actor ON audit_records(actor_uuid, timestamp);
CREATE INDEX idx_audit_action ON audit_records(action, timestamp);

REVOKE UPDATE, DELETE ON audit_records FROM dcm_app;
```

Verification is by **inclusion and consistency proofs** against a signed tree
head (AUD-006 §8.4), not by walking a linked chain — so targeted integrity
checks (a single entity's or request's leaves) are O(log n) against a tree head
and need no full-database recompute, and an external auditor verifies with only
the tree head and the proof.

### 2.4 Append-on-change via trigger (Realized)

```sql
CREATE OR REPLACE FUNCTION update_realized_current() RETURNS TRIGGER AS $$
BEGIN
    -- Flip previous version's is_current to false
    UPDATE realized_entities
    SET is_current = false
    WHERE entity_uuid = NEW.entity_uuid
      AND realized_uuid != NEW.realized_uuid
      AND is_current = true;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER realized_version_update
    AFTER INSERT ON realized_entities
    FOR EACH ROW WHEN (NEW.is_current = true)
    EXECUTE FUNCTION update_realized_current();
```

DCM never UPDATEs realized rows in-place — it always INSERTs a new version
with `is_current = true`. The trigger atomically flips the previous version's
flag.

---

## 3. Query optimization and indexing

### 3.1 Hot paths

| Query | Index strategy |
|---|---|
| Current state of entity | `idx_realized_entity_current` (partial index WHERE is_current = true) |
| Entity history | `idx_realized_entity_history` (entity_uuid, realized_at) |
| Tenant catalog browse | `idx_realized_tenant` |
| Provider drift comparison | `idx_realized_provider` joined with `idx_discovered_entity` |
| Pipeline event delivery | `idx_events_unconsumed` (partial index WHERE consumed_at IS NULL) |
| Audit chain verification (per entity) | `idx_audit_entity` |
| Policy evaluation context lookup | `idx_policies_active` (partial WHERE status = 'active') |

### 3.2 JSONB GIN indexes

For policy evaluation and complex queries on assembled_payload:

```sql
CREATE INDEX idx_requested_payload_gin ON requested_records USING GIN (assembled_payload);
CREATE INDEX idx_realized_payload_gin  ON realized_entities  USING GIN (realized_payload);
```

These enable fast `assembled_payload @> '{...}'` queries used by policy
evaluation and audit search.

### 3.3 Materialized views (catalog browse)

```sql
CREATE MATERIALIZED VIEW catalog_browse_view AS
  SELECT
    ci.catalog_item_uuid,
    ci.handle,
    ci.display_name,
    ci.resource_type,
    ci.allowed_locations,        -- pre-joined from layer_reference
    ci.allowed_versions,
    ci.tenant_visibility,
    rts.schema_summary,
    pco.cost_estimate
  FROM catalog_items ci
  LEFT JOIN resource_type_specs rts USING (resource_type)
  LEFT JOIN provider_cost_overview pco USING (catalog_item_uuid)
  WHERE ci.status = 'active';

CREATE UNIQUE INDEX idx_catalog_browse ON catalog_browse_view(catalog_item_uuid);

-- Refresh on catalog change events via pipeline_events trigger
```

Materialized views handle catalog browse and other read-heavy lookups. They
refresh on `catalog.changed` events; staleness window is bounded by the
event delivery latency (PT5S in standard deployments).

For workloads requiring sub-second refresh, Redis cache is an optional
deployment enhancement (see [`postgres-mandate.md` §3](postgres-mandate.md)).

---

## 4. Connection pooling

DCM uses PgBouncer in transaction-pooling mode for connection management:

```ini
[databases]
dcm = host=postgres.dcm.svc port=5432 dbname=dcm_prod

[pgbouncer]
pool_mode = transaction
default_pool_size = 50
min_pool_size = 10
max_client_conn = 10000
server_idle_timeout = 600
```

Each DCM control plane service instance establishes a connection through
PgBouncer; PgBouncer multiplexes onto a smaller backend pool. This supports
thousands of concurrent API requests without exhausting PostgreSQL backend
connections.

---

## 5. Data retention and archival policies

DCM applies per-domain retention policies:

| Domain | Default retention | Notes |
|---|---|---|
| Intent | Indefinite | Audit and reproducibility; small per-record size |
| Requested | Indefinite | Provenance chain for active entities; archived per profile after entity decommission |
| Realized (historical versions) | Per profile: P365D (homelab) → P10Y (fsi/sovereign) | `is_current = false` rows |
| Realized (current) | While entity active; permanent post-decommission for audit | `is_current = true` rows; immutable after decommission |
| Discovered | P30D rolling | Discovery snapshots; not retained as authoritative state |
| Pipeline events | P7D rolling for delivered events; indefinite for replay-eligible | Consumed events purged; never-consumed events retained for replay |
| Audit | Indefinite | Tamper-evident chain; never deleted; archived to cold storage per profile |

### 5.1 Archival mechanism

For long-retention data (audit, decommissioned entity records), DCM
supports archival to cold storage:

```yaml
archival_policy:
  archive_to: s3 | gcs | azure_blob | filesystem
  archive_after: P1Y                 # archive after 1 year (configurable)
  archive_format: jsonl + sha256 manifest
  archive_encryption: AES-256-GCM with archived-data-encryption-key (HSM)
  verification_schedule: P30D        # periodic random-sample verification
  retention_in_archive: P10Y (default; fsi/sovereign extends to P30Y)
```

Archived data remains queryable through DCM's audit-archive API, with
multi-second latency vs sub-second for hot data.

### 5.2 Profile-governed retention defaults

| Profile | Historical Realized retention | Audit retention | Archival enabled |
|---|---|---|---|
| homelab | P90D | P1Y | No |
| dev | P180D | P1Y | No |
| standard | P365D | P3Y | Optional |
| prod | P3Y | P7Y | Yes |
| fsi | P7Y | P10Y | Yes; PCI DSS, SOX requirements |
| sovereign | P10Y | P30Y | Yes; sovereign data residency in archive |

---

## 6. High availability and disaster recovery

### 6.1 Standard HA

DCM standard deployments use PostgreSQL streaming replication or
Patroni-managed clusters:

- 1 primary + 2 streaming replicas
- Synchronous replication to at least one replica (`synchronous_commit = remote_apply`
  for fsi/sovereign)
- Automatic failover via Patroni leader election
- PgBouncer reads from primary; failover transparent to DCM services

### 6.2 Backup strategy

- Continuous archiving via WAL streaming to object storage (S3 / GCS / etc.)
- Daily base backups (pg_basebackup or Velero with Crunchy Operator)
- Point-in-time recovery to any second within the WAL retention window
- Encrypted backups (AES-256-GCM with HSM-managed KEK for fsi/sovereign)

### 6.3 Cross-zone DR

For sovereign deployments, each sovereignty zone has independent PostgreSQL
HA. Cross-zone DR uses the DCM federation mechanism (signed export bundles)
rather than database-level replication — preserves the sovereignty boundary.

---

## 7. Sovereignty partitioning

```
Sovereign deployment:
  zone-1 (EU): PostgreSQL HA cluster, DCM control plane, local providers
  zone-2 (US): PostgreSQL HA cluster, DCM control plane, local providers
  zone-3 (APAC): PostgreSQL HA cluster, DCM control plane, local providers

Federation between zones: DCM-to-DCM mTLS tunnels per
runtime-features/federation-runtime.md
No cross-zone database replication.
```

Each zone's PostgreSQL is independent. The database boundary IS the
sovereignty boundary. RLS still applies within each zone for tenant isolation.

---

## 8. Schema migration

DCM uses a forward-only migration tool (`golang-migrate` or `dbmate`):

```
schemas/sql/
  001-initial.sql          # base schema
  002-add-conformance.sql
  003-add-archival.sql
  ...
```

Migrations run as part of DCM control plane bootstrap. The application role
does not have schema-change permissions; only the migration tool's
dedicated role (with DDL grants) runs migrations.

Major schema changes require coordinated DCM version bumps and are
documented in `../reference/implementation-specifications.md`.

---

## 9. Operational queries

Standard operator queries that should be fast (< 100ms p99):

| Query | Expected response |
|---|---|
| `GET /api/v1/resources/{entity_uuid}` | Current Realized State for entity |
| `GET /api/v1/resources/{entity_uuid}/audit` | Per-entity audit chain |
| `GET /api/v1/catalog` | Browse-able catalog items for current tenant |
| `GET /api/v1/admin/policies` | Active policies list (platform admin) |
| `GET /api/v1/admin/drift?since=PT1H` | Recent drift events |
| `GET /api/v1/admin/orphans` | Orphan candidate review queue |

Queries that may take longer (< 5s acceptable):

| Query | Notes |
|---|---|
| `GET /api/v1/admin/audit/search?q=...` | Full-text audit search; JSONB GIN |
| `GET /api/v1/admin/cost/attribution?range=...` | Aggregated cost analysis |
| `POST /api/v1/admin/audit/verify` | Hash chain verification for a tenant |

---

## 10. Realization note

The schemas, indexes, and operational patterns above are **DCM's specific
realization choices**. A peer DCM realization using a different storage
technology would have its own equivalent enforcement mechanisms — different
SQL, different indexes, potentially different concurrency models — while
satisfying the same UDLM persistence contract.
