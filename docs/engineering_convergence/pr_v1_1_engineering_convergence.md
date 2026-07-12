# PR: v1.1 Engineering Convergence

## Summary

Establishes the v1.1 engineering convergence baseline: GitHub governance assets, unified CI quality gate, test inventory and triage evidence, E2E journey mapping, architecture boundary documentation, complexity reporting, and split-plan queue.

## Linked Issue

Closes the seed governance issues from `docs/engineering_convergence/github_issue_seed_v1.1.md` after they are created in GitHub.

## Scope

Included:

- Phase 0 scope, risk, baseline, and change admission documentation.
- Phase 1 GitHub templates, CODEOWNERS, quality workflow, and `make ci` entrypoint.
- Phase 2 test inventory, summary, layering policy, and dedupe hotspot disposition.
- Phase 3 E2E journey matrix and fixed-data Odoo journey gate.
- Phase 4 module dependency map, domain boundary ADR, complexity budget report, and split-plan queue.
- Secret scan and CI support scripts.

Excluded:

- GitHub admin-only settings that require authenticated repository admin access.
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

## Data Migration Impact

No production data migration is executed by this PR. Migration-related scripts and evidence are inventoried and classified; execution remains gated by existing guarded Make targets and future owner-reviewed issues.

## Security and Permission Impact

Adds high-confidence secret scanning to `make ci` and records security/permission validation scope in the convergence plan. It does not alter production access rules directly.

## Rollback Plan

Revert this PR if the governance baseline must be removed. No production data or external GitHub setting is mutated by the local code changes.

## Delivery Evidence

- `docs/engineering_convergence/phase0_phase1_status.md`
- `docs/engineering_convergence/test_inventory_summary.md`
- `docs/engineering_convergence/e2e_journey_matrix.md`
- `docs/engineering_convergence/module_dependency_map.md`
- `docs/engineering_convergence/complexity_budget_report.md`
- `docs/engineering_convergence/split_plan_queue.md`
- `docs/engineering_convergence/github_governance_runbook.md`

## Residual Items

- GitHub CLI is not authenticated locally, so milestone creation, issue cleanup, branch protection, and required-check enforcement must be completed through GitHub UI or after `gh auth login`.
- Seven residual 2-asset dedupe hotspot families remain intentionally unmarked as aggregate-covered; their dispositions are documented in `test_inventory_summary.md`.
- Release-scale E2E role/browser evidence, E2E-06/E2E-10 fixed-data gates, security audit, performance baseline, and disaster recovery rehearsal remain future phase work.

## Checklist

- [x] Scope is tied to documented seed issues.
- [x] Acceptance criteria for local Phase 0/1/2 governance assets are met.
- [x] Tests are repeatable locally through `make ci`.
- [x] No direct production mutation is included.
- [x] Residual risk is recorded in convergence documentation.
