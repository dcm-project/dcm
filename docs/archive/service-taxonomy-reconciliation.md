> **Archived 2026-07-23 — Landed.** The decisions this proposal argued for are settled and live in `taxonomy/DCM-Taxonomy.md` (incl. Part 2 anti-vocabulary) and the ADRs (Service=act / Resource=thing; realize/Realized). Historical record of the reasoning — do not extend; on any divergence the taxonomy wins.

# Service Taxonomy Reconciliation (DCM/UDLM ↔ Engineering ↔ OSAC)

**Status:** Proposal — basis for the alignment conversation with **dcm-project engineering** (OSAC convergence is context that motivates one of the proposals, not a party whose sign-off is required). Not yet adopted.
**Date:** 2026-06-27
**Scope:** The *"Service"* family of terms — Service, Service Provider, Atomic/Composite Service, Realize/Realized, Infrastructure Platform, Region/Zone.
**Related:** `taxonomy/DCM-Taxonomy.md` (Part 2 Anti-Vocabulary), `docs/engineering/ENGINEERING-ALIGNMENT.md` (implementation gap map), `architecture/adr/002-three-abstractions.md`, `architecture/adr/003-four-lifecycle-states.md`, `architecture/adr/005-provider-abstraction.md`; dcm-project/dcm `taxonomy/` (engineering vocabulary); osac-project (`fulfillment-service`, `bare-metal-fulfillment-operator`).

> This is a **terminology** reconciliation. It is distinct from `ENGINEERING-ALIGNMENT.md`, which maps *implementations* against the architecture. Here we reconcile *words and concepts* across three taxonomies that are converging.

---

## 1. The core insight: a Service is an *act*; a Resource is a *thing*

The whole knot unties on one distinction:

- A **Resource** is a *thing* (a noun) — a VM, a cluster, a database, an IP pool.
- A **Service** is the *act of doing* (an offering, a rendering) — "X **as a service**" is the act of providing and managing X, not the X itself.

From which the load-bearing sentence follows:

> **A Resource Provider provides a resource via its service.**

The provider *renders a service* (the act of provisioning + managing); that service *yields a resource*. "Service" therefore sits at **both ends of the same contract** — the consumer *requests* a service (the offering they experience), the provider *renders* a service (the act it performs) — and the **resource flows between them**. Same concept, two viewpoints.

This is consistent with the engineering taxonomy's own wording, which already calls a Service "the **capability** supported by a catalog item" — a *capability* is an ability to *do*, not a thing. We are sharpening an instinct the team already had, not overruling it.

### Consequence: name providers by what their service *yields*

Every provider renders a service, so "Service" does not distinguish one provider from another — it is common to all of them. The discriminator is **what the service yields**:

| Provider | Its service yields | Example |
|---|---|---|
| **Resource Provider** | a **resource** (thing) | kubevirt → a VM; acm-cluster → a cluster |
| **Process Provider** | an **act / outcome** (the service *is* the deliverable; no persistent resource) | run an automation, execute a remediation |
| **Information Provider** | **data** (served, not owned) | FOCUS cost data, inventory |
| **Auth Provider** | **credentials / identity acts** | issue/rotate/revoke a credential |
| **Peer DCM** | **federated capability** | another DCM contributing registry/policy |

This is why **"Service Provider" is the wrong name** — it describes *all* of them. The fix in §2 follows directly.

---

## 2. Resource Provider (renames `service_provider`) — and the OSAC collision

**Proposal: rename the provider type `service_provider` → `resource_provider`.**

Two independent reasons:

1. **It tells the truth (§1).** The provider's declared capability is to *provide resources*; naming it for the generic act ("service") it shares with every other provider hides what it actually does. "Resource Provider" names the yield.

2. **OSAC collision.** As DCM and OSAC converge, "Service Provider" becomes genuinely overloaded — OSAC uses it for the **Cloud Service Provider / operator persona** (the org *running* the sovereign cloud), not a software adapter:
   - osac-project/enhancement-proposals: *"As a **Cloud Service Provider admin**, I want to install OSAC…"*
   - *"PublicIPPools are defined by the **service provider**; tenants manage…"*

   That is a *persona/organization*. Ours is a *pluggable component that provisions resources* (`kubevirt-service-provider`, `acm-cluster-service-provider`). Renaming ours to **Resource Provider** frees "Service Provider" for OSAC's operator sense and removes the contradiction we have been carrying ("a Service Provider does not provide services — it provisions resources").

The five provider types restated under the named-by-yield rule:

`resource_provider` (was `service_provider`) · `process_provider` · `information_provider` · `auth_provider` · `peer_dcm`

**Blast radius (why this is a proposal, not an edit):** every `*-service-provider` repo, `service-provider-manager`, the provider-contract, and the `service_provider` enum value across schemas/docs. This is a rename of *our* provider type, so it needs **dcm-project engineering** consensus. **OSAC consensus is not required** — OSAC keeps "service provider" for its operator persona; we are renaming *ours*, and doing so simply leaves their term uncontested. OSAC is the *motivation* (collision avoidance), not an approver.

### Data · Policy · Provider lens
- **Data (UDLM):** the provider declaration carries `provider_type: resource_provider`; `supported_resource_types` is the yield it advertises.
- **Policy (DCM):** placement/capability matching is unchanged — it already matches on *what a provider yields*, which this rename makes explicit.
- **Provider:** renders a service (the act) that yields resources; the rename is purely nominal at the contract level (no behavioral change).

---

## 3. Realize is the act; Realized is the state

One root word does both jobs, and that is the point — no second concept is needed:

| Form | Part of speech | Meaning |
|---|---|---|
| **realize** | verb (**the act**) | make intent *hold true in reality* |
| **Realized** | state noun (**the result**) | the state produced by that act — `Intent → Requested → Realized → Discovered` (ADR-003), linked by `entity_uuid` |

**Why *realize* is the right act verb** — it is the most **general** option, and that generality is load-bearing:

- **provision** — resource-only. You do not "provision" a process or an automation outcome.
- **fulfill** — request-only. It names servicing the *ask*, not the making-real of the *thing*.
- **realize** — making *intent* hold true in reality, true for a **resource** *and* an **act/outcome** alike. As DCM grows `process_provider` / automation-outcome providers, only *realize* stays correct.

**Resolution:** *realize* is the act; *Realized* is the state. Zero blast radius on ADR-003 + the `entity_uuid` chain — and zero new vocabulary. **We do not adopt "fulfillment" as the act.**

**On engineering's anti-`realize` entry:** the objection targets the *casual English* verb ("ah, now I realize…"), which is fair for prose. But as a defined term-of-art — the act that produces the Realized state — *realize* is exactly right and more general than the alternatives. **Proposal: narrow the anti-vocab entry to the prose sense only; keep `realize`/`Realized` as the canonical act/state pair.** ("Fulfillment" remains fine where engineering/OSAC use it as a label for the request/order *flow* — e.g. OSAC's `fulfillment-service` — but that is a flow name, not our term for the act of making intent real.)

---

## 4. Composite **Resource**, not Compound Service — and Atomic **Resource**

Two reconciliations here, one consequence of the other.

**(a) Composite, not Compound.** A *composite* is assembled from parts that **retain their identity**; a *compound* (chemistry) is elements bonded into a new substance where the parts **lose** identity. Our Composition Visibility model (`transparent`/`selective` expose constituents as their own addressable DCM entities) proves the constituents keep their identity — so **composite is the technically correct word**.

**(b) Resource, not Service — naming the *thing*, consistent with §1–2.** Under *Service = act, Resource = thing*, you **compose things, not acts**: a 3-tier app is web + app + db — a composition of **resources**, not of acts. So the composed noun is **Composite Resource**, and the indivisible leaf is **Atomic Resource**. This falls straight out of the `service_provider → Resource Provider` (name-by-yield) rule — the catalog names the *resource* yielded; the *act* of offering/rendering it is still a Service.

- **Atomic Resource** — the smallest complete, actionable, indivisible yielded thing; one catalog item tightly coupled to a single resource. *(renames engineering's "Atomic Service" — which already wanted a nickname — and resolves the nickname by naming the thing, not the act.)*
- **Composite Resource** — composed of multiple constituents (Atomic Resources / resource types) that remain individually addressable; one catalog item, one composite entity, one `entity_uuid`. *(renames "Composite Service".)*
- A **Service** (the act) yields an Atomic or Composite **Resource**; the offering/catalog item is the authored definition of that resource, consumed as a service. (The offering's own lifecycle — author/version/approve/manage — is the composite-resource management capability; see the composite-offering enhancement.)

This supersedes "Composite Service" in `composite-service-model.md` / doc 30 / ADRs — those rename Service→Resource on the *yielded-thing* noun (the act-side wording stays "service").

---

## 5. Adopted from engineering as-is (clean gap-fills, no conflict)

- **Infrastructure Platform** — the native substrate a Resource Provider wraps (bare metal, KubeVirt, a Kubernetes distribution, a storage array). UDLM/DCM left this implicit ("provider-native"); engineering names it well. **Adopt it.** It slots cleanly: `Service` (requested) → `Resource Provider` (renders the act) → **`Infrastructure Platform`** (the substrate that backs it).
- **Region / Zone** — engineering defines these as geo + availability-zone topology. They are **named kinds within UDLM `Topology`** (ADR-001: abstract `kind` ∈ {region, zone, rack, host, …}). No conflict: Region/Zone are two concrete topology kinds; UDLM generalizes the dimension so placement/sovereignty/fault-domain gating all resolve against one model. Reference engineering's Region/Zone definitions as the canonical prose for those two kinds.
- **Six-domain "layer cake"** (Value / Application / Control Plane / Resource / Data Center / Governance & FinOps) — this is an **orthogonal** framing to Data · Policy · Provider (ADR-002), not a competitor. The layer cake is a *responsibility/deployment* view (who experiences which layer); Data · Policy · Provider is an *ontological* view (what kind of thing each artifact is). Both stand; we map our components into the layer cake rather than replacing it.

---

## 6. Net: who absorbs what (a genuine two-way reconciliation)

| Decision | Absorbed by | Cost |
|---|---|---|
| **Service** accepted as the Application-domain act/offering term; anti-vocab narrowed to ban only *unqualified* "Service" | **us (croadfeldt)** | small — edit Anti-Vocabulary entry |
| **Infrastructure Platform** adopted | **us (croadfeldt)** | small — add term |
| **Service Provider → Resource Provider** (named-by-yield; OSAC collision is the motivation, not an approver) | **engineering** | large — repos, contract, enum |
| **Compound → Composite** | **engineering** | small — one vocab entry |
| **`realize` = act, `Realized` = state** kept as the canonical pair; anti-`realize` entry narrowed to the prose sense | **engineering** | small — scope anti-vocab to prose |
| **Region/Zone** kept as canonical kinds within `Topology` | **shared** | none — compose |

It is not us dictating to engineering: two of the substantive moves are ours to absorb, two are theirs, the rest compose.

---

## 7. The reconciled spine (one picture)

```
                         requests
        Consumer  ───────────────────────►  a SERVICE  (the act/offering: "X as a service")
                                                  │
                                                  │ the DCM pipeline REALIZES the intent (realize = the act)
                                                  ▼
                          ┌──────────────────────────────────────────────┐
                          │  a PROVIDER renders a service that yields …    │
                          ├───────────────┬──────────────┬───────────────┤
                          │ Resource Prov.│ Process Prov.│ Info/Auth/Peer │
                          │  → a RESOURCE │  → an ACT/    │  → data/creds/ │
                          │   (a thing)   │    OUTCOME    │   federation   │
                          └───────┬───────┴──────────────┴───────────────┘
                                  │ wraps
                                  ▼
                        an INFRASTRUCTURE PLATFORM (the native substrate)

   …which REALIZES the intent  →  the REALIZED state   (Intent → Requested → Realized → Discovered)
   Region / Zone = named kinds within Topology, resolved during placement.
```

---

## 8. Open items for the alignment conversation

1. **Resource Provider rename** — agree in principle on the named-by-yield rule + OSAC rationale, then sequence the rename (proposal: alias first, flip the canonical name second, deprecate `service_provider` last).
2. **Service at both ends** — confirm "Service = the act" is acceptable as the shared definition (consumer offering ⇄ provider rendering), with **Resource** as the yielded thing.
3. **Realize / Realized** — confirm *realize* = the act, *Realized* = the state (one canonical pair, no "fulfillment" as the act); engineering narrows its anti-`realize` entry to the casual-prose sense.
4. **Composite Resource** (not Compound Service, not "Composite Service") — confirm composing **things** → the noun is Resource; the act stays Service.
5. **Atomic Resource** — confirm; this *also resolves* engineering's "Atomic Service (need a nickname)" by naming the thing, not the act. (renames "Atomic Service".)
6. Whether these land as **UDLM DecisionRecords / DCM ADRs** once agreed (they are architecturally significant enough to warrant the WHY-record).
