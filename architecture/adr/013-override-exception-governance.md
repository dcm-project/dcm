# ADR-013: How to Handle Legitimate Exceptions Without Undermining Governance

**Status:** Accepted  
**Date:** April 2026  
**Docs:** Doc B §18 (Override Model)

## Context

Policies will block legitimate requests. A data residency policy may block a valid exception for a disaster recovery scenario. A sizing policy may block a temporary capacity burst for a product launch. If the only options are "change the policy" or "work around the system," governance degrades.

## Decision

Five override mechanisms, layered from least to most disruptive:

1. **Override Policy** — A planned exception registered in advance (e.g., "DR events may use US-EAST zone")
2. **Exception Grant** — A pre-authorized waiver with compensating controls and expiry
3. **Manual Override** — Immediate single-request authorization with written justification
4. **Compensating Control** — Replace a blocked requirement with an equivalent risk-reduction measure
5. **Dual-Approval** — Required modifier for hard-enforcement policies (two approvers, different roles)

**The consumer experience:** When a policy blocks a request, the consumer sees the blocking reason, compliant value suggestions, and four options: modify the request, request an override, cancel, or escalate. Override is one path among four — not the default.

## Consequences

- Every override is audited with full Merkle tree leaf
- Frequently-overridden policies are surfaced in metrics for policy review
- Block timeout auto-cancels requests where the consumer takes no action
- The governance model is flexible without being permissive
