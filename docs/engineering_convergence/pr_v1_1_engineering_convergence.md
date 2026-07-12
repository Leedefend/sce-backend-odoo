# PR: v1.1 Engineering Convergence

## Summary

Establishes the v1.1 engineering convergence baseline: GitHub governance assets, unified CI quality gate, test inventory and triage evidence, E2E journey mapping, architecture boundary documentation, complexity reporting, and split-plan queue.

## Linked Issue

Tracks seed governance issues `#1008`-`#1023` created from `docs/engineering_convergence/github_issue_seed_v1.1.md`.

## Scope

Included:

- Phase 0 scope, risk, baseline, and change admission documentation.
- Phase 1 GitHub templates, CODEOWNERS, quality workflow, and `make ci` entrypoint.
- Phase 2 test inventory, summary, layering policy, and dedupe hotspot disposition.
- Phase 3 E2E journey matrix and fixed-data Odoo journey gate.
- Phase 4 module dependency map, domain boundary ADR, complexity budget report, and split-plan queue.
- Secret scan and CI support scripts.
- GitHub milestone, labels, seed issues, draft PR, branch protection, and dedicated self-hosted CI runner setup.

Excluded:

- Production deployment or production data mutation.
- Completing the remaining release-scale E2E/security/performance/disaster-recovery phases.

## Impacted Areas

- [x] Backend/Odoo models
- [x] Frontend
- [x] API/Intent contract
- [x] Data migration
- [x] Security/permissions
- [x] DevOps/CI
- [x] Documentation

## Test Evidence

- [x] `make ci`
- [x] `make test.e2e.fixed_data.odoo`
- [x] `make audit.boundary.smart_core.ci`
- [x] `python3 scripts/ci/generate_test_inventory.py`
- [x] `python3 scripts/ci/summarize_test_inventory.py`
- [x] `python3 scripts/ci/generate_e2e_journey_matrix.py`
- [x] `python3 scripts/ci/generate_module_dependency_map.py`
- [x] `python3 scripts/ci/generate_complexity_budget_report.py`
- [x] `python3 scripts/ci/generate_split_plan_queue.py`
- [x] `git diff --check`
- [x] GitHub PR check `v1.1 quality gate / quality_gate` on self-hosted runner `ci-1-95-2-123`

## Data Migration Impact

No production data migration is executed by this PR. Migration-related scripts and evidence are inventoried and classified; execution remains gated by existing guarded Make targets and future owner-reviewed issues.

## Security and Permission Impact

Adds high-confidence secret scanning to `make ci` and records security/permission validation scope in the convergence plan. GitHub branch protection now requires PR review, CODEOWNERS review, conversation resolution, blocked force pushes/deletions, and the `v1.1 quality gate / quality_gate` check.

## Rollback Plan

Revert this PR if the governance baseline must be removed. No production data or external GitHub setting is mutated by the local code changes.

## Delivery Evidence

- `docs/engineering_convergence/phase0_phase1_status.md`
- `docs/engineering_convergence/test_inventory_summary.md`
- `docs/engineering_convergence/e2e_journey_matrix.md`
- `docs/engineering_convergence/module_dependency_map.md`
- `docs/engineering_convergence/complexity_budget_report.md`
- `docs/engineering_convergence/split_plan_queue.md`
- `docs/engineering_convergence/backlog_scope_decision_v1.1.md`
- `docs/engineering_convergence/github_governance_runbook.md`
- GitHub milestone `v1.1 Engineering Convergence`
- GitHub issues `#1008`-`#1023`
- GitHub PR `#1024`
- Self-hosted runner `ci-1-95-2-123` on `1.95.2.123`
- PR check run `v1.1 quality gate / quality_gate`

## Residual Items

- Seven residual 2-asset dedupe hotspot families remain intentionally unmarked as aggregate-covered; their dispositions are documented in `test_inventory_summary.md`.
- Historical BOQ/model backlog `#2`, `#4`-`#9`, and `#64`-`#76` is labeled and explicitly deferred from v1.1 by `backlog_scope_decision_v1.1.md`.
- Release-scale E2E role/browser evidence, E2E-06/E2E-10 fixed-data gates, security audit, performance baseline, and disaster recovery rehearsal remain future phase work.

## Checklist

- [x] Scope is tied to documented seed issues.
- [x] Acceptance criteria for local Phase 0/1/2 governance assets are met.
- [x] Tests are repeatable locally through `make ci`.
- [x] Tests are repeatable remotely through `v1.1 quality gate / quality_gate`.
- [x] No direct production mutation is included.
- [x] Residual risk is recorded in convergence documentation.
