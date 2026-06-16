# ADR-010: Why Tamper-Evident Audit and How It Works

**Status:** Accepted  
**Date:** April 2026  
**Docs:** Doc 16 (Universal Audit)

## Context

Regulated industries (financial services, government, healthcare) require provable audit trails. "We logged it" is insufficient — auditors need mathematical proof that records haven't been modified or deleted after the fact. This is a hard requirement for sovereign cloud deployments.

## Decision

DCM uses a **Merkle tree** audit model (RFC 9162 — the same pattern used in Certificate Transparency):

- Every pipeline stage produces a signed audit record (Ed25519 signature)
- Records are leaves in a Merkle tree — a binary hash tree where modifying any leaf changes the root hash
- **Inclusion proofs** prove a specific record exists in the tree
- **Consistency proofs** prove the tree has only grown (no deletions)
- **Signed tree heads** provide non-repudiation by the DCM instance

**Configurable granularity** because not every deployment needs the same detail:
- **Stage** (~6 leaves/request): one leaf per pipeline stage — sufficient for dev/homelab
- **Mutation** (~15-30 leaves/request): one leaf per field change — standard for production
- **Field** (mutation + per-field hashes): required for FedRAMP/sovereign deployments

## Consequences

- Any modification to audit records is mathematically detectable
- Auditors can independently verify the audit trail without trusting DCM
- Granularity is profile-governed — organizations choose their audit depth
- Three SQL tables support the model: audit_records, signed_tree_heads, merkle_tree_nodes
