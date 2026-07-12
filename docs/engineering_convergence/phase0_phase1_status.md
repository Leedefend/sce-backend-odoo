# Phase 0 and Phase 1 Status

Date: 2026-07-12
Branch: `topic/v1.1-engineering-convergence`
Remote branch: `origin/topic/v1.1-engineering-convergence`

## Completed Locally

| Item | Status | Evidence |
| --- | --- | --- |
| P0-01 Scope freeze draft | Done | `release_scope_v1.1.md` |
| P0-04 Risk ledger | Done | `engineering_risk_ledger.md` |
| P0-05 Baseline report draft | Done | `baseline_report_v1.1.md` |
| P0-06 Change admission assets | Done | PR template, issue templates, CODEOWNERS |
| P1-01 Unified CI workflow | Done | `.github/workflows/v1_1_quality_gate.yml` |
| P1-03 PR and Issue templates | Done | `.github/pull_request_template.md`, `.github/ISSUE_TEMPLATE/*` |
| P1-04 Commit convention | Done | `commit_convention.md` |
| P1-05 CODEOWNERS | Done | `.github/CODEOWNERS` |
| P1-06 Unified quality entry | Done | `make ci`, `make test.*`, `make security.secrets.scan` |
| P1-07 CI failure taxonomy | Done | `ci_failure_taxonomy.md` |
| P2-01 Test inventory | Done | `test_inventory.csv`, `scripts/ci/generate_test_inventory.py` |
| P2-01 Test inventory summary | Done | `test_inventory_summary.md`, `scripts/ci/summarize_test_inventory.py` |
| P2-02 Test asset triage baseline | Done | `decision_gate`, `disposition`, dedupe hotspots in `test_inventory_summary.md` |
| P2-02 Unified page contract aggregate coverage | Done | 65 v2/lite assets marked `covered_by_aggregate` |
| P2-02 Frontend page contract aggregate coverage | Done | 7 assets covered by `verify.frontend.product.ready` |
| P2-02 Backend contract closure aggregate coverage | Done | 5 assets covered by `verify.backend.contract.closure.mainline` |
| P2-02 Scene action surface aggregate coverage | Done | 5 assets covered by `verify.scene.runtime_boundary.gate` |
| P2-02 Scene base contract aggregate coverage | Done | 4 assets covered by `verify.scene.runtime_boundary.gate` |
| P2-02 Low-code customer config aggregate coverage | Done | 5 assets covered by customer module asset pipeline and release hardening gates |
| P2-02 Finance responsibility aggregate coverage | Done | 3 assets covered by `verify.finance_interfund.position.all` |
| P2-02 Config workbench operation aggregate coverage | Done | 3 assets covered by quick and browser acceptance gates |
| P2-02 Backend architecture report aggregate coverage | Done | 3 assets covered by `verify.backend.architecture.full.report.guard.schema.guard` |
| P2-02 Scene frontend contract aggregate coverage | Done | 3 assets covered by scene contract export and portal smoke gates |
| P2-02 Formal list surface aggregate coverage | Done | Placeholder guard covered by `verify.formal_list_surface.no_test_placeholder_guard`; cleanup policy remains explicit |
| P2-02 Smart core boundary aggregate coverage | Done | `smart_core_boundary_guard.py` covered by `verify.smart_core.boundary_guard` |
| P2-02 Secondary dedupe hotspot aggregate coverage | Done | Scene package, grouped governance, release v2.0, scene coverage/recovery, payment approval, smart core minimum, and selected material/form assets mapped to existing gates |
| SEC-06 Secret scan gate | Done | `scripts/ci/secret_scan.py`, `make security.secrets.scan` |
| P4-01 Module dependency map | Done | `module_dependency_map.md`, `scripts/ci/generate_module_dependency_map.py` |
| P4-02 Domain boundary ADR | Done | `adr_0001_domain_boundaries.md` |
| P4-07 Complexity budget baseline | Done | `complexity_budget_policy.md`, `complexity_budget_report.md` |
| P3 E2E journey matrix | Done | `e2e_journey_matrix.md`, `scripts/ci/generate_e2e_journey_matrix.py` |
| P3 fixed-data Odoo journey tests | Done | `addons/smart_construction_core/tests/test_e2e_fixed_journeys.py` |
| P3 fixed-data Odoo journey gate | Done | `make test.e2e.fixed_data.odoo` |
| CI boundary audit artifact output | Done | `audit.boundary.smart_core.ci` writes to `artifacts/ci/boundary_audit/*` |
| P4 split-plan queue | Done | `split_plan_queue.md`, `scripts/ci/generate_split_plan_queue.py` |

## Verified

| Command | Result |
| --- | --- |
| `git diff --check` | Passed |
| `make ci` | Passed |
| `make test.e2e.fixed_data.odoo` | Passed, 3 Odoo post-tests for E2E-02, E2E-03, and E2E-08 |
| `make audit.boundary.smart_core.ci` | Passed, artifact-only output without rewriting tracked docs |
| `python3 scripts/ci/generate_test_inventory.py` | Passed, 1120 inventory entries |
| `python3 scripts/ci/summarize_test_inventory.py` | Passed, 1120 inventory entries, unknown runtime reduced to 3, aggregate-covered assets 142 |
| `python3 scripts/ci/generate_e2e_journey_matrix.py` | Passed, 38 E2E assets mapped to 12 journeys with 0 empty gaps |
| `python3 scripts/ci/generate_module_dependency_map.py` | Passed, 14 modules and 0 circular dependencies |
| `python3 scripts/ci/generate_complexity_budget_report.py` | Passed, 3785 files scanned |
| `python3 scripts/ci/generate_split_plan_queue.py` | Passed, 45 split-plan files classified |
| `make test.e2e.preflight` | Passed, BOQ import, BOQ-to-WBS/task generation, and settlement approval preflight |
| `python3 scripts/ci/python_syntax_check.py addons/smart_construction_core/tests/test_e2e_fixed_journeys.py scripts/e2e` | Passed |
| `git push -u origin topic/v1.1-engineering-convergence` | Passed |

## Requires GitHub Admin or Authenticated Remote Execution

| Item | Status | Next Action |
| --- | --- | --- |
| P0-02 Milestone creation | Blocked locally | Run `github_governance_runbook.md` after `gh auth login` or through GitHub UI |
| P0-03 Existing issue cleanup | Blocked locally | Create seed issues, classify existing issues, merge duplicates |
| P1-02 Branch protection | Blocked locally | Enable `main` protection and required checks in GitHub settings |
| Required CI check enforcement | Blocked locally | After first workflow run, mark `v1.1 quality gate / quality-gate` as required |

## Next Execution Focus

1. Open PR from `topic/v1.1-engineering-convergence` to `main`.
2. Create milestone and labels.
3. Create seed issues from `github_issue_seed_v1.1.md`.
4. Enable branch protection after the workflow is visible.
5. Start Phase 2 cleanup: reduce the top dedupe hotspot families before promoting any PR candidates to required gates.
6. Add role/browser evidence for the fixed-data E2E-02, E2E-03, and E2E-08 journeys before release.
7. Upgrade remaining partial journeys E2E-06 and E2E-10 to fixed-data executable gates.
8. Assign concrete owner names and PR sequence for the P0 split-plan files in `split_plan_queue.md`.
