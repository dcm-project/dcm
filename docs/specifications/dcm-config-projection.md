# DCM Config Projection — the mechanism behind a resource's configuration interface

**What this settles:** *how* DCM turns a provider's declared config detail into a configuration
interface a user operates, and how it keeps a **provider-owned editor** inside DCM's governance. This
is the **mechanism**; the **obligation** it satisfies is the UDLM provider contract
(`udlm/contracts/provider-contract.md §1a.3`) — a conformant peer MAY implement this mechanism
differently and still satisfy that contract (the ADR-008 boundary: UDLM owns *what must hold*, DCM
owns *how*). ADR-016 §2 pins the corollary: the resource-type base + extension model is UDLM's; **the
editor is pure DCM.**

## 1. What UDLM hands DCM

Per the provider contract, a provider supplies **config-projection detail** — enough schema/detail for
DCM to project a configuration interface at the provider's supported scale, plus each resource's
`data_classification` and `tenant_uuid`. UDLM is the **state system-of-record** (UDLM ADR-016 §3): the
config *state* (Base/Type Class + Provider-Class elements, UDLM ADR-038) is recorded on the resource across
Requested/Realized. DCM does not invent config vocabulary — it projects what the provider declares.

## 2. Projection scale — text passthrough → typed

DCM projects along the provider's declared **scale of config integration** (DCM ADR-023 §6):

| Provider detail | DCM projects |
|---|---|
| none | a **basic text passthrough** — opaque blob in, stored + audited, no field semantics |
| partial schema | a **partially-typed** form — typed where declared, passthrough for the rest |
| full typed schema | a **fully-typed** configuration interface — per-field validation, defaults, enums |

Deeper detail ⇒ a richer interface, but the **lifecycle-ownership floor is unchanged**: DCM is the
single pane of glass and state SoR regardless of scale.

## 3. Two editing paths

**(a) DCM-projected interface (default).** The user edits through the interface DCM projects (§2). DCM
authorizes the actor, applies the change through the provider's `reserve`/`commit` lifecycle, reads the
realized state back, and writes the audit leaf — all in one governed flow.

**(b) Provider-owned editor (delegated).** A provider MAY expose its own editor and have DCM delegate
editing to it (e.g. a vendor console). This is **not** an audit bypass — DCM binds the delegated editor
into the same loop:

1. **Authorize before.** DCM resolves the actor through the **PDP** (`provider-contract.md` item 8 —
   "can actor X do action Y on resource Z"), against the resource's `tenant_uuid` and governance
   context. The enabling data (identity, roles, group membership) lives in external IdP/RBAC and is
   *referenced, not custodied* (PDP/PIP split; DCM ADR-022). An unauthorized actor never reaches the
   editor.
2. **Govern the edit.** DCM evaluates the **Governance Matrix** on the pending change (data-residency /
   sovereignty hard-gate; §tenancy). A change that would cross a jurisdiction or leave the tenant is
   gated exactly as any other boundary crossing — the config tooling operates **inside** DCM's
   governance, never around it.
3. **Read back after.** The provider reports the resulting **realized-state updates** back per resource
   (denaturalized read-back), so DCM records the new config **state** — reality, not the request.
4. **Attribute + audit.** DCM attributes the applied change to the **same validated actor** and writes
   an **audit leaf**. Provenance holds end to end.

## 4. The invariant DCM upholds

Whichever path is used, DCM guarantees the contract's invariant:

> **No config change reaches Realized without (1) an authorized in-tenant actor, (2) a governance-cleared
> edit, (3) a per-resource read-back, and (4) an audit leaf.**

Before-and-after actor validation is the mechanism: **authorize before** the edit, **attribute after**
it — so every applied change has a validated author and a recorded outcome.

## 5. Sovereignty & tenancy hold in the tooling

The config editor is not an exception surface. An actor edits **only within their tenant**; config data
carries its `data_classification`; sovereign/regulated profiles apply their floors to the edit (Merkle
audit, attested actor, in-boundary handling) exactly as to any other operation. A provider that cannot
close this loop cannot be delegated an editor — DCM projects the interface itself instead (§3a).

## Related

- **UDLM** `contracts/provider-contract.md §1a.3` — the *obligation* this implements (read-back, actor
  authorization, tenant/sovereignty bounds, the invariant).
- **UDLM** ADR-016 — resource-type role (base + extension model; UDLM is state SoR; the editor is DCM).
- **DCM** ADR-022 — trust brokering / PDP-PIP split; ADR-023 — scale-of-integration tiers.
