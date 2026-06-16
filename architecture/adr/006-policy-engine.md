# ADR-006: Why Policy-as-Code and What It Governs

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc B (Policy Contract)

## Context

Enterprise infrastructure requires governance: sizing limits, security constraints, compliance rules, sovereignty requirements, cost controls, naming conventions. Today this governance is tribal knowledge enforced by manual review gates. Manual gates are slow, inconsistent, and unauditable.

## Decision

Every request is policy-evaluated before provisioning. Policies are code artifacts (Rego), not configuration. They fire automatically when data matches conditions and produce typed outputs.

**What policies govern:**
- **Who can request what** (GateKeeper: allow/deny based on role, tenant, resource type)
- **Whether the request is valid** (Validation: field constraints, range checks, format)
- **How the request is enriched** (Transformation: inject monitoring agents, set backup policies, apply naming conventions)
- **What happens when things fail** (Recovery: retry, requeue, compensate)
- **How pipeline stages are ordered** (Orchestration Flow: dependency sequencing)
- **What crosses boundaries** (Governance Matrix: sovereignty, data classification)

**Key design choices:**
- Multi-pass evaluation with convergence — transformation policies can inject fields that other policies depend on
- Lifecycle-scoped — a CPU-sizing policy fires on provisioning and scaling, not on hostname changes
- Override model with 5 mechanisms — governance is not rigid; legitimate exceptions are handled through audited overrides

## Consequences

- No request bypasses policy evaluation — this is mandatory, not opt-in
- Policies are versioned, have lifecycle (developing → active → retired), and support shadow mode for safe testing
- Every policy evaluation produces an audit record regardless of outcome
- Policy complexity is managed through templates (Gatekeeper ConstraintTemplate pattern) and a Constraint Type Registry
