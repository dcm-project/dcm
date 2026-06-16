# ADR-012: How Organizational Data Merges with Consumer Requests

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 03 (Layering and Versioning)

## Context

When a consumer requests a VM with 4 CPUs, the provisioning system needs much more information: which datacenter, which network, what monitoring agent, what backup policy, what compliance requirements apply. This organizational data shouldn't be the consumer's responsibility — they just want a VM.

## Decision

**Data Layers** carry organizational context that gets merged into every request:

- **System layers** — Datacenter configurations, environment defaults, compliance requirements
- **Tenant layers** — Organization-specific overrides (monitoring agents, naming conventions)
- **Provider layers** — Provider-specific defaults (image mappings, flavor resolution)
- **Consumer intent** — What the consumer actually asked for

Layers merge in precedence order (system → tenant → provider → consumer). Consumer values override layer defaults. Every field in the merged payload carries **provenance** — where the value came from and what modified it.

**Layers are Data, not Logic.** Layers provide values. Policies provide decisions. A layer says "the datacenter is EU-WEST-DC1." A policy says "EU-WEST resources must use the EU-WEST monitoring endpoint." This separation means layers can be managed by infrastructure teams while policies are managed by security/governance teams.

## Consequences

- Consumers declare only what they need — organizational data is injected automatically
- Adding a new datacenter or changing a monitoring agent is a layer change, not a code change
- Provenance on every field answers "why does this VM have this backup policy?"
- Layer conflicts are resolved deterministically by precedence order
