---
Document Status: ✅ Stable — DCM architectural decision
Document Type: Architecture Reference — Persistence Decision
Established: 2026-05-26
Maps to: udlm/design-principles/infrastructure-optimization.md
---

# PostgreSQL Mandate

> **Implements contracts defined in UDLM**:
> [udlm/design-principles/infrastructure-optimization.md](https://github.com/croadfeldt/udlm/blob/main/design-principles/infrastructure-optimization.md).
> UDLM requires that all four data domains (Intent, Requested, Realized,
> Discovered) be persistently queryable. The technology choice is not
> specified by UDLM — it is a realization-layer decision. DCM mandates
> **PostgreSQL** (or any PostgreSQL-compatible database: CockroachDB, Aurora
> PostgreSQL, Crunchy Postgres) as its required persistence infrastructure.

This is a **DCM-level architectural decision**, not a UDLM contract. A peer
DCM realization could pick a different SQL category (or a non-SQL category
entirely) and still satisfy the UDLM persistence contract, provided it
honors immutability, queryability, and the wire-level data formats.

---

## 1. The decision

**DCM mandates PostgreSQL as its sole required external infrastructure.**

All other dependencies — identity, secrets, event streaming, caching, Git
ingress, service mesh — can either be handled internally by DCM or
optionally delegated to external systems. PostgreSQL is the floor.

Specifically: any PostgreSQL-compatible database satisfies the mandate.

| Acceptable | Reason |
|---|---|
| PostgreSQL (vanilla) | Reference implementation |
| CockroachDB | Wire-compatible; native HA; sovereignty-friendly partitioning |
| Aurora PostgreSQL | AWS-managed; PostgreSQL wire-compatible |
| Crunchy Postgres | K8s-native operator; PostgreSQL upstream |
| YugabyteDB (PG mode) | Distributed; PostgreSQL wire-compatible |

What disqualifies a database: missing JSONB, missing `LISTEN/NOTIFY`, missing
RLS, missing append-only tables (REVOKE UPDATE/DELETE), missing `pgcrypto`,
or any subset of these. DCM's contract enforcement assumes all of them.

---

## 2. Why PostgreSQL (the rationale)

DCM's design principle is: prescribe **data contracts** (schemas,
immutability rules, versioning, the Merkle-tree audit) — not infrastructure products.
Where a contract maps directly to a single well-understood infrastructure
category, DCM prescribes the category and the contract, not an abstraction
layer over it.

Abstraction layers earn their place when the underlying implementations have
genuinely different interaction contracts — different APIs, different
lifecycle semantics, different operational models. When the implementations
share a standard protocol (SQL, OIDC, AMQP), the protocol is the
abstraction. Adding a DCM-specific abstraction on top of a standard
protocol is unnecessary indirection.

PostgreSQL satisfies every UDLM persistence contract obligation through
native features:

| UDLM contract obligation | PostgreSQL native feature |
|---|---|
| Append-only on Intent / Requested / Audit | `REVOKE UPDATE, DELETE` + audit trigger |
| Versioning on Realized | Row versioning with semantic version columns + `is_current` flag |
| Tamper-evident audit | RFC 9162 Merkle tree over the `audit_records` leaves, signed tree heads |
| Tenant isolation | Row-Level Security (RLS) policies |
| Event-driven pipeline routing | `LISTEN/NOTIFY` |
| JSONB document storage | Native JSONB with GIN indexes |
| Strong transactional consistency | ACID transactions across all DCM tables |
| Sovereignty partitioning | One PostgreSQL instance per sovereignty zone |
| Air-gapped deployment | Single dependency to operate offline |

### 2.1 Why not separate stores per domain

| Concern | Four-store answer (Git + Kafka + Redis + PostgreSQL) | Single-store answer (PostgreSQL) |
|---|---|---|
| Immutability | Git commits are immutable | Append-only tables + REVOKE UPDATE, DELETE + audit trigger |
| Version history | Git log | Row versioning with semantic version fields |
| Audit trail | Git commit metadata | RFC 9162 Merkle tree (stronger — inclusion/consistency proofs against signed tree heads vs Git's graph integrity) |
| PR-based review | Native Git workflow | DCM's Policy Engine + Scoring Model + Authority Tier routing (more sophisticated) |
| Tamper evidence | Git SHA integrity | Per-leaf Merkle inclusion (per-record, not per-repo) |
| Transactional consistency | Cross-store sync required | Native — intent + audit + operation in same transaction |
| Sovereignty partitioning | Separate Git/Kafka/Redis per zone | Separate PostgreSQL instance per zone (one thing to deploy, not four) |
| Air-gapped deployment | Git + Kafka + Redis + PostgreSQL (4 infra dependencies) | PostgreSQL only (1 dependency) |
| Operations skill set | Git admin + Kafka admin + Redis admin + DBA | DBA only |

The four-store approach was historically considered but rejected on
operational and integrity grounds. A single well-understood database
provides stronger guarantees with one-fourth the operational surface.

### 2.2 The "no abstraction layer over standard protocols" principle

DCM does NOT abstract over SQL. The Catalog Manager, Policy Manager,
Request Orchestrator, and all other services use PostgreSQL directly. The
schema is defined by DCM; the queries are DCM-native.

This is the same pattern DCM applies elsewhere:

- OIDC is the abstraction over identity providers; DCM does not add a
  DCM-specific identity abstraction
- AMQP/Kafka is the abstraction over message buses; DCM does not add a
  DCM-specific bus abstraction
- gRPC/HTTP+JSON is the abstraction over RPC; DCM does not add a
  DCM-specific RPC layer

For persistence, SQL is the abstraction. PostgreSQL is the implementation.
DCM mandates PostgreSQL because writing PostgreSQL-flavored SQL is more
direct, more debuggable, and more operationally stable than writing
SQL-via-an-abstraction.

---

## 3. Optional infrastructure (deployment enhancements)

PostgreSQL is required. Everything else is optional:

| Infrastructure | When to add | What it provides |
|---|---|---|
| OIDC IdP | Enterprise auth; multi-tenant federation | External authentication via registered auth_provider |
| Vault | Existing Vault infrastructure; dynamic secrets; full HSM seal | External secrets backend |
| Kafka | >1000 events/sec; multiple consumer groups with independent replay | Replaces pipeline_events + LISTEN/NOTIFY |
| Redis | Read-heavy catalog/placement workloads; geo-distributed reads | Replaces materialized views |
| Git repository | CI/CD integration; PR-based ingress | Adds Git as ingress path alongside API/CLI |
| Service mesh | Production mTLS between services | Replaces application-level TLS config |

Each can be added per-deployment without changing the architectural mandate.
None are required.

---

## 4. Deployment profiles

| Profile | Required | Optional |
|---|---|---|
| **Minimal** (homelab/dev) | PostgreSQL (single instance) | — |
| **Standard** (production) | PostgreSQL (HA) | Keycloak, Vault, Service mesh, Redis |
| **Enterprise** (large scale) | PostgreSQL (HA + read replicas) | Keycloak (HA), Vault (HA + HSM), Service mesh, Kafka, Redis, Git |
| **Sovereign** (air-gapped) | PostgreSQL (per-zone) | Keycloak (per-zone), Vault (per-zone + HSM seal), Service mesh |

---

## 5. Sovereignty partitioning

DCM supports sovereignty zones by deploying separate PostgreSQL instances
per zone (one DCM control plane plus database per sovereignty zone). The
zones do not share a database; federation between zones uses the
DCM-to-DCM federation mechanism (see
[`../runtime-features/federation-runtime.md`](../runtime-features/federation-runtime.md)),
not database replication.

This means a `sovereign` deployment has N PostgreSQL instances for N
sovereignty zones — never one database serving multiple zones. The single
database per zone simplifies sovereignty enforcement (the database
boundary IS the sovereignty boundary).

---

## 6. Realization note

PostgreSQL is **DCM's choice**, not a UDLM requirement. UDLM requires:

- All four data domains are persistently queryable
- Wire-level data formats are honored
- Immutability invariants are maintained for Intent / Requested / Audit
- Versioning is supported for Realized
- Schema-sharing protocol permits federation peers to exchange schemas

A peer DCM realization could pick:

- A purpose-built database (e.g., a wide-column store + audit chain)
- A multi-engine architecture (e.g., separate ledger + queryable cache)
- A different SQL category (MySQL, MariaDB, SQL Server)

...and remain UDLM-conformant, provided the four-domain queryability and
immutability invariants are honored. This DCM realization deliberately
picks a single well-understood SQL category and avoids abstraction-over-SQL.

For implementation details — table structures, schema, query optimization,
indexing, data retention — see
[`postgres-implementation.md`](postgres-implementation.md).
