# ADR-018: Wire Serialization & Event Conventions

**Status:** Accepted
**Date:** June 2026
**Docs:** ADR-003 (Four Lifecycle States), ADR-009 (API Gateway & Control Plane); UDLM `registry/naming-conventions.md` §4; AEP (`aep.dev`); CNCF CloudEvents
**Tracking:** companion to the UDLM data-model casing decision (naming-conventions §4). Supersedes the camelCase first draft of this ADR.

## Context

UDLM defines the **data model** and fixes its on-the-wire casing — **`snake_case` keys** (UDLM `naming-conventions.md` §4). DCM is the **runtime** that serializes and transports that model — over REST/gRPC at the API gateway (ADR-009) and over the event bus — between services written in **Go and Python**. This ADR covers the DCM-side conventions so the snake_case contract flows end to end without per-hop key-translation layers. (The casing of the data model itself is UDLM's call; this ADR is how the runtime honors it.)

**Why snake_case (the reversal):** UDLM is a **canonical data model consumed natively** — the model *is* the wire form, so there is no separate "API casing" to translate to. DCM's API is the consumer with a hard external constraint: it conforms to **AEP** (`aep.dev`, the dcm-project engineering team's adopted API-design standard, enforced by `aep-dev/aep-openapi-linter`), whose prescribed fields are snake_case (`page_size`, `*_time`). Native-universal consumption **+** AEP-bound API jointly force one casing — snake_case. The first draft of this ADR chose camelCase on research that had not accounted for AEP; this revision reverses it. (Empirically: the AEP linter reports zero casing findings against the existing snake_case OpenAPI specs.)

## Decision

1. **Wire payloads are `snake_case`** — request/response bodies and event payloads match the UDLM data model and AEP. No snake_case↔camelCase translation layer between the API, the event bus, and services.

2. **Go services:** PascalCase exported struct fields with explicit tags — `json:"snake_case" yaml:"snake_case"`. Go keeps its idiom; the wire stays snake_case.
   ```go
   type ResourceDefinition struct {
       ResourceID  string `json:"resource_id" yaml:"resource_id"`
       MemoryLimit string `json:"memory_limit" yaml:"memory_limit"`
   }
   ```

3. **Python services:** native `snake_case` attributes via **Pydantic** — attribute names map **directly** to wire keys, so no alias generator is needed (the camelCase draft required `alias_generator=to_camel`; that is now removed). Python keeps PEP 8 *and* the wire matches it.

4. **Events use the CloudEvents envelope** (CNCF). Event **payload** property keys are `snake_case`. Event **type identifiers / topics** are lowercase **dot notation** — `resource.discovered`, `entity.realized`, `resource.definition.created` — so brokers (Kafka/NATS/etc.) can **wildcard-route** (`resource.definition.*`). Topics are an event-naming concern, orthogonal to payload casing. (CloudEvents *context attributes* are themselves flatcase per the CloudEvents spec — neither snake nor camel — and are unaffected.)

5. **No ad-hoc translation.** Frontends, third-party webhooks, and microservices consume the same snake_case shape; serialization config is centralized (Go tags), not reinvented per service. The one place casing changes is an **export adapter** at a foreign-domain boundary (e.g. projecting a resource into a Kubernetes CRD, which is camelCase by convention) — never inside the DCM/UDLM/DAV core.

## Options considered

- **camelCase on the wire** — rejected: conflicts with AEP (the adopted, lint-enforced API standard) and with native-universal UDLM consumption; would re-introduce the translation layer native consumption exists to remove. (This was the first draft; reversed.)
- **PascalCase keys** — rejected: legacy CloudFormation idiom only.
- **camelCase topics** — moot: event names use dot-notation regardless of payload casing, for broker wildcard routing.

## Consequences

- API specs are AEP-conformant on casing; the `aep-openapi-linter` casing checks pass.
- Python services need **no** Pydantic alias generator — attribute = wire key. Go adds snake_case struct tags (mechanical, centralized).
- Frontends and third-party webhook consumers ingest payloads directly — no key-translation layer; one convention from API request → event bus → service.
- Events are CloudEvents-compliant; dot-notation topics enable wildcard subscriptions.
- This ADR is the DCM realization of UDLM `naming-conventions.md` §4 — the data-model casing is owned by UDLM; the transport/serialization conventions are owned here. Both are now snake_case, so the contract is identity end to end.
