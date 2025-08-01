# RFC: DCM API Object Design Guidelines

**Feature Name:** DCM API Object Design Guidelines

**Type:** feature

**Start Date:** 2025-08-01

**Status:** Draft

## Abstract
This document defines the conventions and principles for designing DCM API objects, both built-in and custom resources.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://datatracker.ietf.org/doc/rfc2119/).

## Motivation
DCM APIs evolve over time and must remain backward compatible while accommodating new features. A consistent design approach ensures:

* Predictability for users
* Stability of contracts across versions
* Extensibility for new use cases without breaking existing ones

## Terminology
* **Built-in Resource Definition**: A top-level DCM API object that is defined within the DCM project.
* **Custom Resource Definition**: An API object that is a user-defined extension of the DCM API.
* **Spec**: The desired state of the object.
* **Status**: The observed state of the object.
* **Metadata**: Common fields such as `name`, `namespace`, `labels`, `annotations`.

## API Object Structure
### Top-Level Structure
All DCM API objects MUST include:

* `apiVersion`: API group and version.
* `kind`: Resource kind name (PascalCase).
* `metadata`: Object metadata (name, namespace, labels, annotations).
* `spec`: Desired state (optional for read-only resources).
* `status`: Observed state (read-only, updated by controllers).

### API version
* API versions MUST follow the DCM versioning convention: `v1alpha1`, `v1beta1`, `v1`.
* Breaking changes MUST only occur between major version bumps (e.g., `v1` → `v2`).
* Alpha versions MAY introduce breaking changes; Beta and GA versions MUST preserve compatibility.
* Deprecation MUST be announced at least two releases before removal.

## Kind
* The `kind` MUST be a valid URI resolvable to the documentation of the oject itself.
* Resource names MUST be lowercase, plural, and in English.
* Field names MUST be in `camelCase`.
* Enumerated values MUST be in `PascalCase`.

### Spec vs Status
* **Spec** MUST be declarative and idempotent.
* **Status** MUST be system-populated and reflect actual runtime state.
* **Spec** changes SHALL NOT directly mutate **Status**; controllers MUST mediate changes.

## Validation and Defaulting
* All fields MUST be validated using OpenAPI v3 schema.
* Default values SHOULD be applied using defaulting mechanisms in the controller.
* Validation errors MUST be explicit and descriptive.

## Extensibility
* Optional fields SHOULD be added in a backward-compatible way.
* New capabilities SHOULD be introduced as optional fields, feature gates, or separate resources.
* Labels and annotations MAY be used for opaque, non-critical extensions. This approach SHOULD be avoided, preferring the creation of new fields within the Resource Definition itself.
* Implementations MUST NOT embed arbitrary JSON in fields; structured schema SHALL be preferred.

## Field Design Principles
* Fields MUST be consistent in naming and type across APIs.
* Boolean fields MUST be prefixed with verbs like `enable`, `allow`, `require`.
* Duration values MUST use standard time units (e.g., `30s`, `5m`).
* Lists SHALL be treated as sets, thus disregarding the order of the items.

## Abstraction Level
* API objects MUST operate at an appropriate level of abstraction for their intended audience.
* User-facing APIs SHOULD abstract implementation details and expose only necessary configuration parameters.
* Low-level APIs MAY expose more granular configuration but MUST remain portable across different environments.
* APIs MUST avoid exposing internal controller logic or cluster-specific implementation details that could break portability.
* Resource Definitions SHOULD define clear boundaries of abstraction to avoid overloading users with unnecessary complexity.

## API Evolution
* Fields MUST NOT be removed from GA APIs; they MAY be deprecated and ignored.
* Renamed fields MUST preserve compatibility via aliasing or conversion.
* Changes MUST be additive to preserve backward compatibility.

## Security and Multi-Tenancy
* Sensitive fields MUST NOT appear in plain text in `status`.
* API access MUST be controlled via RBAC.
* Multi-tenant Resource Definition MUST isolate data per tenant.
