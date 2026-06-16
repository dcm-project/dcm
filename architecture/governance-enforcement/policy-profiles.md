---
Document Status: ✅ Complete
Document Type: Architecture Reference — Policy Organization
Maps to: udlm/observability/universal-groups.md
---

# DCM Data Model — Policy Organization: Groups, Profiles, and External Policy Evaluators

> **Implements contracts defined in UDLM**:
> [udlm/observability/universal-groups.md](https://github.com/croadfeldt/udlm/blob/main/observability/universal-groups.md).
> UDLM defines the Universal Group Model — composable, cross-type group
> membership and the profile/collection grouping contract. DCM operationalizes
> Policy Groups (`group_class: policy_collection`) and Policy Profiles
> (`group_class: policy_profile`) as concrete expressions of that model, plus
> the external policy evaluator integration.

> **Universal Group Model:** Policy Groups (`group_class: policy_collection`) and Policy Profiles (`group_class: policy_profile`) are expressions of the [Universal Group Model](https://github.com/croadfeldt/udlm/blob/main/observability/universal-groups.md). The structures defined in this document remain authoritative for policy-specific behavior; the universal model adds composability, cross-type membership, and the ability to include policy groups within composite groups.

**Document Status:** ✅ Complete  
**Related Documents:** [Scoring Model](../convergence-engine/scoring.md) | [Context and Purpose](https://github.com/croadfeldt/udlm/blob/main/foundations/context-and-purpose.md) | [Data Layers and Assembly](https://github.com/croadfeldt/udlm/blob/main/foundations/layering-and-versioning.md) | [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) | [data stores](https://github.com/croadfeldt/udlm/blob/main/contracts/storage-providers.md)

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: DATA + POLICY**
>
> Data: Policy Group and Profile artifacts. Policy: concern types and composition



---

> **Standards and Compliance Reference:** See [Standards and Compliance Catalog](https://github.com/croadfeldt/udlm/blob/main/reference/standards-catalog.md) for the complete mapping of compliance frameworks (HIPAA, PCI DSS, FedRAMP, NIST SP 800-53, GDPR, DoD IL4) to DCM profiles and system requirements.

## 1. Purpose

DCM's Policy Engine is powerful — but power without usability is a barrier to adoption. This document defines the **policy organization model**: the structures that make DCM easy to configure correctly for any use case, from a home lab evaluation to a sovereign financial services deployment.

Three concepts work together:

- **Policy Groups** — cohesive collections of policies addressing a single identifiable concern (a technology, a compliance standard, a sovereignty requirement, a business process)
- **Policy Profiles** — complete DCM configurations for a specific use case, composed of Policy Groups
- **External Policy Evaluators** — external authoritative sources that supply policies directly into DCM, extending the provider model to its fifth type

The relationship is compositional:

```
Policy Profile     — complete use-case configuration
  │  composed of
  ▼
Policy Groups      — single-concern policy collections
  │  composed of
  ▼
Policies           — individual Transformation / Validation / GateKeeper rules
  │  optionally sourced from
  ▼
External Policy Evaluators   — external authoritative policy sources
```

---

## 1a. Design Priority Order in Policy Profiles

Profiles implement the DCM design priority order (see [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md)):

1. **Security:** Profile defaults implement security correctly. Lower profiles have less strict enforcement — not absent security.
2. **Ease of use:** Profile defaults minimize configuration burden. `standard` profile should work for most deployments without customization.
3. **Extensibility:** Profiles compose with compliance domain overlays. Organizations add compliance requirements additively without rewriting base configuration.
4. **Fit for purpose:** Every profile must support the complete DCM lifecycle.

**The `minimal` profile is not "security optional"** — it is the security model with minimal operational overhead. All security properties are present; thresholds and automation levels are relaxed.

---

## 1b. Policy Authorship — Federated Contribution Model

Policies in DCM are not exclusively authored by platform admins. The DCM federated contribution model enables all actor types to author policies within their permitted domain scope:

- **Platform admins** — all domains, all policy types
- **Consumers / Tenant admins** — tenant domain policies (GateKeeper, Transformation, Recovery, Lifecycle, Orchestration Flow, Governance Matrix rules scoped to their Tenant)
- **Service Providers** — provider-domain GateKeeper and Validation policies for their resource types
- **Peer DCM instances** — policy templates contributed through verified federation relationships

This is not a special case — it is the standard GitOps PR model applied to all contributor types. Consumer-authored policies go through the same lifecycle (developing → proposed → active) with appropriate review requirements per the active profile. See [Federated Contribution Model](https://github.com/croadfeldt/udlm/blob/main/governance/federated-contribution-model.md) for the complete specification.

---

## 2. Policy Groups
## 1a. Two-Dimensional Profile Model


### 1a.0 Profile — One Posture, Multiple Compliance Domains

**A DCM deployment runs exactly one Deployment Posture and zero or more Compliance Domain Groups simultaneously.** This is the complete profile model. No new concept is needed.

```
Active DCM Governance = one Deployment Posture + [zero or more Compliance Domains]

Examples:
  prod + hipaa                         ← healthcare production
  prod + hipaa + gdpr                  ← EU healthcare production  
  sovereign + fedramp-high + dod-il5   ← classified federal
  standard                             ← general enterprise, no compliance overlay
  dev + hipaa                          ← healthcare development (hipaa policies active,
                                          but operational cost reduced by dev posture)
```

**Deployment Postures are mutually exclusive** — you cannot be both `prod` and `dev`. One posture governs the operational characteristics of the entire DCM deployment.

**Compliance domains are additive** — HIPAA + FSI is valid and common. Each compliance domain group adds its own set of policies and constraints on top of the posture. They do not conflict with each other at the domain level (they govern different aspects of data handling); they may produce policy conflicts at the field level, which are resolved through the standard policy conflict resolution process.

**The dev posture and compliance domains** — applying `dev` posture to a HIPAA-scoped deployment does not remove HIPAA obligations. It relaxes the *operational cost* of meeting them: less redundancy, shorter retention windows where permitted, advisory enforcement where HIPAA allows flexibility. The HIPAA compliance domain group remains active and its mandatory controls remain enforced.

**Modules vs Profiles** — DCM uses both concepts with distinct meanings:
- A **Profile** is a governance configuration: it declares how DCM behaves and what operational and compliance requirements apply.
- A **Module** is a capability extension: it adds new functions to DCM (e.g., a HIPAA record validator, a custom resource type). Modules are not profiles and do not configure DCM behavior — they extend what DCM can do.


### 1a.1 The Gap in the Original Model

The original six profiles (minimal → sovereign) are organized around **deployment posture** — how strict, how redundant, how governed. But organizations need compliance governance that is orthogonal to posture. A healthcare organization needs HIPAA controls regardless of whether they deploy at `standard` or `sovereign` posture. A payment processor needs PCI-DSS regardless of their redundancy profile.

The new model makes compliance a first-class dimension that composes with posture:

```
Complete Profile = Deployment Posture Group + Compliance Domain Group(s)
```

### 1a.2 Dimension 1 — Deployment Posture Groups

Posture groups govern how the DCM infrastructure itself behaves — redundancy, enforcement strictness, audit retention, tenancy model, cross-tenant defaults. These are the vertical axis from least to most governed.

| Group Handle | Posture | Key Behaviors |
|-------------|---------|--------------|
| `system/group/posture-minimal` | Minimal | Advisory only; single instance; no redundancy |
| `system/group/posture-dev` | Development | Warn-not-block; basic logging; ephemeral defaults |
| `system/group/posture-standard` | Standard | Full enforcement; 3-replica; explicit cross-tenant |
| `system/group/posture-prod` | Production | Full enforcement + SLA; geo-replicated; cost governance |
| `system/group/posture-hardened` | Enterprise Hardened | 5-replica; 7-year audit; hard tenancy; dual approval |
| `system/group/posture-sovereign` | Sovereign | Air-gap; deny_all cross-tenant; 10-year audit; signed bundles |

### 1a.3 Dimension 2 — Compliance Domain Groups

Compliance domain groups govern what data handling, audit, and control requirements apply to resources managed by DCM. Multiple compliance domains can apply simultaneously.

| Group Handle | Domain | Key Controls |
|-------------|--------|-------------|
| `system/group/compliance-fsi` | Financial Services | Basel III, SOX, Dodd-Frank financial controls |
| `system/group/compliance-pci-dss` | Payment Card | PCI-DSS v4 — payment card industry |
| `system/group/compliance-hipaa` | Healthcare | HIPAA/HITECH PHI handling and audit |
| `system/group/compliance-fedramp-moderate` | US Federal Moderate | FedRAMP Moderate — NIST 800-53 Moderate baseline |
| `system/group/compliance-fedramp-high` | US Federal High | FedRAMP High — NIST 800-53 High baseline |
| `system/group/compliance-dod-il2` | DoD IL2 | Public/unclassified defense data |
| `system/group/compliance-dod-il4` | DoD IL4 | Controlled Unclassified Information (CUI) |
| `system/group/compliance-dod-il5` | DoD IL5 | National Security Systems non-classified |
| `system/group/compliance-dod-il6` | DoD IL6 | Classified — maximum sovereign posture |
| `system/group/compliance-government` | Government General | General government/public sector controls |
| `system/group/compliance-gdpr` | EU Data Protection | GDPR data residency and rights |
| `system/group/compliance-iso27001` | ISO 27001 | Information security management |
| `system/group/compliance-nist-800-53` | NIST 800-53 | NIST security control framework |
| `system/group/compliance-soc2` | SOC 2 | Service organization controls |
| `system/group/compliance-nerc-cip` | Critical Infrastructure | Energy/utilities NERC CIP |
| `system/group/compliance-sovereign` | Sovereign/Classified | Sovereign deployment, air-gap, classified |

### 1a.4 Compliance Domain Group Contents

#### `system/group/compliance-hipaa`

HIPAA/HITECH controls for Protected Health Information (PHI):
- PHI field classification enforcement (fields containing PHI must be tagged `phi: true`)
- PHI access control (only roles with `phi_authorized: true` may access PHI-tagged fields)
- Audit retention: P6Y minimum (HIPAA requires 6 years from creation or last use)
- Encryption at rest: AES-256 required for all PHI storage
- Transmission security: TLS 1.3 minimum for PHI in transit
- Breach notification workflow: sovereignty_violation_record triggers HIPAA breach assessment
- Business Associate Agreement (BAA) tracking: providers handling PHI must declare `baa_in_place: true` in sovereignty_declaration
- Right to Access: consumer data export capability required for PHI entities
- Minimum Necessary standard: data_request_spec on Mode 4 providers limited to minimum PHI fields

#### `system/group/compliance-government`

General government and public sector controls:
- Data classification mandatory on all resources (classification_level field required)
- Cross-boundary controls: data cannot cross classification levels without explicit policy
- Audit retention: P10Y minimum
- Air-gap capability required for Sensitive compartments
- Actor authentication must declare clearance level in external_identity claims
- All provider sovereignty_declarations must declare government_access_risk

#### `system/group/compliance-fedramp-moderate`

FedRAMP Moderate authorization controls:
- NIST 800-53 Rev 5 Moderate baseline implemented as policy group
- FedRAMP-authorized provider preference injected as placement constraint
- Continuous monitoring: drift detection mandatory; P24H maximum drift resolution window
- Incident response: webhook required for security events (audit.chain_break, drift.escalated)
- POA&M tracking: `poam_status` field in status_metadata on all policy artifacts
- Boundary protection: explicit ingress/egress control documentation

#### `system/group/compliance-dod-il4`

DoD Impact Level 4 — Controlled Unclassified Information:
- Inherits compliance-fedramp-moderate
- CUI handling markers on all data fields containing controlled information
- Sovereign posture within US jurisdiction boundary
- Provider sovereignty_declaration must exclude foreign sub-processors
- CMMC Level 2 cyber hygiene controls

#### `system/group/compliance-sovereign`

Sovereign and classified deployment controls:
- All data must remain within declared sovereignty boundary
- Air-gap capability: provider air_gap_capable: true required
- Signed bundle import only — no live registry connectivity
- deny_all cross-tenant cross-boundary data flows
- Hardware security module (HSM) required for key management
- Audit records: 10-year retention; cryptographic signing required

### 1a.5 Profile Composition Model

The six built-in profiles become explicit posture+compliance compositions:

```yaml
system/profile/minimal:
  policy_groups: [system/group/posture-minimal]

system/profile/dev:
  extends: system/profile/minimal
  policy_groups: [system/group/posture-dev]

system/profile/standard:
  extends: system/profile/dev
  policy_groups: [system/group/posture-standard]

system/profile/prod:
  extends: system/profile/standard
  policy_groups: [system/group/posture-prod]

system/profile/fsi:
  extends: system/profile/prod
  policy_groups:
    - system/group/posture-hardened
    - system/group/compliance-fsi
    - system/group/compliance-pci-dss
    - system/group/compliance-iso27001

system/profile/sovereign:
  extends: system/profile/fsi
  policy_groups:
    - system/group/posture-sovereign
    - system/group/compliance-sovereign
```

### 1a.6 DCM Built-In Extended Profiles

In addition to the six core profiles, DCM ships extended profiles for common compliance domains:

```yaml
system/profile/hipaa-prod:
  extends: system/profile/prod
  policy_groups:
    - system/group/compliance-hipaa
    - system/group/compliance-iso27001
  description: "Production infrastructure with HIPAA/HITECH compliance"

system/profile/hipaa-sovereign:
  extends: system/profile/sovereign
  policy_groups:
    - system/group/compliance-hipaa
  description: "Sovereign deployment with HIPAA/HITECH compliance — highest healthcare posture"

system/profile/fedramp-moderate:
  extends: system/profile/prod
  policy_groups:
    - system/group/compliance-fedramp-moderate
    - system/group/compliance-nist-800-53
  description: "FedRAMP Moderate authorized deployment"

system/profile/fedramp-high:
  extends: system/profile/sovereign
  policy_groups:
    - system/group/compliance-fedramp-high
    - system/group/compliance-nist-800-53
  description: "FedRAMP High authorized deployment"

system/profile/government:
  extends: system/profile/prod
  policy_groups:
    - system/group/compliance-government
    - system/group/compliance-nist-800-53
  description: "General government and public sector deployment"

system/profile/dod-il4:
  extends: system/profile/sovereign
  policy_groups:
    - system/group/compliance-dod-il4
    - system/group/compliance-fedramp-high
    - system/group/compliance-nist-800-53
  description: "DoD Impact Level 4 — Controlled Unclassified Information"

system/profile/dod-il5:
  extends: system/profile/dod-il4
  policy_groups:
    - system/group/compliance-dod-il5
  description: "DoD Impact Level 5 — National Security Systems non-classified"

system/profile/dod-il6:
  extends: system/profile/dod-il5
  policy_groups:
    - system/group/compliance-dod-il6
    - system/group/compliance-sovereign
  description: "DoD Impact Level 6 — Classified"
```

### 1a.7 Organization Custom Profiles — Composition Examples

```yaml
# Healthcare with federal cloud authorization
org/profile/hipaa-fedramp:
  extends: system/profile/fedramp-moderate
  policy_groups:
    - system/group/compliance-hipaa
  description: "Healthcare workloads on FedRAMP Moderate platform"

# Multi-compliance financial + healthcare
org/profile/fsi-hipaa:
  extends: system/profile/fsi
  policy_groups:
    - system/group/compliance-hipaa
  description: "FSI-grade deployment for organizations managing both financial and health data"

# Tenant-level compliance override — platform is standard; this Tenant is PCI-scoped
# (declared in tenant_config — not profile)
tenant_compliance_overlay:
  active_profile: system/profile/standard    # platform posture
  compliance_groups:
    - system/group/compliance-pci-dss        # this Tenant handles payment cards
    - system/group/compliance-hipaa          # this Tenant also handles PHI
  # Other Tenants on same platform have standard posture, no compliance overlay
```

### 1a.8 Compliance at Tenant Level

Compliance domain groups may apply at Tenant level — different Tenants on the same DCM deployment can have different compliance domains:

```yaml
tenant_config:
  active_profile: system/profile/prod        # posture from platform
  compliance_groups:
    - system/group/compliance-hipaa          # this Tenant handles PHI
    - system/group/compliance-pci-dss        # this Tenant processes payments
```

This is the critical capability: **one DCM deployment, multiple compliance postures per Tenant**. A hospital system can run a single DCM with: clinical Tenants (HIPAA), billing Tenants (HIPAA + PCI-DSS), and administrative Tenants (standard) — all on the same platform profile.

### 1a.9 System Policies — Profile Composition

| Policy | Rule |
|--------|------|
| `PROF-001` | Profiles compose a Deployment Posture Group with zero or more Compliance Domain Groups. Posture groups govern DCM infrastructure behavior. Compliance domain groups govern data handling, audit, and control requirements. |
| `PROF-002` | Compliance Domain Groups may be applied at platform level (all Tenants) or Tenant level (specific Tenants). Tenant-level compliance groups are additive — they do not replace platform-level groups. |
| `PROF-003` | DCM ships built-in Compliance Domain Groups for: FSI, PCI-DSS, HIPAA/HITECH, FedRAMP Moderate, FedRAMP High, DoD IL2-IL6, Government, GDPR, ISO 27001, NIST 800-53, SOC2, NERC-CIP, and Sovereign/Classified. Organizations extend these groups or compose them into custom profiles. |
| `PROF-004` | The `implementation_posture` concern_type Policy Groups (provenance model, auth simplicity, deployment complexity) are independent of compliance domain — organizations select their implementation posture separately from their compliance requirements. |

---


### 2.1 Definition

A **Policy Group** is a versioned, cohesive collection of policies that together address a **single identifiable concern**. The group is the unit of reuse — activate a group to enable a concern, not individual policies.

```yaml
policy_group:
  artifact_metadata:
    uuid: <uuid>
    handle: "system/group/pci-dss"
    version: "1.2.0"
    status: active
    owned_by:
      display_name: "DCM Project Team"
      notification_endpoint: <endpoint>

  name: "PCI-DSS v4"
  description: >
    Policy group implementing PCI-DSS v4 controls relevant to
    DCM-managed infrastructure. Enforces encryption standards,
    network segmentation, access control, and audit requirements
    for resources in PCI scope.

  concern_type: compliance
  concern_tags: [pci-dss, financial, encryption, network-segmentation]
  extends: null   # or another group handle — inherits all parent policies

  # Source — locally authored or from a External Policy Evaluator
  source:
    type: <local | external>
    provider_uuid: <uuid — if external>
    provider_group_reference: <provider's identifier for this group>
    on_provider_update: <proposed | active>
    # proposed: provider updates require local review before activation
    # active:   provider updates activate immediately (trusted providers only)

  # Constituent policies
  policies:
    - policy_uuid: <uuid>
      handle: "system/gatekeeper/pci-encryption-aes256"
      description: "Enforce AES-256 on all PCI-scoped storage"
      placement_phase: pre
    - policy_uuid: <uuid>
      handle: "system/validation/pci-network-segmentation"
      description: "Validate network segment isolation for PCI resources"
      placement_phase: pre
    - policy_uuid: <uuid>
      handle: "system/transformation/pci-classification-inject"
      description: "Auto-inject PCI classification on scoped resources"
      placement_phase: pre
    - policy_uuid: <uuid>
      handle: "system/gatekeeper/pci-audit-retention"
      description: "Enforce 10-year audit retention for PCI evidence"
      placement_phase: pre

  # Activation scope — surgical application within a profile
  activation_scope:
    resource_types: []          # empty = all resource types
    tenant_tags: [pci-scope]    # only Tenants tagged pci-scope
    regions: []                 # empty = all regions

  # Conflict declarations
  conflicts_with:
    - group_handle: "system/group/dev-defaults"
      reason: "PCI requires blocking enforcement; dev-defaults uses warn-only"
      resolution: this_group_wins
```

### 2.2 Concern Types

| Type | Description | Examples |
|------|-------------|---------|
| `technology` | Policies specific to a technology or provider | kubevirt, openstack, kubernetes, vmware |
| `compliance` | Regulatory or standards compliance | pci-dss, iso-27001, nist-800-53, fedramp |
| `sovereignty` | Data residency, jurisdictional, air-gap | gdpr-eu, air-gap, data-residency-uk |
| `business` | Business process, cost, lifecycle governance | cost-governance, ephemeral-resources, chargeback |
| `operational` | Operational posture, defaults, SLAs | dev-defaults, hard-tenancy, sla-enforcement |
| `security` | Security controls and posture | data-classification, zero-trust, encryption-baseline |
| `implementation_posture` | Implementation complexity vs capability trade-offs | provenance-full-inline, provenance-deduplicated, single-instance-deployment, advisory-policies-only |

### 2.3 Group Inheritance

A Policy Group may extend another group — inheriting all its policies and overriding or adding to them:

```yaml
policy_group:
  handle: "org/group/pci-dss-extended"
  extends: "system/group/pci-dss"
  # Inherits all system/group/pci-dss policies
  # Additional policies added below are on top of the parent
  policies:
    - policy_uuid: <uuid>
      handle: "org/gatekeeper/our-pci-additional-control"
```

### 2.4 DCM Built-In Policy Groups

DCM ships the following policy groups as part of its standard distribution:

| Handle | Concern | Description |
|--------|---------|-------------|
| `system/group/core-minimal` | operational | Absolute minimum — UUID requirements, basic well-formedness |
| `system/group/dev-defaults` | operational | Warn-not-block, 90-day TTL defaults, single-auth cross-tenant |
| `system/group/ephemeral-resources` | business | TTL enforcement, auto-expiry, short-lived resource defaults |
| `system/group/audit-basic` | operational | Basic audit logging, 90-day retention |
| `system/group/audit-compliance` | compliance | Compliance-grade audit, configurable retention |
| `system/group/data-classification` | security | Data classification tagging and handling rules |
| `system/group/cost-governance` | business | Budget enforcement, cost attribution, TTL governance |
| `system/group/sla-enforcement` | operational | SLA tracking, availability commitments |
| `system/group/hard-tenancy` | operational | Full tenant isolation, deny_all cross-tenant default |
| `system/group/explicit-cross-tenant` | operational | Explicit cross-tenant authorization requirement (XTA-001 through XTA-005) |
| `system/group/zero-trust` | security | Zero-trust network and identity enforcement |
| `system/group/encryption-baseline` | security | AES-256 minimum, TLS 1.3, key rotation |
| `system/group/pci-dss` | compliance | PCI-DSS v4 controls |
| `system/group/gdpr-eu` | sovereignty | GDPR data residency and handling |
| `system/group/nist-800-53` | compliance | NIST 800-53 control implementation |
| `system/group/iso-27001` | compliance | ISO 27001 controls |
| `system/group/fedramp-moderate` | compliance | FedRAMP Moderate baseline |
| `system/group/air-gap` | sovereignty | Air-gapped deployment constraints |
| `system/group/fsi-audit` | compliance | Financial services audit retention (7-year minimum) |
| `system/group/lifecycle-ttl-enforcement` | operational | Lifecycle time constraint enforcement (LTC-001 through LTC-004) |
| `system/group/kubevirt` | technology | KubeVirt provider-specific policies |
| `system/group/openstack` | technology | OpenStack provider-specific policies |
| `system/group/vmware` | technology | VMware provider-specific policies |
| `system/group/provenance-full-inline` | implementation_posture | Model A — all provenance inline on entity records; simplest; highest storage cost |
| `system/group/provenance-deduplicated` | implementation_posture | Model B — content-addressed deduplication; recommended; 95-99% storage reduction; lossless |
| `system/group/provenance-tiered-archive` | implementation_posture | Model C — hot/warm/cold tiers; balances cost and access speed |
| `system/group/provenance-deduplicated-tiered` | implementation_posture | Model B+C — maximum efficiency for very large-scale deployments |

---

## 3. Policy Profiles

### 3.1 Definition

A **Policy Profile** is a named, versioned, curated composition of Policy Groups that together configure DCM for a specific use case. Activating a profile is the primary configuration mechanism — most deployments should activate a profile and then add organization-specific groups on top rather than configuring policies individually.

```yaml
policy_profile:
  artifact_metadata:
    uuid: <uuid>
    handle: "system/profile/fsi"
    version: "1.0.0"
    status: active
    owned_by:
      display_name: "DCM Project Team"

  name: "FSI Production"
  description: >
    Policy profile for Financial Services production deployments.
    Enforces hard tenancy, regulatory-grade audit retention,
    full sovereignty controls, and explicit cross-tenant authorization.

  target_use_case: fsi_production
  extends: "system/profile/prod"   # inherits all prod groups + overrides

  enforcement_summary:
    tenancy: hard_tenancy_required
    audit_retention_years: 7
    sovereignty: full
    cross_tenant_default: explicit_only
    policy_enforcement: blocking
    immutable_fields: [sovereignty_zone, classification_level, audit_retention]
    policy_version_pinning: permitted_with_elevation

  policy_groups:
    - group_handle: "system/group/fsi-audit"
    - group_handle: "system/group/pci-dss"
    - group_handle: "system/group/gdpr-eu"
    - group_handle: "system/group/hard-tenancy"
    - group_handle: "system/group/explicit-cross-tenant"
    - group_handle: "system/group/encryption-baseline"
```

### 3.2 DCM Built-In Profiles

DCM ships six profiles covering the spectrum from minimal to sovereign:

#### `system/profile/minimal` — Home Lab / Evaluation

```yaml
handle: "system/profile/minimal"
name: "Minimal"
extends: null
description: >
  Minimal configuration for home lab, local testing, and evaluation.
  Most controls advisory only. Single Tenant auto-created on first use.
  No audit requirements. No sovereignty enforcement.

enforcement_summary:
  tenancy: optional
  audit_retention: none
  sovereignty: none
  cross_tenant_default: allow_all
  policy_enforcement: advisory     # policies warn but do not block
  time_constraints: optional

auto_tenant:
  enabled: true
  default_tenant_handle: "default"
  # TEN-001 satisfied silently — no explicit Tenant declaration required

policy_groups:
  - group_handle: "system/group/core-minimal"
```

#### `system/profile/dev` — Development Environments

```yaml
handle: "system/profile/dev"
name: "Development"
extends: "system/profile/minimal"
description: >
  Development environment profile. Tenancy recommended but not blocking.
  Basic logging. Ephemeral resource defaults. Warn-not-block enforcement.

enforcement_summary:
  tenancy: recommended
  audit_retention: basic
  sovereignty: none
  cross_tenant_default: operational_only
  policy_enforcement: warn_only
  default_ttl: P90D              # dev resources default to 90-day TTL

policy_groups:
  - group_handle: "system/group/dev-defaults"
  - group_handle: "system/group/ephemeral-resources"
  - group_handle: "system/group/audit-basic"
```

#### `system/profile/standard` — General Enterprise Production

```yaml
handle: "system/profile/standard"
name: "Standard"
extends: "system/profile/dev"
description: >
  General enterprise production profile. Full policy enforcement.
  Tenancy required. Explicit cross-tenant authorization. Basic
  data classification. Compliance-grade audit.

enforcement_summary:
  tenancy: required
  audit_retention: compliance_grade
  sovereignty: configurable
  cross_tenant_default: explicit_only
  policy_enforcement: blocking

policy_groups:
  - group_handle: "system/group/data-classification"
  - group_handle: "system/group/audit-compliance"
  - group_handle: "system/group/explicit-cross-tenant"
  - group_handle: "system/group/encryption-baseline"
```

#### `system/profile/prod` — Production with SLA Requirements

```yaml
handle: "system/profile/prod"
name: "Production"
extends: "system/profile/standard"
description: >
  Production profile with SLA enforcement, cost governance, and
  full lifecycle constraint enforcement.

enforcement_summary:
  tenancy: required
  audit_retention: compliance_grade
  sovereignty: configurable
  cross_tenant_default: explicit_only
  policy_enforcement: blocking

policy_groups:
  - group_handle: "system/group/cost-governance"
  - group_handle: "system/group/sla-enforcement"
  - group_handle: "system/group/lifecycle-ttl-enforcement"
```

#### `system/profile/fsi` — Financial Services Production

```yaml
handle: "system/profile/fsi"
name: "FSI Production"
extends: "system/profile/prod"
description: >
  Financial services production. Hard tenancy. 7-year audit retention.
  Full sovereignty enforcement. PCI-DSS and GDPR compliance.

enforcement_summary:
  tenancy: hard_tenancy_required
  audit_retention_years: 7
  sovereignty: full
  cross_tenant_default: explicit_only
  policy_enforcement: blocking

policy_groups:
  - group_handle: "system/group/fsi-audit"
  - group_handle: "system/group/pci-dss"
  - group_handle: "system/group/gdpr-eu"
  - group_handle: "system/group/hard-tenancy"
```

#### `system/profile/sovereign` — Air-Gapped / Sovereign Deployments

```yaml
handle: "system/profile/sovereign"
name: "Sovereign"
extends: "system/profile/fsi"
description: >
  Maximum control profile for air-gapped, sovereign, and highest-security
  deployments. Complete tenant isolation. Zero external dependencies.
  Maximum audit and sovereignty enforcement.

enforcement_summary:
  tenancy: hard_tenancy_required
  audit_retention_years: 10
  sovereignty: maximum
  cross_tenant_default: deny_all
  policy_enforcement: blocking
  immutable_ceiling_on_all_sovereignty_fields: true

policy_groups:
  - group_handle: "system/group/air-gap"
  - group_handle: "system/group/zero-trust"
```

### 3.3 Profile Inheritance Chain

```
system/profile/sovereign
  extends: system/profile/fsi
    extends: system/profile/prod
      extends: system/profile/standard
        extends: system/profile/dev
          extends: system/profile/minimal
            extends: null (base)
```

Each level adds groups without replacing parent groups. An organization extending a DCM profile only needs to declare what differs:

```yaml
# Organization custom profile
org/profile/my-prod:
  extends: system/profile/prod
  policy_groups:
    - group_handle: "org/group/our-naming-conventions"
    - group_handle: "org/group/our-cost-centers"
    - group_handle: "system/group/iso-27001"    # add a DCM compliance group
```

### 3.4 Profile Activation

Profiles activate at three levels — more specific takes precedence:

```yaml
# DCM installation default
installation_config:
  default_profile: "system/profile/minimal"

# Platform-level (applies to all Tenants)
platform_config:
  active_profile: "system/profile/prod"
  minimum_tenant_profile: "system/profile/dev"   # Tenants cannot go below this
  maximum_tenant_profile: null                    # null = no ceiling

# Tenant-level override
tenant_config:
  active_profile: "system/profile/fsi"           # must be >= minimum_tenant_profile
```

**A Tenant cannot activate a profile less restrictive than the platform minimum.** A sovereign deployment can set `minimum_tenant_profile: system/profile/sovereign` — no Tenant can drop below that level.

### 3.5 Profile Conflict Resolution

When a profile is activated, DCM runs conflict detection across all constituent group policies — same ingestion conflict detection that layers use. Conflicts must be resolved before a profile is marked `active`.

Conflict resolution order:
1. **Explicit `conflicts_with` declarations** on groups — use declared resolution rule
2. **Priority schema** — higher numeric priority wins
3. **Domain authority** — `system` beats `platform` beats `tenant`
4. **Unresolved** — profile activation fails with detailed conflict report

### 3.6 Profile Shadow Validation

When a profile is in `proposed` status, all its constituent policies run in shadow mode — the same proposed policy shadow execution model. The Validation Dashboard shows the aggregate impact across all policies in the profile before activation. This enables safe preview of what a profile upgrade would do to an existing deployment.

---

## 4. Policy Evaluation Modes

DCM supports two policy evaluation modes. The distinction is whether DCM or an external system performs the evaluation — not how policies are delivered to the evaluator.

### 4.1 Internal Mode — DCM Evaluates

In Internal mode, the Policy Manager evaluates all policies using its embedded OPA engine. Policies can arrive through any delivery mechanism:

| Delivery | Description |
|----------|-------------|
| **API / GitOps** | Policies stored in DCM's database, managed via API or Git ingress adapter |
| **OPA Bundle** | Standard OPA bundle protocol — point OPA at a bundle server URL |
| **External Schema** | Policies in non-Rego format (e.g., XACML, custom JSON) naturalized to Rego by DCM before evaluation |

All three delivery mechanisms result in the same thing: Rego policies evaluated by OPA against the request payload. Where OPA runs (embedded Go library, sidecar container, or remote OPA instance) is a deployment topology decision — not a mode distinction.

**Policy registration:**
```yaml
policy:
  handle: "vm-size-limits"
  policy_type: gatekeeper
  delivery:
    mode: push                              # or: pull, opa_bundle, external_schema
    source_url: "https://git.corp/policies" # for pull/bundle modes
    format: rego                            # or: xacml, custom_json (naturalized to rego)
  activation: active                        # or: proposed (shadow mode)
  trust_level: trusted                      # trusted, verified, untrusted
```

**Trust levels (Internal mode):**
- `trusted` — GateKeeper authority (can deny requests)
- `verified` — Transformation and Validation authority only
- `untrusted` — advisory only (shadow mode enforcement)

### 4.2 External Mode — External Provider Evaluates

In External mode, DCM sends evaluation context to an external endpoint. The external system evaluates and/or enriches the data, and returns a structured result. DCM does not see the policy logic — it trusts the results within scoped bounds.

**External evaluation can:**
- **Evaluate** — return pass/fail, score, or recommendation
- **Enrich** — inject additional fields into the payload (risk scores, compliance citations, cost predictions, organizational context)
- **Both** — combined decision + enrichment in a single response

**Registration:**
```yaml
policy:
  handle: "compliance-scanner"
  policy_type: validation
  delivery:
    mode: external                          # External mode
    endpoint: "https://compliance.corp/api/evaluate"
    auth: mtls
  data_request_spec:                        # data minimization — only declared fields sent
    fields: [resource_type, sovereignty_zone, data_classification, tenant_uuid]
  on_unavailable: gatekeep                  # fail-closed — unknown is not safe
  trust_level: verified                     # minimum verified for enrichment
```

### 4.3 External Mode Governance (BBQ-001 through BBQ-009)

External evaluation introduces governance concerns that Internal mode does not:

| ID | Requirement |
|----|-------------|
| BBQ-001 | Data sovereignty check before any query is sent to an external endpoint |
| BBQ-002 | Data minimization — only fields declared in `data_request_spec` are sent |
| BBQ-003 | If the external endpoint is outside the entity's sovereignty zone, the query is blocked unless explicitly authorized |
| BBQ-004 | Full audit record per query-response cycle, including `audit_token` for cross-system correlation |
| BBQ-005 | Default failure behavior is `gatekeep` — if the external system is unavailable, the request is denied (fail-closed) |
| BBQ-006 | Cached results must include the original query timestamp and validity period in provenance |
| BBQ-007 | Fields injected by external enrichment carry standard field-level provenance: `source_type: external_external_policy_evaluator`, `source_uuid`, and `audit_token` |
| BBQ-008 | The override control model applies to enrichment-injected fields — a GateKeeper policy may restrict or refuse external enrichment on specific fields |
| BBQ-009 | External enrichment requires minimum `verified` trust level; GateKeeper authority requires `trusted` with dual-approval elevation |

### 4.4 Policy Sources and Policy Groups

Policies from any source (Internal or External) participate in the same Policy Group mechanism. A Policy Group composes multiple policies into a named, versioned, reviewable unit with explicit conflict declarations:

```yaml
policy_group:
  handle: "pci-dss-v4-controls"
  policies:
    - ref: "card-data-encryption"           # Internal — Rego policy in DCM
    - ref: "network-segmentation-check"     # Internal — OPA bundle
    - ref: "compliance-scanner"             # External — calls external endpoint
  activation_scope:
    resource_types: ["*"]
    tenant_tags: ["pci"]
```

### 4.5 Policy Health and Lifecycle

- **Internal policies:** Health is determined by OPA engine health. If OPA is unavailable, all Internal policies are degraded.
- **External policies:** Health is determined by endpoint availability. Each external endpoint has a health check (HTTP GET to a declared health URL). Unhealthy external policies trigger their `on_unavailable` behavior (default: `gatekeep`).
- **Deprecation:** Policies follow the `active → deprecated → retired` lifecycle. Deprecated policies fire with a warning in the audit trail. Retired policies are no longer evaluated.

---

## 5. Lifecycle Time Constraints

### 5.1 Concept

Lifecycle time constraints declare **when a resource should cease to exist or trigger a lifecycle action**. They are a first-class field on any resource entity — not metadata, not a tag, but a governed field that follows the standard data model precedence and override control.

### 5.2 Constraint Types

| Type | Format | Description |
|------|--------|-------------|
| `ttl` | ISO 8601 duration (e.g., `P14D`) | Relative — expires N time after the reference point |
| `expires_at` | ISO 8601 timestamp | Absolute — expires at a specific calendar date/time |

When both are declared, the **earliest expiry wins** (LTC-004).

### 5.3 Data Model

```yaml
lifecycle_constraints:
  ttl:
    duration: P14D                       # ISO 8601 duration — 14 days
    reference_point: realization_timestamp  # created_at | realization_timestamp | last_modified
    on_expiry: <destroy | suspend | notify | review>
    metadata:
      override: allow                    # standard override control applies
      basis_for_value: "Consumer declared ephemeral — 14-day lab resource"

  expires_at:
    timestamp: "2026-06-30T23:59:59Z"
    on_expiry: notify
    metadata:
      override: immutable
      locked_by_policy_uuid: <uuid>
      basis_for_value: "Project deadline — resource must not persist beyond Q2"

  # Enforcement behavior
  enforcement:
    warn_before_expiry: P1D              # warn 1 day before expiry
    warn_notification_endpoint: <from owned_by artifact metadata>
    grace_period: PT1H                  # 1 hour grace after expiry before action
    on_grace_period_expiry: <execute | escalate>
```

### 5.4 Precedence

Lifecycle time constraints follow the standard data model precedence chain:

```
Base Layer default (lowest — e.g., "no TTL by default")
  ↓
Core Layer (e.g., "all dev environment resources: TTL 90 days")
  ↓
Service Layer (e.g., "ephemeral compute: TTL 7 days")
  ↓
Request Layer (consumer declared TTL)
  ↓
Transformation Policy (enrich TTL from business context)
  ↓
GateKeeper Policy (highest — may lock TTL as immutable)
```

A consumer can declare `ttl: P14D` in their request. A GateKeeper policy can override this to `P7D` and lock it immutable if organizational policy mandates shorter maximum lifetimes. A Core Layer can set default TTLs for resource classes. The provenance chain records every modification.

### 5.5 Expiry Enforcement

The **Lifecycle Constraint Enforcer** is a DCM control plane component that:
- Monitors all realized entities against their declared lifecycle constraints
- Fires the configured `on_expiry` action when a constraint is reached
- Records the enforcement action in provenance and the Audit Store
- Emits expiry warnings `warn_before_expiry` duration before the deadline

Expiry enforcement is a DCM concern — not a provider concern. The provider does not need to know about or implement TTL logic.

### 5.6 System Policies

| Policy | Rule |
|--------|------|
| `LTC-001` | Lifecycle time constraints follow standard data model precedence — layers, request, policies |
| `LTC-002` | GateKeeper policies may lock lifecycle constraints as `override: immutable` or `immutable_ceiling: absolute` |
| `LTC-003` | Expiry enforcement is a DCM control plane function — not a provider concern |
| `LTC-004` | When multiple time constraints exist on an entity, the earliest expiry wins |
| `LTC-005` | Expired entities that fail to execute their `on_expiry` action enter `PENDING_EXPIRY_ACTION` state and trigger an escalation |

---

## 6. Cross-Tenancy Authorization Model

### 6.1 Default Stance — Closed

Cross-tenant information sharing is **closed by default**. No cross-tenant relationship of any nature is permitted unless explicitly authorized. This applies to both operational dependencies and informational relationships.

The hard tenancy spectrum:

| Setting | Meaning |
|---------|---------|
| `deny_all` | No cross-tenant relationships of any nature |
| `explicit_only` | All cross-tenant must be explicitly authorized (DEFAULT) |
| `operational_permitted` | Operational cross-tenant permitted; informational requires explicit auth |
| `allow_all` | All cross-tenant permitted — requires justification; not available in sovereign profile |

The default shifts from the Q59 model's `operational_only` to `explicit_only`. Informational sharing is no longer implicitly open — every informational cross-tenant relationship requires an explicit authorization record.

### 6.2 Cross-Tenant Authorization Record

```yaml
cross_tenant_authorization:
  artifact_metadata:
    uuid: <uuid>
    handle: "tenant-a/auth/shared-network-read"
    version: "1.0.0"
    status: active
    owned_by:
      display_name: "Infrastructure Tenant Admin"

  # WHO
  authorized_consumer_tenant_uuid: <uuid — or null for any_authorized_tenant>
  authorized_actor_constraint:
    roles: [service_account, automation]    # null = any actor in the tenant
    specific_uuids: []                      # specific actor UUIDs if needed

  # WHAT
  resource_entity_uuid: <specific entity — or null for type-level>
  resource_type_uuid: <if type-level authorization>
  permitted_fields:
    - field: network_segment
    - field: vlan_id
    # empty list = all fields permitted
  permitted_relationship_natures: [informational, operational]

  # WHEN
  valid_from: <ISO 8601>
  expires_at: <ISO 8601 — null = indefinite>

  # WHERE
  permitted_in_regions: [eu-west, eu-central]   # null = any region
  sovereignty_constraints:
    must_honor_consuming_tenant_sovereignty: true
    must_honor_owning_tenant_sovereignty: true

  # GOVERNANCE
  authorized_by_policy_uuid: <uuid>
  authorization_level: <tenant_global | resource_specific | field_specific>
  # Hierarchy: field_specific > resource_specific > tenant_global
  # More specific = higher precedence
```

### 6.3 Authorization Hierarchy

More specific authorizations take precedence over broader ones:

```
field_specific     ← highest precedence — only these exact fields on this entity
  │
resource_specific  ← this entity — all permitted fields
  │
tenant_global      ← all entities in this Tenant — broadest
```

If a tenant-global policy says "allow informational sharing with Tenant B" but a resource-specific policy says "this resource is not shareable with anyone," the resource-specific policy wins.

### 6.4 System Policies — Cross-Tenancy

| Policy | Rule |
|--------|------|
| `XTA-001` | Cross-tenant information sharing is closed by default — explicit authorization required |
| `XTA-002` | Cross-tenant authorizations must specify who, what, when, and where |
| `XTA-003` | More specific authorizations take precedence: field_specific > resource_specific > tenant_global |
| `XTA-004` | All cross-tenant authorization decisions are policy-driven and DCM-enforced |
| `XTA-005` | Sovereignty constraints declared by either Tenant must be honored by all cross-tenant relationships |

---

## 7. Rehydration Tenancy Controls

### 7.1 Tenancy and Sovereignty Are Always Current

Tenancy controls, sovereignty directives, and cross-tenant authorizations are **always evaluated against current policies during rehydration**. They cannot be pinned to historical versions.

```yaml
rehydration:
  re_evaluate: true/false          # governs placement
  policy_version: current/pinned   # governs resource configuration policies
  # The following are ALWAYS current — cannot be pinned:
  tenancy_controls: always_current
  sovereignty_controls: always_current
  cross_tenant_authorizations: always_current
```

### 7.2 Rehydration Tenancy Conflict

When rehydration produces a tenancy or sovereignty constraint that conflicts with an existing cross-tenant allocation:

```yaml
rehydration_tenancy_conflict_record:
  rehydration_request_uuid: <uuid>
  entity_uuid: <uuid>
  conflict_type: cross_tenant_authorization_conflict
  original_authorization_uuid: <uuid>
  current_policy_violation:
    policy_uuid: <uuid>
    violation: "Consuming Tenant no longer has authorization for this allocation"
  action_taken: paused
  entity_state: PENDING_REVIEW
  notifications_sent:
    - entity_owner
    - owning_tenant_admin
    - consuming_tenant_admin
    - platform_admin
  resolution_options:
    - re_authorize
    - release
    - escalate
  policy_override_available: true
```

### 7.3 System Policies — Rehydration

| Policy | Rule |
|--------|------|
| `RHY-001` | Tenancy, sovereignty, and cross-tenant authorizations always use current policies during rehydration |
| `RHY-002` | Rehydration that conflicts with current tenancy/sovereignty pauses and enters PENDING_REVIEW |
| `RHY-003` | A paused rehydration allocation is not automatically released — requires explicit resolution |
| `RHY-004` | A policy may declare automatic resolution behavior for rehydration tenancy conflicts |

---

## 8. Open Questions

| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | Should organizations be able to submit custom profiles and groups back to the DCM project registry? | Community | ✅ Resolved — community submissions via PR-based workflow; Tier 2; documented use case + deployment reference + test results + named maintainer (PROF-005) |
| 2 | Should there be a certified profile program — profiles that have been validated against specific regulatory frameworks? | Compliance | ✅ Resolved — certified profile program with third-party certification metadata; certified profiles promoted to Tier 1; applies to artifact not deployment (PROF-006) |
| 3 | Should External Policy Evaluator trust elevation require a formal approval workflow in DCM UI or is out-of-band approval sufficient? | Security | ✅ Resolved — formal approval workflow; profile-governed approvers (1 standard → 3 sovereign); P7D shadow period; POLICY_PROVIDER_ELEVATED audit (PROF-007) |
| 4 | Should the default TTL for dev profile resources be configurable at the platform level or only at the group level? | Configuration | ✅ Resolved — overridable at platform domain layer; per-resource-type TTL overrides; on_expiry action configurable (PROF-008) |
| 5 | How does External Policy Evaluator delivery interact with air-gapped deployments — pull from internal mirror? | Sovereignty | ✅ Resolved — signed bundle model identical to registry; Mode 4 in sovereign restricted to within-boundary endpoints (PROF-009) |

---

## 9. Related Concepts

- **Policy Engine** — executes the policies organized by groups and profiles
- **Policy Layers** — the assembly process step where policies execute
- **Artifact Metadata** — universal metadata on all policy artifacts
- **Five Artifact Statuses** — developing → proposed → active → deprecated → retired
- **Shadow Execution** — proposed policies and profiles run in shadow mode for validation
- **Override Control** — policies set override control on fields; immutable_ceiling: absolute for non-negotiables
- **Ingestion Model** — policy profile requirements may gate brownfield promotion
- **Four States** — rehydration tenancy controls govern how historical states are replayed


## 8. Policy Profile Gap Resolutions

### 8.1 Community Profile and Group Submissions (Q1)

Organizations may submit custom profiles and policy groups to the DCM community registry following the same PR-based proposal workflow as Resource Types. Community contributions live in Tier 2 (Verified Community).

```yaml
community_profile_submission:
  profile:
    handle: "community/profile/hipaa-openstack"
    extends: system/profile/hipaa-prod
    description: "HIPAA production profile for OpenStack deployments"
    policy_groups:
      - system/group/compliance-hipaa
      - community/group/openstack-security-baseline
    contributed_by: "Healthcare IT Community Group"
    tested_with: [OpenStack 2024.1, DCM 1.0]
  required_for_submission:
    - documented_use_case
    - at_least_one_real_deployment_reference
    - test_results_against_reference_implementation
    - named_maintainer
```

Community profiles carry the same lifecycle as Resource Types — shadow validation before active, deprecation policies, sunset periods. Organizations adopt them directly or extend them further.

### 8.2 Certified Profile Program (Q2)

DCM supports a certified profile program where profiles carry formal third-party certification metadata against compliance frameworks. Certified profiles are promoted to Tier 1 (DCM Core).

```yaml
profile_certification:
  certifications:
    - framework: HIPAA
      certifying_body: "Coalfire Systems"
      certification_date: "2025-11-01"
      expires_at: "2027-11-01"
      certification_scope: "PHI data lifecycle management via DCM"
      certificate_ref:
        vault_credential_ref: <uuid>
        path: "dcm/registry/certifications/hipaa-prod-2025"
```

**Important:** Profile certification applies to the profile artifact only — it does not certify the deploying organization's compliance posture. A certified profile is evidence that the profile implements the required controls; it is not a compliance certification of any specific deployment.

### 8.3 External Policy Evaluator Trust Elevation Approval (Q3)

External Policy Evaluator trust elevation (increasing the mode level) requires a formal approval workflow. Approval requirements are profile-governed.

```yaml
external_evaluation_trust_elevation:
  elevation_request:
    from_mode: 1
    to_mode: 3
    justification: "Need OPA Rego for complex placement constraints"

  approval_requirements:
    standard:
      approvers: [platform_admin]
      min_approvers: 1
    prod:
      approvers: [platform_admin, security_owner]
      min_approvers: 2
    fsi:
      approvers: [platform_admin, security_owner, compliance_officer]
      min_approvers: 2
      verified_required: true
    sovereign:
      approvers: [platform_admin, security_owner, compliance_officer]
      min_approvers: 3
      requires_change_control_ticket: true

  shadow_period_after_elevation: P7D    # elevated mode runs in shadow before active
  audit_record: POLICY_PROVIDER_ELEVATED
```

The P7D shadow period catches unintended consequences before elevated outputs become binding on production requests.

### 8.4 Dev Profile Resource TTL Configurability (Q4)

The default TTL for dev profile resources is declared in the system domain layer and overridable at the platform domain level.

```yaml
layer:
  handle: "platform/dev-profile/resource-ttl-override"
  domain: platform
  fields:
    dev_profile_resource_ttl:
      default_ttl: P30D               # platform override: 30d instead of system default P7D
      max_ttl: P90D                   # consumers cannot declare TTL > 90 days in dev
      on_expiry: notify               # notify (consumers can extend) vs destroy
      per_resource_type_overrides:
        Compute.VirtualMachine: P7D
        Storage.Block: P14D
        DNS.Record: P3D
```

### 8.5 Air-Gapped External Policy Evaluator Delivery (Q5)

External Policy Evaluator delivery in air-gapped deployments uses signed bundles — same model as the registry bundle system.

```yaml
external_evaluation_airgap:
  delivery_mode: signed_bundle
  bundle_contents:
    - provider_registration_yaml
    - policy_artifacts_zip
    - mode_specific_package:
        mode_3: opa_rego_bundle       # OPA Rego files + data
        mode_4: endpoint_config       # endpoint declaration (must be within boundary)
  signing_key_ref: <org-signing-key>
  expires_at: <ISO 8601>
```

**Mode 4 sovereign constraint:** In sovereign profiles, Mode 4 External Policy Evaluators may only call endpoints within the sovereignty boundary. External AI service calls are blocked by the BBQ-001 sovereignty check before any Mode 4 query.

### 8.6 System Policies — Policy Profile Gaps

| Policy | Rule |
|--------|------|
| `PROF-005` | Organizations may submit custom profiles and policy groups to the DCM community registry via the same PR-based proposal workflow as Resource Types. Community contributions live in Tier 2. Submissions require documented use case, at least one production deployment reference, test results, and a named maintainer. |
| `PROF-006` | DCM supports a certified profile program where profiles carry formal third-party certification metadata. Certified profiles are promoted to Tier 1. Profile certification applies to the artifact only — it does not certify the deploying organization's compliance posture. |
| `PROF-007` | External Policy Evaluator trust elevation requires a formal approval workflow (standard: 1 platform admin; prod: platform admin + security owner; fsi/sovereign: dual approval + compliance officer). Elevated providers run in shadow mode for P7D before activation. All elevations produce a POLICY_PROVIDER_ELEVATED audit record. |
| `PROF-008` | The default TTL for dev profile resources is declared in the system domain layer and overridable at the platform domain level. Per-resource-type TTL overrides are supported. The on_expiry action is configurable. |
| `PROF-009` | External Policy Evaluator delivery in air-gapped deployments uses signed bundles identical to the registry bundle model. Mode 4 providers in sovereign profiles may only call endpoints within the sovereignty boundary. |



---

## 9. Recovery Posture Policy Groups

### 9.1 recovery_posture as a Concern Type

`recovery_posture` is a Policy Group concern_type that governs how DCM responds to provisioning failures, timeouts, and ambiguous states. It is the fifth concern type alongside security, compliance, operational, and implementation posture.

Recovery posture groups contain Recovery Policies — a formal DCM policy type that maps trigger conditions (DISPATCH_TIMEOUT, PARTIAL_REALIZATION, etc.) to response actions (DRIFT_RECONCILE, DISCARD_AND_REQUEUE, NOTIFY_AND_WAIT, etc.).

See [Operational Models](https://github.com/croadfeldt/udlm/blob/main/lifecycle/operational-models.md) Section 5 for the complete Recovery Policy model, trigger vocabulary, and action vocabulary.

### 9.2 Four Built-in Recovery Posture Groups

| Group Handle | Posture | Appropriate For |
|-------------|---------|----------------|
| `system/group/recovery-automated-reconciliation` | Let drift detection converge on correct state | Dev, standard environments |
| `system/group/recovery-discard-and-requeue` | Clean up and restart on any ambiguity | Consistency-critical environments |
| `system/group/recovery-notify-and-wait` | Always notify human; never act automatically | FSI, sovereign, regulated environments |
| `system/group/recovery-aggressive-retry` | Retry everything before giving up | High-transient-failure environments |

### 9.3 Profile Binding Defaults

| Profile | Default Recovery Posture |
|---------|------------------------|
| `minimal` | recovery-automated-reconciliation |
| `dev` | recovery-automated-reconciliation |
| `standard` | recovery-automated-reconciliation |
| `prod` | recovery-notify-and-wait |
| `fsi` | recovery-notify-and-wait |
| `sovereign` | recovery-notify-and-wait |

### 9.4 Override Hierarchy

Organizations override recovery posture at Tenant or resource-type level without changing the deployment profile:

```yaml
# Tenant override — all resources in this Tenant use discard-and-requeue
tenant_config:
  recovery_profile_override: recovery-discard-and-requeue

# Resource-type override — VMs get aggressive retry regardless of Tenant/profile
resource_type_recovery_override:
  resource_type: Compute.VirtualMachine
  recovery_profile: recovery-aggressive-retry
```

Resource-type override wins over Tenant override wins over profile default.



---

## 10. Zero Trust Posture Policy Groups

### 10.1 zero_trust_posture as a Concern Type

`zero_trust_posture` is the sixth Policy Group concern type. It governs authentication requirements, credential lifetime, revocation check frequency, and hardware attestation requirements for all DCM interactions.

See [Accreditation and Authorization Matrix](https://github.com/croadfeldt/udlm/blob/main/governance/accreditation-and-authorization-matrix.md) Section 5 for the complete zero trust model.

### 10.2 Four Zero Trust Posture Levels

| Posture | Boundary | Internal | Hardware | Profile Default |
|---------|---------|----------|----------|----------------|
| `none` | Perimeter model | Trusted | Not required | minimal |
| `boundary` | Zero trust at external boundaries | Service mesh | Not required | dev, standard |
| `full` | Zero trust everywhere | Per-call auth | Not required | prod, fsi |
| `hardware_attested` | Zero trust everywhere | Per-call auth | Required (TPM/HSM) | sovereign |

### 10.3 Credential Lifetime Defaults

| Profile | Max credential lifetime |
|---------|------------------------|
| minimal | PT8H |
| dev | PT4H |
| standard | PT1H |
| prod | PT30M |
| fsi | PT15M |
| sovereign | PT15M + hardware attestation |

### 10.4 Hard Data Boundary Constraints

The sovereign profile enforces a hard constraint via the Data/Capability Authorization Matrix: **data classified as `sovereign` or `classified` never crosses any interaction boundary**. This constraint is declared with `hard_constraint: true` in the federation boundary matrix and cannot be overridden by any policy, profile, or operator action. It is enforced at the matrix level, not the policy level.


---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
