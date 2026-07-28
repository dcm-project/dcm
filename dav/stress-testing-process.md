# Stress-testing UDLM & DCM with DAV — a reusable process

**What this is.** The repeatable procedure for pressure-testing the architecture (UDLM the data model, DCM
the realization) by hammering it with **use cases** run through DAV's gap-analysis engine. A UC the
architecture can't satisfy comes back `unsupported` / `partially_supported` — and *that verdict is a gap
worth a decision*. The output of a run is two things: **a ranked list of architecture gaps**, and **candidate
UDLM resource types** to close them.

**Why it works.** DAV's whole value is *"propose use cases the architect didn't think of."* Hand-authored
UCs test what you already have in mind; a few hundred **edge cases** — simple and complex, across the
capabilities enterprises actually demand — find the corners the spec quietly doesn't cover. The engine turns
"is this supported?" from an argument into a fingerprinted verdict.

## The exemplar

Your **canonical hand-authored UC set** — the reference set your architects curated — is the quality and style
bar: scenario depth, the Data·Policy·Provider decomposition, dimension coverage, concrete capability. **Every
generated UC is modeled on its shape.** Read a handful before generating so the corpus stays coherent, not a
pile of shallow one-liners.

## The process

1. **Baseline — run the canonical sets.** Run your **canonical reference set** plus every scoping set tagged
   **`hammer`** through the gap engine. Capture the verdict distribution (`supported` /
   `partially_supported` / `unsupported`) and the gap factors. This is the "where do we stand today" snapshot
   and the regression baseline for future runs.

2. **Generate — hundreds of edge cases.** Fan out UC generation (parallel agents, or the console's UC-gen)
   modeled on the exemplar: **simple AND complex**, covering the enterprise-capability surface (multi-tenant
   isolation, sovereignty/residency, DR/rehydration, credential lifecycle, cost/chargeback, capacity &
   quota, audit/compliance, federation, brownfield ingestion, decommission safety, day-2 drift, …). Volume is
   the point — hundreds, not dozens. Organize into **scoping sets by capability/theme**.
   - **Tag every generated UC with `generated_by` provenance** (`mode`, `source`, `model`, `prompt_version`).
     This preserves an independent ground-truth signal: at any time you can slice "what does the framework
     say about the UCs the *architect* wrote?" separately from verdicts on generated ones. Guards against
     self-referential validation.

3. **Analyze — run them through the engine.** Same gap-analysis pass. Rank by (a) how many distinct
   high-priority UCs a single gap blocks (foundational gaps first) and (b) verdict severity.

4. **Fill — where a gap meets a standard, add the type.** When a cluster of `unsupported` UCs needs a
   capability the architecture lacks *and a real standard defines it*, create the new **UDLM resource type**
   — never invent when a standard fits. Apply the adopt discipline: **standards-first**, produce the
   **concrete field-level diff** (drop citation-only/ceremony adopts; a protocol RFC is not a data model),
   be **net-negative on bespoke surface**, and ground every field in real **producers/consumers**. Ship as a
   feature-branch PR (validators + estate-token gate green); the maintainer merges.

5. **Report + admit — architect disposes.** Produce the run report: verdict distribution, the ranked gaps,
   the new UCs/sets, and any proposed types with their standard + diff. **No auto-admission** — generated UCs
   and new types are *candidates*; the architect reviews and admits. The framework proposes; the architect
   disposes.

## Both systems under test

Run the same process against **UDLM** (does the *data model* express what the UC needs?) and **DCM** (does the
*realization* — the runtime contracts, providers, policies — deliver it?). A UC can pass at the UDLM layer
(the shape exists) yet gap at DCM (no provider/flow realizes it); keeping both in view is how the two-track
model (intent vs realized) gets exercised, not just asserted.

## Cadence

Re-run after any material architecture change (a boundary sweep, a new capability program, a ratified ADR
batch). The baseline from step 1 makes each run a regression check: gaps that were `unsupported` last time
should be closing, and nothing previously `supported` should regress.

## Discipline checklist

- [ ] Generated UCs modeled on the reference set's depth (read a few first).
- [ ] Every generated UC carries `generated_by` provenance.
- [ ] Gaps ranked foundational-first (most UCs unblocked), not by raw count.
- [ ] New types are standards-first with a concrete field diff — no ceremony adopts.
- [ ] Nothing auto-admitted; the report is for the architect to disposition.
- [ ] Baseline captured so the next run is a regression check.
