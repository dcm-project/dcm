# DCM Provider Management GUI Specification

> **AEP Alignment:** Provider API endpoints referenced in this spec follow [AEP](https://aep.dev) conventions — custom methods use colon syntax. See `schemas/openapi/dcm-admin-api.yaml` for the normative specification.


**Document Status:** 🔄 In Progress
**Document Type:** Specification — Provider Management Interface
**Related Documents:** [Unified Provider Contract](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md) | [OIS Specification](dcm-operator-interface-spec.md) | [Registration Specification](dcm-registration-spec.md) | [Admin GUI Specification](dcm-admin-gui-spec.md) | [credential management service Model](https://github.com/croadfeldt/udlm/blob/main/governance/credentials.md)

> **Status:** Draft — Ready for implementation feedback
>
> The Provider Management GUI is the interface for teams responsible for operating and maintaining DCM providers. It surfaces in the DCM web application for actors holding provider owner roles. Each of the eleven DCM provider types has a common management shell plus type-specific extension panels.

---

## 1. Architecture

### 1.1 Surface in Unified Shell

Provider management is a **third surface in the unified DCM web application**. An actor who owns a provider (registered in a provider's `owner_team_uuid` or holds the `provider_owner` role scoped to a provider) sees a "Providers" section in their navigation alongside the Consumer Portal.

```
DCM Web Application
├── Consumer Portal
├── Admin Panel                    ← platform_admin role
└── Provider Management            ← provider_owner role
      ├── My Providers (list)
      └── [Provider Type] → [type-specific management]
```

### 1.2 Provider Owner Identity

Provider ownership is declared at registration time and may include:
- A tenant UUID (the team that owns this provider)
- A group UUID (the specific group within that tenant)
- Named contacts (from Business Data)

The `provider_owner` role is scoped to specific provider UUIDs — a team may own multiple providers and sees all of them. Platform Admins see all registered providers across all owners.

### 1.3 Common Management Shell

Every provider type (all eleven) renders within the same management shell. The shell provides:
- Provider name, type badge, health status indicator
- Registration status (pending / active / suspended / deregistered)
- Navigation tabs that vary by provider type
- Health check response viewer
- Audit trail for all admin actions on this provider

---

## 2. Common Provider Tabs (All Types)

### 2.1 Overview

- Provider UUID, handle, type, registration date, owner team/group
- Health status: current `pass | warn | fail` with last check timestamp
- Health response detail (from OIS `/health` endpoint — live refresh every 30s)
- Connection details: endpoint URL, OIS version declared
- Registration token status (active / expiry date)

### 2.2 Configuration

- Provider capability declaration YAML viewer (read-only; changes require re-registration or update submission)
- Editable fields: display name, description, owner contact, notification preferences
- Profile compatibility indicator: which DCM profiles this provider is certified to operate under

### 2.3 Health History

- 30-day health check history: pass / warn / fail timeline
- Degraded periods highlighted; duration of each incident
- Correlation with entity realization failures during degraded periods

### 2.4 Audit Trail

- All admin actions on this provider: approval, suspension, config changes, capacity updates
- Actor who performed each action, timestamp, comment
- Filterable by action type

### 2.5 Notifications

- Notification endpoint configuration for this provider
- Which DCM events this provider subscribes to (webhook subscriptions for provider.* events)
- Test webhook delivery

---

## 3. Service Provider — Extended Tabs

Service Providers (the most common type — realize infrastructure resources) have the richest management surface.

### 3.1 Capacity Management

**API:** `POST /api/v1/providers/{uuid}/capacity`

- Current capacity report: available units per resource type per location
- Historical capacity charts: capacity utilization over time
- **Manual capacity update form**: override reported capacity for emergency situations
- Capacity denial history: requests denied due to insufficient capacity
- Alert configuration: notify when capacity below threshold

### 3.2 Managed Entities

- All DCM entities realized by this provider: type, tenant, state, TTL, drift status
- Filterable by tenant (for Platform Admin), resource type, state
- Entity count by state (pie chart)
- Entities with open drift records: grouped by drift severity
- Entities approaching TTL expiry in next P7D
- Click-through to entity detail (read-only view for provider owner; editable for Platform Admin)

### 3.3 Naturalization Mapping

- Resource type → provider-native mapping declarations
- View the Naturalization configuration for each supported resource type
- Denaturalization mapping: what provider-native fields map back to DCM fields
- **Test naturalization**: submit a DCM payload and see the naturalized version without dispatching

### 3.4 Interim Status Configuration

- Enable / disable interim status reporting per resource type
- Reporting frequency configuration (minimum interval, max steps)
- View recent interim status payloads for debugging

### 3.5 Realization History

- Recent realization requests: accepted / failed / in-progress
- Mean realization time by resource type (last 30 days)
- Failure analysis: top failure reasons with counts
- In-flight realizations with live status

---

## 4. credential management service — Extended Tabs

### 4.1 Credential Inventory

- All credentials managed by this provider: type, entity scope, issued date, expiry, last retrieved
- Never shows credential values — only metadata
- Filter by credential type (api_key, x509_certificate, ssh_key, etc.)
- Credentials approaching expiry: highlighted red within renewal trigger window

### 4.2 Rotation Management

- Credentials currently in rotation (transition window open): old UUID → new UUID pairs
- Manual rotation trigger for specific credentials
- Rotation history with trigger reason

### 4.3 Revocation Registry

- Summary: total revoked, still-in-TTL (in registry), post-TTL (pruned from registry)
- Search by credential UUID to check revocation status
- Emergency revocation form: revoke by credential UUID or entity UUID with required reason

### 4.4 External CA Configuration (if ca_type: external)

- CA protocol in use (ACME / EST / SCEP / CMP / Vault PKI / etc.)
- CA endpoint connectivity status
- Certificate chain view: root CA → intermediate → issued certs
- Pending certificate requests
- CRL / OCSP endpoint status

### 4.5 Algorithm Compliance View

- Algorithms in use across managed credentials
- Forbidden algorithm violations (should be zero — highlighted red if any found)
- Algorithm distribution chart: ECDSA P-384 vs P-256 vs RSA vs other
- Upcoming algorithm deprecations from doc 40 forbidden list

---

## 5. Auth Provider — Extended Tabs

### 5.1 Connection Status

- Auth Provider endpoint connectivity: pass / warn / fail
- Failover chain: current primary, configured fallbacks, activation status
- Token validation latency (p50, p99) — last 1 hour

### 5.2 Actor and Group Sync

- SCIM sync status (if SCIM 2.0 enabled): last sync timestamp, records synced, errors
- Group → DCM role mapping table (read-only; changes via configuration update)
- Actor provisioning audit: recent SCIM-triggered creates, updates, deactivations

### 5.3 Session Statistics

- Active session count from this Auth Provider
- Session distribution by auth method (OIDC / LDAP / API key / mTLS)
- MFA verification rates: mfa_verified: true vs false breakdown
- Step-up MFA events in last 24h

### 5.4 Configuration

- Auth Provider YAML viewer
- Editable: display name, session TTL, concurrent session limit, role mapping (changes go through standard artifact lifecycle — proposed → reviewed → active)
- Shadow mode toggle for configuration changes

---

## 6. External Policy Evaluator — Extended Tabs

### 6.1 Policy Inventory

- Policies managed by this provider: handle, type, enforcement class, status (active / shadow / deprecated)
- Policy evaluation counts and outcomes (last 24h)
- Shadow divergence alerts: policies with >5% divergence rate from expected

### 6.2 Trust Level Management

- Current trust level: local / community / verified / authoritative
- Trust elevation request form (requires Platform Admin approval)
- Trust history

### 6.3 Policy Contribution Pipeline

- Policies submitted for contribution to the DCM Policy Registry
- Lifecycle status: shadow validation period, community review, approval
- Withdraw pending contributions

---

## 7. Information Provider — Extended Tabs

### 7.1 Data Source Status

- Connection status to upstream data source
- Last successful sync and record count
- Data freshness indicator (stale threshold from provider registration)

### 7.2 Confidence Score Management

- Declared confidence scores per data field
- Confidence override history (when DCM overrode provider confidence based on corroboration)

### 7.3 Query Performance

- Response time distribution for DCM queries to this provider
- Cache hit rate (if DCM caches this provider's data)
- Top queried fields

---

## 8. data store — Extended Tabs

### 8.1 Store Health

- Store-specific health: write latency, read latency, replication lag (if replicated), disk utilization
- Consistency guarantee compliance: declared vs observed consistency level

### 8.2 Capacity and Retention

- Storage utilization by store type (Intent, Requested, Realized, Audit)
- Retention policy status: records approaching retention deadline
- Partition / shard status (for GitOps stores using partitioning strategies from doc 41)

---

## 9. Notification and event routing services — Extended Tabs

### 9.1 notification service

- Delivery channel status: email, Slack, PagerDuty, etc.
- Delivery success rate (last 24h)
- Failed deliveries with retry status
- Audience routing test: send a test notification to a specific audience

### 9.2 event routing service

- Broker connectivity status
- Topic / stream inventory: DCM topics and consumer group lag
- Message throughput (messages/minute by topic)
- Dead letter queue: messages that failed delivery after retry

---

## 10. composite service definition — Extended Tabs

### 10.1 Composite Service Status

- Active composite service instances: all constituent statuses
- Constituents in PENDING_DEPENDENCY state across all active instances
- Failed compensation attempts (COMPENSATION_FAILED state)

### 10.2 Constituent Provider Health

- Health of each provider this composite service definition depends on
- Impact analysis: if Provider X degrades, which composite services are affected

---

## 11. Resource Type Registry and Peer DCM — Extended Tabs

### 11.1 Resource Type Registry

- Resource type registry sync status: last sync, version, record count
- Type registration submissions pending review
- Registry health: response time, availability

### 11.2 Peer DCM (Federation)

- Federation tunnel status: connected / degraded / disconnected
- Peer DCM version and deployment profile
- Cross-instance request routing: requests forwarded to / from this peer (last 24h)
- Sovereignty boundary status: which data classifications are permitted across this tunnel

---

## 12. Provider-Scoped Security

### 12.1 Provider Interaction Credentials

- Interaction credentials issued to this provider: count, last issued, rotation status
- Emergency credential revocation capability
- Audit of all credential retrievals by this provider (CPX-005: first retrieval always audited)

### 12.2 mTLS Certificate Status

- Provider's mTLS certificate: issuer, expiry, OCSP status
- Certificate renewal tracking (for external CA managed certs)

### 12.3 Provider Audit Trail Contribution

- Provenance records emitted by this provider: count, last emitted
- Audit forwarding status: is the provider successfully forwarding audit events?

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
