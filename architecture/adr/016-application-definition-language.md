# ADR-016: Application Definition Language

**Status:** OPEN — Design Decision Required  
**Date:** April 2026  
**Raised by:** Ondra (machacekondra), repeatedly

## Context

DCM currently has two consumer interfaces:

1. **Single resource** — A JSON payload to the Consumer API: `POST /api/v1/requests { "catalog_item_uuid": "...", "fields": {...} }`
2. **Compound service** — A composite resource type spec that defines constituent resources, dependencies, and binding fields in YAML

The single-resource API works well for atomic resources. The composite service definition (composite service model) works for platform engineers who define reusable application templates. But there is a gap:

**How does a consumer define a custom application?** Not a pre-defined catalog item, but an ad-hoc composition: "I need a database, two app servers, and a load balancer, and here's how they connect." Today, this requires a platform engineer to create a composite resource type spec first.

Comparable projects have made different choices:
- **Radius** uses Bicep (a DSL) for application definitions, with Recipes (Terraform/Bicep templates) for infrastructure implementation
- **KRO** uses ResourceGraphDefinitions with CEL expressions, generating CRDs from the definition
- **Crossplane** uses Compositions with embedded resource templates and patch sets

## The Question

What is DCM's application definition language? Options to evaluate:

### Option A: API-Only (Current State)
Consumers submit JSON payloads. Compound services require pre-defined composite resource type specs. Platform engineers author specs; consumers consume them.

**Pros:** Simple, API-first, no custom language to learn  
**Cons:** No self-service composition. Every new application pattern requires a platform engineer.

### Option B: YAML Application Manifests
A YAML document defining resources, dependencies, and binding fields — similar to the composite resource type spec but authored by consumers, not platform engineers.

```yaml
apiVersion: dcm.io/v1
kind: Application
metadata:
  name: pet-clinic
spec:
  resources:
    - name: database
      type: Database.PostgreSQL
      fields: { engine: postgresql, storage_gb: 50 }
    - name: backend
      type: Compute.VirtualMachine
      depends_on: [database]
      bindings:
        - from: database.ip_address
          to: config.db_host
      fields: { cpu_count: 4, memory_gb: 8 }
    - name: frontend
      type: Compute.VirtualMachine
      depends_on: [backend]
      bindings:
        - from: backend.ip_address
          to: config.api_host
      fields: { cpu_count: 2, memory_gb: 4, replicas: 2 }
```

**Pros:** Declarative, GitOps-friendly, reviewable, versionable  
**Cons:** New format to learn. Validation complexity. How does this interact with the service catalog?

### Option C: Reference Existing DSL (Bicep, CEL, HCL)
Adopt an existing language like Radius does with Bicep or KRO does with CEL. Leverage existing tooling and developer familiarity.

**Pros:** Existing tooling, IDE support, community  
**Cons:** Tight coupling to an external project. Bicep is Azure-originated. CEL is K8s-specific. HCL is HashiCorp-specific.

### Option D: Catalog Composition via API
Consumers compose applications by linking multiple catalog requests through the API, declaring dependencies between them. No new language — just structured API calls.

```json
POST /api/v1/applications
{
  "name": "pet-clinic",
  "components": [
    { "name": "database", "catalog_item_uuid": "pg-standard", "fields": {...} },
    { "name": "backend", "catalog_item_uuid": "vm-standard", "fields": {...},
      "depends_on": ["database"],
      "bindings": [{ "from": "database.ip_address", "to": "config.db_host" }] }
  ]
}
```

**Pros:** API-first, no DSL, consistent with existing patterns  
**Cons:** JSON is verbose for complex compositions. Not as readable/reviewable as YAML. No GitOps-friendly file format.

## Evaluation Criteria

1. **Consumer UX** — How easy is it for a developer to define a three-tier app?
2. **Platform engineer UX** — How easy is it to create reusable templates?
3. **GitOps compatibility** — Can definitions be stored in Git and applied via PR?
4. **Validation** — Can DCM validate the definition before execution?
5. **Existing tooling** — Does it work with existing editors, linters, CI pipelines?
6. **Consistency with DCM patterns** — Does it align with the API-first, JSON, snake_case conventions?

## Recommendation

This decision needs team input. The author's preliminary assessment:

**Option B (YAML manifests) or Option D (API composition) are most aligned** with DCM's existing patterns. Option B is better for GitOps. Option D is better for API-first consistency. They could coexist — the YAML manifest could be a file format that the API endpoint accepts.

**Option C (external DSL) is least aligned** — it introduces a dependency on an external project's language and tooling, which conflicts with DCM's technology-agnostic principle.

**Regardless of choice, the composite resource type spec remains the implementation mechanism.** The application definition language is a consumer-facing UX that ultimately produces a composite resource type spec (or equivalent) for execution.

## Actions Required

- [ ] Team discussion to evaluate options
- [ ] Prototype consumer UX for three-tier app with top 2 options
- [ ] Evaluate interaction with RHDH (Backstage) scaffolding templates
- [ ] Decision by [date TBD]
