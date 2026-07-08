# DCM Validation Corpus

The curated body of use cases that define what the DCM (Data Center
Management) architecture is contractually required to support. This
corpus is consumed by [DAV](https://github.com/croadfeldt/dav) (DCM
Architecture Validation), which runs each use case through an LLM-
driven analysis to verify the architecture supports the scenario.

## What lives here

```
dav/
├── README.md                                  (this file)
├── CHANGELOG.md                               (corpus evolution)
├── schemas/
│   └── use_case.schema.json                   (UC YAML structure)
└── use-cases/
    ├── compute/                               (VMs, bare metal, containers)
    ├── cross-domain/                          (scenarios crossing 2+ domains)
    ├── data/                                  (data services, storage)
    ├── governance/                            (policy, compliance, audit)
    └── identity/                              (authn/authz, IdP integration)
```

The DAV analysis output schema (`analysis.schema.json`) lives in the
DAV repo at `engine/src/dav/schemas/`, since it describes DAV's output
format rather than corpus content.

## Use case format

Every use case is a YAML file conforming to `schemas/use_case.schema.json`.

Filename convention: `<trailing-handle-segment>.yaml` — a use case with
handle `compute/vm-standard-provision` lives at
`use-cases/compute/vm-standard-provision.yaml`. The handle's first
segment is the domain (matching the directory); the second segment
matches the filename.

UUID convention: `uc-<hex>` generated at creation time; stable for the
life of the use case.

## How DAV consumes this

DAV's Tekton pipeline clones the DCM repo and walks `dav/use-cases/**`
loading every YAML it finds. A typical PipelineRun parameterizes:

```
--param consumer-spec-repo-url=https://github.com/croadfeldt/dcm.git
--param consumer-corpus-repo-url=https://github.com/croadfeldt/dcm.git
--param corpus-uc-subpath=dav/use-cases
```

(spec and corpus point at the same repo; the corpus subpath is the
new location.)

For full DAV usage see the DAV README.

## Contribution workflow

Use cases enter the corpus via:

1. **Direct hand authoring.** Open a PR adding a new YAML under the
   appropriate domain. CI (eventually) runs DAV's stage 2 against the
   new case and the architect spot-checks the result.
2. **Promotion from a DAV exploration run.** An architect reviews a
   generated case in DAV's Review Console and clicks "promote to
   corpus," which opens a PR against this directory with the YAML
   pre-filled.

## Review criteria for corpus admission

A use case gets merged when:

- ✅ Schema-valid against `schemas/use_case.schema.json`
- ✅ Dimensions are internally consistent (not contradictory)
- ✅ Scenario is concrete enough that DAV's analysis can engage with it
- ✅ Success criteria are testable (or at least observable in the spec)
- ✅ Tags are useful for filtering (domain, complexity, edge flags)
- ✅ Not a near-duplicate of an existing case
- ✅ Initial DAV run produces a verdict an architect agrees with

## Retirement

A use case can be retired only via a PR with explicit rationale:

- The architecture has genuinely moved past supporting it (NOT "we
  broke it and didn't fix the spec to match")
- It was superseded by a more precise or comprehensive case
- It was admitted in error (e.g., duplicates an existing case)

Retirement moves the YAML to `retired/<date>/` rather than deleting it,
preserving the historical record.

## Controlled vocabularies

Dimension values are constrained. Valid values as of schema v1.0:

- **profile**: `minimal | dev | standard | prod | fsi | sovereign`
- **lifecycle_phase**: `new_request | modification | decommission |
  drift_detection | brownfield_ingestion | rehydration_faithful |
  rehydration_provider_portable | rehydration_historical_exact |
  rehydration_historical_portable | expiry_enforcement`
- **resource_complexity**: `single_no_deps | hard_dependencies |
  composite_service | conditional_soft_deps | process_resource |
  cross_dependency_payload`
- **policy_complexity**: `system_defaults_only | single_gating |
  multi_policy_chain | conflicting_policies | orchestration_flow_static |
  dynamic_conditional_flow | cross_domain_constraint |
  human_escalation_required | governance_matrix_enforcement |
  recovery_policy`
- **provider_landscape**: `single_eligible | multiple_eligible |
  none_eligible | peer_dcm_required | process_provider | mixed`
- **governance_context**: `no_governance | standard_governance |
  audit_heavy | compliance_gated | sovereignty_enforced`
- **failure_mode**: `happy_path | provider_failure | policy_violation |
  peer_dcm_disconnect | data_inconsistency | rollback_required |
  partial_fulfillment | timeout | resource_exhaustion`

Note: `policy_complexity: cross_domain_constraint` is a vocabulary term
and intentionally retains the underscore form. Directory names use
hyphens (`cross-domain/`); the dimension value does not.

These vocabularies evolve alongside DCM itself. Additions require a
schema bump and updates to DAV's `core/consumer_profile.py`.

## License

Apache 2.0 (matches the DCM project).

## History

This corpus previously lived at `croadfeldt/dcm-self-test-corpus`. It
moved to its current location in the DCM repo following ADR-001, which
made DAV a standalone consumer-agnostic framework with DCM as its first
consumer. The old corpus repo is archived; PR history through that
move is preserved there.
