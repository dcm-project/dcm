---
Document Status: ✅ Stable — DCM implementation
Document Type: Architecture Reference — Design Philosophy
Established: 2026-05-26
Maps to: udlm/design-principles/design-priorities.md
---

# DCM Design Principles — Implementation Choices

> **Implements the design principles defined in UDLM**:
> [udlm/design-principles/design-priorities.md](https://github.com/croadfeldt/udlm/blob/main/design-principles/design-priorities.md).
> UDLM owns the four invariant principles (consumer sovereignty, zero trust,
> federation, policy as code) and their decision framework. This document
> records the specific implementation choices DCM makes when applying them.

DCM operationalizes the four UDLM priorities (Security → Ease of Use →
Extensibility → Fit for Purpose) through specific runtime mechanics, profile
configurations, and integration choices. This document captures the
DCM-specific tradeoffs.

---

## 1. Design priorities — implementation choices

The four UDLM priorities apply in DCM exactly as defined. DCM's
implementation choices express them concretely:

| UDLM principle | DCM implementation choice |
|---|---|
| Security (Priority 1) | Non-negotiable security properties wired into every profile via the profile system; auto-approve threshold ≤ 50 enforced at scoring engine; CPX-001 (no credential values in DCM stores) enforced at credential issuance |
| Ease of use (Priority 2) | The profile system as the primary scaling mechanism; consumer Admin API integration point (so external workflow tools can plug in without DCM-side adapters); Flow GUI for policy authoring |
| Extensibility (Priority 3) | Compliance domain overlays compose with base profiles; Policy Groups compose with profile policies; capability extensions compose with base provider contracts; Universal Group Model spans all artifact types |
| Fit for purpose (Priority 4) | Complete lifecycle coverage — every edge case (partial realization, compensation, drift remediation, credential revocation on decommission) handled by named mechanism, not happy-path-only |

---

## 2. Approval tier model (runtime enforcement)

UDLM defines the authority tier vocabulary (auto / reviewed / verified /
authorized) and the rules for custom tier insertion. The four tiers are an
escalating human-gate ladder: `auto` = no human gate; `reviewed` = one
approver; `verified` = two independent approvers; `authorized` = a quorum vote
by a named group. DCM enforces tiers at runtime through the following
mechanisms.

| Tier | DCM enforcement |
|---|---|
| `auto` | Structural and governance validation pipeline; automatic activation on pass; no human gate |
| `reviewed` | Approval record created; eligible reviewer notified via the Notification Service; pipeline held; decision recorded via Admin API endpoint `POST /api/v1/admin/approvals/{uuid}:vote`; activation or rejection on first decision |
| `verified` | Approval record requires two independent decisions; DCM enforces distinct actors (same actor cannot satisfy both); eligible reviewer notification; pipeline held; activation on second decision |
| `authorized` | Approval record specifies the required DCMGroup and quorum threshold (N of M); group member notification; pipeline held; threshold evaluation on each vote; activation when N reached |

**DCM does not build a deliberation/voting platform.** DCM builds:

1. DCMGroup membership management (which actors constitute the authorized group)
2. Quorum declaration (`N of M` in profile or per-decision config)
3. Notification routing on state entry into `pending_authorized`
4. Vote-recording API endpoint (the Admin API is the integration point)
5. Quorum tracking and pipeline advancement
6. Audit trail with `recorded_via` provenance (Slack bot, ServiceNow, Jira, direct API, etc.)

External systems (ServiceNow, Jira, email workflows, Slack bots) connect by
calling the vote-recording API. A Slack bot that collects emoji reactions and
then calls DCM's Admin API is a valid implementation.

### 2.1 Admin API as integration point

```
POST /api/v1/admin/approvals/{approval_uuid}:vote
Authorization: Bearer <token>
{
  "decision": "approve | reject",
  "reason": "<human-readable rationale>",
  "recorded_via": "dcm_admin_ui | servicenow | jira | slack_bot | api_direct | other",
  "external_reference": "<ticket or case ID in external system — optional>"
}
```

The `recorded_via` field provides audit provenance. It is informational, not
enforced — DCM doesn't care how the vote was collected, only that an authorized
group member recorded it.

### 2.2 Deadline and escalation

DCM manages the approval window and fires escalation notifications:

```yaml
approval_window:
  reviewed: PT72H
  verified: PT72H
  authorized: P7D
  on_expiry:
    reviewed:  escalate     # escalate to platform admin
    verified:  escalate
    authorized: reject       # authorized tier that cannot reach quorum → reject
```

See [`credentials-and-auth/authority-enforcement.md`](credentials-and-auth/authority-enforcement.md)
for the tier evaluation algorithm and degradation review orchestration.

---

## 3. Profile-governed system constraints

DCM ships six built-in profiles (`minimal`, `dev`, `standard`, `prod`, `fsi`,
`sovereign`). Profiles control:

- Enforcement strictness (how strictly a security property is enforced)
- Threshold values (TTLs, intervals, thresholds)
- Automation level (automated vs manual trigger)
- Approval tier defaults (which tier routes requests at which score)
- Review periods (shadow mode duration before promotion)

Profiles do **not** control:

- Whether a security property is present (it always is)
- Which non-negotiable constraints apply (CPX-001, SMX-004, SMX-008, etc.)
- Whether the audit trail is maintained
- Whether the data model is valid

**The `minimal` profile is "security with minimal operational overhead" — not
"minimal security."** A minimal-profile deployment still rotates credentials
(longer interval, manual trigger acceptable), detects idle credentials (generous
P30D threshold), audits first credential retrieval, maintains revocation
registry. The security model is present and correct; the enforcement strictness
and automation burden are reduced.

See [`governance-enforcement/policy-profiles.md`](governance-enforcement/policy-profiles.md)
for the complete profile definitions and the matrix of what each profile controls.

---

## 4. Policy-as-code requirement (integration)

DCM realizes the UDLM "policy as code" principle by integrating with OPA
(Open Policy Agent) as the default policy evaluation engine and supporting
External Policy Evaluators for organization-specific policy systems.

**Internal mode (default):** Policies are stored in DCM's PostgreSQL database
and evaluated by OPA. Delivery mechanisms include API push/pull, GitOps
adapter, OPA bundle protocol, or external-schema naturalization. All
mechanisms produce equivalent evaluation.

**External mode:** DCM sends evaluation context to an external endpoint
declared by the External Policy Evaluator provider. The external system
returns structured results (pass/fail, score, enrichment fields). DCM does
not see the policy logic; it trusts the results within scoped bounds.
Governance policies BBQ-001 through BBQ-009 (in
[udlm/contracts/policy-contract.md](https://github.com/croadfeldt/udlm/blob/main/contracts/policy-contract.md))
constrain external evaluation: data sovereignty check, data minimization,
audit per query, default-deny on unknown.

Every policy evaluation produces an audit record regardless of outcome —
audit is non-negotiable.

---

## 5. Documentation discipline requirements (DCM-internal)

DCM-side documents must:

1. Open with `> Implements contracts defined in UDLM: [link]` when implementing
   a UDLM contract
2. Reference the priority order where design decisions involve tradeoffs
3. Explain non-negotiable security properties with clear rationale
4. Document what profiles control vs what they do not
5. Identify the ease-of-use mechanism that accompanies every security requirement
6. State fit-for-purpose scope explicitly

These are operational documentation standards, not UDLM contract requirements.
A peer DCM realization is free to organize its internal documentation
differently.

---

## 6. System policies (DCM realization)

| Policy | Rule |
|--------|------|
| `DPO-001-DCM` | Security properties are architecturally present in all DCM profiles. Profiles control enforcement strictness, thresholds, and automation level — not whether the property exists. |
| `DPO-002-DCM` | Every security requirement in DCM must be accompanied by an ease-of-use mechanism that makes compliance effortless for the common case. |
| `DPO-003-DCM` | New DCM capabilities should be expressed through the existing profile/policy/provider extension system before creating new mechanisms. |
| `DPO-004-DCM` | Fit for purpose is a precondition. All four priorities apply only within the constraint that DCM can fulfill its lifecycle management mission. |
| `DPO-005-DCM` | The `minimal` profile is "security with minimal operational overhead" — not "minimal security." Design changes that disable security properties rather than scaling them violate DPO-001-DCM. |
| `DPO-006-DCM` | When security and ease of use conflict in DCM, redesign the ease-of-use mechanism — not the security requirement. The secure path must also be the easy path. |

---

## 7. Common misapplications to avoid

**"We can disable X in the minimal profile for simplicity."**
Wrong. The minimal profile scales down operational burden, not security
properties. Question: what is the minimum viable implementation of X that
requires no operational overhead? That is what minimal profile gets.

**"Security is too complex for our users, so we'll make it optional."**
Wrong. If security is too complex, the design of the security mechanism needs
to improve (Priority 2). Making security optional removes it — that fails
Priority 1.

**"We need a new mechanism for this capability."**
Wrong starting point. Question: can this be expressed through profiles,
policies, provider capability extensions, or compliance overlays? Usually
yes. If genuinely not, extend the nearest existing mechanism.

**"This edge case isn't part of the lifecycle."**
Wrong framing. Every edge case in the lifecycle — partial realization,
compensation, drift remediation, credential revocation on decommission —
is part of the lifecycle. Fit for purpose means handling the complete
lifecycle, not just the happy path.
