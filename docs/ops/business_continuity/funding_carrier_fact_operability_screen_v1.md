# Funding Carrier Fact Operability Screen v1

## Purpose

After finance project visibility was corrected, finance users can create payment
requests on imported contract-backed projects. The next submit blocker is the
project funding gate:

```text
项目未满足资金承载条件，不能提交付款申请。
```

This screen classifies the missing business facts. It does not write business
data.

## Gate Facts

`payment.request.action_submit()` requires:

- `project.funding_enabled = True`
- `project.code` present
- exactly one active `project.funding.baseline`
- active baseline `total_amount > 0`

## Screen Result

Contract-backed imported projects:

- project_count: 652
- code_present_count: 652
- funding_enabled_count: 0
- is_funding_ready_count: 0
- active_baseline_count: 0
- fully_submit_ready_count: 0

Imported projects with completed payment facts:

- project_count: 559
- code_present_count: 559
- funding_enabled_count: 0
- active_baseline_count: 0
- fully_submit_ready_count: 0

## Baseline Candidate Source

Using non-cancelled contract sums as a deterministic funding carrier source:

- imported_contract_backed_project_count: 652
- positive_amount_final_project_count: 642
- positive_amount_total_project_count: 642
- missing_positive_amount_final_project_count: 10
- existing_active_baseline_project_count: 0
- done_payment_and_positive_final_project_count: 557
- done_payment_without_positive_final_project_count: 2

## Classification

This is a business-fact layer gap.

The system already has project codes, but imported projects were not materialized
as funding carriers. For projects with positive contract sums, the active
funding baseline can be replayed from existing contract business facts.

The 10 projects with zero contract sums must be excluded from automatic funding
baseline creation until a stronger source fact is available.

## Next Batch

Open a dedicated replay/sync batch:

- enable `funding_enabled` only for imported contract-backed projects with
  positive contract sums
- create one active `project.funding.baseline` per eligible project
- set `total_amount` from summed non-cancelled contract final amount
- skip projects with existing active baselines
- skip zero-amount projects
- provide dry-run/check/write modes and rollback evidence
