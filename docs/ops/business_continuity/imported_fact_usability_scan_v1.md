# Imported Fact Usability Scan v1

Task: `ITER-2026-04-17-BUSINESS-CONTINUITY-FACT-USABILITY-SCAN`

Mode: scan only

Runtime:
- profile: daily
- database: `sc_demo`
- timestamp: `2026-04-17T20:44:16+08:00`

## Scan Boundary

This scan only records bounded candidate signals for whether imported legacy
business facts can continue daily processing in the new system.

It does not classify final severity, implement fixes, or modify business code.

## Runtime Surfaces Sampled

Bounded menu/action scan under the 智能施工 daily surface found active entries for:

- `project.project`: 项目总览 / 项目台账 / 项目立项 / 快速创建项目
- `construction.contract`: 合同汇总 / 收入合同 / 支出合同 / 施工合同 / 供货合同
- `payment.request`: 财务账款 / 付款/收款申请
- `payment.ledger`: 付款记录
- `sc.settlement.order`: 结算单
- `project.material.plan`: 物资计划
- `project.budget`: 项目预算 / 预算成本
- legacy fact query models: 审批记录、收款/收入、费用/保证金、发票/税务、借款/贷款、资金日报

## Record Count Signals

| Surface | Table | Count |
| --- | --- | ---: |
| project.project | `project_project` | 756 |
| construction.contract | `construction_contract` | 6793 |
| payment.request | `payment_request` | 30102 |
| payment.request.line | `payment_request_line` | 15917 |
| payment.ledger | `payment_ledger` | 12194 |
| sc.legacy.workflow.audit | `sc_legacy_workflow_audit` | 79702 |
| sc.legacy.receipt.income.fact | `sc_legacy_receipt_income_fact` | 7220 |
| sc.legacy.expense.deposit.fact | `sc_legacy_expense_deposit_fact` | 11167 |
| sc.legacy.invoice.tax.fact | `sc_legacy_invoice_tax_fact` | 5920 |
| sc.legacy.financing.loan.fact | `sc_legacy_financing_loan_fact` | 318 |
| sc.legacy.fund.daily.snapshot.fact | `sc_legacy_fund_daily_snapshot_fact` | 496 |
| tender.bid | `tender_bid` | 0 |
| project.material.plan | `project_material_plan` | 0 |
| project.budget | `project_budget` | 0 |
| sc.settlement.order | `sc_settlement_order` | 0 |
| purchase.order | `purchase_order` | 0 |
| stock.picking | `stock_picking` | 0 |

## Candidate Signals

1. Project lifecycle imported as one opening state.
   - Evidence: all 756 projects are `lifecycle_state=draft`, `phase_key=initiation`.
   - Candidate concern: imported active/historical projects may not expose the correct continuation phase for daily work.

2. Project ownership/customer facts may be incomplete.
   - Evidence: all 756 projects have missing `company_id`; all 756 have missing `partner_id`; `user_id` is present.
   - Candidate concern: downstream forms/actions that depend on company/customer facts may be blocked or weak.

3. Contracts are relation-complete but workflow-state-flat.
   - Evidence: all 6793 contracts have project/partner/company links, but all are `state=draft`.
   - Candidate concern: imported contracts that already have downstream facts may still look unconfirmed to new-system actions.

4. Contract zero-amount records exist.
   - Evidence: 237 inbound and 50 outbound contracts have `amount_total` null or zero.
   - Candidate concern: amount-dependent continuation, reporting, or settlement steps may be unreliable for those records.

5. Payment records are relation-complete for project and partner but missing company.
   - Evidence: all 30102 payment requests have project/partner, but all have missing `company_id`.
   - Candidate concern: company-scoped operations, reporting, and authority flows may be incomplete.

6. Payment contract linkage is sparse.
   - Evidence: pay-type payment requests all miss `contract_id`; receive-type misses 3552 of 5355 contract links.
   - Candidate concern: follow-up payment/collection workflows may not connect to contract context.

7. Payment state is partially aligned but not enough by itself.
   - Evidence: 12194 payments are `done`; 17908 remain `draft`.
   - Candidate concern: records with ledger/downstream facts may require business-fact alignment beyond raw imported state.

8. Payment ledger exists but settlement/order execution surfaces are empty.
   - Evidence: `payment_ledger=12194`, but `sc_settlement_order=0`.
   - Candidate concern: historical paid facts are visible, while continuing settlement workflows may have no operational carrier.

9. Legacy financial fact query surfaces are populated and project-linked.
   - Evidence: receipt/income, expense/deposit, invoice/tax, financing/loan, and fund daily fact tables all have zero missing `project_id`.
   - Candidate concern: these facts are query-ready, but may not yet drive actionable new-system processing.

10. Workflow audit facts exist but classifications are mostly unknown.
    - Evidence: `payment.request=60337` audit rows and `construction.contract=19365` audit rows; all have `approved_at`; most `action_classification=unknown`, `legacy_status=0`.
    - Candidate concern: audit facts can prove historical approval activity, but may need semantic screening before they can align operational state.

11. Tender and procurement/material execution surfaces are empty.
    - Evidence: `tender_bid=0`, `project_material_plan=0`, `purchase_order=0`, `stock_picking=0`.
    - Candidate concern: daily continuation for tender/material/procurement may currently start only as new-system fresh work, not imported work continuation.

12. Native form action signals exist for continuation, but their states may not be reachable from imported records.
    - Evidence: forms contain buttons such as project submit, contract confirm, payment submit/approve, material submit/generate purchase, settlement submit/approve.
    - Candidate concern: because imported records are concentrated in opening states, action availability may not match historical business facts.

## Next Stage Input

Recommended next stage: `screen`.

Screen should classify candidates into:

- business-fact alignment required
- scene-orchestration/action guidance required
- data-quality exception list
- no action, query-only legacy fact surface

The first screen should start with project, contract, and payment because they have the highest imported record counts and clear continuation signals.
