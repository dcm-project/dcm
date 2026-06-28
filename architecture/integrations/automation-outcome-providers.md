# Automation as DCM services — build for the outcome, not the method

> **North star — an intent-based service model, where the outcome *is* the intent.** The goal is to get
> organizations to focus on **outcomes, not methods**: declaring the desired **outcome** *is* the
> expression of intent — there is no separate intent artifact to interpret. The catalog/system deploys
> that outcome; *how* it's achieved is the platform's concern. This maps directly onto UDLM's four
> states, which open with **Intent**: the **Intent state is the declared outcome**, and realization is
> the journey Intent → Requested → Realized → Discovered. DCM is the system that deploys outcomes. This
> document applies the north star to automation — the principle generalizes to every service in the
> catalog.

**Why:** the consumer's ask is *"I need this thing on this target"* — `Observability.LogShipper` on
`host-Z`. That is an **outcome**. The automation that makes it true (an Ansible role, an AAP job
template, a script, a container) is a *method*. DCM providers must be built for the **outcome**, and the
method must be an **encapsulated, swappable internal mechanism** — never a thing the consumer, the
Resource Type, or DCM placement sees. This note settles "do we need a generic automation spec?" — **no**
— and how the homelab's ansible roles become DCM-consumable services.

## The rule

> **Provider = outcome. Method = hidden.**

- **Consumer contract:** Resource Type + target. `LogShipper` on `host-Z`. Nothing about *how*.
- **Provider:** identified by the **outcome capability** it offers — it `realize_resources` of type
  `Observability.LogShipper` (and other outcome types). It is **not** "the Ansible provider" or "the AAP
  provider." Its name is the outcome family, not the engine.
- **Method:** inside the provider. Today: `ansible-runner` invoking the roadfeldt-ansible `alloy` role.
  Tomorrow: an AAP job template, or a container. **Swapping the method is an internal provider change
  with zero impact** on the type, the consumer, or DCM. That swap-invisibility *is* the proof the
  boundary is correct.

## Outcome-derived services — declare the goal, derive the work

The leaf outcome (`LogShipper` on a host) is the floor. The **goal** is to drive **outcome-derived
services**: a consumer declares a *higher-order outcome* — "host-Z is **observable**", "host-Z is
**production-baseline**" — and the concrete services it needs are **derived** from it, not hand-picked.

```
Outcome (goal)        "host-Z is observable"
   | derive
Derived services      Observability.LogShipper + Observability.MetricsExporter ( + … )
   | realize (provider; method hidden)
Realized on host-Z
```

This is the **Composite Service** model — a composite outcome whose **constituents are the derived
services** (the existing depends-on DAG) — and it is the answer to the open **Application Definition
Language** question (`adr/016-application-definition-language.md`): an *outcome is the application*, and
it derives its constituents.

**Where the derivation lives splits on the Data ⇄ Policy line:**
- **Fixed** outcome (observable *always* = this service set) → a **declarative composite** (data).
- **Target-conditional** outcome (a Pi derives X, a server derives Y, by host attributes) → **Policy**.

No new machinery — the same boundary, the same four-state lifecycle, now on the composite outcome (its
Discovered state aggregates its constituents' health). The single data-driven provider still realizes
each leaf; the derivation sits above it.

## Why this beats method-providers

- **Four-state lifecycle works on the outcome.** Intent (want shipping) → Requested (assembled with
  sink + labels) → Realized (shipper running) → **Discovered** (is it healthy / still shipping? → drift).
  You can reconcile *"is the LogShipper healthy,"* which you **cannot** do with *"did the playbook run."*
  A method-provider (`Process.AnsiblePlaybook`) is fire-and-forget; an outcome-provider is reconcilable.
- **Audit/provenance** attach to a durable resource, not a one-shot job.
- **Engine independence by construction:** `ansible-runner` → AAP is a backend change, not a re-model.

## No generic automation spec — the genericity lives in the provider

There is **no automation in the data model**. The only "generic" part is an *implementation* detail
inside the outcome provider: a **data-driven Type → method-binding table**.

```
Observability.LogShipper   -> ansible role 'alloy'         (var-map: spec.sink.url -> loki_url, …)
Observability.MetricsExporter -> ansible role 'node_exporter'
…                          -> …
```

Adding a new outcome is **"define a Resource Type + add a mapping row"** — *not* writing a new provider.
The method binding (which role / which AAP template realizes which type, and the spec→vars mapping) is
the provider's **private catalog config** — the vendor-specific layer. It lives in the provider, **never
in the universal type**, exactly as Koku's native metric names live in its catalog item and not in the
FOCUS type (`koku-focus-adoption.md`).

## raw ansible-runner vs AAP

Not a consumer choice and not two Resource Types — both are **execution backends of the same outcome
provider**:
- **ansible-runner** — lightweight, homelab-grade. The starting backend.
- **AAP** — enterprise execution: RBAC, credential vault, job history, and **surveys (≈ UDLM E1
  constraint profiles)**. Slots in later as the provider's backend with **zero** type/consumer change.

If that swap is truly zero-change, the abstraction held.

## Running an automation is *also* an outcome — the automation as a service

Even "just run automation X" fits the model — there is no second class. The outcome is **a service that
runs X**, not a fire-and-forget job. Its realized form is a **registered, invokable automation service**:
an **AAP job template** *is* exactly "a service to run an automation," as is a DCM-registered job or a
CronJob. That service is itself persistent and reconcilable — *does it exist? can it run? is its
definition current?* are all drift-checkable — and **each invocation is an audited run**.

So every consumer ask is an outcome → a service. The only thing that differs is **what the service
provides**:

| The service provides… | Example | Realized form |
|---|---|---|
| a running / configured **resource** | `Observability.LogShipper` | an agent running on the host |
| an **invokable automation** | a backup service, a cert-rotation service | a registered job (AAP template / CronJob) you can run |

The generic **`Process.Automation`** type models the second row — *the automation-runner service*, a peer
outcome, not an exception. (Executor-neutral: the specific playbook / AAP template it wraps is provider
catalog config, never in the type.) The four-state lifecycle applies to the **service**; running it is an
audited event against that service.

## Worked example (homelab)

`Observability.LogShipper` (`udlm/registry/resource-types/observability.log-shipper.json`) — spec:
`{ target.host, sink.url, source, labels }` — realized by an outcome provider that runs the
roadfeldt-ansible **`alloy`** role (journald → Loki). The consumer asks for a LogShipper on a host; the
provider naturalizes the spec into role vars, runs it, and reports `status` / `last_shipped_at` for drift.
The homelab's roles (`alloy`, `node_exporter`, `smartctl`, `fan_control`, …) become the first real DCM
**outcome** catalog — the live reference proving the model on actual automation.

See also: `data-policy-boundary.md`, `adr/021-adopting-external-standards.md`, and UDLM
`design-principles/adopted-standards.md`.
