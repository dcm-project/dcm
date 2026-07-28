# DCM Operator SDK — API Design

**Document Status:** ✅ Complete
**Document Type:** SDK Reference (Go)
**Related Documents:** [Operator Interface Specification](dcm-operator-interface-spec.md) | [Kubernetes Compatibility](kubernetes-compatibility.md) | [Provider Callback Auth](https://github.com/croadfeldt/udlm/blob/main/contracts/provider-callback-auth.md) | [Registration Specification](dcm-registration-spec.md)

> **AEP Alignment:** DCM interaction uses colon-syntax custom methods (`:approve`, `:suspend`).
> `operation_uuid == request_uuid` — Operations polling uses `GET /api/v1/operations/{uuid}`.
> `resource_type` accepts both FQN string (`Compute.VirtualMachine`) and Registry UUID;
> DCM resolves either form internally. See `schemas/openapi/dcm-operator-api.yaml`
> for the normative operator-facing OpenAPI specification.



> ## 📋 Draft — Promoted from Work in Progress
>
> All questions resolved. Local durable queue, mock test harness, Prometheus metrics, and dynamic field resolution all specified.
>
> **This section is explicitly a work in progress and is less mature than the core DCM data model and architecture documentation.**
>
> The Kubernetes operator integration layer — including the Operator Interface Specification, Operator SDK API, and Kubernetes compatibility mappings — represents design intent that has not yet been validated against implementation. Specific interface contracts, API signatures, SDK method names, and CRD structures **will change** as implementation work begins.
>
> **Do not build against these specifications yet.** They are published to share design direction and invite feedback, not as stable contracts.
>
> Known gaps and open items for this section:
> - Operator Interface Specification: reconciliation hook signatures are provisional
> - Operator SDK API: Go module structure and dependency model not yet finalized
> - Kubernetes Compatibility Mappings: some concept mappings remain under discussion
> - SDK code examples are illustrative only — not yet tested against a real implementation
>
> Feedback and contributions welcome via [GitHub Issues](https://github.com/dcm-project/issues).



**Version:** 0.1.0-draft  
**Status:** Draft — Ready for implementation feedback
**Document Type:** Technical Design  
**Language:** Go  
**Repository:** https://github.com/dcm-project/operator-sdk  
**Related Documents:** [Foundational Abstractions](https://github.com/croadfeldt/udlm/blob/main/foundations/foundations.md) | [DCM Operator Interface Specification](dcm-operator-interface-spec.md) | [Kubernetes Compatibility](kubernetes-compatibility.md)

---

## 1. Purpose

This document defines the public API of the DCM Operator SDK — the Go library that enables Kubernetes operators to implement the DCM Operator Interface Specification with minimal code changes. The SDK handles all DCM protocol concerns so that operator developers only need to implement business logic — field mappings and reconciliation hooks.

**Design principle:** The SDK must be adoptable in a single day. If implementing Level 1 takes more than a day, the API is too complex.

---

## 2. Package Structure

```
github.com/dcm-project/operator-sdk/
├── pkg/
│   ├── client/          # DCM control plane client
│   ├── config/          # SDK configuration
│   ├── mapping/         # Field mapping engine
│   ├── reconciler/      # Reconciliation loop helpers
│   ├── registration/    # Provider registration
│   ├── server/          # HTTP server with DCM endpoints
│   ├── status/          # Status translation and reporting
│   ├── events/          # Lifecycle event types and emission
│   ├── discovery/       # Brownfield discovery helpers (Level 3)
│   └── provenance/      # Provenance metadata generation (Level 3)
├── api/
│   └── v1/              # DCM API type definitions
└── examples/
    ├── level1/          # Minimal Level 1 implementation example
    ├── level2/          # Full Level 2 implementation example
    └── level3/          # Complete Level 3 implementation example
```

---

## 3. Core Types

### 3.1 Config

```go
// Config is the primary SDK configuration structure.
// All fields have sensible defaults — only DCMEndpoint,
// OperatorEndpoint, and ProviderName are required.
type Config struct {
    // Required
    ProviderName     string
    DCMEndpoint      string
    OperatorEndpoint string

    // Required — at least one ServiceType must be declared
    ServiceTypes []ServiceTypeConfig

    // Optional — defaults to Level1 if not specified
    ConformanceLevel ConformanceLevel

    // Optional — defaults to "unknown" if not specified
    DisplayName string
    Version     string

    // Optional — field mappings loaded from file if not inline
    FieldMappings []FieldMapping
    FieldMappingFiles []string

    // Level 2+ — capacity reporter
    // If nil and ConformanceLevel >= Level2, SDK returns error on init
    CapacityReporter CapacityReporter

    // Level 3 — sovereignty and provenance
    SovereigntyCapabilities *SovereigntyCapabilities

    // Optional — HTTP server configuration
    ServerConfig ServerConfig

    // Optional — registration retry configuration
    RegistrationConfig RegistrationConfig

    // Optional — health check configuration
    HealthConfig HealthConfig

    // Optional — logger (defaults to zap logger)
    Logger logr.Logger
}

// ConformanceLevel declares the operator's DCM conformance level
type ConformanceLevel int

const (
    Level1 ConformanceLevel = 1
    Level2 ConformanceLevel = 2
    Level3 ConformanceLevel = 3
)

// ServiceTypeConfig declares a DCM Resource Type this operator implements
type ServiceTypeConfig struct {
    // DCM Resource Type name — e.g., "Storage.Database"
    ServiceTypeName string
    // DCM Resource Type UUID from the registry
    ServiceTypeUUID string
    // Kubernetes CRD this service type maps to
    CRDReference CRDReference
    // Operations this operator supports for this type
    OperationsSupported []Operation
}

type CRDReference struct {
    Group   string
    Version string
    Kind    string
}

type Operation string

const (
    OperationCreate   Operation = "CREATE"
    OperationRead     Operation = "READ"
    OperationUpdate   Operation = "UPDATE"
    OperationDelete   Operation = "DELETE"
    OperationDiscover Operation = "DISCOVER" // Level 3 only
)
```

### 3.2 Client — DCM Control Plane Interface

```go
// Client is the interface for communicating with the DCM control plane.
// The SDK creates and manages this internally — operator developers
// use it only through the higher-level SDK methods.
type Client interface {
    // Register sends the provider registration to DCM.
    // Returns the DCM-assigned provider UUID on success.
    Register(ctx context.Context, reg ProviderRegistration) (string, error)

    // ReportStatus sends a realized state payload to DCM.
    ReportStatus(ctx context.Context, resourceID string, status RealizedState) error

    // ReportEvent sends a lifecycle event to DCM.
    ReportEvent(ctx context.Context, resourceID string, event LifecycleEvent) error

    // ReportCapacity sends a capacity update to DCM.
    // Required for Level 2+.
    ReportCapacity(ctx context.Context, capacity CapacityReport) error

    // ConfirmDecommission acknowledges a decommission request from DCM.
    // Required for Level 3.
    ConfirmDecommission(ctx context.Context, resourceID string, confirmation DecommissionConfirmation) error
}
```

### 3.3 SDK — Primary Interface

```go
// SDK is the primary interface for the DCM Operator SDK.
// Operator developers interact with DCM through this interface.
type SDK interface {
    // --- Lifecycle ---

    // Register sends the provider registration to DCM.
    // Called during operator startup. Retries with exponential backoff.
    // Does not block — runs in background goroutine.
    Register(ctx context.Context)

    // Shutdown gracefully deregisters the operator from DCM and
    // stops background goroutines.
    Shutdown(ctx context.Context) error

    // --- HTTP Server ---

    // StartServer starts the HTTP server with all DCM-required endpoints.
    // Blocks until context is cancelled.
    StartServer(ctx context.Context, addr string) error

    // Handler returns an http.Handler for use with an existing HTTP server.
    // Alternative to StartServer when the operator already has an HTTP server.
    Handler() http.Handler

    // --- Reconciliation Helpers ---

    // IsManagedResource returns true if the Kubernetes object
    // carries DCM management labels.
    IsManagedResource(obj client.Object) bool

    // IsUnsanctionedChange returns true if the object's spec has changed
    // without a corresponding DCM request annotation.
    // Used in reconciliation loops to detect drift.
    IsUnsanctionedChange(obj client.Object) bool

    // DetectChangedFields returns the list of fields that changed
    // relative to the last known DCM request state.
    DetectChangedFields(obj client.Object) []FieldChange

    // InjectLabels adds DCM-required labels to a Kubernetes object
    // before creation. Called before submitting a CR to Kubernetes.
    InjectLabels(obj client.Object, req CreateRequest) client.Object

    // AnnotateRequest adds the DCM request ID annotation to a
    // Kubernetes object. Used to mark changes as DCM-sanctioned.
    AnnotateRequest(obj client.Object, requestID string) client.Object

    // --- Status Translation ---

    // TranslateStatus translates a Kubernetes object's status
    // to a DCM RealizedState using the configured field mappings.
    TranslateStatus(obj client.Object) (RealizedState, error)

    // ReportStatus translates and reports status to DCM in one call.
    // Convenience wrapper for TranslateStatus + Client.ReportStatus.
    ReportStatus(ctx context.Context, obj client.Object) error

    // --- Event Emission ---

    // ReportEvent sends a lifecycle event to DCM.
    ReportEvent(ctx context.Context, obj client.Object, event LifecycleEventType, details EventDetails) error

    // ReportUnsanctionedChange is a convenience method for reporting
    // an unsanctioned change event with the detected changed fields.
    ReportUnsanctionedChange(ctx context.Context, obj client.Object, changes []FieldChange) error

    // ReportDegradation reports a DEGRADATION event to DCM.
    ReportDegradation(ctx context.Context, obj client.Object, reason string) error

    // ReportHealthChange reports an ENTITY_HEALTH_CHANGE event.
    ReportHealthChange(ctx context.Context, obj client.Object, healthy bool, reason string) error

    // --- Capacity ---

    // StartCapacityReporting starts the background capacity reporting
    // goroutine. Required for Level 2+. Called automatically by StartServer.
    StartCapacityReporting(ctx context.Context)

    // --- Discovery (Level 3) ---

    // BuildDiscoveryResponse queries Kubernetes for existing resources
    // and returns them in DCM Realized State format.
    // Used to implement the POST /discover endpoint.
    BuildDiscoveryResponse(ctx context.Context, k8sClient client.Client, opts DiscoveryOptions) ([]RealizedState, error)
}
```

---

## 4. Field Mapping API

```go
// FieldMapping declares how a DCM Resource Type maps to a Kubernetes CRD.
// Can be loaded from a YAML file or declared inline in Go.
type FieldMapping struct {
    ServiceTypeName string
    ServiceTypeUUID string
    CRDReference    CRDReference

    // DCM Requested State → Kubernetes CR spec (Naturalization)
    DCMToCR []FieldMap

    // Kubernetes CR status → DCM Realized State (Denaturalization)
    CRStatusToDCM []FieldMap

    // Kubernetes conditions → DCM lifecycle states
    ConditionMappings []ConditionMapping

    // Kubernetes events → DCM lifecycle event types
    LifecycleEventMappings []LifecycleEventMapping

    // Namespace strategy for this resource type
    NamespaceStrategy NamespaceStrategy
}

// FieldMap declares a single field translation
type FieldMap struct {
    // Source field path — dot-notation, supports array indexing
    // e.g., "resources.cpu" or "nodes.controlPlane[0].cpu"
    SourcePath string

    // Destination field path
    DestPath string

    // Transform function name — registered in the transform registry
    // "none" for direct copy, or a named transform
    Transform string

    // Required — if true and source field is absent, returns error
    Required bool

    // Default — used when source field is absent and Required is false
    Default interface{}
}

// ConditionMapping maps a Kubernetes condition to a DCM lifecycle state
type ConditionMapping struct {
    // Kubernetes condition expression — e.g., "Ready=True"
    // Supports AND: "Ready=False,Progressing=True"
    KubernetesCondition string

    // DCM lifecycle state
    DCMLifecycleState LifecycleState
}

// LifecycleEventMapping maps a Kubernetes event to a DCM event type
type LifecycleEventMapping struct {
    // "condition_change" | "spec_change_without_dcm_request" | "deletion"
    KubernetesEvent string

    // Condition that triggers this mapping (for condition_change events)
    Condition string

    // DCM event type
    DCMEventType LifecycleEventType

    // Severity
    Severity EventSeverity
}

// Transform registry — operator developers register custom transforms
type TransformRegistry interface {
    // Register adds a named transform function
    Register(name string, fn TransformFunc) error

    // Get retrieves a transform function by name
    Get(name string) (TransformFunc, error)
}

// TransformFunc transforms a value from source to destination format
type TransformFunc func(value interface{}) (interface{}, error)
```

---

## 5. Status and State Types

```go
// LifecycleState represents the DCM lifecycle state of a resource
type LifecycleState string

const (
    LifecycleStateProvisioning   LifecycleState = "PROVISIONING"
    LifecycleStateOperational    LifecycleState = "OPERATIONAL"
    LifecycleStateDegraded       LifecycleState = "DEGRADED"
    LifecycleStateSuspended      LifecycleState = "SUSPENDED"
    LifecycleStateFailed         LifecycleState = "FAILED"
    LifecycleStateDecommissioned LifecycleState = "DECOMMISSIONED"
)

// RealizedState is the DCM Unified Data Model representation of
// a resource's realized state. This is what the operator sends
// to DCM after successful provisioning or status change.
type RealizedState struct {
    // DCM resource ID (returned by DCM in the create request)
    ResourceID string

    // DCM entity UUID
    DCMEntityUUID string

    // Current lifecycle state
    LifecycleState LifecycleState

    // Timestamp of this realization
    RealizedTimestamp time.Time

    // All realized fields in DCM Unified Data Model format
    Spec map[string]interface{}

    // Level 3 — field-level provenance
    FieldProvenance map[string]FieldProvenance

    // Kubernetes reference for correlation
    KubernetesReference KubernetesReference

    // Relationships created during realization
    Relationships []RelationshipRecord
}

// KubernetesReference carries Kubernetes-specific identity for correlation
type KubernetesReference struct {
    Namespace       string
    Name            string
    UID             types.UID
    ResourceVersion string
    Generation      int64
}

// FieldProvenance carries lineage for a single field (Level 3)
type FieldProvenance struct {
    SourceType    string    // "provider"
    SourceUUID    string    // operator provider UUID
    Timestamp     time.Time
    Reason        string
}
```

---

## 6. Event Types

```go
// LifecycleEventType represents a DCM lifecycle event type
type LifecycleEventType string

const (
    EventEntityHealthChange     LifecycleEventType = "ENTITY_HEALTH_CHANGE"
    EventDegradation            LifecycleEventType = "DEGRADATION"
    EventMaintenanceScheduled   LifecycleEventType = "MAINTENANCE_SCHEDULED"
    EventMaintenanceStarted     LifecycleEventType = "MAINTENANCE_STARTED"
    EventMaintenanceCompleted   LifecycleEventType = "MAINTENANCE_COMPLETED"
    EventUnsanctionedChange     LifecycleEventType = "UNSANCTIONED_CHANGE"
    EventCapacityChange         LifecycleEventType = "CAPACITY_CHANGE"
    EventDecommissionNotice     LifecycleEventType = "DECOMMISSION_NOTICE"
    EventProviderDegradation    LifecycleEventType = "PROVIDER_DEGRADATION"
)

// EventSeverity represents the severity of a lifecycle event
type EventSeverity string

const (
    SeverityInfo     EventSeverity = "INFO"
    SeverityWarning  EventSeverity = "WARNING"
    SeverityCritical EventSeverity = "CRITICAL"
)

// LifecycleEvent is the payload sent to DCM for a lifecycle event
type LifecycleEvent struct {
    EventUUID             string
    EventType             LifecycleEventType
    ProviderID            string
    ResourceID            string
    DCMEntityUUID         string
    EventTimestamp        time.Time
    Severity              EventSeverity
    RequiresImmediateAction bool
    Details               EventDetails
    KubernetesReference   KubernetesReference
}

// EventDetails carries event-specific detail data
type EventDetails struct {
    // For UNSANCTIONED_CHANGE events
    ChangedFields []FieldChange

    // For DEGRADATION events
    DegradationReason string
    AffectedComponents []string

    // For MAINTENANCE events
    MaintenanceWindow  *MaintenanceWindow
    MaintenanceReason  string

    // For CAPACITY_CHANGE events
    PreviousCapacity   *CapacityReport
    CurrentCapacity    *CapacityReport

    // Human-readable message for any event type
    Message string
}

// FieldChange describes a single field change in an unsanctioned change event
type FieldChange struct {
    FieldPath     string
    PreviousValue interface{}
    CurrentValue  interface{}
    ChangedBy     string    // Kubernetes user or service account
    ChangedAt     time.Time
}
```

---

## 7. Capacity Types

```go
// CapacityReporter is the interface operator developers implement
// to report capacity data to DCM. The SDK calls this on schedule.
type CapacityReporter interface {
    // GetCapacity returns the current capacity for all service types.
    // Called by the SDK on the configured reporting schedule.
    GetCapacity(ctx context.Context) (CapacityReport, error)
}

// CapacityReport contains capacity data for all service types
type CapacityReport struct {
    ProviderID          string
    ReportTimestamp     time.Time
    NextReportAt        time.Time
    CapacityByServiceType []ServiceTypeCapacity
}

// ServiceTypeCapacity contains capacity for a single service type
type ServiceTypeCapacity struct {
    ServiceTypeUUID  string
    AvailableUnits   int
    ReservedUnits    int
    CommittedUnits   int
    UnitDefinition   string
    KubernetesResources KubernetesResourceCapacity
}

// KubernetesResourceCapacity contains raw Kubernetes resource availability
type KubernetesResourceCapacity struct {
    AvailableCPUMillicores int64
    AvailableMemoryBytes   int64
    AvailableStorageBytes  int64
    NodeCount              int
}
```

---

## 8. Constructor and Initialization

```go
// New creates and initializes a new DCM SDK instance.
// Returns an error if the configuration is invalid or
// if required components for the declared conformance level
// are missing.
func New(config Config) (SDK, error)

// NewWithClient creates a new SDK instance with a pre-configured
// DCM client. Used primarily for testing.
func NewWithClient(config Config, client Client) (SDK, error)

// LoadFieldMappings loads field mapping declarations from YAML files.
// Accepts one or more file paths or glob patterns.
func LoadFieldMappings(paths ...string) ([]FieldMapping, error)

// MustNew creates a new SDK instance and panics if initialization fails.
// Convenience function for use in main() where error handling via
// panic is acceptable.
func MustNew(config Config) SDK
```

---

## 9. Minimal Level 1 Example

```go
package main

import (
    "context"
    "os"

    dcmsdk "github.com/dcm-project/operator-sdk"
    ctrl "sigs.k8s.io/controller-runtime"
)

func main() {
    // Minimal Level 1 configuration
    dcm, err := dcmsdk.New(dcmsdk.Config{
        ProviderName:     "my-operator",
        DisplayName:      "My Operator DCM Provider",
        DCMEndpoint:      os.Getenv("DCM_ENDPOINT"),
        OperatorEndpoint: os.Getenv("OPERATOR_ENDPOINT"),
        ConformanceLevel: dcmsdk.Level1,
        ServiceTypes: []dcmsdk.ServiceTypeConfig{
            {
                ServiceTypeName:     "Storage.Database",
                ServiceTypeUUID:     "dcm-registry-uuid-for-storage-database",
                CRDReference: dcmsdk.CRDReference{
                    Group:   "postgresql.cnpg.io",
                    Version: "v1",
                    Kind:    "Cluster",
                },
                OperationsSupported: []dcmsdk.Operation{
                    dcmsdk.OperationCreate,
                    dcmsdk.OperationRead,
                    dcmsdk.OperationDelete,
                },
            },
        },
        FieldMappingFiles: []string{"dcm-mappings.yaml"},
    })
    if err != nil {
        panic(err)
    }

    ctx := ctrl.SetupSignalHandler()

    // Register with DCM in background — does not block startup
    dcm.Register(ctx)

    // Start HTTP server with health + DCM endpoints
    go dcm.StartServer(ctx, ":8080")

    // Start operator manager (existing code unchanged)
    mgr, _ := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{})
    mgr.Start(ctx)
}

// In reconciliation loop — minimal Level 1 additions
func (r *ClusterReconciler) Reconcile(
    ctx context.Context,
    req ctrl.Request,
) (ctrl.Result, error) {

    cluster := &cnpgv1.Cluster{}
    if err := r.Get(ctx, req.NamespacedName, cluster); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    // Only process DCM-managed resources
    if !r.DCM.IsManagedResource(cluster) {
        return ctrl.Result{}, nil
    }

    // Existing reconciliation logic here...

    // Report status to DCM (SDK handles translation via field mappings)
    r.DCM.ReportStatus(ctx, cluster)

    return ctrl.Result{}, nil
}
```

---

## 11. Callback Credential Management

The SDK manages the provider callback credential lifecycle automatically.

### 11.1 Credential Storage

```go
// CallbackCredential is managed internally by the SDK.
// Operators do not need to handle credential rotation manually.
type CallbackCredential struct {
    Value      string    // Bearer token — never logged
    ValidUntil time.Time // Pre-rotation begins at 50% of lifetime
    UUID       string    // For audit correlation
}
```

### 11.2 Automatic Rotation

The SDK initiates credential rotation before expiry (at 50% of the credential lifetime). During the transition window, the SDK accepts both the old and new credentials simultaneously. Operators do not need to handle rotation — the SDK does it transparently.

```go
// The SDK emits a credential rotation event when rotation completes.
// Operators can subscribe to be notified (e.g., to update secret stores).
sdk.OnCredentialRotated(func(old, new CallbackCredential) {
    // Optional: persist new credential to external secret store
    log.Info("credential rotated", "new_uuid", new.UUID)
})
```

### 11.3 entity_uuid and resource_id

The SDK ensures `dcm_entity_uuid` is echoed in every response and callback. `resource_id` is the operator's own stable identifier. DCM uses `dcm_entity_uuid` for all internal routing — `resource_id` is stored by DCM as a correlation handle but never used for routing or identity.

```go
// The SDK automatically populates dcm_entity_uuid from the CreateRequest.
// Operators set resource_id to their own stable identifier.
resp := &CreateResponse{
    ResourceID:   myInternalID,           // operator-assigned
    DCMEntityUUID: req.DCMEntityUUID,     // echoed from CreateRequest — SDK validates this
    LifecycleState: StatePROVISIONING,
}
```

---

## 10. Open Questions

> All questions resolved. See Resolution Notes below.


| # | Question | Impact | Status |
|---|----------|--------|--------|
| 1 | Should the SDK support non-Go operator frameworks via a language-agnostic REST adapter? | Ecosystem breadth | ✅ Resolved |
| 2 | How should the SDK handle DCM endpoint unavailability — queue events locally or drop? | Reliability | ✅ Resolved |
| 3 | Should field mappings support dynamic resolution — a transform that queries external data? | Flexibility | ✅ Resolved |
| 4 | Should the SDK provide a testing framework for unit testing operator-DCM integration? | Developer experience | ✅ Resolved |
| 5 | Should the SDK expose metrics (Prometheus) for DCM registration status, event delivery success, etc.? | Observability | ✅ Resolved |

---



## Resolution Notes

**Q1:** No language-agnostic REST adapter is needed in the Go SDK — the Operator Interface Specification is itself language-agnostic. Operators in any language implement the specification directly via HTTP. Community SDKs for Java/Python are encouraged as community projects. The Go SDK is the reference implementation only.

**Q2:** Queue locally, always. The SDK maintains a local durable queue (SQLite — simple, no external dependencies) with configurable capacity and TTL. On DCM reconnection, queued events are replayed in order. If the local queue reaches capacity (DCM unavailable for an extended period), the SDK enters DEGRADED mode: new events are still accepted up to the hard capacity limit, then dropped with a QUEUE_OVERFLOW audit record and an alert via the operator's configured alerting channel. Dropping events silently is never acceptable — the system is designed to be the authoritative source of truth.

**Q3:** Dynamic field resolution is implemented as an Information Provider reference in the field mapping declaration. The SDK declares 'this field resolves from Information Provider X with lookup key Y'. DCM resolves the value during layer assembly via the standard Information Provider query. This keeps transformation logic in DCM's Policy Engine where it belongs and is auditable via standard field provenance.

**Q4:** A mock DCM test harness ships as a first-class component of the SDK. The harness implements the registration, dispatch, cancel, and discover endpoints with configurable behaviors: inject failures, inject delays, return specific payloads, simulate timeout scenarios. Operators use the test harness for unit and integration testing without a live DCM deployment. This is essential for adoption — operators must be able to test DCM integration in CI without a full environment.

**Q5:** Prometheus metrics are mandatory, not optional. The SDK exposes: registration_status (gauge), event_delivery_total (counter, labels: status=success|failure), event_delivery_duration_seconds (histogram), local_queue_depth (gauge, only when local queuing active), dispatch_duration_seconds (histogram), discovery_cycle_duration_seconds (histogram). Metrics endpoint follows the standard DCM observability model and is required for Level 2 conformance.

*Document maintained by the DCM Project. For questions or contributions see [GitHub](https://github.com/dcm-project).*
