# ADR-028: A discovery source is an Information Provider; whether its observation counts is policy

**Status:** Proposed (croadfeldt upstream). Amends ADR-017 (brownfield greening): its discovery avenues and its claim-proof rule.
**Date:** 2026-11-23
**Background:** ADR-017 (ingestion via the Discovered store); ADR-005 (provider abstraction); UDLM provider-contract §8 (one provider, many capabilities); UDLM register rows 181 (the Discovered record is the observed state) and 182 (`adoption` is a lifecycle operation), dcm-project/udlm#755.

## Context

ADR-017 splits discovery into two avenues. A provider enumerates what it controls (Avenue 1). A "non-provider observer", such as a probe, scanner, CMDB or import tool, reports what it sees (Avenue 2). Two parts of that no longer hold.

1. **Every discovery source is a provider.** In DCM a provider is anything that integrates with DCM and provides a service: information, provisioning, a policy engine. UDLM models this as one provider with capabilities (provider-contract §8). A scanner that sends observations declares `serve_data`: it is an Information Provider. There is no "non-provider" source.
2. **Validity is policy, not architecture.** ADR-017 step 4 fixes a rule: a claim on a resource seen only by a third party is not accepted on the provider's word alone. Which observations count, how far a source is trusted, and who owns what it saw are policy decisions. The data model and DCM only carry the facts.

## Decision

1. **The two avenues stay, named by capability.**

   | Avenue | Source | What it reports |
   |---|---|---|
   | 1 | A provider declaring `realize_resources` | What it controls. Arrives attributed to its owner |
   | 2 | An Information Provider declaring `serve_data` | What it observes but does not own |

   Read ADR-017's "third-party" and "non-provider observer" as Avenue 2 in this sense.

2. **Claimed and unclaimed are unchanged, and are about ownership.** Unclaimed means no owning provider, even when an Information Provider reported the resource.

3. **Policy decides validity and ownership.** The record carries what policy judges: `origin`, `provider`, `matched_by`, `correlation_ids` and each source's `authority_level`. DCM's policy engine decides whether an observation counts and which provider owns a resource. ADR-017's claim-proof rule becomes a default policy that a profile may tighten or relax. It is not a fixed step.

4. **Adoption is the act of doing that work.** It runs as UDLM's `adoption` lifecycle operation (row 182), so policies can scope to it.

## Options considered

- **Edit ADR-017 in place.** Rejected: an Accepted ADR is superseded, not edited.
- **Keep "non-provider observer".** Rejected: it contradicts the single provider model, and a source DCM accepts data from has to be registered, validated and trusted like any provider.
- **Keep claim proof as a fixed rule.** Rejected: it puts a trust decision outside policy, where no profile can change it.

## Consequences

- Avenue 2 sources register as Information Providers and inherit the provider contract: registration, health, trust and `authority_level`.
- ADR-017 is otherwise unchanged: reverse placement, claim, backport, correlation identifiers and its best practices stand.
- The homelab's probes are Avenue 2 Information Providers. They are not unregistered observers.
