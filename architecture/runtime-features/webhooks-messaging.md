# DCM Data Model — Webhooks, Messaging, and External Integration


**Document Status:** ✅ Complete
**Related Documents (updated):** [Notification Model](notifications.md) | [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md)  

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [udlm/foundations/foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: PROVIDER**
>
> The Provider abstraction — Message Bus and webhook delivery channels


**Related Documents:** [Universal Audit Model](https://github.com/croadfeldt/udlm/blob/main/observability/universal-audit.md) | [Deployment and Redundancy](deployment-redundancy.md) | [Authentication and Authorization](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Policy Organization](../governance-enforcement/policy-profiles.md)

---


> **See [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md)** — authoritative source for all DCM event types and payload schemas.

## 1. Purpose

DCM communicates with the outside world through three complementary mechanisms:

- **Outbound Webhooks** — DCM pushes event notifications to external HTTP endpoints
- **Inbound Webhooks** — External systems push requests, queries, and events to DCM HTTP endpoints
- **event routing services** — DCM integrates with external message buses for persistent, high-throughput bidirectional event streaming

All three mechanisms are authenticated, authorized, and audited identically to any other DCM API call. There is no privileged back-channel. Every integration is a registered DCM actor subject to full Policy Engine evaluation.

**Webhooks are optional and policy-governed.** The active Profile sets defaults — `fsi` and `sovereign` profiles may require webhook or message bus coverage for audit events. `minimal` and `dev` profiles make them fully optional.

---

## 2. Ingress and Egress — The Universal Actor Model

### 2.1 The `ingress` Block

Every request entering DCM carries an immutable `ingress` block set by the DCM ingress layer before Policy Engine evaluation. It is never consumer-declarable and never modifiable by policies — policies may only read it.

```yaml
ingress:
  # HOW it arrived
  surface: <web_ui|consumer_api|webhook_inbound|message_bus_inbound|
            provider_callback|policy_engine|scheduler|rehydration|
            ingestion|dcm_internal|operator_cli>
  protocol: <https|amqp|kafka|grpc|websocket>
  authenticated_via: <hmac_sha256|mtls|bearer_token|oidc|api_key|
                      ldap|kerberos|saml|static_api_key|local_password>
  authorized_via: policy_engine

  # WHO sent it — fully resolved actor context
  actor:
    uuid: <dcm-assigned-actor-uuid>
    type: <human|service_account|webhook_service_account|
           provider|scheduler|dcm_internal>
    display_name: "Jane Smith"
    identity_source: <oidc|ldap_direct_bind|active_directory|freeipa|
                      github_oauth|gitlab_oauth|static_api_key|
                      local_password|mtls|hmac|kerberos|saml>
    auth_provider_uuid: <uuid>          # which Auth Provider authenticated
    auth_provider_type: <freeipa|active_directory|oidc|built_in|...>

    # Resolved DCM roles and scope (at authentication time)
    roles: [sre]
    tenant_scope: [<tenant-uuid>]
    groups: [<dcmgroup-uuids>]
    permissions: [request.submit, query.entity_state]

    # Authorization chain
    authorized_by:
      method: <registered_actor|oidc_token|ldap_group_mapping|
               policy_grant|system_policy|api_key>
      authorizing_entity_uuid: <uuid>
      authorization_timestamp: <ISO 8601>
      expiry: <ISO 8601>

    # Session context (human actors)
    session_uuid: <uuid>
    session_started_at: <ISO 8601>
    mfa_verified: <true|false>

    # External identity (federated actors)
    external_identity:
      provider: <okta|azure_ad|freeipa|active_directory|github|custom>
      subject: "uid=jsmith,cn=users,cn=accounts,dc=corp,dc=example,dc=com"
      claims:
        email: jsmith@corp.example.com
        display_name: "Jane Smith"
        department: Engineering
        cost_center: CC-1234
        ldap_groups: [cn=dcm-sre,...]
        sid: "S-1-5-21-..."        # AD Security Identifier

    # Rate limit tracking
    rate_limit_bucket: <actor_uuid>

  # Surface-specific detail
  webhook_registration_uuid: <uuid>   # if surface: webhook_inbound
  (optional infrastructure)_uuid: <uuid>   # if surface: message_bus_inbound
  message_offset: <string>            # if surface: message_bus_inbound
  scheduler_job_uuid: <uuid>          # if surface: scheduler
  parent_request_uuid: <uuid>         # if surface: policy_engine|rehydration
  source_ip: <IP — audit only, never used for authorization>
```

### 2.2 The `egress` Block

All outbound calls from DCM carry DCM's authenticated identity:

```yaml
egress:
  surface: <webhook_outbound|message_bus_outbound|provider_api|
            mode4_query|(prescribed infrastructure)|service_provider|auth_provider>
  protocol: <https|kafka|amqp|grpc>
  actor:
    uuid: <dcm_component_uuid>
    type: dcm_internal
    component: <webhook_delivery_service|audit_forward_service|
                policy_engine|placement_engine|...>
    authenticated_via: <hmac_sha256|mtls|bearer_token|api_key>
    credential_ref:
      service_provider_uuid: <uuid>
      secret_path: <path>
  originating_request_uuid: <uuid>
  originating_actor_uuid: <uuid>
```

### 2.3 Policy Engine Use Cases — Ingress/Egress Fields

The ingress block enables a rich class of governance rules:

```yaml
# Require specific auth for sensitive operations
policy: "If action == decommission AND ingress.actor.mfa_verified == false THEN gatekeep"

# Block legacy API keys from production Tenants
policy: "If tenant.profile == prod AND ingress.actor.identity_source == static_api_key THEN gatekeep"

# Require enterprise auth for security resources
policy: "If resource_type IN [Network.FirewallRule] AND ingress.actor.auth_provider_type NOT IN [oidc, freeipa, active_directory] THEN gatekeep"

# Enrich from OIDC claims
policy: "If ingress.actor.external_identity.claims.department EXISTS THEN inject: business_context.department"

# Block message bus inbound from non-service-accounts
policy: "If ingress.surface == message_bus_inbound AND ingress.actor.type != webhook_service_account THEN gatekeep"

# Sovereignty check on inbound message bus
policy: "If ingress.surface == message_bus_inbound AND (optional infrastructure).jurisdiction != tenant.sovereignty_zone THEN gatekeep"
```


### 2.5 Ingress API vs Consumer API — Relationship Clarification

These two terms refer to different architectural layers:

**Ingress API (infrastructure layer):**
The network-level entry point for all inbound requests to the DCM control plane. It handles:
- TLS termination
- Authentication token validation
- Setting the immutable `ingress` block on every request (surface, actor, timestamp, mfa_verified)
- Rate limiting at the network level
- Routing to the appropriate internal component (Consumer API handlers, Provider API handlers, Admin API handlers)

The Ingress API is infrastructure — it is not directly defined in any consumer-facing specification.

**Consumer API (application layer):**
The logical REST API surface that consumers interact with, as defined in the [Consumer API Specification](../../docs/specifications/consumer-api-spec.md). The Consumer API is *served through* the Ingress API. When a consumer calls `POST /api/v1/requests`, that request enters through the Ingress API (which sets the ingress block) and is then handled by the Consumer API component.

**Other APIs served through the Ingress API:**
- **Provider API** — the callback and notification endpoints that Service Providers call (`/api/v1/provider/...`)
- **Admin API** — platform administration operations (`/api/v1/admin/...`)
- **Webhook Inbound** — external systems calling DCM (`/api/v1/webhooks/...`)

**The Ingress API is one, the Consumer API is one of several logical surfaces routed through it.**

---

### 2.6 Consumer Rate Limiting and Quota Model

Consumer-side rate limiting and resource quotas are enforced by GateKeeper policies — not hardcoded limits. This keeps quota enforcement consistent with DCM's policy-driven model.

**Request rate limiting (per actor):**

```yaml
rate_limit_policy:
  type: gatekeeper
  handle: "system/quotas/api-rate-limit"
  trigger: request.initiated
  conditions:
    - field: ingress.actor_uuid
      rate_window: PT1M
      max_requests: 60           # configurable per Tenant policy
  action: reject
  rejection_code: 429
  rejection_message: "Rate limit exceeded. Retry after PT1M."
```

**Resource quotas (per Tenant per resource type):**

```yaml
quota_policy:
  type: gatekeeper
  handle: "tenant/payments/vm-quota"
  trigger: request.initiated
  conditions:
    - field: request.resource_type
      equals: Compute.VirtualMachine
    - field: tenant.active_entity_count
      resource_type: Compute.VirtualMachine
      operator: gte
      value: 100                 # max 100 concurrent VMs for this Tenant
  action: reject
  rejection_message: "VM quota exceeded (100). Request a quota increase via the Admin API."
```

**Quota increase process:** Tenants request quota increases through the standard request process. A quota change request produces a Requested State record, goes through policy evaluation, and requires Platform Admin approval for significant increases.

**Profile-governed defaults:**

| Profile | Default API rate limit | Default resource quota |
|---------|----------------------|----------------------|
| minimal | 10 req/min | Unlimited |
| dev | 60 req/min | Unlimited |
| standard | 60 req/min | Policy-declared |
| prod | 120 req/min | Policy-declared |
| fsi | 60 req/min | Strict policy-declared |
| sovereign | 30 req/min | Strict policy-declared |


### 2.4 System Policies

| Policy | Rule |
|--------|------|
| `ING-008` | All DCM requests must carry an ingress block. The ingress block is set by the DCM ingress layer and is immutable — policies may read but not modify it. |
| `ING-009` | The ingress block must include a fully resolved actor context: uuid, type, identity_source, roles, tenant_scope, auth_provider_uuid, and authorized_by chain. |
| `ING-010` | All egress calls from DCM must carry DCM's authenticated identity. Unauthenticated egress is rejected. |
| `ING-011` | Authentication enforcement is profile-governed. Standard and above reject unauthenticated requests. Minimal and dev support lightweight authenticated modes. There is no anonymous access in any profile. |
| `ING-012` | Webhook and message bus inbound surfaces always require authentication regardless of active Profile. |
| `ING-013` | Rate limiting is enforced per registered actor. Exceeding rate limits returns 429 Too Many Requests. |

---

## 3. Outbound Webhooks

> **⚠️ Architecture Update — Notification Model Supersedes Outbound Webhooks**
>
> The outbound webhook model described in Section 3 has been one delivery channel within the Notification Model. Outbound webhooks are now one delivery channel type within the notification service model rather than a parallel mechanism.
>
> **For new implementations:** Use the notification service subscription model (doc 23, Section 6) with a webhook-type notification service.
>
>
> The key improvement in the new model: audience is derived from the **entity relationship graph**, not from a manually maintained subscriber list. A webhook subscription for VLAN drift events will now automatically include all VMs attached to that VLAN as audience context.

### 3.1 Concept

DCM pushes event notifications to registered external HTTP endpoints. Outbound webhooks are **optional and policy-governed** — the active Profile and Policy Groups determine which events require external notification.

### 3.2 Webhook Registration

```yaml
webhook_registration:
  artifact_metadata:
    uuid: <uuid>
    handle: "org/webhooks/payments-drift-alerts"
    version: "1.0.0"
    status: active
    owned_by:
      display_name: "Payments Platform Team"
      notification_endpoint: <endpoint>

  name: "Payments Platform Drift Alerts"
  description: "Notifies payments team of drift detection events"

  # SCOPE
  scope:
    type: <tenant|cross_tenant|platform>
    tenant_uuid: <uuid>
    cross_tenant_authorization_uuid: <uuid>   # if cross_tenant

  # EVENT SUBSCRIPTIONS
  event_subscriptions:
    - event_type: drift.detected
      schema_version: "1.0"
      adapter: true              # DCM transforms newer schemas to 1.0
      filter:
        tenant_uuid: <payments-tenant-uuid>
        resource_types: [Compute.VirtualMachine, Storage.Block]
    - event_type: request.realized
      schema_version: "1.0"
    - event_type: entity.state_transition
      schema_version: "1.0"
      filter:
        to_states: [DEGRADED, FAILED]

  # ENDPOINT
  endpoint:
    url: https://alerts.payments.corp.example.com/dcm/events
    sovereignty_check: true     # verify endpoint jurisdiction before delivery

  # AUTHENTICATION
  authentication:
    mode: <hmac_sha256|mtls|bearer_token>
    secret_ref:
      service_provider_uuid: <uuid>
      secret_path: "dcm/webhooks/payments-drift/hmac-secret"
    rotation_policy:
      automatic: true
      interval: P90D
      transition_window: P7D
      notify_before: P14D

  # RELIABILITY
  retry_policy:
    max_attempts: 7
    backoff: exponential
    initial_interval: PT5S
    max_interval: PT1H
    timeout_per_attempt: PT10S
    on_exhaustion: dead_letter   # dead_letter | discard | escalate

  # HEALTH
  health:
    failure_threshold: 10
    suspension_notification: true
    auto_deactivate_after: P30D
    status: active

  # SCHEMA COMPATIBILITY
  schema_adapter:
    enabled: true
    # DCM maintains forward-compatibility adapters per schema version
    # Consumer stays on declared schema_version indefinitely
    deprecation_notice_days: 90
```

### 3.3 Event Taxonomy

> The table below is the event taxonomy for webhook subscriptions.

The event taxonomy maps onto the Universal Audit action vocabulary. All are versioned registry entries:

| Category | Events |
|----------|--------|
| Entity lifecycle | `entity.created`, `entity.modified`, `entity.state_transition`, `entity.deleted`, `entity.expired`, `entity.rehydrated` |
| Group | `group.member_added`, `group.member_removed`, `group.created`, `group.deleted` |
| Relationship | `relationship.created`, `relationship.released` |
| Policy | `policy.activated`, `policy.deactivated`, `policy.evaluated` (fail/gatekeep only), `policy.shadow_result` |
| Provider | `provider.healthy`, `provider.degraded`, `provider.unhealthy`, `provider.registered`, `provider.deregistered` |
| Audit/security | `audit.chain_break`, `audit.forward_failed` |
| Drift | `drift.detected`, `drift.resolved`, `drift.escalated` |
| Request | `request.submitted`, `request.approved`, `request.rejected`, `request.realized`, `request.failed` |
| Rehydration | `rehydration.started`, `rehydration.completed`, `rehydration.paused`, `rehydration.interrupted` |
| Authorization | `authorization.granted`, `authorization.revoked` |
| Webhook | `webhook.secret_rotated`, `webhook.suspended`, `webhook.schema_deprecated` |

### 3.4 Payload Format

```yaml
webhook_payload:
  # Envelope
  event_uuid: <uuid>              # idempotency key
  event_type: drift.detected
  event_schema_version: "1.0"
  timestamp: <ISO 8601>           # from Stage 1 Commit Log — authoritative
  dcm_version: <version>

  # Subject
  subject:
    entity_uuid: <uuid>
    entity_type: infrastructure_resource
    entity_handle: <handle>
    tenant_uuid: <uuid>

  # Delta
  delta:
    drifted_fields:
      - field: cpu_count
        realized_value: 4
        discovered_value: 8
    drift_severity: significant

  # Links
  links:
    self: <DCM API URL for entity>
    audit_record: <DCM API URL for audit record>
```

### 3.5 Delivery Guarantees

- **At-least-once** — not exactly-once; consumers must be idempotent using `event_uuid`
- **Per-entity ordering** — events for a given `entity_uuid` delivered in Commit Log sequence order
- **Cross-entity ordering** — not guaranteed; use `timestamp` for actual occurrence time
- **Sovereignty-aware** — delivery blocked if endpoint jurisdiction incompatible with Tenant sovereignty (WHK-004)

---

## 4. Inbound Webhooks

### 4.1 Concept

DCM exposes authenticated HTTP endpoints that external systems call to submit requests, queries, and events. Inbound webhooks are subject to full Policy Engine evaluation — identical to any other API call.

### 4.2 Inbound Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /webhooks/inbound/request` | Submit a service request |
| `POST /webhooks/inbound/query` | Query entity state or catalog |
| `POST /webhooks/inbound/event` | Push an event (provider state change, CI/CD signal) |
| `POST /webhooks/inbound/ingestion` | Push brownfield ingestion data |
| `POST /webhooks/inbound/data` | Push enrichment or information data |

### 4.3 Webhook Actor Registration

Every inbound webhook caller must be registered as a **webhook actor** — a service account in the DCM identity model:

```yaml
webhook_actor:
  artifact_metadata:
    uuid: <uuid>
    handle: "actors/webhook/cicd-pipeline-prod"
    status: active

  name: "CI/CD Pipeline Production"
  actor_type: webhook_service_account

  # Authentication
  authentication:
    mode: hmac_sha256
    secret_ref:
      service_provider_uuid: <uuid>
      secret_path: "dcm/webhooks/inbound/cicd-pipeline/hmac"

  # Authorization
  role: consumer
  tenant_scope: [<tenant-uuid>]
  permitted_operations:
    - request.submit
    - query.entity_state
    - query.catalog

  # Rate limiting
  rate_limit:
    requests_per_minute: 60
    burst: 10

  # Audit identity
  audit_identity:
    display_name: "CI/CD Pipeline (Production)"
    system: "jenkins-prod-01"
```

### 4.4 Response Model

- **Queries** — synchronous response with result
- **Requests and events** — `202 Accepted` + `request_uuid`; caller polls status or registers outbound webhook for completion notification

---

## 5. event routing service

### 5.1 Concept

A **event routing service** is the sixth DCM provider type — a persistent, high-throughput integration with an external message bus for bidirectional event streaming. Where webhooks are point-to-point HTTP calls, a event routing service is a durable pub/sub connection.

### 5.2 Registration

```yaml
(optional infrastructure)_registration:
  artifact_metadata:
    uuid: <uuid>
    handle: "providers/messagebus/corporate-kafka"
    version: "1.0.0"
    status: active

  name: "Corporate Kafka Cluster"
  provider_type: message_bus

  # Direction
  direction: <outbound|inbound|bidirectional>

  # Protocol
  protocol: <kafka|amqp|nats|mqtt|azure_service_bus|
             aws_eventbridge|gcp_pubsub|rabbitmq|custom>

  # Connection
  connection:
    brokers: [kafka-1.corp:9093, kafka-2.corp:9093, kafka-3.corp:9093]
    credentials_ref:
      service_provider_uuid: <uuid>
      secret_path: "dcm/providers/messagebus/corporate-kafka/credentials"
    tls:
      mode: mtls
      ca_cert_ref:
        service_provider_uuid: <uuid>
        secret_path: "dcm/providers/messagebus/corporate-kafka/ca-cert"

  # Outbound — DCM publishes to external bus
  outbound:
    topic_mapping:
      entity.state_transition: "dcm.entities.state"
      drift.detected: "dcm.drift.alerts"
      request.realized: "dcm.requests.completed"
      audit.chain_break: "dcm.security.alerts"
    schema_version: "1.0"
    delivery_guarantee: at_least_once

  # Inbound — DCM consumes from external bus
  inbound:
    consumer_group: "dcm-inbound-prod"
    topic_mapping:
      "cicd.deployment.completed": request.submit
      "cmdb.discovery.update": ingestion.push
      "itsm.change.approved": request.approve
    # Inbound messages processed as authenticated API calls
    actor_identity_uuid: <webhook-actor-uuid>
    # Same Policy Engine evaluation as inbound webhooks

  # Sovereignty
  operational_sovereignty:
    jurisdiction: eu-west
    certifications: [ISO-27001, GDPR-compliant]

  # Health
  health_check:
    interval_seconds: 30
    on_unhealthy: alert
```

### 5.3 Architecture

```
DCM internal Message Bus (internal pub/sub backbone)
  │
  ├── Webhook Delivery Service ──────→ External HTTP endpoints (outbound webhooks)
  │
  └── Message Bus Bridge Service ────→ External message bus (event routing service)
                                 ←─── External message bus (inbound)
```

The internal Message Bus is never exposed directly. All external event integration goes through either the Webhook Delivery Service or the Message Bus Bridge Service — both of which handle authentication, authorization, sovereignty checks, and schema transformation.

---

## 6. Git PR Ingress — Distributed Git Request Mechanism

### 6.1 Concept

DCM supports **git_pr_merge** as a twelfth ingress surface — enabling teams to submit DCM resource definitions as Pull Requests to a DCM-watched Git repository. This is the native workflow for infrastructure-as-code teams: open a PR, get it reviewed by humans and DCM's policy engine simultaneously, merge to execute.

**Why Git PR ingress matters:**
- GitOps teams work in Git — their deployment workflow is already PR-based
- Security and compliance teams review infrastructure changes the same way they review code
- The PR itself is the human review record; DCM's audit trail captures the automated processing
- Rollback is a Git revert — natural and familiar
- Multi-team approval workflows use existing Git branch protection rules
- The PR diff shows exactly what changes — field-level visibility

### 6.2 The Git Request Watcher

A dedicated control plane component — the **Git Request Watcher** — monitors designated repositories via webhooks (preferred) or polling. It is policy-governed: which repositories it watches, which branches trigger processing, and which resource types may be submitted via Git PR.

### 6.3 Request Repository Structure

```
dcm-requests/                              ← DCM-watched request repository
  {tenant-uuid}/
    pending/
      {resource-handle}/
        request.yaml                       ← Standard DCM resource definition
    realized/
      {resource-handle}/
        realized.yaml                      ← DCM writes realized state here on success
    failed/
      {resource-handle}/
        request.yaml                       ← Moved here on failure with error detail
```

### 6.4 Git Actor Identity Resolution

**Authentication is always required.** Git PR ingress actors must be resolved to DCM actors through the registered Auth Provider — DCM trusts the Git server's authentication assertion, not user-declared Git configuration. Anyone can set their local `git config user.email` to anything; DCM ignores self-declared identity.

**The trust chain:**
```
Git server authenticates user (SSH key, OAuth token, password)
  │  Git server's authentication is trusted — not user's claimed identity
  ▼
DCM Git Request Watcher receives PR merge webhook
  │  Webhook payload contains: actor.login, actor.auth_method, actor.external_id
  │  All verified by the Git server
  ▼
Auth Provider resolution (same path as web UI login for the same user):
  ├── OIDC/OAuth: Git server OAuth subject → OIDC Auth Provider userinfo lookup
  ├── LDAP/AD: Git server username → LDAP lookup → DCM actor
  ├── SSH key: Git server key fingerprint → DCM SSH key registry → DCM actor
  └── Service account: Git service account → registered webhook actor
  ▼
Fully resolved DCM actor — same roles, groups, tenant scope as any other user
```

**Resolution methods:**

```yaml
git_actor_resolution:
  # Method 1: OIDC/OAuth (recommended — Git server uses same IdP as DCM)
  method: oidc_subject_lookup
  auth_provider_uuid: <corporate-oidc-uuid>

  # Method 2: LDAP/AD (enterprise — Git server authenticates via corporate directory)
  method: ldap_username_lookup
  auth_provider_uuid: <freeipa-ldap-uuid>

  # Method 3: SSH key fingerprint
  method: ssh_key_fingerprint
  # Keys registered in DCM SSH key registry, linked to actor UUIDs

  # Method 4: Service account (automated workflows)
  method: webhook_service_account
  # Git service account mapped to registered webhook actor
```

**Identity resolution failure — explicit rejection:**

When DCM cannot map the merge actor to a DCM actor, the PR is rejected with an actionable comment. Never silently ignored.

```
❌ DCM Identity Resolution Failed

DCM could not map the merge actor "jsmith" to a DCM actor identity.

Possible causes:
  • Your Git account is not linked to a DCM actor via the corporate Auth Provider
  • Your DCM actor account has been suspended or deactivated

To resolve:
  • Contact your platform administrator: https://dcm.corp.example.com/actors/git-identity-setup

This PR will not be processed until identity resolution succeeds.
```

### 6.5 The ingress Block for Git PR

```yaml
ingress:
  surface: git_pr_merge               # or: git_pr_open (for shadow validation)
  protocol: https
  authenticated_via: oidc             # or: ldap_direct_bind, active_directory, ssh_key
  actor:
    uuid: <dcm-actor-uuid>
    type: human
    display_name: "Jane Smith"
    identity_source: oidc
    auth_provider_uuid: <uuid>
    roles: [consumer]
    tenant_scope: [<payments-tenant-uuid>]
    groups: [<payments-team-group-uuid>]
    # Groups and tenant scope: SAME mappings as web UI login for this user
    external_identity:
      provider: github                # or: gitlab, gitea, freeipa, active_directory
      subject: <oauth-subject>        # verified by Git server
      git_username: jsmith
      git_verified_email: jsmith@corp.com  # from Git server record — not git config
    mfa_verified: true                # from Auth Provider session record
  git_context:
    repository: https://git.corp.example.com/dcm-requests/payments
    pr_number: 142
    pr_url: https://git.corp.example.com/payments/pulls/142
    merge_commit: <sha>
    base_branch: main
    pr_author: jsmith
    pr_reviewers: [platform-team, security-team]
    pr_approved_by: [<platform-admin-uuid>, <security-owner-uuid>]
    # Approved by: DCM resolves Git reviewer identities via same Auth Provider
```

### 6.6 PR Lifecycle — DCM Processing Flow

```
1. Developer creates resource definition YAML (standard DCM request format)
   │
2. Opens PR against dcm-requests/{tenant-uuid}/pending/
   │
3. DCM Git Watcher detects PR (git_pr_open event)
   │
4. DCM resolves PR author → DCM actor via Auth Provider
   │  Failure → post rejection comment; stop processing
   │
5. DCM validates actor tenant scope against target Tenant
   │  Failure → post rejection comment; stop processing
   │
6. Shadow policy evaluation (same nine-step assembly — dry run)
   │  Results posted as PR review comments:
   │  "✅ Schema valid"
   │  "✅ All policies pass"
   │  "⚠️  Will be placed in eu-west-1 per sovereignty policy"
   │  "❌ GateKeeper: VM size exceeds quota — reduce cpu_count"
   │
7. Human review and approval (standard Git PR workflow)
   │  Branch protection enforces required reviewers
   │  Policy may declare: require DCM-defined approvers in git_context.pr_approved_by
   │
8. PR merged to main (git_pr_merge event)
   │  ingress_surface: git_pr_merge
   │  Actor re-verified at merge time (not assumed from PR open time)
   │
9. DCM processes as standard nine-step assembly (real — not shadow)
   │
10. DCM posts realization result as PR comment + status check
    │  "✅ VM payments-prod-01 realized — UUID: <uuid>"
    │  "❌ Realization failed — audit record: <uuid>"
    │
11. DCM commits realized state to realized/ directory (optional)
    Git history = full lifecycle record
```

### 6.7 Policy Engine Use Cases — Git PR Ingress

```yaml
# Require PR approval before processing production resources
policy:
  type: gatekeeper
  rule: >
    If ingress.surface == git_pr_merge
    AND tenant.profile IN [prod, fsi, sovereign]
    AND ingress.git_context.pr_approved_by NOT CONTAINS required_approvers
    THEN gatekeep: "PR requires approval from platform admin and security owner"

# Require MFA for Git PR merges in production Tenants
policy:
  type: gatekeeper
  rule: >
    If ingress.surface == git_pr_merge
    AND tenant.profile IN [prod, fsi, sovereign]
    AND ingress.actor.mfa_verified == false
    THEN gatekeep: "MFA required for Git PR merges in production Tenants"

# Restrict resource types submittable via Git PR
policy:
  type: gatekeeper
  rule: >
    If ingress.surface == git_pr_merge
    AND resource_type NOT IN [Compute.VirtualMachine, Storage.Block]
    THEN gatekeep: "Only compute and storage resources may be submitted via Git PR"

# Require actor to be in authorized Git team for target Tenant
policy:
  type: gatekeeper
  rule: >
    If ingress.surface == git_pr_merge
    AND ingress.actor.groups NOT CONTAINS tenant.authorized_git_groups
    THEN gatekeep: "Git PR author is not in an authorized group for this Tenant"

# Post shadow results as PR comments (transformation)
policy:
  type: transformation
  placement_phase: pre
  rule: >
    If ingress.surface IN [git_pr_merge, git_pr_open]
    THEN inject: git_feedback.post_as_pr_comment = true
```

### 6.8 Updated Ingress Surface Taxonomy

```yaml
ingress_surface_taxonomy:
  - web_ui                 # DCM's own web interface
  - consumer_api           # Direct REST API call
  - webhook_inbound        # Inbound webhook call
  - message_bus_inbound    # Inbound message bus
  - provider_callback      # Provider reporting back
  - policy_engine          # Policy-generated sub-request
  - scheduler              # Scheduled/timed trigger
  - rehydration            # Rehydration-generated
  - ingestion              # Ingestion pipeline
  - dcm_internal           # DCM system-generated
  - operator_cli           # Command line interface
  - git_pr_merge           # Git PR merge → execute  ← new
  - git_pr_open            # Git PR open → shadow validation only  ← new
```

### 6.9 System Policies — Git PR Ingress

| Policy | Rule |
|--------|------|
| `GIT-001` | DCM supports git_pr_merge and git_pr_open as ingress surfaces. Git PR ingress is subject to full Policy Engine evaluation identical to API ingress. |
| `GIT-002` | DCM trusts the Git server's authentication assertion — not user-declared Git configuration. DCM resolves the Git server's verified identity through the registered Auth Provider to produce a fully-resolved DCM actor with the same role, group, and tenant scope mappings as any other user authenticated via the same Auth Provider. |
| `GIT-003` | Unresolvable Git actor identities are rejected with an actionable PR comment. PRs are never silently ignored. |
| `GIT-004` | The resolved Git PR actor must have the target Tenant UUID in their tenant_scope. PRs targeting Tenants outside the actor's scope are rejected — same enforcement as API tenant scope checks. |
| `GIT-005` | DCM posts shadow policy evaluation results as PR review comments on git_pr_open. GateKeeper failures should be surfaced via repository branch protection integration. |
| `GIT-006` | PR approval status may be declared as an authorization requirement by policy. DCM checks declared reviewer approvals against the PR's actual approval record before processing a merged PR. |
| `GIT-007` | The Git Request Watcher component is policy-governed: which repositories it monitors, which branches trigger processing, and which resource types may be submitted via Git PR are declared via Policy Group. |
| `GIT-008` | Actor identity is re-verified at merge time — not assumed from PR open time. A user whose DCM actor is suspended between PR open and merge will be rejected at merge. |

---



| Policy | Rule |
|--------|------|
| `WHK-001` | Events for a given entity_uuid are delivered in Commit Log sequence order. Cross-entity ordering is not guaranteed. |
| `WHK-002` | Webhook delivery uses at-least-once semantics. Consumers must be idempotent using event_uuid as the deduplication key. |
| `WHK-003` | Outbound webhook authentication must be declared at registration. Supported: hmac_sha256 (default), mtls, bearer_token. Unauthenticated webhooks are rejected. |
| `WHK-004` | Webhook endpoints that would deliver data outside a Tenant's sovereignty boundary are subject to sovereignty checks. |
| `WHK-005` | Webhook governance is policy-driven. Profiles set defaults — fsi/sovereign profiles may require webhook coverage for audit events via Policy Group. |
| `WHK-006` | Webhook registrations must declare the event schema version expected. DCM supports current and N-1 schema versions simultaneously. |
| `WHK-007` | Platform-scoped webhooks require Platform Admin role and are audit-logged as CONFIG_CHANGE. |
| `WHK-008` | Cross-tenant webhooks require a valid cross_tenant_authorization record (XTA-001). |
| `WHK-009` | Inbound webhook callers must be registered as webhook actors with explicit role, tenant scope, and permitted operations. Unregistered callers are rejected with 401. |
| `WHK-010` | Inbound webhook calls are subject to full Policy Engine evaluation — identical to any other API call. No bypass. |
| `WHK-011` | All inbound webhook calls are recorded in the audit trail with the webhook actor as the immediate actor. |
| `WHK-012` | Inbound webhook endpoints return 202 Accepted + request_uuid for async operations. |
| `WHK-013` | Rate limiting is enforced per registered webhook actor. Exceeding rate limits returns 429 Too Many Requests. |
| `WHK-014` | All credential references in webhook and message bus configurations must resolve through a registered credential management service. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
