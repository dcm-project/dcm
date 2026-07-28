> **Archived 2026-07-23.** Pre-split review-strategy memo; the process it describes is superseded by the CI cleanliness gates + the nine-question review brief (croadfeldt/dav docs/repo-cleanliness-review.md). Kept for the reasoning trail — do not extend.

# DCM Architecture Documentation — Review Strategy

**Author:** Chris, Principal Architect  
**Date:** April 2026  
**Audience:** DCM Engineering Team

---

## The Problem

The DCM architecture now comprises 58 data model documents, 15 specifications, 4 OpenAPI schemas, and a capabilities matrix with 331 entries — roughly 30,000 lines of technical documentation. This body of work defines the complete control plane, data model, provider contract, policy engine, audit system, and governance model.

This documentation needs engineering review, but the experience with PRs #7 and #8 demonstrated the challenge: even GitHub's Sourcery bot hit its 20,000-line review limit. Nobody is going to read 30,000 lines linearly, and asking the team to do so would be neither productive nor respectful of their time.

This document proposes a strategy to make the architecture documentation consumable, reviewable, and useful for the engineering team.

---

## Principles

1. **Nobody needs to read everything.** Each team member needs the 3-5 documents relevant to their area, not all 58.
2. **Decisions are reviewable. Reference material is not.** The team should review *what we decided and why* — not the full specification text that implements those decisions.
3. **Concrete examples beat abstract specifications.** A worked example tracing one request through the full pipeline teaches more than 10 documents of structural definitions.
4. **The documentation should be queryable, not just readable.** The AI prompt (5,768 lines, 125 sections) enables conversational exploration of any architectural topic.

---

## Proposal 1: Role-Based Reading Guide

**Effort:** Low (1 page)  
**Impact:** Immediate  

Create a single-page reading guide that tells each person where to start based on what they work on. Example:

| If you work on... | Start with these documents | Then reference... |
|---|---|---|
| **Provider development** (VM, ACM, network) | Doc A (Provider Contract), Doc 06 (Resource Entities), Provider Dev Guide | Docs 10, 22, 30 (provider types) |
| **Policy and placement** | Doc B (Policy Contract §1-7), Doc 14 (Profiles) | Doc B §8-9 (Constraint Registry, Templates), §18 (Overrides) |
| **Request pipeline** (orchestrator, processor) | Doc 02 (Four States), Doc 03 (Layering), Doc 04 (Examples) | Doc 25 (Control Plane), Consumer API Spec |
| **Catalog and API gateway** | Doc 06 (Resource Entities), Consumer API Spec, Admin API Spec | Doc 36 (API Versioning), AEP conventions |
| **Audit, security, compliance** | Doc 16 (Universal Audit §1-8), Doc 31 (Credentials), Doc 43 (Callback Auth) | Doc 26 (Governance Matrix), Doc 14 §8-10 |
| **Database and storage** | Doc 11 (Data Store Contracts), Doc 02 §4 (Data Domains), SQL Schema | Doc 17 (Deployment) |

This cuts the perceived scope by 80% for any individual reviewer. Each path is 3-5 documents, not 58.

---

## Proposal 2: Architecture Decision Records (ADRs)

**Effort:** Medium (1 page per major decision)  
**Impact:** High — this is what the team actually needs to review  

The team does not need to review the full 1,344-line Policy Contract to understand the override model. They need a 1-page summary that says:

> **Decision:** 5 override mechanisms layered by severity.  
> **Context:** Requests can be blocked by hard enforcement policies. The team needs a way to handle legitimate exceptions without undermining policy governance.  
> **Options considered:** Override policies only, manual override only, exception grants, compensating controls.  
> **Decision:** All five, layered: Override Policy (planned) → Exception Grant (pre-authorized) → Manual Override (immediate) → Compensating Control (structural) → Dual-Approval (modifier for hard policies).  
> **Consequences:** `override_requests` SQL table added. 5 new events. Consumer sees POLICY_BLOCKED with resolution options (modify, override, cancel, escalate). Admin API gets 4 new endpoints.

The major decisions that need ADRs (roughly 15):

1. One required infrastructure (PostgreSQL only)
2. Internal auth/secrets/events with optional external delegation
3. 5 provider types (why these 5, what was consolidated)
4. 2 policy evaluation modes (Internal/External)
5. Evaluation Context with multi-pass convergence
6. Constraint Type Registry and Policy Templates
7. Lifecycle-scoped policy evaluation (10 operation types)
8. Policy Override Model (5 mechanisms)
9. Policy Block Resolution (consumer options, not auto-override)
10. Merkle tree audit with configurable granularity
11. Data-driven policy matching (4 sources)
12. Stage signing and payload chain of custody
13. AEP API conventions adoption
14. Traefik over KrakenD (API Gateway decision)
15. PostgreSQL consolidation (stores model)

ADRs are individually reviewable. The full specification documents become reference material that people consult when implementing — not review material that blocks progress.

---

## Proposal 3: Domain-Split PRs

**Effort:** Medium (splitting existing content into themed PRs)  
**Impact:** High — makes the merge process manageable  

Instead of one PR with the entire architecture, submit 6-8 PRs by domain. Each is reviewable in one sitting and can be assigned to the most relevant reviewer:

| PR | Content | Primary Reviewer | Size |
|---|---|---|---|
| Core Data Model | Docs 00-04, 11, SQL schema | machacekondra | ~3,000 lines |
| Provider Contract | Doc A, docs 06, 10, 22, 30, provider callback | pkliczewski, ygalblum | ~3,500 lines |
| Policy Contract | Doc B, doc 14 | gabriel-farache | ~4,000 lines |
| Audit and Security | Docs 16, 31, 43, 26, 27 | jenniferubah | ~2,500 lines |
| Request Pipeline and Lifecycle | Docs 25, 50, 36, consumer/admin API specs | machacekondra | ~3,000 lines |
| Capabilities and Examples | Capabilities Matrix, doc 04, doc 52, taxonomy | All (light review) | ~2,500 lines |
| Infrastructure and Deployment | Doc 51, doc 17, doc 41, OpenAPI schemas | ygalblum | ~2,000 lines |
| Federation and Advanced | Docs 20, 44, 48, DISCUSSION-TOPICS | pkliczewski | ~2,000 lines |

Each reviewer focuses on their area of expertise. Cross-cutting concerns (like "does the policy model work with the provider contract?") are handled in a final integration review after the domain PRs merge.

---

## Proposal 4: End-to-End Walkthrough Document

**Effort:** Medium (1 document, ~500 lines)  
**Impact:** Very High — the single most useful onboarding artifact  

The team responded well to concrete examples. machacekondra specifically requested the three-tier app example. A dedicated walkthrough document that traces one request through the *entire* pipeline — with actual YAML payloads at each stage — would be worth more than 10 specification documents.

The walkthrough would cover:

1. Consumer submits a VM request (show the API call and intent payload)
2. Layer assembly (show which layers merge and the assembled payload)
3. Policy evaluation (show which policies fire, what constraints emit, how conflicts resolve)
4. A policy blocks the request (show the POLICY_BLOCKED response with resolution guidance)
5. Consumer modifies the request (show the modified payload)
6. Placement (show candidate scoring and selection)
7. Dispatch to provider (show the naturalized payload)
8. Provider callback (show the realized state)
9. Audit trail (show the Merkle tree leaves at mutation granularity)

Every stage shows real data structures, not abstract descriptions. The walkthrough references the specification documents for detail but stands alone as a readable narrative.

---

## Proposal 5: Interactive Architecture Map on the Website

**Effort:** Higher (requires frontend work)  
**Impact:** High for onboarding and navigation  

The Hugo website could host a visual diagram (Mermaid or D3) showing the 9 control plane services, the pipeline flow, and provider interactions. Each node links to the relevant documentation. People orient visually before drilling into text.

This is lower priority than proposals 1-4 but would be a strong differentiator for the project's public presence and for onboarding new contributors.

---

## Proposal 6: AI Prompt as Team Onboarding Tool

**Effort:** Zero (already built)  
**Impact:** Immediate for anyone willing to use it  

> **Note (2026-07-11): the AI prompt has since been RETIRED** — it duplicated the specs and drifted stale (it taught the pre-ADR-PROV-002 typed-provider model). Orientation now routes through `AGENTS.md` → the authoritative spec docs. The paragraph below is retained for historical context only.

The AI prompt (DCM-AI-PROMPT.md) is the most comprehensive single document in the project: 5,768 lines covering every architectural decision, every capability, every data structure, and every cross-reference. When loaded into Claude (or any capable LLM), it enables conversational exploration:

- "How does the override model work?" → 2-paragraph answer with doc references
- "What happens when a sovereignty policy blocks a request?" → full flow with YAML examples
- "What's the difference between Internal and External policy evaluation?" → comparison table

This is faster than reading documentation for exploratory understanding. The team should be encouraged to use it as a first stop before reading specification documents.

---

## Proposal 7: Session Changelogs

**Effort:** Low (produced as part of each work session)  
**Impact:** Keeps the team current without re-reading everything  

After each significant architecture session, produce a short changelog:

> **Session: April 4-7, 2026**
> 
> **Added:** Policy Override Model (doc B §18) — 5 mechanisms layered by severity. Policy Block Resolution (doc B §18.8) — consumer gets compliant value suggestions, not just a deny. Merkle tree audit (doc 16 §8) — configurable granularity (stage/mutation/field). Lifecycle-scoped policy evaluation (doc B §2.2-2.3) — 10 operation types, changed_field_filter. Test Framework Specification (doc 52) — 60 invariants, machine-readable YAML summary. OpenStack Nova example provider.
> 
> **Changed:** SQL schema now 18 tables (+override_requests, signed_tree_heads, merkle_tree_nodes). Capabilities matrix 309→331. Admin API 57→61 paths. Events 101→109.
> 
> **Why it matters for you:** If you're working on the policy engine, read doc B §18 (override model) and §2.2 (lifecycle scope). If you're working on audit, read doc 16 §8 (Merkle tree). If you're working on providers, the OpenStack Nova example in dcm-examples shows the complete naturalization/denaturalization pattern.

The team reads the changelog (~1 page). They drill into specific documents only when something affects their work.

---

## Recommended Implementation Order

| Priority | Proposal | Effort | Timeline |
|---|---|---|---|
| **1** | Reading Guide | 1 day | This week |
| **2** | Session Changelogs | Ongoing | Start immediately |
| **3** | Domain-Split PRs | 2-3 days | Before next review cycle |
| **4** | ADRs for top 15 decisions | 3-5 days | Next two weeks |
| **5** | End-to-End Walkthrough | 2-3 days | Before summit demo prep |
| **6** | AI Prompt onboarding | 0 days | Announce to team |
| **7** | Interactive Architecture Map | 1-2 weeks | Future |

---

## Summary

The architecture is comprehensive and consistent. The problem is not the documentation quality — it's the volume. The team needs navigational aids, decision summaries, and concrete examples to make 30,000 lines of specification consumable. The proposals above provide a layered approach: immediate wins (reading guide, changelogs, AI prompt), near-term improvements (domain-split PRs, ADRs), and longer-term investments (walkthrough, interactive map).

The goal is that no team member ever needs to read more than 3,000 lines to understand their area, and that every architectural decision is reviewable in a 1-page ADR — not buried in a 1,344-line specification document.
