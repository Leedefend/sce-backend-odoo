# v1.1 Engineering Convergence Scope

Date: 2026-07-12
Branch: `topic/v1.1-engineering-convergence`
Milestone: `v1.1 Engineering Convergence`

## Goal

v1.1 is an engineering convergence release. The objective is to make the current system governable, testable, recoverable, and ready for controlled real-project pilot usage.

## Included

- Defect fixes for P0/P1 delivery blockers.
- GitHub Issue, PR, CODEOWNERS, milestone, and branch-protection governance.
- Unified CI and local quality entry points.
- Four-layer test structure: unit, Odoo integration, contract/API, E2E.
- Core business-chain E2E smoke coverage and nightly full-regression plan.
- Security, permission, Intent API, file-upload, import, dependency, and secret-scan evidence.
- Performance baseline for list, detail, dashboard, import, and permission-filtered surfaces.
- Backup, filestore, rollback, and restore drill evidence.
- First architecture governance assets: dependency map, domain boundary ADRs, Makefile split plan, and legacy carrier disposition list.

## Excluded

- New large product capabilities not already approved.
- Large-scale model rewrites without an accepted ADR and migration plan.
- UI redesigns that are not tied to delivery blockers or approved usability defects.
- New online integrations unless required for pilot readiness.
- Production data mutation outside approved release, migration, or recovery runbooks.

## Deferred

- Full Makefile physical split after the target entry points are stable.
- Large module extraction after dependency map and domain-boundary ADR approval.
- Non-critical dashboard refinements.
- Terminal/mobile client parity beyond the current web pilot needs.

## P0 Definition

A P0 issue is any of:

- Data error or data loss.
- Permission bypass or cross-project data exposure.
- Incorrect money, tax, payment, settlement, or accumulated amount.
- Core flow cannot be completed.
- System cannot deploy, upgrade, roll back, restore, or attach required files.

## Change Admission

- `main` must be changed only through PR.
- Any feature-sized change must have an Issue with owner, priority, acceptance criteria, test requirements, rollback plan, and evidence.
- During this convergence cycle, only defect fixes, delivery blockers, approved necessary requirements, and governance/test/architecture work are allowed.
- PR evidence must use the unified quality entry points unless explicitly waived by the release owner.
