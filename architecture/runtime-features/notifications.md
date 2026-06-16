# DCM Data Model — Notification Model


**Document Status:** ✅ Complete
**Document Type:** Architecture Reference

> **Foundation Document Reference**
>
> This document is a detailed reference for a specific domain of the DCM architecture.
> The three foundational abstractions — Data, Provider, and Policy — are defined in
> [udlm/foundations/foundations.md](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md). All concepts in this document map to one or
> more of those three abstractions.
> See also: [Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [Policy Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md)
>
> **This document maps to: PROVIDER + POLICY**
>
> Provider: notification service. Policy: audience resolution and subscription rules


**Related Documents:** [Webhooks, Messaging, and External Integration](webhooks-messaging.md) | [Entity Relationships](https://github.com/croadfeldt/udlm/blob/main/entities/entity-relationships.md) | [Resource/Service Entities](https://github.com/croadfeldt/udlm/blob/main/entities/resource-service-entities.md) | [Auth Providers](https://github.com/croadfeldt/udlm/blob/main/governance/auth-providers.md) | [Universal Audit](https://github.com/croadfeldt/udlm/blob/main/observability/universal-audit.md)

---


> **See [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md)** — authoritative source for all DCM event types and payload schemas.

## 1. Purpose

The DCM Notification Model defines a **unified, configurable notification pipeline** that routes event notifications to all parties with a stake in a changed resource — not just the original requestor. The audience for any notification is derived from the **entity relationship graph**, not from who submitted the original request.

This document defines:
- The notification service — the ninth DCM provider type
- The event taxonomy — a closed vocabulary of notification-worthy events
- The audience resolution model — how the relationship graph determines who gets notified
- The subscription model — how actors declare their notification preferences
- The notification payload structure — the unified envelope all notification services receive
- The delivery pipeline — from event trigger through audience resolution through provider delivery

Outbound webhooks are one delivery channel within this model, implemented via the notification service.

---

## 2. Design Principles

**Relationship graph determines audience.** When a resource changes, DCM traverses the entity relationship graph to find all stakeholders. A VLAN decommission notifies every VM attached to that VLAN, regardless of which Tenant owns each VM. The graph is the source of truth for notification scope.

**Delivery mechanism is configurable, not prescribed.** DCM generates and routes notifications. How they are delivered — email, Slack, PagerDuty, ServiceNow, webhook, SMS — is the concern of a notification service. Organizations register the notification service(s) that fit their operations.

**Three notification tiers.** Some notifications are mandatory and non-suppressable (security, sovereignty violations, audit chain breaks). Some are Tenant-default (all resource lifecycle events in a Tenant). Some are actor-subscription (specific events on specific resources). All three compose without conflict.

**Audience role shapes the notification.** The same event produces different notifications for an owner ("your resource changed") versus a stakeholder ("a resource you depend on changed") versus an approver ("your approval is required"). The audience role is part of the notification envelope.

**Delivery is audited.** Every notification dispatch is an audit record. Delivery failures are tracked and escalated per policy.

---

## 3. The notification service

The notification service is the ninth formal DCM provider type. It handles the translation from DCM's unified notification envelope to the delivery channel's native format, and it handles delivery, retry, and delivery confirmation.

### 3.1 Provider Types Table Update

| # | Type | Purpose |
|---|------|---------|
| 1 | Service Provider | Realizes resources |
| 2 | Information Provider | Serves authoritative external data |
| 3 | composite service definition | Composes multiple providers |
| 4 | data store | Persists DCM state |
| 5 | event routing service | Event streaming and messaging |
| 6 | External Policy Evaluator | External policy logic |
| 7 | credential management service | Resolves secrets |
| 8 | Auth Provider | Authenticates identities |
| **9** | **notification service** | **Delivers notifications via configured channels** |

### 3.2 notification service Registration

```yaml
service_provider_registration:
  artifact_metadata:
    uuid: <uuid>
    handle: "org/notifications/slack-provider"
    version: "1.0.0"
    status: active
    owned_by: { display_name: "Platform Engineering" }

  provider_type: notification
  display_name: "Slack notification service"
  description: "Delivers DCM notifications to configured Slack channels"

  # Delivery channels this provider supports
  delivery_channels:
    - channel_type: slack
      config_schema_ref: <uuid>          # JSON Schema for channel config
      supports_threading: true
      supports_urgency_routing: true     # different channels per urgency level
    - channel_type: webhook
      config_schema_ref: <uuid>

  # Sovereignty declaration — same model as all providers
  sovereignty_declaration:
    data_residency_guarantee: EU
    operating_jurisdictions: [DE, FR, NL]

  # Delivery guarantees this provider offers
  delivery_guarantees:
    at_least_once: true
    idempotency_key: notification_uuid
    max_delivery_latency: PT30S        # for critical urgency
    retry_policy:
      max_attempts: 7
      backoff: exponential
      initial_interval: PT5S
      max_interval: PT1H
      on_exhaustion: dead_letter

  # Health check endpoint (on the provider)
  health_endpoint: https://notif-provider.corp.example.com/health

  # Callback endpoint (DCM calls this to submit notifications)
  delivery_endpoint: https://notif-provider.corp.example.com/deliver
```

### 3.3 Multiple notification services

Organizations may register multiple notification services — one for Slack, one for PagerDuty, one for ServiceNow tickets. Notification subscriptions declare which provider to use for delivery. The Notification Router in DCM routes each notification to the correct provider based on the subscription's `service_provider_uuid`.

---

## 4. The Event Taxonomy

The notification event taxonomy is a **closed vocabulary** — a finite, versioned set of event types that DCM can generate notifications for. Events are grouped by category. Subscriptions reference these event types by name.

### 4.1 Request Lifecycle Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `request.acknowledged` | Request received, Intent State created | Owner |
| `request.requires_approval` | Policy requires human review before dispatch | Owner, Approvers |
| `request.approved` | Intent State PR merged; proceeding to assembly | Owner |
| `request.dispatched` | Requested State committed; dispatched to provider | Owner |
| `request.completed` | Provider confirmed realization; Realized State written | Owner |
| `request.failed` | Request failed at any stage | Owner |
| `request.cancelled` | Consumer cancelled; request terminated | Owner |
| `request.gatekeeper_rejected` | GateKeeper policy rejected the request | Owner, Policy Owner |

### 4.2 Resource Lifecycle Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `entity.realized` | Entity first realized by provider | Owner, Stakeholders (depth 1) |
| `entity.state_changed` | Entity lifecycle state transition | Owner, Stakeholders (required) |
| `entity.ttl_warning` | TTL expires within declared warning window | Owner |
| `entity.ttl_expired` | TTL reached; expiry action triggered | Owner, Stakeholders (required) |
| `entity.suspended` | Entity entered SUSPENDED state | Owner, Stakeholders (required) |
| `entity.resumed` | Entity exited SUSPENDED state | Owner, Stakeholders (required) |
| `entity.decommissioning` | Decommission initiated | Owner, Stakeholders (all) |
| `entity.decommissioned` | Entity fully decommissioned | Owner, Stakeholders (all) |
| `entity.decommission_deferred` | Decommission blocked by active stakes | Owner, Stakeholders (required) |
| `entity.ownership_transferred` | Ownership moved to a different Tenant | Previous Owner, New Owner |
| `entity.pending_review` | Entity entered PENDING_REVIEW state | Owner, Platform Admin |

### 4.3 Drift and Discovery Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `drift.detected` | Discovered State differs from Realized State | Owner |
| `drift.severity_escalated` | Drift severity increased | Owner, Platform Admin |
| `drift.resolved` | Drift resolved (REVERT or UPDATE_DEFINITION) | Owner |
| `drift.escalated` | Drift escalated to human review | Owner, Platform Admin, SRE |
| `unsanctioned_change.detected` | Change detected with no corresponding Requested State record | Owner, Security Team, Platform Admin |

### 4.4 Provider Update Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `provider_update.submitted` | Provider submitted an update notification | Owner |
| `provider_update.requires_approval` | Provider update requires consumer approval | Owner (approval required) |
| `provider_update.approved` | Provider update approved; Realized State updated | Owner |
| `provider_update.rejected` | Provider update rejected; becomes drift | Owner, Provider Team |
| `provider_update.auto_approved` | Provider update auto-approved by pre-authorization policy | Owner (informational) |

### 4.5 Dependency and Relationship Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `dependency.state_changed` | A required dependency's state changed | Owner of dependent entity |
| `stakeholder.resource_decommissioning` | A shared resource the actor stakes is decommissioning | All stakeholders |
| `allocation.pool_capacity_low` | Allocation pool capacity below threshold | Pool Owner, Platform Admin |
| `allocation.released` | Allocation decommissioned; capacity returned to pool | Pool Owner |
| `cross_tenant_auth.expiring` | Cross-tenant authorization expiring | Both Tenant Admins |
| `cross_tenant_auth.revoked` | Cross-tenant authorization revoked while allocation active | Both Tenant Admins, Affected Resource Owners |

### 4.6 Governance Events

| Event Type | Trigger | Default Audience |
|-----------|---------|-----------------|
| `policy.activated` | Policy moved to active status | Platform Admin, Policy Owner |
| `policy.deactivated` | Policy deactivated | Platform Admin, Policy Owner |
| `external_policy_evaluation.trust_elevated` | External Policy Evaluator mode level elevated | Platform Admin, Security Team |
| `profile.changed` | Active deployment profile changed | Platform Admin, All Tenant Admins |
| `catalog_item.deprecated` | Catalog item deprecated | All consumers with active resources of that type |

### 4.7 Security and System Events (Mandatory — Non-Suppressable)

| Event Type | Trigger | Audience |
|-----------|---------|---------|
| `audit.chain_integrity_alert` | Hash chain verification failure detected | Security Team, Platform Admin |
| `sovereignty.violation` | Resource in violation of sovereignty constraints | Platform Admin, Security Team, Resource Owner |
| `sovereignty.migration_required` | Provider sovereignty change requires entity migration | Platform Admin, Resource Owner |
| `federation.tunnel_degraded` | DCM-to-DCM federation tunnel health degraded | Platform Admin, SRE |
| `auth.provider_failover` | Auth Provider failed over to secondary | Platform Admin |
| `rehydration.blocked` | Concurrent rehydration attempt rejected | Requesting Actor, Platform Admin |
| `security.unsanctioned_provider_write` | Attempted write to Realized Store without Requested State ref | Security Team, Platform Admin |

---

## 5. Audience Resolution — The Relationship Graph Model

### 5.1 The Fundamental Rule

**The audience for a notification is every entity with a stake in the changed resource, resolved by traversing the relationship graph from the changed entity.**

The notification system does not maintain a separate subscriber list per entity. It derives the audience at event time by traversing the relationship graph. This means the audience is always current — adding a new VM attachment to a VLAN automatically includes that VM's owner in future VLAN notifications, without any subscription update required.

### 5.2 Audience Resolution Algorithm

```
Event fires on entity E (e.g., VLAN-100 decommissioning)
  │
  ▼ Step 1: Resolve direct owner
  │   entity.owned_by_tenant_uuid → Tenant Admin and resource owner actors
  │   Audience role: owner
  │
  ▼ Step 2: Traverse relationship graph
  │   For each relationship on entity E:
  │     Check: is this relationship type notification-relevant for this event type?
  │     Check: does the relationship's stake_strength meet the minimum for this event?
  │     If yes: resolve the related entity's owner → add to audience
  │     Audience role: stakeholder
  │
  ▼ Step 3: Check for approval requirements
  │   Does this event require approval from a specific actor?
  │   If yes: add approver to audience
  │   Audience role: approver
  │
  ▼ Step 4: Apply mandatory system audiences
  │   Security events: always include Security Team and Platform Admin
  │   Governance events: always include Policy Owner and Platform Admin
  │   (These cannot be filtered out by subscription preferences)
  │
  ▼ Step 5: Apply actor subscription overrides
  │   Actors with explicit subscriptions to this event type → include/exclude per subscription
  │   (Subscriptions can add additional audience; they cannot remove mandatory audiences)
  │
  ▼ Step 6: Deduplicate and resolve contact details
  │   Same actor via multiple paths → one notification with all audience_roles listed
  │   Resolve each actor to their configured notification channels
  │
  ▼ Step 7: Route to notification service(s)
      One notification per actor per configured channel
      Notification envelope includes audience_role
```

### 5.3 Relationship Notification Relevance

The Resource Type Specification declares which relationship types are notification-relevant and for which events:

```yaml
resource_type_spec:
  fqn: Network.VLAN
  notification_rules:
    - event_type: entity.decommissioning
      notify_relationships:
        - relationship_type: attached_to     # source direction (VMs attached to this VLAN)
          min_stake_strength: required        # only required stakes get notified
          traversal_depth: 1                  # direct relationships only
          audience_role: stakeholder
        - relationship_type: attached_to
          min_stake_strength: optional        # optional stakes get informational notice
          traversal_depth: 1
          audience_role: observer

    - event_type: entity.state_changed
      notify_relationships:
        - relationship_type: attached_to
          min_stake_strength: required
          traversal_depth: 1
          audience_role: stakeholder
```

**Traversal depth:** `1` means direct relationships only. `2` means relationships of related entities. In most cases `1` is correct — deeper traversal is reserved for critical security events that affect the entire graph.

### 5.4 Cross-Tenant Notification

Notification traversal follows relationship graphs across Tenant boundaries. If a VM in AppTeam Tenant has a `required` stake in a VLAN owned by NetworkOps Tenant, and the VLAN is decommissioned, AppTeam receives a stakeholder notification — even though the VLAN belongs to a different Tenant.

Cross-tenant notifications are governed by the same sovereignty rules as cross-tenant data access:
- Notification content is limited to what the receiving Tenant is authorized to know
- The notification identifies the changed resource but does not expose the owning Tenant's configuration details
- Sovereignty checks apply to notification delivery (a notification about an EU-sovereign resource cannot be delivered to a US-based endpoint)

```yaml
notification_sovereignty_check:
  # Before delivering cross-tenant notification:
  check:
    - receiver_tenant_sovereignty_compatible: true
    - notification_content_authorized_for_receiver: true
    - delivery_endpoint_jurisdiction_compatible: true
  on_failure: redact_and_deliver   # or: suppress_with_audit | block_with_alert
```

---

## 6. Notification Subscriptions

### 6.1 Three Subscription Tiers

**Tier 1 — Mandatory System Notifications (non-suppressable):**
Security events, sovereignty violations, audit chain breaks. Always delivered to the declared system audiences (Security Team, Platform Admin) regardless of any subscription configuration. No actor or policy can suppress these.

**Tier 2 — Tenant Default Notifications:**
Configured by Tenant admins for all resources in their Tenant. Establishes the baseline notification behavior — which events trigger notifications, which channels to use, and which urgency mapping to apply.

```yaml
tenant_notification_defaults:
  tenant_uuid: <uuid>
  service_provider_uuid: <slack-provider-uuid>

  default_channel_config:
    channel_type: slack
    workspace: "corp"
    urgency_routing:
      critical: "#platform-incidents"
      high: "#platform-alerts"
      medium: "#platform-notifications"
      low: "#platform-digest"        # batched hourly

  # Which event categories are enabled by default for all resources in this Tenant
  enabled_event_categories:
    request_lifecycle: [request.completed, request.failed, request.gatekeeper_rejected]
    resource_lifecycle: [entity.state_changed, entity.ttl_warning, entity.decommissioning]
    drift: [drift.detected, unsanctioned_change.detected]
    provider_update: [provider_update.requires_approval, provider_update.rejected]
    dependency: [stakeholder.resource_decommissioning, cross_tenant_auth.revoked]

  # Urgency defaults per event type
  urgency_overrides:
    unsanctioned_change.detected: critical
    drift.detected: high
    entity.ttl_warning: medium
    request.completed: low
```

**Tier 3 — Actor-Level Subscriptions:**
Individual actors subscribe to specific events on specific resources or resource types. Most useful for service accounts (CI/CD pipelines, monitoring tools) that need targeted event feeds.

```yaml
actor_notification_subscription:
  subscription_uuid: <uuid>
  actor_uuid: <uuid>
  service_provider_uuid: <pagerduty-provider-uuid>

  channel_config:
    channel_type: pagerduty
    service_id: "payments-api-on-call"
    escalation_policy_id: "payments-prod"

  subscriptions:
    # Subscribe to all drift events on VMs in AppTeam Tenant
    - scope:
        tenant_uuid: <appteam-uuid>
        resource_type: Compute.VirtualMachine
      events: [drift.detected, unsanctioned_change.detected]
      urgency_override: high

    # Subscribe to decommission of a specific VLAN I depend on
    - scope:
        entity_uuid: <vlan-100-uuid>
      events: [entity.decommissioning, entity.decommissioned]
      urgency_override: critical
```

### 6.2 Subscription Composition Rules

When multiple subscription tiers match for the same actor and event:
- Mandatory system notifications always fire (cannot be suppressed)
- Tenant defaults fire unless the actor's subscription explicitly opts out for that event type
- Actor subscriptions can add additional channels or override urgency — they do not suppress Tenant defaults unless the subscription explicitly declares `suppress_tenant_default: true`
- Deduplication: if the same notification would be delivered to the same actor via two channels from two subscription matches, deliver once per channel (not once per subscription match)

---

## 7. Notification Payload — The Unified Envelope

Every notification delivered to a notification service uses this unified envelope. The notification service translates it to the delivery channel's native format.

```yaml
notification:
  # Identity
  notification_uuid: <uuid>              # idempotency key
  correlation_id: <uuid>                 # links to the audit record for the triggering event
  generated_at: <ISO 8601>

  # The event
  event_type: entity.decommissioning     # from the closed taxonomy
  event_uuid: <uuid>                     # the triggering event's UUID
  urgency: <critical|high|medium|low>

  # The subject entity
  entity:
    uuid: <uuid>
    handle: <string>
    resource_type: Network.VLAN
    display_name: "VLAN-100 (EU-WEST Production)"
    tenant_uuid: <uuid>
    tenant_display_name: "NetworkOps"

  # Audience context
  audience:
    actor_uuid: <uuid>
    actor_display_name: "Jane Smith"
    audience_role: <owner|stakeholder|approver|observer>
    # stakeholder: explains WHY this actor is in the audience
    stakeholder_reason:
      via_entity_uuid: <vm-a-uuid>       # "because your VM-A is attached to this VLAN"
      via_relationship_type: attached_to
      via_entity_display_name: "VM-A (payments-api-server-01)"

  # What changed
  context:
    previous_state: OPERATIONAL
    new_state: DECOMMISSIONING
    change_summary: "VLAN-100 decommission initiated by NetworkOps team"
    changed_fields: []
    changed_by:
      actor_uuid: <uuid>
      actor_display_name: "Bob Jones (NetworkOps)"
    effective_at: <ISO 8601>

  # Action required (if any)
  requires_action: false
  action:
    type: null                           # approve | acknowledge | migrate | release_stake
    description: null
    action_url: null
    deadline: null

  # Deep links
  links:
    entity_url: "https://dcm.corp.example.com/resources/<uuid>"
    event_url: "https://dcm.corp.example.com/audit/<correlation_id>"
    related_entities:
      - uuid: <vm-a-uuid>
        display_name: "VM-A (payments-api-server-01)"
        url: "https://dcm.corp.example.com/resources/<vm-a-uuid>"
```

### 7.1 Urgency Mapping

| Urgency | Meaning | Typical delivery target |
|---------|---------|------------------------|
| `critical` | Immediate action required; outage or security risk imminent | On-call pager, incident channel |
| `high` | Action required; significant impact if not addressed | Alert channel, SRE queue |
| `medium` | Action recommended; non-urgent but should not be ignored | Notification channel, daily digest |
| `low` | Informational; no action required | Digest, async channel |

Default urgency per event type is declared in the event taxonomy. Tenant defaults and actor subscriptions may override upward or downward.

---

## 8. The Delivery Pipeline

```
Event fires (e.g., VLAN-100 enters DECOMMISSIONING state)
  │
  ▼ Stage 1: Audit record written (Stage 1 Commit Log — synchronous)
  │   ENTITY_STATE_CHANGED audit record committed
  │   event_uuid assigned
  │
  ▼ Stage 2: Notification Router evaluates
  │   Load entity relationship graph for VLAN-100
  │   Run audience resolution algorithm (Section 5.2)
  │   Result: [AppTeam, DevTeam, OpsTeam] as stakeholders; [NetworkOps] as owner
  │
  ▼ Stage 3: Subscription resolution
  │   For each audience member:
  │     Resolve Tier 1 mandatory notifications
  │     Apply Tier 2 Tenant defaults
  │     Apply Tier 3 actor subscriptions
  │     Determine: which notification service(s); which channel config; urgency
  │
  ▼ Stage 4: Notification envelope generation
  │   One envelope per audience member per delivery
  │   Audience role set correctly (owner / stakeholder / approver / observer)
  │   Stakeholder reason populated for non-owners
  │
  ▼ Stage 5: Route to notification service(s)
  │   POST to provider delivery endpoint with notification envelope
  │   Provider translates to delivery channel (Slack, PagerDuty, email, etc.)
  │   Provider returns delivery_uuid and status
  │
  ▼ Stage 6: Delivery confirmation
  │   Provider reports: delivered | failed | queued
  │   Delivery record written to Notification Delivery Store
  │   NOTIFICATION_DISPATCHED audit record written (async)
  │
  ▼ Stage 7: Failure handling
      On provider delivery failure:
        Retry per provider's declared retry policy
        On exhaustion: dead_letter to platform admin
        On critical urgency exhaustion: escalate immediately
        NOTIFICATION_DELIVERY_FAILED audit record written
```

### 8.1 Notification Delivery Store

A lightweight store (not the Audit Store) tracking delivery status per notification:

```yaml
notification_delivery_record:
  delivery_uuid: <uuid>
  notification_uuid: <uuid>
  actor_uuid: <uuid>
  service_provider_uuid: <uuid>
  channel_type: slack
  status: <dispatched|delivered|failed|dead_lettered>
  dispatched_at: <ISO 8601>
  delivered_at: <ISO 8601|null>
  failure_reason: <string|null>
  retry_count: 2
```

---

## 9. Provider Update Notification Integration

Provider Update Notifications (doc 06, Section 7a) integrate with the notification model at two points:

**When provider submits update notification:**
- `provider_update.submitted` fires → Owner notified (informational)

**When provider update requires consumer approval:**
- `provider_update.requires_approval` fires → Owner notified (action required)
- `action.type: approve`
- `action.action_url` points to `/api/v1/resources/{uuid}/provider-notifications/{uuid}:approve`
- `action.deadline` set per policy (default PT24H — if no response, escalate)

**On resolution:**
- Approved → `provider_update.approved` fires → Owner notified; Stakeholders notified of state change via `entity.state_changed`
- Rejected → `provider_update.rejected` fires → Owner notified; becomes drift event → `drift.detected` fires

---

## 10. Relationship to Webhooks and Message Bus

### 10.1 Webhooks as a Notification Channel

Outbound webhooks (doc 18) are now **one delivery channel type within the notification service model** rather than a parallel mechanism. A notification service with `channel_type: webhook` delivers notifications to configured HTTP endpoints using the unified notification envelope.

The webhook registration model (doc 18, Section 3.2) is implemented as actor-level subscriptions (Section 6.1, Tier 3) with a webhook-type notification service. 

### 10.2 Message Bus as Notification Infrastructure

The event routing service (doc 18, Section 5) is the **internal transport** for the notification pipeline. The Notification Router publishes notification events to the Message Bus. notification services subscribe to their assigned topics. This decouples event generation from delivery and enables high-throughput notification processing.

```
DCM Event → Notification Router → Message Bus → notification service subscription
```

The Message Bus is infrastructure — not a notification channel. Consumers do not subscribe to the Message Bus directly for notifications; they use the subscription model (Section 6.1).

---

## 11. System Policies

| Policy | Rule |
|--------|------|
| `NOT-001` | The audience for every notification is derived from the entity relationship graph at event time. DCM does not maintain static subscriber lists per entity. |
| `NOT-002` | Mandatory system notifications (Tier 1: security, sovereignty, audit chain) are never suppressable by any subscription configuration or policy. |
| `NOT-003` | Cross-tenant notifications carry only information the receiving Tenant is authorized to see. Sovereignty checks apply to notification delivery endpoints. |
| `NOT-004` | Every notification dispatch is an audit record. Delivery failures are tracked. Critical urgency delivery exhaustion triggers immediate escalation to Platform Admin. |
| `NOT-005` | Provider Update Notifications that require consumer approval carry `action.type: approve` and `action.deadline`. If the deadline passes without resolution, the notification escalates per policy. |
| `NOT-006` | Notification traversal depth is bounded. Resource Type Specifications declare the maximum traversal depth for each event type. Default: depth 1 (direct relationships only). |
| `NOT-007` | A notification service must be registered and active before notifications can be delivered. DCM does not have a built-in delivery channel — at minimum a webhook-type notification service must be configured for external delivery. |
| `NOT-008` | The notification event taxonomy is a closed vocabulary. Custom event types are not supported. New event types require a DCM registry proposal following standard governance. |

---

## 12. Related Concepts

- **notification service** — the ninth DCM provider type; handles translation and delivery
- **Notification Router** — DCM control plane component that resolves audiences and routes to providers
- **Audience Resolution** — deriving notification recipients from the entity relationship graph
- **Notification Subscription** — actor or Tenant declaration of notification preferences
- **Notification Delivery Store** — lightweight store tracking delivery status
- **Provider Update Notification** — formal provider mechanism for reporting authorized state changes (see doc 06, Section 7a)
- **Outbound Webhook** — one delivery channel type within the notification service model

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
