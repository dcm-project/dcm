# Koku — upstream requirements for FOCUS adoption (cost provider)

The DCM Cost provider (`dcm-project/enhancements` #57/#60) must serve **vendor-neutral** cost data so any
cost backend is swappable behind the same `cost` service type. Per ADR-021 (adopt external standards by
reference) and `adopted-standards-dcm.md` (ADS-001…010), the cost data conforms to **FOCUS** (Tier-2
record standard) + **OpenCost** for Kubernetes allocation — not a bespoke, Koku-shaped vocabulary.

This doc records the **upstream changes Koku** (`project-koku/koku`) needs so the cost provider can emit
FOCUS-conformant data. GitHub issues are disabled on that repo (it tracks via the **COST** Jira); these
are written as ready-to-file tickets — one subject per ticket, each with a *Why* — for COST Jira or a
koku GitHub Discussion. Current state (June 2026): no FOCUS export exists upstream; ISO 4217 currency is
already in flight (koku PR #6097).

> **Tiering (why the work is uneven):** FOCUS/OpenCost are **Tier-2** record/schema standards → they need
> a real export + version negotiation + identity join. ISO 4217 is a **Tier-1** codelist → a referenced
> field constraint, already underway. Don't flatten them; see `adopted-standards.md` §1a.

---

## A. FOCUS data export (serializer)

**Why:** [FOCUS](https://focus.finops.org/) (FinOps Foundation, v1.4) is the vendor-neutral cost/usage
standard AWS/Azure/GCP already emit. Koku already normalizes multi-cloud + OpenShift cost into a unified
model; exposing it **as FOCUS** lets any FOCUS-aware consumer (FinOps tooling, the DCM cost provider) read
Koku cost without a Koku-specific integration.

**What:** A FOCUS-conformant export/serializer projecting Koku's unified data into FOCUS columns —
`BilledCost`/`EffectiveCost`/`ListCost`/`ContractedCost`, `BillingCurrency`, `ChargeCategory`/`ChargeClass`,
`ConsumedQuantity`/`ConsumedUnit`, `PricingQuantity`/`PricingUnit`, `ChargePeriodStart/End`,
`ServiceCategory`/`ServiceName`, `ResourceId`/`ResourceType`, and the 1.3+ allocation columns. A projection
over existing data, not new metering.

**Scope:** the export itself; version selection (B), `ResourceId` join (C), and OpenCost alignment (D) are
separate subjects.

## B. FOCUS export — version selection + advertise supported versions

**Why:** consumers need a specific FOCUS `major.minor` (allocation columns require ≥1.3), and a negotiating
platform must know which versions Koku can emit (the cost provider's `adopted_standard_support` matrix).

**What:** accept a requested FOCUS version on the export (e.g. `?focus_version=1.4`), emit that version's
shape, and advertise the supported set (e.g. 1.2–1.4) via the API/capabilities. Depends on **A**.

## C. FOCUS export — stable `ResourceId` for the identity join

**Why:** FOCUS rows must carry a stable `ResourceId` so an external system can join cost back to the
resource it manages (e.g. a cluster/VM identity). Without a stable key, cost can't be attributed to a
managed resource.

**What:** emit a stable, documented `ResourceId` in the FOCUS output (derived from existing tags/labels or
an accepted external correlation id). Depends on **A**.

## D. Align OpenShift cost allocation with OpenCost

**Why:** [OpenCost](https://opencost.io/) (CNCF) is the vendor-neutral standard for Kubernetes cost
allocation (workload/idle split, `max(request,usage)` over CPU/memory/GPU/PV/network). Aligning Koku's
OpenShift allocation to OpenCost — or documenting the precise mapping — makes Koku's container cost
portable and comparable with the ecosystem.

**What:** align (or document the mapping of) Koku's OpenShift allocation to the OpenCost spec, and expose
it in the FOCUS export's allocation columns. Related to **A**.

---

## E. (Not Koku) cost-dcm-provider — the DCM-side seam

`pgarciaq/cost-dcm-provider` (the cost SP adapter) declares `adopted_standard_support` (FOCUS/OpenCost
versions), serves FOCUS via a `serve_data` capability, and binds cost to the target by identity
(`uuid` ↔ FOCUS `ResourceId`). It can perform interim FOCUS translation if A lands slowly — but the durable,
reusable home for the FOCUS projection is **Koku itself** (A), so every Koku consumer benefits, not just DCM.
