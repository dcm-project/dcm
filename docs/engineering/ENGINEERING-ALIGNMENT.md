# DCM Engineering Alignment Guide

**Purpose:** Map what the engineering teams have built today against what the DCM architecture requires. Per-repo, concrete, actionable. This is the bridge document between the enhancement-based implementations and the 56-document architecture specification.

**Architecture source of truth:** [dcm-project/dcm](https://github.com/dcm-project/dcm) (restructure branch)

---

## How to Read This Document

Each section covers one team-owned repo. For each:

- **What you built** — summary of current state based on repo analysis
- **What aligns** — what's already correct and should be kept
- **What to add** — new fields, endpoints, or behaviors the architecture requires
- **What to change** — existing patterns that need modification
- **Priority** — what to do first vs what can wait

Items marked 🔴 are required for architecture compliance. Items marked 🟡 are recommended but can be deferred. Items marked 🟢 are already aligned.

---

## 1. catalog-manager

**Repo:** [dcm-project/catalog-manager](https://github.com/dcm-project/catalog-manager) (58 commits)
**Enhancement source:** `catalog-item-schema`, `service-type-definitions`
**Architecture docs:** [05-resource-type-hierarchy.md](https://github.com/croadfeldt/udlm/blob/main/entities/resource-type-hierarchy.md), [06-resource-service-entities.md](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md), [50-subscription-lifecycle.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/subscription-lifecycle.md), [consumer-api-spec](../specifications/consumer-api-spec.md)

### What you built

Three-tier resource model: `ServiceType → CatalogItem → CatalogItemInstance`. OpenAPI-first with oapi-codegen, Chi router, GORM store (PostgreSQL + SQLite), Ginkgo tests. Field configurations with `path`, `editable`, `default`, `validation_schema`, and `depends_on`. Spec construction merges ServiceType base → CatalogItem defaults → user values. AEP-compliant with Spectral linting. Token-based pagination. RFC 7807 errors. 58 commits of real depth.

### What aligns

- 🟢 **ServiceType → CatalogItem → CatalogItemInstance** maps cleanly to architecture's **Resource Type Spec → Catalog Item → Request**
- 🟢 **Field configurations with `editable` and `depends_on`** — the architecture adopts this pattern (incorporated from your enhancement into doc 05)
- 🟢 **AEP compliance** — keep it. The architecture mandates AEP.
- 🟢 **Spec construction** (resolve chain, merge defaults, validate) — matches the Layer Assembly concept in the Request Processor
- 🟢 **Pagination** (page_size/page_token) — AEP standard, correct
- 🟢 **OpenAPI-first with code generation** — correct development pattern

### What to add

- 🔴 **`tenant_uuid` on all resources** — architecture requires mandatory tenant scoping (doc 15, STI-001). Every ServiceType, CatalogItem, and CatalogItemInstance needs a `tenant_uuid` field. Queries must filter by tenant. This is the single biggest gap across all services.
  - **How:** Add `tenant_uuid` column to all GORM models. Read `X-DCM-Tenant` header in middleware, set as GORM scope. Add RLS policies to PostgreSQL schema.
  - **Architecture ref:** doc 49 §4, STI-001, STI-002

- 🔴 **UUID as primary identifier** — the enhancement used `name` as natural key. Architecture requires UUID as primary identifier on all entities (doc 00 §3). You already support optional user-specified IDs — make UUID the canonical identifier and `handle` the human-readable alias.
  - **How:** Rename `id` to `handle` in API responses. Add `uuid` as the primary key returned in all responses. Keep `id` query param for user-specified handles.

- 🔴 **`consumption_models` and `subscription_tiers` on CatalogItems** — new fields from doc 50 (Subscription Lifecycle). Catalog items declare whether they support `on_demand`, `subscription`, or both. Subscription-capable items include tier definitions with entitlements.
  - **How:** Add `consumption_models` (string array) and `subscription_tiers` (JSONB) to CatalogItem model. Default `consumption_models` to `["on_demand"]` for backward compatibility.

- 🔴 **Provenance tracking** — every field modification must record who changed it, when, and why (doc 00 §4.3). Currently absent from all enhancement-based services.
  - **How:** Add `provenance` JSONB column. On create/update, write `{field_path: {source, actor_uuid, timestamp, reason}}` for each modified field.

- 🟡 **Portability classification** — every field in a ServiceType spec should declare `universal|conditional|provider_specific|exclusive` (doc 05 §3). This enables the portability model for multi-provider scenarios.
  - **How:** Add optional `portability` field to ServiceType field definitions.

- 🟡 **Version model** — switch from `apiVersion: v1alpha1` to semantic versioning (Major.Minor.Revision) per doc 03 §2. All definitions need `version` field.

- 🟡 **Deprecation lifecycle** — add `status` field with values `active → deprecated → retired` per doc 06 §4.

- 🟡 **Audit event emission** — on every CRU operation, publish a structured event to the `dcm-events` Kafka topic. Format per doc 33 (Event Catalog).

### What to change

- 🔴 **CatalogItemInstance creation triggers pipeline, not direct Placement Manager call** — currently, creating an instance forwards directly to the Placement Manager. Architecture requires the request to enter the pipeline: Intent → Layer Assembly → Policy Evaluation → Placement → Provider Dispatch. The catalog-manager should publish a `request.submitted` event to Kafka (or call the Request Orchestrator) rather than calling Placement Manager directly.
  - **Impact:** This is a structural integration change. The Placement Manager call moves from catalog-manager to the pipeline. Catalog-manager becomes the Intent capture point.
  - **Migration:** Phase 1 — keep direct call, add Kafka publish alongside. Phase 2 — remove direct call, pipeline handles everything.

- 🟡 **Dual-path endpoint registration for AEP custom methods** — register both `:rehydrate` and `/rehydrate` paths for the same handler, to support both AEP-compliant clients and gateway-compatible routing.

### Priority

1. Add `tenant_uuid` to all models and queries
2. Publish `request.submitted` event on CatalogItemInstance creation
3. Add `consumption_models` and `subscription_tiers` to CatalogItem
4. Add `provenance` tracking
5. UUID-first identification model

---

## 2. service-provider-manager

**Repo:** [dcm-project/service-provider-manager](https://github.com/dcm-project/service-provider-manager) (110 commits)
**Enhancement source:** `sp-registration-flow`
**Architecture docs:** [A-provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md), [20-resource-type-registry.md](https://github.com/croadfeldt/udlm/blob/main/governance/registry-governance.md), [43-provider-callback-auth.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-callback-auth.md)

### What you built

Provider registration CRUD (POST/GET/PUT/DELETE) with health endpoint. Go client library for providers. GORM store. E2E tests. Docker Compose for local dev. Clean three-layer architecture matching the catalog-manager pattern.

### What aligns

- 🟢 **Provider registration CRUD** — core functionality is correct
- 🟢 **Go client library** — providers will use this to integrate with DCM
- 🟢 **Same development pattern** (oapi-codegen, Chi, GORM) — consistent with catalog-manager

### What to add

- 🔴 **Registration payload expansion** — the enhancement's registration payload is minimal. Architecture requires:
  - `sovereignty_declarations` — what sovereignty zones the provider operates in (doc A §3)
  - `supported_resource_types` — array of FQN resource types the provider can realize
  - `capability_extension` — structured declaration of what the provider can do
  - `capacity_model` — `static|dynamic|on_demand` (doc A §5)
  - `ownership_model_declaration` — how the provider handles entity ownership
  - `public_key_pem` — for mTLS mutual authentication (doc 43, PCA-001)
  - **How:** Add JSONB columns for structured fields. Extend OpenAPI spec with new request/response fields.
  - **Note (doc 51):** DCM defines 5 provider types: `service_provider`, `information_provider`, `auth_provider`, `peer_dcm`, `process_provider`. Credentials and notifications are handled by service_providers via resource type declarations.

- 🔴 **Provider status lifecycle** — current model is likely binary (registered/not). Architecture requires: `PENDING → ACTIVE → SUSPENDED → DEREGISTERED | SANDBOX` with approval pipeline (auto/reviewed/verified/authorized per doc A §2).
  - **How:** Add `status` column with CHECK constraint. Add admin approval endpoint.

- 🔴 **Health monitoring expansion** — current health check is binary (200/non-200). Architecture requires structured Provider Lifecycle Events: `DEGRADATION`, `MAINTENANCE`, `UNSANCTIONED_CHANGE`, `CAPACITY_CHANGE` per doc A §7.
  - **How:** Add `POST /api/v1/providers/{uuid}/lifecycle-event` endpoint that accepts structured event payloads. Keep `GET /health` for liveness.

- 🔴 **Provider Callback Authentication** — two-layer mTLS + credential model per doc 43 (PCA-001 through PCA-010). Providers must authenticate inbound callbacks.
  - **How:** Store `public_key_pem` and `callback_credential_hash` on provider record. Validate on callback receipt.

- 🔴 **Tenant scoping** — same as catalog-manager (STI-001).

- 🟡 **Accreditation status** — providers can have accreditation levels that affect what resource types they're trusted to realize (doc 26).

### What to change

- 🟡 **Capacity reporting** — the enhancement treats `totalCpu`/`totalMemory` as static registration fields. Architecture uses a three-mode model (static declared, dynamic reported, on-demand unlimited). For dynamic mode, providers push capacity updates via the lifecycle event endpoint.

### Priority

1. Add `tenant_uuid`
2. Expand registration payload (sovereignty, capabilities, resource types)
3. Add provider status lifecycle with approval
4. Add lifecycle event endpoint
5. PCA authentication

---

## 3. policy-manager

**Repo:** [dcm-project/policy-manager](https://github.com/dcm-project/policy-manager) (~30 commits)
**Enhancement source:** `policy-engine`
**Architecture docs:** [B-policy-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md), [29-scoring-model.md](../../architecture/convergence-engine/scoring.md), [03-layering-and-versioning.md](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md)

### What you built

Policy artifact CRUD. Stores policy definitions and provides retrieval API.

### What aligns

- 🟢 **Policy artifact storage and retrieval** — correct as a policy repository
- 🟢 **Same development pattern**

### What to add

- 🔴 **Eight policy types** — architecture defines 8 distinct policy categories: `gatekeeper`, `validation`, `transformation`, `placement`, `lifecycle`, `cost_attribution`, `recovery`, `itsm_action` (doc B §2). Each has different execution semantics (boolean deny vs scoring vs field mutation vs routing).
  - **How:** Add `policy_type` field to policy artifacts with CHECK constraint.

- 🔴 **Policy evaluation endpoint** — beyond CRUD, the policy-manager needs an endpoint that other pipeline services call to evaluate policies against a request payload. `POST /api/v1/policies/evaluate` takes a payload + context and returns evaluation results.
  - **How:** This is the core business logic addition. The Request Orchestrator will call this during the pipeline's policy evaluation stage.

- 🔴 **OPA/Rego integration** — policies are expressed as Rego rules (doc B §4). The policy-manager should embed an OPA engine or delegate to an OPA sidecar for evaluation.
  - **How:** Add OPA Go library as dependency. Load Rego policies from stored artifacts. Evaluate against input payloads.

- 🔴 **Scoring model** — GateKeeper policies produce compliance scores; Validation policies produce completeness scores. The scoring model (doc 29) aggregates these into an approval routing decision.
  - **How:** Policy evaluation response includes `score`, `enforcement_class`, and `output_class` fields.

- 🔴 **Provenance on mutations** — Transformation policies modify request payloads. Every modification must record provenance (who, when, which policy, what changed).

- 🔴 **Tenant scoping** — the enhancement explicitly deferred tenant support. Architecture treats tenant as mandatory. Implementation approach: add `tenant_uuid` column defaulting to a single-tenant UUID initially, then enforce multi-tenant scoping when multi-tenancy is enabled.

- 🟡 **GitOps integration** — policies should be maintainable via Git PRs. The policy-manager can watch a Git repo for policy artifact changes (or accept pushes from a GitOps watcher).

### What to change

- 🔴 **`selected_provider` removal** — the enhancement has the policy engine directly selecting providers. Architecture separates this into Placement (a distinct component). Policy evaluation produces a narrowed field set and constraints; the Placement Manager selects the provider based on those constraints. Remove `selected_provider` from policy evaluation output.

### Priority

1. Add policy evaluation endpoint with OPA integration
2. Define 8 policy types
3. Add tenant scoping
4. Implement scoring model
5. Remove `selected_provider` from output (placement is separate)

---

## 4. placement-manager

**Repo:** [dcm-project/placement-manager](https://github.com/dcm-project/placement-manager) (~30 commits)
**Architecture docs:** [29-scoring-model.md](../../architecture/convergence-engine/scoring.md), [48-location-topology-layers.md](https://github.com/croadfeldt/udlm/blob/main/topology/location-topology-layers.md)

### What aligns

- 🟢 **Separate placement component** — architecture mandates this separation from policy

### What to add

- 🔴 **Specificity narrowing model** — placement works by progressive narrowing: available providers → capability match → sovereignty match → capacity match → placement policy → scored selection (doc 29 §4).
- 🔴 **Location topology awareness** — placement considers region, zone, sovereignty zone constraints (doc 48).
- 🔴 **Tenant scoping**
- 🟡 **Placement policy integration** — consumes placement policy evaluation results from policy-manager.

---

## 5. api-gateway

**Repo:** [dcm-project/api-gateway](https://github.com/dcm-project/api-gateway) (33 commits)
**Architecture docs:** [consumer-api-spec](../specifications/consumer-api-spec.md), [admin-api-spec](../specifications/dcm-admin-api-spec.md)

### What you built

KrakenD-based gateway. Config-driven routing to 4 backends (SPM, Catalog, Policy, Placement). Docker Compose for full stack. Health check passthrough.

### What aligns

- 🟢 **Config-driven routing** — correct pattern
- 🟢 **Single ingress point** — architecture requires this
- 🟢 **Health passthrough** — correct

### What to change

- 🔴 **KrakenD → Traefik** — Ygal's PR #19 is the right move. KrakenD doesn't support `:` in URLs, which AEP-136 custom methods require. Traefik (CNCF graduated) handles colons natively.

### What to add

- 🔴 **Route expansion** — current config routes to 4 backends. Full architecture has 9+ backends (add request-orchestrator, request-processor, audit, discovery, subscription endpoints).
  - **How:** Add endpoint entries to the routing config for all greenfield services.

- 🔴 **`X-DCM-Tenant` header injection** — gateway must extract tenant from JWT claims and set `X-DCM-Tenant` header on all backend requests. This is how tenant context propagates.

- 🔴 **`X-Request-ID` generation** — gateway issues UUID for every inbound request. This becomes the `operation_uuid` / `request_uuid` for the pipeline (doc 49 §7.1).

- 🟡 **JWT validation** — marked as future in the current repo. Architecture requires Keycloak JWT validation at the gateway layer.

- 🟡 **Rate limiting** — per-tenant, per-endpoint rate limiting.

### Priority

1. Merge Traefik PR
2. Add `X-DCM-Tenant` and `X-Request-ID` headers
3. Add routes for greenfield services
4. JWT validation (Keycloak)

---

## 6. kubevirt-service-provider

**Repo:** [dcm-project/kubevirt-service-provider](https://github.com/dcm-project/kubevirt-service-provider)
**Enhancement source:** `kubevirt-sp`
**Architecture docs:** [A-provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md), [06-resource-service-entities.md](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md)

### What aligns

- 🟢 **Real KubeVirt integration** — actual VM provisioning, not a scaffold
- 🟢 **VMI phase change monitoring**

### What to add

- 🔴 **Full Denaturalization** — currently returns minimal status. Architecture requires converting KubeVirt-native response into complete DCM-format realized payload with all fields mapped back to DCM's unified model (doc A §6).
- 🔴 **Unsanctioned change detection** — beyond VMI phase changes, detect field-level drift between DCM's Realized State and KubeVirt's actual state.
- 🔴 **Discovery endpoint** — `GET /api/v1/compute.virtualmachine/discover` returns all VMs the provider manages.
- 🔴 **Registration expansion** — same as service-provider-manager §2 (sovereignty, capabilities, etc.)

### Priority

1. Full Denaturalization (return complete DCM-format payloads)
2. Discovery endpoint
3. Unsanctioned change detection

---

## 7. acm-cluster-service-provider

**Repo:** [dcm-project/acm-cluster-service-provider](https://github.com/dcm-project/acm-cluster-service-provider)
**Architecture docs:** [A-provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md)

### Same pattern as kubevirt-service-provider

- 🔴 Full Denaturalization
- 🔴 Discovery endpoint
- 🔴 Registration expansion

---

## 8. three-tier-app-demo-service-provider

**Repo:** [dcm-project/three-tier-app-demo-service-provider](https://github.com/dcm-project/three-tier-app-demo-service-provider)
**Architecture docs:** [30-meta-provider-composability.md](https://github.com/croadfeldt/udlm/blob/main/entities/composite-service-model.md)

### What aligns

- 🟢 **Compound/meta provider pattern** — orchestrates multiple sub-resources

### What to add

- 🔴 **Composite Service contract compliance** — architecture's Composite Service Composition Model (doc 30) requires: composition declaration at registration, dependency graph between constituents, cascading lifecycle management, aggregated status reporting.
- 🟡 **Subscription support** — meta providers can offer subscription-based composite services (doc 50 §12, Q2).

---

## Cross-Cutting Themes

These gaps appear in every team service:

| Gap | Architecture Requirement | Impact | Implementation |
|-----|------------------------|--------|----------------|
| **Tenant scoping** | `tenant_uuid` on every resource, RLS on PostgreSQL | 🔴 Required | Add column, middleware, RLS policies |
| **Provenance tracking** | Field-level `{source, actor, timestamp}` on every modification | 🔴 Required | Add `provenance` JSONB column |
| **Audit event emission** | Every CRU operation publishes to `dcm-events` Kafka topic | 🔴 Required | Add Kafka producer, publish on handler completion |
| **UUID-first identity** | UUID as primary identifier, `handle` as human alias | 🔴 Required | Rename `id`/`name` to `handle`, add `uuid` primary |
| **Universal versioning** | Semantic versioning (Major.Minor.Revision) on all artifacts | 🟡 Deferred | Add `version` field, migrate from `v1alpha1` |
| **Deprecation model** | `active → deprecated → retired` lifecycle on definitions | 🟡 Deferred | Add `status` field with lifecycle |
| **Portability classification** | `universal\|conditional\|provider_specific\|exclusive` per field | 🟡 Deferred | Add to field metadata |

---

## Suggested Implementation Order

### Phase 1 — Structural (do first, enables everything else)

1. **Tenant scoping** across all services — `X-DCM-Tenant` header, middleware, RLS
2. **API Gateway Traefik migration** — unblocks AEP custom methods
3. **Request pipeline integration** — catalog-manager publishes events instead of direct Placement Manager call
4. **Policy evaluation endpoint** — OPA-backed evaluation in policy-manager

### Phase 2 — Contract Compliance

5. **Provider registration expansion** — sovereignty, capabilities, resource types, PCA
6. **Provider Denaturalization** — kubevirt-sp and acm-cluster-sp return full DCM payloads
7. **Provenance tracking** — across all services
8. **Audit event emission** — Kafka producer in all services

### Phase 3 — Feature Completeness

9. **Subscription support** — catalog-manager, consumer API endpoints
10. **Discovery endpoints** — all service providers
11. **Scoring model** — policy-manager
12. **UUID-first identity** — across all services

### Phase 4 — Hardening

13. **Universal versioning** migration
14. **Deprecation lifecycle**
15. **Portability classification**
16. **JWT validation** at gateway

---

## Services That Don't Exist Yet

These are being built in [dcm-project/dcm-examples](https://github.com/dcm-project/dcm-examples) as greenfield:

| Service | Role | Why it doesn't exist |
|---------|------|---------------------|
| **Request Orchestrator** | Event bus — routes Kafka events to pipeline stages | New architectural component — the async pipeline core |
| **Request Processor** | Layer assembly — merges core/service/consumer layers | New architectural component — data assembly |
| **Audit Service** | Immutable audit store with SHA-256 hash chain | New architectural component — compliance evidence |
| **Discovery Service** | Scheduled discovery + drift detection | New architectural component — state reconciliation |

These will eventually need their own repos in the `dcm-project` org.

---

*This document maps to the DCM architecture as of 2026-04-02. Architecture source of truth: [dcm-project/dcm](https://github.com/dcm-project/dcm).*
