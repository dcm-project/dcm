# ADR-017: Brownfield Greening — Ingesting Existing Resources via the Discovered Store

**Status:** Accepted
**Date:** June 2026
**Docs:** ADR-003 (Four Lifecycle States), ADR-005 (Provider Abstraction), ADR-007 (Placement Engine); UDLM `foundations/four-states.md`, `foundations/ownership-sharing-allocation.md`
**Tracking:** #221 (this design) → #222–#227 (build steps)

## Context

DCM's normal flow runs **forward**: Intent → Requested → Realized → Discovered (ADR-003). But real estates are **brownfield** — resources already exist before DCM ever models them (the homelab is the motivating case). DCM needs a defined process to bring existing resources **into** the managed model, working **backward** from observation. We call this **greening the brownfield**.

The anchoring distinction is *who controls the record*:

- **Discovered** = observed to exist, **no provider attached** → **unclaimed**.
- **Realized** = a provider has asserted "I control this" → **claimed**, attributed, managed.

Ingestion is the process of moving a resource across that line. This is not a novel invention — it is the well-established brownfield **import/adoption** pattern (Terraform `import`, Crossplane observe/import, Cluster API / ACK / Config-Connector "acquisition") mapped onto UDLM's four states.

## Decision

Define a **discovered-resource ingestion pipeline**:

1. **Discovery** populates the **Discovered store** by one of two avenues:
   - **Provider-generated** (ADR-005 Level-2 discovery): a registered provider enumerates the resources it controls and emits Discovered records **with provider attribution** — effectively pre-claimed.
   - **Third-party-generated**: a non-provider observer (probes, scanners, CMDB, import tools — e.g. the homelab's `virsh`/`oc`/`ceph`/ansible probes) emits Discovered records with **no provider attribution** — **unclaimed**.
2. The **Discovered store** holds both, durably and queryably (see Decision A).
3. **Reverse placement** (the inverse of the ADR-007 placement engine): given an unclaimed discovered resource, identify the provider(s) that own or can claim it — by `resourceType` + attributes + provider capability / adopted-standard matrices.
4. **Provider claim / adoption**: the identified provider asserts control → the record moves **Discovered → Realized**, preserving the entity UUID (UDLM §28 adopt-then-append).
5. **Intent backport / synthesis** (optional): derive Intent from the Realized/Discovered state so the resource becomes rebuildable (see Decision B).

```
existing resource
  ├─ provider-generated discovery ─┐  (attributed)
  └─ third-party discovery ────────┤  (unclaimed)
                                    ▼
                            DISCOVERED store
                                    │  (unclaimed only)
                            reverse placement → owning provider
                                    │
                            provider claim/adoption
                                    ▼
                              REALIZED  ──(optional backport)──►  INTENT
```

### Decision A — the Discovered store has a dual role (clarified, not a new store)

UDLM today frames Discovered as *ephemeral* (per-cycle snapshots for drift detection). We **clarify** it as having two roles: (1) the ephemeral snapshot stream (drift), **and** (2) a **durable, per-UUID entity inventory** that is the **source of truth for what exists — including discovered-but-unclaimed resources**. We do **not** introduce a separate "inventory" store. This is consistent with UDLM §28 raw/unallocated resources (which already live durably in Discovered with `lifecycleState: available`). *Requires a `foundations/four-states.md` clarification — tracked #222.*

### Decision B — Intent may be generated from Discovered, independent of Realized

Backporting Intent is **permitted and valued**: from Realized (the normal case) **and** directly from Discovered to produce a **provider-agnostic, rehydratable desired state** for DR/portability (rebuild the estate onto different hardware/providers). This is a legitimate state — Intent-declared-but-not-yet-built already exists in the forward flow. Such inferred Intent is marked **`provenance: discovered-derived`** (not human-declared) so consumers trust it appropriately.

### Decision C — discovered records carry correlation identifiers; ingestion resolves to one entity

The two avenues can observe the **same** real-world resource (a 3rd-party probe sees it, and later a provider enumerates it). To avoid double-counting, every discovered record carries **correlation identifiers** — stable natural keys independent of the observer:

- hosts: SMBIOS/system UUID, chassis/system serial, BMC id;
- VMs: hypervisor domain/instance UUID;
- NICs: MAC; disks: WWN / serial; storage clusters: cluster FSID;
- and, when provider-generated, the **provider's own resource ID**.

Ingestion runs **entity resolution**: a new observation is matched against existing entities by these keys (strongest/globally-unique keys first); a match **merges into the existing entity UUID** (the UDLM universal linking key, four-states §3) instead of minting a new one. So when a provider later enumerates a resource a 3rd-party probe already discovered, it **correlates to the same entity and claims it** (Discovered-unclaimed → Realized) rather than creating a duplicate. This is what minimizes 3rd-party-discovered items that are subsequently also injected by a DCM provider.

This builds on the §27 component `Identity` block (serial/wwn/mac/location) but applies at the **top-level resource**, so the discovered/realized record likely needs a dedicated `correlationIds` / `identifiers` field — *tracked as a follow-up*.

## Options considered

- **In-between store for "described but unclaimed".** (a) Reuse **Discovered** ✅ — it is already defined as observed ground truth that may contain unprovisioned/brownfield resources. (b) A new dedicated inventory store — rejected: duplicates Discovered's purpose and the four-state model.
- **Discovered durability.** (a) Clarify dual-role ✅. (b) Keep ephemeral-only and force unclaimed resources into Realized — rejected: Realized requires provider attribution, which unclaimed resources lack.
- **Intent from Discovered.** (a) Allow, provider-agnostic, flagged inferred ✅ — unlocks DR/portability. (b) Forbid; require Realized first — rejected: blocks rehydration of brownfield that no provider has claimed yet.

## Consequences

- The **homelab is the first application** and is entirely **Avenue 2** (no providers yet): its estate store (#219) is a Discovered store of **unclaimed** resources.
- As providers arrive (Kea #208, Ceph #218, a libvirt provider), they **reverse-place and claim** those resources into Realized; Intent backport then makes the estate rebuildable for DR — DCM-at-home dogfooding DCM.
- **Reverse placement** is a new engine alongside the forward placement engine (ADR-007).
- Requires the UDLM `four-states.md` clarification in Decision A (#222).
- The dependency graph stays **emergent** from per-resource Discovered records (#219), never a hand-authored file.

## Best practices

These govern every discovered-ingestion flow:

1. **Minimize unclaimed resources — they are an anti-pattern.** A resource stuck in `Discovered`/unclaimed has **no owning provider**, so it gets no lifecycle management, no authoritative drift reconciliation, and cannot be rehydrated for DR. Lingering unclaimed resources are a tracked **gap**: surface the unclaimed count, alert on it, and drive it toward zero — every discovered resource should converge to **claimed** (a provider owns it) or be explicitly **retired/excluded**. Recorded as a UDLM **Antipattern** (`entities/knowledge-family.md` §4.4): *"long-lived unclaimed discovered resource → claim it (reverse-place + adopt) or retire it."*
2. **Prefer provider-generated discovery (Avenue 1) over third-party (Avenue 2).** Provider discovery arrives already attributed (effectively claimed), skipping the unclaimed limbo and most correlation work. Third-party is the bootstrap/interim — migrate sources onto real providers as they come online (how the homelab graduates from probes to the Kea/Ceph/libvirt providers).
3. **Every discovery source MUST emit correlation identifiers** (Decision C). No identifiers → no reliable entity resolution → duplicates.
4. **One real resource, one entity UUID.** On a correlation match, merge into the existing entity; never mint a second.
5. **Reconcile, don't overwrite.** A discovered value that contradicts Realized is **drift** — surfaced (OBS-001), never silently merged.
6. **Backport Intent for anything that must survive DR.** Claimed-but-no-Intent can't be rebuilt; synthesize provider-agnostic Intent (`provenance: discovered-derived`).
7. **Unclaimed = inventoried, not managed.** Unclaimed resources are queryable for inventory but excluded from lifecycle operations until claimed — they describe reality, they don't yet control it.
