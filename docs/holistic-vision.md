# The Holistic Realization Model — DCM's place in it

_Foundational. Captured 2026-06-08. Master copy: `dav/docs/holistic-vision.md`
(mirrored in `udlm/docs/holistic-vision.md`). This file states the shared model and
where **DCM** sits in it._

## The model

**Use Cases are the unit of desired outcome.** A Use Case is *realized* only when
**three foundational pillars** each support it:

- **Platform** — can the architecture/plan support the UC? Managed through
  capabilities, specification, rules, context, execution. *(answers: can the system
  do it?)*
- **People / Process** — is the organization, its people, skills, and processes
  structured and operating to support the UC? *(operating model, org design, value
  streams)*
- **Enablement** — is the consumer enabled to adopt, consume, and operate the UC?
  *(adoption, change, skills transfer, operationalization)*

> **Platform + People/Process + Enablement → realization of Use Cases → the holistic vision.**

Each pillar is a different **view of mostly the same data** (UCs ↔ gaps ↔
capabilities), evaluated by the same gap-analysis engine (DAV); only the **evaluation
target** and **ingestion method** change per pillar. Output is always: gaps →
prioritized capabilities → strategy + roadmap.

## DCM's role: the Platform pillar realization

DCM is a reference realization of the **Platform** pillar — the declarative control
plane (Data / Provider / Policy) that makes a platform *able to support* Use Cases. In
the holistic model, DCM answers **"can the system do it?"** — one of three pillars, not
the whole picture. People/Process and Enablement sit alongside it, evaluated against the
same UCs.

This framing keeps DCM's scope honest: DCM enables the platform foundation; realizing a
Use Case end-to-end still requires the organization (People/Process) and the consumer's
ability to adopt it (Enablement). DAV is the engine that evaluates all three; DCM is what
"good" looks like for the platform pillar, and the spec DAV validates against in AD mode.

## Data ownership boundary

UDLM provides the design language and minimal requirements. DCM is one realization
(implementation) of that language. **Neither UDLM nor DCM owns or stores sensitive
customer data** (contract pricing, customer PII, credential values). They provide
the plumbing, integration hooks, and event bus for data exchange — the sensitive
instance data stays with the customer's systems or the credential management service.
