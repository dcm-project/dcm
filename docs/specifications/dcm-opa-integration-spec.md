# DCM OPA Integration Specification

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Integration Specification


> **AEP Alignment:** DCM API endpoints referenced in this spec follow [AEP](https://aep.dev) conventions. `resource_type` accepts FQN string or Registry UUID — DCM resolves internally. See `schemas/openapi/dcm-consumer-api.yaml` and `dcm-admin-api.yaml`.


> **📋 Draft**
>
> This specification has been promoted from Work in Progress to Draft status. All questions resolved. All 7 policy types validated with working Rego examples. OPA/Rego confirmed as complete reference implementation. It is ready for implementation feedback but has not yet been formally reviewed for final release.
>
> This specification defines the OPA integration contract for DCM External Policy Evaluators. It is published to share design direction and invite feedback. Do not build production integrations against this specification until it reaches draft status.

**Version:** 0.1.0-draft
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Specification
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [Policy Profiles](../../architecture/governance-enforcement/policy-profiles.md) | [Control Plane Components](../../architecture/control-plane/components.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md)

---

## Abstract

This specification defines how Open Policy Agent (OPA) integrates with the DCM Policy Engine as the reference implementation for OPA-based policy evaluations. It defines the DCM payload schema as an OPA input document, the expected decision schema as OPA output, the built-in functions DCM provides to Rego policies, and the test harness contract for validating policies before activation.

OPA is not required to implement DCM — any OPA-based policy evaluation can implement DCM's policy contract. However, OPA with Rego is the recommended reference implementation, and this specification enables implementors and integrators to build standards-compliant DCM policy engines.

---

## 1. Introduction

### 1.1 The Policy Engine Contract

DCM's Policy Engine evaluates policies at multiple points in the request lifecycle. The engine receives a payload, evaluates all active matching policies, and accumulates mutations. The OPA integration maps this contract to Rego evaluation.

DCM policy types:
- **Validation Policy** — approve/reject (compliance-class) or contribute risk score (operational-class); output is a decision (allow/deny + reason) or risk score contribution
  - `enforcement_class`: `compliance` (boolean deny — halts request) or `operational` (contributes risk score)
  - `output_class`: `structural` (boolean pass/fail) or `advisory` (warnings without blocking)
- **Transformation** — enrich or modify; output is a set of field mutations
- **Recovery** — respond to failure/ambiguity; output is a recovery action
- **Orchestration Flow** — coordinate pipeline steps; output is a flow directive

All policy types share the same OPA input schema. The output schema differs per type.

### 1.2 OPA-based policy evaluation

A OPA-based policy evaluation executes OPA Rego bundles. DCM dispatches the policy input document to the OPA instance and receives the decision document. The OPA instance may be:
- Embedded within DCM (the reference implementation)
- A sidecar OPA instance (co-located with DCM)
- A remote OPA instance (requires network call; latency considerations apply)

---

## 2. Input Schema — DCM Payload as OPA Document

Every OPA policy evaluation receives the following input document:

```rego
# input document structure
input := {
  # The current payload being evaluated
  "payload": {
    "type": "request.initiated",         # payload type from the vocabulary
    "entity_uuid": "...",
    "resource_type": "Compute.VirtualMachine",
    "version": "2.1.0",
    "fields": {
      "cpu_count": {
        "value": 4,
        "provenance": { "origin": {...}, "modifications": [...] }
      }
      # ... all assembled fields with provenance
    }
  },

  # The requesting actor context
  "actor": {
    "uuid": "...",
    "type": "human",                     # human | service_account | system
    "tenant_uuid": "...",
    "roles": ["developer"],
    "groups": ["payments-team", "eu-west-users"],
    "mfa_verified": true,
    "auth_level": "oidc_mfa"
  },

  # The active deployment governance
  "deployment": {
    "posture": "prod",
    "compliance_domains": ["hipaa", "gdpr"],
    "recovery_posture": "notify-and-wait",
    "profile_uuid": "..."
  },

  # Entity context (null for new requests)
  "entity": {
    "uuid": "...",
    "lifecycle_state": "OPERATIONAL",
    "ownership_model": "whole_allocation",
    "owned_by_tenant_uuid": "...",
    "relationship_count": 3,
    "drift_status": "clean"
  },

  # Provider context (null before placement)
  "provider": {
    "uuid": "...",
    "sovereignty_declaration": {...},
    "trust_score": 94,
    "capacity_confidence": "high"
  },

  # DCM built-in data (resolved by DCM before OPA evaluation)
  "dcm": {
    "tenant": {
      "uuid": "...",
      "display_name": "Payments Platform",
      "active_entity_count": { "Compute.VirtualMachine": 47 },
      "compliance_overlays": ["hipaa"]
    },
    "cost_estimate": {
      "per_hour": 0.32,
      "confidence": "high"
    }
  }
}
```

---

## 3. Output Schema — OPA Decision Documents

### 3.1 Validation Policy Output (Compliance-Class)

```rego
package dcm.validation.vm_size_limits

import future.keywords

# Main decision
allow if {
  input.payload.fields.cpu_count.value <= max_cpu
}

deny contains reason if {
  input.payload.fields.cpu_count.value > max_cpu
  reason := sprintf("cpu_count %d exceeds maximum %d for tenant %s",
    [input.payload.fields.cpu_count.value, max_cpu, input.actor.tenant_uuid])
}

# DCM reads the deny set; empty = allow
max_cpu := 32
```

DCM output contract:
```json
{
  "allow": true,
  "deny": [],
  "warnings": [],
  "policy_uuid": "...",
  "evaluated_at": "..."
}
```

### 3.2 Transformation Output

```rego
package dcm.transformation.inject_monitoring

mutations contains mutation if {
  input.payload.type == "request.layers_assembled"
  not input.payload.fields.monitoring_endpoint
  mutation := {
    "field": "monitoring_endpoint",
    "value": concat(".", ["https://metrics.internal", input.deployment.posture, "example.com"]),
    "source_type": "policy",
    "operation_type": "enrichment",
    "reason": "Standard monitoring endpoint injection"
  }
}
```

DCM output contract:
```json
{
  "mutations": [
    {
      "field": "monitoring_endpoint",
      "value": "https://metrics.internal.prod.example.com",
      "source_type": "policy",
      "operation_type": "enrichment",
      "reason": "Standard monitoring endpoint injection"
    }
  ],
  "policy_uuid": "..."
}
```

### 3.3 Recovery Policy Output

```rego
package dcm.recovery.discard_on_timeout

action := "DISCARD_AND_REQUEUE" if {
  input.payload.type == "recovery.timeout_fired"
  input.entity.lifecycle_state == "TIMEOUT_PENDING"
}
```

DCM output contract:
```json
{
  "action": "DISCARD_AND_REQUEUE",
  "action_parameters": { "requeue_delay": "PT0S" },
  "policy_uuid": "..."
}
```

---

## 4. DCM Built-in Functions for Rego

DCM provides built-in functions callable from Rego policies:

```rego
# Entity relationship graph queries
dcm.entity.relationships(entity_uuid)
  # Returns: array of relationship records for the entity

dcm.entity.has_relationship(entity_uuid, relationship_type)
  # Returns: bool

dcm.entity.stakeholder_count(entity_uuid, min_stake_strength)
  # Returns: int

# Information Provider data
dcm.entity.field_confidence(entity_uuid, field_path)
  # Returns: { band, score, authority_level }

# Sovereignty checks
dcm.sovereignty.compatible(entity_uuid, provider_uuid)
  # Returns: bool

dcm.sovereignty.violates(entity_uuid, data_residency_requirement)
  # Returns: bool

# Cost queries
dcm.cost.estimate(catalog_item_uuid, fields)
  # Returns: { per_hour, currency, confidence }

# Tenant quota queries
dcm.tenant.active_count(tenant_uuid, resource_type)
  # Returns: int

dcm.tenant.has_authorization(granting_tenant_uuid, consuming_tenant_uuid, resource_type)
  # Returns: bool
```

---

## 5. Policy Bundle Structure

OPA policies for DCM are packaged as bundles:

```
dcm-policy-bundle/
├── .manifest
│   {
│     "roots": ["dcm"],
│     "metadata": {
│       "dcm_policy_type": "validation",
│       "resource_types": ["Compute.VirtualMachine"],
│       "domain": "tenant",
│       "handle": "org/policies/vm-size-limits",
│       "version": "1.0.0"
│     }
│   }
├── dcm/
│   └── validation/
│       └── vm_size_limits/
│           └── policy.rego
└── tests/
    └── vm_size_limits_test.rego
```

---

## 6. Test Harness

DCM provides a test harness that policy authors use to validate policies against sample payloads before activation:

```
POST /api/v1/admin/policies/test

{
  "policy_bundle": "<base64-encoded bundle>",
  "test_cases": [
    {
      "description": "VM within CPU limit should be allowed",
      "input": {
        "payload": { "type": "request.initiated", "fields": { "cpu_count": { "value": 4 } } },
        "actor": { "roles": ["developer"] },
        "deployment": { "posture": "prod" }
      },
      "expected_output": { "allow": true, "deny": [] }
    }
  ]
}
```

The test harness is also used during shadow mode — DCM runs the policy against real traffic and compares actual output to expected output before the policy activates.

---

## 7. Policy Shadow Mode with OPA

When a policy is in `proposed` status, DCM evaluates it in shadow mode:

1. Policy bundle loaded into a shadow OPA instance
2. Every real request payload is evaluated by both active policies AND shadow policies
3. Shadow outputs recorded in the Validation Store (not applied to requests)
4. Policy authors review shadow results via the Admin API or Flow GUI
5. On approval (no adverse results): policy status → `active`


---

## 8. Policy Model Validation — All Seven Types

This section validates that OPA/Rego can express all seven DCM policy types and both levels of the orchestration model. Each type is shown with a working Rego example and an assessment.

### 8.1 Validation Policy (Compliance-Class)

```rego
package dcm.validation.vm_size_limits

import future.keywords

allow if {
    input.payload.type == "request.layers_assembled"
    input.payload.fields.cpu_count.value <= 32
}

deny contains reason if {
    input.payload.type == "request.layers_assembled"
    input.payload.fields.cpu_count.value > 32
    reason := sprintf("cpu_count %d exceeds maximum 32",
                      [input.payload.fields.cpu_count.value])
}

field_locks contains lock if {
    input.deployment.compliance_domains[_] == "hipaa"
    lock := {"field": "fields.patient_id", "lock_type": "immutable"}
}
```
**Assessment:** Clean. Set-based deny with reasons, allow rules, field locks as set output.

### 8.2 Validation

```rego
package dcm.validation.memory_alignment

field_results contains result if {
    input.payload.fields.memory_gb.value % 2 != 0
    result := {
        "field": "fields.memory_gb",
        "result": "invalid",
        "message": "memory_gb must be a power of 2"
    }
}

result := "pass" if count(field_results) == 0
result := "fail" if count(field_results) > 0
```
**Assessment:** Clean. Set comprehension for field results.

### 8.3 Transformation

```rego
package dcm.transformation.inject_monitoring

import future.keywords

mutations contains mutation if {
    input.payload.type == "request.layers_assembled"
    not input.payload.fields.monitoring_endpoint
    mutation := {
        "field": "fields.monitoring_endpoint",
        "operation": "set",
        "value": concat(".", ["https://metrics.internal",
                               input.deployment.deployment_posture, "example.com"]),
        "reason": "Standard monitoring endpoint injection",
        "source_type": "enrichment"
    }
}
```
**Assessment:** Clean. Multiple mutations as independent set members.

### 8.4 Recovery

```rego
package dcm.recovery.timeout_response

action := "NOTIFY_AND_WAIT" if {
    input.payload.type == "recovery.timeout_fired"
    input.deployment.deployment_posture in ["prod", "fsi", "sovereign"]
}

action := "DRIFT_RECONCILE" if {
    input.payload.type == "recovery.timeout_fired"
    input.deployment.deployment_posture in ["minimal", "dev", "standard"]
}

action_parameters := {"deadline": "PT4H", "on_deadline_exceeded": "ESCALATE"}
    if action == "NOTIFY_AND_WAIT"
```
**Assessment:** Clean. Conditional action based on trigger + context.

### 8.5 Orchestration Flow (Named Workflow)

```rego
package dcm.orchestration.request_lifecycle

steps := [
    {"step": 1, "payload_type": "request.initiated",
     "policy_handle": "system/orchestration/capture-intent", "on_fail": "halt"},
    {"step": 2, "payload_type": "request.intent_captured",
     "policy_handle": "system/orchestration/assemble-layers", "on_fail": "halt"},
    {"step": 3, "payload_type": "request.layers_assembled",
     "policy_handle": "system/orchestration/run-placement", "on_fail": "halt"},
    {"step": 4, "payload_type": "request.placement_complete",
     "policy_handle": "system/orchestration/dispatch", "on_fail": "halt"}
]

ordered := true
```
**Assessment:** Clean. Step sequence as an array with `ordered: true` flag. Validation Policy and Transformation policies declared in separate packages fire on the same payload types independently — the Policy Engine coordinates both.

### 8.6 Governance Matrix Rule

```rego
package dcm.governance_matrix.phi_federation

import future.keywords

decision := "DENY" if {
    input.data.classification == "phi"
    input.target.type == "dcm_peer"
    not "hipaa" in input.target.accreditation_held
}

decision := "ALLOW_WITH_CONDITIONS" if {
    input.data.classification == "phi"
    input.target.type == "dcm_peer"
    "hipaa" in input.target.accreditation_held
    input.target.trust_posture == "verified"
}

field_permissions := {
    "mode": "allowlist",
    "paths": ["fields.resource_type", "fields.lifecycle_state"],
    "on_blocked_field": "STRIP_FIELD"
} if decision == "ALLOW_WITH_CONDITIONS"

enforcement := "hard" if decision == "DENY"
enforcement := "soft" if decision != "DENY"
```
**Assessment:** Clean. Four-axis input maps directly to OPA's input document. Decision + field permissions + enforcement as structured output.

### 8.7 Lifecycle Policy

```rego
package dcm.lifecycle.required_dependency

import future.keywords

on_related_destroy := "cascade" if {
    input.payload.type == "relationship.related_entity_destroying"
    input.relationship.stake_strength == "required"
}

on_related_destroy := "notify" if {
    input.payload.type == "relationship.related_entity_destroying"
    input.relationship.stake_strength == "preferred"
}

propagation_depth := 1
action_delay := "PT0S"
```
**Assessment:** Clean. Relationship event conditions; action output.

---

## 9. Three Things the Policy Engine Does That OPA Does Not

OPA evaluates each package independently and returns results. The Policy Engine provides three coordination functions that OPA alone cannot:

**1. Cross-policy ordered enforcement:** OPA produces the Orchestration Flow step sequence; the Policy Engine tracks which steps have fired and enforces ordering. Clean separation — OPA declares; Policy Engine enforces.

**2. Hard enforcement composition:** OPA returns `enforcement: "hard"` as output metadata; the Policy Engine ensures hard DENY wins over all soft decisions. Clean — OPA produces the flag; Policy Engine applies the composition algorithm.

**3. Domain precedence sequencing:** Multiple packages match the same payload type. The Policy Engine evaluates them in domain precedence order (system → platform → tenant → resource_type → entity) and composes results. Clean — each OPA package is stateless and independently evaluable; Policy Engine manages composition.

**Conclusion:** OPA/Rego is a complete reference implementation for all seven DCM policy types and both levels of the orchestration model. No model gaps exist.


---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*


---

## Scoring Model — OPA/Rego Patterns

### Operational Validation Policy Output Schema

```rego
package dcm.validation.operational.cost_ceiling

# Operational-class Validation Policy produces risk_score_contribution, not deny
# enforcement_class: operational is declared in policy YAML metadata

risk_score_contribution[result] {
    input.payload.cost_estimate.per_month > 500
    result := {
        "contribution": 35,
        "label": "cost_ceiling_exceeded",
        "reason": sprintf(
            "Estimated monthly cost $%v exceeds Tenant ceiling $500",
            [input.payload.cost_estimate.per_month]
        )
    }
}

# Operational Validation Policies can also produce hard deny for extreme values
deny contains reason {
    input.payload.cost_estimate.per_month > 10000
    reason := "Cost exceeds absolute maximum — manual review required before submission"
}
```

### Advisory Validation Output Schema

```rego
package dcm.validation.advisory.cost_center

# Advisory-class Validation produces completeness_contribution + warning
# output_class: advisory is declared in policy YAML metadata

completeness_warnings[warning] {
    not input.payload.fields.cost_center
    warning := {
        "contribution": 10,
        "warning_code": "recommended_field_absent",
        "warning_message": "cost_center not provided — cost attribution will use Tenant default",
        "field": "fields.cost_center"
    }
}
```

### Validation — Structural vs Advisory in Same Package

```rego
package dcm.validation.vm_fields

# Structural validation (output_class: structural)
fail contains reason {
    not input.payload.fields.cpu_count
    reason := {
        "field": "fields.cpu_count",
        "code": "required_field_absent",
        "message": "cpu_count is required"
    }
}

# Advisory validation (output_class: advisory — separate policy)
# Never mix structural and advisory in the same policy artifact
```

