# DCM — Adopted External Standards (the DCM-domain requirements)

UDLM defines the **Adopt** disposition: when a credible external standard already models a domain's data
(FOCUS for cost/usage, OpenCost for k8s allocation, OSCAL for compliance, SCIM for identity), the data
substrate carries only *identity*, a *version-pinned conformance reference*, and the *binding* — never
the standard's schema. See UDLM `design-principles/core-tenets.md` **T5** and
`design-principles/adopted-standards.md`.

That is the **Data** half. This document states the **DCM** half: the requirements DCM must implement
and enable so adopted standards actually work at runtime. It is an application of the
**Data ⇄ Policy boundary** (`data-policy-boundary.md`): **the data declares which standard versions are
in play; DCM (Policy/Provider runtime) negotiates, enforces, and translates between them.**

DCM **MUST** adhere to T5: it does not absorb an external standard's schema into its own persistence,
and does not become the system of record for adopted data — that data is referenced via an Information
Provider, lookup-only (`contracts/information-providers.md`).

> **Scope — Tier 2 only.** These requirements apply to **record/schema** standards (FOCUS, OpenCost,
> OSCAL, SCIM), which version in ways that change their shape. **Value/codelist** standards (ISO 4217,
> ISO 8601, RFC 4122) are adopted as a plain referenced field constraint — *no* support matrix, *no*
> version negotiation, *no* ADS requirements. Route by kind first (UDLM `adopted-standards.md` §1a).

## Requirements (ADS — Adopted Standards)

### Registration & discovery
- **ADS-001 — Provider support matrix.** DCM **MUST** accept and validate a provider's
  `adopted_standard_support[]` declaration at registration: for each adopted standard, the supported
  version range, a `preferred` version, and `direction` (`emit` | `consume` | `both`). It is validated
  and trust-stamped like any other provider capability.
- **ADS-002 — Compatibility discovery.** DCM **MUST** expose, for discovery, which providers can serve
  which standard versions, so an implementor can select a compatible provider before binding. Silent
  incompatibility is not permitted.

### Negotiation, translation, enforcement (Policy)
- **ADS-003 — Version negotiation.** At binding time DCM **MUST** resolve the intersection of the
  consumer/type **required** version range and the provider's **supported** range, selecting the
  effective version (highest common, or `preferred` when inside the overlap).
- **ADS-004 — Translation as Policy.** When required and supported do not directly overlap, DCM **MAY**
  translate between versions via a **registered, deterministic** mapping — preferably the standard's own
  published migration. Translation is a **Policy act** (transformation is Policy, UDLM T2), evaluated and
  **audited**; it is never an evaluator embedded in the portable data.
- **ADS-005 — Enforcement / reject.** If there is no compatible version **and** no registered
  translation path, DCM **MUST** reject the binding as non-conformant and **surface** it — never
  silently drop or downgrade.
- **ADS-006 — Implementor-bounded parameters.** Parameters defined by the standard but constrained by
  the implementor (e.g. cost rate ranges, markup minimums, budget ceilings) **MUST** be enforced via
  **policy-as-code** (OPA/Rego), not hard-coded — consistent with DCM's policy-governance model.

### Identity, provenance, audit (recording the decision)
- **ADS-007 — Identity join, no ownership.** DCM **MUST** resolve an adopted-standard binding using the
  UDLM identity ↔ standard-column join (e.g. resource `uuid` ↔ FOCUS `ResourceId`) and **MUST NOT**
  cache or persist the external records as a system of record — the data is served by the Information
  Provider with the freshness/authority the IP contract provides
  (`contracts/information-providers-advanced.md`).
- **ADS-008 — Effective-version provenance.** DCM **MUST** record the negotiated **effective version**
  (and, when it translated, the source version + translation reference) as **provenance** on the
  realized entity, and **MUST** lower confidence/authority for translated/derived values.
- **ADS-009 — Auditability.** The negotiation outcome (accept / translate / reject) and any translation
  **MUST** be written to the tamper-evident audit log (`AUD-001/002`) as a decision — reproducible from
  the immutable record.

### Lifecycle
- **ADS-010 — Standard version lifecycle.** DCM **MUST** track adopted-standard version deprecation and
  allow a configured **minimum** and **preferred** version per environment, so an operator can require,
  e.g., "FOCUS ≥ 1.3" platform-wide and let negotiation/translation satisfy older providers.

## How this maps to the boundary

| Step | Data (UDLM) — the noun | DCM (Policy/Provider) — the verb |
|---|---|---|
| Provider declares support | `adopted_standard_support[]` record | validate + register (ADS-001) |
| Consumer/type needs a version | `adopts[].version` range | — |
| Pick the version | — | **negotiate** required ∩ supported (ADS-003) |
| Versions don't match | registered migration reference | **translate** (ADS-004) or **reject** (ADS-005) |
| Bind to the resource | identity ↔ standard column | **resolve** join, IP lookup (ADS-007) |
| Record what happened | effective-version provenance slot | **write** provenance + audit (ADS-008/009) |
| Constrain parameters | the declared parameter values | **enforce** via Rego (ADS-006) |

> Test (same as the boundary doc): a **noun** (a support record, a version pin, a join key, a provenance
> slot) is UDLM's; a **verb** (negotiate, translate, enforce, reject, resolve, record) is DCM's.

## Worked example — cost (FOCUS + OpenCost)

The Cost Management Service Provider (`dcm-project/enhancements#57`) is the reference case: it declares
`adopted_standard_support` for FOCUS (`≥1.2 <2.0`, preferred 1.4, emit) and OpenCost (`1.x`); DCM
negotiates against a chargeback view that requires FOCUS ≥ 1.3 (allocation columns); rate ranges and
budgets are enforced by Rego (ADS-006); the effective version is recorded as provenance (ADS-008). The
cost data itself is **never** modeled in DCM/UDLM — it conforms to FOCUS and is served via the SP's
Information-Provider query API. This is what "adopt, don't absorb" looks like end-to-end.

See also: `data-policy-boundary.md`, UDLM `design-principles/adopted-standards.md` (the Data-side
contract), `dcm-platform-requirements.md` (the broader requirement set).
