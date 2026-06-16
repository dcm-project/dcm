---
Document Status: 📋 Draft — Ready for Implementation Feedback
Document Type: Capability Specification
Maps to: udlm/governance/accreditation-and-authorization-matrix.md
---

# DCM Data Model — Accreditation Monitor

> **Implements contracts defined in UDLM**:
> [udlm/governance/accreditation-and-authorization-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md).
> UDLM defines the accreditation entity, the authorization matrix, and the
> validity model. DCM operationalizes continuous external verification of
> accreditation status against authoritative sources.

**Document Status:** 📋 Draft — Ready for Implementation Feedback
**Document Type:** Capability Specification
**Related Documents:** [Accreditation and Authorization Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) | [Information Providers](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers.md) | [Advanced Information Providers](https://github.com/croadfeldt/udlm/blob/main/contracts/information-providers-advanced.md) | [Standards Catalog](https://github.com/croadfeldt/udlm/blob/main/reference/standards-catalog.md) | [Scoring Model](../convergence-engine/scoring.md) | [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md) | [Governance Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/governance-matrix.md)

> **AEP Alignment:** API endpoints follow [AEP](https://aep.dev) conventions.
> Custom methods use colon syntax. Async operations return `Operation` resources.
> See `schemas/openapi/dcm-admin-api.yaml` for the normative admin API specification.

---

## 1. Purpose

The Accreditation Monitor is a DCM **Information Provider** that continuously verifies the status of registered accreditations against authoritative external sources — compliance registries, certificate authority portals, and contract management systems. It answers the question DCM's existing accreditation lifecycle model cannot answer alone:

> *"Is this accreditation still valid according to the issuing authority — not just according to the expiry date we were told?"*

An accreditation can become invalid before its declared `expires_at` date: FedRAMP authorizations can be revoked mid-cycle, ISO 27001 certificates can be suspended by the certification body, CMMC certifications can be downgraded. Without external monitoring, DCM would continue treating a provider as accredited until the date it was told to check — which may be 12 months away.

The Accreditation Monitor closes this gap by polling authoritative external registries on a configurable schedule and surfacing discrepancies to DCM's existing accreditation lifecycle model.

---

## 2. What Can Be Automated — Framework by Framework

Automation depth varies significantly by framework. The Accreditation Monitor implements four verification tiers:

### Tier 1 — Full External Verification (public registry API)

DCM can query the authoritative registry directly. Status changes are detected without any manual intervention.

| Framework | Authoritative Source | What Is Verified |
|-----------|---------------------|-----------------|
| **FedRAMP Moderate/High/LI-SaaS** | [marketplace.fedramp.gov/api](https://marketplace.fedramp.gov) | Authorization status (Authorized / In Process / Revoked), impact level, authorization date, annual assessment currency |
| **StateRAMP** | [stateramp.org](https://stateramp.org) | Authorization status, status changes |
| **CMMC 2.0** | [cyberab.org/catalog](https://cyberab.org/catalog) | Certification level (1/2/3), certification status, expiry date |
| **IAF / ISO 27001** | [iaf.nu CertSearch](https://iaf.nu) | Certificate status (valid/suspended/withdrawn), expiry date, scope, issuing CB identity |

**Required field at registration:** `external_registry_id` — the provider's identifier in the external registry (FedRAMP ID, CMMC certification number, ISO certificate number).

### Tier 2 — Document Currency Verification

DCM cannot query a central registry, but it can verify that the stored evidence document is current relative to the framework's required renewal cycle.

| Framework | Verification Method | Currency Check |
|-----------|---------------------|---------------|
| **SOC 2 Type I / Type II** | Document metadata extraction from `audit_report_ref` | Report period end date must be within 12 months (configurable); examines PDF metadata or report header |
| **PCI DSS** | QSA authorization check + AoC date | Verifies the issuing QSA firm is currently listed as authorized at PCI SSC; verifies stored AoC covers current period |
| **ISO 27001** (when CB portal is unavailable) | Certificate document date + P3Y renewal cycle | Falls back to document-based verification if IAF CertSearch is unreachable |

### Tier 3 — Contract Lifecycle Integration

No external registry exists. Verification is driven by events from contract management systems.

| Framework | Integration Mechanism | What Triggers Verification |
|-----------|----------------------|--------------------------|
| **HIPAA BAA** | Contract management webhook (DocuSign, Ironclad, Agiloft, custom) | BAA signed, amended, terminated, or approaching renewal |
| **DoD IL2/IL4/IL5/IL6** | Manual submission + webhook on DISA action letter | Authorization letter received, amended, or revoked |
| **Custom / Sovereign** | Manual submission + optional webhook | Platform admin triggers; or custom webhook from issuing authority |

### Tier 4 — Expiry-Only Monitoring (no external verification available)

No external API, no document currency check, no contract integration. DCM monitors only the declared `expires_at` date.

| Framework | What Is Monitored |
|-----------|-----------------|
| **HIPAA BAA** (if no contract system) | Declared BAA expiry date |
| **Internal / first_party accreditations** | Declared validity period |
| **Self-declared** | Declared validity period |

---

## 3. Accreditation Record Additions

The existing accreditation record (doc 26 Section 3.3) is extended with three new fields to support automated monitoring:

```yaml
accreditation:
  # ... existing fields unchanged ...

  # NEW — Verification model
  verification:
    tier: external_registry | document_currency | contract_webhook | expiry_only
    # ── Tier 1 specific ──
    registry_api:
      provider: fedramp | stateramp | cmmc_ab | iaf_certsearch | custom
      lookup_key: <external_registry_id value>    # e.g., FedRAMP ID "FR2024-0042"
      poll_interval: P1D                          # how often to check
      last_checked_at: <ISO 8601>
      last_result: confirmed_active | status_changed | registry_unavailable | not_found
    
    # ── Tier 2 specific ──
    document_check:
      document_url: <same as certificate_ref or audit_report_ref>
      max_age: P365D                              # how old the document can be
      date_extraction_method: pdf_metadata | report_header_parse | manual
      last_checked_at: <ISO 8601>
      last_document_date: <ISO 8601>
    
    # ── Tier 3 specific ──
    contract_webhook:
      contract_system: docusign | ironclad | agiloft | custom
      contract_id: <external contract ID>
      webhook_url: <DCM inbound webhook URL for this accreditation>
      last_event_at: <ISO 8601>
    
    # ── Shared ──
    stale_after: P7D                              # how long before last_checked_at = stale
    stale_action: warn | suspend | escalate       # what to do when stale
    verification_failure_count: 0                 # consecutive failures; triggers escalation
    verification_failure_threshold: 3
```

The `last_verified_at` field on the existing accreditation record (doc 26) is updated by the Accreditation Monitor on each successful verification. It remains the canonical "last confirmed active" timestamp used by the Governance Matrix and Scoring Model.

---

## 4. Accreditation Monitor as an Information Provider

The Accreditation Monitor registers with DCM as an Information Provider with `information_type: accreditation_verification`. It is a separately deployable component — it does not require changes to the DCM control plane and can be upgraded independently.

```yaml
accreditation_monitor_registration:
  provider_type: information_provider
  information_type: accreditation_verification
  display_name: "DCM Accreditation Monitor"
  version: "1.0.0"
  
  # What it monitors
  supported_tiers:
    - external_registry
    - document_currency
    - contract_webhook
    - expiry_only
  
  supported_registries:
    - fedramp
    - stateramp
    - cmmc_ab
    - iaf_certsearch
    - pci_ssc_qsa      # QSA verification only
  
  supported_contract_systems:
    - docusign
    - ironclad
    - custom_webhook
  
  # How it communicates results back to DCM
  push_events: true
  event_types:
    - accreditation.verified           # periodic confirmation: still active
    - accreditation.status_changed     # external registry shows different status
    - accreditation.registry_mismatch  # external status != DCM recorded status
    - accreditation.verification_stale # last_checked_at exceeds stale_after threshold
    - accreditation.expiry_approaching # approaching expires_at (supplement to existing)
    - accreditation.document_expired   # document_check: document older than max_age
    - accreditation.contract_event     # contract_webhook: BAA signed/amended/terminated

  health_check:
    endpoint: /health
    interval: PT5M
```

---

## 5. Verification Flows

### 5.1 Tier 1 — FedRAMP External Registry Verification

```
Accreditation Monitor poll cycle (default: P1D):
  │
  ▼ For each active Tier 1 accreditation:
  │   Load accreditation record
  │   Extract: framework, external_registry_id, last known status
  │
  ▼ Query external registry:
  │   FedRAMP: GET marketplace.fedramp.gov/api/products?id={external_registry_id}
  │   CMMC:    GET cyberab.org/api/certifications?cert_number={external_registry_id}
  │   IAF:     GET iaf.nu/certsearch?cert={external_registry_id}
  │
  ├── Registry returns: status = Authorized, impact_level = High
  │     Matches DCM record → no action
  │     Update: last_checked_at, last_result: confirmed_active
  │     Fire: accreditation.verified (urgency: low)
  │
  ├── Registry returns: status = In Process (was Authorized)
  │     Status changed → MISMATCH
  │     Fire: accreditation.status_changed (urgency: high)
  │     Payload: {from: authorized, to: in_process, external_source: fedramp_marketplace}
  │     DCM action: accreditation status → pending_review
  │     Platform Admin notified — human must review and decide: suspend or retain
  │
  ├── Registry returns: status = Revoked
  │     Fire: accreditation.status_changed (urgency: critical)
  │     DCM action: accreditation status → revoked immediately
  │     Accreditation Gap triggered for all affected providers
  │     Recovery Policy evaluated
  │
  ├── Registry returns: 404 / not_found
  │     May indicate ID change or deregistration
  │     Fire: accreditation.registry_mismatch (urgency: high)
  │     Increment verification_failure_count
  │     Platform Admin notified to verify external_registry_id is correct
  │
  └── Registry unreachable (timeout, 5xx)
        Update: last_result: registry_unavailable
        Increment verification_failure_count
        If count >= verification_failure_threshold:
          Fire: accreditation.verification_stale (urgency: medium)
        Do NOT change accreditation status on registry failure alone
        (conservative: prefer false negative over false positive revocation)
```

### 5.2 Tier 2 — Document Currency Verification (SOC 2, PCI DSS AoC)

```
Verification cycle (default: P7D):
  │
  ▼ Fetch document from certificate_ref or audit_report_ref URL
  │
  ├── PDF: extract creation_date from PDF metadata
  │         or parse report header for "Report Date: YYYY-MM-DD"
  │
  ├── HTML report: parse structured date field
  │
  └── Fallback: flag for manual review if date cannot be extracted
  
  ▼ Compare document date to max_age threshold (default P365D):
  │
  ├── Within threshold → update last_checked_at, last_document_date
  │                      Fire: accreditation.verified (urgency: low)
  │
  └── Beyond threshold → Fire: accreditation.document_expired (urgency: high)
                          Platform Admin notified: new report needed
                          Accreditation status → pending_renewal
```

### 5.3 Tier 3 — Contract Webhook (HIPAA BAA, DoD IL)

```
Contract management system fires webhook to DCM:
  POST /api/v1/admin/accreditations/{uuid}/contract-event
  
  Payload:
  {
    "contract_id": "<external-id>",
    "event_type": "signed | amended | terminated | renewal_due | renewed",
    "effective_date": "<ISO 8601>",
    "details": { ... contract-system-specific fields ... }
  }
  
  DCM processes:
  ├── signed   → accreditation status: active (if was pending)
  ├── amended  → accreditation status: pending_review; Platform Admin notified
  ├── terminated → accreditation status: revoked; Accreditation Gap triggered
  ├── renewal_due → notification to Compliance Team (urgency: medium)
  └── renewed  → accreditation status: active; expires_at updated; last_verified_at updated
```

### 5.4 Stale Verification Handling

Regardless of tier, when `last_checked_at` is older than `stale_after`:

```
stale_action: warn     → Fire: accreditation.verification_stale (urgency: low)
                          No change to accreditation status
                          
stale_action: suspend  → Fire: accreditation.verification_stale (urgency: high)
                          Accreditation status → suspended
                          Accreditation Gap triggered (gap_type: suspended)
                          Platform Admin must manually verify and reactivate
                          
stale_action: escalate → Fire: accreditation.verification_stale (urgency: critical)
                          Escalation chain notified (Compliance Team + Platform Admin)
                          No automatic status change
                          If not resolved within escalation_window: → suspend
```

`stale_action` defaults by profile: `warn` for dev/standard, `suspend` for prod, `escalate` for fsi/sovereign.

---

## 6. New Event Types (additions to doc 33)

These events are added to the event catalog as domain `accreditation.*`:

| Event Type | Urgency | Description | Key Payload Fields |
|-----------|---------|-------------|-------------------|
| `accreditation.verified` | low | Periodic external confirmation — accreditation still active | accreditation_uuid, framework, registry, checked_at |
| `accreditation.status_changed` | high or critical | External registry shows a different status than DCM records | accreditation_uuid, framework, from_status, to_status, external_source |
| `accreditation.registry_mismatch` | high | External registry cannot find the accreditation by its external_registry_id | accreditation_uuid, external_registry_id, registry, failure_detail |
| `accreditation.verification_stale` | varies | last_checked_at exceeds stale_after threshold | accreditation_uuid, last_checked_at, stale_after, stale_action_taken |
| `accreditation.document_expired` | high | Evidence document older than max_age threshold | accreditation_uuid, framework, document_url, document_date, max_age |
| `accreditation.contract_event` | varies | Contract management webhook received | accreditation_uuid, contract_event_type, contract_id, effective_date |
| `accreditation.expiry_approaching` | medium | Approaching expires_at within renewal_warning_before (supplement to existing TTL-based check) | accreditation_uuid, expires_at, days_remaining |

---

## 7. Accreditation Record Additions to doc 26

The following fields are added to the accreditation record structure in doc 26 Section 3.3.
These are non-breaking additions — existing records without these fields default to `tier: expiry_only`.

```yaml
# Additions to existing accreditation record (doc 26 Section 3.3)

  verification:
    tier: external_registry | document_currency | contract_webhook | expiry_only
    
    # For external_registry tier:
    registry_api:
      provider: fedramp | stateramp | cmmc_ab | iaf_certsearch | pci_ssc_qsa | custom
      lookup_key: <string>           # value to use as query key in registry
      poll_interval: P1D             # ISO 8601 duration; how often Monitor checks
      last_checked_at: <ISO 8601>
      last_result: confirmed_active | status_changed | registry_unavailable | not_found | pending
    
    # For document_currency tier:
    document_check:
      document_url: <URL>            # usually same as certificate_ref or audit_report_ref
      max_age: P365D                 # maximum acceptable document age
      date_extraction_method: pdf_metadata | report_header_parse | manual
      last_checked_at: <ISO 8601>
      last_document_date: <ISO 8601>
    
    # For contract_webhook tier:
    contract_webhook:
      contract_system: docusign | ironclad | agiloft | custom
      contract_id: <string>          # ID in the contract management system
      webhook_configured: true | false
      last_event_at: <ISO 8601>
    
    # Shared across all tiers:
    stale_after: P7D                 # max acceptable gap between verifications
    stale_action: warn | suspend | escalate
    verification_failure_count: 0
    verification_failure_threshold: 3
```

---

## 8. Impact on Scoring Model (doc 29)

The Scoring Model's Signal 5 (Provider Accreditation Richness, doc 29 Section 4.5) is
enhanced with a verification currency dimension. An accreditation that has been externally
verified recently is worth more than one that has only ever been manually submitted.

```yaml
# Addition to accreditation_weights in doc 29:
verification_multipliers:
  # Applied to each accreditation's weight based on verification currency
  external_registry_verified_within_P1D:  1.0    # full weight
  external_registry_verified_within_P7D:  0.9    # slight discount
  document_verified_within_P30D:          0.85
  contract_webhook_active:                0.9
  expiry_only_no_external_check:          0.7    # meaningful discount
  verification_stale:                     0.4    # significant discount
  verification_failed_threshold_reached:  0.1    # near-zero weight
```

This means a provider with a FedRAMP High accreditation that was externally verified
yesterday scores higher in placement tie-breaking than a provider with the same
accreditation whose verification check has been stale for 30 days.

---

## 9. Admin API Additions

```
# List all accreditations with their current verification status
GET /api/v1/admin/accreditations
  ?verification_status=stale|failed|confirmed|pending
  &framework=fedramp_high|iso_27001|...
  &subject_uuid={provider_uuid}
  page_size=50&page_token=...

# Trigger immediate re-verification of a specific accreditation
POST /api/v1/admin/accreditations/{accreditation_uuid}:verify

Response 200 — returns Operation:
  {
    "name": "/api/v1/operations/{uuid}",
    "done": false,
    "metadata": {
      "stage": "VERIFICATION_INITIATED",
      "accreditation_uuid": "{uuid}",
      "verification_tier": "external_registry"
    }
  }

# Register a contract webhook endpoint for a BAA or DoD IL accreditation
POST /api/v1/admin/accreditations/{accreditation_uuid}:configure-webhook
  {
    "contract_system": "docusign",
    "contract_id": "abc-def-123",
    "webhook_secret": "<hmac-secret>"
  }

# Inbound webhook endpoint (called by contract management systems)
POST /api/v1/admin/accreditations/{accreditation_uuid}/contract-event
  Authorization: Bearer <contract-webhook-credential>
  {
    "contract_event_type": "terminated",
    "effective_date": "2026-04-01",
    "contract_id": "abc-def-123",
    "details": {}
  }
```

---

## 10. Deployment and Configuration

The Accreditation Monitor is deployed as a standalone container alongside the DCM control plane. It requires:

- Network access to external registries (FedRAMP, CMMC AB, IAF CertSearch, PCI SSC)
- Network access to the DCM API Gateway (to push accreditation events)
- Access to `certificate_ref` and `audit_report_ref` document URLs (for Tier 2 checks)
- Inbound webhook endpoint (for Tier 3 contract system integrations)

**Air-gapped / sovereign deployments:** For deployments without external internet access, the Accreditation Monitor operates in Tier 4 (expiry-only) mode by default for all frameworks. Tier 2 checks can still work if documents are stored on internal object storage (certificate_ref points to an internal URL). Tier 3 contract webhooks work if the contract management system is internal. Tier 1 registry checks are disabled — a manual verification workflow applies instead, with platform admins periodically updating `last_verified_at` after out-of-band confirmation.

```yaml
accreditation_monitor_config:
  # Per-registry enable/disable
  registries:
    fedramp:
      enabled: true
      poll_interval: P1D
      timeout: PT30S
    cmmc_ab:
      enabled: true
      poll_interval: P7D
    iaf_certsearch:
      enabled: true
      poll_interval: P7D
    stateramp:
      enabled: false               # enable if state/local gov providers present
  
  # Document currency checks
  document_checks:
    enabled: true
    default_max_age: P365D
    extraction_timeout: PT60S
  
  # Air-gapped mode
  air_gapped_mode: false
  air_gapped_fallback: expiry_only | manual_workflow
  
  # Global escalation
  global_stale_after: P7D
  global_failure_threshold: 3
  escalation_contact:
    service_provider_uuid: <uuid>
    urgency: critical
```

---

## 11. System Policies

| Policy | Rule |
|--------|------|
| `ACM-001` | The Accreditation Monitor is the authoritative source for `last_verified_at` on accreditation records. Platform admins may update it manually only when the Monitor is unavailable or in air-gapped mode — all manual updates require a justification reason stored in the audit trail. |
| `ACM-002` | An accreditation status change detected by the Monitor (external registry reports different status than DCM) does not automatically revoke the accreditation. It fires `accreditation.status_changed` and sets status to `pending_review`. A platform admin must confirm the change. The exception: if the external status is `Revoked` or `Terminated`, DCM immediately sets accreditation status to `revoked` without waiting for admin confirmation. |
| `ACM-003` | Verification failure (registry unreachable, document inaccessible) does not revoke an accreditation. The Monitor increments `verification_failure_count`. At `verification_failure_threshold`, it fires `accreditation.verification_stale` and applies `stale_action`. Failure itself does not constitute a gap — only confirmed negative status does. |
| `ACM-004` | Accreditations in `sovereign` and `fsi` profiles must have `verification.tier` declared at a level of `document_currency` or above. `expiry_only` is not permitted for sovereign/fsi accreditations unless `air_gapped_mode: true` is explicitly configured. |
| `ACM-005` | The `verification_multipliers` in the Scoring Model (Signal 5) apply to all accreditations, including those submitted before the Accreditation Monitor was deployed. Legacy accreditations with no `last_checked_at` are treated as `verification_stale` and weighted at the stale multiplier (0.4) until the Monitor performs its first check. |
| `ACM-006` | Inbound contract webhooks (Tier 3) must authenticate using a provider callback credential issued at accreditation configuration time. Unauthenticated webhook calls are rejected with `401 Unauthorized` and generate an audit record. |
| `ACM-007` | All verification events (`accreditation.*`) are written to the Audit Store regardless of outcome. There are no silent verifications — every check, success or failure, has an audit record. |
| `ACM-008` | In air-gapped mode, the Monitor operates in Tier 4 for registries it cannot reach. It does not repeatedly attempt unreachable external registries. After `air_gapped_retry_interval` (default P30D), it retries once to detect if network access has been restored. |

---

## 12. Relationship to Existing Architecture

### doc 26 — Accreditation and Authorization Matrix
The Accreditation Monitor extends but does not replace the accreditation lifecycle model in doc 26. The existing `proposed → active → expired/revoked` lifecycle is preserved. The Monitor adds automated transitions into `pending_review` and `pending_renewal` states, and provides the data that drives the existing `ACCREDITATION_GAP` logic.

### doc 27 — Governance Matrix
The Governance Matrix already evaluates accreditation status as part of Check 3 of the five-check boundary model. The Monitor improves the quality of that check: instead of relying solely on the declared `expires_at` date, the Governance Matrix now has access to externally verified current status via `last_verified_at` and `last_result`.

### doc 29 — Scoring Model
The `verification_multipliers` addition to Signal 5 (Provider Accreditation Richness) means placement decisions can prefer providers whose accreditations have been recently externally verified over those relying on self-declared or stale verifications. This is a conservative, progressive enhancement — it does not block placement, only refines tie-breaking.

### doc 33 — Event Catalog
Seven new `accreditation.*` events are added (Section 6 of this document). These follow the same envelope and urgency model as all other DCM events.

### doc 40 — Standards Catalog
The Accreditation Monitor is the operational implementation of the standards catalog's compliance framework entries. The standards catalog says *what* DCM recognizes; the Accreditation Monitor says *how* DCM verifies that recognition is still current.

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*

---

## 13. Accreditation Governance Enforcement

> **Implements contracts defined in UDLM**:
> [udlm/governance/accreditation-and-authorization-matrix.md](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md).
> UDLM defines the accreditation model, lifecycle, and authorization matrix.
> This section operationalizes the governance enforcement DCM applies on
> top of the Accreditation Monitor.

### 13.1 Accreditation gap response

When a required accreditation becomes missing, expired, or revoked, DCM
enters an Accreditation Gap state for the affected provider:

```yaml
accreditation_gap_record:
  uuid: <uuid>
  provider_uuid: <uuid>
  required_framework: hipaa
  required_for: [phi data fields in active requests]
  gap_type: missing | expired | revoked | suspended | verification_stale
  detected_at: <ISO 8601>
  severity: critical                    # accreditation gaps are always high or critical
  affected_entity_uuids: [<list>]       # entities currently hosted at this provider
  policy_response: <from Recovery Policy>
  # Default: NOTIFY_AND_WAIT for fsi/sovereign; ESCALATE for standard/prod
```

The Recovery Policy evaluation runs through the standard
[`../convergence-engine/recovery-and-retry.md`](../convergence-engine/recovery-and-retry.md)
mechanism — accreditation gaps are first-class recovery triggers.

### 13.2 Authorization evaluation at runtime

The Governance Matrix evaluator (see
[`../convergence-engine/policy-evaluation.md`](../convergence-engine/policy-evaluation.md))
consults Accreditation Monitor data on every outbound interaction. The
matrix evaluator:

1. Resolves required accreditation from the data axis (e.g., PHI requires
   HIPAA BAA)
2. Queries the target's active accreditations via the Accreditation Monitor
3. Verifies the accreditation is current and not suspended (via
   `last_verified_at` and `last_result`)
4. Returns ALLOW / DENY / STRIP_FIELD per the matrix rule

The Accreditation Monitor's verification currency (Section 8) feeds into
matrix evaluation: an accreditation with stale verification produces a
weaker effective trust than one externally verified yesterday.

### 13.3 DCM deployment accreditation

DCM deployments themselves can carry accreditations (a FedRAMP-authorized
DCM deployment, for example). DCM enforces:

- `subject_type: dcm_deployment` accreditations registered as standard
  accreditation artifacts
- Federation peer DCMs verify each other's deployment accreditation before
  accepting federation messages (see
  [`../runtime-features/federation-runtime.md`](../runtime-features/federation-runtime.md))
- Accreditation Monitor verifies deployment accreditations on the same
  schedule as provider accreditations

### 13.4 Profile-governed accreditation constraints

```yaml
accreditation_profile_config:
  minimal:
    verification_tier_minimum: expiry_only
    air_gapped_fallback: expiry_only
    stale_action_default: warn

  dev:
    verification_tier_minimum: expiry_only
    stale_action_default: warn

  standard:
    verification_tier_minimum: document_currency
    stale_action_default: warn

  prod:
    verification_tier_minimum: document_currency
    stale_action_default: escalate

  fsi:
    verification_tier_minimum: external_registry
    # ACM-004: expiry_only NOT permitted unless air_gapped_mode: true
    stale_action_default: suspend

  sovereign:
    verification_tier_minimum: external_registry
    stale_action_default: suspend
```

These are enforced at accreditation registration: an accreditation with
`tier: expiry_only` in `fsi`/`sovereign` profile is rejected unless
`air_gapped_mode: true` is explicitly configured (`ACM-004`).
