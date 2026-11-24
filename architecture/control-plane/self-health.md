---
Document Status: ✅ Complete
Document Type: Architecture Reference — Operational Health
Maps to: udlm/contracts/provider-contract.md
---

# DCM Data Model — DCM Self-Health Endpoints

> **Implements contracts defined in UDLM**:
> [udlm/contracts/provider-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-contract.md).
> UDLM defines the provider health contract that Service Providers must expose.
> DCM operationalizes its own liveness, readiness, and component-health
> endpoints — DCM exposes the same health contract it requires of the providers
> it integrates, so it is itself a well-behaved provider to its operator and
> load-balancer.

**Document Status:** ✅ Complete
**Document Type:** Architecture Reference — Operational Health
**Related Documents:** [Deployment and Redundancy](../runtime-features/deployment-redundancy.md) | [Internal Component Authentication](internal-component-auth.md) | [Operator Interface Specification](../../docs/specifications/dcm-operator-interface-spec.md) | [Admin API Specification](../../docs/specifications/dcm-admin-api-spec.md)

> **Events:** Health state change events fire as `provider.healthy` / `provider.unhealthy` for external systems, and `governance.profile_changed` when health thresholds are adjusted. See [Event Catalog](https://github.com/croadfeldt/udlm/blob/main/contracts/event-catalog.md).

> **This document maps to: PROVIDER**
>
> DCM itself must expose the same health contract it requires of Service Providers (doc OIS §4). This document specifies DCM's own liveness, readiness, and component health endpoints — required for Kubernetes operator deployment, load balancer health checking, and operational monitoring.

---

## 1. Three Health Endpoints

DCM exposes three distinct health endpoints, following Kubernetes conventions:

| Endpoint | Purpose | Failure action | Authentication |
|----------|---------|---------------|---------------|
| `GET /livez` | Is DCM alive? | Kubernetes restarts the pod | None |
| `GET /readyz` | Is DCM ready to serve traffic? | Kubernetes removes from load balancer | None |
| `GET /api/v1/admin/health` | Detailed component status | Informational — no automatic action | Admin auth required |

Liveness and readiness are unauthenticated because they must work before authentication infrastructure is operational (e.g. during startup).

---

## 2. Liveness — `/livez`

Liveness answers: **is this DCM process alive?**

A liveness failure means the process is deadlocked, in an unrecoverable state, or otherwise unable to continue. Kubernetes responds by restarting the pod.

```http
GET /livez HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/health+json

{
  "status": "pass"
}
```

**Liveness checks (minimal — fast):**
- Process is responding
- No deadlock detected in core event loop
- Internal CA is reachable (for deployments with component auth)

**Liveness failure response:**
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/health+json

{
  "status": "fail",
  "failure_reason": "event_loop_deadlock | internal_ca_unreachable | oom_imminent"
}
```

**Liveness SLA:** Must respond within PT5S. No external calls. No database reads.

---

## 3. Readiness — `/readyz`

Readiness answers: **is this DCM instance ready to serve requests?**

A readiness failure removes the instance from the load balancer rotation without restarting it. This handles startup, migration, and graceful drain scenarios.

```http
GET /readyz HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/health+json

{
  "status": "pass",
  "checks": {
    "session_store": "pass",
    "audit_store": "pass",
    "policy_engine": "pass",
    "message_bus": "pass",
    "auth_provider": "pass"
  }
}
```

**Readiness checks:**
- Session Store: can write and read a test record
- Audit Store: reachable and writable
- Policy Engine: responding to internal health ping
- Message Bus: connected and subscribed
- Auth Provider: at least one Auth Provider is responding
- Schema version: database schema matches running code version

**Readiness failure** (any check fails):
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/health+json

{
  "status": "fail",
  "checks": {
    "session_store": "pass",
    "audit_store": "fail",
    "policy_engine": "pass",
    "message_bus": "pass",
    "auth_provider": "pass"
  },
  "failing_checks": ["audit_store"]
}
```

**Readiness SLA:** Must respond within PT10S. Performs lightweight connectivity checks — no heavy queries.

### 3.1 Startup vs Operational Readiness

During startup, DCM goes through a startup sequence before becoming ready:

```
Process starts
  │
  ▼ /livez → pass (process alive)
  │   /readyz → fail (not ready yet)
  │
  ▼ Internal CA connects → component certs verified
  ▼ Session Store connected → revocation registry loaded
  ▼ Audit Store connected → schema version validated
  ▼ Policy Engine ready → policies loaded and shadow mode initialized
  ▼ Auth Providers connected → at least one responding
  ▼ Message Bus connected → subscriptions established
  │
  ▼ /readyz → pass (ready to serve traffic)
```

`startupProbe` in Kubernetes uses `/readyz` with a longer `failureThreshold` to allow startup time before the liveness probe takes over.

---

## 4. Detailed Health — `/api/v1/admin/health`

The detailed health endpoint provides per-component status for operational monitoring. Requires admin authentication.

```http
GET /api/v1/admin/health HTTP/1.1
Authorization: Bearer <admin-token>

HTTP/1.1 200 OK
Content-Type: application/health+json

{
  "status": "pass | warn | fail",
  "dcm_version": "1.2.0",
  "dcm_instance_uuid": "<uuid>",
  "deployment_profile": "prod",
  "uptime_seconds": 864023,
  "checked_at": "<ISO 8601>",

  "components": {
    "api_gateway": {
      "status": "pass",
      "latency_p99_ms": 12,
      "requests_per_minute": 340
    },
    "request_orchestrator": {
      "status": "pass",
      "queue_depth": 3,
      "in_flight": 7
    },
    "policy_engine": {
      "status": "pass",
      "active_policies": 42,
      "shadow_policies": 3,
      "evaluations_per_minute": 280
    },
    "placement_engine": {
      "status": "pass"
    },
    "scoring_engine": {
      "status": "pass",
      "evaluations_per_minute": 280
    },
    "request_scheduler": {
      "status": "pass",
      "scheduled_requests_queued": 5,
      "next_dispatch_at": "<ISO 8601>"
    },
    "drift_reconciler": {
      "status": "pass",
      "last_cycle_completed_at": "<ISO 8601>",
      "open_drift_records": 2
    },
    "lifecycle_enforcer": {
      "status": "pass",
      "entities_monitored": 1240,
      "ttl_warnings_pending": 3
    },
    "discovery_scheduler": {
      "status": "pass",
      "pending_jobs": 1,
      "last_completed_at": "<ISO 8601>"
    },
    "notification_router": {
      "status": "pass",
      "providers_active": 2,
      "delivery_backlog": 0
    },
    "session_store": {
      "status": "pass",
      "active_sessions": 47,
      "revocation_registry_size": 3
    },
    "audit_store": {
      "status": "pass",
      "records_last_hour": 1840,
      "integrity": "verified"          # Merkle inclusion/consistency
    },
    "message_bus": {
      "status": "pass",
      "lag_consumer_group_ms": 12
    },
    "internal_ca": {
      "status": "pass",
      "certificates_active": 12,
      "next_expiry_at": "<ISO 8601>"
    }
  },

  "providers": {
    "registered": 4,
    "healthy": 4,
    "degraded": 0,
    "unhealthy": 0
  },

  "auth_providers": {
    "registered": 2,
    "healthy": 2,
    "unhealthy": 0
  }
}
```

### 4.1 Status Semantics

| Status | Meaning |
|--------|---------|
| `pass` | Component fully operational |
| `warn` | Operational but degraded (high latency, reduced capacity, elevated error rate) |
| `fail` | Component not operational; DCM degraded |

The top-level `status` is the worst status across all components:
- Any `fail` → top-level `fail`
- Any `warn`, no `fail` → top-level `warn`
- All `pass` → top-level `pass`

---

## 5. Kubernetes Manifest

```yaml
# Standard Kubernetes probe configuration for DCM
livenessProbe:
  httpGet:
    path: /livez
    port: 8443
    scheme: HTTPS
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 3
  timeoutSeconds: 5

readinessProbe:
  httpGet:
    path: /readyz
    port: 8443
    scheme: HTTPS
  initialDelaySeconds: 30
  periodSeconds: 5
  failureThreshold: 6
  timeoutSeconds: 10

startupProbe:
  httpGet:
    path: /readyz
    port: 8443
    scheme: HTTPS
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 30    # allow up to 300s for startup
  timeoutSeconds: 10
```

---

## 6. Prometheus Metrics

DCM exposes Prometheus-compatible metrics alongside health endpoints:

```
GET /metrics      # Prometheus scrape endpoint (unauthenticated in cluster; 
                  # configurable for external exposure)
```

Key metric families:

```
# Request pipeline
dcm_requests_total{status, resource_type, profile}
dcm_request_duration_seconds{quantile, resource_type}
dcm_requests_pending_dependency_total
dcm_requests_scheduled_total

# Policy engine
dcm_policy_evaluations_total{outcome, enforcement_class}
dcm_policy_shadow_divergences_total

# Sessions
dcm_sessions_active_total
dcm_session_revocations_total{trigger}

# Drift
dcm_drift_open_records_total{severity}
dcm_drift_detected_total

# Providers
dcm_providers_registered_total
dcm_providers_healthy_total
dcm_provider_dispatch_duration_seconds{provider_type, quantile}

# Internal
dcm_internal_ca_certificates_active
dcm_internal_ca_days_until_next_expiry
```

---

## 7. Per-Provider Metrics Contract

In addition to DCM control plane metrics, each registered Service Provider must
expose a Prometheus-compatible `/metrics` endpoint meeting the contract defined in
the Registration Specification (GATE-SP-05).

### 7.1 Required Provider Metric Families

```
# Dispatch metrics — how many requests DCM sent to this provider
dcm_provider_dispatches_total{resource_type="Compute.VirtualMachine", outcome="success|failed|timeout"}
dcm_provider_dispatch_duration_seconds{resource_type="Compute.VirtualMachine", quantile="0.5|0.95|0.99"}

# Realization metrics — outcomes of provisioning
dcm_provider_realizations_total{resource_type="Compute.VirtualMachine", status="OPERATIONAL|FAILED"}

# Health signal
dcm_provider_health_status  # gauge: 1=healthy, 0.5=degraded, 0=unhealthy
```

### 7.2 Recommended Provider Metric Families

```
# Capacity
dcm_provider_capacity_remaining{resource_type="Compute.VirtualMachine"}  # gauge
dcm_provider_capacity_total{resource_type="Compute.VirtualMachine"}      # gauge

# Queue depth (for async-only providers)
dcm_provider_queue_depth{resource_type="Compute.VirtualMachine"}  # gauge

# Tenant usage
dcm_provider_active_resources_total{tenant_uuid="...", resource_type="..."}
```

### 7.3 DCM Control Plane Aggregated Provider Metrics

The DCM control plane exposes aggregated provider metrics at its own `/metrics`
endpoint alongside the control plane metrics from Section 6:

```
# Already in Section 6 — shown here for cross-reference
dcm_providers_registered_total               # count of registered providers
dcm_providers_healthy_total                  # count currently healthy
dcm_provider_dispatch_duration_seconds{...}  # aggregated across all providers
```

### 7.4 Tenant Metadata Endpoint

Service Providers in `standard` and above profiles (GATE-SP-04) must implement
a tenant metadata endpoint that DCM calls to retrieve per-tenant usage summaries:

```
GET /api/v1/tenants/{tenant_uuid}/metadata
Authorization: Bearer <provider_callback_credential>

Response 200:
{
  "tenant_uuid": "<uuid>",
  "active_resources": {
    "Compute.VirtualMachine": 12,
    "Storage.Block": 8
  },
  "capacity_consumed": {
    "Compute.VirtualMachine": {
      "cpu_cores": 96,
      "ram_gb": 384
    }
  },
  "quota_consumed_pct": {
    "Compute.VirtualMachine": 48.0
  }
}
```

This data is used by DCM's Cost Analysis component and multi-tenant quota
enforcement. It is also exposed to tenant administrators via the consumer API.

---

## 8. Profile-Governed Health Exposure

| Profile | /livez | /readyz | /api/v1/admin/health | /metrics scraping |
|---------|--------|---------|----------------------|-------------------|
| `homelab` | Unauthenticated | Unauthenticated | Admin auth | Internal network only |
| `dev` | Unauthenticated | Unauthenticated | Admin auth | Internal network only |
| `standard` | Unauthenticated | Unauthenticated | Admin auth | mTLS client cert or auth token |
| `prod` | Unauthenticated | Unauthenticated | Admin auth | mTLS client cert or auth token |
| `fsi` | Unauthenticated | Unauthenticated | Admin auth (MFA required) | mTLS + authorized scraper registration |
| `sovereign` | Unauthenticated within cluster | Unauthenticated within cluster | Admin auth (MFA + step-up) | Disabled externally; internal only |

**Notes:**
- `/livez` and `/readyz` are always unauthenticated *within the cluster* — Kubernetes probes cannot present auth credentials. However, at the ingress boundary (external load balancer), these paths may be network-restricted.
- For `fsi` and `sovereign` profiles, `/api/v1/admin/health` requires MFA-verified sessions (mfa_verified: true). Step-up MFA is required for sovereign.
- The `sovereign` profile does not expose `/metrics` externally. Prometheus must scrape from within the cluster network only.
- Component-level detail in `/api/v1/admin/health` may be redacted in fsi/sovereign profiles based on the requesting actor's role — SRE sees full detail; read-only admin sees summary only.

## 7. System Policies

| Policy | Rule |
|--------|------|
| `HLT-001` | DCM must expose `/livez` and `/readyz` endpoints on the same port as the API, unauthenticated, following RFC 8615 / IANA health+json format. |
| `HLT-002` | `/livez` must respond within PT5S with no external calls or database reads. A non-response within PT5S is treated as liveness failure. |
| `HLT-003` | `/readyz` returns `fail` if the Session Store, Audit Store, Policy Engine, Message Bus, or any Auth Provider is unreachable. It returns `warn` if any optional component is degraded. |
| `HLT-004` | `GET /api/v1/admin/health` requires admin authentication and provides per-component status. It must include the DCM version, instance UUID, and deployment profile. |
| `HLT-005` | DCM must expose Prometheus-compatible metrics at `GET /metrics`. Metrics must include request pipeline, policy engine, session, drift, and provider metrics at minimum. |
| `HLT-006` | The startup sequence must be observable via `/readyz`. DCM must not report `pass` on `/readyz` until the Session Store, Audit Store, Policy Engine, Auth Provider, and Message Bus are all reachable. |

---

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
