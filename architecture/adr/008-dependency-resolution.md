# ADR-008: How Resources Know What They Need

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 07 (Service Dependencies), Doc 30 (Composite Service Composition Model)

## Context

Infrastructure resources have dependencies. A VM needs an IP address. A database needs a network port. A three-tier application needs all of its components provisioned in the right order with runtime values (IP addresses, connection strings) flowing from one resource to the next.

## Decision

Dependencies are declared at two levels:

**Type-level** (in the Resource Type Specification): "Every VM requires exactly one IP address." These are portable, provider-agnostic, and apply to all implementations of the resource type. DCM automatically creates sub-requests for type-level dependencies.

**Binding fields** (in composite service definitions): "The backend's db_host field gets its value from the database's realized ip_address." These connect resources via runtime values — the output of one resource becomes the input of another.

**How it works:**
1. Request Processor reads the resource type spec and identifies dependencies
2. Dependencies without parents are dispatched first (topological sort)
3. When a dependency is realized, its output values are injected into dependent resources via dependency payload passing (with full provenance tracking)
4. Dependent resources are dispatched after their dependencies are satisfied

For composite services, the composite resource type spec declares the full dependency graph with binding fields.

## Consequences

- Consumers don't manage dependencies — they request a catalog item and DCM resolves the graph
- Each dependency is a first-class DCM entity with its own audit trail and lifecycle
- Decommission reverses the dependency order — dependents are torn down before their dependencies
- Circular dependencies are detected at resource type registration time, not at request time
