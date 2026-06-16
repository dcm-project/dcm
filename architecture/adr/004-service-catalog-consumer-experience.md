# ADR-004: Service Catalog and Consumer Experience

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 05 (Resource Type Hierarchy), Doc 06 (Resource/Service Entities)

## Context

Consumers need a way to discover what services are available and request them. The service catalog must abstract away infrastructure complexity — a developer requesting a VM should not need to know which hypervisor, which datacenter, or which network configuration is required.

## Decision

A four-level hierarchy separates what consumers see from what providers implement:

1. **Resource Type Category** — Broad groupings (Compute, Network, Storage, Database)
2. **Resource Type** — Specific resource kinds (Compute.VirtualMachine, Network.VLAN)
3. **Resource Type Specification** — Vendor-neutral field schemas, constraints, lifecycle rules
4. **Provider Catalog Item** — A specific provider's offering (pricing, SLAs, availability)

Consumers browse the catalog, select a catalog item, and submit a request with only the fields they care about (e.g., CPU count, memory, OS). DCM handles everything else: layer assembly, policy evaluation, provider selection, dependency resolution.

**Consumer request surface** is a JSON payload via the Consumer API:

```json
POST /api/v1/requests
{ "catalog_item_uuid": "...", "fields": { "cpu_count": 4, "memory_gb": 8, "os_family": "rhel" } }
```

## Open Question — Application Definition Language

The current consumer interface is an API call with a JSON payload. This works for single resources. For multi-resource applications (three-tier web app, data pipeline, ML training environment), the consumer needs a way to define the application as a whole. This is an open design question — see [ADR-016: Application Definition Language](016-application-definition-language.md).

## Consequences

- Resource types are vendor-neutral; provider catalog items are provider-specific
- Multiple providers can offer catalog items for the same resource type
- Consumers never choose a provider directly — placement does that
- The catalog is queryable via API; RHDH provides the frontend
