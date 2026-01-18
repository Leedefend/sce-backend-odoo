---
capability_stage: P0.1
status: active
since: v0.3.0-stable
---
# Capability Stages

This document defines the capability stages for the project.

## Overview
- P0: baseline stability and production safety.
- P0.1: operational hardening and documentation alignment.
- P1: functional expansion (product features beyond baseline).
- P2: advanced workflows and enterprise-grade depth.

## P0
- Position: stable baseline for production safety.
- Keywords: guard, release, baseline.
- Commitments:
  - Prod guard enforced.
  - Release checklist available.
  - Base profile usable.
- Non-commitments:
  - Feature expansion beyond baseline.

## P0.1
- Position: operational alignment and governance.
- Keywords: seed lifecycle, boundaries, onboarding.
- Commitments:
  - Seed lifecycle documented and guarded.
  - Module boundaries documented.
  - Dev entry point available.
- Non-commitments:
  - New business features.

## P1
- Position: functional growth.
- Keywords: workbench depth, domain features, workflows.
- Commitments:
  - Expanded business flows.
  - User-facing feature enhancement.
- Non-commitments:
  - Enterprise-only scale features.

## P2
- Position: enterprise maturity.
- Keywords: compliance, audit, scale.
- Commitments:
  - Advanced governance and auditability.
  - Scalability and enterprise readiness.
- Non-commitments:
  - Experimental or unstable flows.

## Versioning
- v0.3.0-stable == P0 freeze.
- P0.1 builds on P0 without breaking P0 guarantees.
