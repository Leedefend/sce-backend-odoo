# Legacy Fact Usability ACL Views v1

Status: PASS
Date: 2026-04-15

## Scope

This checkpoint makes the newly assetized legacy fact models usable after a fresh
database rebuild. The batch supplies native Odoo read visibility through ACL XML,
views, actions, and finance-center menus.

Target models:

- `sc.legacy.workflow.audit`
- `sc.legacy.expense.deposit.fact`
- `sc.legacy.invoice.tax.fact`
- `sc.legacy.receipt.income.fact`
- `sc.legacy.financing.loan.fact`
- `sc.legacy.fund.daily.snapshot.fact`

## Access Boundary

Access is intentionally narrow:

- `smart_construction_core.group_sc_cap_finance_read`: read-only access.
- `smart_construction_core.group_sc_super_admin`: full administrative access.
- No record rules are introduced in this batch.
- `addons/smart_construction_core/security/ir.model.access.csv` is not changed.
- `addons/smart_construction_core/__manifest__.py` is not changed.

ACL records are added through the already-loaded XML file
`addons/smart_construction_core/security/action_groups_patch.xml` so the fresh
rebuild path does not require a manifest change.

## Native Views

Each target model receives native read-only tree, form, and search views in
`addons/smart_construction_core/views/support/evidence_views.xml`.

The views expose only business fact inspection fields such as old-system source,
project anchor, counterparty, amount, state, date, and note fields. They do not
add mutation workflows, computed business conclusions, or frontend-specific
presentation logic.

## Menu Entries

The new visibility path is:

`财务账款 -> 历史迁移资产`

Child menus:

- `历史资金日报`
- `历史借款/贷款`
- `历史收款/收入`
- `历史费用/保证金`
- `历史发票/税务`
- `历史审批事实`

The menus are restricted to finance-read users and super administrators.

## Verification

Gate commands:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-LEGACY-FACT-USABILITY-ACL-VIEWS.yaml`
- XML parse and required-id assertions for `action_groups_patch.xml` and
  `evidence_views.xml`
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core make mod.upgrade MODULE=smart_construction_core`
- `rg -n 'Legacy Fact Usability ACL Views v1|Access Boundary|Menu Entries' docs/migration_alignment/frozen/legacy_fact_usability_acl_views_v1.md`
- `git diff --check`

Result:

- Task contract validation: PASS.
- XML parse and required-id assertions: PASS.
- `smart_construction_core` module upgrade: PASS.
- Report anchor check: PASS.
- Whitespace diff check: PASS.
- Database materialization check: PASS. `sc_demo` contains 7 legacy fact menus,
  6 legacy fact actions, and 12 legacy fact access records.

Observed non-blocking warnings during upgrade:

- Existing project view alert role warnings.
- Existing docutils indentation warning in downstream custom module loading.
- Existing missing-ACL warning for unrelated models
  `sc.project.member.staging`, `sc.contract.recon.summary`, and
  `project.quick.create.wizard`.

## Rollback

Rollback is limited to removing the ACL records from
`action_groups_patch.xml`, removing the views/actions/menus from
`evidence_views.xml`, and removing this frozen checkpoint plus the task contract.
