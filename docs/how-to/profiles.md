# How-to: set a profile, and build your own

**Audience:** an operator standing up a DCM instance. **What this settles:** how to choose the
profile your instance runs under, and how to make your own when a built-in isn't quite right.

A **profile** is the posture your DCM instance runs under — a named set of required policies,
operational config, and mechanics that DCM guarantees are present (the *floor*). It is a composed
**set, not a level** (UDLM ADR-007). Two facts shape everything below:

- **A floor is a minimum, not a filter.** Setting a profile never *disables* a capability. A profile
  requires a floor; every capability above the floor stays available and is a config toggle away.
- **Profiles are platform-scoped.** One profile applies per DCM instance (UDLM ADR-007 §5). If you
  genuinely need two different postures, run two instances — that's the supported pattern, not
  sub-scoping one instance.

UDLM ships six built-ins as `policy_profile` records (`registry/instances/profile-*.yaml`):
`dev` (the default), **`homelab`**, `standard`, `prod`, `fsi`, `sovereign`. This guide uses
`homelab` — the single-operator on-ramp (UDLM ADR-017) — as the running example.

---

## 1. Set your platform profile

Setting a profile points your instance at one `policy_profile` record and brings its floor up before
the instance serves requests.

**1. Pick a profile.** For a self-hosted lab, `homelab`: the smallest floor that still gives you the
headline value (the estate dependency graph → ordered shutdown/startup, drift visibility,
rehydration), with drift/recovery/discovery pre-tuned *on* at low ceremony and nothing heavier
required. Inspect it:

```
udlm/profile/homelab   (registry/instances/profile-homelab.yaml)
  floor:              structural-validation, tenant-isolation, resolved-profile-evaluation,
                      append-only-log, four-state-tracking
  required_mechanics: store/requested, store/realized, store/discovered, time-sync/causal
  operational_config: drift/recovery/discovery on (low ceremony); governance advisory;
                      approval none; merkle/attestation off  ← all one toggle from production-grade
```

**2. Point your instance at it.** Set the instance's platform profile to the record's handle (or
uuid) through the admin interface (`docs/specifications/dcm-admin-api-spec.md`):

```
platform_profile: udlm/profile/homelab
```

**3. DCM brings the floor up — atomically.** Before the profile goes live, DCM verifies every
`required_mechanics` entry is provisioned and operative (the stores exist, a causal time source is
present) — the same all-or-nothing floor check used for tenant onboarding
(UDLM `docs/profile-resolution.md` §5). **The instance does not serve requests until its floor is
present**; a partial bring-up rolls back. Only `approved: true` profiles are selectable — the
built-ins ship approved.

**4. From here, it resolves for every request.** DCM records the resolved profile uuid + version on
each Requested record, alongside the policy results it drove (`profile-resolution.md` §1) — so every
decision is auditable against the posture that was in force.

**Changing profile later** is the same operation with a different record. Moving to a *higher* floor
re-runs the floor check (it must provision the new required mechanics before it goes live). Note you
can get most of the way to "more" without changing profile at all — because nothing was shut off,
raising an `operational_config` value (below) is usually all you need.

---

## 2. Build a custom profile

When a built-in is close but not exact, **fork it.** You never edit a built-in — built-ins are
immutable and reproducible, so *any* modification produces a new custom profile (UDLM ADR-007 §3;
`profile-resolution.md` §4). Forking is copy-on-write.

**Worked example — "homelab, but I want drift *remediated* and a merkle audit trail."**

**1. Fork the built-in.** Copy the record, give it a new uuid and handle, mark it custom, and record
its parent:

```yaml
uuid: <new uuid>
handle: udlm/profile/homelab-strict          # your own handle
group_class: policy_profile
name: Homelab (strict)
# ... name/description/version/status as usual ...
profile:
  is_builtin: false                          # custom
  forked_from: f9985d7f-c298-408d-a9da-6da0dd820570   # the homelab record's uuid (lineage)
  approved: false                            # not selectable until you ratify it (step 3)
  composed_from: []
  floor:                                     # inherit homelab's floor, then add what you want REQUIRED
    - policy/structural-validation
    - policy/tenant-isolation
    - policy/resolved-profile-evaluation
    - audit/append-only-log
    - lifecycle/four-state-tracking
    - policy/drift-reconciliation            # ← now floor-REQUIRED, not just config-on
  required_mechanics:
    - store/requested
    - store/realized
    - store/discovered
    - time-sync/causal
  operational_config:
    drift_reconciliation: { enabled: true, mode: reconcile }   # raise report → reconcile
    audit:               { merkle_transparency: true }         # raise the toggle
    # everything else inherited from homelab's low-ceremony defaults
```

Two ways to "add" a capability, and the difference matters:

- **Raise a config value** (`merkle_transparency: true`) — the capability is *on for this instance*,
  but still not part of the guaranteed floor. Good for "I want this, for now."
- **Add a floor entry** (`policy/drift-reconciliation`) — the capability is now *required*: the
  profile won't come up unless it's present, and a tenant can't restrict below it. Good for "this is
  non-negotiable for my estate."

You can only ever **add** at or above the floor — a custom profile may restrict further, never below
the floor it inherits (UDLM ADR-007 §2).

**2. (Optional) Compose instead of copy.** For an add-on posture (e.g. a compliance overlay you want
to reuse), set `composed_from: [<base uuid>]` and put only the *additions* in this record's floor;
DCM unions the floors at resolution (`profile-resolution.md` §3). Composition is the reuse path; a
plain fork is the "tweak one thing" path.

**3. Ratify it.** A custom profile is first-class but inert until approved — set `approved: true`
(your org's ratification step; for a homelab, that's you). Unapproved profiles never resolve.

**4. Set it** as your platform profile using §1. DCM runs the floor check against the new, higher
floor before it goes live.

---

## Quick reference

| I want to… | Do this |
|---|---|
| Turn a capability on for my instance | Raise its `operational_config` value — no new profile |
| Make a capability *required* (floor) | Fork the profile, add the floor entry, ratify, set |
| Run a genuinely different posture | Run a **second DCM instance** (profiles are platform-scoped) |
| Reuse an add-on across profiles | `composed_from` an overlay profile (floors union) |
| Change a built-in | You can't — modifying one **forks** a custom profile |

**Specs behind this:** UDLM ADR-007 (profile model), UDLM ADR-017 (the homelab profile),
`profile-resolution.md` (resolution, floor-containment, onboarding), `dcm-group.schema.json`
(the `policy_profile` record shape).
