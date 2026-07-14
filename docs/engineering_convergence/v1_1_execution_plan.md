# v1.1 Engineering Convergence Execution Plan

Milestone: `v1.1 Engineering Convergence`
Duration: 6 weeks

## Sequence

1. Phase 0: freeze scope and establish baseline.
2. Phase 1: converge GitHub and quality gates.
3. Phase 2: restructure testing into unit, Odoo integration, contract/API, E2E.
4. Phase 3: automate the 12 real business-chain E2E scenarios.
5. Phase 4: start architecture and code-scale governance.
6. Phase 5: produce security, performance, and disaster-recovery evidence.
7. Phase 6: enter controlled real-project pilot.

## Week 1 Required Outputs

- `release_scope_v1.1.md`
- `baseline_report_v1.1.md`
- `engineering_risk_ledger.md`
- `phase0_phase1_status.md`
- GitHub Issue and PR templates.
- CODEOWNERS.
- Unified Makefile quality entries.
- CI workflow calling the unified quality entries.
- Initial `test_inventory.csv`.
- `commit_convention.md`
- `adr_0001_domain_boundaries.md`
- `module_dependency_map.md`
- `complexity_budget_policy.md`

## Issue Labels

- `priority:P0`, `priority:P1`, `priority:P2`
- `area:backend`, `area:frontend`, `area:contract`, `area:devops`, `area:security`, `area:data`, `area:docs`
- `type:bug`, `type:refactor`, `type:test`, `type:governance`
- `status:ready`, `status:in-progress`, `status:blocked`, `status:verification`
- `risk:data`, `risk:security`, `risk:release`, `risk:performance`
- `evidence:required`

## Phase Exit Rule

A phase is not complete until its evidence is committed or linked in the milestone. "Development complete" is not an exit criterion.

## Current Checkpoint

As of `origin/main` `7d2f86ec973594d8919474a1f075c0672e557b65`,
the initial Phase 4 P4-P0 split sequence has landed on mainline. The next
focus is Phase 5/6 evidence closure:

- core amount calculation tests;
- permission and project-isolation verification;
- backup and filestore restore drill;
- performance baseline;
- controlled pilot readiness.

The latest `origin/main` commit currently needs a linked workflow-run evidence
record before this document can claim that the mainline commit itself passed
the remote quality gate.
