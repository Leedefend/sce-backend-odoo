# Contract Model Current Inventory v1

Iteration: `ITER-2026-04-13-1838`

Target model: `construction.contract`

Line model: `construction.contract.line`

## Main Model

The current `construction.contract` model is defined in `addons/smart_construction_core/models/support/contract_center.py`.

Important stored fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `name` | char | no | system-generated contract number, readonly |
| `subject` | char | yes | contract subject/name |
| `type` | selection | yes | `out` income contract, `in` expense contract |
| `project_id` | many2one `project.project` | yes | required relation |
| `partner_id` | many2one `res.partner` | yes | required relation |
| `category_id` | many2one `sc.dictionary` | no | contract category |
| `contract_type_id` | many2one `sc.dictionary` | no | contract direction type |
| `name_short` | char | no | short name |
| `company_id` | many2one `res.company` | yes | default company, readonly |
| `currency_id` | many2one `res.currency` | yes | default company currency |
| `tax_id` | many2one `account.tax` | yes | required; type must match contract direction |
| `date_contract` | date | no | signing/contract date |
| `date_start` | date | no | planned start |
| `date_end` | date | no | planned finish |
| `analytic_id` | many2one `account.analytic.account` | no | defer for migration |
| `budget_id` | many2one `project.budget` | no | defer for migration |
| `line_ids` | one2many `construction.contract.line` | no | contract lines |
| `note` | text | no | notes |
| `state` | selection | no | `draft`, `confirmed`, `running`, `closed`, `cancel` |

Computed stored amount fields:

- `line_amount_total`
- `amount_untaxed`
- `amount_tax`
- `amount_total`
- `amount_change`
- `amount_final`

These are derived from line data and tax rules, so legacy amount import must be designed carefully.

## Required Write Blockers

The model requires:

- `subject`
- `type`
- `project_id`
- `partner_id`
- `company_id`
- `currency_id`
- `tax_id`

`company_id`, `currency_id`, and default `tax_id` can be defaulted by Odoo under some conditions, but `project_id` and `partner_id` require migration mapping.

## State Workflow

Current state values:

- `draft`: 草稿
- `confirmed`: 已生效
- `running`: 执行中
- `closed`: 已关闭
- `cancel`: 已取消

State actions can have business checks:

- `action_confirm` requires contract lines.
- `action_close` requires contract lines.
- cancel/reset are blocked if the contract is referenced by downstream records.

Initial safe import should not replay old workflow state until mapping and line/amount semantics are frozen.

## Line Model

The current `construction.contract.line` model is also defined in `contract_center.py`.

Important fields:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `contract_id` | many2one `construction.contract` | yes | parent contract |
| `project_id` | related | no | from contract |
| `boq_line_id` | many2one `project.budget.boq.line` | no | optional BOQ relation |
| `boq_code` | related char | no | from BOQ |
| `boq_name` | related char | no | from BOQ |
| `wbs_id` | related many2one | no | from BOQ |
| `uom_id` | related many2one | no | from BOQ |
| `qty_contract` | float | no | line quantity |
| `price_contract` | monetary | no | line price |
| `amount_contract` | monetary | no | computed amount |
| `note` | char | no | line note |

The old contract export currently appears as a contract master/terms export, not a structured contract-line BOQ export. First-round contract import should avoid creating contract lines unless a separate line source is identified.

## Existing Database Baseline

In `sc_demo`:

- existing `construction.contract`: 71
- existing `construction.contract.line`: 83

These are existing/demo records and are not part of this contract migration batch.
