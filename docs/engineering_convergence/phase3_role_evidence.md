# Phase 3 Role-Level E2E Evidence

Date: 2026-07-12
Branch: `topic/v1.1-engineering-convergence`
Tracked issues: `#1027`, `#1028`

## Evidence Boundary

This evidence closes the release-readiness gap for E2E-02, E2E-03, E2E-06, E2E-08, and E2E-10 at role level. It does not claim full browser visual evidence. The executable gate proves that the fixed-data journeys can be completed by non-admin business roles through Odoo access rules, record rules, workflow actions, and cross-project denial checks.

Repeatable gate:

```bash
make test.e2e.fixed_data.odoo
```

Latest local result:

```text
5 post-tests in 8.08s
0 failed, 0 error(s)
PASS signature matched: (0 failed, 0 error(s))
Log: artifacts/ci/test-e2e-fixed.log
```

## Role Coverage

| Journey | Business path | Role evidence | Executable assertion |
| --- | --- | --- | --- |
| E2E-02 | Cost engineer imports fixed-data BOQ. | `e2e_cost_user` has `group_sc_cap_cost_user` and imports BOQ lines on a followed project. | `test_e2e_02_boq_import_fixed_data` asserts imported lines, project BOQ status, and role group membership. |
| E2E-03 | Project manager generates WBS/tasks from imported BOQ. | `e2e_cost_user` imports BOQ; `e2e_project_manager` has `group_sc_cap_project_manager` and generates tasks. | `test_e2e_03_boq_generates_wbs_and_tasks` asserts generated task, WBS linkage, project WBS status, and manager role membership. |
| E2E-06 | Finance user starts a payment request from a fixed contract and project. | `e2e_finance_user` has project read, contract read, and finance user capabilities, and follows the target project. | `test_e2e_06_finance_user_starts_payment_request_fixed_data` asserts draft payment request, project, contract, amount, and role group membership. |
| E2E-08 | Settlement user creates and submits settlement; settlement manager approves and completes it. | `e2e_settlement_user` has settlement user capability; `e2e_settlement_manager` has settlement manager capability. | `test_e2e_08_settlement_submit_approve_done_fixed_data` asserts submitted, approved, done states and final amount. |
| E2E-10 | Ordinary and finance users are denied cross-project records. | `e2e_ordinary_member` and `e2e_finance_user` follow only the allowed project; the denied project is followers-only and not followed by those users. | `test_e2e_10_project_and_payment_cross_project_denial_fixed_data` asserts search filtering and direct read denial for project and payment records. |

## Boundary Fixes Proven By The Gate

| Boundary | Fix | Reason |
| --- | --- | --- |
| BOQ freeze checks | `project.project.is_boq_frozen()` reads settlement and payment milestones with system privileges. | Cost users should not need settlement or finance read permission just to import BOQ; the freeze check is an internal integrity decision. |
| Settlement contract consistency | `sc.settlement.order._check_contract_consistency_or_raise()` reads linked payment requests with system privileges. | Settlement approval should validate consistency without requiring the approving role to directly read every linked payment object. |
| BOQ import master data | Fixed-data role test uses an existing UoM instead of creating a new unit. | Cost import evidence should validate BOQ import workflow, not grant master-data maintenance privileges implicitly. |
| Project isolation fixture | Fixed-data project fixtures are followers-only and explicitly assign followers per role. | Cross-project denial must be proven against the same project-level isolation semantics expected in product use. |
| Payment request scope | Finance evidence creates and queries payment requests as a finance role, not as admin. | E2E-06 and E2E-10 must prove payment operations obey role capability and project record rules. |

## Remaining Release Evidence

Browser screenshots or traces can still be added later for visual/user-operation acceptance, but the permission and workflow closure for these five journeys is now executable and repeatable through the fixed-data Odoo gate.
