# Flows by persona — how each role uses the system

**What this settles:** the 21 September-release use cases (DAV set 29, *FF Extended Target*), grouped by the
**persona** who drives them — a usage view of the system, one role at a time. Every entry is a **lighter**
flow that builds on [request-realization](request-realization.md); read that first. Each flow has a
**stage** (in croadfeldt/udlm — the model's telling) and a **play** (in croadfeldt/dcm — the engine's
telling); the links below resolve to the docs in *this* repo.

## platform-operator — model, register, and operate the estate
Runs the substrate: models resources and their dependency graph, registers providers, keeps ordering sound.
- [UC-01 · VM as a first-class UDLM resource](uc-01-vm-as-udlm-resource.md)
- [UC-07 · Dependency graph as first-class data](uc-07-dependency-graph-data-model.md)
- [UC-08 · Cross-provider dependency ordering](uc-08-cross-provider-dependency-ordering.md)
- [UC-09 · Dependency failure surfaced](uc-09-dependency-failure-surfaced.md)
- [UC-17 · Provider registration and capability advertisement](uc-17-provider-registration-capability.md)

## solution-architect — decompose an architecture into resources
Turns a whole architecture into ordered, dependency-aware resource requests.
- [UC-02 · Architectural pattern to composite request](uc-02-architecture-to-composite.md)

## application-team-member — request and consume resources
The everyday consumer: asks for what they need in portable terms and lets the system realize it.
- [UC-03 · Standard VM provision](uc-03-vm-standard-provision.md)
- [UC-04 · Intent to VM placement on OSAC](uc-04-vm-intent-osac-placement.md)
- [UC-06 · Persistent volume provision and attach](uc-06-persistent-volume-provision.md)
- [UC-11 · Provider-failure recovery](uc-11-provider-failure-recovery.md)
- [UC-13 · VM lifecycle reconciliation](uc-13-vm-lifecycle-reconciliation.md)

## compliance-auditor — provenance and cryptographic audit
Verifies what happened: field-level provenance and tamper-evident proofs.
- [UC-05 · VM status provenance](uc-05-vm-status-provenance.md)
- [UC-15 · Merkle-tree audit verification](uc-15-merkle-tree-audit-verification.md)
- [UC-21 · Cryptographically verifiable audit chain](uc-21-audit-chain-signed-proofs.md)

## platform-engineer — day-2: rehydration, drift, policy, profiles
Owns the running system: recovery, drift, policy overrides, and how profiles resolve.
- [UC-10 · Full rehydration from intent](uc-10-full-rehydration-from-intent.md)
- [UC-12 · Resilience posture rehydration test](uc-12-resilience-posture-rehydration.md)
- [UC-14 · Drift detection and remediation](uc-14-drift-detection-remediation.md)
- [UC-16 · Policy override approval workflow](uc-16-policy-override-approval.md)
- [UC-18 · Workload portability across providers](uc-18-workload-portability.md)
- [UC-19 · Policy resolution by profile](uc-19-policy-resolution-by-profile.md)
- [UC-20 · Profile resolution and tenant onboarding](uc-20-profile-resolution-onboarding.md)
