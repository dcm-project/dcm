# Workload migration and rehydration — a worked example (and its limits)

**What this is.** Examples of migrating and rehydrating workloads by **replaying their stored intent**, using
UDLM and DCM — shown as **one mechanism** with a **complete** part list: not just compute and a disk, but the
**IP allocation, network connection, and DNS** a workload needs to come back to life.

Because both **replay intent** rather than translate one provider's constructs into another's, DCM can
orchestrate the rebuild end-to-end — calling capable providers to do the work, including one that migrates the
data. How much of a workload carries over is a function of its requirements.

---

## Migration and rehydration are the same process

**Three words, one act — so they stop contradicting.** *Rehydration* is the **operation**: replay stored intent
against a target. *Rebuild* is its **mechanism**: the target stands up a fresh, native realization from that
intent — never a lift-and-shift of the source construct. *Migration* is the **effect** the user sees: the
workload now runs on the new provider. So "is it a migration or a rebuild?" is a false choice — it is a
**rebuild-from-intent that produces an effective migration**, and *rehydration* is the name of the operation
that performs it. Ryan's "rebuild" and the user's "migration" are the **same act named at different layers**;
they were never in tension. And because a rebuild is driven by the intent — not the source construct — there is
no NSX→OVN conversion to fail at: NSX was never carried across, only the requirement behind it (`isolation:
private`), which OCPVirt satisfies natively with OVN.

Both paths **replay stored intent against a target and activate a DR data source to repopulate the data.** They
differ only in *circumstance*, not mechanism:

| | **Migration** | **Rehydration** |
|---|---|---|
| **Trigger** | a planned move — new provider, consolidation, exit | loss / DR event / scheduled rebuild |
| **Target** | a *different* provider — requirements or provider state changed | a *different* provider — the one that held the original is offline |
| **Intent source** | the workload's stored requirement set (its original request) | the same stored Intent/Requested/Realized record |
| **Data source** | a data-migration provider pulls from the source (MTV, `virt-v2v`) | a DR replica / backup already staged near the target |
| **Identity** | a **new** entity (the source may still exist) | a **new** realized entity, new UUID — the original is gone, so the workload is re-realized from intent. *(A faithful restore from the **Realized** record while its provider is still available can instead preserve the UUID — `RHY-005`, four-states §5.1 — a different scenario than this one.)* |
| **Sovereignty/tenancy** | evaluated for the target | **re-evaluated under *current* policy** (`RHY-001`) — may land in `PENDING_REVIEW` |
| **Ordering** | the dependency graph | the same dependency graph (`entities/service-dependencies.md`) |

**The pivot is intent.** Neither path translates a source construct into a target construct. Both ask what the
workload *needs* — `isolation: private`, an address, a name — and let each provider satisfy it natively. So the
mechanism below is written once; migration and rehydration are two entry points to it.

---

## What to expect

- **DCM orchestrates; providers do the work.** DCM plans and drives the steps a migration needs and calls a
  provider capable of each — including a provider that migrates the **data** (MTV, `virt-v2v`, backup/restore,
  replication, or a **Disaster Recovery service**). DCM coordinates the sequence end-to-end; the providers execute it, so a
  workload with the capable providers wired in migrates unattended. Where no provider automates a step, it falls
  to a human.
- **A migration rebuilds from requirements.** The workload re-realizes on the target's native services from its own
  requirements — each provider naturalizes them in its own form (DCM ADR-023), like a fresh deployment.
- **Portability follows what you expressed as requirements.** Whatever is stated portably (Base/Type intent)
  re-realizes automatically; source-specific features with no target equivalent are surfaced for a decision. A
  partial or assisted result is normal.
- **The result tracks the intent you have.** A workload realized through DCM already carries its intent, so it
  migrates or rehydrates cleanly. A brownfield resource carries only its native form, so **greening** (DCM
  ADR-017) must recover the intent first — and the result is only as good as that recovered intent.

---

## The parts of a complete re-realization

A workload is not one resource — it is a small graph. A *complete enabled solution* re-realizes every part, each
a real UDLM Resource with its own provider. All types below **exist in the registry today**
(`registry/resource-types/`).

| Part | UDLM type | Portable requirement (Base/Type intent) | Provider realizes | DR / data-migration role | Migration vs rehydration |
|---|---|---|---|---|---|
| **Compute** | `Compute.VirtualMachine` | `cpu`, `memory`, `os_image` (by standard identity, ADR-035) | a VM provider builds the guest | — (rebuilt from intent) | identical |
| **Disk / data** | `Storage.Volume` (+ DR replica) | `tier`, `min_gib` | storage provider provisions the target volume | **the data step** — a **data-migration provider** (MTV / replication / backup / a DR service) DCM calls | migration: provider pulls from source · rehydration: replica already staged |
| **IP allocation** | `Network.IPAddress` from `Network.IPAddressPool` (or `Network.DHCPScope`) | `ip_family`, `allocation: dynamic\|static` | an IPAM/DHCP provider (`Network.AddressService`) leases an address | — | migration: **new** address · rehydration: often **reserved/preserved** for the same UUID |
| **Network connection** | `Compute.VM.networks[]` → `Network.VirtualNetwork` (+ `Network.ConnectionProfile` NMstate) | **`isolation: private`, `egress: restricted`** (the private-networking intent) | network provider naturalizes: NSX portgroup **↔** OVN NAD + `NetworkPolicy` | — | reattach to the target segment |
| **Egress / gateway** | `Network.Gateway` | `egress: restricted` | gateway provider programs NAT/edge; emits `external_address` | — | re-establish egress |
| **DNS** | `Network.DNSZone` (records folded in) | the workload's `hostname` / FQDN | DNS provider writes the RR → the new `Network.IPAddress` | — | update the record to the new address |

The `Compute.VM` outputs (`ip_address`, `hostname`, `target_segment`) are the realized payloads the DNS and
network steps consume — the dependency graph passes them downstream in order.

---

## Scoped classes — portable intent vs. the provider element

Whether a given piece of data carries across comes down to **where it sits** in the scoped-Class hierarchy
(ADR-038). Each piece is a **`SharedDataElement`** — a named element with its own schema, allowed values, and
curation state — and it attaches at one of three scopes:

- **Base Class** (`Compute`, `Network`) — universal primitives; every provider honors them.
- **Type Class** (`Compute.VM`, the network connection) — the **portable requirement**:
  `isolation: private, egress: restricted` expressed as *what must hold*. The OVN provider naturalizes it to a
  `NetworkPolicy`, NSX to a security group — same intent, native realization. This is the payoff of stating the
  requirement portably instead of storing the vendor construct.
- **Provider Class** (`Compute.VM.VMware`, `Compute.VM.OCPVirt`) — the **provider-specific element**. This is the
  *private-networking Provider Class element*:

  ```yaml
  # Provider Class: Compute.VM.VMware  (provider-authored, illustrative)
  shared_data_element:
    scope:   Compute.VM.VMware          # Provider-Class scope
    element: nsx_security_group          # the provider-specific private-networking datum
    schema:  { type: string }            # an NSX security-group handle
    values:  free                        # provider vocabulary
    state:   curated

  # Provider Class: Compute.VM.OCPVirt  (provider-authored, illustrative)
  shared_data_element:
    scope:   Compute.VM.OCPVirt
    element: network_policy_ref          # the OVN-native equivalent
    schema:  { type: string }            # a NetworkPolicy / NAD reference
    values:  free
    state:   curated
  ```

> **Status.** Scoped classes are defined in **UDLM ADR-038** (accepted) but are not yet a live registry
> construct, and UDLM ships *no* concrete Provider Class — Provider Classes are **provider-authored**. So the
> elements above are the **pattern a provider authors**, and a portable `isolation` intent at the Type Class is a
> greenfield candidate under that pattern. Provider-specific data is Provider-Class `SharedDataElement`s
> (**UDLM ADR-038**; schema realization tracked udlm #199 — the `provider_extensions` carrier is retired
> and removed). Realizing these classes and the
> contribution lifecycle for org-authored ones are the DCM engine's domain (**DCM ADR-025**, scoped-class
> realization).

---

## Example A — portable migration (Base/Type only)

A VM requested at the **Type Class** with portable requirements only:

```yaml
class: Compute.VM
requirements:                                # all Base/Type SharedDataElements — portable
  cpu:     { min_cores: 8 }
  memory:  { min_gib: 32 }
  storage: [ { tier: ssd, min_gib: 500 } ]   # requirements descriptor (ADR-036)
  os_image: { family: rhel, version: "9" }   # by standard identity (ADR-035)
  network: [ { isolation: private, egress: restricted } ]   # portable private-networking intent
  dns:     { hostname: web-01 }
```

Every requirement is Base/Type-scoped, so the set carries **wholesale**. The flow — DCM orchestrating each part,
the data-migration provider included:

```mermaid
flowchart TD
    I[Stored intent + DR data source] --> P[Placement<br/>ADR-007/019 picks the target provider]
    P --> VM[Provision Compute.VirtualMachine<br/>from cpu / memory / os_image]
    VM --> IP[Allocate Network.IPAddress<br/>from Network.IPAddressPool / DHCPScope]
    IP --> NET[Attach Network.VirtualNetwork<br/>naturalize isolation: private → NetworkPolicy<br/>+ Network.ConnectionProfile NMstate]
    NET --> GW[Program Network.Gateway<br/>egress: restricted]
    VM --> DATA[[Migrate data<br/>data-migration provider MTV / replication, DCM calls]]
    IP --> DNS[Write Network.DNSZone record<br/>hostname → allocated address]
    DATA --> REC[Reconcile + health-check<br/>REALIZED → OPERATIONAL]
    GW --> REC
    DNS --> REC
```

**Parts / providers needed:** a VM provider, a storage provider + a **data-migration provider** (MTV), an
IPAM/DHCP provider (`Network.AddressService`), a network provider (naturalizes `isolation`), a gateway provider,
a DNS provider. Wire all of them and the migration runs unattended; the *requirements* carry over with no loss,
and only the data **contents** need the migration provider.

---

## Example B — provider-explicit (VMware on NSX → `Compute.VM.OCPVirt` on OVN)

The reviewer's case. The source VM carries **provider-specific** elements alongside the portable ones:

```yaml
class: Compute.VM.VMware
requirements:
  cpu:     { min_cores: 8 }                              # Base — ports
  memory:  { min_gib: 32 }                               # Base — ports
  storage: [ { tier: ssd, min_gib: 500 } ]              # Type — ports
  os_image: { family: rhel, version: "9" }              # Type — ports
  network: [ { isolation: private, egress: restricted } ]  # Type — ports as a *requirement*
  nsx_security_group: prod-web-tier                      # Provider Class element — needs a target equivalent
  distributed_switch: dvs-prod-01                        # Provider (VMware) — no OCPVirt equivalent
```

```mermaid
flowchart TD
    I[Stored intent VMware / NSX + DR data] --> P[Placement → OCPVirt / OVN]
    P --> VM[Provision Compute.VM.OCPVirt<br/>cpu / memory / os_image re-realize]
    VM --> IP[Allocate Network.IPAddress<br/>OVN IPAM]
    IP --> NET[Attach OVN network<br/>Type intent isolation: private → NetworkPolicy]
    NET --> PC{Provider Class element:<br/>nsx_security_group?}
    PC -->|intent captured at Type| MAP[Map → OVN network_policy_ref]
    PC -->|only the raw NSX name| DROP[Surface as non-portable remainder]
    VM --> DATA[[Migrate data<br/>provider MTV, DCM orchestrates]]
    IP --> DNS[Update Network.DNSZone record]
    NET --> DS[distributed_switch → no OCPVirt equivalent<br/>dropped, flagged non-portable]
    MAP --> REC[Reconcile → OPERATIONAL]
    DROP --> REC
    DATA --> REC
    DNS --> REC
    DS --> REC
```

1. **The portable subset re-realizes automatically** — cpu / memory / storage / os_image / the *network
   requirement* (`isolation: private`) all have OCPVirt/OVN native realizations. The network requirement ports
   because it was stated at the **Type Class** as *what must hold* — OVN naturalizes it to a `NetworkPolicy`,
   exactly as NSX naturalized it to a security group.
2. **The Provider Class element is surfaced** — `nsx_security_group` maps to the OVN equivalent
   (`network_policy_ref`) *only if* the intent behind it was captured as the Type-class requirement above; the raw
   NSX group name does **not** cross. `distributed_switch` has no OCPVirt equivalent and is dropped, **flagged
   non-portable** — a human decides whether it mattered.
3. **A data-migration provider migrates the data — DCM orchestrating it.** MTV performs the
   VMware→OCPVirt data migration as a provider DCM calls; DCM sequences it with the rest and
   re-realizes the spec around it. Wired that way, the data step runs *inside* the automated flow, not a pause.

The difference between A and B is **not** the mechanism; it's how much of the requirement set was expressed
portably (Base/Type) vs locked to a Provider Class. The model doesn't make NSX portable — it makes the *portion
you expressed as requirements* portable, and tells you honestly what's left.

---

## Rehydration — the same flow, a different trigger

Rehydration reuses **Example A's flow verbatim**, with these deltas that fall straight out of the table above:

- **A new resource on a new provider** — the scenario here is that the provider holding the original is
  **offline**, so there is nothing to restore in place: the workload is **re-realized from its stored intent** as
  a **new entity with a new UUID**, placed on a currently-available provider. Lineage is preserved — the new
  Intent records the source it was rehydrated from (`source_store` / `source_record_uuid`, a `rehydration`
  provenance source, four-states §5.2) — and relationships that pointed at the lost entity re-point to the
  replacement. *(The other case — a faithful restore from the **Realized** record while its provider is still
  available — preserves the same UUID per `RHY-005`; that is a different scenario than this one.)*
- **The DR data is already staged** — the data-migration step is a **replica/backup activation** (often a
  **Disaster Recovery service**) near the target rather than a cross-provider pull, so it is typically faster and
  lower-loss than a migration's.
- **Sovereignty/tenancy re-evaluated under *current* policy** (`RHY-001`) — a rehydration into today's estate may
  hit a residency/tenancy rule that did not exist at original realization, so the entity can land in
  `PENDING_REVIEW` before it proceeds. Migration evaluates target policy the same way; only the *timing* (an
  outage, not a plan) differs.

Everything else — placement, IP allocation, private-network attach, gateway, DNS, reconcile — is the identical
dependency-ordered sequence — **one enabled solution serves both.**

---

## What DCM orchestrates vs. what needs a human

- **Data migration** — done by a **capable provider** (wrapping MTV, `virt-v2v`, backup/restore, replication, or
  a **Disaster Recovery service**) that DCM orchestrates — not DCM's own bytes, and not a human step. The whole flow runs unattended
  where such a provider and its automation exist; only where none does it fall to a human.
- **The non-portable remainder** — provider-specific features with no target equivalent (`distributed_switch`);
  surfaced, not silently dropped.
- **Brownfield intent recovery** — a resource discovered in the field carries the native construct, not the
  intent behind it; greening (ADR-017) reverse-derives the requirement, imperfectly.
- **Advanced rebuilds** — where even the requirements need reshaping; the original request (or recovered intent)
  is still the starting point, not a blank page.

---

## References
- UDLM **ADR-038** — the scoped-Class model (Base/Type/Provider Class + `SharedDataElement`) + migration;
  supersedes the retired ADR-PROV-004 `provider_extensions` mechanism (removed per udlm #202).
- UDLM **`four-states.md` §5** — rehydration: replay the stored record through the dependency graph, preserve the
  UUID (`RHY-005`), re-evaluate sovereignty under current policy (`RHY-001`).
- UDLM **`entities/service-dependencies.md`** — the dependency graph that supplies the rebuild order for both
  paths.
- UDLM network types — `Network.IPAddress`, `Network.IPAddressPool`, `Network.DHCPScope`, `Network.DNSZone`,
  `Network.VirtualNetwork`, `Network.ConnectionProfile`, `Network.Gateway`, `Network.AddressService`.
- DCM **ADR-020** (migration & operational gating), **ADR-023** (provider naturalization boundary),
  **ADR-007/019** (placement), **ADR-017** (greening / brownfield discovery), **ADR-025** (scoped-class
  realization + the contribution lifecycle for org-authored classes).
- **MTV** — the third-party data mover a data-migration provider wraps.
