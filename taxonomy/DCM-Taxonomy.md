# DCM Taxonomy

The DCM taxonomy defines the precise vocabulary used throughout the architecture. Every term used in the data model, specifications, and implementation should conform to these definitions.

**Purpose:** Eliminate ambiguity. When two people use the same word to mean different things, architecture breaks down. This taxonomy prevents that.

---

## Part 1 — Core Vocabulary

### The Three Foundational Abstractions

| Term | Definition |
|------|-----------|
| **Data** | Any structured artifact in DCM with a type, UUID, lifecycle state, fields, data classification, and provenance. Everything that exists, is stored, and has a lifecycle. Entities, layers, policies, accreditations, audit records, groups, relationships — all Data. |
| **Provider** | Any external component DCM calls or that calls DCM. Implements the unified Provider base contract (registration, health, sovereignty, accreditation, governance matrix enforcement, zero trust). What varies between provider types is the capability extension. |
| **Policy** | A rule artifact that fires when Data matches declared conditions, produces a typed output (decision, mutation, action, or directive), and is enforced at a declared level. Policies govern every transition, transformation, and constraint in DCM. |

### Provider Types (11)

| Term | Definition |
|------|-----------|
| **Service Provider** | Typed Provider. Capability: realize infrastructure resources. Implements naturalization, realization, denaturalization, and discovery. A Service Provider can additionally register Composite Services (catalog items composed of multiple constituent resource types) — see the Composite Service Composition Terms section below. |
| **Information Provider** | Typed Provider. Capability: serve authoritative external data (CMDB, HR, Finance, identity). |
| **Data Store Contract** | PostgreSQL store contract defining persistence requirements per data domain (Intent, Requested, Realized, Discovered, Audit). |
| **External Policy Evaluator** | Typed Provider. Capability: evaluate policies externally. Modes 1–4; Mode 3–4 for OPA/Rego sidecar and black-box query enrichment. |
| **credential management service** | Typed Provider. Capability: issue, rotate, and revoke secrets and credentials. |
| **Auth Provider** | Typed Provider. Capability: authenticate actor identities and resolve role/group memberships. |
| **notification service** | Typed Provider. Capability: deliver notification envelopes to configured channels (Slack, PagerDuty, email, webhook). |
| **event routing service** | Typed Provider. Capability: async event streaming between DCM and external systems. |
| **Resource Type Registry** | Typed Provider. Capability: serve the Resource Type Registry (core, community, organization tiers). |
| **Peer DCM** | Typed Provider. Another DCM instance participating in federation. Federation is the Provider abstraction applied across DCM instances. |

### Policy Types (7)

| Term | Definition |
|------|-----------|
| **GateKeeper Policy** | Typed Policy. Declares `enforcement_class: compliance` (boolean deny — halts request) or `operational` (contributes `risk_score_contribution` to request risk score). Compliance-class is the default and fail-safe. See [Scoring Model](data-model/scoring-model/). |
| **Validation Policy** | Typed Policy. Declares `output_class: structural` (boolean pass/fail — halts on fail) or `advisory` (contributes completeness score + warning list without blocking). Structural is the default and fail-safe. See [Scoring Model](data-model/scoring-model/). |
| **Transformation Policy** | Typed Policy. Output: mutations[] — field additions, changes, locks. Fires on request payload. All mutations collected and applied with provenance. |
| **Recovery Policy** | Typed Policy. Output: action + parameters. Fires on failure/timeout trigger conditions. Governs what DCM does when things go wrong. |
| **Orchestration Flow Policy** | Typed Policy. Output: ordered step sequence. Fires on pipeline payload type events. Named workflow artifacts — the explicit, visible pipeline skeleton. |
| **Governance Matrix Rule** | Typed Policy. Output: ALLOW / DENY / ALLOW_WITH_CONDITIONS / STRIP_FIELD / REDACT / AUDIT_ONLY. Fires at every cross-boundary interaction. The single enforcement point for all data/capability boundary decisions. |
| **Lifecycle Policy** | Typed Policy. Output: action on related entity (cascade, protect, detach, notify). Fires on relationship events. |

### Data Model Terms

| Term | Definition |
|------|-----------|
| **Entity** | A Resource Entity, Process Entity, or Composite Entity — the primary managed thing in DCM. Has a UUID that is stable across all four lifecycle states. |
| **Four States** | Intent (consumer declaration), Requested (assembled/policy-validated), Realized (provider-confirmed), Discovered (independently observed). Same entity at four lifecycle stages in four data domains within a single PostgreSQL-compatible database (doc 51). |
| **Data Layer** | A versioned data artifact that contributes fields to request payload assembly. Types: Base, Core, Intermediate, Service, Request. Each has a declared contributor type. |
| **Resource Type Specification** | The schema definition for a resource type. Declares fields, constraints, portability class, dependency graph, and field criticality. |
| **Provider Catalog Item** | A provider-specific instantiation of a Resource Type Specification. What consumers actually request from the service catalog. |
| **Artifact Metadata** | Standard metadata block on every DCM artifact: uuid, handle, version, status, owned_by, created_by, contributed_by. |
| **Provenance** | Field-level lineage metadata embedded in every payload field, recording origin and all modifications. |
| **Data Classification** | Field-level metadata: public / internal / confidential / restricted / phi / pci / sovereign / classified. Phi, sovereign, and classified are immutable once set. |
| **Sovereignty Zone** | A registered DCM artifact declaring a geopolitical/regulatory boundary. Rules reference zones by ID, not raw country codes. |
| **Accreditation** | A formal, versioned, time-bounded attestation that a DCM component satisfies a specific compliance framework. First-class Data artifact with its own lifecycle. |
| **DCMGroup** | Universal grouping artifact with typed group_class: tenant_boundary, resource_grouping, policy_collection, policy_profile, composite, federation. |
| **Drift Record** | A Data artifact produced by the Drift Reconciliation Component recording field-by-field comparison of Realized vs Discovered state with severity classification. |
| **Governance Matrix Rule** | A Data artifact (also a Policy type) — a rule artifact governing cross-boundary interactions using four-axis match conditions. |

### Operational Terms

| Term | Definition |
|------|-----------|
| **Request Orchestrator** | The event bus. Routes lifecycle events to the Policy Engine. Contains no pipeline logic — Policies define all behavior. |
| **Policy Engine** | Evaluates all policy types using the same algorithm. The single policy evaluator — no component bypasses it. |
| **Placement Engine** | Six-step provider selection: sovereignty filter → accreditation filter → capability filter → parallel reserve queries → tie-breaking (policy/priority/affinity/cost/load/hash) → confirm. |
| **Drift Reconciliation** | Control plane component. Compares Discovered State vs Realized State. Produces drift records and events. Never writes to the Realized Store. |
| **Shadow Mode** | A Policy in `proposed` status evaluates against real traffic; output is captured but never applied. The primary mechanism for safe policy change management. |
| **Naturalization** | Service Provider converts a DCM unified payload to provider-native format before execution. |
| **Denaturalization** | Service Provider converts provider-native result back to DCM unified format after execution. |
| **Rehydration** | Replaying a resource's intent state to a new provider or context. Produces a new Requested State from the existing Intent State. |
| **Contributor** | An actor type that authored a Data artifact. Recorded in artifact_metadata.contributed_by. Types: platform_admin, consumer, service_provider, peer_dcm. Determines review requirements. |
| **Two-Level Orchestration** | Level 1: Named Workflow Artifacts (Orchestration Flow Policy, ordered: true) — explicit sequence skeleton. Level 2: Dynamic Policies (GateKeeper, Transformation, Recovery) — fire conditionally on same events without being declared in the workflow. |
| **Reserve Query** | A parallel capacity query sent to all eligible provider candidates. Providers confirm capacity and hold it for PT5M. The Placement Engine selects the winner and releases other holds. |




### credential management service Terms

| Term | Definition |
|------|-----------|
| **Credential Record** | DCM Data artifact storing credential metadata (UUID, type, scope, expiry, status). Never contains the credential value — values are held by the credential management service. |
| **DCM Interaction Credential** | Short-lived (PT15M–PT1H profile-governed), scoped credential issued before every provider dispatch. Implements ZTS-002. Never stored beyond the interaction window. |
| **Credential Revocation Registry** | Fast-queryable store of revoked credential UUIDs. All components that receive interaction credentials must check this registry at each use. Cache TTL: PT1M standard; PT30S fsi/sovereign. |
| **Transition Window** | Period during rotation when both the old and new credential are valid. Prevents downtime. P1D for consumer credentials; PT5M for dcm_interaction; P7D for x509. |
| **Emergency Rotation** | Rotation triggered by a security event. No transition window — old credential revoked immediately. Fastest-channel notification delivery. |
| **CPX-001–CPX-012** | credential management service system policies. Key: CPX-001 (values never in DCM stores — every profile), CPX-002 (every dispatch must present scoped interaction credential), CPX-009 (algorithm and key_usage declared at issuance; validated at use), CPX-012 (CPX-001 applies in ALL profiles — no exceptions). |
| **credential_profile** | Profile-governed credential configuration block controlling: permitted credential types, max lifetime per type, rotation requirements, retrieval auth level (bearer/step-up-mfa/mtls), FIPS level enforcement, approved algorithms, revocation SLA, idle detection threshold, IP binding requirement. |
| **AAL (Authenticator Assurance Level)** | NIST 800-63B vocabulary: AAL1 (minimal/dev — single factor), AAL2 (standard/prod — MFA required for sensitive credentials), AAL2+ (fsi — hardware MFA, FIPS L2), AAL3 (sovereign — hardware-bound, FIPS L3, tamper evidence). |
| **Idle Credential** | A credential issued but not retrieved within the profile-governed threshold. Triggers notification but not automatic revocation. Auto-revocation after 2× threshold is profile-configurable. |
| **key_usage** | Declared purpose of a credential: authentication, signing, or encryption. Non-overlapping — a credential issued for authentication cannot be used for signing even if the algorithm supports both. Validated at use time by credential management service. |


### Composite Service Composition Terms

| Term | Definition |
|------|-----------|
| **Composite Service** | A catalog-level registration that declares a composite payload — multiple constituent resource types with declared dependencies and delivery requirements — fulfillable as a single request. Registered by an ordinary Service Provider; not a separate provider type. See doc 30 (Composite Service Composition Model). |
| **Composite Entity** | A DCM entity produced by a Composite Service request. Exists across all four states as a single entity aggregating constituent Resource Entities. Has one entity UUID that links it through all states. |
| **Constituent** | A sub-resource within a Composite Service. Declared with a `component_id`, `resource_type`, `depends_on`, `provided_by` (`self` or `external`), and `required_for_delivery` classification. |
| **required_for_delivery** | Constituent delivery classification: `required` (failure halts the composite request and triggers compensation), `partial` (failure produces DEGRADED but not FAILED), `optional` (failure is noted but ignored). |
| **Composite Status** | Top-level outcome of a Composite Service request: `OPERATIONAL` (all required constituents succeeded), `DEGRADED` (required succeeded; partial(s) failed; accepted if profile permits), `FAILED` (required constituent(s) failed; triggers compensation). |
| **Compensation** | Ordered teardown of successfully realized constituents when a Composite Service cannot be delivered. Runs in dependency-reverse order. Best-effort; failures produce `PARTIALLY_COMPENSATED` with orphan detection. |
| **Composition Visibility** | How a Composite Service exposes its internal structure to consumers: `opaque` (top-level only), `transparent` (all constituents as DCM entities), `selective` (declared sub-set as DCM entities). |
| **Dependency Round** | A batch of constituents that can execute in parallel because all their `depends_on` constituents are complete. Multiple rounds execute sequentially; constituents within a round execute in parallel. |
| **CMP-001–CMP-008** | Composite Service system policies. Key: CMP-001 (`self` constituents dispatched via standard Services API), CMP-002 (constituent ordering derived from `depends_on` by DCM), CMP-004 (composite status determined by DCM), CMP-005 (Recovery Policy governs failure handling), CMP-007 (deterministic constituent UUIDs in transparent mode), CMP-008 (max nesting depth 3). |









### External CA and Live Update Terms

| Term | Definition |
|------|-----------|
| **External CA credential management service** | A credential management service backend that issues x509 certificates using standard protocols (ACME/RFC 8555, EST/RFC 7030, SCEP, CMP, or native API like HashiCorp Vault PKI). Recommended for fsi and sovereign profiles to maintain enterprise PKI chain. Registered trust anchor root cert must be installed in all component trust stores. |
| **Trust Anchor** | The root or intermediate CA certificate installed in all DCM component trust stores. May be the built-in Internal CA or an external CA registered as a credential management service. ICOM-009: components only accept certificates from registered trust anchors. |
| **Server-Sent Events (SSE)** | W3C standard HTTP/1.1 unidirectional event stream. DCM exposes `GET /api/v1/requests/{uuid}/stream` as an SSE endpoint for live request status updates without polling. Stream closes on terminal status. |
| **Interim Status** | Provider-sent progress update during a long-running operation, via `POST /api/v1/provider/entities/{uuid}/status`. Includes step_current/step_total, step_label, and constituent_status array for composite operations. Triggers `request.progress_updated` event. |
| **constituent_status** | Array of named component statuses in a Composite Service request (e.g. `[{ref: "vm", status: "OPERATIONAL"}, {ref: "dns", status: "PROVISIONING"}]`). Surfaced in SSE stream and polling response so consumers can track multi-part operations. |





### RHDH and Backstage Integration Terms

| Term | Definition |
|------|-----------|
| **Red Hat Developer Hub (RHDH)** | Red Hat's enterprise distribution of Backstage. Primary deployment target for DCM consumer GUI. Provides pre-built auth (RHSSO/Keycloak), RBAC plugin, Dynamic Plugins, ArgoCD/Tekton/AAP integrations, and the PatternFly design system. |
| **Dynamic Plugin** | An RHDH/Backstage plugin loaded at runtime without rebuilding the RHDH image. DCM ships all its plugins as Dynamic Plugins — new versions deploy by updating a tag. |
| **DCMService** | Backstage custom entity kind representing a DCM service catalog item. Auto-generated by `@dcm/backstage-plugin-catalog-backend`. Appears in RHDH Software Catalog and drives Software Template generation. |
| **DCMResource** | Backstage custom entity kind representing a realized DCM resource (entity in REALIZED or later lifecycle state). Auto-synced from DCM Realized State every PT5M. Namespace = DCM tenant UUID. |
| **Software Template** | Backstage Scaffolder construct that provides a wizard-based form for creating resources. DCM auto-generates one Software Template per catalog item from the item's field schema. The Scaffolder IS the DCM request form in RHDH mode. |
| **Scaffolder Action** | A Backstage backend function executable from a Software Template. DCM provides: `dcm:request:submit`, `dcm:request:wait` (with live log streaming), `dcm:request:group`, `dcm:request:estimate`, `dcm:catalog:refresh`. |
| **Entity Provider** | A Backstage catalog backend component that emits entity mutations. `@dcm/backstage-plugin-catalog-backend` implements an entity provider that syncs DCM catalog items and realized resources to the RHDH catalog. |
| **PatternFly** | Red Hat's open-source design system and React component library. Used for all DCM GUI surfaces. Key components: Nav (sidebar), NavGroup (non-clickable headers), NavItem with NotificationBadge (approvals count), Table, Toolbar, Gallery (catalog cards), Drawer (live status), Modal (step-up MFA). |
| **GUI-011–GUI-013** | RHDH-specific capabilities: Dynamic Plugin loading (GUI-011), Scaffolder Template auto-generation (GUI-012), DCM Entity Provider for catalog sync (GUI-013). |



### ITSM Integration Terms

| Term | Definition |
|------|-----------|
| **ITSM Bridge** | DCM's bidirectional integration with ITSM systems (ServiceNow, Jira Service Management, Remedy). DCM is the system of record; ITSM is a consumer of DCM events and a source of approval votes. No ITSM dependency for DCM core operation. |
| **ITSM Reference** | Optional metadata on a DCM entity linking it to one or more ITSM records (Change Request, Incident, CMDB CI). Stored as business data fields; visible on resource entity Overview tab; included in audit records. |
| **CMDB Sync** | One-way sync from DCM to CMDB. DCM entities are the system of record; CMDB CI state is updated via notification service subscription to `entity.*` events. Field mapping is provider-configured, not hardcoded. |
| **GUI-014** | ITSM Integration Bridge capability — ITSM references on entity pages, change records linked to requests, ITSM-sourced approval votes in request status, CMDB sync via notification service. |



### ITSM Integration Terms

| Term | Definition |
|------|-----------|
| **ITSM Integration** | Bidirectional integration with IT Service Management systems (ServiceNow, Jira Service Management, BMC Remedy/Helix, Freshservice, PagerDuty, etc.) via process_provider and service_provider types. Outbound: DCM lifecycle events → ITSM records. Inbound: ITSM approvals → DCM approval votes. |
| **ITSM Action Policy** | The 8th DCM Policy output type. Side-effect policy that triggers an action in a connected ITSM system when a DCM event matches. Non-blocking by default (`on_failure: log_and_continue`). May gate the pipeline via `block_until_created: true` with mandatory timeout (ITSM-005). |
| **ITSM Reference** | Metadata stored on a DCM entity linking it to an ITSM record: system, record_type (change_request/incident/cmdb_ci), record_id, record_url, status, last_synced_at. Preserved through entity lifecycle; included in audit records. |
| **block_until_created** | Optional ITSM Policy flag. When `true`, DCM waits for ITSM record creation confirmation before dispatching to Service Provider. Requires `block_timeout`. Timeout expiry triggers `on_failure` behavior — the pipeline never permanently stalls due to ITSM unavailability (ITSM-005). |
| **CMDB CI Mapping** | ITSM integration configuration mapping DCM resource type FQNs to ITSM CI class names (e.g. `Compute.VirtualMachine → cmdb_ci_server` in ServiceNow). Used for `create_cmdb_ci`, `update_cmdb_ci`, and `retire_cmdb_ci` actions. |
| **recorded_via** | Field on DCM approval vote records identifying the system that submitted the vote (dcm_admin_ui / servicenow / jira / slack_bot / api_direct / other). Used by ITSM integration inbound approval routing and in audit records for compliance traceability. |
| **ITSM-001–007** | ITSM integration system policies. Key: ITSM-002 (DCM never requires ITSM — non-blocking default), ITSM-003 (inbound webhooks must be authenticated), ITSM-005 (block_until_created must have timeout — pipeline never permanently stalled). |
| **ITSM-POL-001–004** | ITSM Policy system policies. Key: ITSM-POL-002 (ITSM Policies are side-effect only — not GateKeeper substitutes), ITSM-POL-003 (full audit record per evaluation), ITSM-POL-004 (multiple ITSM Policies on same event fire independently). |


### Web Interface Terms

| Term | Definition |
|------|-----------|
| **Consumer Portal** | The self-service web interface for application developers, owners, and tenant admins. Wraps the Consumer API completely. Bounded by tenancy (X-DCM-Tenant context). Features: catalog browse, request submission with scheduling and dependency groups, live SSE status stream with constituent tracking, resource management, approvals, cost and quota, notifications, sessions. |
| **Admin Panel** | The platform operations console for Platform Admins, SREs, Policy Owners, Security teams, and Auditors. Wraps the Admin API. Features: platform health dashboard, tenant management, provider registration approval, accreditation, quota, scoring configuration, approval queue, tier registry editor, audit and compliance, session management. |
| **Provider Management GUI** | The management interface for provider owner teams. One common shell (overview, health, config, audit) for all 11 provider types, with type-specific extension tabs. Service Provider extends with capacity, managed entities, naturalization; credential management service with inventory, rotation, revocation, external CA config; Auth Provider with session stats and SCIM sync; etc. |
| **Unified Shell** | A single DCM web application with role-gated surfaces: Consumer Portal (all actors), Admin Panel (platform-level roles), Provider Management (provider_owner role), Flow GUI (policy_owner/sre). One login, one session. Navigation adapts to actor's highest privilege level. |
| **GUI-001–GUI-010** | Web Interface capabilities. Key: GUI-002 (SSE live status stream for consumer — status_change, progress_updated, approval events), GUI-006 (tier registry drag-and-drop with hard-stop at auto_approve_below ≤ 50), GUI-010 (unified shell — one application, role-gated surfaces). |


### Operational Reference Terms

| Term | Definition |
|------|-----------|
| **GitOps Store Partitioning** | For deployments using Git as an ingress adapter (doc 51 — optional): splitting the intent repository into multiple repositories to manage scale. Three strategies: tenant-shard (hash of tenant_uuid), per-tenant (one repo per tenant), and time-based archiving (active vs cold). Git is not a required DCM infrastructure component — it is one of several ingress paths (alongside API, CLI, and message bus). |
| **Dual-Write Mode** | Migration technique where DCM writes to both source and target store simultaneously. Required before store cutover. Duration is profile-governed (P1D minimal → P60D sovereign). |
| **Burn-In Period** | Post-cutover period during which the source store remains accessible in read-only mode for rollback. Profile-governed: P7D minimal → P90D fsi/sovereign. Source must NOT be decommissioned before burn-in completes. |
| **Repave** | The complete recovery scenario: all DCM infrastructure lost but Git remotes intact. DCM bootstraps from Git, restores operational stores from backup, and rehydrates managed resources. OPS-005 requires post-recovery validation checklist completion. |
| **RTO (Recovery Time Objective)** | Maximum acceptable time to restore DCM service after failure. Profile-governed: PT1M–PT5M component failure (sovereign/standard), PT5M–PT30M full control plane loss. |
| **RPO (Recovery Point Objective)** | Maximum acceptable data loss window. GitOps stores: 0 (Git remote is source of truth). Realized Store: PT1M (fsi/sovereign) to PT5M (standard). Audit Store: PT1M (fsi/sovereign) to PT15M (standard). |
| **OPS-001–007** | Operational Reference system policies. Key: OPS-002 (audit chain continuity across migration), OPS-003 (source read-only during burn-in; do not decommission early), OPS-006 (Audit Store retention minimum P365D all profiles). |


### Scheduling and Dependency Terms

| Term | Definition |
|------|-----------|
| **Scheduled Request** | A DCM request with an explicit dispatch schedule (at a specific time, during a maintenance window, or recurring). Goes through the same pipeline as immediate requests; policy evaluates at declaration AND at dispatch time. |
| **PENDING_DEPENDENCY** | Intent State status for a request in a dependency group waiting for its declared dependency to reach the required wait_for state before dispatch. |
| **Request Dependency Group** | A consumer-declared set of requests with ordering constraints (depends_on) between them. Distinct from type-level dependencies (doc 07) and Composite Service composition (doc 30). |
| **Field Injection** | Mechanism for passing realized output fields from a dependency automatically into a dependent request's fields at dispatch time. Subject to Transformation policies. |
| **Maintenance Window** | A reusable, named recurrence artifact declaring approved change windows. Consumers reference window_uuid in scheduled requests to slot into the next matching window. |
| **SCH-001–SCH-006** | Scheduled requests system policies. Key: SCH-001 (dual policy evaluation: declaration + dispatch), SCH-003 (dispatch-time policy rejection → FAILED), SCH-005 (not_after deadline miss → FAILED, no retry). |
| **RDG-001–RDG-006** | Request dependency graph policies. Key: RDG-001 (circular deps rejected at submission), RDG-002 (max 50 requests per group), RDG-004 (PENDING_DEPENDENCY requests count against quota), RDG-006 (request may belong to one group only). |

### Self-Health Terms

| Term | Definition |
|------|-----------|
| **Liveness (/livez)** | Fast DCM health check (PT5S max, no external calls). Failure → Kubernetes restarts the pod. Unauthenticated. |
| **Readiness (/readyz)** | DCM readiness check — validates Session Store, Audit Store, Policy Engine, Message Bus, Auth Provider. Failure → removed from load balancer. Used for startup probes. |
| **HLT-001–HLT-006** | Self-health system policies. Key: HLT-001 (livez and readyz required, unauthenticated), HLT-002 (livez PT5S max, no external calls), HLT-003 (readyz fails if core dependencies unreachable), HLT-005 (Prometheus metrics required). |


### Session Revocation Terms

| Term | Definition |
|------|-----------|
| **Session Record** | DCM Data artifact tracking an active actor session: session_uuid, actor_uuid, auth_provider_uuid, created_at, expires_at, status (active/refreshing/revoked/expired), revocation metadata. |
| **Session Revocation Registry** | Fast-queryable store of revoked-but-not-yet-expired session UUIDs. All components that accept bearer tokens must check this on every request. Cache age is profile-governed (PT5M minimal → no cache sovereign). |
| **Session Store** | Operational store for active sessions (not GitOps-backed). Separate from Realized State Store. Backed by Redis or Postgres (standard+) or in-memory (minimal/dev). |
| **Token Introspection** | RFC 7662 endpoint (`POST /api/v1/auth/introspect`) for validating bearer tokens. Returns active/inactive plus session metadata. Requires `introspection` scope. |
| **AUTH-016–AUTH-022** | Session revocation system policies. Key: AUTH-016 (deprovisioning fires session + credential revocation in parallel), AUTH-017 (revocation SLA), AUTH-018 (all components check revocation registry), AUTH-019 (emergency revocation: critical urgency, non-suppressable). |

### Internal Component Auth Terms

| Term | Definition |
|------|-----------|
| **Internal CA** | The Certificate Authority operated by each DCM deployment for issuing mTLS certificates to internal components. Not exposed externally. Root cert installed in all component trust stores at deployment time. |
| **Component Identity** | Each DCM control plane component has a stable UUID, an mTLS certificate from the Internal CA, and a service account with declared allowed_sources and allowed_targets. |
| **Bootstrap Token** | A one-time-use credential (max PT1H lifetime) that enables a new component to acquire its first mTLS certificate from the Internal CA. Invalidated immediately after use. |
| **Component Communication Graph** | The declared graph of which components may call which others. Components may only call `allowed_targets`; endpoints only accept calls from `allowed_sources`. Violations are rejected and audited (ICOM-003, ICOM-004). |
| **ICOM-001–ICOM-009** | Internal Component Auth system policies. Key: ICOM-001 (mTLS required for all internal calls), ICOM-002 (interaction credential required in addition to mTLS), ICOM-007 (bootstrap tokens one-time-use, PT1H max), ICOM-008 (compromised certs → CRL immediately). |


### API Versioning Terms

| Term | Definition |
|------|-----------|
| **Breaking Change** | Any change that requires an existing client to modify code or configuration to continue working. Removing fields, changing types, removing endpoints, tightening validation, changing HTTP status semantics. See [34-api-versioning-strategy.md] Section 2 for the complete definition. |
| **Deprecation Period** | The window between when a version is announced as deprecated and when it reaches its sunset date. Deprecated versions continue to function; responses include `Deprecation` and `Sunset` headers. Profile-governed: prod=365 days notice, 2 years support; sovereign=2 years notice, 4 years support. |
| **Sunset Date** | The date after which a deprecated API version returns `410 Gone`. Clients must migrate before this date. |
| **Preview Endpoint** | An endpoint at `/api/v{N}/preview/` path with no stability commitment. May change or be removed without a major version increment. Not for production use. |
| **VER-001–VER-009** | API Versioning system policies. Key: VER-002 (breaking change definition — when in doubt, treat as breaking), VER-003 (deprecation headers required on all deprecated version responses), VER-005 (support windows are profile-governed), VER-008 (machine-readable migration guide required for each new major version). |


### Event Catalog Terms

| Term | Definition |
|------|-----------|
| **Event Catalog** | The authoritative source for all DCM event types, their payload schemas, urgency levels, and trigger conditions. See [33-event-catalog.md]. 82 event types across 20 domains. |
| **Event Envelope** | The common wrapper all DCM events share: event_uuid (idempotency key), event_type, event_schema_version, timestamp (from Commit Log), dcm_version, dcm_instance_uuid, subject, urgency, payload, links. |
| **event_uuid** | Stable idempotency key assigned to each event. Consumers must treat duplicate event_uuid values as already-processed — DCM delivers at-least-once. |
| **event_schema_version** | Increments on breaking payload schema changes. Adding optional fields is not breaking. Removing fields, changing types, or changing semantics are breaking. |
| **EVT-001–EVT-007** | Event Catalog system policies. Key: EVT-001 (all events must include base envelope), EVT-002 (event_uuid is idempotency key), EVT-005 (critical urgency events delivered via push regardless of subscriptions), EVT-006 (non-standard events use reverse-DNS prefix), EVT-007 (audit.* critical events are non-suppressable). |


### Authority Tier Model Terms

| Term | Definition |
|------|-----------|
| **Authority Tier Registry** | The ordered list of authority tiers that governs approval routing across all DCM pipelines. Stored as a versioned registry entry. Changes require impact detection before activation.  |
| **Tier Impact Diff** | Computed before any tier registry change activates. Compares proposed ordered list to current list; classifies each changed tier as SECURITY_DEGRADATION, BROKEN_REFERENCE, PROFILE_GAP, SECURITY_UPGRADE, or NEW. |
| **SECURITY_DEGRADATION** | Impact classification for a tier whose gravity or position decreased after a registry change. Blocks registry activation until explicitly accepted by a verified-tier or above reviewer (ATM-009). |
| **BROKEN_REFERENCE** | Impact classification when a tier name referenced in active configuration no longer exists in the registry. Blocks activation until resolved (ATM-010). |
| **PROFILE_GAP** | Impact classification when a profile's threshold list is incomplete after new tier insertion. Warning only — does not block activation (ATM-012). | Stored as a versioned registry entry. Custom tiers are inserted into the list by position; existing tier names remain stable. |
| **decision_gravity** | Stable, position-independent severity classification on each tier: `none` (auto), `routine` (reviewed), `elevated` (verified), `critical` (authorized). Used by the scoring model and profile system to reason about tier severity independently of tier names. |
| **Tier Weight** | Numeric value derived from a tier's position in the ordered list. Never hardcoded — resolved at evaluation time. Stored in approval records for point-in-time audit (ATM-008). |
| **Custom Tier** | An organization-defined tier inserted between existing tiers. Must declare `decision_gravity` consistent with position. Requires `verified` tier approval to contribute (ATM-004). |
| **ATM-001–ATM-008** | Authority Tier Model system policies. Key: ATM-001 (tiers identified by name; weight derived from position), ATM-002 (auto tier max_score ≤ 50), ATM-003 (custom tier gravity must be consistent with position), ATM-008 (approval records store weight at creation for point-in-time audit). |


### Authority Tier Terms

| Term | Definition |
|------|-----------|
| **Authority Tier** | The required organizational authority level for a decision, expressed as a named position in an ordered list. DCM defines four tiers; organizations define what constitutes sufficient authority at each level. |
| **`auto`** | No human judgment required. System confidence (scoring, validation) is sufficient to proceed. |
| **`reviewed`** | Standard authority required. One qualified reviewer in the relevant domain must record a decision via the DCM Admin API. Who constitutes a qualified reviewer is the organization's definition. |
| **`verified`** | Elevated authority required. Two independent, distinct reviewers must each record a decision. The same actor cannot satisfy both. Enforces separation of duties. |
| **`authorized`** | Highest authority level required. Most consequential decisions — policy governance changes, regulated actions, high-risk provider registrations. N members of a declared DCMGroup must record decisions via the Admin API. The authority group composition (CTO, CISO, security board, one person with delegated authority) is entirely the organization's definition. |
| **DCMGroup (authority context)** | A declared set of actors who constitute the required authority for `authorized` tier decisions. Platform admin declares membership; quorum threshold (N of M) is profile-governed. |
| **`recorded_via`** | Audit field on approval decisions capturing which system submitted the decision (dcm_admin_ui, servicenow, jira, slack_bot, api_direct). Informational for audit; not enforced. |


### Design Priority Terms

| Term | Definition |
|------|-----------|
| **Design Priority Order** | The four-priority hierarchy governing all DCM design decisions: (1) Security — industry best practices are the baseline; (2) Ease of use — secure path must be easy path; (3) Extensibility — adaptable through configuration not code; (4) Fit for purpose — always required. |
| **DPO-001–006** | Design Priority system policies. Key: DPO-001 (security properties present in all profiles), DPO-002 (every security requirement needs ease-of-use mechanism), DPO-005 (`minimal` profile = minimal overhead not minimal security), DPO-006 (when security and ease conflict, redesign ease-of-use not security). |
| **Priority 1 (Security)** | Security properties are architecturally present in ALL profiles. Profiles control enforcement strictness and automation level — never whether the property exists. Non-negotiable across all profiles: CPX-001, SMX-004, SMX-008, CPX-003, CPX-005 first retrieval audit, forbidden algorithm baseline. |
| **Priority 2 (Ease of use)** | The secure path must also be the easy path. Every security requirement must be accompanied by an ease-of-use mechanism. The scoring model auto-approval threshold, profile defaults, and Flow GUI visual condition builder are all Priority 2 implementations. |

### Scoring Model Terms

| Term | Definition |
|------|-----------|
| **enforcement_class** | Required property of GateKeeper policies. `compliance`: boolean deny gate — always halts on fire. `operational`: contributes `risk_score_contribution` to the request risk score. |
| **output_class** | Required property of Validation policies. `structural`: boolean pass/fail. `advisory`: contributes completeness score and warnings without blocking. |
| **request_risk_score** | Aggregate score (0–100) assembled from five weighted signals: operational GateKeeper contributions, completeness, actor risk history, quota pressure, provider accreditation richness. Drives approval routing. |
| **risk_score_contribution** | The weighted score a fired operational-class GateKeeper contributes to the request risk score. Declared as `scoring_weight` (1–100) in the policy. |
| **completeness_score** | Aggregate of advisory Validation contributions. Represents how incomplete or unusual the request is — higher = more warnings. Does not block requests. |
| **actor_risk_history_score** | Decay-weighted (λ=0.1, half-life ≈7 days) history of an actor's previous request outcomes. Contributes to request risk score. Not exposed to other consumers. |
| **quota_pressure_score** | Continuous score representing how close a Tenant is to quota limits for the requested resource type. Zero below 75% utilization; 100 at full quota. |
| **accreditation_richness_score** | Weighted sum of a provider's accreditation portfolio normalized to 0–100. Influences placement preference and inversely contributes to provider risk signal. |
| **scoring_threshold** | Profile-governed boundary on the request risk score that maps to an approval routing tier. Four tiers: auto_approve, reviewed, verified, authorized. `auto_approve_below` may not exceed 50 (SMX-008). |
| **Risk Score Aggregator** | Sub-function of the Policy Engine. Assembles five scoring signals into the request risk score after all compliance-class and Governance Matrix evaluations complete. |
| **regulatory_mandate** | Policy metadata flag. When `true`, the policy's `enforcement_class: compliance` cannot be demoted to operational by any profile (SMX-003). Set by platform admins, audited. |
| **score_drivers** | Human-readable list of the top contributing factors to a request risk score. Exposed to consumers (top 3 only). Full breakdown in Score Record for platform admins. |
| **Score Record** | Immutable audit artifact recording the full signal breakdown, weights, routing decision, and threshold applied for a scored request evaluation. Written to Audit Store for every scored request. |


### Federation Topology

| Term | Definition |
|------|-----------|
| **Peer DCM** | A federated DCM instance. Treated as a typed Provider. Trust postures: verified (manually approved), vouched (Hub-introduced), provisional (crypto-verified only). |
| **Hub DCM** | A DCM instance that coordinates Regional DCMs in hub-spoke topology. Policy distribution source. Cannot force-activate policies on Regional DCMs. |
| **Regional DCM** | A DCM instance in a specific sovereignty region, managed by a Hub DCM. |
| **Federation Tunnel** | Mutually authenticated, encrypted, scoped channel between DCM instances. Establishes secure transport — not implicit trust. |
| **Federated Contribution** | A Peer DCM contributing registry entries, policy templates, or service layers to a receiving DCM, scoped by the peer's federation trust posture. |

---

## Part 2 — Anti-Vocabulary

Terms to avoid because they introduce ambiguity. Use the precise alternatives instead.

| Avoid | Because | Use Instead |
|-------|---------|-------------|
| **Widget** | Vague — what thing, exactly? | Name the specific resource type (VirtualMachine, IPAddress, VLAN, etc.) |
| **Realize** (standalone) | Ambiguous — "realize" can mean understand, achieve, or provision | **Provision** a VM, **fulfill** a request, **execute** a process. "Realized State" is accepted vocabulary. |
| **Data Center** (as architectural term) | A building — not architecturally meaningful | **Region** (large geographically distinct area) or **Zone** / **Availability Zone** (isolated group within a Region) |
| **Orchestrator** (as a standalone component) | Suggests a single sequencer; DCM orchestration is policy-driven, not procedural | **Request Orchestrator** (the event bus) + **Orchestration Flow Policy** (named workflow) + **Policy Engine** (evaluator) |
| **Tangible / Intangible** | Nothing in DCM architecture is intangible — these words add no precision | Describe what the thing actually is |
| **Workflow** (without qualification) | Ambiguous between Level 1 (named Orchestration Flow Policy) and general process | **Named Workflow** (Orchestration Flow Policy with `ordered: true`) or **dynamic policy** (conditional policy) |
| **Producer** | DCM uses "Provider" terminology with typed contracts | **Service Provider** (provisions resources) or the specific provider type |
| **Shore / Ship / Enclave** | Legacy terminology from defense IT contexts; replaced in DCM | **Hub DCM** (central/global) / **Regional DCM** (distributed regional) / **Sovereign DCM** (air-gapped/compliance-isolated) |
| **User** (generic) | Ambiguous across domains — humans "use" DCM in every domain | **Consumer**, **Developer**, **Application Owner**, **Platform Engineer**, **SRE**, **Tenant Admin**, **Policy Author** |
| **Service** (unqualified) | Means different things in different contexts — provision target, catalog entry, or provider | **Catalog Item** (what consumers browse), **Resource Type** (abstract classification), **Service Provider** (who provisions) |
| **Manage** (unqualified) | Too broad — what action specifically? | **Provision**, **Configure**, **Monitor**, **Decommission**, **Govern** — name the lifecycle operation |

---

## Part 3 — Roles and Personas

| Role | Scope | API surface |
|------|-------|-------------|
| **Consumer** | Requests services from the catalog; manages owned resources | Consumer API |
| **Tenant Admin** | Manages a Tenant; can author tenant-domain policies and groups | Consumer API + contribution endpoints |
| **Policy Author** | Authors policies within assigned domain scope | Consumer API contribution endpoints, Flow GUI |
| **Platform Admin** | Manages the DCM deployment; all artifact types; all domains | Admin API, Flow GUI (full) |
| **Platform Observer** | Read-only view across all platform operations | Flow GUI (read-only), Admin API (read) |
| **Service Provider Operator** | Manages a registered Service Provider | Operator Interface (provider side), Admin API (registration) |
| **Policy Reviewer** | Reviews and approves/rejects contributed policies | Admin API, Flow GUI |
| **Auditor** | Read-only access to audit records and compliance reports | Consumer API (audit), Admin API (audit) |

---

## Part 4 — Capability Domain Prefixes

| Prefix | Domain |
|--------|--------|
| IAM | Identity and Access Management |
| CAT | Service Catalog |
| REQ | Request Lifecycle Management |
| PRV | Provider Contract and Realization |
| LCM | Resource Lifecycle Management |
| DRF | Drift Detection and Remediation |
| POL | Policy Management |
| LAY | Data Layer Management |
| INF | Information and Data Integration |
| ING | Ingestion and Brownfield Management |
| AUD | Audit and Compliance |
| OBS | Observability and Operations |
| STO | Storage and State Management |
| FED | DCM Federation and Multi-Instance |
| GOV | Platform Governance and Administration |
| ACC | Accreditation Management |
| ZTS | Zero Trust and Security Posture |
| GMX | Unified Governance Matrix |
| DRC | Drift Reconciliation |
| FCM | Federated Contribution Model |
| SMX | Scoring Model |
| CMP | Composite Service Composition |
| CPX | credential management service Model |
| DPO | Design Priority Order |
| ATM | Authority Tier Model |
| EVT | Event Catalog |
| VER | API Versioning |
| SES | Session Revocation |
| ICOM | Internal Component Auth |
| SCH | Scheduled Requests |
| RDG | Request Dependency Graph |
| HLT | DCM Self-Health |
| OPS | Operational Reference |
| GUI | Web Interfaces |
| ITSM | ITSM Integration |
| AUTH | Auth Provider Capabilities |
| PCA | Provider Callback Authentication |
| PRR | Provider Readiness |
| WLA | Workload Analysis |
| ACM | Accreditation Monitoring |
| LOC | Location Topology Management |
| SUB | Subscription Management |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
