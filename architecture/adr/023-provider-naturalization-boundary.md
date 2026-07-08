# ADR-023: Provider Naturalization Boundary (naturalize / denaturalize)

**Status:** Proposed
**Date:** 2026-07-11
**Type:** Architecture Decision Record (a `DecisionRecord` with architecture scope)
**Related:** ADR-002 (Data·Policy·Provider triad), ADR-005 (Provider Abstraction), ADR-019 (Placement & Policy), ADR-021 (Adopting External Standards by Reference); UDLM ADR-004 (Provider capability declaration), UDLM ADR-008 (the UDLM/DCM boundary). **Prior art:** Open Service Broker API; DDD *anti-corruption layer*; Crossplane Claim→Composition.

## Context

UDLM is a **generic** substrate: typed records, four states, intent + data. A provider executes a **specific** mechanism — an Ansible playbook, libvirt domain XML, a Kubernetes manifest, a KMIP call. Something has to translate between the two, in **both** directions, and the whole system's integrity depends on **where that translation lives**.

If the mechanism leaks into the substrate — e.g. a `Automation.Playbook` resource type, or a "terraform module" field — the UDLM/DCM boundary (UDLM ADR-008) breaks: a peer that realizes the same intent with a different tool can no longer read the data. So the translation must be named, owned by the provider, and kept out of the substrate. This ADR names that boundary.

## Decision

**1. Naturalization / denaturalization — the provider's anti-corruption boundary.** Every provider translates at its edge:
- **Naturalize** (inbound) — take the generic UDLM request + data and render it into the provider's **native** form (playbook vars, a domain definition, a manifest). Generic → provider-native.
- **Denaturalize** (outbound) — take the provider's native results and render them back into **generic UDLM** (realized/discovered state, outputs). Provider-native → generic.

The native form **never enters the substrate**. UDLM holds only generic intent, data, and denaturalized results; the mechanism is the provider's business.

**2. Two provider modes — do not conflate them.** A "mode" here is a **capability grouping, not a provider type** (ADR-PROV-002): *resource* mode = declaring `realize_resources` (typed, four-state, lifecycle contract); *process* mode = declaring `execute_workflows` (catalog, ephemeral). Both are capability verbs in the one vocabulary, and a single provider MAY declare both — "mode" names which capability it is exercising, never a mutually-exclusive kind.
- **Resource-mode providers** provision **and manage resources** — they publish **defined resource types** and honor **lifecycle-management contracts** (the four states: intent → requested → realized → discovered; converge; decommission — `contracts/provider-contract.md`). This is **day-0/day-1**: bring a thing into being and keep it converged. *Example: OCP/podman realizing `Compute.Container`; the libvirt provider realizing `Compute.VirtualMachine`.*
- **Process-mode providers** run **processes / automation only** — they publish a **catalog of processes** and the data each needs, execute, and report; they own **no resource** and manage no lifecycle. This is **day-2**: operate, remediate, scan, report. *Example: "run a compliance scan," "rotate now."*

Both modes naturalize/denaturalize. The difference is only the **outcome shape**: a resource provider persists a typed, four-state resource; a process provider reports an ephemeral result. **A process provider MUST NOT provision or manage resources** — anything that owns a thing is a resource provider with a typed contract.

**3. The realize loop (shared spine).** catalog → DCM **presents** → consumer **picks + supplies data** → **intent** → **policy** (ADR-002/019, re-entrant) → **request** → **placement** (UDLM ADR-004 capability match) → **naturalize** → **execute** → **denaturalize** → **report → DCM** (realized/discovered) → **report → user**.

**4. Consequence for the type system.** No provider-mechanism types in UDLM. Capabilities are **declared** (UDLM ADR-004) and offered as `CatalogItem`s; mechanisms are provider-internal. `Automation.Job` carries a chosen `CatalogItem` reference + generic supplied data only — never a playbook, module, or manifest.

**5. Ownership split — three tiers of "configuration," not two.** The line is *not* "config in the substrate vs not." It is:
- **(i) The resource's *typed, declared* config — UDLM owns it, as intent.** The resource-type schema: a VM's `vcpu`/`memory`/`disks`, a Container's `image`/`ports`, a file-share's `shares`/`workgroup`. This *is* configuration and DCM's interface manages it. A VM is **not** special — model any resource's semantic config as typed properties and it lives here. (The original error was excluding Samba's shares from this tier by leaving Samba unmodeled.)
- **(ii) The provider's *serialization / mechanism* + execution — provider owns it, naturalized (§1), never stored.** Rendering tier (i) into native form — libvirt domain XML, the `smb.conf` *file*, the IPA `[global]` block — and applying it. `smb.conf`-the-file lives here, not with the typed config.
- **(iii) Config *below/outside* the resource's typed schema — handled at the integration scale it warrants (§6).** Files inside a VM's guest OS, an app's own config in a container, opaque knobs not lifted into the type. This tier is met at whatever **scale** the provider supports: **basic text passthrough** (DCM edits it, UDLM stores it as an opaque blob, provider applies) or a **reference/redirect** to the provider's own interface — always via the resource's **managing-provider** link.
- **DCM/UDLM own the lifecycle across all three** — the record, intended state, four-state transitions, ordering, policy (the *what state, when/why*); the provider **executes** the transitions (the *how*). So a VM and Samba are consistent: typed config → UDLM (`vcpu` ≙ `shares`), serialization → provider-naturalized (XML ≙ smb.conf), deep/opaque → referenced.

**6. Scales of integration — one interface, depth set by the provider (the OpenShift route).** DCM is *always* the configuration interface (single pane of glass); how deep it goes is a **spectrum**, chosen per provider by how much interface detail the provider exposes:
- **Basic (text passthrough).** For records DCM has no native typed interface for, DCM offers a **basic text-level config edit** and **passes it to the provider**; UDLM stores it as **opaque config-as-intent** (a blob), the provider applies it. Like `oc edit` on a raw resource, or a ConfigMap holding a file. Shallow, but still one interface.
- **Full (native typed).** For providers that expose enough interface detail (rich capability declaration, ADR-004), **DCM is the full config interface and UDLM stores the *typed* config** (tier (i)), then passes it to the provider to naturalize + apply. A VM's `vcpu`, a file-share's `shares`.
- **In between / reference.** Partial typing, or a pure **reference/redirect** to the provider's own interface (embedded delegation) when neither fits.

The provider **always owns execution + the serialization** (naturalization, §1). DCM storing config here is **config-as-intent for a provider to realize**, at the fidelity the integration supports — **not** authoritative config management for its own sake, and **not** a universal store: depth is opt-in per provider, and a resource with no integration is just a record + reference. The deferred first-class-config capability (Consequences) is simply the deep end of this same scale. **Prior art:** Kubernetes' spectrum — deeply-typed native resources ↔ opaque ConfigMaps/Secrets ↔ CRDs+operators, all under one `oc`/`kubectl`; API **aggregation**; LDAP/DNS **referrals**; the Open Service Broker delegation model.

## Data · Policy · Provider (required lens)

- **Data** — UDLM carries generic intent + data + denaturalized results only; naturalized/native forms are never Data. `CatalogItem` (offerings + required-data schema) and `Automation.Job` (the generic request) are the Data touchpoints.
- **Policy** — policy evaluates the generic intent before naturalization and gates the request (tenancy, sovereignty, approval, re-entry on drift/denial). Placement policy matches request → capable provider.
- **Provider** — the provider **owns** naturalize/denaturalize and the mechanism. Resource providers additionally honor the lifecycle contract; process providers honor the catalog/execute/report contract.

## Options considered

- **(A) Mechanism types in the substrate** (a `Playbook`/`Module` type). Rejected: breaks UDLM ADR-008 — a peer with a different tool can't read the data; couples the substrate to one provider's tooling.
- **(B) Fully opaque provider (no declared capabilities).** Rejected: with nothing declared there is no catalog to present and nothing for placement to match; DCM can't broker.
- **(C) [chosen] Declared capabilities (ADR-004) + a provider-owned naturalize/denaturalize boundary.** Generic in, mechanism hidden, generic out.

## Consequences

- **+** The boundary is explicit and enforceable — reviewers can reject any substrate field that is a mechanism.
- **+** Peers interoperate at the generic layer; providers stay swappable (Ansible today, AAP/Terraform tomorrow) with no substrate change.
- **+** Clean home for day-0/1 (resource providers) vs day-2 (process providers) as both arrive.
- **−** Every provider must implement two translations; a thin provider still pays the naturalize/denaturalize cost.
- **Open** — a shared *denaturalization conformance* (how faithfully results must round-trip to generic state) may warrant its own follow-up.
- **Deferred — first-class config ownership.** DCM/UDLM deliberately do **not** absorb application configuration today: §5–6 keep the provider owning config + execution while DCM references and can redirect to it. A **future version may take config ownership as a first-class capability if demand warrants** — customers wanting DCM to be their config source of truth. The embedded/redirect interface (§6) is the on-ramp, so adopting it later is **additive, not a redesign**. Revisit when enough consumers ask for it (same "defer, add-when-demanded" discipline as the `ownership_model` deferral).
