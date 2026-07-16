# Flows by persona — how each role uses the system

**What this settles:** the 21 September-release use cases (DAV set 29, *FF Extended Target*), grouped by the
**persona** who drives them — a usage view of the system, one role at a time. Every entry is a **lighter**
flow that builds on [request-realization](request-realization.md); read that first. Each flow has a
**stage** (in croadfeldt/udlm — the model's telling) and a **play** (in croadfeldt/dcm — the engine's
telling); the links below resolve to the docs in *this* repo.

## application-team-member — request and consume resources
The everyday consumer: asks for what they need in portable terms and lets the system realize it.
- [UC-01 · Standard VM provision](uc-01-vm-standard-provision.md)
- [UC-02 · VM intent onto OSAC](uc-02-vm-intent-osac-placement.md)
- [UC-03 · Persistent volume with attach](uc-03-persistent-volume-provision.md)
- [UC-04 · VM provision, provider fails mid-realization](uc-04-vm-provision-with-provider-failure.md)
- [UC-05 · Idempotent reconvergence](uc-05-idempotent-reconvergence.md)

## platform-operator — model, register, and operate the estate
Runs the substrate: models resources and their dependency graph, registers providers, keeps ordering sound.
- [UC-06 · VM as a first-class resource](uc-06-vm-resource-representation.md)
- [UC-07 · Dependency graph as first-class data](uc-07-udlm-dependency-graph-data-model.md)
- [UC-08 · Cross-provider ordering](uc-08-cross-provider-dependency-ordering.md)
- [UC-09 · Broken dependency, surfaced](uc-09-dependency-failure-impact.md)
- [UC-10 · Provider registration + capability](uc-10-provider-registration-capability.md)

## platform-engineer — day-2: rehydration, drift, policy, profiles
Owns the running system: recovery, drift, policy overrides, and how profiles resolve.
- [UC-11 · Policy override approval](uc-11-policy-override-approval.md)
- [UC-12 · Dynamic rehydration](uc-12-dynamic-rehydration.md)
- [UC-13 · Rehydration RTO measurement](uc-13-rehydration-rto-measurement.md)
- [UC-14 · Drift detection & remediation](uc-14-drift-detection-remediation.md)
- [UC-15 · Provider-portable rebuild](uc-15-provider-portable-rebuild.md)
- [UC-16 · Policy resolution by profile](uc-16-policy-resolution-capability.md)
- [UC-17 · Profile resolution & atomic onboarding](uc-17-profile-resolution-capability.md)

## compliance-auditor / auditor — provenance and cryptographic audit
Verifies what happened: field-level provenance and tamper-evident proofs.
- [UC-18 · Realized status with field-level provenance](uc-18-vm-status-provenance.md)
- [UC-19 · Cryptographic audit verification](uc-19-audit-merkle-tree-verification.md)
- [UC-20 · Transparency-log capability validation](uc-20-audit-chain-proofs-capability.md)

## solution-architect — decompose an architecture into resources
Turns a whole architecture into ordered, dependency-aware resource requests.
- [UC-21 · Solution architecture deployment](uc-21-solution-architecture-deployment.md)
