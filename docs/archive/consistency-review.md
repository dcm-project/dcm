> **Archived 2026-07-23.** Point-in-time review record; its findings are resolved. Kept for the reasoning trail — do not extend.

# DCM — Consistency Review Findings

**Document Status:** ✅ Complete
**Document Type:** Review Record
**Date:** 2026-03
**Scope:** Full review of all 50 data model documents, 14 specifications, 11 schema files, and 4 OpenAPI specs for naming inconsistencies, field conflicts, API surface misalignments, and terminology drift.

---

## Summary

| Category | Issues Found | Fixed | Notes |
|----------|-------------|-------|-------|
| API path format (AEP colon syntax) | 13 + 4 | ✅ All | admin-api-spec.md and consumer-api-spec.md had stale slash-verb paths |
| Stale entity_type values | 2 | ✅ All | `allocated_resource` and `resource_entity` replaced with canonical values |
| Stale threshold key format | 5 | ✅ All | `auto_approve_below`/`verified_above` in scoring doc examples replaced with named-tier format |
| provider_id vs provider_uuid | 6 | ✅ All | Resolved to `provider_uuid` in all DCM API paths |
| Four store naming | Variant | ⚠️ Noted | Multiple names in use — canonical list documented below |
| Operation (LRO) shape completeness | 1 | ✅ | Polling section added to consumer spec |
| lifecycle_state casing | Mixed | ⚠️ Noted | UPPERCASE in YAML examples, lowercase in prose — by design |
| Resource Type naming | Mixed | ⚠️ Noted | `resource_type` (field) vs `resource_type_fqn` (format ref) — not a conflict |
| Provider type count references | 1 | ⚠️ Superseded by ADR-005 | ADR-005 abolished a fixed provider-type COUNT in favor of declared CAPABILITY; the UDLM provider-contract kinds are service/information/process/peer_dcm (auth = a capability). "Eleven/11" is legacy — align to the capability model. |
| Anti-vocabulary: 'widget' | 0 | N/A | Clean — eliminated in prior sessions |

---

## 1. API Path Format (AEP Colon Syntax)

### 1.1 Findings

The AEP colon syntax was applied to the OpenAPI YAML files in a prior session but **not propagated** to the narrative specification documents. This meant `dcm-admin-api-spec.md` and `dcm-consumer-api-spec.md` still used slash-verb paths while the normative OpenAPI specs used colon-verb paths.

**Affected specs:**
- `dcm-admin-api-spec.md` — 13 stale slash-verb paths
- `dcm-consumer-api-spec.md` — 4 stale slash-verb paths (partially fixed but not fully)
- `dcm-flow-gui-spec.md` — 2 stale paths (`:promote`, `:run` fixed in prior session)

### 1.2 Resolution

Applied the full set of colon conversions to both narrative specs. Both specs now include AEP alignment notes referencing the normative OpenAPI YAML files. Specific conversions:

**Consumer spec:** `:suspend`, `:resume`, `:rehydrate`, `:rotate`, `:extend-ttl`, `:transfer`, `:bulk-decommission`, `:acknowledge`, `:revert`, `:accept`, `:reject`, `:approve`, `:read-all`

**Admin spec:** `:approve`, `:reject`, `:suspend`, `:reinstate`, `:revoke-sessions`, `:reset`, `:vote`, `:rotate-credential`, `:trigger`, `:rebuild`, `:accept-degradation`, `:activate`

### 1.3 Canonical Rule

> Custom method paths use colon syntax: `POST /resources/{name}:verb`.
> This applies to all narrative specs, OpenAPI YAML, and code examples.
> Sub-resources (`.../status`, `.../stream`, `.../pending` as filtered list) keep slash notation.

---

## 2. Entity Type Values

### 2.1 Findings

Two documents used stale or incorrect values for the `entity_type` field:

| Document | Stale Value | Correct Value |
|----------|-------------|---------------|
| `09-entity-relationships.md` | `allocated_resource` | `infrastructure_resource` (with `ownership_model: allocation`) |
| `18-webhooks-messaging.md` | `resource_entity` | `infrastructure_resource` |

The `related_entity_type: internal` and `related_entity_type: external` in doc 09 are **not** entity_type values — they are relationship scope descriptors and are correct as-is. They describe whether the related entity is managed within DCM or is an external reference.

### 2.2 Resolution

Both corrected in place. The `allocated_resource` correction includes a comment: `# ownership_model: allocation` to preserve the semantic intent of the original example.

### 2.3 Canonical Values

The three valid `entity_type` values are:
- `infrastructure_resource` — persistent physical or virtual resource
- `composite_resource` — composite service definition-orchestrated aggregate
- `process_resource` — ephemeral execution (automation job, playbook)

Pool resources and shared resources are `infrastructure_resource` entities with `ownership_model: whole_allocation` or `ownership_model: shareable`. There is no separate pool or shared entity type.

---

## 3. Scoring Model Threshold Keys

### 3.1 Findings

`29-scoring-model.md` contained 5 examples using the old fixed-column threshold key format (`auto_approve_below`, `verified_above`) in per-service-type override examples. The authority tier model (doc 32) replaced these with a named-tier list format in a prior session, but the scoring doc examples were not updated.

**Old format (stale):**
```yaml
auto_approve_below: 20
verified_above: 40
```

**Current format:**
```yaml
thresholds:
  - { tier: auto,     max_score: 20 }
  - { tier: verified, max_score: 40 }
```

### 3.2 Resolution

Replaced stale threshold keys with comments pointing to the named-tier format. The SMX-008 policy row was verified as already using current terminology.

---

## 4. provider_id vs provider_uuid

### 4.1 Findings

The operator interface spec (`dcm-operator-interface-spec.md`) and provider callback auth doc (`43-provider-callback-auth.md`) used `provider_id` in some places where `provider_uuid` is the correct DCM term.

The distinction is important:
- **`provider_uuid`** — DCM-assigned UUID for the provider record. Used in all DCM API paths and payloads.
- **`resource_id`** — Operator-assigned identifier for a specific resource instance. Used in operator-to-DCM callbacks to identify the resource being reported on.

### 4.2 Resolution

DCM API endpoint paths updated to use `provider_uuid` consistently:
- `POST /api/v1/providers/{provider_uuid}/capacity`
- Registration response field `provider_id` → `provider_uuid`

`resource_id` in callback APIs is **intentionally different** from `entity_uuid`. It is the operator's own identifier for the resource (returned in the `CreateResponse`). DCM maps it to `entity_uuid` internally. This distinction is correct and remains unchanged.

---

## 5. Four Store Naming — Canonical Reference

Multiple naming variants found across documents. The canonical names are:

| Store | Canonical Name | Also Used (acceptable) | Do Not Use |
|-------|---------------|----------------------|------------|
| Intent State storage | **Intent Store** | DCM database (when emphasizing the implementation) | Intent State Store |
| Requested State storage | **Requested Store** | — | Requested State Store |
| Realized State storage | **Realized Store** | Realized State Store | Realization Store |
| Discovered State storage | **Discovered Store** | — | Discovered State Store |

No bulk renaming was performed — both "Intent Store" and "DCM database" are used accurately in different contexts (the former emphasizes the state model, the latter the implementation). The variation is acceptable context-dependent usage, not an error.

---

## 6. Operation (LRO) Shape

### 6.1 Finding

The `consumer-api-spec.md` applied LRO `Operation` responses to async endpoints but did not include a dedicated section explaining the `GET /api/v1/operations/{uuid}` polling endpoint or the complete Operation shape.

### 6.2 Resolution

Added an "Operations — Polling Long-Running Requests" section to `consumer-api-spec.md` covering:
- The polling endpoint shape with in-progress, success, and failure states
- Polling backoff guidance (1s → 2s → 5s → 10s → 30s)
- Alternatives: webhook subscription (`request.progress_updated`), SSE stream

---

## 7. Lifecycle State Casing

### 7.1 Finding

Lifecycle state values appear in UPPERCASE in YAML examples (e.g., `lifecycle_state: OPERATIONAL`) and in lowercase in prose text (e.g., "the resource enters the operational state"). This is **by design**, not an inconsistency:

- UPPERCASE in YAML/JSON — machine-readable, matches enum values in schemas
- Lowercase in prose — natural language, matches how engineers write documentation

No changes made.

---

## 8. resource_type vs resource_type_fqn

### 8.1 Finding

The JSON entity schema uses `$ref: resource_type_fqn` as a type reference (meaning the field value must be a Fully Qualified Name like `Compute.VirtualMachine`). Narrative YAML examples use `resource_type:` as the field name. This appears inconsistent but is not.

`resource_type` is the **field name**. The value it holds must conform to the **FQN format** (`Category.TypeName`). The schema type reference is just documenting the format constraint.

No changes made.

---

## 9. What Remains Acceptable (Not Fixed)

These were identified but are not bugs — they are intentional or context-appropriate variation:

| Item | Why It's Acceptable |
|------|---------------------|
| `Service Provider` (title case) vs `service_provider` (snake_case) | Title case in prose, snake_case in code/YAML — correct by context |
| `Auth Provider` vs `auth_provider` | Same as above |
| `Resource Type Spec` vs `Resource Type Specification` | Shortened form acceptable in prose; full form in formal definitions |
| `Realized State` vs `realized state` | Title case for the formal concept, lowercase in general prose |
| `related_entity_type: internal/external` in doc 09 | Not entity_type values — relationship scope descriptors, correct as-is |
| Provider type count varies ("nine", "eleven", "11") | Moot after ADR-005 — providers are typed by declared capability, not a fixed count (see ADR-002 supersede note). |

---

## 10. Remaining Items Requiring Action by Implementers

These are not documentation issues but implementation decisions that need to be made explicit when building DCM:

| Item | Decision Needed |
|------|----------------|
| `resource_type` field in API payloads accepts short names (`Compute.VirtualMachine`) or requires registry UUID? | Current spec allows both `resource_type` (FQN string) and `resource_type_uuid` — need to decide if UUID is required at dispatch or optional |
| Operation polling endpoint `GET /api/v1/operations/{uuid}` — is operation status part of request status, or a separate Operation resource? | Currently: request status via `GET /api/v1/requests/{uuid}/status`; Operation via `GET operation.name`. Need to clarify if these are the same or different responses |
| `provider_id` in operator-assigned resource IDs vs DCM `provider_uuid` — implementers must ensure they're not conflated at the API Gateway level | Code-level concern — the API Gateway maps `resource_id` (operator-assigned) to `entity_uuid` (DCM-assigned) |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*

---

## Second Review Pass — 2026-03

A second comprehensive scan identified additional issues and confirmed no new architectural conflicts.

### Additional Fixes Applied

| Fix | Files Affected | Description |
|-----|---------------|-------------|
| Stale slash-verb paths | 14 files | Data model docs 00, 23, 24, 32, 35, 40, 42, 43 and specs dcm-admin-gui, dcm-consumer-gui, dcm-examples, dcm-registration, dcm-admin-api | All remaining colon-less custom method paths converted |
| DELETE /api/v1/auth/session | dcm-consumer-api.yaml | Missing endpoint added to OpenAPI YAML (was in narrative spec only) |
| GET /api/v1/operations/{uuid} | dcm-consumer-api.yaml | Operation polling endpoint added to OpenAPI YAML |
| Missing event types | 33-event-catalog.md | 6 event types added: entity.deleted, entity.state_transition, group.deleted, group.member_added, group.member_removed, authorization.granted |
| Prompt section numbering | DCM-AI-PROMPT.md | Duplicate section 78 resolved; sections 0–80 now sequential with no duplicates |

### Confirmed Clean (No Issues)

- **OpenAPI schemas**: All 4 specs (consumer/admin/operator/callback) — 0 schema conflicts
- **Lifecycle state casing**: UPPERCASE in YAML/JSON examples, lowercase in prose — intentional
- **`Ingress API` usage**: Two occurrences are contextually correct (infrastructure layer explanation)
- **`resource_type` vs `resource_type_fqn`**: Field name vs format description — not a conflict
- **`name:` vs `display_name:`**: Context-appropriate — `name:` is a property name, `display_name:` is a human label
- **Policy type casing**: Uppercase in section headers, lowercase in code/YAML — by convention
- **Provider type count**: All references to "eleven" or "11" provider types — consistent
- **Realized State write authority**: Consistent across all docs — providers never write directly; DCM API Gateway is sole writer

### Remaining Acceptable Variation

These are not errors — they are deliberate context-dependent usage:

| Pattern | Both Forms Correct | Reason |
|---------|--------------------|--------|
| `Service Provider` / `service_provider` | Title case in prose, snake_case in code | Convention |
| `Auth Provider` / `auth_provider` | Same | Convention |
| `Policy Engine` / `policy_engine` | Same | Convention |
| Intent Store / DCM database | Both describe the same store | Different emphasis (state model vs implementation) |
| `entity.created` / `resource.provisioned` | Different semantic levels | Entity creation vs provisioning completion are distinct events |

### Implementation Decisions Still Outstanding

These three items were identified in the prior review and remain open — they require implementation choices, not documentation changes:

1. **`resource_type` at dispatch**: Accept FQN string (`Compute.VirtualMachine`) or require UUID? Current specs allow both; implementation must pick one canonical form.
2. **Operation polling endpoint**: Is `GET /api/v1/operations/{uuid}` the same resource as `GET /api/v1/requests/{uuid}/status`, or a separate resource? Added to OpenAPI YAML as separate endpoint.
3. **`resource_id` → `entity_uuid` mapping**: The API Gateway must map operator-assigned `resource_id` to DCM `entity_uuid` at the callback boundary. This is a code-level concern with no documentation gap.

