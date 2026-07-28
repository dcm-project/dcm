# DCM OpenAPI — AEP conformance

DCM's public APIs adopt the **[API Enhancement Proposals](https://aep.dev/)** (AEP) — resource-oriented
design, the standard methods (Get/List/Create/Update/Delete), and the RFC 9457 error model — per
**ADR-AEP-001** (croadfeldt/udlm). Conformance is checked by the AEP **Spectral** OpenAPI ruleset.

## Run the linter locally

```
npm install @stoplight/spectral-cli @aep_dev/aep-openapi-linter
npx spectral lint "schemas/openapi/*.yaml" --ruleset .spectral.yaml
```

CI runs the same lint on every PR that touches `schemas/openapi/**` (`.github/workflows/lint-openapi.yml`).
It is **advisory** today (`continue-on-error: true`) while the baseline below is burned down; flip it to
blocking once the error count reaches zero.

## Baseline (2026-07-08, first run)

| Spec | Errors | Warnings | Notes |
|------|--------|----------|-------|
| `dcm-consumer-api.yaml` | 144 | 236 | |
| `dcm-operator-api.yaml` | 32 | 24 | |
| `dcm-provider-callback-api.yaml` | 22 | 25 | |
| `dcm-admin-api.yaml` | — | — | **P0: invalid YAML — does not parse / lint (see below)** |

### Top rule categories (across the three parseable specs)

| Count | Rule(s) | Category |
|------:|---------|----------|
| ~110 | `aep-158-*` (next-page-token, max-page-size, page-token) | **Pagination** — List methods need `page_size`/`page_token` params + `next_page_token` in the response |
| ~90 | `aep-131/132/133/135-*` (operation-id, request-body, response-body) | **Standard methods** — Get/List/Create/Update/Delete operationId + body conventions |
| ~62 | `aep-142-time-field-*` | **Time fields** — timestamp fields must be named `*_time` |
| 77 | `operation-description` | Every operation needs a description |
| 35 | `oas3-schema` | Structural OpenAPI validity (non-AEP) |
| ~7 | `aep-193-error-response-schema` | **Errors** — responses should be RFC 9457 Problem Details |
| misc | `aep-140-uri-property-naming`, `aep-136-operation-id` (LRO) | naming / long-running operations |

## Remediation plan (ratchet the baseline down)

1. **P0 — fix `dcm-admin-api.yaml` structural corruption.** It has **two `components:` blocks** (~line 1535 and ~line 1838) and duplicated/misplaced `/api/v1/admin/overrides…` path blocks nested under `components:`; the YAML is invalid (fails to parse at ~line 1846). Repair: consolidate to one `components:`, move the misplaced path blocks under `paths:`, de-duplicate. Then it can lint.
2. **RFC 9457 errors (`aep-193`).** Replace the bespoke `Error` / `OperatorError` / `ProviderError` schemas with a shared `ProblemDetails` schema (`type/status/title/detail/instance` + extension members), `application/problem+json` — consistent with the UDLM error model (croadfeldt/udlm `contracts/error-model.md`, ADR-AEP-001).
3. **Pagination (`aep-158`).** Give every List method `page_size` + `page_token` parameters and `next_page_token` in the response.
4. **Standard methods (`aep-131/132/133/135`).** Normalize operationIds and request/response bodies to the AEP method shapes.
5. **Time fields (`aep-142`).** Rename timestamp fields to the `*_time` suffix.
6. **Descriptions.** Add operation descriptions.

Flip CI to blocking after step 4; steps 5–6 are polish.
