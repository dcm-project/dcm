# ADR-005: Why Providers Exist and What They Do

**Status:** Accepted  
**Date:** April 2026  
**Docs:** Doc A (Provider Contract), Doc 53 (Capability Discovery)

## Context

DCM must interact with many external systems: hypervisors, container platforms, network controllers, IPAM systems, identity services, other DCM instances, ITSM tools, FinOps platforms, and more. Each has its own API, data format, and operational model. Without a common abstraction, DCM becomes tightly coupled to specific infrastructure platforms.

## Decision

A **Provider** is any external system DCM interacts with through a defined contract. All providers share the same base contract: registration, health check, sovereignty declaration, accreditation, zero trust authentication, and provenance emission.

What varies is the **capabilities** the provider declares. Capabilities define what the provider can do — not a rigid type assignment, but a profile of operations:

| Capability | What it means | Example |
|-----------|--------------|---------|
| `realize_resources` | Provisions, updates, and decommissions infrastructure resources | OpenStack Nova, KubeVirt, ACM |
| `serve_data` | Responds to queries with authoritative external data | CMDB, DNS, IPAM (InfoBlox) |
| `authenticate` | Authenticates identities and returns tokens/roles/groups | Keycloak, LDAP, FreeIPA |
| `federate` | Another DCM instance — mTLS mandatory, dual audit | Cross-region DCM |
| `execute_workflows` | Runs ephemeral workflows without producing persistent resources | Approval chains, ITSM, runbooks |

**A provider can declare multiple capabilities.** An IPAM system that both serves IP availability data AND allocates IP addresses registers once with `capabilities: [serve_data, realize_resources]` — not twice as two separate providers.

The key mechanism is **Naturalization/Denaturalization**: DCM sends a unified payload to the provider. The provider translates (naturalizes) it into its native API format, acts on it, then translates (denaturalizes) the result back into DCM's unified format.

## Capability Discovery

DCM and providers discover each other's capabilities bidirectionally:

- **DCM advertises** its capabilities via `GET /api/v1/capabilities` — external systems query what DCM offers (cost data, audit trail, entity lifecycle events, placement decisions) and subscribe to data streams automatically
- **Providers declare** what they offer to DCM (capabilities) AND what they need from DCM (data streams, events) at registration time. DCM matches needs to available capabilities and offers subscription endpoints.

This replaces the old one-directional model where providers register with DCM but DCM doesn't advertise anything back.

## Alternatives Considered

1. **12 provider types** (original design) — rejected because credential, notification, message bus, registry, storage, meta, policy, and ITSM providers were implementation details or data concepts, not architectural abstractions
2. **5 rigid types** (interim design) — rejected because it still forced providers into exactly one type, preventing multi-capability providers and providing no discovery mechanism
3. **Unified model with capability declarations** (current) — one provider type with capability profiles, bidirectional discovery, and automatic pipeline establishment

## Consequences

- Adding a new infrastructure platform means writing one provider — not changing DCM core
- Consumers don't know or care which provider fulfills their request
- Provider selection is policy-driven (placement), not consumer-chosen
- All provider interactions are audited and sovereignty-checked
- Multi-capability providers register once, not once per capability
- External systems discover DCM's data streams without reading docs
