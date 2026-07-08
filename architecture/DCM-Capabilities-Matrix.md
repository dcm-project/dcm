# DCM — Foundational Capabilities Matrix

> **Purpose:** This document defines the core operational capabilities required for DCM to perform lifecycle management as defined by the data model. Each capability maps to a consumer/service provider perspective and will be used to drive implementation work in Jira.
>
> **How to read this document:**
> - **Capability Domain** — the architectural area the capability belongs to
> - **Capability** — a discrete operational function; the smallest unit of independently implementable behavior
> - **Consumer perspective** — what the end user / application team experiences
> - **Service Provider perspective** — what the Service Provider or platform component must implement
> - **Platform/Admin perspective** — what the platform engineer or SRE must configure or operate
> - **Depends on** — other capabilities that must exist first

---

## 1. Identity and Access Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| IAM-001 | Actor Authentication | Authenticate to DCM via configured IdP | — | Register and configure Auth Providers; manage local user store | — |
| IAM-002 | Session Token Management | Receive and use session tokens; token refresh | — | Configure session TTL, failover chain | IAM-001 |
| IAM-003 | Role-Based Access Control | Receive role-appropriate service catalog and API responses | — | Declare role mappings; assign roles to actors | IAM-001 |
| IAM-004 | Group Membership Resolution | Group memberships automatically applied from IdP | — | Map IdP groups to DCM groups; declare group-role relationships | IAM-001, IAM-003 |
| IAM-005 | Multi-Factor Authentication | Satisfy per-session and step-up MFA challenges | — | Configure MFA methods; declare step-up operations | IAM-001 |
| IAM-006 | SCIM Automated Provisioning | Actor created/updated/deprovisioned from IdP automatically | — | Configure SCIM endpoint and attribute mappings | IAM-001 |
| IAM-007 | Tenant Scope Enforcement | Access restricted to authorized Tenants | — | Declare Tenant membership; configure cross-tenant policies | IAM-003, IAM-004 |
| AUTH-002 | Multi-Auth-Provider Routing | — | — | Register multiple Auth Providers simultaneously; ingress routes by authentication signal | IAM-001 |
| AUTH-003 | Auth Provider Trust Level Enforcement | Requests evaluated per provider trust level (authoritative / verified / advisory) | — | Configure trust level per registered Auth Provider | IAM-001 |
| AUTH-004 | Auth Provider Artifact Versioning | — | — | Manage role/tenant mapping versioning through standard DCM artifact lifecycle; activate/deprecate mappings | IAM-003 |
| AUTH-005 | Auth Provider Failover | Existing sessions remain valid on provider failure; new auth routes to failover chain | — | Configure failover chain; monitor provider health; manage session cache TTL | IAM-001 |
| AUTH-006 | Auth Context in Audit Trail | — | — | Auth Provider identity and ingress context automatically recorded in all audit records | IAM-001 |
| AUTH-007 | Auth Provider Credential Security | — | — | Enforce Auth Provider config credentials reference secrets management; no plaintext credentials | IAM-001 |
| AUTH-008 | No Anonymous Access | — | — | Enforce authenticated access at all ingress surfaces across all profiles | IAM-001 |
| AUTH-009 | Webhook and Message Bus Authentication | Authenticate webhook registrations | — | Enforce authentication on all inbound surfaces regardless of profile | IAM-001 |
| AUTH-010 | Per-Actor Rate Limiting | Receive 429 responses when rate limit exceeded | — | Configure rate limits per actor; manage burst allowances | IAM-001 |
| AUTH-011 | Git PR Identity Resolution | Git PR submissions resolve to same actor identity as API/UI login | — | Configure Auth Provider to trust Git server's identity assertion | IAM-001 |
| AUTH-012 | SCIM Automated Provisioning | Actor created/updated/deprovisioned from IdP automatically via SCIM | — | Configure SCIM 2.0 endpoint; manage suspension-on-deprovision policy | IAM-001 |
| AUTH-013 | In-Flight Request Continuity on Auth Failure | In-flight requests before auth failure are not interrupted | — | Configure session cache TTL; manage graceful degradation | IAM-001 |
| AUTH-014 | Two-Tier MFA Enforcement | Satisfy per-session MFA at login and step-up MFA for high-risk operations | — | Configure per-session and step-up MFA; declare step-up trigger operations | IAM-005 |
| AUTH-015 | Built-In Auth Provider Storage Backend | — | — | Configure built-in Auth Provider storage backend (SQLite for minimal/dev; PostgreSQL/MySQL for standard+) | IAM-001 |

---

## 2. Service Catalog

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| CAT-001 | Service Catalog Presentation | Browse available services filtered by RBAC | Declare catalog items for offered resource types | Activate catalog items; configure catalog visibility policies | IAM-003, IAM-007 |
| CAT-002 | Service Schema Discovery | View field schemas, constraints, and edit constraints for a catalog item | Declare field schemas in Resource Type Spec | Configure constraint visibility level per profile | CAT-001 |
| CAT-003 | Catalog Item Search and Filter | Search catalog by keyword, resource type, tag | — | Configure Search Index for catalog | CAT-001 |
| CAT-004 | Catalog Item Versioning | Request a specific version of a catalog item | Publish new catalog item versions following semver | Manage version lifecycle; enforce deprecation timelines | CAT-001 |
| CAT-005 | Cost Estimation | Receive estimated cost before submitting a request | Declare cost metadata on provider registration | Configure Cost Analysis component | CAT-001 |
| CAT-006 | Dependency Visualization | See required dependencies for a catalog item before requesting | Declare dependency graph in Resource Type Spec | — | CAT-001 |
| CAT-007 | Catalog Item Deprecation | Receive deprecation warnings on deprecated catalog items | Declare successor types in deprecation notice | Manage deprecation lifecycle; notify consumers | CAT-004 |

---

## 3. Request Lifecycle Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| REQ-001 | Submit Service Request | Submit a resource request via UI, API, or Git PR | — | Configure request ingress surfaces | IAM-007, CAT-001 |
| REQ-002 | Intent State Capture | Request stored as versioned GitOps artifact before processing | — | Configure Intent Store; manage Git repository structure | REQ-001 |
| REQ-003 | Layer Assembly | Request enriched with organizational defaults and context layers | Contribute Service Layers for resource types | Manage Core Layers; configure Layer Cache | REQ-002 |
| REQ-004 | Policy Evaluation | Request validated, transformed, and gated by applicable policies | Contribute provider-specific policies | Manage Policy Engine; configure Policy Groups and Profiles | REQ-003 |
| REQ-005 | Placement Engine Execution | Resource placed with the best available provider instance | Implement capacity reserve_query response | Configure placement constraints; manage provider priorities | REQ-004 |
| REQ-006 | Requested State Persistence | Assembled payload stored as authoritative GitOps record | — | Configure Requested Store; manage storage redundancy | REQ-005 |
| REQ-007 | Provider Dispatch | Request payload delivered to selected provider | Implement Services API to receive DCM payloads | Configure API Gateway and egress | REQ-006 |
| REQ-008 | Request Status Tracking | Monitor request status from submitted through realized | Report realization status back to DCM | Configure observability for request tracking | REQ-007 |
| REQ-009 | Request Cancellation | Cancel a pending request before realization | Handle cancellation payloads | Configure cancellation policies | REQ-002 |
| REQ-010 | Git PR Request Ingress | Submit requests via Git Pull Request with policy dry-run feedback | — | Configure Git Request Watcher; manage repository structure | REQ-001, IAM-001 |

---

## 4. Provider Contract and Realization

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| PRV-001 | Provider Registration | — | Register provider with DCM: declare type, capabilities, sovereignty, cost metadata | Configure Provider Registry; validate sovereignty declarations | IAM-001 |
| PRV-002 | Naturalization | — | Convert DCM unified payload to provider-native format | — | PRV-001, REQ-007 |
| PRV-003 | Realization | — | Execute required actions to provision/configure/change resource | — | PRV-002 |
| PRV-004 | Denaturalization | — | Convert provider-native result back to DCM unified format | — | PRV-003 |
| PRV-005 | Realized State Reporting | — | Report realized payload and status to DCM API Gateway | Configure Realized State Store; manage Event Stream | PRV-004 |
| PRV-006 | Capacity Reporting | — | Respond to reserve_query with current capacity and availability | Configure placement engine; manage capacity confidence | PRV-001 |
| PRV-007 | Provider Health Reporting | — | Expose health check endpoint; report availability | Monitor provider health; configure trust score updates | PRV-001 |
| PRV-008 | Sovereignty Declaration Maintenance | — | Notify DCM when sovereignty data changes within declared SLA | Monitor sovereignty changes; trigger re-evaluation | PRV-001 |
| PRV-009 | Composite Service Composition | — | Register Composite Service catalog items declaring constituent resource types, dependencies, and delivery requirements | Configure Composite Service registration eligibility | PRV-001, PRV-003 |
| PRR-001 | OpenAPI Spec Declaration (GATE-SP-01) | — | Declare OpenAPI spec URL at registration; spec must be machine-readable and reachable | Validate spec URL reachability during approval pipeline | PRV-001 |
| PRR-002 | Healthy API at Activation (GATE-SP-02) | — | Health endpoint returns `{"status": "healthy"}` at activation time | Enforce health check as activation precondition | PRV-001, HLT-001 |
| PRR-003 | State Management Callback (GATE-SP-03) | — | Implement realized_state_push callback at all conformance levels | Validate callback endpoint reachability during approval | PRV-001 |
| PRR-004 | Tenant Metadata Endpoint (GATE-SP-04) | — | Implement GET /api/v1/tenants/{uuid}/metadata returning usage data | Require for standard+ profile activation; enforce quota integration | PRV-001 |
| PRR-005 | Prometheus Metrics (GATE-SP-05) | — | Expose required metric families at declared metrics_endpoint | Validate metric presence during approval; gate standard+ activation | PRV-001, HLT-005 |
| PRR-006 | AEP.DEV Linting (GATE-SP-06) | — | Pass AEP linter against OpenAPI spec with no errors before registration; include linting report URL | Gate standard+ activation on linting pass; block activation on errors | PRV-001 |

| PRV-010 | Provider Sandbox/Test Mode | Submit test requests targeting sandbox providers via `_test_context.target_provider_uuid`; sandbox providers visible in registry with `status: sandbox` | Register with `sandbox_mode: true`; implement full OIS contract; graduate to production via standard approval | Manage sandbox provider registry; review graduation requests; sandbox providers excluded from production placement | PRV-001, GATE-SP-01 || PRR-007 | Multi-Tenant Dispatch (GATE-SP-07) | — | Accept tenant_uuid in all dispatch payloads; return tenant-scoped resources | Gate standard+ activation on multi-tenant compatibility test | PRV-001 |

---

## 5. Resource Lifecycle Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| LCM-001 | Resource State Transitions | Trigger lifecycle actions: suspend, resume, decommission | Handle state transition payloads | Configure lifecycle policies; manage state machine | REQ-008 |
| LCM-002 | Post-Realization Field Updates | Update editable fields on realized resources (targeted delta) | Handle delta update payloads; apply partial changes | Configure editable field declarations; manage edit policies | PRV-005 |
| LCM-003 | Resource TTL Management | Declare and extend resource TTLs; receive expiry notifications | Handle TTL-triggered decommission payloads | Configure Lifecycle Constraint Enforcer; manage expiry policies | LCM-001 |
| LCM-004 | Ownership Transfer | Transfer resource ownership to a different Tenant | — | Authorize and execute ownership transfers; record transfer history | IAM-007, LCM-001 |
| LCM-005 | Rehydration | Replay a resource's intent state to a new provider or context | Receive and execute rehydration payloads | Manage rehydration leases; configure auth level requirements | REQ-002, PRV-003 |
| LCM-006 | Billing State Management | — | — | Configure billing state policies; integrate with Cost Analysis | LCM-001 |
| LCM-007 | Resource Decommission | Decommission resources individually or as part of group decommission | Handle decommission payloads; release resources | Manage decommission workflows; coordinate dependency teardown | LCM-001 |

---

## 6. Drift Detection and Remediation

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| DRF-001 | Active Discovery | — | Expose discovery endpoint; respond to interrogation queries | Configure discovery schedules; manage Discovered Store | PRV-005 |
| DRF-002 | Drift Comparison | Receive drift notifications for owned resources | — | Configure drift detection policies; manage comparison logic | DRF-001, PRV-005 |
| DRF-003 | Drift Notification | Receive actionable drift alerts with field-level detail | — | Configure drift notification channels and escalation policies | DRF-002 |
| DRF-004 | Drift Remediation | Approve or reject automatic drift remediation | Execute remediation payloads | Configure remediation policies (revert/update/alert/escalate) | DRF-002, LCM-002 |
| DRF-005 | Unsanctioned Change Detection | Receive alerts on unauthorized resource modifications | Report all external state changes to DCM | Configure unsanctioned change policies | DRF-001 |

---

## 7. Policy Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| POL-001 | Policy Authoring | — | Contribute provider-specific policy rules | Author and manage policies via API or GitOps ingress | IAM-003 |
| POL-002 | Policy Validation and Shadow Mode | View shadow evaluation results on own requests | — | Configure shadow mode; review shadow results | POL-001 |
| POL-003 | Policy Activation and Review | — | — | Manage policy review periods; authorize policy activation | POL-001, POL-002 |
| POL-004 | Policy Group Management | — | — | Compose Policy Groups; manage profile assignments | POL-003 |
| POL-005 | Profile Management | — | — | Configure deployment profiles; manage compliance domain groups | POL-004 |
| POL-006 | External Policy Evaluation | — | Register as external evaluation endpoint; implement BBQ-001–009 governance | Configure external evaluation trust levels; manage trust elevation | PRV-001, POL-001 |
| POL-007 | Policy Override and Constraint Visibility | View constraint details for service catalog fields | Declare constraint schemas on Resource Type Specs | Configure constraint visibility levels per profile | CAT-002, POL-003 |
| POL-008 | Constraint Type Registry | — | — | Register constraint types with OpenAPI v3 schemas; configure emittable_by/consumable_by; manage core and organization tiers | POL-001 |
| POL-009 | Evaluation Context and Multi-Pass Convergence | — | — | Configure max evaluation passes; monitor convergence; manage escalation for unresolvable conflicts | POL-001, POL-008 |
| POL-010 | Policy Templates | — | Contribute policy templates with parameterized Rego | Register templates (Gatekeeper ConstraintTemplate pattern); validate parameter schemas and constraint type references | POL-001, POL-008 |
| POL-011 | DCM Constraint Types Library | — | — | Manage auto-generated Rego library (data.dcm.constraint_types); sync with Constraint Type Registry | POL-008, POL-010 |
| POL-012 | Data-Driven Policy Matching | — | — | Configure match sources (request payload, operation context, evaluation context, entity metadata); validate match fields at activation | POL-001 |
| POL-013 | Lifecycle-Scoped Policy Evaluation | — | — | Configure lifecycle_scope per policy (which operation types trigger it); enforce profile minimums (fsi/sovereign require sovereignty policies on all operations); configure changed_field_filter for update/scale operations | POL-001, POL-012 |
| POL-014 | Override Policies | — | — | Author override policies targeting specific policies for defined scopes; enforce expiry and review dates; cannot target hard enforcement policies | POL-001, POL-003 |
| POL-015 | Exception Grants | — | — | Create time-bounded, scope-limited waivers with compensating controls; track usage count; enforce dual-approval for hard policies; manage renewal limits | POL-001, AUD-008 |
| POL-016 | Manual Override | Submit override request for blocked request with justification | — | Grant single-request overrides; enforce dual-approval for hard policies; manage override authority roles | POL-001, IAM-001 |
| POL-017 | Dual-Approval Escalation | — | — | Configure role separation requirements; manage approval workflow for hard policy overrides; enforce fsi/sovereign dual-approval on all overrides | POL-001 |
| POL-018 | Compensating Control Substitution | — | — | Define substitute control sets that satisfy policy intent through different mechanisms; require compliance officer validation | POL-001 |
| POL-019 | Override Approval Flow | Submit override request for blocked request; view pending overrides awaiting approval | — | Configure override notification routing (internal, webhook); configure timeout per profile; configure escalation rules; manage override authority roles | POL-016, IAM-001 |
| POL-020 | Override Notification Routing | — | — | Configure per-profile notification channels (LISTEN/NOTIFY, webhook to ServiceNow/Jira/Slack); configure routing by policy domain and enforcement level; configure escalation timeouts | POL-019 |
| POL-021 | Policy Block Resolution | View blocking details, resolution guidance with compliant values; choose resolution action (modify, request override, cancel, escalate) | — | Configure block timeout per profile; configure resolution guidance generation; manage escalation routing | POL-001 |

---

## 8. Data Layer Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| LAY-001 | Core Layer Authoring | — | — | Author and manage Core and Organizational Layers in GitOps | IAM-003 |
| LAY-002 | Service Layer Contribution | — | Contribute Service Layers for offered resource types | Manage layer compatibility declarations | PRV-001, LAY-001 |
| LAY-003 | Layer Cache Management | — | — | Manage Layer Cache synchronization; handle cache invalidation | LAY-001, LAY-002 |
| LAY-004 | Layer Exclusion | Declare layer exclusions on specific requests | — | Configure which layers may be excluded; manage non-excludable declarations | REQ-003 |
| LAY-005 | Layer Versioning and Lifecycle | — | — | Manage layer versions; handle deprecation; enforce immutability | LAY-001 |

---

## 9. Information and Data Integration

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| INF-001 | Information Provider Registration | — | Register Information Provider; declare authority scope and schema | Configure Information Provider Registry; manage authority layers | IAM-001 |
| INF-002 | Information Provider Push | — | Push field value updates to DCM; respond to conflict notifications | Configure ingestion pipeline; manage conflict resolution policies | INF-001 |
| INF-003 | Information Provider Pull / Discovery | — | Expose data query endpoint for DCM pull operations | Configure pull schedules; manage cache TTLs | INF-001 |
| INF-004 | Write-Back | — | Implement write-back endpoint to receive DCM-initiated updates | Configure write-back triggers via policy | INF-001, INF-002 |
| INF-005 | Confidence Score Visibility | View confidence bands on entity field values; query confidence aggregation API | — | Configure confidence scoring formula; manage trust score thresholds | INF-001 |
| INF-006 | Conflict Resolution Management | — | — | Review and resolve contested field values; manage conflict escalation | INF-002 |

---

## 10. Ingestion and Brownfield Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ING-001 | Resource Discovery and Ingestion | — | Expose discovery endpoints for brownfield resources | Configure ingestion pipeline; manage __transitional__ Tenant | DRF-001 |
| ING-002 | Ingested Entity Review | — | — | Review ingested entities; resolve conflicts; promote to active Tenants | ING-001 |
| ING-003 | Bulk Promotion | — | — | Execute bulk entity promotions with preview and rollback | ING-002 |
| ING-004 | Catalog Item Association | — | — | Associate ingested entities with Resource Type Specs; create catalog items | ING-002, CAT-001 |

---

## 11. Audit and Compliance

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| AUD-001 | Audit Trail Access | Query audit records for own resources | — | Configure Audit Store; manage retention policies | IAM-003 |
| AUD-002 | Compliance Reporting | — | — | Generate compliance reports; manage report schedules | AUD-001 |
| AUD-003 | Merkle Tree Verification | — | — | Run inclusion proofs, consistency proofs, request chain verification; manage integrity incidents | AUD-001 |
| AUD-004 | Cross-DCM Audit Correlation | — | — | Correlate audit records across DCM instances via correlation_id; authorize cross-DCM pulls | AUD-001, DCM-001 |
| AUD-005 | Audit Record Retention Management | — | — | Configure reference-based retention; manage post-lifecycle retention | AUD-001 |
| AUD-006 | Audit Granularity Configuration | — | — | Configure granularity level per profile (stage, mutation, field); enforce minimum for fsi/sovereign | AUD-001 |
| AUD-007 | Signed Tree Heads | — | — | Configure STH interval; manage audit signing keys; publish STH for external verification | AUD-001 |
| AUD-008 | Payload Chain of Custody | View chain-of-custody proof for own requests | Verify dispatched payload matches DCM's signed output | Verify full pipeline integrity via request chain verification API | AUD-003 |
| AUD-009 | Inter-Stage Verification | — | — | Configure verification mode per profile (synchronous, asynchronous, disabled) | AUD-001 |

---

## 12. Observability and Operations

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| OBS-001 | Operational Dashboard | View health and status of own resources | — | Configure and manage observability dashboard | — |
| OBS-002 | Metrics and Telemetry Export | — | Expose resource-level metrics to DCM | Configure observability export; integrate enterprise observability platform, or deploy the packaged dcm-observability stack as the authoritative platform | — |
| OBS-003 | Curated Event Stream Subscription | Subscribe to observability event types via Message Bus | — | Configure event stream publication policies; manage subscriber roles | OBS-002 |
| OBS-004 | Alert and Notification Management | Receive resource and policy alerts via declared channels | — | Configure alert routing; manage notification channels and escalation | OBS-001 |

| OBS-006 | SLA/SLO Declaration | View SLO status for owned resources (`GET /resources/{uuid}/slo-status`) | Declare resource_type SLOs in Resource Type Specification; report realization timing via callbacks | Configure SLO targets per resource type; view aggregate SLO performance report (`GET /admin/slo/report`) | RLM-001, LCM-001 |
| OBS-007 | SLO Breach Detection and Notification | Receive `slo.breach_approaching` and `slo.breach_detected` events | — | Configure SLO breach routing and escalation; review aggregate breach reports | OBS-006, EVT-001 |
| OBS-005 | Cost Analysis and Attribution | View cost estimates and actuals for owned resources | Provide cost metadata; report utilization | Configure Cost Analysis component; manage cost attribution policies | PRV-006 |
| OBS-008 | Group-Scoped Observability | View dashboards, reports, and alerts scoped to the business/operational groups (DCMGroup) own resources belong to | Attribute telemetry to entity UUIDs so group scoping resolves from resource definitions | Scope dashboards, reporting, alerting, and their management to DCMGroups; scoping derives from data in the resource definitions themselves (group membership, ownership), never side-channel configuration | OBS-001, OBS-002, OBS-004 |

---

## 13. Storage and State Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| STO-001 | Data Store Management | — | — | Configure PostgreSQL data domains (intent, requested, realized, discovered); manage schema, RLS, and tenant isolation | — |
| STO-002 | Realized State Management | — | — | Configure realized_entities table; manage version retention and is_current flag | PRV-005 |
| STO-003 | Discovered State Management | — | — | Configure discovered_records table; manage retention policies per profile | DRF-001 |
| STO-004 | Search and Query | Use entity and catalog search | — | Configure materialized views and indexes; manage cache refresh | STO-001 |
| STO-005 | Backup and Recovery | — | — | Configure PostgreSQL backup (PITR); test recovery; verify audit hash chain integrity | STO-001 |
| STO-006 | Provenance Model Configuration | — | — | Select and configure provenance model (full_inline / deduplicated / tiered); manage tier transitions | STO-001 |
| STO-007 | Sovereignty Partitioning | — | Declare sovereignty constraints at registration | Configure separate PostgreSQL instances per sovereignty zone; manage cross-zone prohibition | STO-001, GOV-001 |
| STO-008 | Tenant-Scoped Storage Isolation | Data is isolated by tenant via RLS | — | Configure RLS policies per table; enforce STI-001 through STI-004 | STO-001, IAM-001 |
| STO-009 | Tenant-Scoped Encryption (fsi/sovereign) | — | — | Configure per-tenant AES-256-GCM encryption via secrets management; manage key rotation | STO-008, CPX-001 |
| STO-010 | Internal Secrets Management | — | — | Configure envelope encryption (KEK source: env var, K8s secret, or HSM); manage secrets table; optional Vault external backend | STO-001 |
| STO-011 | Pipeline Event Routing | — | — | Configure LISTEN/NOTIFY for pipeline events; optional Kafka for high-throughput; manage consumption tracking | STO-001 |
| STO-012 | Internal Authentication | — | — | Configure local actor accounts (argon2id hashes, DCM-issued JWT); optional OIDC/SAML external auth_provider | STO-001, IAM-001 |

---

## 14. DCM Federation and Multi-Instance

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| FED-001 | DCM Provider Registration | Submit requests that are routed to peer DCMs | Register as DCM Provider in peer instances | Configure DCM Provider registrations; manage federation trust | PRV-001, IAM-001 |
| FED-002 | Federation Routing | Requests automatically routed to appropriate Regional/Sovereign DCM | Respond to reserve queries from Hub DCM | Configure federation placement policies; manage sovereignty pre-filters | FED-001, REQ-005 |
| FED-003 | Federation Trust Management | — | — | Manage mTLS certificates; monitor federation trust scores; handle cert rotation | FED-001 |
| FED-004 | Cross-DCM Drift Detection | Receive drift alerts for federated resources | Publish Discovered State events to federation Message Bus | Configure federated drift detection; manage alert-and-hold policies | FED-001, DRF-002 |
| FED-005 | DCM Export and Import | — | — | Export and import DCM state packages; verify import trust scores | STO-001, STO-002 |

---

## 15. Platform Governance and Administration

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| GOV-001 | Tenant Management | — | — | Create, configure, and decommission Tenants; manage compliance overlays | IAM-007 |
| GOV-002 | Group Management | — | — | Create and manage DCM Groups; configure sovereignty rules; manage time-bounded memberships | IAM-003 |
| GOV-003 | Registry Management | — | Register and maintain Resource Type Specifications in organization registry | Manage registry sync; configure registry policies; manage Tier 3 types | PRV-001 |
| GOV-004 | Resource Type Lifecycle | — | Manage deprecation notices; declare successor types; maintain migration guidance | Enforce deprecation timelines; manage sunset periods | GOV-003 |
| GOV-005 | Platform Configuration Management | — | — | Manage platform-wide layers; configure profiles; manage deployment manifest | LAY-001, POL-005 |
| GOV-006 | Bootstrap and Self-Hosting | — | — | Manage DCM self-deployment; verify bootstrap manifest; handle repave scenarios | STO-001 |

| GOV-008 | Tenant Onboarding Workflow | Trigger onboarding completion: receive `tenant.onboarding_complete` when first entity OPERATIONAL | — | Execute full provisioning sequence: tenant entity, default groups, quota, admin actor, GitOps namespace, audit stream; dispatch `tenant.created` and member invitation events | IAM-001, STO-008 || GOV-007 | Sovereign Deployment Management | — | — | Manage air-gapped DCM instances; configure signed bundle import; manage offline registry | FED-001, STO-001 |

---

## 16. Accreditation Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ACC-001 | Accreditation Submission | — | Submit accreditation records (BAA, ISO 27001, FedRAMP, etc.) referencing external certificate evidence | Register accrediting bodies; configure minimum accreditation types per profile | PRV-001 |
| ACC-002 | Accreditation Review and Approval | — | Receive approval/rejection notification | Review submitted accreditations; verify certificate references; approve or reject via Admin API | ACC-001 |
| ACC-003 | Accreditation Lifecycle Monitoring | Receive notification when a provider's accreditation is nearing expiry or revoked | Renew accreditations before expiry; submit renewal documentation | Monitor expiry timelines; fire P90D renewal warnings; handle accreditation gaps | ACC-001 |
| ACC-004 | Accreditation Gap Response | Receive notification when a provider enters accreditation gap affecting owned resources | — | Configure Recovery Policy for accreditation gap events; manage affected entity remediation | ACC-003, POL-005 |
| ACC-005 | Data Classification Enforcement | Receive enforcement feedback when request payload contains data the selected provider cannot handle | Declare max_data_classification_accepted in capability registration | Configure classification immutability rules; manage phi/sovereign classification locks | ACC-001, PRV-001 |
| ACC-006 | DCM Deployment Accreditation | — | — | Register DCM deployment-level accreditations; expose to federation peers for trust verification | PRV-001, FED-001 |

---

## 17. Zero Trust and Security Posture

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ZTS-001 | Mutual TLS Enforcement | All interactions authenticated via mTLS at the client side | Present valid mTLS certificate on every interaction; rotate certificates on declared schedule | Configure trust anchors; manage CA chain; enforce mTLS at all interaction boundaries | IAM-001 |
| ZTS-002 | Scoped Interaction Credentials | Receive scoped short-lived credentials for authorized operations | Validate credential scope before executing operations; reject out-of-scope credentials | Configure credential lifetime per profile; manage credential issuance via secrets management | IAM-001, PRV-001 |
| ZTS-003 | Certificate Rotation Management | — | Implement certificate rotation before expiry; use transition window to avoid downtime | Monitor certificate expiry; fire P14D rotation warnings; manage P7D transition window | ZTS-001 |
| ZTS-004 | Zero Trust Posture Configuration | — | — | Configure zero_trust_posture per profile (none/boundary/full/hardware_attested); manage posture overrides | POL-005 |
| ZTS-005 | Hardware Attestation (Sovereign Profile) | — | Present hardware-attested identity (TPM/HSM) for sovereign profile interactions | Configure hardware attestation requirements; manage HSM integration; enforce for sovereign profile | ZTS-001, ZTS-002 |

| ZTS-007 | Provider OpenAPI Spec Signing (SEC-001) | — | Sign OpenAPI spec with mTLS private key at registration; rejected at GATE-SP-01 if unsigned | Verify signature during registration approval pipeline | PRV-001, ZTS-001 |
| ZTS-008 | GitOps Secrets Scanning (SEC-002) | Commits with detected secrets rejected with `SECRETS_DETECTED` audit record | Ensure service layer SCM does not contain plaintext secrets | Configure scanning ruleset; review and remediate detected secrets | GOV-001, AUD-001 |
| ZTS-009 | Software Bill of Materials (SBOM) Declaration (SEC-003) | — | Declare SBOM reference at registration (mandatory for fsi/sovereign) | Enforce SBOM requirement during registration approval for fsi/sovereign profiles | PRV-001, ACR-001 || ZTS-006 | Five-Check Boundary Enforcement | — | Pass all five boundary checks on every interaction: identity → authorization → accreditation → matrix → sovereignty | Monitor boundary check audit records; respond to INTERACTION_DENIED events | ZTS-001, ACC-001, GMX-001 |

---

## 18. Unified Governance Matrix

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| GMX-001 | Governance Matrix Rule Authoring | — | — | Author governance matrix rules in GitOps; declare match conditions across four axes (subject/data/target/context); declare field permissions | POL-001 |
| GMX-002 | Boundary Enforcement Evaluation | Receive DENY response with governing rule_uuid and human-readable reason when a request crosses a prohibited boundary | Receive field-stripped or redacted payloads when STRIP_FIELD/REDACT decisions apply | Monitor GMX evaluation audit records; respond to DENY events | GMX-001, ZTS-006 |
| GMX-003 | Field-Level Data Control | Receive request feedback when specific payload fields are stripped or redacted by active matrix rules | Receive filtered payloads; handle missing optional fields gracefully | Configure allowlist/blocklist field permissions per rule; manage STRIP_FIELD vs REDACT vs DENY_REQUEST escalation | GMX-001 |
| GMX-004 | Sovereignty Zone Management | — | Declare operating sovereignty zones in provider registration | Register sovereignty zones; declare jurisdictions, regulatory frameworks, inter-zone agreements | PRV-001, GMX-001 |
| GMX-005 | Compliance Domain Matrix Activation | — | — | Activate compliance domain matrix rules (HIPAA, GDPR, etc.) by enabling compliance domain in profile; rules apply automatically | POL-005, GMX-001 |
| GMX-006 | Tenant and Resource-Type Matrix Overrides | — | — | Declare Tenant-level and resource-type-level matrix rules that tighten (never relax) platform defaults | GMX-001, GOV-001 |
| GMX-007 | Matrix Rule Lifecycle Management | — | — | Manage governance matrix rule lifecycle (developing → proposed → active); use shadow mode for safe validation before activation | GMX-001, POL-002 |

---

## 19. Drift Reconciliation

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| DRC-001 | Drift Record Production | Receive drift records with field-level detail: realized value, discovered value, field criticality, severity, unsanctioned flag | — | Configure Drift Reconciliation Component; manage comparison algorithm and severity thresholds | DRF-001, PRV-005 |
| DRC-002 | Unsanctioned Change Classification | Receive elevated-severity alert when change has no corresponding Requested State record | — | Configure unsanctioned change detection; manage severity escalation rules | DRC-001 |
| DRC-003 | Drift Severity Classification | Receive severity-classified drift records (minor/significant/critical) based on field criticality × change magnitude | — | Declare field criticality in Resource Type Specifications; configure magnitude thresholds per profile | DRC-001, GOV-003 |
| DRC-004 | Drift Resolution Tracking | View drift record status (open/acknowledged/resolved/escalated); receive resolved notification when next discovery confirms clean state | — | Monitor drift resolution rates; configure escalation policies for aged-open drift records | DRC-001, DRF-004 |
| DRC-005 | Governance Matrix Drift Integration | — | — | Configure governance matrix check in drift comparison pipeline: expected provider changes are not flagged as drift | DRC-001, GMX-001 |


## 20. Federated Contribution Model

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| FCM-001 | Consumer Policy Authoring | Author and submit tenant-domain policies (Gating Policy, Transformation, Recovery, Lifecycle, Orchestration Flow, Governance Matrix rules) via API or Flow GUI; receive PR URL and shadow mode results | — | Configure consumer policy authoring permissions (policy_author role); manage review requirements per profile | POL-001, IAM-003, IAM-007 |
| FCM-002 | Provider Resource Type Publication | — | Publish Resource Type Specifications and Catalog Items for offered resource types via provider contribution API; receive registry PR for platform admin review | Manage provider contribution registry; configure review requirements for provider specs; manage Organization-tier registry | PRV-001, GOV-003 |
| FCM-003 | Provider Service Layer Contribution | — | Contribute Service Layers for offered resource types; layers applied during request assembly for all consumers requesting that resource type | Review and activate provider-contributed layers; manage layer compatibility | PRV-001, LAY-002 |
| FCM-004 | Consumer Resource Group and Definition Contribution | Author and manage resource groups, notification subscriptions, webhook registrations, and cross-tenant authorization records within own Tenant | — | Configure contribution permissions per role; manage Tenant-scoped artifact lifecycle | IAM-007, GOV-002 |
| FCM-005 | Federation Contribution (Peer DCM) | — | Peer DCM contributes registry entries, policy templates, and service layers via federation channels | Manage federation contribution trust posture (verified/vouched/provisional); configure review requirements per trust posture; manage cross-DCM artifact lifecycle | FED-001, GOV-003, POL-003 |
| FCM-006 | Contribution Review and Lifecycle | View contribution status (proposed, pending_review, active, withdrawn); withdraw a pending contribution; receive notification when contribution is approved or rejected | Receive notification when provider contributions are reviewed | Review and approve/reject contributions via Admin API; manage shadow review periods; assign new owners to orphaned artifacts | POL-002, POL-003 |
| FCM-007 | Contributor Scope Enforcement | Receive clear DENY response when attempting to contribute outside permitted domain scope | Receive DENY when contributing specs for resource types not offered | Monitor Governance Matrix enforcement at contribution time; configure scope violation audit and notification | GMX-001, GMX-002 |

---


## 21. Scoring Model

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| SMX-001 | Operational Gating Policy Scoring | Receive risk score and score_drivers with request acknowledgment; understand why score is at its level | Declare `enforcement_class: operational` and `scoring_weight` on contributed Gating policies | Configure operational Gating policies with appropriate weights; manage per-policy enforcement class | POL-001, REQ-004 |
| SMX-002 | Advisory Validation and Completeness Score | Receive advisory_warnings list with request acknowledgment; understand what optional improvements exist | Declare `output_class: advisory` on advisory Validation policies | Configure advisory Validation policies; manage completeness score thresholds | POL-001, REQ-004 |
| SMX-003 | Actor Risk History Tracking | View own risk history score and contributing events via Consumer API | — | Monitor actor risk history; reset scores for trusted automation accounts; configure decay parameters | AUD-001, IAM-001 |
| SMX-004 | Quota Pressure Scoring | Receive quota_pressure as a score driver when approaching Tenant quota limits | — | Configure per-resource-type quota limits; manage free_threshold parameter | IAM-007, REQ-004 |
| SMX-005 | Provider Accreditation Richness Scoring | — | Benefit from lower risk contribution by maintaining rich accreditation portfolio | Configure accreditation richness weights; manage portfolio scoring | ACC-001, PRV-001 |
| SMX-006 | Profile Scoring Threshold Management | — | — | Configure approval routing thresholds per profile (auto/reviewed/verified/authorized + custom tiers via named-tier list); manage signal weights; enforce SMX-008 (max auto_approve_below: 50) | POL-005, REQ-004 |
| SMX-007 | Policy Enforcement Class Override | — | Contribute policies with declared enforcement_class; receive notification when profile overrides enforcement class | Declare per-profile enforcement class overrides; manage regulatory_mandate flag to protect compliance-class policies from demotion | POL-004, POL-005 |
| SMX-008 | Score Audit Trail | Query risk score and routing decision for own requests; view score_drivers and advisory_warnings | — | Query full Score Record detail including signal breakdown and actor risk history; manage score audit retention | AUD-001, REQ-004 |
| SMX-009 | Scoring Weight Range Enforcement | — | Declare operational Gating Policy scoring_weight between 1 and 100 | Enforce weight range at policy activation; reject out-of-range weights | SMX-001 |
| SMX-010 | Score Breakdown Audit Inclusion | View score breakdown in request audit record | — | Configure score breakdown storage in Audit Store for all scored requests | SMX-001, AUD-001 |

---


## 22. Composite Service Composition

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| CMP-001 | Composite Service Request | Request a Composite Service as a single catalog item; receive composite entity UUID; track composite execution status via standard request status endpoint | Register Composite Service with constituent specification; implement standard Services API for `self` constituents | Configure Composite Service registration; manage composite catalog items | CAT-001, REQ-007, PRV-001 |
| CMP-002 | Dependency-Ordered Constituent Execution | — | Implement standard Services API for `self` constituents (DCM derives ordering from depends_on declarations) | Configure composition model; monitor execution round progress via status events | CMP-001, PRV-003 |
| CMP-003 | Partial Delivery and DEGRADED State | Receive DEGRADED composite entity when partial delivery is accepted; choose to accept or reject degraded state | Declare partial_delivery_supported and required_for_delivery per constituent; return standard realized state per constituent | Configure accept_degraded_delivery per profile; manage degraded notification urgency | CMP-001, PRV-005 |
| CMP-004 | Composite Compensation | Receive notification and recovery decision when a Composite Service fails; approve or reject compensation | Implement standard decommission for `self` constituents (DCM dispatches in dependency-reverse order); guarantee idempotent decommission calls | Configure compensation timeout; manage PARTIALLY_COMPENSATED orphan detection | CMP-001, LCM-007, DRC-001 |
| CMP-005 | Transparent Constituent Visibility | Query and manage DCM-visible constituent entities independently (when transparency mode); receive constituent-level drift alerts | Declare composition_visibility mode; register transparent constituents with deterministic UUIDs | Configure visibility mode per composite resource type; manage constituent entity lifecycle policies | CMP-001, DRF-001 |
| CMP-006 | Composite Execution Status Tracking | Monitor composite execution round progress via request status; see component-level status during long-running compositions | Send intermediate status events to DCM during execution; declare status_reporting.interval | Monitor composite execution health; configure execution timeout alerts | CMP-001, REQ-008 |
| CMP-007 | Nested Composite Service Composition | Request high-order Composite Services composed of other Composite Services (max depth 3) | Register a Composite Service whose constituents include other Composite Services; declare max_nesting_depth | Configure nesting depth limits; manage nested compensation chains | CMP-001, PRV-009 |
| CMP-008 | Composite Service Nesting Depth Enforcement | — | Declare nesting depth in Composite Service registration | Enforce maximum nesting depth of 3 at placement time; reject deeper compositions | CMP-001 |

---


## 23. Credential Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| CPX-001 | Resource Credential Issuance | Receive credential metadata and retrieval URL with realized resource; retrieve credential value via authenticated endpoint | Declare credential requirements in Resource Type Spec; receive credential issuance confirmation | Register service_provider with Credential.* resource types; configure credential types and lifetimes per resource type; manage issuance policies | PRV-005, ZTS-002 |
| CPX-002 | DCM Interaction Credential Issuance | — | Validate scoped interaction credential on every DCM dispatch; reject interactions without valid scoped credential (CPX-002) | Configure interaction credential lifetime per profile; manage secrets table for DCM-internal credentials | ZTS-002, PRV-001 |
| CPX-003 | Credential Rotation | Receive rotation notification before old credential expires; retrieve new credential during transition window | Implement rotate endpoint; honor transition window; notify DCM when rotation is complete | Configure rotation schedules and transition windows per credential type; manage pre-expiry rotation warnings | CPX-001, IAM-001 |
| CPX-004 | Emergency Rotation and Security Event Response | Receive immediate notification on emergency rotation; retrieve new credential via fastest channel | Implement immediate revocation with no transition window on security_event trigger | Configure security event triggers; manage emergency rotation audit trail; notify platform admin | CPX-003, OBS-004 |
| CPX-005 | Credential Revocation | Receive revocation notification when credentials are revoked (actor deprovisioned, entity decommissioned); confirm transition to new credential | Implement revoke endpoint with declared SLA; invalidate value immediately on emergency revocation | Manage Credential Revocation Registry; configure revocation cache TTL per profile (PT1M standard, PT30S fsi/sovereign); enforce CPX-007 (decommission blocks on credential revocation) | CPX-001, LCM-007 |
| CPX-006 | Revocation Propagation | — | Refresh revocation cache within profile-governed TTL; validate credential UUID against cache at use time (not only at receipt) | Configure revocation cache TTL; monitor revocation propagation latency; alert on SLA violations | CPX-005, IAM-001 |
| CPX-007 | Audit Trail for Credential Lifecycle | View own credential record history (issue, rotate, revoke events); every value retrieval audited with retrieval_uuid | — | Query full credential audit trail including retrieval count; manage credential audit retention | CPX-001, AUD-001 |
| CPX-008 | IP-Bound Credentials for fsi/sovereign | — | — | Enforce IP binding (bound_to_ip) on all credentials issued for fsi and sovereign profiles | CPX-001, ZTS-002 |
| CPX-009 | Algorithm and Key Usage Declaration | — | Declare algorithm and key_usage on credential records at issuance | Enforce declaration at issuance; reject credentials without declared algorithm | CPX-001 |
| CPX-010 | Idle Credential Detection | Receive notification when credential reaches idle threshold | — | Configure idle_detection_threshold per profile; enforce alert-only action | CPX-001 |
| CPX-011 | Compliance Domain Additive Credential Requirements | — | — | Enforce additive credential requirements when compliance domains are active on a profile | CPX-001, POL-005 |
| CPX-012 | Credential Value Store Isolation (All Profiles) | — | — | Enforce credential values never stored in DCM stores in ALL profiles including minimal | CPX-001 |

---


## 24. Authority Tier Model

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ATM-001 | Authority Tier Registry | Reference approval decisions by tier name; tier weight resolved dynamically from ordered list | Implement approval workflows that reference tier names (not hardcoded weights) | Manage the ordered authority tier list; control tier positions and gravity values | POL-005 |
| ATM-002 | Custom Tier Definition | — | — | Contribute custom tiers between existing tiers; declare decision_gravity and dcm_gate semantics; requires verified-tier approval | ATM-001, FCM-001 |
| ATM-003 | Dynamic Threshold Configuration | View which tier an action routes to | — | Configure profile approval_routing as named-tier threshold list; adjust score ranges when new tiers inserted | ATM-001, SMX-001 |
| ATM-004 | Tier Registry Change Impact Detection | Receive notification when tier changes affect owned resources or pending approvals | — | Propose tier registry changes; receive tier impact diff report; review SECURITY_DEGRADATION and BROKEN_REFERENCE items; accept degradations via Admin API | ATM-001, AUD-001 |
| ATM-005 | Degradation Review Gate | — | — | Review and explicitly accept each SECURITY_DEGRADATION item before a registry change activates; provide compensating control rationale; must hold verified or authorized tier reviewer role | ATM-004, IAM-001 |
| ATM-006 | Profile Gap Detection | — | — | Receive PROFILE_GAP warnings when tier registry changes leave profile threshold lists incomplete; update threshold lists or acknowledge gap within approval window | ATM-003, ATM-004 |
| ATM-007 | Tier Registry Audit Trail | Query historical tier registry versions and impact reports | — | Access full audit trail of all tier registry changes: proposal, impact assessment, degradation acceptances, activation | ATM-004, AUD-001 |
| ATM-008 | Approval Record Tier Weight Snapshot | — | — | Store tier name and resolved weight at approval record creation; historical records retain weight for audit comparison across regime changes | ATM-001 |
| ATM-009 | Tier Registry Degradation Gate | Receive notification when tier change produces degradation affecting owned resources | — | Block tier registry activation on SECURITY_DEGRADATION items; require verified-tier acceptance per item | ATM-001 |
| ATM-010 | Broken Reference Gate | — | — | Block tier registry activation when BROKEN_REFERENCE items exist (removed tier still referenced in active config) | ATM-001 |
| ATM-011 | Tier Change Impact Report | — | — | Generate and store tier impact report in Audit Store at proposal and activation time | ATM-001, AUD-001 |
| ATM-012 | Profile Gap Warning on Tier Insertion | — | — | Detect PROFILE_GAP when new tier inserted but profile threshold list not updated; emit non-blocking warning | ATM-001, POL-005 |

---


## 25. Event Catalog

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| EVT-001 | Event Subscription | Subscribe to DCM events via notification service_provider or Message Bus; filter by event type, entity type, urgency; idempotency via event_uuid | Publish standard events when provider actions occur; use reverse-DNS prefix for non-standard events | Configure notification service_provider channels and audience routing | IAM-001, OBS-001 |
| EVT-002 | Request Pipeline Events | Receive real-time status of own requests (submitted → intent_captured → policies_evaluated → requires_approval → approved → dispatched → realized/failed) | — | Configure request event delivery per profile; manage urgency routing | REQ-001 |
| EVT-003 | Entity Lifecycle Events | Receive entity lifecycle events (realized, state_changed, ttl_warning, decommissioning, etc.) for owned entities and entities with stakes | — | Configure entity event delivery; manage stakeholder audience routing | LCM-001 |
| EVT-004 | Security and Critical Events | Receive critical security events (audit chain alerts, sovereignty violations, unsanctioned provider writes) regardless of subscription preferences | — | Configure non-suppressable event delivery; manage security team routing | AUD-001, ZTS-001 |
| EVT-005 | Approval Pipeline Events | Receive approval events (requires_approval, decision_recorded, quorum_reached, window_expiring, expired) for own requests and approvals | — | Configure reviewer notification routing; manage approval window alerts | ATM-001, IAM-001 |
| EVT-006 | Provider and Infrastructure Events | — | Publish provider health events (registered, healthy, unhealthy, degraded); publish provider_update events on entity changes | Monitor provider health events; configure provider degradation alerts | PRV-001 |
| EVT-007 | Tier Registry and Governance Events | — | — | Receive tier_registry events (proposed, impact_assessed, degradation_detected, activated); configure governance event routing | ATM-004 |

---


## 26. API Versioning

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| VER-001 | Version Discovery | Discover available API versions and their status via `GET /.well-known/dcm-api-versions`; learn current, supported, and deprecated versions; get changelog and migration guide URLs | Declare supported OIS version in capability registration | Monitor version adoption; manage sunset schedules | — |
| VER-002 | Breaking Change Governance | Receive at least the profile-governed deprecation notice period before a breaking change takes effect; continue using deprecated versions until sunset date | Receive OIS version deprecation notice; migrate to new OIS version before sunset | Declare new major versions; configure deprecation timeline per profile; ensure VER-002 (breaking change definition) is applied | VER-001 |
| VER-003 | Deprecation Headers | Receive `Deprecation`, `Sunset`, and `Link` headers on all responses from deprecated API versions (RFC 8594/RFC 9745); use these to drive migration priority | — | Configure header injection for deprecated versions; ensure headers are accurate | VER-002 |
| VER-004 | Migration Guide | Access machine-readable migration guide at `GET /api/v{N}/migration-guide`; understand all breaking changes from previous version with migration instructions | Access OIS migration guide at `GET /provider/api/v{N}/migration-guide` | Maintain migration guides for all new major versions (required by VER-008) | VER-002 |
| VER-005 | Preview Endpoints | Access preview endpoints at `/api/v{N}/preview/`; understand stability commitment is none; provide feedback before graduation | — | Mark endpoints as preview; graduate to stable in new major version | VER-001 |
| VER-006 | Latest Alias Production Warning | — | — | Support `latest` version alias; emit response header discouraging production use | VER-001 |
| VER-007 | Preview Endpoint Instability Declaration | — | — | Mark preview endpoints explicitly; may change or be removed without major version bump | VER-001 |
| VER-009 | Provider Dispatch Compatibility | — | Maintain backward compatibility with DCM dispatch payloads from supported prior versions | Manage provider dispatch versioning; maintain supported version matrix | VER-001 |

---


## 27. Session Revocation

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| SES-001 | Session Lifecycle Management | View own active sessions; logout single session (DELETE /api/v1/auth/session); logout all sessions; revoke specific session by UUID | — | Force revoke sessions for any actor; view session store health | IAM-001, AUTH-001 |
| SES-002 | Actor Deprovisioning Session Revocation | — | — | Parallel session + credential revocation on actor deprovisioning; deprovisioning not acknowledged until both complete (AUTH-016) | SES-001, CPX-005 |
| SES-003 | Emergency Session Revocation | Receive critical notification on security-event session revocation | — | Trigger emergency revocation (security_event); revocation propagates within profile SLA (PT5S sovereign to PT30S standard) | SES-001, EVT-001 |
| SES-004 | Token Introspection | — | Call POST /api/v1/auth/introspect to validate bearer tokens without maintaining own revocation cache | Configure introspection endpoint access; manage introspection scope grants | SES-001, IAM-001 |
| SES-005 | Concurrent Session Enforcement | Oldest session auto-revoked when new session exceeds concurrent limit; receive notification via notification service_provider | — | Configure concurrent_sessions limit per profile; monitor session counts | SES-001 |
| AUTH-017 | Session Revocation Propagation SLA | — | — | Propagate revocation to Session Revocation Registry within profile SLA (PT5S sovereign → PT30S standard) | SES-001 |
| AUTH-018 | Per-Request Revocation Registry Check | — | Check Session Revocation Registry on each request bearing a bearer token | Configure revocation registry query path; manage registry availability | SES-001 |
| AUTH-019 | Emergency Revocation No-Grace Period | Receive critical notification on emergency revocation | — | Emergency session revocation fires immediately with no grace period | SES-003 |
| AUTH-020 | Introspection Endpoint Authentication | — | Authenticate introspection calls using provider interaction credential | Configure introspection scope grants; manage endpoint access | SES-004 |
| AUTH-021 | Oldest Session Revocation on Limit | Receive notification when oldest session is auto-revoked | — | Configure concurrent_sessions limit; enforce oldest-first revocation order | SES-005 |
| AUTH-022 | Refresh Token Invalidation on Session Revoke | — | — | Invalidate refresh token when parent session is revoked; return REVOKED_SESSION error on use | SES-001 |

---

## 28. Internal Component Authentication

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ICOM-001 | Component Identity and mTLS | — | — | Manage Internal CA; issue and rotate component certificates; all inter-component calls use mTLS (ICOM-001) | ZTS-001, CPX-001 |
| ICOM-002 | Component Bootstrap | — | — | Generate one-time bootstrap tokens (PT1H max lifetime); components acquire first certificate via bootstrap token; token invalidated after single use (ICOM-007) | ICOM-001 |
| ICOM-003 | Internal Call Authorization | — | — | Declare allowed_sources per internal endpoint; declare allowed_targets per component; unauthorized source calls rejected with ICOM_UNAUTHORIZED_SOURCE audit record (urgency: high) | ICOM-001, AUD-001 |
| ICOM-004 | Internal Interaction Credentials | — | — | Every internal call presents a scoped ZTS-002 interaction credential in addition to mTLS; credential scoped to specific operation and target component | ICOM-001, CPX-002, ZTS-002 |
| ICOM-005 | Component Certificate Revocation | — | — | Compromised component certificates added to Internal CA CRL immediately; CRL cache refresh within profile SLA (PT15S sovereign to PT1M standard); ICOM_CERT_COMPROMISED audit record (urgency: critical) | ICOM-001, AUD-001 |
| ICOM-006 | Component Certificate Maximum Validity | — | — | Issue internal component certificates with maximum validity P90D; enforce expiry and rotation | ICOM-001 |
| ICOM-008 | Compromised Certificate Immediate CRL | — | — | Add compromised internal component certificates to Internal CA CRL immediately; propagate within PT60S | ICOM-001 |
| ICOM-009 | Trust Anchor Registration | — | — | Register root or intermediate CA as trust anchor for internal mTLS; reject certificates not chaining to registered trust anchor | ICOM-001 |

---


## 29. Scheduled and Deferred Requests

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| SCH-001 | Request Scheduling | Submit requests with schedule.dispatch: at/window/recurring; SCHEDULED requests visible in GET /api/v1/requests; cancellable before dispatch; receive request.scheduled event | — | Manage Maintenance Windows; configure Request Scheduler; monitor scheduled queue depth | REQ-001 |
| SCH-002 | Maintenance Windows | Reference maintenance windows in scheduled requests; view available windows at GET /api/v1/maintenance-windows | — | Create/manage/suspend maintenance windows; approve window schedules; configure platform-wide windows | SCH-001, GOV-001 |
| SCH-003 | Dual Policy Evaluation | — | — | Understand that scheduled requests run Gating Policy at declaration AND at dispatch; dispatch-time failure → FAILED with schedule_policy_rejection (SCH-003) | SCH-001, POL-001 |
| SCH-004 | Deadline Enforcement | Set not_after on scheduled requests; receive request.failed(schedule_deadline_missed) if deadline passes without dispatch | — | Monitor deadline miss rates; configure alerting on deadline misses | SCH-001, EVT-001 |
| SCH-005 | Not-After Expiry Failure | Receive FAILED status when scheduled request expires before dispatch | — | Configure not_after enforcement; manage SCHEDULE_EXPIRED recovery policy | SCH-001 |
| SCH-006 | Maintenance Window Platform Authorization | — | — | Require platform_admin or tenant_admin authority to create/modify Maintenance Windows | SCH-004 |

---

## 30. Request Dependency Graph

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| RDG-001 | Dependency Group Submission | Submit POST /api/v1/request-groups with requests and depends_on declarations; local refs within submission; receive group_uuid and per-request entity_uuids | — | Monitor group queue depth; configure max group size | REQ-001 |
| RDG-002 | Field Injection | Declare inject_fields to pass realized output fields (e.g. IP address) from dependency into dependent request fields automatically at dispatch time | — | — | RDG-001, REQ-001 |
| RDG-003 | PENDING_DEPENDENCY Status | Track dependent requests in PENDING_DEPENDENCY status; cancel pending requests individually or cancel whole group; receive request.pending_dependency and request.dependency_met events | — | Monitor PENDING_DEPENDENCY queue depth; detect stalled groups | RDG-001, EVT-001 |
| RDG-004 | Group Failure Handling | Configure on_failure: cancel_remaining or continue; group-level timeout; group status via GET /api/v1/request-groups/{uuid} | — | Monitor group failure rates | RDG-001 |
| RDG-005 | Group-Level Timeout Enforcement | Receive TIMEOUT failure when group-level timeout elapses | — | Configure group_timeout independent of individual request timeouts | RDG-001 |
| RDG-006 | Single Group Membership Enforcement | — | — | Reject attempts to add a request to more than one dependency group | RDG-001 |

---

## 31. DCM Self-Health

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| HLT-001 | Liveness Probe | — | — | GET /livez: fast liveness check (PT5S max, no external calls); Kubernetes restarts pod on failure; unauthenticated | — |
| HLT-002 | Readiness Probe | — | — | GET /readyz: checks Session Store, Audit Store, Policy Engine, Message Bus, Auth Provider connectivity; Kubernetes removes from LB on failure; startup sequence observable via readyz | — |
| HLT-003 | Component Health Detail | — | — | GET /api/v1/admin/health: per-component status (pass/warn/fail), metrics, queue depths, provider/auth summary; admin auth required | IAM-001 |
| HLT-004 | Prometheus Metrics | — | — | GET /metrics: Prometheus scrape endpoint; request pipeline, policy, session, drift, provider, internal CA metrics | OBS-001 |
| HLT-005 | Prometheus Metrics Endpoint | — | — | Expose Prometheus-compatible metrics at GET /metrics including request throughput, store latency, policy eval time, provider health counters | HLT-001 |
| HLT-006 | Startup Readiness via /readyz | — | — | Report PASSING on /readyz only after all required stores available and bootstrap complete | HLT-001 |

---


## 32. Operational Reference

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| OPS-001 | Data Store Partitioning | — | — | Declare partitioning strategy in deployment manifest; execute tenant-shard, per-tenant, or time-based archiving migration; configure shard routing and mirror lag monitoring | STO-001 |
| OPS-002 | Store Migration | — | — | Execute dual-write migration between store implementations; maintain audit chain continuity across cutover; enforce profile-governed burn-in before source decommission | STO-001, AUD-001 |
| OPS-003 | Disaster Recovery | — | — | Execute scenario-specific recovery procedures (component/store/full-CP/repave); meet profile-governed RTOs (PT1M–PT15M component, PT5M–PT2H store, PT5M–PT30M full-CP); complete post-recovery validation checklist | HLT-001, AUD-001 |
| OPS-004 | Backup Management | — | — | Configure PostgreSQL backup schedules (PITR for all data domains); enforce P365D minimum audit retention | STO-001 |

---


## 33. Web Interfaces

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| GUI-001 | Consumer Portal — Catalog, Requests, Resources | Browse catalog; live cost estimate; submit requests with scheduling and dependency groups; live SSE status with constituent tracking; cross-resource drift report; consumer-scoped audit trail with correlation ID trace | — | — | CAT-001, REQ-001, SCH-001, RDG-001, EVT-002 |
| GUI-002 | Consumer Portal — Live Request Status | Real-time status via SSE stream (status_change, progress_updated, approval events, heartbeat); constituent status for composite requests; approval flow inline; fallback to polling | — | — | REQ-001, EVT-002 |
| GUI-003 | Consumer Portal — Resource Management | View/filter owned resources by state and type; lifecycle state badges; drift indicator; resource detail with Overview/Drift/Audit/Cost/Credentials/Relationships/Groups tabs; state-sensitive action buttons; bulk operations | — | — | LCM-001, DRF-001, AUD-001 |
| GUI-004 | Consumer Portal — Session and Security | View active sessions; revoke individual or all other sessions; step-up MFA prompt for gated operations; tenant context selector; role-gated navigation (hide not disable) | — | — | SES-001, IAM-001 |
| GUI-005 | Admin Panel — Platform Dashboard | Control plane component health grid; provider health summary; pending approvals count; open drift records by severity; request throughput; all driven by GET /api/v1/admin/health | — | Platform Admins, SREs configure dashboard widgets; role-gated sections | HLT-003 |
| GUI-006 | Admin Panel — Governance and Approvals | Approval queue (all tenants); approval detail with risk score breakdown; authority tier registry editor (drag-and-drop reordering, impact report visualization, degradation acceptance flow); scoring threshold editor (auto_approve_below ≤ 50 hard-stop) | — | Policy Owners and Platform Admins | ATM-004, SMX-001 |
| GUI-007 | Admin Panel — Audit and Compliance | Platform-wide cross-tenant audit trail; pre-built compliance reports (SOC 2, FedRAMP, HIPAA); audit chain integrity status; correlation ID trace; session and security event feed | — | Auditors, Security team, Platform Admins | AUD-001, SES-003 |
| GUI-008 | Provider Management — Common Shell | Overview, configuration, health history, audit trail, and notification tabs per provider, organized by declared CAPABILITY (not a fixed 11-type taxonomy — ADR-005); provider owner role gates access; Platform Admins see all providers | — | Provider owners manage own providers; Platform Admins manage all | PRV-001, IAM-001 |
| GUI-009 | Provider Management — Type Extensions | Service Provider: capacity, managed entities, naturalization mapping, realization history; secrets management: inventory, rotation, revocation, external CA config, algorithm compliance; authentication capability: session stats, SCIM sync, connection status (auth is a capability, not a standalone provider type — ADR-005); external policy evaluation: trust level, contribution pipeline | — | Provider owners access type-specific tabs for their provider type | GUI-008, PRV-001 |
| GUI-011 | RHDH Plugin Suite | Use DCM capabilities within Red Hat Developer Hub (RHDH) or Backstage via Dynamic Plugins (@dcm/backstage-plugin-*); no RHDH rebuild required for updates | — | Configure RHDH app-config.yaml with DCM connection; configure Dynamic Plugin loading |
| GUI-012 | Scaffolder Template Auto-Generation | DCM catalog items automatically generate Backstage Software Templates; new resource types appear as templates without UI code; field schema → JSON Schema → Scaffolder form | — | Configure @dcm/backstage-plugin-catalog-backend; template generation is automatic |
| GUI-013 | DCM Entity Provider | DCMService (catalog items) and DCMResource (realized entities) appear in RHDH Software Catalog; entities sync every PT5M; search-indexed; tenancy enforced via namespace | — | Service account credential configuration; sync interval configuration |
| GUI-014 | ITSM Integration Bridge | View ITSM references (ServiceNow, Jira) on resource entity Overview tab; link change records to DCM requests; see ITSM-sourced approval votes in request status; CMDB reference on entity pages | ITSM systems receive DCM lifecycle events via notification service_provider and call Admin API to record approval votes; CMDB sync via webhook subscription | Configure ITSM notification service_provider; map DCM event → ITSM action; configure CMDB field mapping | EVT-001, GUI-002 |
| GUI-010 | Unified Shell | Single DCM web application with role-gated surfaces: Consumer Portal (all actors), Admin Panel (platform roles), Provider Management (provider_owner role), Flow GUI link (policy_owner/sre); one login, one session; no separate applications | — | Platform Admins configure which surfaces are available | IAM-001, SES-001 |

---


## 34. ITSM Integration

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| ITSM-001 | ITSM integration Registration | — | Register as ITSM integration with declared capabilities (supported_actions, itsm_system, field_mapping_ref, cmdb_ci_type_map); implement standard OIS health check | Register ITSM integrations; review and approve ITSM integration registrations; configure inbound webhook authentication | PRV-001, CPX-001 |
| ITSM-002 | Outbound ITSM Record Creation | View ITSM references on resource entities (change request, incident, CMDB CI links with deep links to ITSM system) | Receive action requests from DCM; create/update records in ITSM system; return record ID for storage on entity | Configure ITSM Policies (create_change_request, create_incident, update_cmdb_ci); configure block_until_created for compliance gates | ITSM-001, POL-001 |
| ITSM-003 | Inbound ITSM Approval Routing | — | Verify HMAC signature on inbound webhook; forward ITSM approval decisions to DCM Admin API approval vote endpoint | Configure inbound webhook secret (secrets management); monitor approval routing from ITSM systems (ServiceNow CAB, Jira workflow) | ITSM-001, CPX-001, ATM-001 |
| ITSM-004 | ITSM Policy Authoring | — | — | Author ITSM Action policies with template expressions; configure shadow validation; configure on_failure behavior; use block_until_created for pipeline gates (with mandatory timeout per ITSM-005) | ITSM-001, POL-001 |
| ITSM-005 | CMDB Synchronization | View CMDB CI reference on resource entities; CI auto-created on realization, auto-retired on decommission | Receive create_cmdb_ci and retire_cmdb_ci actions; maintain dcm_entity_uuid correlation on CMDB CI records | Configure CMDB CI type mapping per resource type; monitor CMDB sync failures | ITSM-001, ITSM-002 |
| ITSM-006 | ITSM Field Mapping Declaration | — | — | Declare field mappings between DCM entity fields and ITSM CI types in ITSM integration config; validate against Resource Type Specs | ITSM-001 |
| ITSM-007 | ITSM Policy Template Expression Validation | — | — | Validate template expressions in ITSM Policy action_payload at policy activation; reject unresolvable expressions | ITSM-001, POL-003 |

---


## 35. Provider Callback Authentication

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|
| PCA-001 | Two-Layer Provider Callback Authentication | — | Present valid mTLS certificate (Layer 1) and provider callback credential (Layer 2) on every call to DCM callback endpoints | Configure DCM CA trust anchor; issue provider callback credentials at activation; enforce both layers | PRV-001, ZTS-001 |
| PCA-002 | Provider Callback Credential Scope Enforcement | — | Use callback credential scoped to own provider_uuid only; cannot act on other providers | Enforce credential scope at validation; reject cross-provider credential use | PRV-001 |
| PCA-003 | Entity-Level Callback Authorization | — | Receive 403 ENTITY_NOT_OWNED_BY_PROVIDER when pushing state for entities not dispatched to this provider | Enforce per-call entity ownership check independent of credential validity | PRV-001, REQ-007 |
| PCA-004 | Scope Violation Auto-Suspension | Receive critical notification when owned provider is suspended due to scope violations | — | Auto-suspend provider and notify platform admin after 5 consecutive scope violations within PT1H | PRV-001, ZTS-001 |
| PCA-005 | Callback Credential Issued by secrets management | — | Retrieve callback credential via secrets management at activation; not directly from API Gateway | Issue callback credentials exclusively through secrets management; reject direct credential issuance requests | PRV-001, CPX-001 |
| PCA-006 | Registration Token Single-Use Enforcement | — | Use registration token for initial registration only; obtain callback credential after activation | Invalidate registration token after first successful use regardless of expiry timestamp | PRV-001 |
| PCA-007 | Sovereignty Change Re-Registration | — | Submit new registration with new registration token when sovereignty declaration changes | Require new registration token and approval pipeline for sovereignty declaration changes | PRV-001, GMX-004 |
| PCA-008 | Callback Credential Pre-Expiry Rotation | — | Implement credential refresh; receive new credential before old expires during transition window | Initiate rotation before expiry; maintain transition window (50% of credential lifetime) | PRV-001, CPX-001 |
| PCA-009 | IP-Bound Callback Credentials for fsi/sovereign | — | Present callback calls from declared bound_to_ip address for fsi/sovereign profiles | Enforce IP binding on callback credentials for fsi and sovereign profiles | PCA-001, CPX-008 |
| PCA-010 | All Inbound Provider Calls Produce Audit Records | — | — | Write audit record for every inbound provider call including rejected calls; no silent failures | PCA-001, AUD-001 |

---


## 36. Workload Analysis

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|| WLA-001 | Automated Workload Classification | View workload profile for owned resources; see archetype, resource type match, confidence | Report resource metadata via discovery for classification input | Configure classification ruleset version; review low-confidence classifications manually | DRC-001, INF-001 |
| WLA-002 | Migration Readiness Scoring | View containerization score and migration blockers for owned resources | Report workload characteristics that inform migration scoring | Configure migration readiness thresholds; integrate MTA Information Provider | WLA-001 |
| WLA-003 | MTA Information Provider Integration | — | Implement workload_analysis information type OR delegate to MTA | Register MTA as Information Provider; configure analysis trigger policies | WLA-001, INF-001 |
| WLA-004 | On-Demand Re-Analysis | Request re-analysis when resource role changes (`POST /resources/{uuid}/workload-profile:analyze`) | — | Trigger re-analysis for any resource; override archetype manually with reason | WLA-001 |
| WLA-005 | WorkloadProfile Audit Chain | View analysis history for owned resources | — | Query full analysis history including superseded profiles | WLA-001, AUD-001 |
| WLA-006 | Low-Confidence Manual Review Gate | Receive notification when owned resource requires manual classification | — | Review and resolve low-confidence classifications; unblock ingestion | WLA-001, LCM-001 |

---


## 37. Accreditation Monitoring

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|| ACM-001 | Tier 1 External Registry Verification | — | Declare `external_registry_id` at registration for FedRAMP, CMMC, ISO 27001 | Configure registry poll intervals; review status change alerts; manage `external_registry_id` accuracy | PRV-001, ACR-001 |
| ACM-002 | Tier 2 Document Currency Verification | — | Maintain current `certificate_ref` and `audit_report_ref` URLs pointing to valid, accessible documents | Configure `max_age` per framework; review document expiry alerts; upload new reports when notified | PRV-001, ACR-001 |
| ACM-003 | Tier 3 Contract Webhook Integration | — | Configure contract management webhook for BAA and DoD IL accreditations | Register contract system; configure inbound webhook credential; receive BAA/contract lifecycle events | PRV-001, ACR-001 |
| ACM-004 | Verification Staleness Enforcement | — | Ensure monitoring infrastructure can reach DCM to deliver verification events | Configure stale_after thresholds and stale_action per profile; enforce sovereign/fsi minimum tier requirements | ACM-001, ACR-001 |
| ACM-005 | Immediate Revocation on External Revoke | Receive notification when provider accreditation is revoked; understand service impact | — | Review `accreditation.status_changed` events; confirm immediate revocations; trigger recovery policy | ACM-001, ACR-001 |
| ACM-006 | Verification Currency in Scoring | — | Maintain verification currency to maximize accreditation richness score | Monitor verification multiplier impact on provider placement; prioritize externally verified providers | ACM-001, SMX-001 |
| ACM-007 | Manual Override in Air-Gapped Mode | — | — | Manually update `last_verified_at` with justification in air-gapped deployments; maintain audit trail of manual verifications | ACR-001, AUD-001 |

---


## 38. Location Topology Management

| ID | Capability | Consumer | Service Provider | Platform/Admin | Depends On |
|----|-----------|---------|---------|---------------|-----------|| LOC-001 | Location Type Registry | Browse available location types (standard and custom) | Declare supported locations in provider registration capability declaration | Register custom location types; manage standard type definitions; deprecate types | PRV-001 |
| LOC-002 | Location Node Management | Browse available locations via `GET /api/v1/locations`; filter by resource type, data classification, sovereignty zone | Declare which location nodes (DC, Zone, etc.) the provider serves at registration | Create, version, and retire location layer instances via GitOps; update mutable capacity fields | LOC-001 |
| LOC-003 | Location Selection at Request Time | Submit `location_uuid` or `location_handle` with service request; select at any level (Country through Rack); DCM refines to specific DC at placement | — | Configure default location selection rules; enforce location-based placement policies | LOC-001, LOC-002 |
| LOC-004 | Location Layer Assembly | Transparent — full location context injected into payload automatically | Receive full location context in dispatch payload (location.country_code, location.zone_code, location.dc_code, etc.) | Configure layer assembly order; define location-level field overrides | LOC-002, DLM-001 |
| LOC-005 | Location-Based Sovereignty Enforcement | See sovereignty zone and data residency on each location node | Declare sovereignty capabilities per served location | Configure `max_data_classification` per location; enforce cross-border policies at location layer | LOC-002, GOV-001 |
| LOC-006 | Location Hierarchy Navigation | Browse parent/child location relationships; query ancestors of a selected node | — | Manage location hierarchy; validate acyclicity on layer submission | LOC-001, LOC-002 |
| LOC-007 | Custom Location Types | Use custom location types in selection (e.g., Fleet/Ship in Navy context) | Declare support for resources at custom location types | Register and manage custom types; define level insertion point in hierarchy | LOC-001 |
| LOC-008 | Location Capacity Visibility | See `capacity_status` (available/limited/full) and `providers_available` count per location | Report capacity scoped to location during reserve query | Update mutable capacity fields (e.g., rack_units_available) without a new layer version | LOC-002, PRV-001 |

---




## 39. Subscription Management (SUB)

| ID | Capability | Consumer | Provider | Platform/Admin | Dependencies |
|----|-----------|----------|----------|----------------|-------------|
| SUB-001 | Create subscription | Submit subscription request with tier and terms | Acknowledge subscription, provision initial entities | Approve subscription creation | CAT-001, REQ-001, POL-001 |
| SUB-002 | Manage subscription lifecycle | Suspend, resume, cancel own subscriptions | Report managed entity status | Force-cancel, view all subscriptions | LCM-001, AUD-001 |
| SUB-003 | Change subscription tier | Request tier upgrade/downgrade | Adjust capacity for managed entities | Approve tier changes requiring admin | POL-001, POL-003 |
| SUB-004 | Subscription renewal | Approve/decline renewal; view renewal status | Honor renewed terms | Configure renewal policies | SCH-001, POL-001 |
| SUB-005 | Provider-originated updates | Approve/reject non-auto updates | Submit updates via standard callback | View update audit trail | PRV-003, AUD-001 |
| SUB-006 | Update channel management | Configure auto_apply per channel | Declare available update channels | Set organization-wide channel policies | POL-001, POL-003 |
| SUB-007 | Subscription cost attribution | View subscription cost | Declare cost model per tier | Configure cost allocation rules | — |
| SUB-008 | Entitlement enforcement | View remaining capacity | Stay within entitlement bounds | Override entitlements in exceptional cases | POL-002 |
| SUB-009 | Grace period management | View grace period; request extension | Continue health reporting during grace | Configure grace period defaults | LCM-001 |
| SUB-010 | Subscription audit trail | View own subscription audit history | — | View all subscription audit records | AUD-001, AUD-002 |

## Capability Count Summary

| Domain | Capabilities |
|--------|-------------|
| Identity and Access Management | 21 |
| Service Catalog | 7 |
| Request Lifecycle Management | 10 |
| Provider Contract and Realization | 16 |
| Resource Lifecycle Management | 7 |
| Drift Detection and Remediation | 5 |
| Policy Management | 7 |
| Data Layer Management | 5 |
| Information and Data Integration | 6 |
| Ingestion and Brownfield Management | 4 |
| Audit and Compliance | 5 |
| Observability and Operations | 8 |
| Storage and State Management | 8 |
| DCM Federation and Multi-Instance | 5 |
| Platform Governance and Administration | 7 |
| Accreditation Management | 6 |
| Zero Trust and Security Posture | 8 |
| Unified Governance Matrix | 7 |
| Drift Reconciliation | 5 |
| Federated Contribution Model | 7 |
| Scoring Model | 10 |
| Composite Service Composition | 8 |
| Credential Management (CPX) | 12 |
| Authority Tier Model | 12 |
| Event Catalog | 7 |
| API Versioning | 8 |
| Session Revocation | 11 |
| Internal Component Authentication | 8 |
| Scheduled and Deferred Requests | 6 |
| Request Dependency Graph | 6 |
| DCM Self-Health | 6 |
| Operational Reference | 4 |
| Web Interfaces | 14 |
| ITSM Integration | 7 |
| Provider Callback Authentication | 10 |
| Workload Analysis | 5 |
| Accreditation Monitoring | 6 |
| Location Topology Management | 7 |
| Subscription Management | 10 |
| **Total** | **311** |
---

## Dependency Map — Critical Path Capabilities

These capabilities block the most downstream work and should be implemented first:

```
IAM-001 (Actor Authentication)
  └── IAM-002 (Session Tokens) → IAM-003 (RBAC) → IAM-007 (Tenant Scope)
        └── CAT-001 (Service Catalog)
              └── REQ-001 (Submit Request)
                    └── REQ-002 (Intent State) → REQ-003 (Layer Assembly)
                          └── REQ-004 (Policy Evaluation) → REQ-005 (Placement)
                                └── REQ-007 (Provider Dispatch)
                                      └── PRV-003 (Realization) → PRV-005 (Realized State)
                                            └── LCM-001 (State Transitions)
                                                  └── DRF-001 (Discovery) → DRF-002 (Drift)

PRV-001 (Provider Registration) — parallel critical path
  └── PRV-002 (Naturalization) → PRV-003 (Realization)
  └── PRV-006 (Capacity Reporting) → REQ-005 (Placement)
```

**Minimum viable DCM capability set (to demonstrate end-to-end lifecycle):**

IAM-001 → IAM-002 → IAM-003 → IAM-007 → CAT-001 → REQ-001 → REQ-002 → REQ-003 → REQ-004 → REQ-005 → REQ-006 → REQ-007 → PRV-001 → PRV-002 → PRV-003 → PRV-004 → PRV-005 → LCM-001 → DRF-001 → DRF-002 → AUD-001

### Findings-review additions (2026-07-07) — capability domains flagged as absent

These domains have ADR backing but were missing from the matrix (consistency review). Rows are
intentionally concise pointers pending the DCM team's detailed capability breakdown:

| ID | Capability | Description | ADR |
|----|-----------|-------------|-----|
| PLP-001 | Placement Policy | Declarative affinity/anti-affinity/spread/co-locate/pin over abstract Topology kinds; the 8th typed policy; engine evaluates + enforces portability | ADR-019 |
| MIG-001 | Migration & Operational Gating | Migration permission (Governance-Matrix) + sequence (Orchestration-Flow) + freshness gating + rehearsal scheduling | ADR-020 |
| TRU-001 | Trust Model / Introduction Grant | Five trust planes; credential-API selection; the Introduction Grant primitive for provider onboarding | ADR-022 |
| ING-005 | Ingestion — claim/adoption + backport | Reverse placement, provider claim (Discovered→Realized), correlation-id entity resolution, Intent backport | ADR-017 |

**21 capabilities for a functional end-to-end demonstration.**

**Note:** FCM-001 through FCM-007 (Federated Contribution Model) are not on the critical path — they extend DCM's multi-user capabilities but are not required for the initial end-to-end lifecycle demonstration.

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
