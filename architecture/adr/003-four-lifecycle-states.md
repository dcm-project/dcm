# ADR-003: Four Lifecycle States

**Status:** Accepted  
**Date:** March 2026  
**Docs:** Doc 02 (Four States)

## Context

A resource entity goes through multiple stages: the consumer declares intent, the system processes and approves, the provider provisions, and discovery observes what actually exists. If we track this as a single mutable record, we lose the ability to answer: "What did they ask for? What did we approve? What got built? What exists now?"

These four questions are the foundation of governance, audit, compliance, and drift detection.

## Decision

Every resource entity flows through four immutable states:

1. **Intent** — What the consumer asked for (raw declaration, no processing)
2. **Requested** — What was approved after layer assembly and policy evaluation (write-once)
3. **Realized** — What the provider actually created (snapshot from provider callback)
4. **Discovered** — What exists right now (independent observation via polling)

The `entity_uuid` links all four states for the same resource. States are immutable — updates create new records. Drift is the delta between Realized and Discovered. Compliance is provable because Requested State records the policy-approved payload.

## Consequences

- Every resource has exactly 4 records linked by entity_uuid
- Drift detection is a comparison: Realized ≠ Discovered
- Rehydration (disaster recovery) re-enters at Intent with current policies
- Audit can trace any resource from consumer's original ask through to what's running
