# ADR-001: Why DCM Exists

**Status:** Accepted  
**Date:** March 2026  

## Context

Enterprise data centers run hundreds of thousands of resources — VMs, containers, network segments, storage volumes — across multiple infrastructure platforms. Today, each platform has its own provisioning workflow, API, data format, and lifecycle model. The result:

- **No unified view of what's deployed.** Intended state, deployed state, and actual state diverge silently. Nobody can answer "what's running, who owns it, and does it match what was approved?"
- **No consistent governance.** Policy enforcement is tribal knowledge. Security reviews are manual gates. Compliance is verified after the fact rather than enforced at request time.
- **No common abstraction.** A team requesting a VM goes through one process; requesting a database goes through another; requesting a three-tier application requires manually coordinating both plus networking.

Public cloud solves this with unified control planes (AWS CloudFormation, Azure Resource Manager, GCP Deployment Manager). On-premises infrastructure has no equivalent.

## Decision

Build DCM — a management plane for enterprise data center infrastructure that provides:
- A unified data model and API across all infrastructure platforms
- Policy-as-code enforcement on every request before provisioning
- Full lifecycle management from request through decommission with tamper-evident audit
- A provider abstraction that makes any infrastructure platform consumable through the same interface

DCM is **not** a provisioning tool. It is the governance and orchestration layer that sits above provisioning tools (Ansible, Terraform, operators) and governs what gets requested, approved, built, owned, and decommissioned.

## Consequences

- DCM must be infrastructure-agnostic — it cannot favor any single platform
- The data model must be extensible to any resource type without code changes
- Policy evaluation must be mandatory, not optional — governance is the value proposition
- Audit must be tamper-evident to satisfy regulated environments (the primary adopters)
