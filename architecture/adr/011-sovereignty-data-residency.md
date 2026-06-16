# ADR-011: Why Sovereignty Is a First-Class Concept

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 14 (Profiles), Doc B §18 (Overrides), Doc 26 (Governance Matrix)

## Context

Organizations operating in regulated industries or across jurisdictions face data residency requirements: EU data must stay in EU, classified data must stay on approved infrastructure, healthcare data must meet HIPAA locality requirements. Public clouds handle this with regions. On-premises infrastructure has no equivalent enforcement mechanism.

## Decision

Sovereignty is enforced at three levels:

1. **Provider declaration** — Every provider declares its sovereignty zones and data residency scope at registration. This is not self-reported trust — it's validated against the accreditation model.

2. **Policy enforcement** — Sovereignty policies are GateKeeper policies with hard enforcement. They fire on every lifecycle operation (not just initial provisioning). A resource in EU-WEST stays in EU-WEST for its entire lifecycle, including updates, scaling, and rehydration.

3. **Placement pre-filter** — The placement engine eliminates non-compliant providers before scoring begins. Sovereignty is a hard gate, not a soft preference.

**Override governance:** Sovereignty policies can be overridden, but only through dual-approval (two approvers from different roles). Every override is audited at field granularity.

## Consequences

- Sovereignty violations are caught at request time, not after deployment
- Cross-zone data movement is impossible without explicit, audited override
- Rehydration (disaster recovery) respects current sovereignty policies — rebuilding in a non-compliant zone is blocked
- Profiles (minimal, standard, fsi, sovereign) set sovereignty enforcement minimums
