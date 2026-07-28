---
Document Status: 📋 Draft — Specification in Progress
Document Type: Capability Specification
Maps to: udlm/lifecycle/ingestion-model.md
---

# DCM — Workload Analysis

> **Implements contracts defined in UDLM**:
> [udlm/lifecycle/ingestion-model.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/ingestion-model.md).
> UDLM defines the ingestion model — how discovered resources enter the data
> model and are classified through the ingestion lifecycle. DCM operationalizes
> Workload Analysis as the active classification stage of that lifecycle:
> results are delivered as Information Provider payloads and stored as
> `process_resource_entity` instances of type `Analysis.WorkloadProfile`.

**Document Status:** 📋 Draft — Specification in Progress
**Document Type:** Capability Specification
**Related Documents:** [Ingestion Model](https://github.com/croadfeldt/udlm/blob/main/lifecycle/ingestion-model.md) | [Information Providers](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers.md) | [Resource Type Hierarchy](https://github.com/croadfeldt/udlm/blob/main/entities/resource-type-hierarchy.md) | [Discovery and Drift](../control-plane/components.md) | [Kubernetes Compatibility](../../docs/specifications/kubernetes-compatibility.md)

> **AEP Alignment:** API endpoints follow [AEP](https://aep.dev) conventions.
> Workload analysis results are delivered as Information Provider payloads
> and stored as `process_resource_entity` instances of type `Analysis.WorkloadProfile`.

---

## 1. Purpose

Workload Analysis is the DCM capability that actively classifies discovered resources
by their operational characteristics — what they are, how they behave, what lifecycle
model should apply to them, and which DCM Resource Type they best map to.

It answers questions that passive discovery cannot:
- *"This VM was discovered — is it a web server, a database, a batch processor?"*
- *"This workload can be migrated to containers — what is its archetype?"*
- *"This resource has no DCM UUID — what is the minimum viable Resource Type we can
   assign it for lifecycle management?"*

Workload Analysis is the bridge between **Discovered State** (what exists) and
**Intent State** (what should be managed). Without it, brownfield ingestion stalls
at the enrichment phase because the Tenant, Resource Type, and lifecycle ownership
cannot be automatically determined.

---

## 2. Relationship to Existing Capabilities

```
Discovery (DRC)          Workload Analysis       Ingestion ([ingestion-model.md](https://github.com/croadfeldt/udlm/blob/main/lifecycle/ingestion-model.md))
      │                        │                        │
      ▼                        ▼                        ▼
Discovered State     WorkloadProfile entity    INGESTED → ENRICHING
(what physically      (what it IS and what      → PROMOTED → OPERATIONAL
  exists today)        lifecycle applies)
```

**Workload Analysis is a DCM-managed process resource** (`Analysis.WorkloadProfile`)
that fires as part of the brownfield ingestion pipeline. It is triggered by the
Discovery Scheduler when a new resource enters Discovered State without a matching
DCM entity in Realized State.

It can also be triggered manually by a platform admin to re-classify a resource
whose operational profile has changed (e.g., a VM that was a web server and is
now a database).

---

## 3. WorkloadProfile Entity

Workload Analysis produces a `process_resource_entity` of type `Analysis.WorkloadProfile`:

```yaml
workload_profile_entity:
  entity_uuid: <uuid>
  entity_type: process_resource
  resource_type: Analysis.WorkloadProfile
  lifecycle_state: OPERATIONAL       # while active; DECOMMISSIONED when superseded
  
  # Linked to the resource being analyzed
  subject_entity_uuid: <uuid>        # the VM, container, or other resource
  subject_discovered_state_uuid: <uuid>
  
  classification:
    resource_type_match:             # best-fit DCM Resource Type
      primary:    Compute.VirtualMachine
      confidence: high               # high | medium | low | undetermined
      alternatives:
        - resource_type: Platform.Container
          confidence: medium
          rationale: "Workload is containerizable per MTA assessment"
    
    workload_archetype:              # operational classification
      type: web_server | database | batch_processor | message_broker |
            api_gateway | cache | storage | monitoring | unknown
      confidence: high
      signals: [port_scan, process_list, resource_utilization_pattern]
    
    migration_readiness:             # if MTA integration is active
      containerization_score: 7     # 1-10
      blockers: []
      suggested_target: Platform.KubernetesDeployment
      mta_report_ref: <url>          # link to MTA HTML report if available
    
    lifecycle_recommendation:
      dcm_lifecycle_model: standard | stateful | ephemeral | infrastructure
      rehydration_eligible: true
      notes: "Application data on /data partition; OS on /; static replace eligible"
    
  analysis_metadata:
    analyzed_at: <ISO 8601>
    analysis_version: "1.0.0"        # versioned analysis ruleset
    information_providers_used:
      - provider_uuid: <uuid>
        provider_type: information_provider
        data_types_used: [port_scan, process_list, os_metadata]
    analyst_actor_uuid: <uuid>       # null if automated; actor UUID if manual review
```

---

## 4. Analysis Pipeline

Workload Analysis is an Orchestration Flow Policy that fires when a discovered
resource enters the enrichment phase:

```
discovery.new_entity_found
  │
  ▼ Orchestration Step 1: Create WorkloadProfile entity (INGESTED state)
  │   Linked to discovered resource via 'operational' relationship
  │
  ▼ Orchestration Step 2: Gather signals from Information Providers
  │   Port scan (network topology)
  │   Process list (running services)
  │   OS metadata (version, packages, mount points)
  │   Resource utilization patterns (CPU/memory/disk I/O profile)
  │   MTA assessment (if MTA Information Provider registered)
  │
  ▼ Orchestration Step 3: Apply classification ruleset (Policy Engine)
  │   Transformation Policy: compute workload_archetype from signals
  │   Transformation Policy: compute resource_type_match from archetype
  │   Transformation Policy: compute migration_readiness from MTA signals
  │   Validation Policy (compliance): flag if confidence < medium for manual review
  │
  ▼ Orchestration Step 4: Write WorkloadProfile to Realized State
  │   WorkloadProfile entity → OPERATIONAL
  │
  ▼ Orchestration Step 5: Trigger ingestion enrichment
      WorkloadProfile classification informs:
        - Tenant auto-assignment (if auto-assignment rules match)
        - Resource Type assignment for the ingestion record
        - Lifecycle model selection
```

---

## 5. MTA (Migration Toolkit for Applications) Integration

When the MTA Information Provider is registered, Workload Analysis invokes it
as part of Step 2 above. MTA provides workload archetype classification and
containerization readiness scores for discovered workloads.

```yaml
mta_information_provider_registration:
  provider_type: information_provider
  information_type: workload_analysis
  display_name: "MTA — Migration Toolkit for Applications"
  endpoint: https://mta.internal:8080/api/v1
  
  capabilities:
    workload_archetypes:
      - web_server
      - database
      - batch_processor
      - message_broker
    provides_containerization_score: true
    provides_migration_blockers: true
    provides_target_recommendations: true
  
  query_interface:
    # MTA receives discovered state payload and returns analysis
    input: discovered_state_payload
    output: mta_workload_report
    async: true
    callback_supported: true
```

The MTA integration is the primary implementation path for Workload Analysis in
Red Hat environments. In non-MTA environments, a custom Information Provider
implementing the same `workload_analysis` information type can be registered.

---

## 6. Consumer API — Workload Analysis Endpoints

```
# Get the WorkloadProfile for a specific resource
GET /api/v1/resources/{entity_uuid}/workload-profile

Response 200:
{
  "workload_profile_uuid": "<uuid>",
  "subject_entity_uuid": "<uuid>",
  "classification": {
    "resource_type_match": {
      "primary": "Compute.VirtualMachine",
      "confidence": "high"
    },
    "workload_archetype": {
      "type": "web_server",
      "confidence": "high"
    },
    "migration_readiness": {
      "containerization_score": 7,
      "blockers": [],
      "suggested_target": "Platform.KubernetesDeployment"
    },
    "lifecycle_recommendation": {
      "dcm_lifecycle_model": "standard",
      "rehydration_eligible": true
    }
  },
  "analyzed_at": "<ISO 8601>"
}

# Trigger a re-analysis of a resource
POST /api/v1/resources/{entity_uuid}/workload-profile:analyze

Request body:
{
  "reason": "Role change — web server migrated to database role",
  "include_mta": true
}

Response 200 — returns Operation:
{
  "name": "/api/v1/operations/{request_uuid}",
  "done": false,
  "metadata": { "stage": "ANALYSIS_INITIATED", "resource_uuid": "{entity_uuid}" }
}

# List all resources with a given workload archetype (platform admin)
GET /api/v1/admin/workload-analysis?archetype=web_server&confidence=high

Response 200:
{
  "items": [ { "entity_uuid": "...", "resource_type": "...", "archetype": "..." } ],
  "next_page_token": "..."
}
```

---

## 7. System Policies

| Policy | Rule |
|--------|------|
| `WLA-001` | Workload Analysis fires automatically for every entity entering Discovered State without a matching Realized State record. It is not optional — it is part of the brownfield ingestion pipeline. |
| `WLA-002` | WorkloadProfile entities are versioned. When re-analysis produces a different classification, the old WorkloadProfile enters DECOMMISSIONED state and a new one is created. The chain is preserved for audit. |
| `WLA-003` | If classification confidence is `low` or `undetermined`, the WorkloadProfile compliance validation policy fires and the entity is routed to manual review before ingestion can proceed to PROMOTED. |
| `WLA-004` | The MTA Information Provider is the reference implementation for workload_analysis information type in Red Hat environments. Custom implementations must provide the same output schema. |
| `WLA-005` | Workload Analysis results are stored in Realized State as `process_resource_entity` instances. They are immutable once written — re-analysis creates a new entity, not an update. |
| `WLA-006` | Migration readiness scores and archetype classifications are advisory — they inform human decision-making and Orchestration Flow Policies but do not automatically trigger migrations. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
