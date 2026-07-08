# Deployment Pattern Catalog — How It Overlays on DCM

**Date:** April 2026  
**Status:** Architecture Overlay — For Team Discussion

---

## What a Deployment Pattern Is

A deployment pattern is a **reusable, provider-agnostic blueprint** that defines a collection of resources, their dependencies, their runtime wiring, and their operational policies — together delivering a service that no single provider offers.

Examples:

| Pattern | Constituents | What it delivers |
|---------|-------------|-----------------|
| **Standard Web Application** | 2 app server VMs, 1 PostgreSQL DB, 1 load balancer, 1 network segment, 3 DNS records | A production web app with HA, monitoring, and DNS |
| **Secure Data Pipeline** | 1 Kafka cluster, 2 worker VMs, 1 S3-compatible store, 1 network policy, 1 encryption key | An encrypted ingest pipeline with data residency controls |
| **Developer Sandbox** | 1 VM, 1 namespace, 1 ephemeral DB, 1 port forward | A disposable dev environment with TTL auto-cleanup |
| **Regulated Database Service** | 1 PostgreSQL cluster (HA), 1 backup schedule, 1 encryption key, 1 audit log sink, 2 DNS records | A database meeting FSI data handling requirements |
| **Edge Compute Node** | 1 bare metal host, 1 MicroShift cluster, 1 VPN tunnel, 1 monitoring agent, 1 cert | A self-contained edge node with central management |

The key property: **no single provider owns the pattern.** The PostgreSQL DB might come from one provider, the VMs from another, the load balancer from a third, and the DNS records from a fourth. The pattern defines *what* is needed and *how the pieces connect* — DCM figures out *who* provides each piece.

---

## The Layering Model

```
┌─────────────────────────────────────────────────────────┐
│                   PATTERN CATALOG                        │
│  Curated library of reusable deployment blueprints       │
│  "Standard Web App" · "Data Pipeline" · "Dev Sandbox"    │
│                                                          │
│  Authored by: Platform Engineers                         │
│  Consumed by: Consumer Developers                        │
│  Stored in: Resource Type Registry (composite types)      │
├─────────────────────────────────────────────────────────┤
│                   SERVICE CATALOG                         │
│  Provider-specific offerings of patterns + atomic items   │
│  "EU-WEST Web App — Standard" · "APAC VM — Large"        │
│                                                          │
│  Populated by: Providers (atomic) + Patterns (composite)  │
│  Consumed by: Consumer Developers                        │
├─────────────────────────────────────────────────────────┤
│                   DCM CONTROL PLANE                       │
│  Decompose → Policy → Placement → Dispatch → Audit       │
│                                                          │
│  Processes: Both atomic requests and pattern requests     │
│  Each constituent → full pipeline independently           │
├─────────────────────────────────────────────────────────┤
│                   SERVICE PROVIDERS                       │
│  VM · Network · Database · DNS · Storage · Container      │
│                                                          │
│  Fulfill: Individual constituents of a pattern            │
│  Report back: Realized state per constituent              │
└─────────────────────────────────────────────────────────┘
```

**The Pattern Catalog is not a new architectural component.** It is a curated view of the Resource Type Registry filtered to composite resource types. DCM already has all the machinery to execute patterns — the composite service model, dependency graphs, binding fields, and constituent dispatch. What the Pattern Catalog adds is the **curation and consumer experience layer** on top of that machinery.

---

## How a Pattern Maps to DCM Constructs

A single deployment pattern maps to these existing DCM concepts:

| Pattern concept | DCM construct | Where it lives |
|----------------|--------------|----------------|
| The pattern itself | Composite Resource Type Specification | Resource Type Registry |
| The constituents | Resource Type references with dependency declarations | `constituents[]` in the composite spec |
| How pieces connect | Binding fields — runtime values from one constituent injected into another | `binding_fields[]` on dependent constituents |
| What the consumer fills in | Parameterized fields exposed at the pattern level | `fields_from_parent[]` mapping pattern params → constituent fields |
| Who provides each piece | `provided_by: external` (DCM places) or `provided_by: self` (composite service handles) | Per-constituent declaration |
| What happens on failure | Lifecycle policy on the composite spec | `on_constituent_failure: rollback_all | continue_degraded | notify` |
| Operational policies | Standard DCM policies scoped to the pattern's resource type | Policy match on `resource_type = ApplicationStack.WebApp` |

---

## Concrete Example: "Standard Web Application" Pattern

### Pattern Definition (authored by Platform Engineer)

```yaml
# Registered in Resource Type Registry as a composite resource type
resource_type: ApplicationStack.WebApp
version: "1.0.0"
entity_type: composite_resource
description: "Production web application with database, app servers, load balancer, and DNS"

# What the consumer fills in when requesting this pattern
parameters:
  app_name:
    type: string
    required: true
    description: "Application name — used for hostnames, DNS, and resource tagging"
  environment:
    type: string
    required: true
    constraint: { layer_reference: "environment" }  # values governed by environment layers
  db_engine:
    type: string
    required: true
    default: postgresql
    constraint: { enum: [postgresql, mysql, mariadb] }
  db_storage_gb:
    type: integer
    required: true
    default: 50
    constraint: { min: 10, max: 1000 }
  app_replicas:
    type: integer
    required: true
    default: 2
    constraint: { min: 1, max: 10 }
  expose_public:
    type: boolean
    default: false
    description: "Whether to create a public DNS record and public LB listener"

# The constituents and how they connect
constituents:
  - name: network_segment
    resource_type: Network.Segment
    provided_by: external
    depends_on: []
    required_for_delivery: required
    fields_from_parent:
      - source: "environment"
        target: "environment"
      - source: "app_name"
        target: "segment_name_prefix"

  - name: database
    resource_type: Database.Managed
    provided_by: external
    depends_on: [network_segment]
    required_for_delivery: required
    binding_fields:
      - source: "network_segment.subnet_cidr"
        target: "database.network_cidr"
      - source: "network_segment.security_group_id"
        target: "database.security_group_id"
    fields_from_parent:
      - source: "db_engine"
        target: "engine"
      - source: "db_storage_gb"
        target: "storage_gb"
      - source: "environment"
        target: "environment"

  - name: app_server
    resource_type: Compute.VirtualMachine
    provided_by: external
    depends_on: [database, network_segment]
    required_for_delivery: required
    binding_fields:
      - source: "database.ip_address"
        target: "app_server.config.db_host"
      - source: "database.port"
        target: "app_server.config.db_port"
      - source: "database.credentials_ref"
        target: "app_server.config.db_credentials_ref"
      - source: "network_segment.subnet_cidr"
        target: "app_server.network_cidr"
    fields_from_parent:
      - source: "app_name"
        target: "hostname_prefix"
      - source: "app_replicas"
        target: "replicas"
      - source: "environment"
        target: "environment"

  - name: load_balancer
    resource_type: Network.LoadBalancer
    provided_by: external
    depends_on: [app_server]
    required_for_delivery: required
    binding_fields:
      - source: "app_server.ip_addresses"
        target: "load_balancer.backend_pool"
      - source: "app_server.port"
        target: "load_balancer.backend_port"
    fields_from_parent:
      - source: "app_name"
        target: "lb_name"
      - source: "expose_public"
        target: "public_listener"

  - name: dns_internal
    resource_type: DNS.Record
    provided_by: external
    depends_on: [load_balancer]
    required_for_delivery: partial
    binding_fields:
      - source: "load_balancer.vip_address"
        target: "dns_internal.target_address"
    fields_from_parent:
      - source: "app_name"
        target: "hostname"

  - name: dns_public
    resource_type: DNS.Record
    provided_by: external
    depends_on: [load_balancer]
    required_for_delivery: optional
    condition: "parent.expose_public == true"  # only created if consumer wants public access
    binding_fields:
      - source: "load_balancer.public_vip_address"
        target: "dns_public.target_address"
    fields_from_parent:
      - source: "app_name"
        target: "hostname"

lifecycle_policy:
  on_constituent_failure: rollback_all
  decommission_order: reverse_dependency  # DNS first, then LB, then app, then DB, then network
```

### What the Consumer Sees

The consumer browses the service catalog, finds "Standard Web Application," and submits:

```json
POST /api/v1/requests
{
  "catalog_item_uuid": "webapp-standard-uuid",
  "fields": {
    "app_name": "pet-clinic",
    "environment": "production",
    "db_engine": "postgresql",
    "db_storage_gb": 100,
    "app_replicas": 3,
    "expose_public": true
  }
}
```

Six fields. The consumer has no idea that this will produce 6 resources across potentially 4 different providers.

### What DCM Does

```
1. Intent captured — consumer's 6 fields stored

2. Pattern decomposed — DCM reads the composite resource type spec
   → 6 constituents identified
   → Dependency graph resolved:
     Network Segment (no deps)
       ├── Database (needs network)
       │     └── App Server (needs DB + network)
       │           └── Load Balancer (needs app server)
       │                 ├── DNS Internal (needs LB)
       │                 └── DNS Public (needs LB, conditional on expose_public=true)

3. Each constituent gets its own full pipeline:
   → Layer assembly (datacenter, environment, tenant, compliance layers merge in)
   → Policy evaluation (sovereignty, sizing, naming, monitoring — per constituent)
   → Placement (each constituent placed independently, all honoring sovereignty)

4. Execution in dependency order:

   Round 1: Network Segment
     → Placed with EU-WEST network provider
     → Realized: subnet_cidr=10.5.0.0/24, security_group_id=sg-abc123

   Round 2: Database (binding fields inject network values)
     → config.network_cidr = 10.5.0.0/24 (from network_segment)
     → config.security_group_id = sg-abc123 (from network_segment)
     → Placed with EU-WEST database provider
     → Realized: ip_address=10.5.0.50, port=5432, credentials_ref=vault:secret/pet-clinic-db

   Round 3: App Server (binding fields inject DB + network values)
     → config.db_host = 10.5.0.50 (from database)
     → config.db_port = 5432 (from database)
     → config.db_credentials_ref = vault:secret/pet-clinic-db (from database)
     → config.network_cidr = 10.5.0.0/24 (from network_segment)
     → Placed with EU-WEST compute provider, 3 replicas
     → Realized: ip_addresses=[10.5.0.10, 10.5.0.11, 10.5.0.12], port=8080

   Round 4: Load Balancer (binding fields inject app server IPs)
     → config.backend_pool = [10.5.0.10, 10.5.0.11, 10.5.0.12] (from app_server)
     → config.backend_port = 8080 (from app_server)
     → Placed with EU-WEST network provider
     → Realized: vip_address=10.5.0.100, public_vip_address=203.0.113.50

   Round 5: DNS records (binding fields inject LB addresses)
     → DNS Internal: pet-clinic.internal → 10.5.0.100
     → DNS Public: pet-clinic.example.com → 203.0.113.50 (created because expose_public=true)

5. All constituents realized → composite entity status: OPERATIONAL
   → Consumer receives: entity_uuid, status, and connection details
   → 6 entities, each with independent audit trail, drift detection, lifecycle
```

### What Policies See

Policies don't need special awareness of patterns. Each constituent is a standard DCM request with a standard resource type. Existing policies apply naturally:

| Policy | Fires on which constituent | What it does |
|--------|---------------------------|-------------|
| Sovereignty Gating Policy | All 6 | Ensures all constituents land in EU-WEST |
| VM sizing limits | App Server only | Validates replica count and VM size within tenant tier |
| DB storage limits | Database only | Validates db_storage_gb within allowed range |
| Network naming | Network Segment, DNS | Enforces naming conventions |
| Monitoring injection | App Server, Database | Injects monitoring agent config |
| Backup policy | Database | Injects backup schedule based on environment |

**No new policy types are needed.** The pattern decomposes into standard resource types, and standard policies match on those types.

---

## How the Pattern Catalog Surfaces in DCM

### In the Resource Type Registry

Patterns are compound Resource Type Specifications with `entity_type: composite_resource`. They live alongside atomic resource types in the same registry:

```
Resource Type Registry
├── Compute.VirtualMachine (atomic)
├── Network.Segment (atomic)
├── Database.Managed (atomic)
├── DNS.Record (atomic)
├── Network.LoadBalancer (atomic)
├── ApplicationStack.WebApp (composite ← this is a pattern)
├── ApplicationStack.DataPipeline (composite ← this is a pattern)
├── Environment.DevSandbox (composite ← this is a pattern)
└── Platform.EdgeNode (composite ← this is a pattern)
```

### In the Service Catalog

Provider catalog items can reference either atomic or composite resource types. For patterns, the catalog item represents the pattern itself — the consumer requests the pattern, not the individual constituents:

```
Service Catalog
├── "EU-WEST VM — Standard" → Compute.VirtualMachine (atomic, provider-specific)
├── "EU-WEST VM — Large" → Compute.VirtualMachine (atomic, provider-specific)
├── "Standard Web Application" → ApplicationStack.WebApp (composite, multi-provider)
├── "Secure Data Pipeline" → ApplicationStack.DataPipeline (composite, multi-provider)
└── "Developer Sandbox" → Environment.DevSandbox (composite, multi-provider)
```

### In the Consumer API

No API changes. The consumer requests a catalog item. Whether it's atomic or compound is transparent — the same `POST /api/v1/requests` endpoint handles both. The response includes constituent status for composite requests.

### In RHDH

The RHDH catalog page shows patterns alongside atomic offerings. Patterns have a "Components" view showing the constituent resources, their dependency graph, and (after realization) the binding field values. Platform engineers use RHDH scaffolding templates to create new patterns.

---

## Who Authors Patterns vs Who Consumes Them

| Role | What they do with patterns |
|------|--------------------------|
| **Platform Engineer** | Authors pattern definitions (composite resource type specs). Defines constituents, dependencies, binding fields, parameters, lifecycle policies. Registers patterns in the Resource Type Registry. Creates service catalog items for patterns. |
| **Policy/Compliance Owner** | Writes policies that apply to pattern constituents. Does not need to know about patterns specifically — policies match on resource types, which patterns decompose into. May also write pattern-level policies (e.g., "all ApplicationStack.* types require monitoring on every constituent"). |
| **Consumer Developer** | Browses the catalog, selects a pattern, fills in parameters, submits. Sees aggregate status. Can drill into constituent detail. Does not need to understand the decomposition. |
| **Infrastructure Operator** | Provides the atomic services that patterns compose. Registers providers for Compute, Network, Database, DNS — not for the pattern itself. |

---

## Pattern Lifecycle

Patterns follow the standard DCM artifact lifecycle:

```
developing → proposed → active → deprecated → retired
```

**Versioning:** Patterns are versioned (`ApplicationStack.WebApp v1.0.0`). A new version can add optional constituents, change defaults, or add new binding fields without breaking existing deployments. Removing a required constituent is a major version bump.

**Deprecation:** When a pattern version is deprecated, existing realized instances continue operating. New requests are redirected to the successor version. Consumers are notified of the deprecation timeline.

**Pattern evolution:** Adding an optional constituent (e.g., adding a cache layer to the web app pattern) is a minor version bump. Existing deployments don't gain the new constituent automatically — but new requests do. Consumers with existing deployments can opt in via an update request.

---

## Interaction with Other DCM Features

| Feature | How it interacts with patterns |
|---------|-------------------------------|
| **Drift detection** | Each constituent is independently discoverable. Drift on any constituent is detected and attributed to that constituent — not to the pattern as a whole. |
| **Decommission** | Pattern decommission triggers reverse-dependency-order teardown of all constituents. Consumer can also decommission individual constituents (e.g., remove the public DNS record) without tearing down the pattern. |
| **Rehydration** | Pattern rehydration rebuilds all constituents in dependency order with current policies. Binding fields resolve against newly realized values. |
| **Sovereignty** | Every constituent is independently sovereignty-checked. A pattern cannot span sovereignty zones unless every constituent passes its own sovereignty policy. |
| **Cost estimation** | Pattern cost is the sum of constituent costs. Each constituent's cost comes from its provider catalog item. |
| **Audit** | Each constituent has its own Merkle audit trail. The pattern entity has a composite audit record linking all constituent entity_uuids. |
| **Override** | A policy block on any constituent blocks the entire pattern. The consumer resolves the block for that specific constituent — modify, override, cancel, or escalate to the responsible policy domain owner. |
| **Federation** | Pattern constituents can be placed across DCM instances. The network segment might be local while the database is federated to a remote DCM with a specialized database provider. |

---

## New Use Case for Requirements Document

### UC-100: Deploy a Resource Pattern from the Pattern Catalog

A consumer browses the Pattern Catalog section of the service catalog and selects "Standard Web Application." The catalog shows the pattern's components (network, database, app servers, load balancer, DNS), the parameters the consumer needs to provide, the dependency graph, and estimated cost.

The consumer fills in 6 parameters (app_name, environment, db_engine, db_storage_gb, app_replicas, expose_public) and submits. DCM decomposes the pattern into 6 constituent resources, resolves the dependency graph, and processes each constituent through the full pipeline — layer assembly, policy evaluation, placement, dispatch — independently. Binding fields inject runtime values (IP addresses, connection strings, credentials references) from realized constituents into dependent ones.

The consumer monitors aggregate progress ("3 of 6 constituents realized") and can drill into individual constituent status. On completion, the consumer has a fully wired application environment: database with data, app servers connected to the database, load balancer distributing traffic, and DNS records resolving.

If any required constituent fails (e.g., the database provider reports an error), the pattern's lifecycle policy determines the response — rollback all realized constituents, continue in degraded mode, or notify and hold for manual intervention.

**Success criteria:** Single request produces a complete, wired application environment. Runtime values flow correctly between constituents via binding fields. Each constituent is independently managed (own entity_uuid, audit trail, drift detection, lifecycle). Decommission reverses dependency order. Sovereignty enforced per-constituent. No new control plane services, policy types, or API endpoints required — patterns use existing DCM machinery.
